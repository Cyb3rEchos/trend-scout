#!/usr/bin/env python3
"""
iOS-Optimized AI Recommendation System

Generates structured AI recommendations specifically formatted for clean display 
in iOS apps with proper JSON structure and mobile-friendly formatting.
"""

import os
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from dotenv import load_dotenv
from trendscout.ai_recommender import AIRecommender

# Load environment variables
load_dotenv()


@dataclass
class IOSRecommendation:
    """iOS-optimized recommendation structure."""
    # Core identification
    app_name: str
    app_id: str
    category: str
    clone_score: float  # 1-5 scoring
    
    # iOS display fields
    title: str  # Short catchy title for iOS card
    subtitle: str  # One-line description 
    emoji: str  # Category emoji for iOS
    
    # Structured features for iOS list display
    key_features: List[Dict[str, str]]  # [{"icon": "🎨", "title": "AI Filters", "desc": "Smart photo enhancement"}]
    
    # Monetization for iOS business model display
    revenue_model: Dict[str, str]  # {"type": "freemium", "primary": "Premium filters", "secondary": "Remove watermarks"}
    
    # Build planning for iOS project view
    build_estimate: Dict[str, str]  # {"time": "2-3 hours", "difficulty": "Easy", "priority": "Tonight"}
    
    # Market insight for iOS strategy display
    market_gap: str  # Single sentence opportunity
    competitive_edge: str  # How to beat the original
    
    # Risk assessment for iOS decision making
    risks: List[str]  # Max 2 risks for mobile display
    
    # Technical specs for iOS development planning
    ios_features: List[str]  # iOS-specific features to implement
    
    # Metadata
    confidence: float  # AI confidence 0-1
    generated_at: str


class IOSOptimizedAIRecommender(AIRecommender):
    """AI recommender optimized for iOS app display."""
    
    def __init__(self, hf_api_key: Optional[str] = None):
        """Initialize with iOS-specific configuration."""
        super().__init__(hf_api_key)
        
        # Category emojis for iOS display
        self.category_emojis = {
            'Photo & Video': '📷',
            'Utilities': '🔧', 
            'Productivity': '📋',
            'Health & Fitness': '💪',
            'Lifestyle': '🌟',
            'Finance': '💰',
            'Music': '🎵',
            'Education': '📚',
            'Games': '🎮',
            'Entertainment': '🎬'
        }
    
    def _create_ios_optimized_prompt(self, app_data: Dict) -> str:
        """Create prompt optimized for iOS-friendly responses."""
        
        name = app_data.get('name', 'Unknown App')
        category = app_data.get('category', 'Unknown')
        price = app_data.get('price', 0)
        rating_avg = app_data.get('rating_avg', 0)
        rating_count = app_data.get('rating_count', 0)
        desc_len = app_data.get('desc_len', 0)
        clone_difficulty = app_data.get('clone_difficulty', 'MODERATE')
        revenue_potential = app_data.get('revenue_potential', 'MODEST_REVENUE')
        total_score = app_data.get('total', 0)
        
        prompt = f"""You are an expert iOS app developer and product strategist. Analyze this App Store app and provide a structured recommendation for building a competitive clone optimized for indie iOS development.

App Analysis:
- Name: {name}
- Category: {category}  
- Price: ${price}
- Rating: {rating_avg} stars ({rating_count:,} ratings)
- Clone Difficulty: {clone_difficulty}
- Market Score: {total_score}/5.0

Create a recommendation that will be displayed in a mobile iOS app interface. Focus on:
1. Quick-build opportunities (2-4 hours max)
2. Clear competitive advantages
3. Realistic iOS implementation
4. Mobile-first monetization

Respond in this EXACT structured format:

TITLE: [Catchy 3-4 word title for iOS card display]
SUBTITLE: [One sentence opportunity summary]
MARKET_GAP: [One sentence unmet user need]
COMPETITIVE_EDGE: [One sentence how to beat the original]

FEATURE_1: [Icon emoji]|[Feature title]|[Brief description]
FEATURE_2: [Icon emoji]|[Feature title]|[Brief description]  
FEATURE_3: [Icon emoji]|[Feature title]|[Brief description]

REVENUE_TYPE: [freemium/paid/subscription]
REVENUE_PRIMARY: [Main monetization method]
REVENUE_SECONDARY: [Secondary revenue stream]

BUILD_TIME: [2-3 hours/3-4 hours/1-2 nights]
BUILD_DIFFICULTY: [Easy/Medium/Hard]
BUILD_PRIORITY: [Tonight/This Week/This Month]

IOS_FEATURE_1: [iOS-specific feature to implement]
IOS_FEATURE_2: [iOS-specific feature to implement]
IOS_FEATURE_3: [iOS-specific feature to implement]

RISK_1: [Main risk factor]
RISK_2: [Secondary risk factor]

CONFIDENCE: [0.1-1.0 confidence score]

Keep all responses concise and mobile-friendly. Each line should be under 60 characters for iOS display."""

        return prompt
    
    def generate_ios_recommendation(self, app_data: Dict) -> IOSRecommendation:
        """Generate iOS-optimized recommendation."""
        try:
            # Create iOS-optimized prompt
            prompt = self._create_ios_optimized_prompt(app_data)
            
            # Get AI response
            ai_response = self._query_hugging_face(prompt)
            
            # Parse into iOS structure
            recommendation = self._parse_ios_response(app_data, ai_response)
            
            return recommendation
            
        except Exception as e:
            print(f"AI generation failed, using fallback: {e}")
            return self._create_ios_fallback(app_data)
    
    def _parse_ios_response(self, app_data: Dict, ai_response: str) -> IOSRecommendation:
        """Parse AI response into iOS-optimized structure."""
        
        # Default values
        title = f"Clone {app_data.get('category', 'App')}"
        subtitle = "Build a competitive alternative"
        market_gap = "Existing app lacks modern iOS design"
        competitive_edge = "Focus on better user experience"
        
        features = [
            {"icon": "🚀", "title": "Modern UI", "desc": "Clean iOS design"},
            {"icon": "⚡", "title": "Fast Performance", "desc": "Optimized for speed"},
            {"icon": "🎯", "title": "Focus Mode", "desc": "Distraction-free experience"}
        ]
        
        revenue_model = {
            "type": "freemium",
            "primary": "Premium features",
            "secondary": "Remove ads"
        }
        
        build_estimate = {
            "time": "3-4 hours",
            "difficulty": "Medium", 
            "priority": "This Week"
        }
        
        ios_features = [
            "SwiftUI interface",
            "Core Data storage",
            "StoreKit integration"
        ]
        
        risks = ["Market competition", "User acquisition"]
        confidence = 0.7
        
        try:
            lines = ai_response.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('TITLE:'):
                    title = line.replace('TITLE:', '').strip()
                elif line.startswith('SUBTITLE:'):
                    subtitle = line.replace('SUBTITLE:', '').strip()
                elif line.startswith('MARKET_GAP:'):
                    market_gap = line.replace('MARKET_GAP:', '').strip()
                elif line.startswith('COMPETITIVE_EDGE:'):
                    competitive_edge = line.replace('COMPETITIVE_EDGE:', '').strip()
                elif line.startswith('FEATURE_'):
                    feature_text = line.split(':', 1)[1].strip()
                    parts = feature_text.split('|')
                    if len(parts) == 3:
                        idx = int(line.split('_')[1].split(':')[0]) - 1
                        if 0 <= idx < 3:
                            features[idx] = {
                                "icon": parts[0].strip(),
                                "title": parts[1].strip(),
                                "desc": parts[2].strip()
                            }
                elif line.startswith('REVENUE_TYPE:'):
                    revenue_model["type"] = line.replace('REVENUE_TYPE:', '').strip()
                elif line.startswith('REVENUE_PRIMARY:'):
                    revenue_model["primary"] = line.replace('REVENUE_PRIMARY:', '').strip()
                elif line.startswith('REVENUE_SECONDARY:'):
                    revenue_model["secondary"] = line.replace('REVENUE_SECONDARY:', '').strip()
                elif line.startswith('BUILD_TIME:'):
                    build_estimate["time"] = line.replace('BUILD_TIME:', '').strip()
                elif line.startswith('BUILD_DIFFICULTY:'):
                    build_estimate["difficulty"] = line.replace('BUILD_DIFFICULTY:', '').strip()
                elif line.startswith('BUILD_PRIORITY:'):
                    build_estimate["priority"] = line.replace('BUILD_PRIORITY:', '').strip()
                elif line.startswith('IOS_FEATURE_'):
                    feature = line.split(':', 1)[1].strip()
                    idx = int(line.split('_')[2].split(':')[0]) - 1
                    if 0 <= idx < 3:
                        ios_features[idx] = feature
                elif line.startswith('RISK_'):
                    risk = line.split(':', 1)[1].strip()
                    idx = int(line.split('_')[1].split(':')[0]) - 1
                    if 0 <= idx < 2:
                        risks[idx] = risk
                elif line.startswith('CONFIDENCE:'):
                    try:
                        confidence = float(line.replace('CONFIDENCE:', '').strip())
                    except ValueError:
                        confidence = 0.7
                        
        except Exception as e:
            print(f"Parse error, using defaults: {e}")
            # Keep default values
        
        # Get category emoji
        category = app_data.get('category', 'Unknown')
        emoji = self.category_emojis.get(category, '📱')
        
        return IOSRecommendation(
            app_name=app_data.get('name', 'Unknown App'),
            app_id=app_data.get('app_id', ''),
            category=category,
            clone_score=app_data.get('total', 0),
            title=title,
            subtitle=subtitle,
            emoji=emoji,
            key_features=features,
            revenue_model=revenue_model,
            build_estimate=build_estimate,
            market_gap=market_gap,
            competitive_edge=competitive_edge,
            risks=risks,
            ios_features=ios_features,
            confidence=confidence,
            generated_at=app_data.get('generated_at', '')
        )
    
    def _create_ios_fallback(self, app_data: Dict) -> IOSRecommendation:
        """Create fallback recommendation for iOS."""
        category = app_data.get('category', 'Unknown')
        
        fallbacks = {
            'Photo & Video': {
                'title': 'Photo Editor Pro',
                'subtitle': 'Advanced editing with AI filters',
                'market_gap': 'Most editors lack intuitive AI enhancements',
                'competitive_edge': 'One-tap AI improvements with custom presets',
                'features': [
                    {"icon": "🎨", "title": "AI Filters", "desc": "Smart auto-enhancement"},
                    {"icon": "✂️", "title": "Quick Edit", "desc": "One-tap improvements"},
                    {"icon": "☁️", "title": "Cloud Sync", "desc": "Cross-device editing"}
                ],
                'ios_features': ['Core Image filters', 'Photos framework', 'Metal performance']
            },
            'Utilities': {
                'title': 'Smart Utility',
                'subtitle': 'Essential iOS tools in one app',
                'market_gap': 'Utility apps lack modern iOS design',
                'competitive_edge': 'Native iOS widgets and shortcuts',
                'features': [
                    {"icon": "🔧", "title": "Multi-Tool", "desc": "Combined utilities"},
                    {"icon": "📱", "title": "Widgets", "desc": "Home screen access"},
                    {"icon": "⚡", "title": "Shortcuts", "desc": "Siri integration"}
                ],
                'ios_features': ['WidgetKit support', 'Shortcuts app', 'Background processing']
            }
        }
        
        fallback = fallbacks.get(category, fallbacks['Utilities'])
        emoji = self.category_emojis.get(category, '📱')
        
        return IOSRecommendation(
            app_name=app_data.get('name', 'Unknown App'),
            app_id=app_data.get('app_id', ''),
            category=category,
            clone_score=app_data.get('total', 0),
            title=fallback['title'],
            subtitle=fallback['subtitle'],
            emoji=emoji,
            key_features=fallback['features'],
            revenue_model={
                "type": "freemium",
                "primary": "Premium features",
                "secondary": "Remove ads"
            },
            build_estimate={
                "time": "3-4 hours",
                "difficulty": "Medium",
                "priority": "This Week"
            },
            market_gap=fallback['market_gap'],
            competitive_edge=fallback['competitive_edge'],
            risks=["Market competition", "User acquisition"],
            ios_features=fallback['ios_features'],
            confidence=0.6,
            generated_at=''
        )


def demo_ios_recommendations():
    """Demo the iOS recommendation system."""
    
    # Sample Photo & Video app data (from our collection above)
    sample_apps = [
        {
            'name': 'CapCut - Video Editor',
            'app_id': '1500855883',
            'category': 'Photo & Video',
            'price': 0.0,
            'rating_avg': 4.8,
            'rating_count': 16400,
            'desc_len': 3127,
            'total': 2.35,
            'clone_difficulty': 'MODERATE',
            'revenue_potential': 'GOOD_REVENUE',
            'bundle_id': 'com.lemon.lvoverseas'
        },
        {
            'name': 'Canva: AI Photo & Video Editor',
            'app_id': '1457136161', 
            'category': 'Photo & Video',
            'price': 0.0,
            'rating_avg': 4.8,
            'rating_count': 13300,
            'desc_len': 2636,
            'total': 2.23,
            'clone_difficulty': 'EASY_CLONE',
            'revenue_potential': 'GOOD_REVENUE',
            'bundle_id': 'com.canva.canvaeditor'
        }
    ]
    
    print("📱 iOS-OPTIMIZED AI RECOMMENDATIONS DEMO")
    print("=" * 60)
    
    recommender = IOSOptimizedAIRecommender(os.getenv("HUGGING_FACE_API_KEY"))
    
    for i, app_data in enumerate(sample_apps, 1):
        print(f"\n{i}. {app_data['name']}")
        print("-" * 50)
        
        try:
            # Generate iOS recommendation
            rec = recommender.generate_ios_recommendation(app_data)
            
            # Display in iOS-style format
            print(f"📱 {rec.emoji} {rec.title}")
            print(f"💡 {rec.subtitle}")
            print(f"📊 Clone Score: {rec.clone_score:.2f}/5.0")
            print(f"🎯 Priority: {rec.build_estimate['priority']}")
            
            print(f"\n🚀 KEY FEATURES:")
            for feature in rec.key_features:
                print(f"   {feature['icon']} {feature['title']}: {feature['desc']}")
            
            print(f"\n💰 REVENUE MODEL:")
            print(f"   Type: {rec.revenue_model['type']}")
            print(f"   Primary: {rec.revenue_model['primary']}")
            print(f"   Secondary: {rec.revenue_model['secondary']}")
            
            print(f"\n⏱️ BUILD PLAN:")
            print(f"   Time: {rec.build_estimate['time']}")
            print(f"   Difficulty: {rec.build_estimate['difficulty']}")
            
            print(f"\n📱 iOS FEATURES:")
            for feature in rec.ios_features:
                print(f"   • {feature}")
            
            print(f"\n💡 STRATEGY:")
            print(f"   Gap: {rec.market_gap}")
            print(f"   Edge: {rec.competitive_edge}")
            
            print(f"\n⚠️ RISKS: {', '.join(rec.risks)}")
            print(f"🤖 Confidence: {rec.confidence:.1%}")
            
            # Show JSON structure for iOS app
            print(f"\n📋 JSON FOR iOS APP:")
            json_data = asdict(rec)
            print(json.dumps(json_data, indent=2)[:500] + "...")
            
        except Exception as e:
            print(f"❌ Error generating recommendation: {e}")


if __name__ == "__main__":
    demo_ios_recommendations()