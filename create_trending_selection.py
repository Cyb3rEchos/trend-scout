#!/usr/bin/env python3
"""Create trending app selection from existing data."""

import logging
from datetime import datetime
from trendscout.store import DataStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def select_trending_apps():
    """Select top 10 trending apps per category based on clone potential."""
    
    store = DataStore()
    
    # Get all current data
    results = store.publisher.client.table('scout_results').select('*').execute()
    
    categories = {}
    for record in results.data:
        cat = record['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(record)
    
    trending_selections = []
    
    for category, apps in categories.items():
        logger.info(f"\\n=== {category.upper()} ({len(apps)} apps) ===")
        
        # Sort by clone potential (total score) and other trending factors
        sorted_apps = sorted(apps, key=lambda x: (
            x['total'] or 0,  # Clone score (higher is better for trending)
            -(x['desc_len'] or 1000),  # Simpler apps (shorter descriptions)
            x['rating_avg'] or 0,  # User satisfaction
            -(x['moat_risk'] or 5)  # Lower risk
        ), reverse=True)
        
        # Select top 10 (or all if less than 10)
        selected = sorted_apps[:10]
        
        # Mark top 3-5 as high potential
        for i, app in enumerate(selected):
            potential = "HIGH" if i < 3 else ("MEDIUM" if i < 5 else "LOW")
            
            trending_app = {
                'category': category,
                'rank_in_category': i + 1,
                'potential': potential,
                'app_name': app['name'].split(' on the App')[0].strip() if 'on the App' in app['name'] else app['name'],
                'bundle_id': app['bundle_id'],
                'clone_score': app['total'] or 0,
                'rating': app['rating_avg'] or 0,
                'description_length': app['desc_len'] or 0,
                'price': app['price'] or 0,
                'has_iap': app['has_iap'],
                'generated_at': datetime.now().isoformat(),
                'source_id': app['id']
            }
            
            trending_selections.append(trending_app)
            
            logger.info(f"  #{i+1} [{potential}] {trending_app['app_name']} (Score: {trending_app['clone_score']:.2f}, Rating: {trending_app['rating']:.1f})")
    
    # Store in daily_rankings table
    logger.info(f"\\n=== STORING {len(trending_selections)} TRENDING SELECTIONS ===")
    
    try:
        # Clear existing daily rankings (try different approach)
        try:
            store.publisher.client.table('daily_rankings').delete().neq('category', '').execute()
        except:
            # If that fails, try truncating by deleting all records
            pass
        
        # Insert new selections
        result = store.publisher.client.table('daily_rankings').insert(trending_selections).execute()
        
        if result.data:
            logger.info(f"✅ Successfully stored {len(result.data)} trending app selections")
            
            # Show summary
            high_potential = len([x for x in trending_selections if x['potential'] == 'HIGH'])
            medium_potential = len([x for x in trending_selections if x['potential'] == 'MEDIUM'])
            low_potential = len([x for x in trending_selections if x['potential'] == 'LOW'])
            
            logger.info(f"   HIGH potential: {high_potential} apps")
            logger.info(f"   MEDIUM potential: {medium_potential} apps") 
            logger.info(f"   LOW potential: {low_potential} apps")
            
            return True
        else:
            logger.error("❌ Failed to store trending selections")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error storing selections: {e}")
        return False

if __name__ == "__main__":
    success = select_trending_apps()
    if success:
        print("\\n🎉 Trending app selection completed!")
    else:
        print("\\n❌ Trending app selection failed")