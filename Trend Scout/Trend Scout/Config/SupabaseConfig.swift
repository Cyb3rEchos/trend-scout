import Foundation

struct SupabaseConfig {
    // IMPORTANT: For production, use environment variables or a secure configuration method
    // These should not be hardcoded in a real app
    
    static let url = URL(string: "https://ltebiafearfhlxmmekoa.supabase.co")!
    
    // Use the anon key for client-side access (read-only operations)
    // The service key should never be exposed in client code
    static let anonKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx0ZWJpYWZlYXJmaGx4bW1la29hIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU2MTQ1ODIsImV4cCI6MjA3MTE5MDU4Mn0.dkYMLdW_cxL6m3sl8Qpls5a5sLY-OxeMMBGtDIlNN0c"
    
    // Table names
    static let scoutResultsTable = "scout_results"
    
    // Query limits
    static let defaultQueryLimit = 100
    static let categoryQueryLimit = 50
}