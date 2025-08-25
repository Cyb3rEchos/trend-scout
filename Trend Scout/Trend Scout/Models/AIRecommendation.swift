import Foundation

// MARK: - AI Recommendation Models

struct AIRecommendation: Codable {
    let title: String?
    let subtitle: String?
    let emoji: String?
    let cloneScore: Double?
    let keyFeatures: [AIFeature]?
    let revenueModel: AIRevenueModel?
    let buildEstimate: AIBuildEstimate?
    let iosFeatures: [String]?
    let marketGap: String?
    let competitiveEdge: String?
    let risks: [String]?
    let confidence: Double?
    let improvement: String?
    
    enum CodingKeys: String, CodingKey {
        case title, subtitle, emoji
        case cloneScore = "clone_score"
        case keyFeatures = "key_features"
        case revenueModel = "revenue_model"
        case buildEstimate = "build_estimate"
        case iosFeatures = "ios_features"
        case marketGap = "market_gap"
        case competitiveEdge = "competitive_edge"
        case risks, confidence, improvement
    }
}

struct AIFeature: Codable, Identifiable {
    let id = UUID()
    let icon: String
    let title: String
    let desc: String
    
    enum CodingKeys: String, CodingKey {
        case icon, title, desc
    }
}

struct AIRevenueModel: Codable {
    let type: String
    let primary: String
}

struct AIBuildEstimate: Codable {
    let time: String
    let difficulty: String
    let priority: String
}

// MARK: - Enhanced Daily Ranking Model

struct EnhancedDailyRanking: Identifiable, Codable {
    let id: String
    let date: String
    let category: String
    let country: String
    let chart: String
    let rank: Int
    let appId: String
    let bundleId: String
    let name: String
    let price: Double?
    let hasIap: Bool
    let ratingCount: Int?
    let ratingAvg: Double?
    let descLen: Int?
    let demand: Double?
    let monetization: Double?
    let lowComplexity: Double?
    let moatRisk: Double?
    let total: Double?
    let cloneDifficulty: CloneDifficulty?
    let revenuePotential: RevenuePotential?
    let categoryRank: Int?
    let aiRecommendationRaw: String?
    let recommendationGeneratedAt: String?
    
    // NEW FIELDS for perfect alignment:
    let cloneName: String?
    let cloneNameCustom: String?
    let buildPriority: String?
    
    let createdAt: String?
    let updatedAt: String?
    
    // Parsed AI recommendation
    var aiRecommendation: AIRecommendation? {
        guard let rawJson = aiRecommendationRaw else { return nil }
        return parseAIRecommendation(from: rawJson)
    }
    
    // Intelligent priority based on database field first, then AI analysis
    var intelligentPriority: Priority {
        // Use database build_priority if available
        if let buildPriorityString = buildPriority,
           let priority = Priority(rawValue: buildPriorityString) {
            return priority
        }
        
        // Fallback to AI-based calculation
        guard let difficulty = cloneDifficulty,
              let revenue = revenuePotential else {
            return .future
        }
        
        switch (difficulty, revenue) {
        case (.easyClone, .highRevenue),
             (.easyClone, .goodRevenue):
            return .tonight
        case (.easyClone, .modestRevenue):
            return .tonight
        case (.mediumClone, .highRevenue),
             (.mediumClone, .goodRevenue),
             (.moderate, .highRevenue),
             (.moderate, .goodRevenue):
            return .thisWeek
        case (.easyClone, .lowRevenue),
             (.mediumClone, .modestRevenue),
             (.moderate, .modestRevenue):
            return .thisWeek
        default:
            return .future
        }
    }
    
    // AI-enhanced opportunity score
    var enhancedScore: Double {
        let baseScore = total ?? 0.0
        
        // Boost score based on AI factors
        var aiBonus = 0.0
        
        if let difficulty = cloneDifficulty {
            switch difficulty {
            case .easyClone: aiBonus += 0.5
            case .mediumClone: aiBonus += 0.2
            case .moderate: aiBonus += 0.1  // Moderate difficulty gets small bonus
            case .hardClone: aiBonus -= 0.2
            case .complex: aiBonus -= 0.4  // Complex gets biggest penalty
            }
        }
        
        if let revenue = revenuePotential {
            switch revenue {
            case .highRevenue: aiBonus += 0.5  // Highest bonus for high revenue
            case .goodRevenue: aiBonus += 0.3
            case .modestRevenue: aiBonus += 0.1
            case .lowRevenue: aiBonus -= 0.1
            }
        }
        
        return baseScore + aiBonus
    }
    
    enum CodingKeys: String, CodingKey {
        case id, date, category, country, chart, rank
        case appId = "app_id", bundleId = "bundle_id", name, price
        case hasIap = "has_iap", ratingCount = "rating_count"
        case ratingAvg = "rating_avg", descLen = "desc_len"
        case demand, monetization, lowComplexity = "low_complexity"
        case moatRisk = "moat_risk", total
        case cloneDifficulty = "clone_difficulty"
        case revenuePotential = "revenue_potential"
        case categoryRank = "category_rank"
        case aiRecommendationRaw = "ai_recommendation"
        case recommendationGeneratedAt = "recommendation_generated_at"
        
        // NEW FIELDS for perfect alignment:
        case cloneName = "clone_name"
        case cloneNameCustom = "clone_name_custom"
        case buildPriority = "build_priority"
        
        case createdAt = "created_at", updatedAt = "updated_at"
    }
}

// MARK: - AI Classification Enums

enum CloneDifficulty: String, Codable, CaseIterable {
    case easyClone = "EASY_CLONE"
    case mediumClone = "MEDIUM_CLONE"
    case hardClone = "HARD_CLONE"
    case moderate = "MODERATE"  // Added to match database values
    case complex = "COMPLEX"  // Added to match database values
    
    var displayName: String {
        switch self {
        case .easyClone: return "Easy"
        case .mediumClone: return "Medium"
        case .hardClone: return "Hard"
        case .moderate: return "Moderate"
        case .complex: return "Complex"
        }
    }
    
    var emoji: String {
        switch self {
        case .easyClone: return "🟢"
        case .mediumClone: return "🟡"
        case .hardClone: return "🔴"
        case .moderate: return "🟠"  // Orange for moderate
        case .complex: return "🟣"  // Purple for complex
        }
    }
}

enum RevenuePotential: String, Codable, CaseIterable {
    case highRevenue = "HIGH_REVENUE"  // Added to match database
    case goodRevenue = "GOOD_REVENUE"
    case modestRevenue = "MODEST_REVENUE"
    case lowRevenue = "LOW_REVENUE"
    
    var displayName: String {
        switch self {
        case .highRevenue: return "Very High Revenue"
        case .goodRevenue: return "High Revenue"
        case .modestRevenue: return "Modest Revenue"
        case .lowRevenue: return "Low Revenue"
        }
    }
    
    var emoji: String {
        switch self {
        case .highRevenue: return "💎"  // Diamond for very high revenue
        case .goodRevenue: return "💰"
        case .modestRevenue: return "💵"
        case .lowRevenue: return "🪙"
        }
    }
}

// MARK: - AI Recommendation Parser

private func parseAIRecommendation(from text: String) -> AIRecommendation? {
    // Handle different AI recommendation formats
    
    // First try parsing as JSON
    if let data = text.data(using: .utf8) {
        do {
            let recommendation = try JSONDecoder().decode(AIRecommendation.self, from: data)
            return recommendation
        } catch {
            // Not valid JSON, continue to text parsing
        }
    }
    
    // Parse as structured text (the actual format from database)
    if text.contains("IMPROVEMENT:") {
        // Extract structured information from the text
        let components = text.components(separatedBy: "\n")
        var improvement: String?
        var features: String?
        var monetization: String?
        var buildTime: String?
        var marketGap: String?
        var risks: String?
        
        for component in components {
            let trimmed = component.trimmingCharacters(in: .whitespaces)
            if trimmed.hasPrefix("IMPROVEMENT:") {
                improvement = String(trimmed.dropFirst("IMPROVEMENT:".count)).trimmingCharacters(in: .whitespaces)
            } else if trimmed.hasPrefix("FEATURES:") {
                features = String(trimmed.dropFirst("FEATURES:".count)).trimmingCharacters(in: .whitespaces)
            } else if trimmed.hasPrefix("MONETIZATION:") {
                monetization = String(trimmed.dropFirst("MONETIZATION:".count)).trimmingCharacters(in: .whitespaces)
            } else if trimmed.hasPrefix("BUILD_TIME:") {
                buildTime = String(trimmed.dropFirst("BUILD_TIME:".count)).trimmingCharacters(in: .whitespaces)
            } else if trimmed.hasPrefix("MARKET_GAP:") {
                marketGap = String(trimmed.dropFirst("MARKET_GAP:".count)).trimmingCharacters(in: .whitespaces)
            } else if trimmed.hasPrefix("RISKS:") {
                risks = String(trimmed.dropFirst("RISKS:".count)).trimmingCharacters(in: .whitespaces)
            }
        }
        
        // Parse build time for structured estimate
        var buildEstimate: AIBuildEstimate?
        if let buildTime = buildTime {
            let difficulty = buildTime.contains("3–4 hours") || buildTime.contains("3-4 hours") ? "Easy" : "Medium"
            buildEstimate = AIBuildEstimate(
                time: buildTime.components(separatedBy: "–").first?.trimmingCharacters(in: .whitespaces) ?? "2-4 hours",
                difficulty: difficulty,
                priority: difficulty == "Easy" ? "Tonight" : "This Week"
            )
        }
        
        // Parse monetization for revenue model  
        var revenueModel: AIRevenueModel?
        if let monetization = monetization {
            let type = monetization.lowercased().contains("freemium") ? "freemium" : "paid"
            revenueModel = AIRevenueModel(type: type, primary: monetization)
        }
        
        return AIRecommendation(
            title: nil, // Will be generated from app name
            subtitle: improvement, // Use improvement as subtitle
            emoji: nil, // Will use category emoji
            cloneScore: nil,
            keyFeatures: features != nil ? [AIFeature(icon: "⚡", title: "Key Features", desc: features!)] : nil,
            revenueModel: revenueModel,
            buildEstimate: buildEstimate,
            iosFeatures: nil,
            marketGap: marketGap,
            competitiveEdge: features,
            risks: risks != nil ? [risks!] : nil,
            confidence: nil,
            improvement: improvement
        )
    }
    
    // Fallback: treat entire text as improvement
    return AIRecommendation(
        title: nil,
        subtitle: nil,
        emoji: nil,
        cloneScore: nil,
        keyFeatures: nil,
        revenueModel: nil,
        buildEstimate: nil,
        iosFeatures: nil,
        marketGap: nil,
        competitiveEdge: nil,
        risks: nil,
        confidence: nil,
        improvement: text
    )
}

// MARK: - Enhanced Opportunity Creation

extension EnhancedDailyRanking {
    func toOpportunity() -> Opportunity {
        let recommendation = self.aiRecommendation
        
        // Generate category emoji
        let categoryEmoji = getCategoryEmoji(category)
        
        // Use AI data when available, fall back to generated content
        let opportunityTitle = recommendation?.title ?? generateTitle()
        let opportunitySubtitle = recommendation?.subtitle ?? generateSubtitle()
        let opportunityEmoji = recommendation?.emoji ?? categoryEmoji
        
        // Create features from AI or generate basic ones
        let features = recommendation?.keyFeatures?.map { aiFeature in
            Feature(
                icon: aiFeature.icon,
                title: aiFeature.title,
                desc: aiFeature.desc
            )
        } ?? generateBasicFeatures()
        
        // Create revenue model from AI or basic one
        let revenueModel = RevenueModel(
            type: recommendation?.revenueModel?.type ?? (hasIap ? "freemium" : "paid"),
            primary: recommendation?.revenueModel?.primary ?? (hasIap ? "In-app purchases" : "One-time purchase")
        )
        
        // Create build estimate from AI or basic one
        let buildEstimate = BuildEstimate(
            time: recommendation?.buildEstimate?.time ?? estimatedBuildTime(),
            difficulty: recommendation?.buildEstimate?.difficulty ?? cloneDifficulty?.displayName ?? "Medium",
            priority: intelligentPriority.rawValue.capitalized
        )
        
        return Opportunity(
            id: bundleId,
            appName: name,
            category: category,
            cloneScore: enhancedScore,
            title: opportunityTitle,
            subtitle: opportunitySubtitle,
            emoji: opportunityEmoji,
            keyFeatures: features,
            revenueModel: revenueModel,
            buildEstimate: buildEstimate,
            marketGap: recommendation?.marketGap ?? generateMarketGap(),
            competitiveEdge: recommendation?.competitiveEdge ?? generateCompetitiveEdge(),
            risks: recommendation?.risks ?? generateRisks(),
            iosFeatures: recommendation?.iosFeatures ?? generateIOSFeatures(),
            confidence: recommendation?.confidence ?? calculateConfidence(),
            priority: intelligentPriority,
            generatedAt: Date(),
            
            // NEW: Phase 2 ranking data for top-3 highlighting
            categoryRank: categoryRank,
            originalRank: rank,
            
            // NEW: Clone name fields for display system
            cloneName: cloneName,
            cloneNameCustom: cloneNameCustom
        )
    }
    
    private func generateTitle() -> String {
        let baseName = name.components(separatedBy: " - ").first ?? name
        return "\(baseName) Clone"
    }
    
    private func generateSubtitle() -> String {
        return "AI-optimized \(category.lowercased()) app with enhanced features"
    }
    
    private func generateBasicFeatures() -> [Feature] {
        var features: [Feature] = []
        
        if hasIap {
            features.append(Feature(icon: "💰", title: "Monetized", desc: "In-app purchases available"))
        }
        
        if let count = ratingCount, count > 1000 {
            features.append(Feature(icon: "⭐", title: "Popular", desc: "\(count) user ratings"))
        }
        
        if rank <= 5 {
            features.append(Feature(icon: "🏆", title: "Top Ranked", desc: "Top 5 in category"))
        }
        
        features.append(Feature(icon: "📱", title: "Mobile First", desc: "Optimized for iOS"))
        
        return features
    }
    
    private func generateMarketGap() -> String {
        return "Market opportunity identified through AI analysis of \(category) category trends and user needs."
    }
    
    private func generateCompetitiveEdge() -> String {
        let ratingText = ratingCount ?? 0 > 0 ? " with \(String(format: "%.1f", ratingAvg ?? 0)) star rating" : ""
        return "Proven concept with \(ratingCount ?? 0) user ratings\(ratingText) and strong market position."
    }
    
    private func generateRisks() -> [String] {
        var risks = ["Market competition", "User acquisition costs"]
        
        if cloneDifficulty == .hardClone {
            risks.append("Technical complexity")
        }
        
        if revenuePotential == .lowRevenue {
            risks.append("Limited revenue potential")
        }
        
        return risks
    }
    
    private func generateIOSFeatures() -> [String] {
        var features = ["Native iOS integration", "SwiftUI interface"]
        
        if category == "Health & Fitness" {
            features.append("HealthKit integration")
        }
        
        if category == "Photo & Video" {
            features.append("Camera integration")
            features.append("Core Image processing")
        }
        
        return features
    }
    
    private func calculateConfidence() -> Double {
        var confidence = 0.5
        
        // Boost confidence for easy clones
        if cloneDifficulty == .easyClone {
            confidence += 0.3
        }
        
        // Boost for high revenue potential
        if revenuePotential == .highRevenue {
            confidence += 0.3
        } else if revenuePotential == .goodRevenue {
            confidence += 0.2
        }
        
        // Boost for high rating
        if let avg = ratingAvg, avg >= 4.0 {
            confidence += 0.1
        }
        
        return min(1.0, confidence)
    }
    
    private func estimatedBuildTime() -> String {
        guard let difficulty = cloneDifficulty else { return "2-4 hours" }
        
        switch difficulty {
        case .easyClone: return "2-3 hours"
        case .mediumClone: return "3-6 hours"
        case .moderate: return "4-8 hours"
        case .hardClone: return "1-2 days"
        case .complex: return "3-5 days"
        }
    }
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