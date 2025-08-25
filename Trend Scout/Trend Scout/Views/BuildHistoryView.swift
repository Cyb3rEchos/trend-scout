import SwiftUI

struct BuildHistoryView: View {
    @StateObject private var buildTracker = BuildTracker()
    @State private var selectedTab = 0
    
    var body: some View {
        NavigationView {
            VStack {
                Picker("Status", selection: $selectedTab) {
                    Text("Active").tag(0)
                    Text("Completed").tag(1)
                    Text("All").tag(2)
                }
                .pickerStyle(.segmented)
                .padding()
                
                List {
                    ForEach(filteredRecords, id: \.id) { record in
                        BuildRecordCard(record: record)
                            .listRowSeparator(.hidden)
                            .listRowInsets(EdgeInsets(top: 4, leading: 16, bottom: 4, trailing: 16))
                    }
                }
                .listStyle(.plain)
                .overlay {
                    if filteredRecords.isEmpty {
                        VStack {
                            Image(systemName: "hammer.slash")
                                .font(.system(size: 50))
                                .foregroundColor(.gray)
                            Text("No builds found")
                                .font(.title2)
                                .fontWeight(.medium)
                            Text("Start building an opportunity to see it here")
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }
            .navigationTitle("Build History")
        }
    }
    
    private var filteredRecords: [BuildRecord] {
        switch selectedTab {
        case 0:
            return buildTracker.inProgressBuilds
        case 1:
            return buildTracker.completedBuilds
        default:
            return buildTracker.buildHistory.sorted { $0.dateBuilt > $1.dateBuilt }
        }
    }
}

struct BuildRecordCard: View {
    let record: BuildRecord
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: record.status.icon)
                    .foregroundColor(record.status.color)
                    .font(.title2)
                
                VStack(alignment: .leading, spacing: 2) {
                    Text(record.title)
                        .font(.headline)
                        .fontWeight(.semibold)
                    Text(record.status.displayName)
                        .font(.subheadline)
                        .foregroundColor(record.status.color)
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 2) {
                    Text(record.dateBuilt.formatted(date: .abbreviated, time: .omitted))
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(record.dateBuilt.formatted(date: .omitted, time: .shortened))
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            if record.status == .completed {
                HStack {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.green)
                        .font(.caption)
                    Text("Completed \(timeAgo(from: record.dateBuilt))")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                }
            } else if record.status == .wip {
                HStack {
                    Image(systemName: "clock.fill")
                        .foregroundColor(.orange)
                        .font(.caption)
                    Text("Started \(timeAgo(from: record.dateBuilt))")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                }
            } else if record.status == .paused {
                HStack {
                    Image(systemName: "pause.circle.fill")
                        .foregroundColor(.gray)
                        .font(.caption)
                    Text("Paused \(timeAgo(from: record.dateBuilt))")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
    }
    
    private func timeAgo(from date: Date) -> String {
        let interval = Date().timeIntervalSince(date)
        
        if interval < 60 {
            return "just now"
        } else if interval < 3600 {
            let minutes = Int(interval / 60)
            return "\(minutes)m ago"
        } else if interval < 86400 {
            let hours = Int(interval / 3600)
            return "\(hours)h ago"
        } else {
            let days = Int(interval / 86400)
            return "\(days)d ago"
        }
    }
}

#Preview {
    BuildHistoryView()
}