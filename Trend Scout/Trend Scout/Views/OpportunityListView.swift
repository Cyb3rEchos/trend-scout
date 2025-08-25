import SwiftUI

struct OpportunityListView: View {
    @StateObject private var opportunityService = OpportunityService.shared
    @StateObject private var userSelectionService = UserSelectionService.shared
    @State private var selectedPriority: Priority? = nil
    
    var filteredOpportunities: [Opportunity] {
        let selectedOpportunities = opportunityService.selectedOpportunities
        let filtered = if let priority = selectedPriority {
            selectedOpportunities.filter { $0.priority == priority }
        } else {
            selectedOpportunities
        }
        
        // Sort by priority (Tonight first) and then by score
        return filtered.sorted { first, second in
            if first.priority.sortOrder != second.priority.sortOrder {
                return first.priority.sortOrder < second.priority.sortOrder
            }
            return first.cloneScore > second.cloneScore
        }
    }
    
    var tonightCount: Int {
        opportunityService.selectedOpportunities.filter { $0.priority == .tonight }.count
    }
    
    var body: some View {
        NavigationView {
            VStack {
                if opportunityService.isLoading {
                    ProgressView("Loading opportunities...")
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
                                await opportunityService.fetchTodaysOpportunities()
                            }
                        }
                        .buttonStyle(.borderedProminent)
                        .padding(.top)
                    }
                    .padding()
                } else {
                    VStack {
                        // Tonight's Opportunities Banner (if any)
                        if tonightCount > 0 && selectedPriority != .tonight {
                            TonightBanner(count: tonightCount) {
                                selectedPriority = .tonight
                            }
                            .padding(.horizontal)
                            .padding(.top, 8)
                        }
                        
                        // Priority Filter
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack {
                                FilterChip(
                                    title: "All",
                                    isSelected: selectedPriority == nil
                                ) {
                                    selectedPriority = nil
                                }
                                
                                ForEach(Priority.allCases, id: \.self) { priority in
                                    PriorityFilterChip(
                                        priority: priority,
                                        isSelected: selectedPriority == priority,
                                        count: countOpportunities(for: priority)
                                    ) {
                                        selectedPriority = priority
                                    }
                                }
                            }
                            .padding(.horizontal)
                        }
                        .frame(height: 44) // Fixed height to prevent vertical movement
                        .fixedSize(horizontal: false, vertical: true) // Lock vertical size
                        .padding(.bottom, 8)
                        
                        // Opportunities List
                        if filteredOpportunities.isEmpty {
                            VStack {
                                Image(systemName: "star.slash")
                                    .font(.system(size: 50))
                                    .foregroundColor(.gray)
                                Text("No opportunities selected")
                                    .font(.title2)
                                    .fontWeight(.medium)
                                Text("Browse categories to add opportunities to your daily brief")
                                    .foregroundColor(.secondary)
                                    .multilineTextAlignment(.center)
                            }
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                        } else {
                            List {
                                ForEach(filteredOpportunities) { opportunity in
                                    NavigationLink(destination: OpportunityDetailView(opportunity: opportunity)) {
                                        OpportunityCard(opportunity: opportunity)
                                    }
                                    .listRowSeparator(.hidden)
                                    .listRowInsets(EdgeInsets(top: 4, leading: 16, bottom: 4, trailing: 16))
                                }
                                .onDelete(perform: deleteOpportunities)
                            }
                            .listStyle(.plain)
                        }
                    }
                }
            }
            .navigationTitle("Daily Brief")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Clear Old") {
                        userSelectionService.clearAllSelections()
                    }
                    .foregroundColor(.red)
                    .font(.caption)
                }
            }
            .refreshable {
                await opportunityService.fetchTodaysOpportunities()
            }
            .task {
                await opportunityService.fetchTodaysOpportunities()
            }
        }
    }
    
    private func deleteOpportunities(offsets: IndexSet) {
        for index in offsets {
            let opportunity = filteredOpportunities[index]
            userSelectionService.removeFromDaily(opportunity.id)
        }
    }
    
    private func countOpportunities(for priority: Priority) -> Int {
        return opportunityService.selectedOpportunities.filter { $0.priority == priority }.count
    }
}

struct OpportunityCard: View {
    let opportunity: Opportunity
    
    // 🏆 Top-3 highlighting logic
    var isTop3: Bool {
        guard let categoryRank = opportunity.categoryRank else { return false }
        return categoryRank <= 3
    }
    
    var rankBadgeColor: Color {
        guard let categoryRank = opportunity.categoryRank else { return .gray }
        switch categoryRank {
        case 1: return .yellow      // 🥇 Gold
        case 2: return .gray        // 🥈 Silver  
        case 3: return .orange      // 🥉 Bronze
        default: return .blue       // 📍 Regular
        }
    }
    
    var rankEmoji: String {
        guard let categoryRank = opportunity.categoryRank else { return "📍" }
        switch categoryRank {
        case 1: return "🥇"
        case 2: return "🥈" 
        case 3: return "🥉"
        default: return "#\(categoryRank)"
        }
    }
    
    // Helper function for clone name badge color
    func badgeColor(for type: CloneNameType) -> Color {
        switch type {
        case .userCustom: return .purple
        case .aiGenerated: return .blue
        case .original: return .gray
        }
    }
    
    // Build time visual indicators
    var buildTimeIcon: String {
        if opportunity.buildEstimate.time.contains("2-3 hour") || opportunity.buildEstimate.time.contains("3-4 hour") {
            return "bolt.fill"  // Lightning for quick builds
        } else if opportunity.buildEstimate.time.contains("day") {
            return "calendar"  // Calendar for multi-day
        } else {
            return "clock"  // Default clock
        }
    }
    
    var buildTimeColor: Color {
        if opportunity.priority == .tonight {
            return .green  // Green for quick builds
        } else if opportunity.priority == .thisWeek {
            return .orange  // Orange for week builds
        } else {
            return .gray  // Gray for future
        }
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(opportunity.emoji)
                    .font(.system(size: 30))
                
                VStack(alignment: .leading, spacing: 2) {
                    HStack(alignment: .center, spacing: 6) {
                        Text(opportunity.displayName)
                            .font(.headline)
                            .fontWeight(.semibold)
                        
                        // Clone name type badge
                        if !opportunity.displayNameType.badgeText.isEmpty {
                            Text(opportunity.displayNameType.badgeText)
                                .font(.caption2)
                                .fontWeight(.medium)
                                .padding(.horizontal, 4)
                                .padding(.vertical, 1)
                                .background(badgeColor(for: opportunity.displayNameType))
                                .foregroundColor(.white)
                                .cornerRadius(3)
                        }
                        
                        Spacer()
                    }
                    Text(opportunity.subtitle)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 4) {
                    PriorityBadge(priority: opportunity.priority)
                    
                    // 🏆 Top-3 rank badge
                    if let categoryRank = opportunity.categoryRank, categoryRank <= 10 {
                        HStack(spacing: 2) {
                            Text(rankEmoji)
                                .font(.caption)
                            if categoryRank > 3 {
                                Text("#\(categoryRank)")
                                    .font(.caption2)
                                    .fontWeight(.medium)
                            }
                        }
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(isTop3 ? rankBadgeColor.opacity(0.2) : Color.gray.opacity(0.1))
                        .foregroundColor(isTop3 ? rankBadgeColor : .secondary)
                        .cornerRadius(8)
                    }
                    
                    HStack(spacing: 4) {
                        Image(systemName: "star.fill")
                            .foregroundColor(.yellow)
                            .font(.caption)
                        Text(String(format: "%.1f", opportunity.cloneScore))
                            .font(.caption)
                            .fontWeight(.medium)
                    }
                }
            }
            
            HStack {
                // Build time with visual indicator
                HStack(spacing: 4) {
                    Image(systemName: buildTimeIcon)
                        .foregroundColor(buildTimeColor)
                        .font(.caption)
                    Text(opportunity.buildEstimate.time)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                // Priority urgency indicator
                if opportunity.priority == .tonight {
                    Label("Build Tonight!", systemImage: "moon.stars.fill")
                        .font(.caption2)
                        .fontWeight(.medium)
                        .foregroundColor(.red)
                }
                
                Text(opportunity.category)
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(Color.blue.opacity(0.1))
                    .foregroundColor(.blue)
                    .cornerRadius(4)
            }
        }
        .padding()
        .background(
            isTop3 ? 
            LinearGradient(
                colors: [Color(.systemBackground), rankBadgeColor.opacity(0.05)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            ) : 
            LinearGradient(
                colors: [Color(.systemBackground), Color(.systemBackground)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
        .overlay(
            // Special border for top-3
            RoundedRectangle(cornerRadius: 12)
                .stroke(
                    isTop3 ? rankBadgeColor.opacity(0.3) : Color.clear,
                    lineWidth: isTop3 ? 1.5 : 0
                )
        )
    }
}

struct PriorityBadge: View {
    let priority: Priority
    
    var backgroundColor: Color {
        switch priority {
        case .tonight: return .red
        case .thisWeek: return .orange
        case .thisMonth: return .blue
        case .future: return .gray
        }
    }
    
    var body: some View {
        HStack(spacing: 3) {
            Text(priority.emoji)
                .font(.caption2)
            Text(priority.displayName)
                .font(.caption2)
                .fontWeight(.semibold)
        }
        .padding(.horizontal, 6)
        .padding(.vertical, 2)
        .background(backgroundColor)
        .foregroundColor(.white)
        .cornerRadius(6)
    }
}

struct PriorityFilterChip: View {
    let priority: Priority
    let isSelected: Bool
    let count: Int
    let action: () -> Void
    
    var backgroundColor: Color {
        if isSelected {
            switch priority {
            case .tonight: return .red
            case .thisWeek: return .orange
            case .thisMonth: return .blue
            case .future: return .gray
            }
        }
        return Color(.systemGray5)
    }
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 4) {
                Text(priority.emoji)
                    .font(.caption)
                Text(priority.displayName)
                    .font(.caption)
                    .fontWeight(.medium)
                if count > 0 {
                    Text("(\(count))")
                        .font(.caption2)
                        .fontWeight(.bold)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(backgroundColor)
            .foregroundColor(isSelected ? .white : .primary)
            .cornerRadius(16)
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(isSelected ? Color.clear : Color(.systemGray4), lineWidth: 0.5)
            )
        }
    }
}

struct FilterChip: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.caption)
                .fontWeight(.medium)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(isSelected ? Color.blue : Color(.systemGray5))
                .foregroundColor(isSelected ? .white : .primary)
                .cornerRadius(16)
        }
    }
}

struct TonightBanner: View {
    let count: Int
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    HStack(spacing: 6) {
                        Image(systemName: "moon.stars.fill")
                            .font(.title2)
                        Text("Build Tonight!")
                            .font(.headline)
                            .fontWeight(.bold)
                    }
                    Text("\(count) quick-win \(count == 1 ? "opportunity" : "opportunities") ready in 2-3 hours")
                        .font(.subheadline)
                        .foregroundColor(.white.opacity(0.9))
                }
                
                Spacer()
                
                Image(systemName: "chevron.right.circle.fill")
                    .font(.title2)
                    .foregroundColor(.white.opacity(0.8))
            }
            .padding()
            .background(
                LinearGradient(
                    colors: [Color.red, Color.red.opacity(0.8)],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
            .foregroundColor(.white)
            .cornerRadius(12)
            .shadow(color: .red.opacity(0.3), radius: 4, x: 0, y: 2)
        }
    }
}

#Preview {
    OpportunityListView()
}