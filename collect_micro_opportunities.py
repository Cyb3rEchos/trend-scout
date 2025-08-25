#!/usr/bin/env python3
"""
Micro-Opportunities Collection Script

Focused data collection for finding clone-worthy apps across categories
that are most likely to contain simple, revenue-generating utilities
that can be built quickly with Claude.
"""

import argparse
import logging
import time
from datetime import datetime
from pathlib import Path

from trendscout.config import ProductionConfig
from trendscout.models import CollectConfig
from trendscout.rss import RSSFetcher
from trendscout.scrape import AppScraper
from trendscout.score import AppScorer
from trendscout.store import DataStore


def setup_logging():
    """Set up logging for micro-opportunities collection."""
    log_dir = Path.home() / "Library" / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "trendscout-micro-opportunities.log"),
            logging.StreamHandler()
        ]
    )


def get_micro_opportunity_categories():
    """
    Get categories most likely to contain clone-worthy apps.
    
    Focus on categories with:
    - Simple utility apps  
    - Tools and productivity apps
    - Apps that can be built quickly
    - Categories with good revenue potential but not dominated by big tech
    """
    return [
        "Utilities",           # Cleaners, battery tools, calculators, flashlights
        "Productivity",        # Note apps, task managers, simple tools
        "Photo & Video",       # Filters, simple editors, converters  
        "Lifestyle",           # Simple trackers, utilities
        "Health & Fitness",    # Step counters, water reminders, simple trackers
        "Finance",             # Budget trackers, tip calculators
        "Music",               # Simple players, converters, utilities
        "Education"            # Quiz apps, flashcards, simple learning tools
    ]


def collect_micro_opportunities(test_mode=False, max_apps_per_category=15):
    """
    Collect data specifically targeted at finding micro-opportunities.
    
    Args:
        test_mode: If True, runs with limited scope for testing
        max_apps_per_category: Maximum apps to collect per category
    """
    logger = logging.getLogger(__name__)
    
    if test_mode:
        logger.info("🧪 Running in TEST MODE")
        categories = ["Utilities", "Productivity"]  # Just 2 categories for testing
        countries = ["US"]
        max_apps = 10
    else:
        logger.info("🎯 Running FULL MICRO-OPPORTUNITIES collection")
        categories = get_micro_opportunity_categories()
        countries = ["US", "CA", "GB"]  # Expand to English-speaking markets
        max_apps = max_apps_per_category
    
    logger.info(f"Target categories: {', '.join(categories)}")
    logger.info(f"Target countries: {', '.join(countries)}")
    logger.info(f"Max apps per category: {max_apps}")
    
    config = CollectConfig(
        categories=categories,
        countries=countries,
        charts=["free", "paid"],  # Include paid apps for better monetization scores
        top_n=max_apps
    )
    
    # Initialize components
    fetcher = RSSFetcher(rate_limit_delay=ProductionConfig.RSS_RATE_LIMIT_DELAY)
    scraper = AppScraper(rate_limit_delay=ProductionConfig.SCRAPE_RATE_LIMIT_DELAY)
    scorer = AppScorer()
    store = DataStore()
    
    start_time = datetime.now()
    
    try:
        # Phase 1: Collect RSS data
        logger.info("Phase 1: 📥 Collecting RSS data across multiple categories...")
        raw_records = fetcher.collect_all(config)
        logger.info(f"Collected {len(raw_records)} raw app records")
        
        if not raw_records:
            logger.error("No RSS data collected")
            return False
        
        # Phase 2: Scrape app details (with intelligent caching)
        logger.info("Phase 2: 🕷️  Scraping app details...")
        app_data_map = {}
        successful_scrapes = 0
        
        for i, record in enumerate(raw_records, 1):
            logger.info(f"Processing app {i}/{len(raw_records)}: {record.name} - {record.category}")
            
            try:
                # Check cache first
                cached_html = store.cache.get_html(
                    record.app_id, 
                    record.country, 
                    max_age_hours=ProductionConfig.HTML_CACHE_HOURS
                )
                
                if cached_html:
                    logger.debug(f"Using cached data for {record.app_id}")
                    app_data = scraper.parse_app_page(cached_html, record.app_id)
                else:
                    logger.debug(f"Scraping fresh data for {record.app_id}")
                    html = scraper.fetch_app_page(record.app_id, record.country)
                    store.cache.store_html(record.app_id, record.country, html)
                    app_data = scraper.parse_app_page(html, record.app_id)
                
                app_data_map[record.app_id] = app_data
                successful_scrapes += 1
                
                # Conservative rate limiting for production
                time.sleep(ProductionConfig.SCRAPE_RATE_LIMIT_DELAY)
                
            except Exception as e:
                logger.warning(f"Failed to scrape {record.app_id} ({record.name}): {e}")
                continue
        
        logger.info(f"Successfully scraped {successful_scrapes}/{len(raw_records)} apps")
        
        if not app_data_map:
            logger.error("No app data could be scraped")
            return False
        
        # Phase 3: Compute scores
        logger.info("Phase 3: 📊 Computing competitive intelligence scores...")
        rank_deltas = store.cache.get_rank_deltas(list(app_data_map.keys()))
        scored_records = scorer.score_apps(raw_records, app_data_map, rank_deltas)
        
        if not scored_records:
            logger.error("No records could be scored")
            return False
        
        # Phase 4: Store and publish
        logger.info("Phase 4: 💾 Storing and publishing results...")
        success = store.store_and_publish(scored_records)
        
        if not success:
            logger.error("Failed to store and publish results")
            return False
        
        # Phase 5: Analyze micro-opportunities 
        logger.info("Phase 5: 🎯 Analyzing micro-opportunities...")
        analyze_micro_opportunities(store, scored_records)
        
        elapsed = datetime.now() - start_time
        logger.info(f"✅ Collection completed successfully in {elapsed}")
        logger.info(f"📈 Processed {len(scored_records)} apps across {len(categories)} categories")
        
        return True
        
    except Exception as e:
        logger.error(f"Collection failed: {e}")
        return False


def analyze_micro_opportunities(store, scored_records):
    """Analyze and report on micro-opportunities found."""
    logger = logging.getLogger(__name__)
    
    # Group by categories to see distribution
    category_stats = {}
    clone_candidates = []
    
    for record in scored_records:
        cat = record.category
        if cat not in category_stats:
            category_stats[cat] = {'count': 0, 'avg_score': 0, 'max_score': 0}
        
        category_stats[cat]['count'] += 1
        category_stats[cat]['avg_score'] += record.total
        category_stats[cat]['max_score'] = max(category_stats[cat]['max_score'], record.total)
        
        # Identify potential clone candidates
        is_simple = record.low_complexity >= 2.0
        is_safe = record.moat_risk <= 2.5
        has_potential = record.total >= 1.8
        
        if is_simple and is_safe and has_potential:
            clone_candidates.append(record)
    
    # Calculate averages
    for cat in category_stats:
        if category_stats[cat]['count'] > 0:
            category_stats[cat]['avg_score'] /= category_stats[cat]['count']
    
    # Report findings
    logger.info("📊 CATEGORY ANALYSIS:")
    for cat, stats in sorted(category_stats.items(), key=lambda x: x[1]['avg_score'], reverse=True):
        logger.info(f"  {cat}: {stats['count']} apps, avg score {stats['avg_score']:.2f}, max {stats['max_score']:.2f}")
    
    logger.info(f"\n🎯 CLONE CANDIDATES FOUND: {len(clone_candidates)}")
    for candidate in sorted(clone_candidates, key=lambda x: x.total, reverse=True)[:5]:
        logger.info(f"  • {candidate.name[:50]} - Score: {candidate.total:.2f} "
                   f"(C:{candidate.low_complexity:.1f} R:{candidate.moat_risk:.1f})")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Collect micro-opportunities for app cloning")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    parser.add_argument("--max-apps", type=int, default=15, help="Max apps per category")
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🎯 MICRO-OPPORTUNITIES COLLECTION STARTING")
    logger.info("Target: Find simple, clone-worthy apps with revenue potential")
    
    success = collect_micro_opportunities(
        test_mode=args.test,
        max_apps_per_category=args.max_apps
    )
    
    if success:
        logger.info("✅ Micro-opportunities collection completed successfully")
    else:
        logger.error("❌ Micro-opportunities collection failed")
        exit(1)


if __name__ == "__main__":
    main()