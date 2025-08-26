import SwiftUI

struct ContentView: View {
    var body: some View {
        TabView {
            OpportunityListView()
                .tabItem {
                    Image(systemName: "star.fill")
                    Text("Daily Brief")
                }
            
            CategoryBrowserView()
                .tabItem {
                    Image(systemName: "grid.circle")
                    Text("Categories")
                }
            
            CloneNameStudioView()
                .tabItem {
                    Image(systemName: "sparkles")
                    Text("Name Studio")
                }
            
            SettingsView()
                .tabItem {
                    Image(systemName: "gearshape")
                    Text("Settings")
                }
        }
    }
}

#Preview {
    ContentView()
}