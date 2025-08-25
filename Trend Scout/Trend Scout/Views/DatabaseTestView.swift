import SwiftUI

struct DatabaseTestView: View {
    @State private var isLoading = false
    @State private var testResults: String = "Tap 'Test Connection' to begin"
    @State private var successCount = 0
    @State private var failureCount = 0
    
    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                Text("Supabase Connection Test")
                    .font(.largeTitle)
                    .bold()
                
                // Status indicators
                HStack(spacing: 40) {
                    VStack {
                        Image(systemName: successCount > 0 ? "checkmark.circle.fill" : "circle")
                            .font(.title)
                            .foregroundColor(successCount > 0 ? .green : .gray)
                        Text("\(successCount) Success")
                            .font(.caption)
                    }
                    
                    VStack {
                        Image(systemName: failureCount > 0 ? "xmark.circle.fill" : "circle")
                            .font(.title)
                            .foregroundColor(failureCount > 0 ? .red : .gray)
                        Text("\(failureCount) Failures")
                            .font(.caption)
                    }
                }
                .padding()
                
                // Test button
                Button(action: runTests) {
                    HStack {
                        if isLoading {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle())
                                .scaleEffect(0.8)
                        } else {
                            Image(systemName: "network")
                        }
                        Text(isLoading ? "Testing..." : "Test Connection")
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                }
                .disabled(isLoading)
                
                // Results
                VStack(alignment: .leading, spacing: 10) {
                    Text("Test Results:")
                        .font(.headline)
                    
                    Text(testResults)
                        .font(.system(.body, design: .monospaced))
                        .padding()
                        .background(Color.gray.opacity(0.1))
                        .cornerRadius(8)
                }
                
                // Clear cache button
                Button(action: clearCache) {
                    HStack {
                        Image(systemName: "trash")
                        Text("Clear Cache")
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.orange)
                    .foregroundColor(.white)
                    .cornerRadius(10)
                }
            }
            .padding()
        }
    }
    
    private func runTests() {
        isLoading = true
        testResults = "🔄 Running tests...\n"
        successCount = 0
        failureCount = 0
        
        Task {
            // Test 1: Fetch latest rankings
            testResults += "\n📊 Test 1: Fetching latest rankings..."
            do {
                let rankings = try await SupabaseManager.shared.fetchLatestRankings(limit: 5, forceRefresh: true)
                testResults += "\n✅ Success! Found \(rankings.count) rankings"
                if let first = rankings.first {
                    testResults += "\n   Sample: \(first.name) (\(first.category))"
                }
                successCount += 1
            } catch {
                testResults += "\n❌ Failed: \(error.localizedDescription)"
                failureCount += 1
            }
            
            // Test 2: Fetch category leaders
            testResults += "\n\n🏆 Test 2: Fetching category leaders..."
            do {
                let leaders = try await SupabaseManager.shared.fetchCategoryLeadersLegacy(forceRefresh: true)
                let categories = Set(leaders.map { $0.category })
                testResults += "\n✅ Success! Found \(leaders.count) leaders across \(categories.count) categories"
                successCount += 1
            } catch {
                testResults += "\n❌ Failed: \(error.localizedDescription)"
                failureCount += 1
            }
            
            // Test 3: Fetch specific category
            testResults += "\n\n📱 Test 3: Fetching Utilities category..."
            do {
                let utilities = try await SupabaseManager.shared.fetchLatestRankings(category: "Utilities", limit: 3, forceRefresh: true)
                testResults += "\n✅ Success! Found \(utilities.count) Utilities apps"
                for (index, app) in utilities.enumerated() {
                    testResults += "\n   \(index + 1). \(app.name)"
                }
                successCount += 1
            } catch {
                testResults += "\n❌ Failed: \(error.localizedDescription)"
                failureCount += 1
            }
            
            // Test 4: Cache test
            testResults += "\n\n💾 Test 4: Testing cache..."
            let start = Date()
            do {
                // First call (should hit database)
                _ = try await SupabaseManager.shared.fetchLatestRankings(limit: 10, forceRefresh: true)
                let dbTime = Date().timeIntervalSince(start)
                
                // Second call (should hit cache)
                let cacheStart = Date()
                _ = try await SupabaseManager.shared.fetchLatestRankings(limit: 10, forceRefresh: false)
                let cacheTime = Date().timeIntervalSince(cacheStart)
                
                testResults += "\n✅ Cache working!"
                testResults += String(format: "\n   DB fetch: %.2fs", dbTime)
                testResults += String(format: "\n   Cache fetch: %.3fs", cacheTime)
                successCount += 1
            } catch {
                testResults += "\n❌ Cache test failed: \(error.localizedDescription)"
                failureCount += 1
            }
            
            // Summary
            testResults += "\n\n" + String(repeating: "-", count: 40)
            testResults += "\n📈 Summary: \(successCount) passed, \(failureCount) failed"
            
            if successCount == 4 && failureCount == 0 {
                testResults += "\n\n🎉 All tests passed! Database connection is working perfectly!"
            } else if successCount > 0 {
                testResults += "\n\n⚠️ Some tests passed. Check failures above."
            } else {
                testResults += "\n\n❌ All tests failed. Check your connection and credentials."
            }
            
            isLoading = false
        }
    }
    
    private func clearCache() {
        SupabaseManager.shared.clearCache()
        testResults = "🗑️ Cache cleared successfully!"
    }
}

#Preview {
    DatabaseTestView()
}