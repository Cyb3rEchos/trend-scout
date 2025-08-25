"""AI-powered recommendation system using Hugging Face API for app improvement suggestions."""

import os
import logging
import requests
import time
from typing import List, Optional, Dict
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class AppRecommendation:
    """AI-generated app improvement recommendation."""
    app_name: str
    app_id: str
    category: str
    improvement_summary: str
    key_features: List[str]
    monetization_tips: List[str]
    build_estimate: str
    market_gap: str
    risk_factors: List[str]
    generated_at: str


class AIRecommender:
    """Generates AI-powered app improvement recommendations using Hugging Face."""
    
    def __init__(self, hf_api_key: Optional[str] = None):
        """Initialize AI recommender with Hugging Face API key."""
        self.hf_api_key = hf_api_key or os.getenv("HUGGING_FACE_API_KEY")
        if not self.hf_api_key:
            raise ValueError("Hugging Face API key required. Set HUGGING_FACE_API_KEY env var.")
        
        # Use HuggingFace router endpoint for OpenAI gpt-oss-120b model
        self.router_endpoint = "https://router.huggingface.co/v1/chat/completions"
        self.model_name = "openai/gpt-oss-120b"
        
        self.headers = {
            "Authorization": f"Bearer {self.hf_api_key}",
            "Content-Type": "application/json"
        }
        
    def generate_recommendation(self, app_data: Dict) -> AppRecommendation:
        """
        Generate AI-powered improvement recommendation for an app.
        
        Args:
            app_data: Dict containing app information (name, category, bundle_id, etc.)
            
        Returns:
            AppRecommendation object with detailed suggestions
        """
        try:
            # Create contextual prompt for the AI
            prompt = self._create_improvement_prompt(app_data)
            
            # Get AI response
            ai_response = self._query_hugging_face(prompt)
            
            # Parse and structure the response
            recommendation = self._parse_ai_response(app_data, ai_response)
            
            logger.info(f"Generated AI recommendation for {app_data.get('name', 'Unknown app')}")
            return recommendation
            
        except Exception as e:
            logger.error(f"Failed to generate AI recommendation: {e}")
            # Return fallback recommendation
            return self._create_fallback_recommendation(app_data)
    
    def _create_improvement_prompt(self, app_data: Dict) -> str:
        """Create a contextual prompt for AI recommendation generation."""
        
        name = app_data.get('name', 'Unknown App')
        category = app_data.get('category', 'Unknown')
        price = app_data.get('price', 0)
        rating_avg = app_data.get('rating_avg', 0)
        rating_count = app_data.get('rating_count', 0)
        desc_len = app_data.get('desc_len', 0)
        clone_difficulty = app_data.get('clone_difficulty', 'MODERATE')
        revenue_potential = app_data.get('revenue_potential', 'MODEST_REVENUE')
        total_score = app_data.get('total', 0)
        
        prompt = f"""You are an expert app developer and business strategist. Analyze this App Store app and provide actionable improvement suggestions for creating a competitive clone that can be built quickly.

App Details:
- Name: {name}
- Category: {category}  
- Price: ${price}
- Rating: {rating_avg} stars ({rating_count:,} ratings)
- Description Length: {desc_len} characters
- Clone Difficulty: {clone_difficulty}
- Revenue Potential: {revenue_potential}
- Competitive Score: {total_score}/5.0

Requirements for your recommendation:
1. Focus on ONE night build improvements (3-4 hours max)
2. Identify specific market gaps or pain points this app doesn't address well
3. Suggest 2-3 key features that would differentiate a clone
4. Recommend monetization strategies appropriate for indie developers
5. Estimate realistic build time and highlight potential risks

Provide a concise response in this format:
IMPROVEMENT: [One sentence summary of main improvement opportunity]
FEATURES: [2-3 specific features to add, separated by | ]  
MONETIZATION: [2 monetization tips, separated by | ]
BUILD_TIME: [Realistic estimate like "3-4 hours" or "1-2 nights"]
MARKET_GAP: [One sentence about unmet user need]
RISKS: [1-2 main risks, separated by | ]

Keep it actionable and focused on quick wins for an indie developer."""

        return prompt
    
    def _query_hugging_face(self, prompt: str, max_retries: int = 3) -> str:
        """Query Hugging Face API with retry logic."""
        
        for attempt in range(max_retries):
            try:
                # Use HuggingFace router with OpenAI-compatible chat completions format
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 400,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
                
                response = requests.post(self.router_endpoint, headers=self.headers, json=payload, timeout=60)
                response.raise_for_status()
                
                result = response.json()
                
                # Handle OpenAI-compatible response format
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"].strip()
                else:
                    raise ValueError(f"Unexpected API response format: {result}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"HuggingFace API attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
        
        raise Exception("All HuggingFace API attempts failed")
    
    def _parse_ai_response(self, app_data: Dict, ai_response: str) -> AppRecommendation:
        """Parse AI response into structured recommendation."""
        
        # Default values
        improvement_summary = "Optimize user experience and add premium features"
        key_features = ["Enhanced UI/UX", "Offline functionality", "Premium features"]
        monetization_tips = ["Freemium model with premium features", "In-app purchases for advanced tools"]
        build_estimate = "3-4 hours"
        market_gap = "Existing app lacks polish and advanced features"
        risk_factors = ["Market competition", "User acquisition challenges"]
        
        try:
            # Parse structured response
            lines = ai_response.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('IMPROVEMENT:'):
                    improvement_summary = line.replace('IMPROVEMENT:', '').strip()
                elif line.startswith('FEATURES:'):
                    features_text = line.replace('FEATURES:', '').strip()
                    key_features = [f.strip() for f in features_text.split('|') if f.strip()]
                elif line.startswith('MONETIZATION:'):
                    monetization_text = line.replace('MONETIZATION:', '').strip()
                    monetization_tips = [m.strip() for m in monetization_text.split('|') if m.strip()]
                elif line.startswith('BUILD_TIME:'):
                    build_estimate = line.replace('BUILD_TIME:', '').strip()
                elif line.startswith('MARKET_GAP:'):
                    market_gap = line.replace('MARKET_GAP:', '').strip()
                elif line.startswith('RISKS:'):
                    risks_text = line.replace('RISKS:', '').strip()
                    risk_factors = [r.strip() for r in risks_text.split('|') if r.strip()]
                    
        except Exception as e:
            logger.warning(f"Failed to parse AI response, using defaults: {e}")
            # Keep default values if parsing fails
        
        return AppRecommendation(
            app_name=app_data.get('name', 'Unknown App'),
            app_id=app_data.get('app_id', ''),
            category=app_data.get('category', 'Unknown'),
            improvement_summary=improvement_summary,
            key_features=key_features[:3],  # Limit to 3 features
            monetization_tips=monetization_tips[:2],  # Limit to 2 tips
            build_estimate=build_estimate,
            market_gap=market_gap,
            risk_factors=risk_factors[:2],  # Limit to 2 risks
            generated_at=time.strftime('%Y-%m-%d %H:%M:%S')
        )
    
    def _create_fallback_recommendation(self, app_data: Dict) -> AppRecommendation:
        """Create fallback recommendation if AI fails."""
        
        category = app_data.get('category', 'Unknown')
        name = app_data.get('name', 'Unknown App')
        clone_difficulty = app_data.get('clone_difficulty', 'MODERATE')
        
        # Category-specific fallbacks
        fallback_recommendations = {
            'Utilities': {
                'improvement': 'Add modern UI design and premium utility features',
                'features': ['Dark mode support', 'Widget functionality', 'Cloud sync'],
                'monetization': ['Pro version with advanced features', 'Remove ads subscription'],
                'build_time': '2-3 hours',
                'gap': 'Most utility apps lack modern design and user-friendly interfaces',
                'risks': ['Saturated market', 'Low user engagement']
            },
            'Productivity': {
                'improvement': 'Integrate AI assistance and cross-platform sync',
                'features': ['AI-powered suggestions', 'Team collaboration', 'Smart notifications'],
                'monetization': ['Subscription for premium AI features', 'Team plans'],
                'build_time': '4-6 hours',
                'gap': 'Many productivity apps lack intelligent automation features',
                'risks': ['Complex feature set', 'High user expectations']
            },
            'Photo & Video': {
                'improvement': 'Add unique filters and AI-powered editing tools',
                'features': ['Custom AI filters', 'One-tap enhancements', 'Social sharing'],
                'monetization': ['Premium filter packs', 'Watermark removal'],
                'build_time': '3-4 hours',
                'gap': 'Generic editing apps lack distinctive creative tools',
                'risks': ['Technical complexity', 'Content creation competition']
            }
        }
        
        fallback = fallback_recommendations.get(category, fallback_recommendations['Utilities'])
        
        return AppRecommendation(
            app_name=name,
            app_id=app_data.get('app_id', ''),
            category=category,
            improvement_summary=fallback['improvement'],
            key_features=fallback['features'],
            monetization_tips=fallback['monetization'],
            build_estimate=fallback['build_time'],
            market_gap=fallback['gap'],
            risk_factors=fallback['risks'],
            generated_at=time.strftime('%Y-%m-%d %H:%M:%S')
        )
    
    def generate_batch_recommendations(self, apps_data: List[Dict]) -> List[AppRecommendation]:
        """Generate recommendations for multiple apps with rate limiting."""
        
        recommendations = []
        
        for i, app_data in enumerate(apps_data, 1):
            try:
                logger.info(f"Generating recommendation {i}/{len(apps_data)}: {app_data.get('name', 'Unknown')}")
                
                recommendation = self.generate_recommendation(app_data)
                recommendations.append(recommendation)
                
                # Rate limiting - be respectful to API
                if i < len(apps_data):  # Don't sleep after the last request
                    time.sleep(2)  # 2 second delay between requests
                    
            except Exception as e:
                logger.error(f"Failed to generate recommendation for app {i}: {e}")
                # Continue with other apps even if one fails
                continue
        
        logger.info(f"Generated {len(recommendations)}/{len(apps_data)} recommendations successfully")
        return recommendations