import SwiftUI

struct OpportunityDetailView: View {
    let opportunity: Opportunity
    @StateObject private var buildTracker = BuildTracker()
    var showBuildTracking: Bool = true
    
    private var buildStatus: BuildStatus {
        buildTracker.getBuildStatus(opportunity.id)
    }
    
    private var buildRecord: BuildRecord? {
        buildTracker.getBuildRecord(for: opportunity.id)
    }
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Header
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text(opportunity.emoji)
                            .font(.system(size: 50))
                        
                        VStack(alignment: .leading, spacing: 4) {
                            HStack(spacing: 6) {
                                Text(opportunity.displayName)
                                    .font(.title2)
                                    .fontWeight(.bold)
                                
                                // Clone name type badge
                                if !opportunity.displayNameType.badgeText.isEmpty {
                                    Text(opportunity.displayNameType.badgeText)
                                        .font(.caption2)
                                        .fontWeight(.medium)
                                        .padding(.horizontal, 6)
                                        .padding(.vertical, 2)
                                        .background(badgeColor(for: opportunity.displayNameType))
                                        .foregroundColor(.white)
                                        .cornerRadius(4)
                                }
                                
                                Spacer()
                            }
                            Text(opportunity.subtitle)
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                        
                        Spacer()
                    }
                    
                    HStack {
                        PriorityBadge(priority: opportunity.priority)
                        
                        Spacer()
                        
                        HStack(spacing: 16) {
                            MetricView(
                                title: "Clone Score",
                                value: String(format: "%.1f", opportunity.cloneScore),
                                icon: "star.fill",
                                color: .yellow
                            )
                            
                            MetricView(
                                title: "Confidence",
                                value: "\(Int(opportunity.confidence * 100))%",
                                icon: "checkmark.circle.fill",
                                color: .green
                            )
                        }
                    }
                }
                .padding()
                .background(Color(.systemGray6))
                .cornerRadius(12)
                
                // Build Estimate
                BuildEstimateCard(buildEstimate: opportunity.buildEstimate)
                
                // Key Features
                if !opportunity.keyFeatures.isEmpty {
                    SectionView(title: "Key Features", icon: "sparkles") {
                        LazyVGrid(columns: [
                            GridItem(.flexible()),
                            GridItem(.flexible())
                        ], spacing: 12) {
                            ForEach(opportunity.keyFeatures) { feature in
                                FeatureCard(feature: feature)
                            }
                        }
                    }
                }
                
                // Revenue Model
                SectionView(title: "Revenue Model", icon: "dollarsign.circle") {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Type: \(opportunity.revenueModel.type.capitalized)")
                            .font(.headline)
                        Text(opportunity.revenueModel.primary)
                            .font(.body)
                            .foregroundColor(.secondary)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding()
                    .background(Color(.systemBackground))
                    .cornerRadius(8)
                }
                
                // iOS Features
                if !opportunity.iosFeatures.isEmpty {
                    SectionView(title: "iOS Features", icon: "iphone") {
                        VStack(alignment: .leading, spacing: 8) {
                            ForEach(opportunity.iosFeatures, id: \.self) { feature in
                                HStack {
                                    Image(systemName: "checkmark.circle.fill")
                                        .foregroundColor(.blue)
                                    Text(feature)
                                        .font(.body)
                                    Spacer()
                                }
                            }
                        }
                        .padding()
                        .background(Color(.systemBackground))
                        .cornerRadius(8)
                    }
                }
                
                // Market Analysis
                VStack(alignment: .leading, spacing: 16) {
                    SectionView(title: "Market Gap", icon: "target") {
                        Text(opportunity.marketGap)
                            .font(.body)
                            .fixedSize(horizontal: false, vertical: true)
                            .padding()
                            .background(Color(.systemBackground))
                            .cornerRadius(8)
                    }
                    
                    SectionView(title: "Competitive Edge", icon: "trophy") {
                        Text(opportunity.competitiveEdge)
                            .font(.body)
                            .fixedSize(horizontal: false, vertical: true)
                            .padding()
                            .background(Color(.systemBackground))
                            .cornerRadius(8)
                    }
                }
                
                // Risks
                if !opportunity.risks.isEmpty {
                    SectionView(title: "Risks", icon: "exclamationmark.triangle") {
                        VStack(alignment: .leading, spacing: 8) {
                            ForEach(opportunity.risks, id: \.self) { risk in
                                HStack(alignment: .top) {
                                    Image(systemName: "minus.circle.fill")
                                        .foregroundColor(.orange)
                                        .padding(.top, 2)
                                    Text(risk)
                                        .font(.body)
                                        .fixedSize(horizontal: false, vertical: true)
                                    Spacer()
                                }
                            }
                        }
                        .padding()
                        .background(Color(.systemBackground))
                        .cornerRadius(8)
                    }
                }
                
                // Build Status & Actions
                if showBuildTracking {
                    VStack(spacing: 16) {
                    // Status Display
                    if buildStatus != .notStarted {
                        VStack(spacing: 8) {
                            HStack {
                                Image(systemName: buildStatus.icon)
                                    .foregroundColor(buildStatus.color)
                                    .font(.title2)
                                
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("Status: \(buildStatus.displayName)")
                                        .font(.headline)
                                        .fontWeight(.semibold)
                                    
                                    if let record = buildRecord {
                                        Text("Started: \(record.dateBuilt.formatted(date: .abbreviated, time: .shortened))")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                }
                                
                                Spacer()
                                
                                // Status Badge
                                Text(buildStatus.shortName)
                                    .font(.caption)
                                    .fontWeight(.semibold)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(buildStatus.color)
                                    .foregroundColor(.white)
                                    .cornerRadius(8)
                            }
                        }
                        .padding()
                        .background(buildStatus.color.opacity(0.1))
                        .cornerRadius(12)
                    }
                    
                    // Action Buttons
                    VStack(spacing: 12) {
                        HStack(spacing: 12) {
                            // Primary Action Button
                            if let nextStatus = buildStatus.nextStatus {
                                Button(action: {
                                    buildTracker.advanceToNextStatus(opportunity.id, title: opportunity.displayName)
                                }) {
                                    HStack {
                                        Image(systemName: nextStatus.icon)
                                        Text(getActionButtonText(for: buildStatus))
                                    }
                                    .frame(maxWidth: .infinity)
                                    .padding()
                                    .background(nextStatus.color)
                                    .foregroundColor(.white)
                                    .cornerRadius(10)
                                }
                            }
                            
                            // Pause/Resume Toggle
                            if buildStatus.canTogglePause {
                                Button(action: {
                                    buildTracker.togglePause(opportunity.id)
                                }) {
                                    HStack {
                                        Image(systemName: buildStatus == .wip ? "pause.circle" : "play.circle")
                                        Text(buildStatus == .wip ? "Pause" : "Resume")
                                    }
                                    .frame(maxWidth: .infinity)
                                    .padding()
                                    .background(buildStatus == .wip ? Color.orange : Color.blue)
                                    .foregroundColor(.white)
                                    .cornerRadius(10)
                                }
                            }
                        }
                        
                        // Reset Button (only show for non-completed builds)
                        if buildStatus != .notStarted && buildStatus != .completed {
                            Button(action: {
                                buildTracker.resetBuild(opportunity.id)
                            }) {
                                HStack {
                                    Image(systemName: "arrow.counterclockwise")
                                    Text("Reset")
                                }
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.gray)
                                .foregroundColor(.white)
                                .cornerRadius(10)
                            }
                        }
                    }
                    }
                    .padding(.top)
                }
            }
            .padding()
        }
        .overlay(
            // Floating Add Button (only when not showing build tracking)
            Group {
                if !showBuildTracking {
                    VStack {
                        Spacer()
                        HStack {
                            Spacer()
                            FloatingAddButton(opportunity: opportunity)
                                .padding(.trailing, 20)
                                .padding(.bottom, 20)
                        }
                    }
                }
            }
        )
        .navigationTitle("Opportunity Details")
        .navigationBarTitleDisplayMode(.inline)
    }
    
    private func getActionButtonText(for status: BuildStatus) -> String {
        switch status {
        case .notStarted: return "Start Building"
        case .wip: return "Mark Complete"
        case .paused: return "Resume & Complete"
        case .completed: return "Completed"
        }
    }
    
    // Helper function for clone name badge color
    private func badgeColor(for type: CloneNameType) -> Color {
        switch type {
        case .userCustom: return .purple
        case .aiGenerated: return .blue
        case .original: return .gray
        }
    }
}

struct MetricView: View {
    let title: String
    let value: String
    let icon: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 2) {
            HStack(spacing: 4) {
                Image(systemName: icon)
                    .foregroundColor(color)
                    .font(.caption)
                Text(value)
                    .font(.caption)
                    .fontWeight(.semibold)
            }
            Text(title)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
    }
}

struct BuildEstimateCard: View {
    let buildEstimate: BuildEstimate
    
    var body: some View {
        HStack(spacing: 20) {
            VStack(alignment: .leading, spacing: 4) {
                Text("Build Time")
                    .font(.caption)
                    .foregroundColor(.secondary)
                Text(buildEstimate.time)
                    .font(.headline)
                    .fontWeight(.semibold)
            }
            
            Divider()
                .frame(height: 30)
            
            VStack(alignment: .leading, spacing: 4) {
                Text("Difficulty")
                    .font(.caption)
                    .foregroundColor(.secondary)
                Text(buildEstimate.difficulty)
                    .font(.headline)
                    .fontWeight(.semibold)
                    .foregroundColor(difficultyColor)
            }
            
            Spacer()
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
    
    var difficultyColor: Color {
        switch buildEstimate.difficulty.lowercased() {
        case "easy": return .green
        case "medium": return .orange
        case "hard": return .red
        default: return .primary
        }
    }
}

struct FeatureCard: View {
    let feature: Feature
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(feature.icon)
                    .font(.title2)
                Text(feature.title)
                    .font(.headline)
                    .fontWeight(.semibold)
                    .lineLimit(1)
                Spacer()
            }
            
            Text(feature.desc)
                .font(.caption)
                .foregroundColor(.secondary)
                .fixedSize(horizontal: false, vertical: true)
                .lineLimit(nil)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(8)
    }
}

struct SectionView<Content: View>: View {
    let title: String
    let icon: String
    let content: () -> Content
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(.blue)
                Text(title)
                    .font(.headline)
                    .fontWeight(.semibold)
                Spacer()
            }
            
            content()
        }
    }
}

struct FloatingAddButton: View {
    let opportunity: Opportunity
    @StateObject private var userSelectionService = UserSelectionService.shared
    @StateObject private var opportunityService = OpportunityService.shared
    @State private var isAdded = false
    
    private var isSelected: Bool {
        userSelectionService.isSelected(opportunity.id)
    }
    
    var body: some View {
        Button(action: {
            if isSelected {
                userSelectionService.removeFromDaily(opportunity.id)
                // 🔧 Note: Cache cleanup is handled by OpportunityService.toggleOpportunitySelection
            } else {
                // 🔧 NEW: Cache the opportunity in OpportunityService first
                opportunityService.cacheOpportunity(opportunity)
                
                userSelectionService.addToDaily(opportunity.id)
                isAdded = true
                // Reset after animation
                DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                    isAdded = false
                }
            }
        }) {
            HStack(spacing: 8) {
                Image(systemName: isSelected ? "checkmark.circle.fill" : "plus.circle.fill")
                    .font(.title2)
                Text(isSelected ? "Added" : "Add to Brief")
                    .font(.headline)
                    .fontWeight(.semibold)
            }
            .foregroundColor(.white)
            .padding(.horizontal, 20)
            .padding(.vertical, 12)
            .background(isSelected ? Color.green : Color.blue)
            .cornerRadius(25)
            .shadow(color: .black.opacity(0.3), radius: 5, x: 0, y: 2)
            .scaleEffect(isAdded ? 1.1 : 1.0)
            .animation(.spring(response: 0.3, dampingFraction: 0.6), value: isAdded)
        }
    }
}

#Preview {
    NavigationView {
        OpportunityDetailView(opportunity: Opportunity(
            id: "sample",
            appName: "Design Studio Pro",
            category: "Photo & Video",
            cloneScore: 2.23,
            title: "Design Studio",
            subtitle: "Create stunning graphics with AI assistance",
            emoji: "🎨",
            keyFeatures: [
                Feature(icon: "🎨", title: "Smart Templates", desc: "AI-generated layouts"),
                Feature(icon: "🖼️", title: "Photo Editor", desc: "Advanced editing tools")
            ],
            revenueModel: RevenueModel(type: "subscription", primary: "Premium templates and AI features"),
            buildEstimate: BuildEstimate(time: "2-3 hours", difficulty: "Easy", priority: "Tonight"),
            marketGap: "Complex design tools intimidate casual users",
            competitiveEdge: "Mobile-first design with voice commands",
            risks: ["Template licensing costs", "Adobe competition"],
            iosFeatures: ["SwiftUI drag-drop", "Shortcuts integration"],
            confidence: 0.9,
            priority: .tonight,
            generatedAt: Date(),
            categoryRank: 2,  // Mock rank for preview
            originalRank: 5,   // Mock original rank
            cloneName: "DesignStudio AI",
            cloneNameCustom: nil
        ))
    }
}