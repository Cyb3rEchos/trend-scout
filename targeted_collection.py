#!/usr/bin/env python3
"""Targeted data collection to fill missing gaps in database."""

import logging
from datetime import date
from trendscout.store import DataStore
from trendscout.rss import RSSFetcher
from trendscout.models import CollectConfig
from trendscout.scrape import AppScraper
from trendscout.score import AppScorer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_current_data():
    """Analyze what data we currently have."""
    
    store = DataStore()
    results = store.publisher.client.table('scout_results').select('category, country, chart').execute()
    
    # Build current data matrix
    current_data = {}
    for record in results.data:
        category = record['category']
        country = record['country']
        chart = record['chart']
        
        if category not in current_data:
            current_data[category] = {}
        if country not in current_data[category]:
            current_data[category][country] = {}
        if chart not in current_data[category][country]:
            current_data[category][country][chart] = 0
        
        current_data[category][country][chart] += 1
    
    return current_data

def get_missing_combinations():
    """Get list of missing/incomplete combinations."""
    
    categories = ['Utilities', 'Productivity', 'Photo & Video', 'Health & Fitness', 
                  'Lifestyle', 'Finance', 'Music', 'Education', 'Graphics & Design', 'Entertainment']
    countries = ['US', 'CA', 'GB']
    charts = ['free', 'paid']
    
    current_data = analyze_current_data()
    missing = []
    
    for category in categories:
        for country in countries:
            for chart in charts:
                current_count = current_data.get(category, {}).get(country, {}).get(chart, 0)
                if current_count < 25:  # We want 25 per combination
                    missing.append({
                        'category': category,
                        'country': country, 
                        'chart': chart,
                        'current': current_count,
                        'needed': 25 - current_count
                    })
    
    return missing

def test_rss_collection():
    """Test RSS collection to see how many records we actually get."""
    
    logger.info("🧪 Testing RSS collection...")
    
    fetcher = RSSFetcher()
    
    # Test one combination to see what we get
    test_config = CollectConfig(
        categories=["Utilities"],
        countries=["US"], 
        charts=["free"],
        top_n=25  # Request 25
    )
    
    try:
        records = fetcher.collect_all(test_config)
        logger.info(f"✅ RSS test: Got {len(records)} records (expected 25)")
        
        if records:
            sample = records[0]
            logger.info(f"Sample record: {sample.name} - Rank {sample.rank}")
            
        return len(records)
        
    except Exception as e:
        logger.error(f"❌ RSS test failed: {e}")
        return 0

def collect_targeted_data(max_combinations=5):
    """Collect data for missing combinations only."""
    
    logger.info(f"🎯 Starting targeted data collection (max {max_combinations} combinations)...")
    
    # Get missing combinations 
    missing = get_missing_combinations()
    logger.info(f"Found {len(missing)} missing/incomplete combinations")
    
    # Focus on highest priority first
    priority_missing = []
    
    # Priority 1: Completely missing Utilities
    utilities_missing = [m for m in missing if m['category'] == 'Utilities']
    priority_missing.extend(utilities_missing[:max_combinations])
    
    # If we have space, add some incomplete ones
    if len(priority_missing) < max_combinations:
        incomplete = [m for m in missing if m['current'] > 0 and m['current'] < 25]
        remaining_space = max_combinations - len(priority_missing)
        priority_missing.extend(incomplete[:remaining_space])
    
    logger.info(f"Targeting {len(priority_missing)} combinations:")
    for combo in priority_missing:
        logger.info(f"  {combo['category']} {combo['country']} {combo['chart']} (need {combo['needed']})")
    
    # Initialize services
    fetcher = RSSFetcher()
    scraper = AppScraper()
    scorer = AppScorer()
    store = DataStore()
    
    total_collected = 0
    
    for combo in priority_missing:
        logger.info(f"📱 Collecting {combo['category']} {combo['country']} {combo['chart']}...")
        
        try:
            # Create config for this specific combination
            config = CollectConfig(
                categories=[combo['category']],
                countries=[combo['country']],
                charts=[combo['chart']], 
                top_n=25  # Always try for 25
            )
            
            # Collect RSS data
            raw_records = fetcher.collect_all(config)
            logger.info(f"  RSS: Got {len(raw_records)} records")
            
            if not raw_records:
                logger.warning(f"  ❌ No RSS data for {combo['category']} {combo['country']} {combo['chart']}")
                continue
            
            # Scrape app details for first few apps to test
            app_data_map = {}
            scraped_count = 0
            max_scrapes = min(3, len(raw_records))  # Test with first 3 apps
            
            for record in raw_records[:max_scrapes]:
                try:
                    app_data = scraper.scrape_app(record.app_id, combo['country'])
                    if app_data:
                        app_data_map[record.app_id] = app_data
                        scraped_count += 1
                except Exception as e:
                    logger.warning(f"  Scraping failed for {record.app_id}: {e}")
            
            logger.info(f"  Scraped: {scraped_count}/{max_scrapes} apps")
            
            if app_data_map:
                # Score the apps we successfully scraped
                rank_deltas = store.cache.get_rank_deltas(list(app_data_map.keys()))
                scored_records = scorer.score_apps(raw_records[:max_scrapes], app_data_map, rank_deltas)
                
                if scored_records:
                    logger.info(f"  Scored: {len(scored_records)} apps")
                    total_collected += len(scored_records)
                    
                    # Store results
                    success = store.store_and_publish(scored_records)
                    if success:
                        logger.info(f"  ✅ Stored {len(scored_records)} records")
                    else:
                        logger.warning(f"  ❌ Failed to store records")
                else:
                    logger.warning(f"  ❌ Scoring failed")
            else:
                logger.warning(f"  ❌ No app data scraped")
                
        except Exception as e:
            logger.error(f"  ❌ Collection failed: {e}")
    
    logger.info(f"🎯 Targeted collection complete: {total_collected} new records")
    return total_collected

if __name__ == "__main__":
    # First test RSS to understand the issue
    rss_count = test_rss_collection()
    
    if rss_count > 0:
        # Run targeted collection
        collected = collect_targeted_data(max_combinations=3)  # Start small
        logger.info(f"✅ Total new records collected: {collected}")
    else:
        logger.error("❌ RSS collection test failed - fix this first")