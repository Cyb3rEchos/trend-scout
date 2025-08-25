#!/usr/bin/env python3
"""Recover the deleted 600 records from SQLite cache."""

import logging
import sqlite3
from datetime import datetime
from trendscout.store import DataStore
from trendscout.scrape import AppScraper
from trendscout.score import AppScorer
from trendscout.models import RawAppRecord, AppPageData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recover_data():
    """Recover deleted data from SQLite cache."""
    
    logger.info("🔄 Starting data recovery from SQLite cache...")
    
    # Initialize services
    store = DataStore()
    scraper = AppScraper()
    scorer = AppScorer()
    
    # Get cached rank data
    cache_db_path = "/Users/billyjo182/.trendscout/cache.db"
    
    with sqlite3.connect(cache_db_path) as conn:
        conn.row_factory = sqlite3.Row
        
        # Get all cached ranks from both dates
        cursor = conn.execute("""
            SELECT app_id, category, country, chart, rank, date 
            FROM app_ranks 
            WHERE date IN ('2025-08-19', '2025-08-20')
            ORDER BY category, rank
        """)
        
        cached_ranks = cursor.fetchall()
        logger.info(f"Found {len(cached_ranks)} cached rank records")
        
        # Get cached HTML for each app
        raw_records = []
        app_data_map = {}
        
        for rank_record in cached_ranks:
            app_id = rank_record['app_id']
            category = rank_record['category']
            country = rank_record['country']
            chart = rank_record['chart']
            rank = rank_record['rank']
            
            # Get cached HTML
            html_cursor = conn.execute("""
                SELECT html FROM app_html_cache 
                WHERE app_id = ? AND country = ?
            """, (app_id, country))
            
            html_row = html_cursor.fetchone()
            if html_row:
                html = html_row['html']
                
                try:
                    # Parse the cached HTML
                    app_data = scraper.parse_app_page(html, app_id)
                    if app_data:
                        # Create raw record with required fields
                        # Extract app name from HTML title or use app_id
                        app_name = f'App {app_id}'  # Default fallback
                        if 'name' in html.lower():
                            # Try to extract name from HTML
                            from bs4 import BeautifulSoup
                            soup = BeautifulSoup(html, 'html.parser')
                            title_tag = soup.find('title')
                            if title_tag:
                                app_name = title_tag.text.split(' on the App Store')[0].strip()
                        
                        raw_record = RawAppRecord(
                            app_id=app_id,
                            category=category,
                            country=country,
                            chart=chart,
                            rank=rank,
                            name=app_name,
                            rss_url='https://rss.applemarketingtools.com/api/v2/us/apps/top-free/25/apps.rss',
                            fetched_at=datetime.now(),
                            raw_data={'app_data': app_data.__dict__ if hasattr(app_data, '__dict__') else str(app_data)}
                        )
                        
                        raw_records.append(raw_record)
                        app_data_map[app_id] = app_data
                        
                        if len(raw_records) % 50 == 0:
                            logger.info(f"Processed {len(raw_records)} cached records...")
                            
                except Exception as e:
                    logger.warning(f"Failed to parse cached data for {app_id}: {e}")
                    continue
            else:
                logger.warning(f"No cached HTML found for {app_id}")
    
    logger.info(f"Successfully processed {len(raw_records)} records from cache")
    
    # Score the recovered records
    logger.info("📊 Scoring recovered records...")
    rank_deltas = store.cache.get_rank_deltas(list(app_data_map.keys()))
    scored_records = scorer.score_apps(raw_records, app_data_map, rank_deltas)
    
    # Store in Supabase
    logger.info("💾 Storing recovered data in Supabase...")
    success = store.store_and_publish(scored_records)
    
    if success:
        logger.info(f"✅ Successfully recovered {len(scored_records)} records!")
        
        # Show distribution
        category_counts = {}
        for record in scored_records:
            cat = record.category
            if cat not in category_counts:
                category_counts[cat] = 0
            category_counts[cat] += 1
        
        logger.info("📊 Recovered data distribution:")
        for category, count in sorted(category_counts.items()):
            logger.info(f"  {category}: {count} records")
            
        return True
    else:
        logger.error("❌ Failed to store recovered data")
        return False

if __name__ == "__main__":
    success = recover_data()
    if success:
        print("🎉 Data recovery completed successfully!")
    else:
        print("❌ Data recovery failed")