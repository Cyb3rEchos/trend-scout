import SwiftUI

struct SettingsView: View {
    @AppStorage("preferredCategories") private var preferredCategoriesData: Data = Data()
    @AppStorage("showOnlyTonight") private var showOnlyTonight: Bool = false
    @AppStorage("enableNotifications") private var enableNotifications: Bool = true
    @State private var preferredCategories: Set<String> = []
    
    let allCategories = [
        "Utilities", "Productivity", "Photo & Video", "Health & Fitness",
        "Lifestyle", "Finance", "Music", "Education", "Graphics & Design", "Entertainment"
    ]
    
    var body: some View {
        NavigationView {
            Form {
                Section {
                    HStack {
                        VStack(alignment: .leading) {
                            Text("Trend Scout")
                                .font(.title2)
                                .fontWeight(.bold)
                            Text("App Store Trend Analysis")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                        
                        Text("📱")
                            .font(.system(size: 40))
                    }
                    .padding(.vertical, 8)
                }
                
                Section("Preferences") {
                    Toggle("Show Only Tonight's Opportunities", isOn: $showOnlyTonight)
                    Toggle("Enable Notifications", isOn: $enableNotifications)
                }
                
                Section("Preferred Categories") {
                    ForEach(allCategories, id: \.self) { category in
                        HStack {
                            Text(category)
                            Spacer()
                            if preferredCategories.contains(category) {
                                Image(systemName: "checkmark")
                                    .foregroundColor(.blue)
                            }
                        }
                        .contentShape(Rectangle())
                        .onTapGesture {
                            toggleCategory(category)
                        }
                    }
                }
                
                Section("Build Tracking") {
                    NavigationLink("Build History", destination: BuildHistoryView())
                }
                
                Section("Data") {
                    Button("Refresh Data") {
                        // Trigger data refresh
                    }
                    
                    Button("Clear Cache") {
                        // Clear local cache
                    }
                }
                
                Section("About") {
                    HStack {
                        Text("Version")
                        Spacer()
                        Text("1.0.0")
                            .foregroundColor(.secondary)
                    }
                    
                    HStack {
                        Text("Build")
                        Spacer()
                        Text("1")
                            .foregroundColor(.secondary)
                    }
                    
                    Link("Support", destination: URL(string: "https://github.com/anthropics/claude-code/issues")!)
                    Link("Privacy Policy", destination: URL(string: "https://example.com/privacy")!)
                }
            }
            .navigationTitle("Settings")
        }
        .onAppear {
            loadPreferredCategories()
        }
        .onChange(of: preferredCategories) {
            savePreferredCategories()
        }
    }
    
    private func toggleCategory(_ category: String) {
        if preferredCategories.contains(category) {
            preferredCategories.remove(category)
        } else {
            preferredCategories.insert(category)
        }
    }
    
    private func loadPreferredCategories() {
        if let categories = try? JSONDecoder().decode(Set<String>.self, from: preferredCategoriesData) {
            preferredCategories = categories
        }
    }
    
    private func savePreferredCategories() {
        if let data = try? JSONEncoder().encode(preferredCategories) {
            preferredCategoriesData = data
        }
    }
}

#Preview {
    SettingsView()
}