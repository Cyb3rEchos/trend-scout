import Foundation
import Supabase

// Singleton manager for Supabase connection
class SupabaseManager: ObservableObject {
    static let shared = SupabaseManager()
    
    let client: SupabaseClient
    private let cache = CacheManager.shared
    
    private init() {
        // Initialize with configuration
        self.client = SupabaseClient(
            supabaseURL: SupabaseConfig.url,
            supabaseKey: SupabaseConfig.anonKey
        )
        
        // Clear expired cache on init
        cache.clearExpiredCache()
    }
    
    // MARK: - Optimized Database Views (Phase 2)
    
    /// Fetch today's top opportunities (10 per category) using optimized view
    func fetchTodaysOpportunities(forceRefresh: Bool = false) async throws -> [EnhancedDailyRanking] {
        let cacheKey = CacheManager.CacheKey.latestRankings
        
        if !forceRefresh, let cachedData = cache.load([EnhancedDailyRanking].self, for: cacheKey) {
            return cachedData
        }
        do {
            // Query daily_rankings directly for ALL apps with AI data (all categories)
            let response = try await client
                .from("daily_rankings")
                .select()
                .not("clone_name", operator: .is, value: AnyJSON.null)
                .not("build_priority", operator: .is, value: AnyJSON.null)
                .order("total", ascending: false)
                .limit(80) // Get top 80 AI apps across all categories (includes Forest at rank 53)
                .execute()
                .data
            
            let decoder = JSONDecoder()
            let opportunities = try decoder.decode([EnhancedDailyRanking].self, from: response)
            
            cache.save(opportunities, for: cacheKey)
            return opportunities
        } catch {
            print("⚠️ AI query failed, using fallback: \(error)")
            return try await fetchEnhancedRankingsManualLimit()
        }
    }
    
    /// Fetch tonight's buildable apps (EASY_CLONE + TONIGHT priority)
    func fetchTonightOpportunities(forceRefresh: Bool = false) async throws -> [EnhancedDailyRanking] {
        let cacheKey = CacheManager.CacheKey.categoryLeaders // Reuse cache key
        
        if !forceRefresh, let cachedData = cache.load([EnhancedDailyRanking].self, for: cacheKey) {
            print("✨ Using cached tonight's opportunities")
            return cachedData
        }
        
        do {
            let response = try await client
                .from("tonight_opportunities") 
                .select()
                .order("total", ascending: false)
                .execute()
                .data
            
            let decoder = JSONDecoder()
            let tonightApps = try decoder.decode([EnhancedDailyRanking].self, from: response)
            
            print("🌙 Fetched \(tonightApps.count) tonight's buildable apps")
            cache.save(tonightApps, for: cacheKey)
            return tonightApps
        } catch {
            print("⚠️ tonight_opportunities view failed, falling back to manual filter: \(error)")
            return try await fetchEnhancedRankingsManualFilter(priority: "TONIGHT", difficulty: "EASY_CLONE")
        }
    }
    
    /// Fetch category leaders (top 3 from each category)
    func fetchCategoryLeaders(forceRefresh: Bool = false) async throws -> [EnhancedDailyRanking] {
        let cacheKey = CacheManager.CacheKey.categoryLeaders
        
        if !forceRefresh, let cachedData = cache.load([EnhancedDailyRanking].self, for: cacheKey) {
            print("✨ Using cached category leaders")
            return cachedData
        }
        
        // Manual implementation since we don't have category_leaders view yet
        let allOpportunities = try await fetchTodaysOpportunities(forceRefresh: forceRefresh)
        
        // Group by category and take top 3 from each
        let grouped = Dictionary(grouping: allOpportunities, by: { $0.category })
        var leaders: [EnhancedDailyRanking] = []
        
        for (_, categoryApps) in grouped {
            let top3 = Array(categoryApps.prefix(3))
            leaders.append(contentsOf: top3)
        }
        
        // Sort by total score
        leaders.sort { ($0.total ?? 0) > ($1.total ?? 0) }
        
        print("🏆 Generated \(leaders.count) category leaders")
        cache.save(leaders, for: cacheKey)
        return leaders
    }

    // Helper method to fetch AI-enhanced rankings from daily_rankings table
    func fetchEnhancedRankings(category: String? = nil, limit: Int = 100, forceRefresh: Bool = false) async throws -> [EnhancedDailyRanking] {
        print("🔍 fetchEnhancedRankings called - category: \(category ?? "all"), limit: \(limit), forceRefresh: \(forceRefresh)")
        
        // Check cache first unless force refresh
        if !forceRefresh {
            let cacheKey: CacheManager.CacheKey = category != nil ? .categoryData : .latestRankings
            if let cachedData = cache.load([EnhancedDailyRanking].self, for: cacheKey, category: category) {
                print("✨ Using cached AI-enhanced data for \(category ?? "all categories")")
                print("📋 Cached data count: \(cachedData.count)")
                if cachedData.isEmpty {
                    print("⚠️ WARNING: Cache returned EMPTY array!")
                }
                return cachedData
            }
            print("🔍 No cache found, fetching from database...")
        } else {
            print("🔍 Force refresh requested, skipping cache")
        }
        
        // Build and execute query - PRIMARY: daily_rankings (AI-enhanced)
        do {
            print("🔍 Querying daily_rankings table...")
            let baseQuery = client
                .from("daily_rankings")  // Switch to AI-enhanced table
                .select()
            
            let response: Data
            if let category = category {
                print("🔍 Filtering by category: \(category)")
                response = try await baseQuery
                    .eq("category", value: category)
                    .order("total", ascending: false)
                    .limit(limit)
                    .execute()
                    .data
            } else {
                print("🔍 Fetching all categories, limit: \(limit)")
                response = try await baseQuery
                    .order("total", ascending: false)
                    .limit(limit)
                    .execute()
                    .data
            }
            
            print("🔍 Response size: \(response.count) bytes")
            
            let decoder = JSONDecoder()
            // Don't use snake_case conversion for daily_rankings - fields are already in correct format
            let enhancedData = try decoder.decode([EnhancedDailyRanking].self, from: response)
            
            print("🚀 Fetched \(enhancedData.count) AI-enhanced rankings from daily_rankings table!")
            
            if enhancedData.isEmpty {
                print("⚠️ WARNING: daily_rankings table returned EMPTY!")
                print("⚠️ This could mean:")
                print("⚠️   1. No data in daily_rankings table")
                print("⚠️   2. Query filters are too restrictive")
                print("⚠️   3. Date mismatch in data")
            } else {
                print("🚀 Sample data: \(enhancedData.prefix(2).map { "\($0.name) - \($0.category)" })")
            }
            
            // Cache the results
            let cacheKey: CacheManager.CacheKey = category != nil ? .categoryData : .latestRankings
            cache.save(enhancedData, for: cacheKey, category: category)
            
            return enhancedData
        } catch {
            print("⚠️ Failed to fetch from daily_rankings: \(error)")
            // FALLBACK: Try scout_results (basic data)
            return try await fetchBasicRankingsAsFallback(category: category, limit: limit)
        }
    }
    
    // Legacy method for backward compatibility - now uses enhanced rankings
    func fetchLatestRankings(category: String? = nil, limit: Int = 100, forceRefresh: Bool = false) async throws -> [DailyRanking] {
        // Convert enhanced rankings to basic format for backward compatibility
        let enhancedRankings = try await fetchEnhancedRankings(category: category, limit: limit, forceRefresh: forceRefresh)
        return enhancedRankings.map { enhanced in
            DailyRanking(
                id: enhanced.id,
                generatedAt: enhanced.date,
                category: enhanced.category,
                country: enhanced.country,
                chart: enhanced.chart,
                rank: enhanced.rank,
                appId: enhanced.appId,
                bundleId: enhanced.bundleId,
                name: enhanced.name,
                price: enhanced.price ?? 0,
                hasIap: enhanced.hasIap,
                ratingCount: enhanced.ratingCount,
                ratingAvg: enhanced.ratingAvg,
                descLen: enhanced.descLen,
                rankDelta7d: nil, // Not in daily_rankings
                demand: enhanced.demand,
                monetization: enhanced.monetization,
                lowComplexity: enhanced.lowComplexity,
                moatRisk: enhanced.moatRisk,
                total: enhanced.total,
                createdAt: enhanced.createdAt,
                updatedAt: enhanced.updatedAt
            )
        }
    }
    
    // Fallback to basic scout_results if daily_rankings fails
    private func fetchBasicRankingsAsFallback(category: String? = nil, limit: Int = 100) async throws -> [EnhancedDailyRanking] {
        print("🔄 Falling back to scout_results table...")
        
        let baseQuery = client
            .from(SupabaseConfig.scoutResultsTable)
            .select()
        
        let response: Data
        if let category = category {
            response = try await baseQuery
                .eq("category", value: category)
                .order("total", ascending: false)
                .limit(limit)
                .execute()
                .data
        } else {
            response = try await baseQuery
                .order("total", ascending: false)
                .limit(limit)
                .execute()
                .data
        }
        
        let decoder = JSONDecoder()
        // Don't use convertFromSnakeCase since DailyRanking CodingKeys already handle field mapping
        let basicData = try decoder.decode([DailyRanking].self, from: response)
        
        // Convert basic rankings to enhanced format (without AI data)
        return basicData.map { basic in
            EnhancedDailyRanking(
                id: basic.id,
                date: basic.generatedAt,
                category: basic.category,
                country: basic.country,
                chart: basic.chart,
                rank: basic.rank,
                appId: basic.appId,
                bundleId: basic.bundleId,
                name: basic.name,
                price: basic.price,
                hasIap: basic.hasIap,
                ratingCount: basic.ratingCount,
                ratingAvg: basic.ratingAvg,
                descLen: basic.descLen,
                demand: basic.demand,
                monetization: basic.monetization,
                lowComplexity: basic.lowComplexity,
                moatRisk: basic.moatRisk,
                total: basic.total,
                cloneDifficulty: nil, // No AI data in basic
                revenuePotential: nil, // No AI data in basic
                categoryRank: basic.rank,
                aiRecommendationRaw: nil, // No AI data in basic
                recommendationGeneratedAt: nil,
                
                // NEW FIELDS: Set defaults for fallback data
                cloneName: nil,
                cloneNameCustom: nil, 
                buildPriority: nil,
                
                createdAt: basic.createdAt,
                updatedAt: basic.updatedAt
            )
        }
    }
    
    // Helper method to fetch category leaders with caching (legacy format)
    func fetchCategoryLeadersLegacy(forceRefresh: Bool = false) async throws -> [DailyRanking] {
        // Check cache first unless force refresh
        if !forceRefresh {
            if let cachedData = cache.load([DailyRanking].self, for: .categoryLeaders) {
                print("Using cached category leaders")
                return cachedData
            }
        }
        
        do {
            // Fetch from database - get top apps by total score
            let responseData = try await client
                .from(SupabaseConfig.scoutResultsTable)
                .select()
                .order("total", ascending: false)
                .limit(150)
                .execute()
                .data
            
            let decoder = JSONDecoder()
            // Don't use convertFromSnakeCase since DailyRanking CodingKeys already handle field mapping
            let allRankings = try decoder.decode([DailyRanking].self, from: responseData)
            
            // Group by category and take top 3 from each
            var categoryLeaders: [DailyRanking] = []
            let grouped = Dictionary(grouping: allRankings, by: { $0.category })
            
            for (_, rankings) in grouped {
                let topThree = Array(rankings.prefix(3))
                categoryLeaders.append(contentsOf: topThree)
            }
            
            let sortedLeaders = categoryLeaders.sorted { ($0.total ?? 0) > ($1.total ?? 0) }
            
            print("Fetched \(sortedLeaders.count) category leaders from Supabase")
            
            // Cache the results
            cache.save(sortedLeaders, for: .categoryLeaders)
            
            return sortedLeaders
        } catch {
            print("Error fetching category leaders: \(error)")
            // Fall back to simulated data
            return try await fetchSimulatedData(category: nil, limit: 150)
        }
    }
    
    // MARK: - Fallback Methods for Optimized Views
    
    /// Manual implementation when todays_opportunities view is empty/unavailable
    private func fetchEnhancedRankingsManualLimit() async throws -> [EnhancedDailyRanking] {
        let allRankings = try await fetchEnhancedRankings(limit: 500)
        
        // Group by category and take top 10 from each
        let grouped = Dictionary(grouping: allRankings, by: { $0.category })
        var limitedOpportunities: [EnhancedDailyRanking] = []
        
        for (_, categoryApps) in grouped {
            let top10 = Array(categoryApps.prefix(10))
            limitedOpportunities.append(contentsOf: top10)
        }
        
        // Sort by total score
        limitedOpportunities.sort { ($0.total ?? 0) > ($1.total ?? 0) }
        
        return limitedOpportunities
    }
    
    /// Manual filter when tonight_opportunities view is unavailable
    private func fetchEnhancedRankingsManualFilter(priority: String, difficulty: String) async throws -> [EnhancedDailyRanking] {
        let allRankings = try await fetchEnhancedRankings(limit: 500)
        
        // Filter for tonight's buildable apps
        let tonightApps = allRankings.filter { ranking in
            ranking.buildPriority == priority && 
            ranking.cloneDifficulty?.rawValue == difficulty
        }
        
        // Sort by score
        let sorted = tonightApps.sorted { ($0.total ?? 0) > ($1.total ?? 0) }
        
        print("🌙 Manual filter: \(sorted.count) tonight opportunities")
        return sorted
    }

    // Clear all cached data
    func clearCache() {
        cache.clearCache()
    }
    
    // Fallback method for simulated data when database is unavailable
    private func fetchSimulatedData(category: String? = nil, limit: Int) async throws -> [DailyRanking] {
        // Simulate network delay
        try await Task.sleep(nanoseconds: 500_000_000)
        
        let categories = [
            "Utilities", "Productivity", "Photo & Video", "Health & Fitness",
            "Lifestyle", "Finance", "Music", "Education", "Graphics & Design", "Entertainment"
        ]
        
        var rankings: [DailyRanking] = []
        let dateFormatter = ISO8601DateFormatter()
        let currentDate = dateFormatter.string(from: Date())
        
        let categoriesToUse = category != nil ? [category!] : categories
        
        for cat in categoriesToUse {
            for rank in 1...5 {
                let ranking = DailyRanking(
                    id: UUID().uuidString,
                    generatedAt: currentDate,
                    category: cat,
                    country: "US",
                    chart: "topfreeapplications",
                    rank: rank,
                    appId: "\(Int.random(in: 100000000...999999999))",
                    bundleId: "com.example.\(cat.lowercased())app\(rank)",
                    name: "\(cat) App #\(rank)",
                    price: rank == 1 ? 0 : Double(rank - 1) * 0.99,
                    hasIap: rank <= 3,
                    ratingCount: Int.random(in: 100...50000),
                    ratingAvg: Double.random(in: 3.5...5.0),
                    descLen: Int.random(in: 500...2000),
                    rankDelta7d: Int.random(in: -5...5),
                    demand: Double.random(in: 0.5...1.0),
                    monetization: Double.random(in: 0.3...0.9),
                    lowComplexity: Double.random(in: 0.4...0.8),
                    moatRisk: Double.random(in: 0.2...0.6),
                    total: Double.random(in: 1.5...3.0),
                    createdAt: currentDate,
                    updatedAt: currentDate
                )
                rankings.append(ranking)
            }
        }
        
        // Sort by total score descending
        rankings.sort { ($0.total ?? 0) > ($1.total ?? 0) }
        
        // Apply limit
        return Array(rankings.prefix(limit))
    }
}