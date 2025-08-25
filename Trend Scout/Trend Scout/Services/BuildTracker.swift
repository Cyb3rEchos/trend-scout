import Foundation
import SwiftUI

class BuildTracker: ObservableObject {
    @Published private(set) var builtApps: Set<String> = []
    @Published private(set) var buildHistory: [BuildRecord] = []
    
    private let userDefaults = UserDefaults.standard
    private let builtAppsKey = "built_apps"
    private let buildHistoryKey = "build_history"
    
    init() {
        loadData()
    }
    
    func updateBuildStatus(_ opportunityId: String, status: BuildStatus, title: String? = nil) {
        if let existingIndex = buildHistory.firstIndex(where: { $0.opportunityId == opportunityId }) {
            let existing = buildHistory[existingIndex]
            buildHistory[existingIndex] = BuildRecord(
                id: existing.id,
                opportunityId: opportunityId,
                title: title ?? existing.title,
                dateBuilt: status == .wip && existing.status == .notStarted ? Date() : existing.dateBuilt,
                status: status
            )
        } else {
            buildHistory.append(BuildRecord(
                id: UUID(),
                opportunityId: opportunityId,
                title: title ?? "Untitled Opportunity",
                dateBuilt: Date(),
                status: status
            ))
        }
        
        // Update built apps set
        if status == .completed {
            builtApps.insert(opportunityId)
        } else {
            builtApps.remove(opportunityId)
        }
        
        saveData()
    }
    
    func advanceToNextStatus(_ opportunityId: String, title: String? = nil) {
        let currentStatus = getBuildStatus(opportunityId)
        if let nextStatus = currentStatus.nextStatus {
            updateBuildStatus(opportunityId, status: nextStatus, title: title)
        }
    }
    
    func togglePause(_ opportunityId: String) {
        let currentStatus = getBuildStatus(opportunityId)
        if currentStatus.canTogglePause {
            let newStatus: BuildStatus = currentStatus == .wip ? .paused : .wip
            updateBuildStatus(opportunityId, status: newStatus)
        }
    }
    
    func resetBuild(_ opportunityId: String) {
        if let index = buildHistory.firstIndex(where: { $0.opportunityId == opportunityId }) {
            buildHistory.remove(at: index)
        }
        builtApps.remove(opportunityId)
        saveData()
    }
    
    func getBuildStatus(_ opportunityId: String) -> BuildStatus {
        return getBuildRecord(for: opportunityId)?.status ?? .notStarted
    }
    
    func isBuilt(_ opportunityId: String) -> Bool {
        return getBuildStatus(opportunityId) == .completed
    }
    
    func getBuildRecord(for opportunityId: String) -> BuildRecord? {
        buildHistory.first { $0.opportunityId == opportunityId }
    }
    
    var completedBuilds: [BuildRecord] {
        buildHistory.filter { $0.status == .completed }.sorted { $0.dateBuilt > $1.dateBuilt }
    }
    
    var activeBuilds: [BuildRecord] {
        buildHistory.filter { $0.status == .wip }.sorted { $0.dateBuilt > $1.dateBuilt }
    }
    
    var pausedBuilds: [BuildRecord] {
        buildHistory.filter { $0.status == .paused }.sorted { $0.dateBuilt > $1.dateBuilt }
    }
    
    var inProgressBuilds: [BuildRecord] {
        buildHistory.filter { $0.status == .wip || $0.status == .paused }.sorted { $0.dateBuilt > $1.dateBuilt }
    }
    
    private func loadData() {
        if let builtAppsData = userDefaults.data(forKey: builtAppsKey),
           let decodedBuiltApps = try? JSONDecoder().decode(Set<String>.self, from: builtAppsData) {
            builtApps = decodedBuiltApps
        }
        
        if let buildHistoryData = userDefaults.data(forKey: buildHistoryKey),
           let decodedBuildHistory = try? JSONDecoder().decode([BuildRecord].self, from: buildHistoryData) {
            buildHistory = decodedBuildHistory
        }
    }
    
    private func saveData() {
        if let builtAppsData = try? JSONEncoder().encode(builtApps) {
            userDefaults.set(builtAppsData, forKey: builtAppsKey)
        }
        
        if let buildHistoryData = try? JSONEncoder().encode(buildHistory) {
            userDefaults.set(buildHistoryData, forKey: buildHistoryKey)
        }
    }
}

struct BuildRecord: Identifiable, Codable {
    let id: UUID
    let opportunityId: String
    let title: String
    let dateBuilt: Date
    let status: BuildStatus
}

enum BuildStatus: String, Codable, CaseIterable {
    case notStarted = "not_started"
    case wip = "wip"
    case paused = "paused"
    case completed = "completed"
    
    var displayName: String {
        switch self {
        case .notStarted: return "Not Started"
        case .wip: return "Work in Progress"
        case .paused: return "Paused"
        case .completed: return "Completed"
        }
    }
    
    var shortName: String {
        switch self {
        case .notStarted: return "Start"
        case .wip: return "WIP"
        case .paused: return "Paused"
        case .completed: return "Done"
        }
    }
    
    var color: Color {
        switch self {
        case .notStarted: return .blue
        case .wip: return .orange
        case .paused: return .gray
        case .completed: return .green
        }
    }
    
    var icon: String {
        switch self {
        case .notStarted: return "play.circle.fill"
        case .wip: return "hammer.fill"
        case .paused: return "pause.circle.fill"
        case .completed: return "checkmark.circle.fill"
        }
    }
    
    var nextStatus: BuildStatus? {
        switch self {
        case .notStarted: return .wip
        case .wip: return .completed
        case .paused: return .wip
        case .completed: return nil
        }
    }
    
    var canTogglePause: Bool {
        return self == .wip || self == .paused
    }
}