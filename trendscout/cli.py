"""Command-line interface for Trend Scout."""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from .models import CollectConfig, RawAppRecord, ScoredAppRecord
from .rss import RSSFetcher
from .scrape import AppScraper
from .score import AppScorer
from .store import DataStore

# Configure logging
def setup_logging(log_level: str = "INFO") -> None:
    """Set up logging configuration."""
    log_dir = Path.home() / "Library" / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "trendscout.log"
    
    # Configure rotating file handler
    from logging.handlers import RotatingFileHandler
    
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    
    console_handler = logging.StreamHandler()
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Suppress noisy loggers
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def collect_command(args: argparse.Namespace) -> None:
    """Execute collect command."""
    logger = logging.getLogger(__name__)
    
    try:
        # Parse configuration
        if args.cats:
            categories = [cat.strip() for cat in args.cats.split(",")]
        else:
            categories = CollectConfig.default().categories
        
        countries = [c.strip() for c in args.countries.split(",")]
        charts = [c.strip() for c in args.charts.split(",")]
        
        config = CollectConfig(
            categories=categories,
            countries=countries,
            charts=charts,
            top_n=args.top
        )
        
        logger.info(f"Starting collection with config: {config}")
        
        # Collect data
        fetcher = RSSFetcher()
        records = fetcher.collect_all(config)
        
        if not records:
            logger.error("No records collected")
            sys.exit(1)
        
        # Save to file
        output_data = [record.model_dump(mode="json") for record in records]
        
        with open(args.out, "w") as f:
            json.dump(output_data, f, indent=2, default=str)
        
        logger.info(f"Collected {len(records)} records and saved to {args.out}")
        
    except Exception as e:
        logger.error(f"Collection failed: {e}")
        sys.exit(1)


def score_command(args: argparse.Namespace) -> None:
    """Execute score command."""
    logger = logging.getLogger(__name__)
    
    try:
        # Load raw data
        with open(args.input) as f:
            raw_data = json.load(f)
        
        raw_records = [RawAppRecord.model_validate(data) for data in raw_data]
        logger.info(f"Loaded {len(raw_records)} raw records")
        
        # Initialize components
        scraper = AppScraper()
        scorer = AppScorer()
        store = DataStore()
        
        # Scrape app data with caching
        app_data_map = {}
        scrape_errors = []
        
        for i, record in enumerate(raw_records):
            logger.info(f"Scraping app {i+1}/{len(raw_records)}: {record.app_id}")
            
            try:
                # Check cache first
                cached_html = store.cache.get_html(record.app_id, record.country)
                
                if cached_html:
                    logger.debug(f"Using cached HTML for {record.app_id}")
                    app_data = scraper.parse_app_page(cached_html, record.app_id)
                else:
                    # Scrape fresh data
                    app_data = scraper.scrape_app(record.app_id, record.country)
                    
                    # Cache the HTML for future use
                    html = scraper.fetch_app_page(record.app_id, record.country)
                    store.cache.store_html(record.app_id, record.country, html)
                
                app_data_map[record.app_id] = app_data
                
            except Exception as e:
                logger.error(f"Failed to scrape app {record.app_id}: {e}")
                scrape_errors.append(f"{record.app_id}: {e}")
                continue
        
        if scrape_errors:
            logger.warning(f"Scraping failed for {len(scrape_errors)} apps")
        
        if not app_data_map:
            logger.error("No app data could be scraped")
            sys.exit(1)
        
        # Get rank deltas from cache
        app_ids = list(app_data_map.keys())
        rank_deltas = store.cache.get_rank_deltas(app_ids)
        
        # Score apps
        logger.info("Computing scores...")
        scored_records = scorer.score_apps(raw_records, app_data_map, rank_deltas)
        
        if not scored_records:
            logger.error("No records could be scored")
            sys.exit(1)
        
        # Save scored data
        output_data = [record.model_dump(mode="json") for record in scored_records]
        
        with open(args.out, "w") as f:
            json.dump(output_data, f, indent=2, default=str)
        
        logger.info(f"Scored {len(scored_records)} records and saved to {args.out}")
        
        # Print summary
        if scrape_errors:
            print(f"\nScraping errors ({len(scrape_errors)}):")
            for error in scrape_errors[:10]:  # Show first 10
                print(f"  {error}")
            if len(scrape_errors) > 10:
                print(f"  ... and {len(scrape_errors) - 10} more")
        
    except Exception as e:
        logger.error(f"Scoring failed: {e}")
        sys.exit(1)


def publish_command(args: argparse.Namespace) -> None:
    """Execute publish command."""
    logger = logging.getLogger(__name__)
    
    try:
        # Load scored data
        with open(args.input) as f:
            scored_data = json.load(f)
        
        scored_records = [ScoredAppRecord.model_validate(data) for data in scored_data]
        logger.info(f"Loaded {len(scored_records)} scored records")
        
        # Initialize store and publish
        store = DataStore()
        success = store.store_and_publish(scored_records)
        
        if success:
            logger.info("Successfully published results to Supabase")
        else:
            logger.error("Failed to publish results")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Publishing failed: {e}")
        sys.exit(1)


def backfill_command(args: argparse.Namespace) -> None:
    """Execute backfill command."""
    logger = logging.getLogger(__name__)
    
    try:
        # Parse date range
        start_date, end_date = args.date_range.split("..")
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        logger.info(f"Backfilling data from {start_date} to {end_date}")
        
        # For now, just run a single collection
        # In a full implementation, this would iterate through dates
        logger.warning("Backfill not fully implemented - running single collection")
        
        # Create a temporary args object for collect command
        collect_args = argparse.Namespace(
            cats=None,  # Use defaults
            countries="US,CA,GB,AU,DE",
            charts="free,paid",
            top=25,
            out=f"backfill_{start_date}_{end_date}.json"
        )
        
        collect_command(collect_args)
        
    except Exception as e:
        logger.error(f"Backfill failed: {e}")
        sys.exit(1)


def doctor_command(args: argparse.Namespace) -> None:
    """Execute doctor command to check system health."""
    logger = logging.getLogger(__name__)
    
    print("🩺 Trend Scout Health Check")
    print("=" * 40)
    
    issues = []
    
    # Check environment variables
    import os
    print("📋 Environment Variables:")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if supabase_url:
        print(f"  ✅ SUPABASE_URL: {supabase_url[:50]}...")
    else:
        print("  ❌ SUPABASE_URL: Not set")
        issues.append("SUPABASE_URL environment variable not set")
    
    if supabase_key:
        print(f"  ✅ SUPABASE_SERVICE_KEY: {supabase_key[:20]}...")
    else:
        print("  ❌ SUPABASE_SERVICE_KEY: Not set")
        issues.append("SUPABASE_SERVICE_KEY environment variable not set")
    
    # Check RSS reachability
    print("\n🌐 RSS Endpoints:")
    try:
        fetcher = RSSFetcher()
        test_url = fetcher.build_rss_url("Utilities", "US", "free", 5)
        fetcher.fetch_rss_data(test_url)
        print("  ✅ Apple RSS API: Reachable")
    except Exception as e:
        print(f"  ❌ Apple RSS API: {e}")
        issues.append(f"RSS endpoint unreachable: {e}")
    
    # Check Supabase connectivity
    print("\n💾 Database:")
    try:
        if supabase_url and supabase_key:
            store = DataStore()
            health = store.check_health()
            
            if health.get("cache"):
                print("  ✅ SQLite Cache: Working")
            else:
                print("  ❌ SQLite Cache: Failed")
                issues.append("SQLite cache not working")
            
            if health.get("supabase"):
                print("  ✅ Supabase: Connected")
            else:
                print("  ❌ Supabase: Connection failed")
                issues.append("Supabase connection failed")
        else:
            print("  ⚠️  Supabase: Cannot test (missing credentials)")
            
    except Exception as e:
        print(f"  ❌ Database check failed: {e}")
        issues.append(f"Database check failed: {e}")
    
    # Check file permissions
    print("\n📁 File System:")
    try:
        log_dir = Path.home() / "Library" / "Logs"
        cache_dir = Path.home() / ".trendscout"
        
        log_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Test write permissions
        test_file = log_dir / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
        
        print(f"  ✅ Log directory: {log_dir}")
        print(f"  ✅ Cache directory: {cache_dir}")
        
    except Exception as e:
        print(f"  ❌ File system: {e}")
        issues.append(f"File system issue: {e}")
    
    # Summary
    print("\n📊 Summary:")
    if not issues:
        print("  🎉 All checks passed! System is healthy.")
    else:
        print(f"  ⚠️  Found {len(issues)} issue(s):")
        for issue in issues:
            print(f"    • {issue}")
        
        print("\n💡 Suggestions:")
        if any("SUPABASE" in issue for issue in issues):
            print("    • Create a .env file with SUPABASE_URL and SUPABASE_SERVICE_KEY")
        if any("RSS" in issue for issue in issues):
            print("    • Check internet connection and firewall settings")
        if any("Supabase connection" in issue for issue in issues):
            print("    • Verify Supabase credentials and database setup")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="ts",
        description="Trend Scout - App Store trend analysis and scoring"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Collect command
    collect_parser = subparsers.add_parser("collect", help="Collect app data from RSS feeds")
    collect_parser.add_argument(
        "--cats", 
        help="Comma-separated categories (default: all configured)"
    )
    collect_parser.add_argument(
        "--countries", 
        default="US,CA,GB,AU,DE",
        help="Comma-separated countries"
    )
    collect_parser.add_argument(
        "--charts", 
        default="free,paid",
        help="Comma-separated chart types"
    )
    collect_parser.add_argument(
        "--top", 
        type=int, 
        default=25,
        help="Number of top apps per chart"
    )
    collect_parser.add_argument(
        "--out", 
        required=True,
        help="Output JSON file"
    )
    
    # Score command
    score_parser = subparsers.add_parser("score", help="Score raw app data")
    score_parser.add_argument("input", help="Input JSON file with raw data")
    score_parser.add_argument("--out", required=True, help="Output JSON file")
    
    # Publish command
    publish_parser = subparsers.add_parser("publish", help="Publish scored data to Supabase")
    publish_parser.add_argument("input", help="Input JSON file with scored data")
    
    # Backfill command
    backfill_parser = subparsers.add_parser("backfill", help="Backfill historical data")
    backfill_parser.add_argument(
        "date_range", 
        help="Date range in format YYYY-MM-DD..YYYY-MM-DD"
    )
    
    # Doctor command
    doctor_parser = subparsers.add_parser("doctor", help="Check system health")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Set up logging
    setup_logging(args.log_level)
    
    # Execute command
    if args.command == "collect":
        collect_command(args)
    elif args.command == "score":
        score_command(args)
    elif args.command == "publish":
        publish_command(args)
    elif args.command == "backfill":
        backfill_command(args)
    elif args.command == "doctor":
        doctor_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()