import SwiftUI

// MARK: - AI Difficulty Badge
struct AIDifficultyBadge: View {
    let difficulty: CloneDifficulty?
    
    var body: some View {
        if let difficulty = difficulty {
            HStack(spacing: 4) {
                Text(difficulty.emoji)
                    .font(.caption2)
                Text(difficulty.displayName)
                    .font(.caption2)
                    .fontWeight(.medium)
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(backgroundColorForDifficulty(difficulty))
            .foregroundColor(textColorForDifficulty(difficulty))
            .cornerRadius(6)
        }
    }
    
    private func backgroundColorForDifficulty(_ difficulty: CloneDifficulty) -> Color {
        switch difficulty {
        case .easyClone: return .green.opacity(0.2)
        case .mediumClone: return .orange.opacity(0.2)
        case .moderate: return .yellow.opacity(0.2)
        case .hardClone: return .red.opacity(0.2)
        case .complex: return .purple.opacity(0.2)
        }
    }
    
    private func textColorForDifficulty(_ difficulty: CloneDifficulty) -> Color {
        switch difficulty {
        case .easyClone: return .green
        case .mediumClone: return .orange
        case .moderate: return .yellow
        case .hardClone: return .red
        case .complex: return .purple
        }
    }
}

// MARK: - AI Revenue Potential Badge
struct AIRevenueBadge: View {
    let potential: RevenuePotential?
    
    var body: some View {
        if let potential = potential {
            HStack(spacing: 4) {
                Text(potential.emoji)
                    .font(.caption2)
                Text(potential.displayName)
                    .font(.caption2)
                    .fontWeight(.medium)
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(backgroundColorForRevenue(potential))
            .foregroundColor(textColorForRevenue(potential))
            .cornerRadius(6)
        }
    }
    
    private func backgroundColorForRevenue(_ potential: RevenuePotential) -> Color {
        switch potential {
        case .highRevenue: return .purple.opacity(0.2)  // Purple for very high revenue
        case .goodRevenue: return .green.opacity(0.2)
        case .modestRevenue: return .blue.opacity(0.2)
        case .lowRevenue: return .gray.opacity(0.2)
        }
    }
    
    private func textColorForRevenue(_ potential: RevenuePotential) -> Color {
        switch potential {
        case .highRevenue: return .purple
        case .goodRevenue: return .green
        case .modestRevenue: return .blue
        case .lowRevenue: return .gray
        }
    }
}

// MARK: - AI Priority Badge  
struct AIPriorityBadge: View {
    let priority: Priority
    
    var body: some View {
        HStack(spacing: 4) {
            Text(priority.emoji)
                .font(.caption2)
            Text(priority.rawValue)
                .font(.caption2)
                .fontWeight(.semibold)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(backgroundColorForPriority(priority))
        .foregroundColor(textColorForPriority(priority))
        .cornerRadius(6)
    }
    
    private func backgroundColorForPriority(_ priority: Priority) -> Color {
        switch priority {
        case .tonight: return .orange.opacity(0.2)
        case .thisWeek: return .blue.opacity(0.2)
        case .thisMonth: return .green.opacity(0.2)
        case .future: return .gray.opacity(0.2)
        }
    }
    
    private func textColorForPriority(_ priority: Priority) -> Color {
        switch priority {
        case .tonight: return .orange
        case .thisWeek: return .blue
        case .thisMonth: return .green
        case .future: return .gray
        }
    }
}

// MARK: - AI Enhancement Indicator
struct AIEnhancementIndicator: View {
    let isEnhanced: Bool
    
    var body: some View {
        if isEnhanced {
            HStack(spacing: 3) {
                Image(systemName: "sparkles")
                    .font(.caption2)
                Text("AI Enhanced")
                    .font(.caption2)
                    .fontWeight(.medium)
            }
            .foregroundColor(.purple)
            .padding(.horizontal, 6)
            .padding(.vertical, 3)
            .background(Color.purple.opacity(0.1))
            .cornerRadius(4)
        }
    }
}

// MARK: - Enhanced Opportunity Card (with AI indicators)
struct EnhancedOpportunityRankingCard: View {
    let ranking: EnhancedDailyRanking
    let isSelected: Bool
    let onToggleSelection: () -> Void
    var onTap: (() -> Void)? = nil
    
    var body: some View {
        Button(action: onTap ?? {}) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("#\(ranking.rank)")
                        .font(.headline)
                        .fontWeight(.bold)
                        .foregroundColor(.blue)
                    
                    VStack(alignment: .leading, spacing: 2) {
                        Text(ranking.name)
                            .font(.headline)
                            .fontWeight(.semibold)
                            .lineLimit(1)
                        
                        if let bundleId = ranking.bundleId.split(separator: ".").last {
                            Text(String(bundleId))
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    Spacer()
                    
                    VStack(alignment: .trailing, spacing: 8) {
                        Button(action: onToggleSelection) {
                            Image(systemName: isSelected ? "checkmark.circle.fill" : "plus.circle")
                                .font(.title2)
                                .foregroundColor(isSelected ? .green : .blue)
                        }
                        .buttonStyle(BorderlessButtonStyle())
                        
                        VStack(alignment: .trailing, spacing: 2) {
                            // AI-Enhanced Score
                            HStack(spacing: 4) {
                                Image(systemName: "star.fill")
                                    .foregroundColor(.yellow)
                                    .font(.caption)
                                Text(String(format: "%.1f", ranking.enhancedScore))
                                    .font(.caption)
                                    .fontWeight(.medium)
                            }
                            
                            if let price = ranking.price {
                                Text(price > 0 ? "$\(String(format: "%.2f", price))" : "Free")
                                    .font(.caption2)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                }
                
                // AI Enhancement Badges
                HStack(spacing: 8) {
                    AIEnhancementIndicator(isEnhanced: ranking.aiRecommendation != nil)
                    
                    AIDifficultyBadge(difficulty: ranking.cloneDifficulty)
                    
                    AIRevenueBadge(potential: ranking.revenuePotential)
                    
                    Spacer()
                }
                
                // Basic info row
                HStack {
                    if let ratingCount = ranking.ratingCount, ratingCount > 0 {
                        Label("\(ratingCount)", systemImage: "person.2")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                    
                    if let ratingAvg = ranking.ratingAvg {
                        Label(String(format: "%.1f", ratingAvg), systemImage: "star")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    AIPriorityBadge(priority: ranking.intelligentPriority)
                }
            }
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(12)
            .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
            .overlay(
                // Special border for tonight priorities
                RoundedRectangle(cornerRadius: 12)
                    .stroke(ranking.intelligentPriority == .tonight ? Color.orange : Color.clear, lineWidth: 2)
            )
        }
        .buttonStyle(PlainButtonStyle())
        .disabled(onTap == nil)
    }
}

// MARK: - Enhanced Category Card (with AI stats)
struct EnhancedCategoryCard: View {
    let name: String
    let icon: String
    let emoji: String
    let enhancedLeaders: [EnhancedDailyRanking]
    let onTap: () -> Void
    
    var topApp: EnhancedDailyRanking? {
        enhancedLeaders.first
    }
    
    var aiStats: (enhanced: Int, easyClone: Int, tonight: Int) {
        let enhanced = enhancedLeaders.filter { $0.aiRecommendation != nil }.count
        let easyClone = enhancedLeaders.filter { $0.cloneDifficulty == .easyClone }.count  
        let tonight = enhancedLeaders.filter { $0.intelligentPriority == .tonight }.count
        return (enhanced, easyClone, tonight)
    }
    
    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Text(emoji)
                        .font(.title)
                    
                    VStack(alignment: .leading, spacing: 2) {
                        Text(name)
                            .font(.headline)
                            .fontWeight(.semibold)
                            .foregroundColor(.primary)
                        
                        HStack(spacing: 4) {
                            Text("\(enhancedLeaders.count) opportunities")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            
                            if aiStats.enhanced > 0 {
                                Image(systemName: "sparkles")
                                    .font(.caption2)
                                    .foregroundColor(.purple)
                            }
                        }
                    }
                    
                    Spacer()
                    
                    Image(systemName: "chevron.right")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                if let topApp = topApp {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Top Opportunity:")
                            .font(.caption2)
                            .fontWeight(.medium)
                            .foregroundColor(.secondary)
                        
                        Text(topApp.name)
                            .font(.caption)
                            .fontWeight(.medium)
                            .lineLimit(1)
                            .foregroundColor(.primary)
                        
                        HStack(spacing: 8) {
                            // Enhanced AI score
                            HStack(spacing: 2) {
                                Image(systemName: "star.fill")
                                    .font(.caption2)
                                    .foregroundColor(.yellow)
                                Text(String(format: "%.1f", topApp.enhancedScore))
                                    .font(.caption2)
                                    .fontWeight(.medium)
                            }
                            
                            // AI Indicators
                            if let difficulty = topApp.cloneDifficulty {
                                Text(difficulty.emoji)
                                    .font(.caption2)
                            }
                            
                            if topApp.intelligentPriority == .tonight {
                                Text("🌙")
                                    .font(.caption2)
                            }
                        }
                    }
                    .padding(.top, 4)
                }
                
                // AI Stats Summary
                if aiStats.enhanced > 0 || aiStats.easyClone > 0 || aiStats.tonight > 0 {
                    HStack(spacing: 8) {
                        if aiStats.enhanced > 0 {
                            Label("\(aiStats.enhanced)", systemImage: "sparkles")
                                .font(.caption2)
                                .foregroundColor(.purple)
                        }
                        
                        if aiStats.easyClone > 0 {
                            Label("\(aiStats.easyClone)", systemImage: "bolt.fill")
                                .font(.caption2)
                                .foregroundColor(.green)
                        }
                        
                        if aiStats.tonight > 0 {
                            Label("\(aiStats.tonight)", systemImage: "moon.fill")
                                .font(.caption2)
                                .foregroundColor(.orange)
                        }
                    }
                    .padding(.top, 2)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(12)
            .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
            .overlay(
                // Special highlight for categories with tonight priorities
                RoundedRectangle(cornerRadius: 12)
                    .stroke(aiStats.tonight > 0 ? Color.orange.opacity(0.3) : Color.clear, lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
    }
}