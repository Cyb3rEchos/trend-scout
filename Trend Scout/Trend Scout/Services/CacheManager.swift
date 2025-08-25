import Foundation

class CacheManager {
    static let shared = CacheManager()
    
    private let cacheDirectory: URL
    private let cacheExpirationInterval: TimeInterval = 3600 // 1 hour
    
    private init() {
        let cacheDir = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first!
        self.cacheDirectory = cacheDir.appendingPathComponent("TrendScoutCache")
        
        // Create cache directory if it doesn't exist
        try? FileManager.default.createDirectory(at: cacheDirectory, withIntermediateDirectories: true)
    }
    
    // MARK: - Cache Keys
    enum CacheKey: String {
        case latestRankings = "latest_rankings"
        case categoryLeaders = "category_leaders"
        case categoryData = "category_" // Append category name
        
        func fileName() -> String {
            return "\(self.rawValue).json"
        }
    }
    
    // MARK: - Cache Entry
    private struct CacheEntry<T: Codable>: Codable {
        let data: T
        let timestamp: Date
        
        var isExpired: Bool {
            return Date().timeIntervalSince(timestamp) > CacheManager.shared.cacheExpirationInterval
        }
    }
    
    // MARK: - Cache Operations
    func save<T: Codable>(_ data: T, for key: CacheKey, category: String? = nil) {
        let cacheEntry = CacheEntry(data: data, timestamp: Date())
        let fileName = category != nil ? "\(key.rawValue)\(category!).json" : key.fileName()
        let fileURL = cacheDirectory.appendingPathComponent(fileName)
        
        do {
            let encoder = JSONEncoder()
            let encodedData = try encoder.encode(cacheEntry)
            try encodedData.write(to: fileURL)
            print("Cached data for key: \(fileName)")
        } catch {
            print("Failed to cache data: \(error)")
        }
    }
    
    func load<T: Codable>(_ type: T.Type, for key: CacheKey, category: String? = nil) -> T? {
        let fileName = category != nil ? "\(key.rawValue)\(category!).json" : key.fileName()
        let fileURL = cacheDirectory.appendingPathComponent(fileName)
        
        guard FileManager.default.fileExists(atPath: fileURL.path) else {
            print("No cache found for key: \(fileName)")
            return nil
        }
        
        do {
            let data = try Data(contentsOf: fileURL)
            let decoder = JSONDecoder()
            let cacheEntry = try decoder.decode(CacheEntry<T>.self, from: data)
            
            if cacheEntry.isExpired {
                print("Cache expired for key: \(fileName)")
                try? FileManager.default.removeItem(at: fileURL)
                return nil
            }
            
            print("Loaded cached data for key: \(fileName)")
            return cacheEntry.data
        } catch {
            print("Failed to load cache: \(error)")
            return nil
        }
    }
    
    func clearCache() {
        do {
            let files = try FileManager.default.contentsOfDirectory(at: cacheDirectory, includingPropertiesForKeys: nil)
            for file in files {
                try FileManager.default.removeItem(at: file)
            }
            print("Cache cleared successfully")
        } catch {
            print("Failed to clear cache: \(error)")
        }
    }
    
    func clearExpiredCache() {
        do {
            let files = try FileManager.default.contentsOfDirectory(at: cacheDirectory, includingPropertiesForKeys: [.contentModificationDateKey])
            let now = Date()
            
            for file in files {
                if let attributes = try? FileManager.default.attributesOfItem(atPath: file.path),
                   let modificationDate = attributes[.modificationDate] as? Date {
                    if now.timeIntervalSince(modificationDate) > cacheExpirationInterval {
                        try? FileManager.default.removeItem(at: file)
                        print("Removed expired cache file: \(file.lastPathComponent)")
                    }
                }
            }
        } catch {
            print("Failed to clear expired cache: \(error)")
        }
    }
}