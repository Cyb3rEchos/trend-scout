import Foundation
import SwiftUI

@MainActor
class UserSelectionService: ObservableObject {
    static let shared = UserSelectionService()
    
    @Published private(set) var selectedOpportunities: [String] = []
    
    private let userDefaults = UserDefaults.standard
    private let selectedOpportunitiesKey = "selected_opportunities"
    
    private init() {
        loadSelectedOpportunities()
    }
    
    func addToDaily(_ opportunityId: String) {
        if !selectedOpportunities.contains(opportunityId) {
            selectedOpportunities.append(opportunityId)
            saveSelectedOpportunities()
        }
    }
    
    func removeFromDaily(_ opportunityId: String) {
        selectedOpportunities.removeAll { $0 == opportunityId }
        saveSelectedOpportunities()
    }
    
    func isSelected(_ opportunityId: String) -> Bool {
        selectedOpportunities.contains(opportunityId)
    }
    
    func toggleSelection(_ opportunityId: String) {
        if isSelected(opportunityId) {
            removeFromDaily(opportunityId)
        } else {
            addToDaily(opportunityId)
        }
    }
    
    private func loadSelectedOpportunities() {
        if let data = userDefaults.data(forKey: selectedOpportunitiesKey),
           let decoded = try? JSONDecoder().decode([String].self, from: data) {
            selectedOpportunities = decoded
        }
    }
    
    func clearAllSelections() {
        selectedOpportunities.removeAll()
        saveSelectedOpportunities()
    }
    
    private func saveSelectedOpportunities() {
        if let data = try? JSONEncoder().encode(selectedOpportunities) {
            userDefaults.set(data, forKey: selectedOpportunitiesKey)
        }
    }
}