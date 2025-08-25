import Foundation

struct Opportunity: Identifiable, Codable {
    let id: String
    let appName: String
    let category: String
    let cloneScore: Double
    let title: String
    let subtitle: String
    let emoji: String
    let keyFeatures: [Feature]
    let revenueModel: RevenueModel
    let buildEstimate: BuildEstimate
    let marketGap: String
    let competitiveEdge: String
    let risks: [String]
    let iosFeatures: [String]
    let confidence: Double
    let priority: Priority
    let generatedAt: Date?
    
    // NEW: For top-3 highlighting (Phase 2)
    let categoryRank: Int?
    let originalRank: Int? // App Store rank for reference
    
    // NEW: Clone name fields for display system
    let cloneName: String?
    let cloneNameCustom: String?
    
    enum CodingKeys: String, CodingKey {
        case id, appName = "app_name", category, cloneScore = "clone_score"
        case title, subtitle, emoji, keyFeatures = "key_features"
        case revenueModel = "revenue_model", buildEstimate = "build_estimate"
        case marketGap = "market_gap", competitiveEdge = "competitive_edge"
        case risks, iosFeatures = "ios_features", confidence, priority
        case generatedAt = "generated_at"
        case categoryRank = "category_rank", originalRank = "original_rank"
        case cloneName = "clone_name", cloneNameCustom = "clone_name_custom"
    }
    
    // MARK: - Clone Name Display Logic
    
    /// The display name to show in the UI with smart fallback logic:
    /// 1. Custom clone name (user-edited)
    /// 2. AI-generated clone name  
    /// 3. Original app name (fallback)
    var displayName: String {
        if let customName = cloneNameCustom, !customName.isEmpty {
            return customName
        }
        
        if let cloneName = cloneName, !cloneName.isEmpty {
            return cloneName
        }
        
        return appName
    }
    
    /// Whether this opportunity has any AI-generated clone name available
    var hasCloneName: Bool {
        return (cloneName != nil && !cloneName!.isEmpty) || (cloneNameCustom != nil && !cloneNameCustom!.isEmpty)
    }
    
    /// Returns the type of name being displayed
    var displayNameType: CloneNameType {
        if let customName = cloneNameCustom, !customName.isEmpty {
            return .userCustom
        }
        
        if let cloneName = cloneName, !cloneName.isEmpty {
            return .aiGenerated
        }
        
        return .original
    }
}

enum CloneNameType {
    case userCustom    // User edited the clone name
    case aiGenerated   // AI-generated clone name
    case original      // Original app name (fallback)
    
    var badgeText: String {
        switch self {
        case .userCustom: return "Custom"
        case .aiGenerated: return "AI"
        case .original: return ""
        }
    }
    
    var badgeColor: String {
        switch self {
        case .userCustom: return "purple"
        case .aiGenerated: return "blue"
        case .original: return "gray"
        }
    }
}

struct Feature: Identifiable, Codable {
    let id = UUID()
    let icon: String
    let title: String
    let desc: String
    
    enum CodingKeys: String, CodingKey {
        case icon, title, desc
    }
}

struct RevenueModel: Codable {
    let type: String
    let primary: String
}

struct BuildEstimate: Codable {
    let time: String
    let difficulty: String
    let priority: String
}

enum Priority: String, Codable, CaseIterable {
    case tonight = "TONIGHT"
    case thisWeek = "THIS_WEEK"
    case thisMonth = "THIS_MONTH" 
    case future = "FUTURE"
    
    var sortOrder: Int {
        switch self {
        case .tonight: return 0
        case .thisWeek: return 1
        case .thisMonth: return 2
        case .future: return 3
        }
    }
    
    var emoji: String {
        switch self {
        case .tonight: return "🌙"
        case .thisWeek: return "📅"
        case .thisMonth: return "📆"
        case .future: return "⏳"
        }
    }
    
    var color: String {
        switch self {
        case .tonight: return "red"
        case .thisWeek: return "orange"
        case .thisMonth: return "blue"
        case .future: return "gray"
        }
    }
    
    var displayName: String {
        switch self {
        case .tonight: return "Tonight"
        case .thisWeek: return "This Week"
        case .thisMonth: return "This Month"
        case .future: return "Future"
        }
    }
}

struct DailyRanking: Identifiable, Codable {
    let id: String  // Changed from Int to String to match UUID
    let generatedAt: String  // Changed from date to match database
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
    let rankDelta7d: Int?  // Added to match database
    let demand: Double?
    let monetization: Double?
    let lowComplexity: Double?
    let moatRisk: Double?
    let total: Double?
    let createdAt: String?  // Added to match database
    let updatedAt: String?  // Added to match database
    
    enum CodingKeys: String, CodingKey {
        case id, category, country, chart, rank
        case appId = "app_id", bundleId = "bundle_id", name, price
        case hasIap = "has_iap", ratingCount = "rating_count"
        case ratingAvg = "rating_avg", descLen = "desc_len"
        case rankDelta7d = "rank_delta7d"
        case demand, monetization, lowComplexity = "low_complexity"
        case moatRisk = "moat_risk", total
        case createdAt = "created_at", updatedAt = "updated_at"
        case generatedAt = "generated_at"
    }
    
    // Computed properties for backward compatibility
    var date: String { generatedAt }
    var cloneDifficulty: Double? { lowComplexity }
    var revenuePotential: Double? { 
        // Calculate revenue potential based on rank and ratings
        guard let count = ratingCount, let avg = ratingAvg else { return nil }
        let baseScore = Double(count) / 10000.0 * avg / 5.0
        let rankBonus = max(0, (51 - Double(rank)) / 50.0)
        return min(10.0, baseScore + rankBonus * 3.0)
    }
    var categoryRank: Int? { rank }
    var aiRecommendation: String? { nil }
    var recommendationGeneratedAt: Date? { 
        guard let createdAt = createdAt else { return nil }
        return ISO8601DateFormatter().date(from: createdAt)
    }
}