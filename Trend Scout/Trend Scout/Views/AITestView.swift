import SwiftUI

struct AITestView: View {
    @StateObject private var supabaseManager = SupabaseManager.shared
    @State private var enhancedRankings: [EnhancedDailyRanking] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var testResults: String = "Tap 'Test AI Features' to begin"
    
    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                Text("🤖 AI Features Test")
                    .font(.largeTitle)
                    .bold()
                
                // Test button
                Button(action: testAIFeatures) {
                    HStack {
                        if isLoading {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle())
                                .scaleEffect(0.8)
                        } else {
                            Image(systemName: "sparkles")
                        }
                        Text(isLoading ? "Testing AI..." : "Test AI Features")
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.purple)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                }
                .disabled(isLoading)
                
                // Results
                VStack(alignment: .leading, spacing: 10) {
                    Text("AI Test Results:")
                        .font(.headline)
                    
                    Text(testResults)
                        .font(.system(.body, design: .monospaced))
                        .padding()
                        .background(Color.gray.opacity(0.1))
                        .cornerRadius(8)
                }
                
                // AI-Enhanced Rankings Display
                if !enhancedRankings.isEmpty {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("🚀 AI-Enhanced Opportunities:")
                            .font(.headline)
                        
                        ForEach(enhancedRankings.prefix(5), id: \.id) { ranking in
                            EnhancedOpportunityRankingCard(
                                ranking: ranking,
                                isSelected: false,
                                onToggleSelection: {},
                                onTap: nil
                            )
                        }
                    }
                }
                
                // AI Stats Summary
                if !enhancedRankings.isEmpty {
                    AIStatsSummary(rankings: enhancedRankings)
                }
            }
            .padding()
        }
    }
    
    private func testAIFeatures() {
        isLoading = true
        testResults = "🔄 Testing AI features...\n"
        errorMessage = nil
        
        Task {
            // Test 1: Fetch AI-enhanced data
            testResults += "\n🤖 Test 1: Fetching AI-enhanced data from daily_rankings..."
            do {
                let rankings = try await supabaseManager.fetchEnhancedRankings(limit: 20, forceRefresh: true)
                enhancedRankings = rankings
                testResults += "\n✅ Success! Found \(rankings.count) AI-enhanced rankings"
                
                // Analyze AI content
                let withAI = rankings.filter { $0.aiRecommendation != nil }.count
                let easyClones = rankings.filter { $0.cloneDifficulty == .easyClone }.count
                let tonightPriority = rankings.filter { $0.intelligentPriority == .tonight }.count
                
                testResults += "\n   📊 AI Analysis:"
                testResults += "\n   - \(withAI) apps have AI recommendations"
                testResults += "\n   - \(easyClones) apps are easy to clone"
                testResults += "\n   - \(tonightPriority) apps prioritized for tonight"
                
                // Test 2: AI Recommendation Parsing
                testResults += "\n\n🧠 Test 2: Testing AI recommendation parsing..."
                var parsedCount = 0
                for ranking in rankings {
                    if let ai = ranking.aiRecommendation {
                        parsedCount += 1
                        if parsedCount == 1 {
                            testResults += "\n✅ Sample AI recommendation found:"
                            if let title = ai.title {
                                testResults += "\n   Title: \(title)"
                            }
                            if let improvement = ai.improvement {
                                let shortImprovement = String(improvement.prefix(50)) + "..."
                                testResults += "\n   Improvement: \(shortImprovement)"
                            }
                        }
                    }
                }
                testResults += "\n✅ Parsed \(parsedCount) AI recommendations successfully!"
                
                // Test 3: Opportunity Conversion
                testResults += "\n\n🎯 Test 3: Converting to opportunities..."
                let opportunities = rankings.map { $0.toOpportunity() }
                let aiEnhancedOpps = opportunities.filter { opp in
                    // Check if opportunity has AI-derived content
                    return rankings.first(where: { $0.bundleId == opp.id })?.aiRecommendation != nil
                }
                testResults += "\n✅ Created \(opportunities.count) opportunities"
                testResults += "\n   - \(aiEnhancedOpps.count) are AI-enhanced"
                
                // Test 4: Priority Intelligence
                testResults += "\n\n🌙 Test 4: Testing intelligent prioritization..."
                let priorityCounts = Dictionary(grouping: opportunities, by: { $0.priority })
                    .mapValues { $0.count }
                
                for priority in Priority.allCases {
                    let count = priorityCounts[priority] ?? 0
                    testResults += "\n   \(priority.emoji) \(priority.rawValue): \(count) apps"
                }
                
            } catch {
                testResults += "\n❌ Failed: \(error.localizedDescription)"
                errorMessage = error.localizedDescription
            }
            
            testResults += "\n\n" + String(repeating: "=", count: 40)
            testResults += "\n🎉 AI Testing Complete!"
            
            if enhancedRankings.isEmpty {
                testResults += "\n⚠️ No AI data found - check database connection"
            } else {
                testResults += "\n✨ AI features are working perfectly!"
            }
            
            isLoading = false
        }
    }
}

struct AIStatsSummary: View {
    let rankings: [EnhancedDailyRanking]
    
    private var stats: (ai: Int, easy: Int, medium: Int, hard: Int, goodRevenue: Int, tonight: Int, thisWeek: Int) {
        let aiCount = rankings.filter { $0.aiRecommendation != nil }.count
        let easyCount = rankings.filter { $0.cloneDifficulty == .easyClone }.count
        let mediumCount = rankings.filter { $0.cloneDifficulty == .mediumClone }.count
        let hardCount = rankings.filter { $0.cloneDifficulty == .hardClone }.count
        let goodRevenueCount = rankings.filter { $0.revenuePotential == .goodRevenue }.count
        let tonightCount = rankings.filter { $0.intelligentPriority == .tonight }.count
        let thisWeekCount = rankings.filter { $0.intelligentPriority == .thisWeek }.count
        
        return (aiCount, easyCount, mediumCount, hardCount, goodRevenueCount, tonightCount, thisWeekCount)
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("📈 AI Intelligence Summary")
                .font(.headline)
            
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 8) {
                StatCard(
                    title: "AI Enhanced",
                    value: "\(stats.ai)",
                    icon: "sparkles",
                    color: .purple
                )
                
                StatCard(
                    title: "Easy Clones",
                    value: "\(stats.easy)",
                    icon: "bolt.fill",
                    color: .green
                )
                
                StatCard(
                    title: "Good Revenue",
                    value: "\(stats.goodRevenue)",
                    icon: "dollarsign.circle.fill",
                    color: .green
                )
                
                StatCard(
                    title: "Tonight Priority",
                    value: "\(stats.tonight)",
                    icon: "moon.fill",
                    color: .orange
                )
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

struct StatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(color)
            
            Text(value)
                .font(.title2)
                .fontWeight(.bold)
            
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(8)
    }
}

#Preview {
    AITestView()
}