#!/usr/bin/env python3
"""Small test of the automation pipeline."""

import logging
from datetime import date
from trendscout.store import DataStore  
from trendscout.scrape import AppScraper
from trendscout.score import AppScorer
from trendscout.ai_recommender import AIRecommender

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_automation_pipeline():
    """Test the full automation pipeline with 1 category."""
    
    logger.info("🧪 Testing automation pipeline...")
    
    # Initialize services
    store = DataStore()
    scraper = AppScraper()
    scorer = AppScorer()
    ai_recommender = AIRecommender()
    
    # Test data collection for 1 category (Utilities)
    logger.info("📱 Testing data collection...")
    test_params = [
        ("Utilities", "US", "free")
    ]
    
    total_collected = 0
    
    for category, country, chart in test_params:
        logger.info(f"Testing {category} {country} {chart}...")
        
        try:
            # Fetch RSS rankings
            rss_url = f"https://rss.applemarketingtools.com/api/v2/{country.lower()}/apps/top-{chart}/25/{category.lower().replace(' ', '').replace('&', '')}.rss"
            rss_records = scraper.get_app_rankings(rss_url, category, country, chart)
            
            if rss_records:
                logger.info(f"✅ Got {len(rss_records)} rankings for {category}")
                total_collected += len(rss_records)
                
                # Test app page scraping (just first app)
                if rss_records:
                    test_app = rss_records[0]
                    logger.info(f"Testing app page scraping for: {test_app.name}")
                    
                    try:
                        page_data = scraper.scrape_app_page(test_app.app_id, country)
                        if page_data:
                            logger.info(f"✅ Successfully scraped app page data")
                            
                            # Test scoring
                            raw_records = [test_app]
                            app_data_map = {test_app.app_id: page_data}
                            rank_deltas = {}
                            
                            scored_records = scorer.score_apps(raw_records, app_data_map, rank_deltas)
                            if scored_records:
                                logger.info(f"✅ Successfully scored {len(scored_records)} apps")
                                
                                # Test AI recommendation (optional)
                                try:
                                    sample_app = {
                                        'name': scored_records[0].name,
                                        'category': scored_records[0].category,
                                        'bundle_id': scored_records[0].bundle_id,
                                        'rating_avg': scored_records[0].rating_avg,
                                        'total': scored_records[0].total
                                    }
                                    
                                    recommendation = ai_recommender.generate_recommendation(sample_app)
                                    logger.info(f"✅ AI recommendation: {recommendation.improvement_summary[:50]}...")
                                    
                                except Exception as e:
                                    logger.warning(f"AI recommendation failed: {e}")
                                
                            else:
                                logger.error("❌ Scoring failed")
                        else:
                            logger.error("❌ App page scraping failed")
                    except Exception as e:
                        logger.error(f"❌ App page test failed: {e}")
            else:
                logger.error(f"❌ No rankings found for {category}")
                
        except Exception as e:
            logger.error(f"❌ Category test failed: {e}")
    
    logger.info(f"🎯 Test Results:")
    logger.info(f"  Categories tested: {len(test_params)}")
    logger.info(f"  Total apps collected: {total_collected}")
    
    # Test database connection
    logger.info("💾 Testing database connection...")
    try:
        connection_ok = store.publisher.check_connection()
        if connection_ok:
            logger.info("✅ Supabase connection working")
        else:
            logger.error("❌ Supabase connection failed")
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
    
    # Show current database state
    logger.info("📊 Current database state:")
    try:
        results = store.publisher.client.table('scout_results').select('category', count='exact').execute()
        logger.info(f"  scout_results: {results.count} records")
        
        rankings = store.publisher.client.table('daily_rankings').select('*', count='exact').execute()
        logger.info(f"  daily_rankings: {rankings.count} records")
        
    except Exception as e:
        logger.error(f"❌ Database state check failed: {e}")
    
    logger.info("🧪 Test completed!")

if __name__ == "__main__":
    test_automation_pipeline()