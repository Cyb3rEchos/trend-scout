#!/usr/bin/env python3
"""Generate AI recommendations for trending high-potential apps."""

import logging
from datetime import datetime
from trendscout.store import DataStore
from trendscout.ai_recommender import AIRecommender

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_trending_high_potential_apps():
    """Get the top 3-5 high potential apps per category."""
    
    store = DataStore()
    results = store.publisher.client.table('scout_results').select('*').execute()
    
    categories = {}
    for record in results.data:
        cat = record['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(record)
    
    high_potential_apps = []
    
    for category, apps in categories.items():
        # Sort by clone potential 
        sorted_apps = sorted(apps, key=lambda x: (
            x['total'] or 0,  # Clone score
            -(x['desc_len'] or 1000),  # Simpler apps
            x['rating_avg'] or 0,  # User satisfaction
            -(x['moat_risk'] or 5)  # Lower risk
        ), reverse=True)
        
        # Take top 3-5 high potential apps per category
        high_potential = sorted_apps[:5]
        
        for i, app in enumerate(high_potential):
            app['category_rank'] = i + 1
            app['potential_level'] = 'HIGH' if i < 3 else 'MEDIUM'
            high_potential_apps.append(app)
    
    return high_potential_apps

def generate_ai_recommendations():
    """Generate AI recommendations for high-potential apps."""
    
    logger.info("🤖 Generating AI recommendations for trending apps...")
    
    # Get high potential apps
    apps = get_trending_high_potential_apps()
    logger.info(f"Found {len(apps)} high-potential apps across all categories")
    
    # Initialize AI recommender
    ai_recommender = AIRecommender()
    
    recommendations = []
    processed = 0
    
    for app in apps:
        logger.info(f"\\nProcessing {app['category']} #{app['category_rank']}: {app['name'].split(' on the App')[0].strip()[:50]}")
        
        try:
            # Clean app name
            app_name = app['name'].split(' on the App')[0].strip()
            app_name = app_name.replace('â\x80\x8e', '').replace('â¢', '').strip()
            
            # Prepare app data for AI
            app_data = {
                'name': app_name,
                'category': app['category'],
                'bundle_id': app['bundle_id'],
                'rating_avg': app['rating_avg'] or 0,
                'rating_count': app['rating_count'] or 0,
                'total': app['total'] or 0,
                'price': app['price'] or 0,
                'has_iap': app['has_iap'],
                'desc_len': app['desc_len'] or 0,
                'potential_level': app['potential_level']
            }
            
            # Generate AI recommendation
            recommendation = ai_recommender.generate_recommendation(app_data)
            
            # Create enhanced recommendation record
            enhanced_rec = {
                'app_name': app_name,
                'category': app['category'],
                'category_rank': app['category_rank'],
                'potential_level': app['potential_level'],
                'clone_score': app['total'] or 0,
                'bundle_id': app['bundle_id'],
                
                # AI-generated content
                'improvement_summary': recommendation.improvement_summary,
                'build_estimate': recommendation.build_estimate,
                'market_gap': recommendation.market_gap,
                'key_features': recommendation.key_features,
                'monetization_tips': recommendation.monetization_tips,
                'risk_factors': recommendation.risk_factors,
                
                'generated_at': datetime.now().isoformat(),
                'source_app_id': app['id']
            }
            
            recommendations.append(enhanced_rec)
            processed += 1
            
            logger.info(f"  ✅ Generated recommendation ({len(recommendation.improvement_summary)} chars)")
            logger.info(f"  💡 Key insight: {recommendation.improvement_summary[:100]}...")
            logger.info(f"  ⏰ Build time: {recommendation.build_estimate}")
            
        except Exception as e:
            logger.error(f"  ❌ Failed to generate recommendation: {e}")
            continue
    
    logger.info(f"\\n🎯 Generated {len(recommendations)} AI recommendations ({processed}/{len(apps)} apps)")
    
    # Save recommendations to a JSON file for now (since daily_rankings has issues)
    import json
    output_file = 'ai_recommendations.json'
    
    try:
        with open(output_file, 'w') as f:
            json.dump(recommendations, f, indent=2)
        
        logger.info(f"💾 Saved recommendations to {output_file}")
        
        # Show summary by category
        categories = {}
        for rec in recommendations:
            cat = rec['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(rec)
        
        logger.info(f"\\n📊 RECOMMENDATIONS BY CATEGORY:")
        for category, recs in sorted(categories.items()):
            high_count = len([r for r in recs if r['potential_level'] == 'HIGH'])
            medium_count = len([r for r in recs if r['potential_level'] == 'MEDIUM'])
            logger.info(f"  {category}: {len(recs)} total ({high_count} HIGH, {medium_count} MEDIUM)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to save recommendations: {e}")
        return False

if __name__ == "__main__":
    success = generate_ai_recommendations()
    if success:
        print("\\n🎉 AI recommendations generated successfully!")
        print("📋 Check ai_recommendations.json for detailed output")
    else:
        print("\\n❌ AI recommendation generation failed")