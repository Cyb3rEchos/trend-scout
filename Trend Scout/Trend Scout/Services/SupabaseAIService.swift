import Foundation

// MARK: - Supabase Edge Function AI Service  
@MainActor
class SupabaseAIService: ObservableObject {
    static let shared = SupabaseAIService()
    private let supabaseManager = SupabaseManager.shared
    
    // Generate names using Supabase Edge Function
    func generateCloneNames(for opportunity: Opportunity, style: NamingStyle, count: Int = 5) async -> [GeneratedName] {
        print("🌐 DEBUG: SupabaseAIService.generateCloneNames called")
        print("   - App: \(opportunity.appName)")
        print("   - Style: \(style.rawValue)")
        
        do {
            // Prepare request data
            let requestData = [
                "opportunity": [
                    "appName": opportunity.appName,
                    "category": opportunity.category,
                    "buildEstimate": opportunity.buildEstimate.time,
                    "marketGap": opportunity.marketGap,
                    "competitiveEdge": opportunity.competitiveEdge
                ],
                "style": style.rawValue,
                "count": count
            ] as [String: Any]
            
            // Call Supabase Edge Function
            let response = try await callEdgeFunction(
                functionName: "generate-names",
                data: requestData
            )
            
            // Parse response
            if let names = response["names"] as? [[String: Any]] {
                let generatedNames = names.compactMap { nameData -> GeneratedName? in
                    guard let name = nameData["name"] as? String,
                          let reasoning = nameData["reasoning"] as? String else {
                        return nil
                    }
                    
                    return GeneratedName(
                        name: name,
                        style: "AI Generated",
                        reasoning: reasoning
                    )
                }
                
                print("✅ DEBUG: Parsed \(generatedNames.count) names from Supabase")
                return generatedNames
            }
            
            throw AIServiceError.invalidResponse
            
        } catch {
            print("❌ DEBUG: Supabase AI service failed: \(error)")
            
            // Check for rate limiting
            if let serviceError = error as? AIServiceError,
               case .rateLimited(let message) = serviceError {
                return [GeneratedName(
                    name: "Rate Limited",
                    style: "System",
                    reasoning: message
                )]
            }
            
            // Return fallback names
            return createFallbackNames(for: opportunity, style: style, count: count)
        }
    }
    
    // Generate with custom prompt
    func generateCloneNamesWithPrompt(for opportunity: Opportunity, customPrompt: String, count: Int = 5) async -> [GeneratedName] {
        print("💡 DEBUG: SupabaseAIService.generateCloneNamesWithPrompt called")
        
        do {
            let requestData = [
                "opportunity": [
                    "appName": opportunity.appName,
                    "category": opportunity.category,
                    "buildEstimate": opportunity.buildEstimate.time,
                    "marketGap": opportunity.marketGap
                ],
                "customPrompt": customPrompt,
                "count": count
            ] as [String: Any]
            
            let response = try await callEdgeFunction(
                functionName: "generate-names-custom",
                data: requestData
            )
            
            if let names = response["names"] as? [[String: Any]] {
                let generatedNames = names.compactMap { nameData -> GeneratedName? in
                    guard let name = nameData["name"] as? String,
                          let reasoning = nameData["reasoning"] as? String else {
                        return nil
                    }
                    
                    return GeneratedName(
                        name: name,
                        style: "Custom AI",
                        reasoning: reasoning
                    )
                }
                
                return generatedNames
            }
            
            throw AIServiceError.invalidResponse
            
        } catch {
            print("❌ DEBUG: Custom prompt generation failed: \(error)")
            return createFallbackNames(for: opportunity, style: .balanced, count: count)
        }
    }
    
    // MARK: - Private Methods
    private func callEdgeFunction(functionName: String, data: [String: Any]) async throws -> [String: Any] {
        guard let url = URL(string: "\(SupabaseConfig.url.absoluteString)/functions/v1/\(functionName)") else {
            throw AIServiceError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(SupabaseConfig.anonKey)", forHTTPHeaderField: "Authorization")
        
        // Add JSON body
        request.httpBody = try JSONSerialization.data(withJSONObject: data)
        
        let (responseData, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw AIServiceError.invalidResponse
        }
        
        print("📡 DEBUG: Edge function HTTP status: \(httpResponse.statusCode)")
        
        // Handle rate limiting
        if httpResponse.statusCode == 429 {
            let errorData = try? JSONSerialization.jsonObject(with: responseData) as? [String: Any]
            let message = errorData?["error"] as? String ?? "Too many requests"
            throw AIServiceError.rateLimited(message)
        }
        
        guard httpResponse.statusCode == 200 else {
            throw AIServiceError.serverError(httpResponse.statusCode)
        }
        
        guard let jsonResponse = try? JSONSerialization.jsonObject(with: responseData) as? [String: Any] else {
            throw AIServiceError.invalidResponse
        }
        
        return jsonResponse
    }
    
    private func createFallbackNames(for opportunity: Opportunity, style: NamingStyle, count: Int) -> [GeneratedName] {
        let baseName = opportunity.appName.components(separatedBy: " ").first ?? "App"
        
        return (1...count).map { i in
            GeneratedName(
                name: "\(baseName) \(style.rawValue) \(i)",
                style: "Fallback",
                reasoning: "AI service unavailable - fallback name generated"
            )
        }
    }
}

// MARK: - Error Types
enum AIServiceError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case rateLimited(String)
    case serverError(Int)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API URL"
        case .invalidResponse:
            return "Invalid response format"
        case .rateLimited(let message):
            return message
        case .serverError(let code):
            return "Server error: \(code)"
        }
    }
}