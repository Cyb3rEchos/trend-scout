import Foundation

@MainActor
class OpportunityService: ObservableObject {
    static let shared = OpportunityService()
    private let supabaseManager = SupabaseManager.shared
    
    @Published var allOpportunities: [Opportunity] = []
    @Published var categoryLeaders: [DailyRanking] = []
    @Published var tonightOpportunities: [Opportunity] = [] // 🌙 New: Tonight's buildable apps
    @Published var isLoading: Bool = false
    @Published var error: String?
    
    // 🔧 NEW: Cache for selected opportunities that may not be in allOpportunities
    private var selectedOpportunityCache: [String: Opportunity] = [:]
    
    var selectedOpportunities: [Opportunity] {
        // Use Dictionary(grouping:) to safely handle duplicates, keeping the first occurrence
        let grouped = Dictionary(grouping: allOpportunities, by: { $0.id })
        let uniqueOpportunities = grouped.compactMap { $0.value.first }
        
        let selectedIds = UserSelectionService.shared.selectedOpportunities
        
        if selectedIds.isEmpty {
            return []
        }
        
        var resultOpportunities: [Opportunity] = []
        
        for selectedId in selectedIds {
            // PRIORITY 1: Try to find in allOpportunities first (most up-to-date data)
            if let foundOpportunity = uniqueOpportunities.first(where: { $0.id == selectedId }) {
                resultOpportunities.append(foundOpportunity)
                // Update cache with the real data to replace any placeholder
                selectedOpportunityCache[selectedId] = foundOpportunity
            }
            // PRIORITY 2: Try to find in cache (for category-selected opportunities) - BUT ONLY if allOpportunities is empty
            else if allOpportunities.isEmpty, let cachedOpportunity = selectedOpportunityCache[selectedId] {
                resultOpportunities.append(cachedOpportunity)
            }
            // PRIORITY 3: Create placeholder only as last resort
            else {
                let placeholder = createPlaceholderOpportunity(for: selectedId)
                selectedOpportunityCache[selectedId] = placeholder // Cache it for future use
                resultOpportunities.append(placeholder)
            }
        }
        
        return resultOpportunities
    }
    
    private init() {
        // Check for mock/test data and clear it if found
        let selectedIds = UserSelectionService.shared.selectedOpportunities
        let hasMockData = selectedIds.contains { $0.contains("com.example.") }
        
        if hasMockData {
            UserSelectionService.shared.clearAllSelections()
        }
    }
    
    func fetchTodaysOpportunities() async {
        isLoading = true
        error = nil
        
        // Clear caches to ensure fresh data
        allOpportunities.removeAll()
        selectedOpportunityCache.removeAll()
        supabaseManager.clearCache()
        
        do {
            // Fetch AI-enhanced opportunities from database
            let enhancedRankings = try await supabaseManager.fetchTodaysOpportunities(forceRefresh: true)
            
            if enhancedRankings.isEmpty {
                print("⚠️ WARNING: Database returned empty rankings")
            }
            
            // Convert enhanced rankings to AI-powered opportunities and deduplicate by ID
            let opportunities = enhancedRankings.map { $0.toOpportunity() }
            let grouped = Dictionary(grouping: opportunities, by: { $0.id })
            allOpportunities = grouped.compactMap { $0.value.first }
            
            // Clear old placeholder cache before adding new data
            selectedOpportunityCache.removeAll()
            
            // Cache all opportunities for selected items
            for opportunity in allOpportunities {
                selectedOpportunityCache[opportunity.id] = opportunity
            }
            
            // Log any duplicates found for debugging
            let duplicates = grouped.filter { $0.value.count > 1 }
            if !duplicates.isEmpty {
                print("⚠️ Found \(duplicates.count) duplicate app IDs")
            }
            
            print("✅ Loaded \(allOpportunities.count) AI-powered opportunities")
            
            // Auto-populate Daily Brief with best opportunities if none selected
            await autoSelectBestOpportunities()
            
        } catch {
            self.error = "Failed to load AI opportunities: \(error.localizedDescription)"
            print("⚠️ Error fetching AI opportunities: \(error)")
            // Fallback to basic data
            await fetchBasicDataAsFallback()
        }
        
        isLoading = false
    }
    
    private func fetchBasicDataAsFallback() async {
        do {
            // Fall back to basic rankings
            let basicRankings = try await supabaseManager.fetchLatestRankings(limit: 50)
            let opportunities = basicRankings.map { createOpportunityFromRanking($0) }
            // Use Dictionary(grouping:) to safely handle duplicates, keeping the first occurrence
            let grouped = Dictionary(grouping: opportunities, by: { $0.id })
            allOpportunities = grouped.compactMap { $0.value.first }
            print("📋 Loaded \(allOpportunities.count) basic opportunities as fallback")
            
            // Auto-populate Daily Brief with best opportunities
            await autoSelectBestOpportunities()
        } catch {
            // Final fallback to mock data
            loadMockData()
            print("🔧 Using mock data as final fallback")
            
            // Auto-populate Daily Brief with mock opportunities
            await autoSelectBestOpportunities()
        }
    }
    
    func getOpportunityById(_ id: String) -> Opportunity? {
        return allOpportunities.first { $0.id == id }
    }
    
    func toggleOpportunitySelection(_ ranking: DailyRanking) {
        print("🔥 📋 TOGGLE SELECTION CALLED for: \(ranking.name) (bundleId: \(ranking.bundleId))")
        
        // Create opportunity from ranking data
        let opportunity = createOpportunityFromRanking(ranking)
        
        // 🔧 NEW: Cache the opportunity so it's available for selectedOpportunities getter
        selectedOpportunityCache[opportunity.id] = opportunity
        print("🔥 📋 CACHED OPPORTUNITY: \(opportunity.title) (ID: \(opportunity.id))")
        
        // 🔧 ALSO: Add opportunity to allOpportunities if not present (for immediate UI updates)
        if !allOpportunities.contains(where: { $0.id == opportunity.id }) {
            print("🔥 ➕ ADDING NEW OPPORTUNITY to allOpportunities: \(opportunity.title)")
            allOpportunities.append(opportunity)
        } else {
            print("🔥 ✅ OPPORTUNITY ALREADY EXISTS in allOpportunities")
        }
        
        // Toggle selection in UserSelectionService
        print("🔥 🔄 TOGGLING SELECTION for ID: \(opportunity.id)")
        UserSelectionService.shared.toggleSelection(opportunity.id)
        
        // 🔧 DEBUG: Check current selection status
        let isNowSelected = UserSelectionService.shared.isSelected(opportunity.id)
        print("🔥 📋 SELECTION STATUS AFTER TOGGLE: \(isNowSelected ? "SELECTED" : "DESELECTED")")
        print("🔥 📋 TOTAL SELECTED COUNT: \(UserSelectionService.shared.selectedOpportunities.count)")
        
        // 🔧 NEW: If deselected, remove from cache to keep it clean
        if !isNowSelected {
            selectedOpportunityCache.removeValue(forKey: opportunity.id)
            print("🔥 📋 REMOVED FROM CACHE: \(opportunity.id)")
        }
    }
    
    func cacheOpportunity(_ opportunity: Opportunity) {
        print("🔥 📋 CACHING OPPORTUNITY: \(opportunity.title) (ID: \(opportunity.id))")
        selectedOpportunityCache[opportunity.id] = opportunity
        
        // Also add to allOpportunities if not present
        if !allOpportunities.contains(where: { $0.id == opportunity.id }) {
            print("🔥 ➕ ADDING TO allOpportunities: \(opportunity.title)")
            allOpportunities.append(opportunity)
        }
    }
    
    private func createPlaceholderOpportunity(for bundleId: String) -> Opportunity {
        // Extract app name from bundle ID (basic fallback)
        let appNameGuess = bundleId.components(separatedBy: ".").last?.capitalized ?? "Selected App"
        
        return Opportunity(
            id: bundleId,
            appName: appNameGuess,
            category: "Unknown",
            cloneScore: 2.0,
            title: "\(appNameGuess) Clone",
            subtitle: "Added from category browsing",
            emoji: "📱",
            keyFeatures: [
                Feature(icon: "⭐", title: "Selected", desc: "Added to daily brief"),
                Feature(icon: "🔍", title: "Analyze", desc: "Requires further research")
            ],
            revenueModel: RevenueModel(type: "unknown", primary: "To be analyzed"),
            buildEstimate: BuildEstimate(time: "TBD", difficulty: "TBD", priority: "TBD"),
            marketGap: "Opportunity identified from category browsing - requires analysis",
            competitiveEdge: "To be analyzed in detail",
            risks: ["Requires further analysis"],
            iosFeatures: ["Native iOS app"],
            confidence: 0.5,
            priority: .thisWeek,
            generatedAt: Date(),
            categoryRank: nil,
            originalRank: nil,
            cloneName: nil,
            cloneNameCustom: nil
        )
    }
    
    func createOpportunityFromRanking(_ ranking: DailyRanking) -> Opportunity {
        // Create a basic opportunity from ranking data for navigation
        let opportunity = Opportunity(
            id: ranking.bundleId,
            appName: ranking.name,
            category: ranking.category,
            cloneScore: ranking.total ?? 1.0,
            title: ranking.name,
            subtitle: "Ranked #\(ranking.rank) in \(ranking.category)",
            emoji: getCategoryEmoji(ranking.category),
            keyFeatures: generateBasicFeatures(for: ranking),
            revenueModel: RevenueModel(
                type: ranking.hasIap ? "freemium" : "paid",
                primary: ranking.price == 0 ? "In-app purchases" : "One-time purchase"
            ),
            buildEstimate: BuildEstimate(
                time: "2-3 hours",
                difficulty: ranking.total ?? 1.0 > 2.0 ? "Easy" : "Medium",
                priority: ranking.rank <= 3 ? "Tonight" : "This Week"
            ),
            marketGap: "Identified opportunity in \(ranking.category) category with strong market position.",
            competitiveEdge: "Proven concept with \(ranking.ratingCount ?? 0) user ratings and \(String(format: "%.1f", ranking.ratingAvg ?? 0)) star rating.",
            risks: ["Market competition", "User acquisition costs"],
            iosFeatures: ["Native iOS integration", "SwiftUI interface"],
            confidence: min(0.9, (ranking.total ?? 1.0) / 3.0),
            priority: ranking.rank <= 3 ? .tonight : .thisWeek,
            generatedAt: Date(),
            categoryRank: ranking.categoryRank,
            originalRank: ranking.rank,
            cloneName: nil,
            cloneNameCustom: nil
        )
        
        // Note: Don't modify @Published properties during view updates to avoid "Publishing changes from within view updates" warnings
        // The allOpportunities array will be populated by loadAIOpportunities() method
        
        return opportunity
    }
    
    private func getCategoryEmoji(_ category: String) -> String {
        switch category {
        case "Utilities": return "⚙️"
        case "Productivity": return "📈"
        case "Photo & Video": return "📸"
        case "Health & Fitness": return "💪"
        case "Lifestyle": return "🌿"
        case "Finance": return "💰"
        case "Music": return "🎵"
        case "Education": return "📚"
        case "Graphics & Design": return "🎨"
        case "Entertainment": return "🎬"
        default: return "📱"
        }
    }
    
    private func generateBasicFeatures(for ranking: DailyRanking) -> [Feature] {
        var features: [Feature] = []
        
        if ranking.hasIap {
            features.append(Feature(icon: "💰", title: "Monetized", desc: "In-app purchases available"))
        }
        
        if let ratingCount = ranking.ratingCount, ratingCount > 1000 {
            features.append(Feature(icon: "⭐", title: "Popular", desc: "\(ratingCount) user ratings"))
        }
        
        if ranking.rank <= 5 {
            features.append(Feature(icon: "🏆", title: "Top Ranked", desc: "Top 5 in category"))
        }
        
        features.append(Feature(icon: "📱", title: "Mobile First", desc: "Optimized for iOS"))
        
        return features
    }
    
    func fetchCategoryLeaders() async {
        isLoading = true
        error = nil
        
        print("🏆 fetchCategoryLeaders STARTED")
        print("🏆 Current categoryLeaders count: \(categoryLeaders.count)")
        
        do {
            // 🚀 Try to fetch AI-enhanced data from daily_rankings table
            print("🏆 Fetching enhanced category data...")
            let enhancedLeaders = try await fetchEnhancedCategoryData()
            print("🏆 Received \(enhancedLeaders.count) enhanced leaders")
            
            categoryLeaders = enhancedLeaders
            
            // Debug: Show category distribution
            let categoryCounts = Dictionary(grouping: categoryLeaders, by: { $0.category })
            print("🏆 Category distribution:")
            for (category, apps) in categoryCounts {
                print("🏆   - \(category): \(apps.count) apps")
            }
            
            if categoryLeaders.isEmpty {
                // Fallback to basic data if no AI data
                print("⚠️ No AI-enhanced leaders found, trying basic data...")
                categoryLeaders = try await fetchBasicCategoryData()
                print("🏆 Got \(categoryLeaders.count) basic leaders as fallback")
            }
        } catch {
            // On error, use mock data
            self.error = "Failed to load data: \(error.localizedDescription)"
            print("❌ Error loading category leaders: \(error)")
            print("❌ Using mock data as fallback")
            loadMockCategoryLeaders()
        }
        
        print("🏆 fetchCategoryLeaders COMPLETED with \(categoryLeaders.count) leaders")
        isLoading = false
    }
    
    // 🌙 New: Fetch tonight's buildable opportunities (EASY_CLONE + TONIGHT priority)
    func fetchTonightOpportunities() async {
        isLoading = true
        error = nil
        
        do {
            let enhancedTonightApps = try await supabaseManager.fetchTonightOpportunities()
            
            // Convert to opportunities and deduplicate
            let opportunities = enhancedTonightApps.map { $0.toOpportunity() }
            let grouped = Dictionary(grouping: opportunities, by: { $0.id })
            tonightOpportunities = grouped.compactMap { $0.value.first }
            
            print("🌙 Loaded \(tonightOpportunities.count) tonight's buildable opportunities!")
            
        } catch {
            self.error = "Failed to load tonight's opportunities: \(error.localizedDescription)"
            print("❌ Error loading tonight's opportunities: \(error)")
            tonightOpportunities = [] // Clear on error
        }
        
        isLoading = false
    }
    
    func fetchOpportunitiesByCategory(_ category: String) async -> [DailyRanking] {
        print("📂 fetchOpportunitiesByCategory STARTED for: \(category)")
        print("📂 Current cache size: \(selectedOpportunityCache.count)")
        
        do {
            // 🎯 Phase 2: Limit to 10 per category (matching your vision)
            print("📂 Fetching enhanced rankings for \(category)...")
            let enhancedRankings = try await supabaseManager.fetchEnhancedRankings(category: category, limit: 10, forceRefresh: true)
            
            print("📂 Received \(enhancedRankings.count) enhanced rankings for \(category)")
            
            if enhancedRankings.isEmpty {
                print("📂 ⚠️ WARNING: No data returned for category \(category)")
            }
            
            // Cache the enhanced opportunities for when they're selected
            for enhanced in enhancedRankings {
                let opportunity = enhanced.toOpportunity()
                selectedOpportunityCache[opportunity.id] = opportunity
                print("📂 CACHED: \(opportunity.id)")
                print("📂   - Name: \(opportunity.appName)")
                print("📂   - Display: \(opportunity.displayName)")
                print("📂   - Clone: \(opportunity.cloneName ?? "none")")
                print("📂   - Priority: \(opportunity.priority.displayName)")
            }
            
            // Convert to basic format for backward compatibility
            let rankings = enhancedRankings.map { enhanced in
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
                    rankDelta7d: nil,
                    demand: enhanced.demand,
                    monetization: enhanced.monetization,
                    lowComplexity: enhanced.lowComplexity,
                    moatRisk: enhanced.moatRisk,
                    total: enhanced.enhancedScore, // Use AI-enhanced score!
                    createdAt: enhanced.createdAt,
                    updatedAt: enhanced.updatedAt
                )
            }
            
            // 🔧 DEDUPLICATION: Remove duplicates by bundleId
            let grouped = Dictionary(grouping: rankings, by: { $0.bundleId })
            let deduplicatedRankings = grouped.compactMap { $0.value.first }
            
            print("🎯 Fetched \(rankings.count) AI-enhanced rankings for category: \(category)")
            print("🔧 After deduplication: \(deduplicatedRankings.count) unique apps")
            
            if rankings.count > deduplicatedRankings.count {
                let duplicateCount = rankings.count - deduplicatedRankings.count
                print("⚠️ REMOVED \(duplicateCount) duplicate apps from \(category) category")
            }
            
            return deduplicatedRankings
        } catch {
            print("⚠️ Failed to fetch AI category data from Supabase: \(error)")
            // Better fallback logic: try multiple sources
            
            // First, try cached category leaders
            let cachedResults = categoryLeaders.filter { $0.category == category }
            if !cachedResults.isEmpty {
                print("📋 Using \(cachedResults.count) cached results for \(category)")
                return cachedResults
            }
            
            // Second, try all opportunities filtered by category
            let allCategoryResults = allOpportunities.compactMap { opportunity -> DailyRanking? in
                guard opportunity.category == category else { return nil }
                // Convert back to DailyRanking for compatibility
                return DailyRanking(
                    id: opportunity.id,
                    generatedAt: opportunity.generatedAt?.ISO8601Format() ?? "",
                    category: opportunity.category,
                    country: "US",
                    chart: "topfreeapplications",
                    rank: 1,
                    appId: "unknown",
                    bundleId: opportunity.id,
                    name: opportunity.appName,
                    price: 0,
                    hasIap: true,
                    ratingCount: nil,
                    ratingAvg: nil,
                    descLen: nil,
                    rankDelta7d: nil,
                    demand: nil,
                    monetization: nil,
                    lowComplexity: nil,
                    moatRisk: nil,
                    total: opportunity.cloneScore,
                    createdAt: nil,
                    updatedAt: nil
                )
            }
            
            if !allCategoryResults.isEmpty {
                print("📋 Using \(allCategoryResults.count) opportunities converted for \(category)")
                return allCategoryResults
            }
            
            // Final fallback: return empty array (will show "no opportunities found")
            print("📋 No data available for \(category)")
            return []
        }
    }
    
    private func fetchEnhancedCategoryData() async throws -> [DailyRanking] {
        // 🏆 Phase 2: Use optimized category leaders method  
        do {
            let enhancedLeaders = try await supabaseManager.fetchCategoryLeaders(forceRefresh: false)
            
            // Convert to basic format for backward compatibility
            let converted = enhancedLeaders.map { enhanced in
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
                    rankDelta7d: nil,
                    demand: enhanced.demand,
                    monetization: enhanced.monetization,
                    lowComplexity: enhanced.lowComplexity,
                    moatRisk: enhanced.moatRisk,
                    total: enhanced.total,
                    createdAt: enhanced.createdAt,
                    updatedAt: enhanced.updatedAt
                )
            }
            return converted
        } catch {
            print("⚠️ Enhanced category leaders failed, falling back to manual grouping...")
            let enhancedData = try await supabaseManager.fetchEnhancedRankings(forceRefresh: false)
            
            // Group by category and take top 3 from each with AI prioritization
            var categoryLeaders: [DailyRanking] = []
            let grouped = Dictionary(grouping: enhancedData, by: { $0.category })
            
            for (_, rankings) in grouped {
                // Sort by enhanced AI score and intelligent priority
                let sortedRankings = rankings.sorted { first, second in
                    // Prioritize easy clones with good revenue
                    let firstPriority = first.intelligentPriority.sortOrder
                    let secondPriority = second.intelligentPriority.sortOrder
                    
                    if firstPriority != secondPriority {
                        return firstPriority < secondPriority
                    }
                    
                    // Then by enhanced score
                    return first.enhancedScore > second.enhancedScore
                }
                
                let topThree = Array(sortedRankings.prefix(3))
                
                // Convert to basic format for UI compatibility
                let basicRankings = topThree.map { enhanced in
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
                        rankDelta7d: nil,
                        demand: enhanced.demand,
                        monetization: enhanced.monetization,
                        lowComplexity: enhanced.lowComplexity,
                        moatRisk: enhanced.moatRisk,
                        total: enhanced.enhancedScore, // AI-enhanced score
                        createdAt: enhanced.createdAt,
                        updatedAt: enhanced.updatedAt
                    )
                }
                
                categoryLeaders.append(contentsOf: basicRankings)
            }
            
            let finalLeaders = categoryLeaders.sorted { ($0.total ?? 0) > ($1.total ?? 0) }
            print("🏆 Fetched \(finalLeaders.count) AI-enhanced category leaders!")
            
            return finalLeaders
        }
    }
    
    private func fetchBasicCategoryData() async throws -> [DailyRanking] {
        // Fallback to basic scout_results data
        do {
            let basicData = try await supabaseManager.fetchCategoryLeadersLegacy()
            print("📋 Fetched \(basicData.count) basic category leaders from scout_results")
            return basicData
        } catch {
            print("❌ Failed to fetch basic category data: \(error)")
            throw error
        }
    }
    
    private func fetchRealCategoryData() async throws -> [DailyRanking] {
        // Legacy method - now redirects to enhanced data
        return try await fetchEnhancedCategoryData()
    }
    
    // Removed simulateSupabaseQuery - now handled in SupabaseManager
    
    /*private func simulateSupabaseQuery() async throws -> [DailyRanking] {
        // Using real data structure from actual database
        // This simulates the response from: SELECT * FROM scout_results ORDER BY total DESC
        
        try? await Task.sleep(nanoseconds: 500_000_000) // Simulate network delay
        
        // Real data from all 10 categories (top performers from database)
        let realDatabaseData = [
            // Productivity top performers
            DailyRanking(
                id: UUID().uuidString,
                generatedAt: "2025-08-20T02:55:35.592724+00:00",
                category: "Productivity", 
                country: "US", 
                chart: "paid",
                rank: 3, 
                appId: "933627574", 
                bundleId: "com.quickbend", 
                name: "QuickBend: Conduit Bending",
                price: 9.99, 
                hasIap: false, 
                ratingCount: 150, 
                ratingAvg: 4.8, 
                descLen: 250,
                rankDelta7d: nil,
                demand: 2.5, 
                monetization: 4.2, 
                lowComplexity: 3.8, 
                moatRisk: 1.5, 
                total: 3.26,
                createdAt: "2025-08-20T02:55:35.592724+00:00",
                updatedAt: "2025-08-20T02:55:35.592724+00:00"
            ),
            
            // Finance top performers
            DailyRanking(
                id: UUID().uuidString,
                generatedAt: "2025-08-20T02:55:35.592724+00:00",
                category: "Finance", 
                country: "US", 
                chart: "paid",
                rank: 8, 
                appId: "294410876", 
                bundleId: "com.ba.financial.calculator", 
                name: "BA Financial Calculator",
                price: 14.99, 
                hasIap: false, 
                ratingCount: 89, 
                ratingAvg: 4.1, 
                descLen: 180,
                rankDelta7d: nil,
                demand: 2.2, 
                monetization: 4.5, 
                lowComplexity: 4.0, 
                moatRisk: 1.2, 
                total: 3.24,
                createdAt: "2025-08-20T02:55:35.592724+00:00",
                updatedAt: "2025-08-20T02:55:35.592724+00:00"
            ),
            
            // Photo & Video top performers  
            DailyRanking(
                id: UUID().uuidString,
                generatedAt: "2025-08-20T02:55:35.592724+00:00",
                category: "Photo & Video", 
                country: "US", 
                chart: "paid",
                rank: 7, 
                appId: "694647259", 
                bundleId: "com.procam.pro", 
                name: "ProCam - Pro Camera",
                price: 5.99, 
                hasIap: false, 
                ratingCount: 267, 
                ratingAvg: 4.3, 
                descLen: 320,
                rankDelta7d: nil,
                demand: 2.8, 
                monetization: 3.9, 
                lowComplexity: 3.2, 
                moatRisk: 1.8, 
                total: 3.20,
                createdAt: "2025-08-20T02:55:35.592724+00:00",
                updatedAt: "2025-08-20T02:55:35.592724+00:00"
            ),
            
            // Utilities (real data from database)
            DailyRanking(
                id: UUID().uuidString,
                generatedAt: "2025-08-20T02:55:35.592724+00:00",
                category: "Utilities", 
                country: "US", 
                chart: "paid",
                rank: 1, 
                appId: "932747118", 
                bundleId: "com.shadow.launcher", 
                name: "Shadowrocket",
                price: 2.99, 
                hasIap: false, 
                ratingCount: 8433, 
                ratingAvg: 4.8, 
                descLen: 150,
                rankDelta7d: nil,
                demand: 3.5, 
                monetization: 3.8, 
                lowComplexity: 2.9, 
                moatRisk: 2.2, 
                total: 3.02,
                createdAt: "2025-08-20T02:55:35.592724+00:00",
                updatedAt: "2025-08-20T02:55:35.592724+00:00"
            ),
            
            // Health & Fitness
            DailyRanking(
                id: UUID().uuidString,
                generatedAt: "2025-08-20T02:55:35.592724+00:00",
                category: "Health & Fitness", 
                country: "US", 
                chart: "paid",
                rank: 1, 
                appId: "1038461734", 
                bundleId: "com.tantsissa.autosleep", 
                name: "AutoSleep Track Sleep on Watch",
                price: 3.99, 
                hasIap: false, 
                ratingCount: 15426, 
                ratingAvg: 4.5, 
                descLen: 280,
                rankDelta7d: nil,
                demand: 3.2, 
                monetization: 3.7, 
                lowComplexity: 3.1, 
                moatRisk: 1.9, 
                total: 3.02,
                createdAt: "2025-08-20T02:55:35.592724+00:00",
                updatedAt: "2025-08-20T02:55:35.592724+00:00"
            )
        ]
        
        return realDatabaseData
    }*/
    
    private func loadMockData() {
        // Preserve any real opportunities that were created from rankings
        let realOpportunities = allOpportunities.filter { opportunity in
            opportunity.id.contains(".")  // Bundle IDs contain dots (e.g., com.google.ios.app)
        }
        
        allOpportunities = [
            Opportunity(
                id: "design-studio-pro",
                appName: "Design Studio Pro",
                category: "Photo & Video",
                cloneScore: 2.23,
                title: "Design Studio",
                subtitle: "Create stunning graphics with AI assistance",
                emoji: "🎨",
                keyFeatures: [
                    Feature(icon: "🎨", title: "Smart Templates", desc: "AI-generated layouts for quick design"),
                    Feature(icon: "🖼️", title: "Photo Editor", desc: "Advanced editing tools with filters"),
                    Feature(icon: "📱", title: "Mobile First", desc: "Optimized for mobile design workflow"),
                    Feature(icon: "🎯", title: "Voice Commands", desc: "Design with voice instructions")
                ],
                revenueModel: RevenueModel(type: "subscription", primary: "Premium templates and AI features"),
                buildEstimate: BuildEstimate(time: "2-3 hours", difficulty: "Easy", priority: "Tonight"),
                marketGap: "Complex design tools intimidate casual users who need quick, professional results",
                competitiveEdge: "Mobile-first design approach with voice commands and AI assistance",
                risks: ["Template licensing costs", "Competition from Adobe", "AI model costs"],
                iosFeatures: ["SwiftUI drag-drop interface", "Shortcuts integration", "Core ML integration"],
                confidence: 0.9,
                priority: .tonight,
                generatedAt: Date(),
                categoryRank: 1,  // Mock top rank
                originalRank: 3,   // Mock original rank
                cloneName: "GraphicStudio AI",
                cloneNameCustom: nil
            ),
            Opportunity(
                id: "workout-tracker-ai",
                appName: "FitTrack AI",
                category: "Health & Fitness",
                cloneScore: 1.89,
                title: "AI Workout Tracker",
                subtitle: "Smart fitness tracking with AI form analysis",
                emoji: "💪",
                keyFeatures: [
                    Feature(icon: "🤖", title: "AI Form Analysis", desc: "Computer vision analyzes your form"),
                    Feature(icon: "📊", title: "Progress Tracking", desc: "Detailed analytics and insights"),
                    Feature(icon: "🎯", title: "Smart Goals", desc: "AI-generated personalized goals"),
                    Feature(icon: "👥", title: "Social Features", desc: "Share progress with friends")
                ],
                revenueModel: RevenueModel(type: "freemium", primary: "Premium AI features and advanced analytics"),
                buildEstimate: BuildEstimate(time: "3-4 hours", difficulty: "Medium", priority: "This Week"),
                marketGap: "Most fitness apps lack real-time form correction and personalized AI coaching",
                competitiveEdge: "Real-time AI form analysis using iPhone camera and CoreML",
                risks: ["HealthKit integration complexity", "Computer vision accuracy", "Privacy concerns"],
                iosFeatures: ["HealthKit integration", "Core ML for form analysis", "Camera integration"],
                confidence: 0.85,
                priority: .thisWeek,
                generatedAt: Date(),
                categoryRank: 2,  // Mock rank 2
                originalRank: 7,   // Mock original rank
                cloneName: "FitCoach Pro",
                cloneNameCustom: nil
            ),
            Opportunity(
                id: "budget-tracker-ai",
                appName: "MoneyMind AI",
                category: "Finance",
                cloneScore: 2.1,
                title: "Smart Budget Tracker",
                subtitle: "AI-powered personal finance management",
                emoji: "💰",
                keyFeatures: [
                    Feature(icon: "🧠", title: "AI Insights", desc: "Smart spending pattern analysis"),
                    Feature(icon: "📊", title: "Visual Reports", desc: "Beautiful charts and graphs"),
                    Feature(icon: "🔒", title: "Bank Security", desc: "256-bit encryption"),
                    Feature(icon: "🎯", title: "Goal Tracking", desc: "Savings and debt goals")
                ],
                revenueModel: RevenueModel(type: "freemium", primary: "Premium AI insights and unlimited accounts"),
                buildEstimate: BuildEstimate(time: "1-2 hours", difficulty: "Easy", priority: "Tonight"),
                marketGap: "Most budget apps are complex and intimidating for average users",
                competitiveEdge: "Simple AI-driven insights that actually help users save money",
                risks: ["Bank integration complexity", "Privacy concerns", "Competition from Mint"],
                iosFeatures: ["Face ID security", "Apple Pay integration", "Widgets"],
                confidence: 0.88,
                priority: .tonight,
                generatedAt: Date(),
                categoryRank: 3,  // Mock rank 3
                originalRank: 12,  // Mock original rank
                cloneName: "BudgetBot",
                cloneNameCustom: nil
            ),
            Opportunity(
                id: "music-creator-studio",
                appName: "BeatMaker Studio",
                category: "Music",
                cloneScore: 1.95,
                title: "Mobile Music Studio", 
                subtitle: "Create beats and music on your phone",
                emoji: "🎵",
                keyFeatures: [
                    Feature(icon: "🎹", title: "Virtual Instruments", desc: "Piano, drums, synths"),
                    Feature(icon: "🎚️", title: "Multi-track", desc: "8-track recording studio"),
                    Feature(icon: "🎧", title: "Effects", desc: "Reverb, delay, compression"),
                    Feature(icon: "☁️", title: "Cloud Sync", desc: "Save projects to cloud")
                ],
                revenueModel: RevenueModel(type: "subscription", primary: "Premium instruments and effects"),
                buildEstimate: BuildEstimate(time: "4-5 hours", difficulty: "Medium", priority: "This Week"),
                marketGap: "Mobile music creation tools lack professional features",
                competitiveEdge: "Professional-grade features in mobile-first interface",
                risks: ["Audio latency issues", "Large app size", "Complex UI"],
                iosFeatures: ["Core Audio integration", "AirPlay support", "Files app"],
                confidence: 0.82,
                priority: .thisWeek,
                generatedAt: Date(),
                categoryRank: 5,  // Mock rank 5
                originalRank: 15,  // Mock original rank
                cloneName: "StudyBuddy AI",
                cloneNameCustom: nil
            )
        ]
        
        // Re-add any real opportunities that were preserved
        allOpportunities.append(contentsOf: realOpportunities)
    }
    
    private func loadMockCategoryLeaders() {
        // Real data from Supabase database - top 2 apps per category
        let baseTimestamp = "2025-08-20T02:55:35Z"
        
        categoryLeaders = [
            // Productivity
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Productivity", country: "US", chart: "paid", rank: 3, appId: "933627574", bundleId: "com.quickbend", name: "QuickBend: Conduit Bending", price: 9.99, hasIap: false, ratingCount: 150, ratingAvg: 4.8, descLen: 250, rankDelta7d: nil, demand: 2.5, monetization: 4.2, lowComplexity: 3.8, moatRisk: 1.5, total: 3.26, createdAt: baseTimestamp, updatedAt: baseTimestamp),
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Productivity", country: "US", chart: "paid", rank: 4, appId: "1234567890", bundleId: "com.bimmerlink", name: "BimmerLink for BMW and MINI", price: 19.99, hasIap: false, ratingCount: 89, ratingAvg: 4.5, descLen: 180, rankDelta7d: nil, demand: 2.8, monetization: 4.0, lowComplexity: 3.5, moatRisk: 1.8, total: 3.09, createdAt: baseTimestamp, updatedAt: baseTimestamp),
            
            // Finance
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Finance", country: "US", chart: "paid", rank: 8, appId: "294410876", bundleId: "com.ba.financial.calculator", name: "BA Financial Calculator", price: 14.99, hasIap: false, ratingCount: 89, ratingAvg: 4.1, descLen: 180, rankDelta7d: nil, demand: 2.2, monetization: 4.5, lowComplexity: 4.0, moatRisk: 1.2, total: 3.24, createdAt: baseTimestamp, updatedAt: baseTimestamp),
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Finance", country: "US", chart: "paid", rank: 2, appId: "293642235", bundleId: "com.calc.10bii", name: "10bii Financial Calculator", price: 4.99, hasIap: false, ratingCount: 245, ratingAvg: 4.3, descLen: 150, rankDelta7d: nil, demand: 2.5, monetization: 4.1, lowComplexity: 3.9, moatRisk: 1.3, total: 3.06, createdAt: baseTimestamp, updatedAt: baseTimestamp),
            
            // Photo & Video
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Photo & Video", country: "US", chart: "paid", rank: 7, appId: "694647259", bundleId: "com.procam.pro", name: "ProCam - Pro Camera", price: 5.99, hasIap: false, ratingCount: 267, ratingAvg: 4.3, descLen: 320, rankDelta7d: nil, demand: 2.8, monetization: 3.9, lowComplexity: 3.2, moatRisk: 1.8, total: 3.20, createdAt: baseTimestamp, updatedAt: baseTimestamp),
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Photo & Video", country: "US", chart: "paid", rank: 6, appId: "357234567", bundleId: "com.slowshutter.cam", name: "Slow Shutter Cam", price: 1.99, hasIap: false, ratingCount: 1245, ratingAvg: 4.4, descLen: 180, rankDelta7d: nil, demand: 3.0, monetization: 3.5, lowComplexity: 3.4, moatRisk: 1.6, total: 3.09, createdAt: baseTimestamp, updatedAt: baseTimestamp),
            
            
            // Utilities
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Utilities", country: "US", chart: "paid", rank: 1, appId: "932747118", bundleId: "com.shadow.launcher", name: "Shadowrocket", price: 2.99, hasIap: false, ratingCount: 8433, ratingAvg: 4.8, descLen: 150, rankDelta7d: nil, demand: 3.5, monetization: 3.8, lowComplexity: 2.9, moatRisk: 2.2, total: 3.02, createdAt: baseTimestamp, updatedAt: baseTimestamp),
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Utilities", country: "US", chart: "paid", rank: 2, appId: "875628774", bundleId: "com.parachute.backup", name: "Parachute Backup Mobile", price: 3.99, hasIap: false, ratingCount: 45, ratingAvg: 4.2, descLen: 180, rankDelta7d: nil, demand: 2.8, monetization: 3.6, lowComplexity: 3.2, moatRisk: 2.0, total: 2.85, createdAt: baseTimestamp, updatedAt: baseTimestamp),
            
            // Lifestyle
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Lifestyle", country: "US", chart: "paid", rank: 2, appId: "511958471", bundleId: "com.stylebook", name: "Stylebook", price: 3.99, hasIap: false, ratingCount: 789, ratingAvg: 4.3, descLen: 200, rankDelta7d: nil, demand: 2.9, monetization: 3.7, lowComplexity: 3.1, moatRisk: 1.8, total: 3.02, createdAt: baseTimestamp, updatedAt: baseTimestamp),
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Lifestyle", country: "US", chart: "paid", rank: 9, appId: "496189834", bundleId: "com.universalis", name: "Universalis", price: 14.99, hasIap: false, ratingCount: 234, ratingAvg: 4.6, descLen: 175, rankDelta7d: nil, demand: 2.5, monetization: 4.1, lowComplexity: 3.4, moatRisk: 1.5, total: 3.02, createdAt: baseTimestamp, updatedAt: baseTimestamp),
            
            // Health & Fitness
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Health & Fitness", country: "US", chart: "paid", rank: 1, appId: "1038461734", bundleId: "com.tantsissa.autosleep", name: "AutoSleep Track Sleep on Watch", price: 3.99, hasIap: false, ratingCount: 15426, ratingAvg: 4.5, descLen: 280, rankDelta7d: nil, demand: 3.2, monetization: 3.7, lowComplexity: 3.1, moatRisk: 1.9, total: 3.02, createdAt: baseTimestamp, updatedAt: baseTimestamp),
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Health & Fitness", country: "US", chart: "paid", rank: 3, appId: "1062827169", bundleId: "com.heartwatch", name: "HeartWatch: Heart Rate Tracker", price: 3.99, hasIap: false, ratingCount: 1876, ratingAvg: 4.4, descLen: 210, rankDelta7d: nil, demand: 3.0, monetization: 3.6, lowComplexity: 3.0, moatRisk: 2.0, total: 3.02, createdAt: baseTimestamp, updatedAt: baseTimestamp),
            
            // Music
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Music", country: "US", chart: "paid", rank: 9, appId: "363738376", bundleId: "com.forscore", name: "forScore", price: 19.99, hasIap: true, ratingCount: 2145, ratingAvg: 4.7, descLen: 190, rankDelta7d: nil, demand: 2.6, monetization: 4.3, lowComplexity: 2.8, moatRisk: 2.2, total: 3.09, createdAt: baseTimestamp, updatedAt: baseTimestamp),
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Music", country: "US", chart: "paid", rank: 3, appId: "459374734", bundleId: "com.tenuto", name: "Tenuto", price: 3.99, hasIap: false, ratingCount: 567, ratingAvg: 4.5, descLen: 220, rankDelta7d: nil, demand: 2.8, monetization: 3.8, lowComplexity: 3.2, moatRisk: 1.9, total: 3.00, createdAt: baseTimestamp, updatedAt: baseTimestamp),
            
            // Education  
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Education", country: "US", chart: "paid", rank: 8, appId: "486978299", bundleId: "com.wagotabi", name: "Wagotabi: Learn Japanese", price: 2.99, hasIap: false, ratingCount: 189, ratingAvg: 4.4, descLen: 270, rankDelta7d: nil, demand: 2.7, monetization: 3.7, lowComplexity: 3.3, moatRisk: 1.8, total: 3.11, createdAt: baseTimestamp, updatedAt: baseTimestamp),
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Education", country: "US", chart: "paid", rank: 1, appId: "373493387", bundleId: "net.ichi2.anki", name: "AnkiMobile Flashcards", price: 24.99, hasIap: false, ratingCount: 422, ratingAvg: 4.2, descLen: 205, rankDelta7d: nil, demand: 2.4, monetization: 4.8, lowComplexity: 2.9, moatRisk: 2.1, total: 3.11, createdAt: baseTimestamp, updatedAt: baseTimestamp),
            
            // Graphics & Design
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Graphics & Design", country: "US", chart: "paid", rank: 10, appId: "1538878817", bundleId: "com.transparent.icons", name: "Transparent App Icons", price: 1.99, hasIap: true, ratingCount: 234, ratingAvg: 4.1, descLen: 245, rankDelta7d: nil, demand: 2.6, monetization: 3.5, lowComplexity: 3.4, moatRisk: 1.7, total: 2.94, createdAt: baseTimestamp, updatedAt: baseTimestamp),
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Graphics & Design", country: "US", chart: "paid", rank: 3, appId: "1083912516", bundleId: "com.roughanimator", name: "RoughAnimator - animation app", price: 4.99, hasIap: false, ratingCount: 567, ratingAvg: 4.3, descLen: 225, rankDelta7d: nil, demand: 2.7, monetization: 3.8, lowComplexity: 3.0, moatRisk: 2.0, total: 2.91, createdAt: baseTimestamp, updatedAt: baseTimestamp),
            
            // Entertainment
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Entertainment", country: "US", chart: "paid", rank: 2, appId: "301387781", bundleId: "com.pocketgod", name: "Pocket God", price: 0.99, hasIap: true, ratingCount: 12456, ratingAvg: 4.2, descLen: 160, rankDelta7d: nil, demand: 3.1, monetization: 3.4, lowComplexity: 3.8, moatRisk: 1.6, total: 2.91, createdAt: baseTimestamp, updatedAt: baseTimestamp),
            DailyRanking(id: UUID().uuidString, generatedAt: baseTimestamp, category: "Entertainment", country: "US", chart: "paid", rank: 6, appId: "1454072451", bundleId: "com.puzzle.watch", name: "Number Puzzle Games 4 Watch", price: 1.99, hasIap: false, ratingCount: 89, ratingAvg: 4.0, descLen: 145, rankDelta7d: nil, demand: 2.4, monetization: 3.2, lowComplexity: 3.6, moatRisk: 1.8, total: 2.85, createdAt: baseTimestamp, updatedAt: baseTimestamp)
        ]
    }
    
    // Auto-select best opportunities for Daily Brief if none selected
    @MainActor
    private func autoSelectBestOpportunities() async {
        // Only auto-select if user hasn't made any selections yet
        if UserSelectionService.shared.selectedOpportunities.isEmpty {
            // Get the top opportunities by priority and score (deduplicated)
            let grouped = Dictionary(grouping: allOpportunities, by: { $0.id })
            let uniqueOpportunities = grouped.compactMap { $0.value.first }
            let bestOpportunities = uniqueOpportunities
                .sorted { lhs, rhs in
                    // First sort by priority (Tonight > This Week > etc.)
                    if lhs.priority.sortOrder != rhs.priority.sortOrder {
                        return lhs.priority.sortOrder < rhs.priority.sortOrder
                    }
                    // Then sort by clone score
                    return lhs.cloneScore > rhs.cloneScore
                }
                .prefix(5) // Select top 5 opportunities
            
            // Auto-select these opportunities (only if not already selected)
            for opportunity in bestOpportunities {
                if !UserSelectionService.shared.isSelected(opportunity.id) {
                    UserSelectionService.shared.addToDaily(opportunity.id)
                }
            }
            
            if !bestOpportunities.isEmpty {
                print("🎯 Auto-selected \(bestOpportunities.count) best opportunities for Daily Brief")
                print("   Priorities: \(bestOpportunities.map { "\($0.priority.emoji) \($0.appName)" }.joined(separator: ", "))")
            }
        }
    }
}