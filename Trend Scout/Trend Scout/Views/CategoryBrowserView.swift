import SwiftUI

struct CategoryBrowserView: View {
    @StateObject private var opportunityService = OpportunityService.shared
    @StateObject private var userSelectionService = UserSelectionService.shared
    @State private var selectedCategory: String?
    @State private var categoryOpportunities: [DailyRanking] = []
    @State private var isLoadingCategory = false
    @State private var showCategorySheet = false
    
    let categories = [
        ("Utilities", "wrench.and.screwdriver.fill", "⚙️"),
        ("Productivity", "checklist", "📈"),
        ("Photo & Video", "camera.fill", "📸"),
        ("Health & Fitness", "heart.fill", "💪"),
        ("Lifestyle", "leaf.fill", "🌿"),
        ("Finance", "dollarsign.circle.fill", "💰"),
        ("Music", "music.note", "🎵"),
        ("Education", "book.fill", "📚"),
        ("Graphics & Design", "paintbrush.fill", "🎨"),
        ("Entertainment", "tv.fill", "🎬")
    ]
    
    var body: some View {
        NavigationView {
            VStack {
                if opportunityService.isLoading && opportunityService.categoryLeaders.isEmpty {
                    ProgressView("Loading categories...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let error = opportunityService.error {
                    VStack {
                        Image(systemName: "exclamationmark.triangle")
                            .font(.system(size: 50))
                            .foregroundColor(.orange)
                        Text("Error")
                            .font(.title)
                            .fontWeight(.semibold)
                        Text(error)
                            .multilineTextAlignment(.center)
                            .foregroundColor(.secondary)
                        Button("Retry") {
                            Task {
                                await opportunityService.fetchCategoryLeaders()
                            }
                        }
                        .buttonStyle(.borderedProminent)
                        .padding(.top)
                    }
                    .padding()
                } else {
                    ScrollView {
                        LazyVGrid(columns: [
                            GridItem(.flexible()),
                            GridItem(.flexible())
                        ], spacing: 16) {
                            ForEach(categories, id: \.0) { category in
                                CategoryCard(
                                    name: category.0,
                                    icon: category.1,
                                    emoji: category.2,
                                    leaders: opportunityService.categoryLeaders.filter { $0.category == category.0 },
                                    onTap: {
                                        print("🏷️ Tapped category: \(category.0)")
                                        loadCategoryOpportunities(category.0)
                                    }
                                )
                            }
                        }
                        .padding()
                    }
                }
            }
            .navigationTitle("Categories")
            .refreshable {
                await opportunityService.fetchCategoryLeaders()
            }
            .task {
                await opportunityService.fetchCategoryLeaders()
            }
            .sheet(isPresented: $showCategorySheet) {
                let _ = print("🔥 SHEET BLOCK EXECUTING - showCategorySheet: \(showCategorySheet), selectedCategory: \(selectedCategory ?? "nil")")
                CategoryDetailSheetView(
                    selectedCategory: selectedCategory ?? "Unknown",
                    categoryOpportunities: categoryOpportunities,
                    isLoadingCategory: isLoadingCategory,
                    userSelectionService: userSelectionService,
                    opportunityService: opportunityService,
                    onDismiss: { showCategorySheet = false }
                )
            }
        }
    }
    
    private func loadCategoryOpportunities(_ category: String) {
        print("🔥 🎯 loadCategoryOpportunities called for: \(category)")
        
        print("🔥 BEFORE STATE CHANGE - selectedCategory: \(selectedCategory ?? "nil"), isLoadingCategory: \(isLoadingCategory), showCategorySheet: \(showCategorySheet)")
        
        // 🔧 CLEAR PREVIOUS DATA to avoid stale state in sheet
        categoryOpportunities = []
        
        // 🔧 SET STATE SYNCHRONOUSLY for immediate UI response
        selectedCategory = category
        isLoadingCategory = true
        showCategorySheet = true  // ✅ SHOW SHEET IMMEDIATELY!
        
        print("🔥 AFTER STATE CHANGE - selectedCategory: \(selectedCategory ?? "nil"), isLoadingCategory: \(isLoadingCategory), showCategorySheet: \(showCategorySheet)")
        print("🔥 🎯 Sheet should now be visible with loading state")
        
        Task {
            print("🔥 🎯 Task started - Fetching opportunities for \(category)...")
            let opportunities = await opportunityService.fetchOpportunitiesByCategory(category)
            print("🔥 🔍 Task completed - Got \(opportunities.count) opportunities")
            
            // 🔧 DEBUG: Check for duplicate bundle IDs in fetched data
            let bundleIds = opportunities.map { $0.bundleId }
            let uniqueBundleIds = Set(bundleIds)
            if bundleIds.count > uniqueBundleIds.count {
                print("⚠️ 🔍 FOUND \(bundleIds.count - uniqueBundleIds.count) DUPLICATE BUNDLE IDs in fetched data!")
            }
            
            print("🔥 🔍 Sample opportunity names: \(opportunities.prefix(3).map { $0.name })")
            
            await MainActor.run {
                print("🔥 🎯 MainActor.run started - updating UI with \(opportunities.count) opportunities")
                print("🔥 BEFORE FINAL STATE CHANGE - categoryOpportunities.count: \(categoryOpportunities.count), isLoadingCategory: \(isLoadingCategory)")
                
                categoryOpportunities = opportunities
                isLoadingCategory = false
                // ✅ No longer setting showCategorySheet here - it's already true!
                
                print("🔥 AFTER FINAL STATE CHANGE - categoryOpportunities.count: \(categoryOpportunities.count), isLoadingCategory: \(isLoadingCategory), showCategorySheet: \(showCategorySheet)")
                print("🔥 🎯 MainActor.run completed - UI should now show \(opportunities.count) opportunities")
            }
            
            print("🔥 ✅ Task fully completed - \(opportunities.count) opportunities for \(category)")
        }
    }
}

struct CategoryDetailSheetView: View {
    let selectedCategory: String
    let categoryOpportunities: [DailyRanking]
    let isLoadingCategory: Bool
    let userSelectionService: UserSelectionService
    let opportunityService: OpportunityService
    let onDismiss: () -> Void
    
    // 🔧 TRY EXTERNAL STATE MANAGEMENT instead of internal state
    @State private var selectedOpportunityForDetail: DailyRanking? {
        didSet {
            print("🔥 💥 selectedOpportunityForDetail CHANGED: \(selectedOpportunityForDetail?.name ?? "nil")")
        }
    }
    
    var body: some View {
        let _ = print("🔥 CategoryDetailSheetView RENDERING - category: \(selectedCategory), count: \(categoryOpportunities.count), loading: \(isLoadingCategory)")
        NavigationView {
            let _ = print("🔥 NavigationView RENDERING")
            VStack {
                let _ = print("🔥 VStack RENDERING")
                let _ = print("🔥 STATE CHECK - isLoadingCategory: \(isLoadingCategory), categoryOpportunities.count: \(categoryOpportunities.count)")
                if isLoadingCategory {
                    let _ = print("🔥 SHOWING LOADING STATE")
                    ProgressView("Loading \(selectedCategory) opportunities...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .onAppear { print("🔥 ProgressView APPEARED") }
                } else if categoryOpportunities.isEmpty {
                    let _ = print("🔥 SHOWING EMPTY STATE")
                    VStack {
                        Image(systemName: "magnifyingglass")
                            .font(.system(size: 50))
                            .foregroundColor(.gray)
                        Text("No opportunities found")
                            .font(.title2)
                            .fontWeight(.medium)
                        Text("Check back later for new opportunities")
                            .foregroundColor(.secondary)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .onAppear { print("🔥 Empty State APPEARED") }
                } else {
                    let _ = print("🔥 SHOWING LIST with \(categoryOpportunities.count) items")
                    
                    // 🔧 FIX: Use ScrollView + LazyVStack to prevent double rendering
                    ScrollView {
                        LazyVStack(spacing: 8) {
                            ForEach(categoryOpportunities, id: \.bundleId) { opportunity in
                                let _ = print("🔥 ITEM RENDERING: \(opportunity.name) (\(opportunity.bundleId))")
                                OpportunityRankingCard(
                                    opportunity: opportunity,
                                    isSelected: userSelectionService.isSelected(opportunity.bundleId),
                                    onToggleSelection: {
                                        print("🔥 TOGGLE SELECTION: \(opportunity.name)")
                                        opportunityService.toggleOpportunitySelection(opportunity)
                                    },
                                    onTap: {
                                        print("🔥 💥 TAP DETECTED for: \(opportunity.name)")
                                        print("🔥 💥 BEFORE: selectedOpportunityForDetail=\(selectedOpportunityForDetail?.name ?? "nil")")
                                        
                                        // 🔧 SIMPLE STATE UPDATE
                                        selectedOpportunityForDetail = opportunity
                                        
                                        print("🔥 💥 AFTER SET: selectedOpportunityForDetail=\(selectedOpportunityForDetail?.name ?? "nil")")
                                    }
                                )
                                .padding(.horizontal)
                            }
                        }
                        .padding(.vertical)
                    }
                    .background(Color.clear)
                    .onAppear { print("🔥 SCROLLVIEW APPEARED with \(categoryOpportunities.count) items") }
                }
            }
            .onAppear { print("🔥 VStack APPEARED") }
            .navigationTitle(selectedCategory)
            .navigationBarTitleDisplayMode(.large)
        }
        .onAppear { print("🔥 NavigationView APPEARED") }
        .sheet(item: $selectedOpportunityForDetail) { opportunity in
            let _ = print("🔥 💥 OPPORTUNITY SHEET PRESENTING with item: \(opportunity.name)")
            OpportunityDetailView(
                opportunity: opportunityService.createOpportunityFromRanking(opportunity),
                showBuildTracking: false
            )
            .onAppear {
                print("🔥 💥 OPPORTUNITY DETAIL VIEW APPEARED!")
            }
        }
    }
}

struct CategoryWrapper: Identifiable {
    let id = UUID()
    let name: String
}

struct CategoryCard: View {
    let name: String
    let icon: String
    let emoji: String
    let leaders: [DailyRanking]
    let onTap: () -> Void
    
    var topApp: DailyRanking? {
        leaders.first
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
                        Text("\(leaders.count) opportunities")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    Image(systemName: "chevron.right")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                if let topApp = topApp {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Top Opportunity:")
                            .font(.caption2)
                            .fontWeight(.medium)
                            .foregroundColor(.secondary)
                        
                        Text(topApp.name)
                            .font(.caption)
                            .fontWeight(.medium)
                            .lineLimit(1)
                            .foregroundColor(.primary)
                        
                        if let score = topApp.total {
                            HStack {
                                Image(systemName: "star.fill")
                                    .font(.caption2)
                                    .foregroundColor(.yellow)
                                Text(String(format: "%.1f", score))
                                    .font(.caption2)
                                    .fontWeight(.medium)
                            }
                        }
                    }
                    .padding(.top, 4)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(12)
            .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct CategoryDetailView: View {
    let categoryName: String
    let opportunities: [DailyRanking]
    let isLoading: Bool
    @Environment(\.dismiss) private var dismiss
    @StateObject private var userSelectionService = UserSelectionService.shared
    @StateObject private var opportunityService = OpportunityService.shared
    
    var body: some View {
        NavigationView {
            VStack {
                if isLoading {
                    ProgressView("Loading \(categoryName) opportunities...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if opportunities.isEmpty {
                    VStack {
                        Image(systemName: "magnifyingglass")
                            .font(.system(size: 50))
                            .foregroundColor(.gray)
                        Text("No opportunities found")
                            .font(.title2)
                            .fontWeight(.medium)
                        Text("Check back later for new opportunities")
                            .foregroundColor(.secondary)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List(opportunities, id: \.id) { opportunity in
                        OpportunityRankingCardWithNavigation(
                            opportunity: opportunity,
                            isSelected: userSelectionService.isSelected(opportunity.bundleId),
                            onToggleSelection: {
                                opportunityService.toggleOpportunitySelection(opportunity)
                            },
                            opportunityService: opportunityService
                        )
                        .listRowSeparator(.hidden)
                        .listRowInsets(EdgeInsets(top: 4, leading: 16, bottom: 4, trailing: 16))
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle(categoryName)
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}

struct OpportunityRankingCardWithNavigation: View {
    let opportunity: DailyRanking
    let isSelected: Bool
    let onToggleSelection: () -> Void
    let opportunityService: OpportunityService
    @State private var showDetail = false
    
    var body: some View {
        OpportunityRankingCard(
            opportunity: opportunity,
            isSelected: isSelected,
            onToggleSelection: onToggleSelection,
            onTap: {
                showDetail = true
            }
        )
        .sheet(isPresented: $showDetail) {
            OpportunityDetailView(
                opportunity: opportunityService.createOpportunityFromRanking(opportunity),
                showBuildTracking: false
            )
        }
    }
}

struct OpportunityRankingCard: View {
    let opportunity: DailyRanking
    let isSelected: Bool
    let onToggleSelection: () -> Void
    var onTap: (() -> Void)? = nil
    
    var body: some View {
        Button(action: onTap ?? {}) {
            VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("#\(opportunity.rank)")
                    .font(.headline)
                    .fontWeight(.bold)
                    .foregroundColor(.blue)
                
                VStack(alignment: .leading, spacing: 2) {
                    Text(opportunity.name)
                        .font(.headline)
                        .fontWeight(.semibold)
                        .lineLimit(1)
                    
                    if let bundleId = opportunity.bundleId.split(separator: ".").last {
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
                        if let total = opportunity.total {
                            HStack(spacing: 4) {
                                Image(systemName: "star.fill")
                                    .foregroundColor(.yellow)
                                    .font(.caption)
                                Text(String(format: "%.1f", total))
                                    .font(.caption)
                                    .fontWeight(.medium)
                            }
                        }
                        
                        if let price = opportunity.price {
                            Text(price > 0 ? "$\(String(format: "%.2f", price))" : "Free")
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }
            
            HStack {
                if let ratingCount = opportunity.ratingCount, ratingCount > 0 {
                    Label("\(ratingCount)", systemImage: "person.2")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
                
                if let ratingAvg = opportunity.ratingAvg {
                    Label(String(format: "%.1f", ratingAvg), systemImage: "star")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                Text(opportunity.chart.capitalized)
                    .font(.caption2)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color.blue.opacity(0.1))
                    .foregroundColor(.blue)
                    .cornerRadius(4)
            }
            }
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(12)
            .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
        }
        .buttonStyle(PlainButtonStyle())
        .disabled(onTap == nil)
    }
}

#Preview {
    CategoryBrowserView()
}