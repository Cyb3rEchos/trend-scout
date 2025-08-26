import Foundation

// MARK: - Generated Name Model
struct GeneratedName: Identifiable {
    let id = UUID().uuidString
    let name: String
    let style: String
    let reasoning: String
}

// MARK: - Naming Styles
enum NamingStyle: String, CaseIterable {
    case direct = "Direct"
    case trendy = "Trendy"
    case playful = "Fun"
    case premium = "Premium"
    case balanced = "Balanced"
    
    var icon: String {
        switch self {
        case .direct: return "arrow.right"
        case .trendy: return "sparkles"
        case .playful: return "face.smiling"
        case .premium: return "crown"
        case .balanced: return "scale.3d"
        }
    }
    
    var description: String {
        switch self {
        case .direct: return "Similar to original"
        case .trendy: return "Modern startup vibe"
        case .playful: return "Fun & approachable"
        case .premium: return "High-end feel"
        case .balanced: return "Professional blend"
        }
    }
}