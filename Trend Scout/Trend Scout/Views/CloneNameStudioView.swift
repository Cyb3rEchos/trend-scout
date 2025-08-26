import SwiftUI

struct CloneNameStudioView: View {
    @StateObject private var supabaseManager = SupabaseManager.shared
    @StateObject private var opportunityService = OpportunityService.shared
    @StateObject private var aiService = SupabaseAIService.shared
    
    // App selection
    @State private var selectedOpportunity: Opportunity?
    @State private var opportunities: [Opportunity] = []
    
    // Name generation
    @State private var generatedNames: [GeneratedName] = []
    @State private var selectedStyle: NamingStyle = .balanced
    @State private var customPrompt: String = ""
    @State private var isGenerating = false
    
    // UI State
    @State private var showingAppPicker = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // App Selection
                appSelectionSection
                    .padding(.horizontal)
                    .padding(.top)
                
                // Server Status Info
                serverStatusSection
                    .padding(.horizontal)
                
                ScrollView {
                    VStack(spacing: 20) {
                        if selectedOpportunity != nil {
                            // Style Selection
                            styleSelectionSection
                                .padding(.horizontal)
                            
                            // Generated Names
                            generatedNamesSection
                                .padding(.horizontal)
                            
                            // Custom Prompt (Advanced)
                            customPromptSection
                                .padding(.horizontal)
                        }
                    }
                    .padding(.vertical)
                }
            }
            .navigationTitle("Clone Name Studio")
            .navigationBarTitleDisplayMode(.large)
        }
        .sheet(isPresented: $showingAppPicker) {
            AppPickerView(selectedOpportunity: $selectedOpportunity, opportunities: opportunities)
        }
        .onAppear {
            loadOpportunities()
        }
    }
    
    // MARK: - App Selection Section
    private var appSelectionSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Select an App to Name")
                .font(.headline)
                .padding(.bottom, 4)
            
            Button(action: { showingAppPicker = true }) {
                HStack {
                    if let opportunity = selectedOpportunity {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(opportunity.appName)
                                .font(.headline)
                                .foregroundColor(.primary)
                            Text("\(opportunity.category) • Score: \(String(format: "%.1f", opportunity.cloneScore))")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    } else {
                        Text("Choose an opportunity to name")
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    Image(systemName: "chevron.down")
                        .foregroundColor(.secondary)
                }
                .padding()
                .background(Color(.systemGray6))
                .cornerRadius(12)
            }
        }
    }
    
    // MARK: - Server Status Section
    private var serverStatusSection: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("AI Service Status")
                    .font(.headline)
                
                Text("✅ Supabase Edge Function deployed")
                    .font(.caption)
                    .foregroundColor(.green)
                
                Text("🔐 Server-side API key protection")
                    .font(.caption)
                    .foregroundColor(.green)
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 2) {
                Text("Rate Limit")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Text("20/hour")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 8)
        .padding(.horizontal, 12)
        .background(Color(.systemGray6))
        .cornerRadius(8)
    }
    
    // MARK: - Style Selection Section
    private var styleSelectionSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Choose Naming Style")
                .font(.headline)
                .padding(.bottom, 4)
            
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 12) {
                    ForEach(NamingStyle.allCases, id: \.self) { style in
                        StyleChip(
                            style: style,
                            isSelected: selectedStyle == style,
                            action: { selectedStyle = style }
                        )
                    }
                }
            }
            
            // Generate button
            Button(action: generateNames) {
                HStack {
                    if isGenerating {
                        ProgressView()
                            .scaleEffect(0.8)
                    } else {
                        Image(systemName: "sparkles")
                    }
                    Text(isGenerating ? "Generating..." : "Generate 5 Names")
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.blue)
                .foregroundColor(.white)
                .cornerRadius(12)
            }
            .disabled(isGenerating)
        }
    }
    
    // MARK: - Generated Names Section
    private var generatedNamesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Generated Names")
                    .font(.headline)
                
                Spacer()
                
                if !generatedNames.isEmpty {
                    Button("Clear All") {
                        withAnimation {
                            generatedNames.removeAll()
                        }
                    }
                    .font(.caption)
                    .foregroundColor(.red)
                }
            }
            
            if generatedNames.isEmpty && !isGenerating {
                Text("Tap 'Generate' to create name variations")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 20)
            } else {
                ForEach(generatedNames) { name in
                    GeneratedNameCard(name: name)
                }
            }
        }
    }
    
    // MARK: - Custom Prompt Section
    private var customPromptSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Advanced: Custom Prompt")
                    .font(.headline)
                
                Spacer()
                
                Text("Optional")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(Color(.systemGray5))
                    .cornerRadius(4)
            }
            
            VStack(alignment: .leading, spacing: 8) {
                TextField("e.g., Make it sound like a Y Combinator startup", text: $customPrompt)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                
                if !customPrompt.isEmpty {
                    Button(action: generateWithCustomPrompt) {
                        HStack {
                            Image(systemName: "wand.and.stars")
                            Text("Generate with Custom Prompt")
                        }
                        .font(.subheadline)
                        .foregroundColor(.purple)
                    }
                }
            }
        }
    }
    
    // MARK: - Actions
    private func loadOpportunities() {
        opportunities = opportunityService.selectedOpportunities
        
        if selectedOpportunity == nil && !opportunities.isEmpty {
            selectedOpportunity = opportunities.first!
        }
    }
    
    private func generateNames() {
        guard let opportunity = selectedOpportunity else { return }
        
        isGenerating = true
        
        Task {
            let names = await aiService.generateCloneNames(
                for: opportunity, 
                style: selectedStyle, 
                count: 5
            )
            
            await MainActor.run {
                withAnimation {
                    generatedNames = names
                    isGenerating = false
                }
            }
        }
    }
    
    private func generateWithCustomPrompt() {
        guard let opportunity = selectedOpportunity, !customPrompt.isEmpty else { return }
        
        isGenerating = true
        
        Task {
            let names = await aiService.generateCloneNamesWithPrompt(
                for: opportunity, 
                customPrompt: customPrompt,
                count: 5
            )
            
            await MainActor.run {
                withAnimation {
                    generatedNames = names
                    isGenerating = false
                }
            }
        }
    }
}

// MARK: - Supporting Components
struct StyleChip: View {
    let style: NamingStyle
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                Image(systemName: style.icon)
                    .font(.title2)
                
                Text(style.rawValue)
                    .font(.caption)
                    .fontWeight(.semibold)
                
                Text(style.description)
                    .font(.system(size: 10))
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
            .frame(width: 100, height: 80)
            .padding(8)
            .background(isSelected ? Color.purple.opacity(0.1) : Color(.systemGray6))
            .foregroundColor(isSelected ? .purple : .primary)
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isSelected ? Color.purple : Color.clear, lineWidth: 2)
            )
        }
    }
}

struct GeneratedNameCard: View {
    let name: GeneratedName
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(name.name)
                    .font(.headline)
                
                Text(name.reasoning)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(10)
    }
}

// MARK: - App Picker
struct AppPickerView: View {
    @Binding var selectedOpportunity: Opportunity?
    let opportunities: [Opportunity]
    @Environment(\.dismiss) private var dismiss
    @State private var searchText = ""
    
    var filteredOpportunities: [Opportunity] {
        if searchText.isEmpty {
            return opportunities
        }
        return opportunities.filter { 
            $0.appName.localizedCaseInsensitiveContains(searchText) ||
            $0.category.localizedCaseInsensitiveContains(searchText)
        }
    }
    
    var body: some View {
        NavigationView {
            List {
                ForEach(filteredOpportunities) { opportunity in
                    AppPickerRow(
                        opportunity: opportunity,
                        isSelected: selectedOpportunity?.id == opportunity.id,
                        onSelect: {
                            selectedOpportunity = opportunity
                            dismiss()
                        }
                    )
                }
            }
            .searchable(text: $searchText, prompt: "Search opportunities")
            .navigationTitle("Select App to Name")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
        }
    }
}

struct AppPickerRow: View {
    let opportunity: Opportunity
    let isSelected: Bool
    let onSelect: () -> Void
    
    var body: some View {
        Button(action: onSelect) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(opportunity.appName)
                        .font(.headline)
                        .foregroundColor(.primary)
                    
                    HStack {
                        Text(opportunity.category)
                            .font(.caption)
                        
                        Text("•")
                            .font(.caption)
                        
                        Text("Score: \(String(format: "%.1f", opportunity.cloneScore))")
                            .font(.caption)
                    }
                    .foregroundColor(.secondary)
                }
                
                Spacer()
                
                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.purple)
                }
            }
            .padding(.vertical, 4)
        }
    }
}

#Preview {
    CloneNameStudioView()
}