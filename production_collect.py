#!/usr/bin/env python3
"""
Production data collection script for Trend Scout.

This script implements best practices for legitimate data collection:
- Conservative rate limiting
- Intelligent caching
- Proper error handling
- Respectful API usage
"""

import argparse
import logging
import random
import time
from datetime import datetime
from pathlib import Path

from trendscout.config import ProductionConfig
from trendscout.models import CollectConfig
from trendscout.rss import RSSFetcher
from trendscout.scrape import AppScraper
from trendscout.score import AppScorer
from trendscout.store import DataStore


def setup_production_logging():
    """Set up production logging."""
    log_dir = Path.home() / "Library" / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "trendscout-production.log"),
            logging.StreamHandler()
        ]
    )


def collect_with_conservative_limits(categories=None, countries=None):
    """Collect data with production-safe rate limits."""
    logger = logging.getLogger(__name__)
    
    # Use conservative defaults
    if categories is None:
        categories = ["Utilities", "Productivity", "Finance"]  # Start with 3 categories
    if countries is None:
        countries = ["US", "CA"]  # Start with 2 countries
    
    config = CollectConfig(
        categories=categories,
        countries=countries,
        charts=["free"],  # Start with free only
        top_n=10  # Smaller number to reduce load
    )
    
    logger.info(f"Starting production collection: {len(categories)} categories, {len(countries)} countries")
    
    # Use different user agents for different parts
    ua_index = random.randint(0, len(ProductionConfig.USER_AGENTS) - 1)
    
    # Initialize with production settings
    fetcher = RSSFetcher(
        user_agent=ProductionConfig.get_user_agent(ua_index),
        rate_limit_delay=ProductionConfig.RSS_RATE_LIMIT_DELAY
    )
    
    scraper = AppScraper(
        user_agent=ProductionConfig.get_user_agent((ua_index + 1) % len(ProductionConfig.USER_AGENTS)),
        rate_limit_delay=ProductionConfig.SCRAPE_RATE_LIMIT_DELAY
    )
    
    scorer = AppScorer()
    store = DataStore()
    
    try:
        # Step 1: Collect RSS data
        logger.info("Phase 1: Collecting RSS data...")
        raw_records = fetcher.collect_all(config)
        
        if not raw_records:
            logger.error("No RSS data collected. Check network and rate limits.")
            return False
        
        logger.info(f"Collected {len(raw_records)} raw records")
        
        # Step 2: Scrape app data (with caching)
        logger.info("Phase 2: Scraping app details...")
        app_data_map = {}
        successful_scrapes = 0
        
        for i, record in enumerate(raw_records):
            logger.info(f"Processing app {i+1}/{len(raw_records)}: {record.name}")
            
            try:
                # Check cache first
                cached_html = store.cache.get_html(
                    record.app_id, 
                    record.country, 
                    max_age_hours=ProductionConfig.HTML_CACHE_HOURS
                )
                
                if cached_html:
                    logger.info(f"Using cached data for {record.app_id}")
                    app_data = scraper.parse_app_page(cached_html, record.app_id)
                else:
                    logger.info(f"Scraping fresh data for {record.app_id}")
                    # Fetch HTML first for caching
                    html = scraper.fetch_app_page(record.app_id, record.country)
                    store.cache.store_html(record.app_id, record.country, html)
                    
                    # Parse the HTML we just fetched
                    app_data = scraper.parse_app_page(html, record.app_id)
                
                app_data_map[record.app_id] = app_data
                successful_scrapes += 1
                
                # Be extra conservative with delays
                time.sleep(ProductionConfig.SCRAPE_RATE_LIMIT_DELAY)
                
            except Exception as e:
                logger.warning(f"Failed to scrape {record.app_id}: {e}")
                continue
        
        logger.info(f"Successfully scraped {successful_scrapes}/{len(raw_records)} apps")
        
        if not app_data_map:
            logger.error("No app data could be scraped")
            return False
        
        # Step 3: Score apps
        logger.info("Phase 3: Computing scores...")
        rank_deltas = store.cache.get_rank_deltas(list(app_data_map.keys()))
        scored_records = scorer.score_apps(raw_records, app_data_map, rank_deltas)
        
        if not scored_records:
            logger.error("No records could be scored")
            return False
        
        # Step 4: Store and publish
        logger.info("Phase 4: Storing and publishing results...")
        success = store.store_and_publish(scored_records)
        
        if success:
            logger.info(f"Successfully processed {len(scored_records)} records")
            return True
        else:
            logger.error("Failed to publish results")
            return False
            
    except Exception as e:
        logger.error(f"Production collection failed: {e}")
        return False


def main():
    """Main entry point for production collection."""
    parser = argparse.ArgumentParser(description="Production Trend Scout data collection")
    parser.add_argument("--categories", nargs="+", help="Categories to collect")
    parser.add_argument("--countries", nargs="+", help="Countries to collect")
    parser.add_argument("--test", action="store_true", help="Test mode with minimal data")
    
    args = parser.parse_args()
    
    setup_production_logging()
    logger = logging.getLogger(__name__)
    
    if args.test:
        logger.info("Running in test mode")
        categories = ["Utilities"]
        countries = ["US"]
    else:
        categories = args.categories
        countries = args.countries
    
    logger.info("Starting Trend Scout production collection")
    logger.info(f"Configuration: RSS delay={ProductionConfig.RSS_RATE_LIMIT_DELAY}s, "
                f"Scrape delay={ProductionConfig.SCRAPE_RATE_LIMIT_DELAY}s")
    
    success = collect_with_conservative_limits(categories, countries)
    
    if success:
        logger.info("Production collection completed successfully")
        exit(0)
    else:
        logger.error("Production collection failed")
        exit(1)


if __name__ == "__main__":
    main()