"""Data storage and caching for Trend Scout."""

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from supabase import create_client, Client
from dotenv import load_dotenv
import os

from .models import RawAppRecord, ScoredAppRecord, ScoutResultRow

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class SQLiteCache:
    """Local SQLite cache for ranks and HTML data."""
    
    def __init__(self, db_path: str = "~/.trendscout/cache.db"):
        """Initialize SQLite cache.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS app_ranks (
                    app_id TEXT,
                    category TEXT,
                    country TEXT,
                    chart TEXT,
                    rank INTEGER,
                    date TEXT,
                    PRIMARY KEY (app_id, category, country, chart, date)
                );
                
                CREATE TABLE IF NOT EXISTS app_html_cache (
                    app_id TEXT,
                    country TEXT,
                    html TEXT,
                    cached_at TEXT,
                    PRIMARY KEY (app_id, country)
                );
                
                CREATE INDEX IF NOT EXISTS idx_ranks_date 
                ON app_ranks(date);
                
                CREATE INDEX IF NOT EXISTS idx_html_cached_at 
                ON app_html_cache(cached_at);
            """)
    
    def store_ranks(self, records: List[RawAppRecord]) -> None:
        """Store rank data from raw records.
        
        Args:
            records: List of raw app records to cache
        """
        with sqlite3.connect(self.db_path) as conn:
            date_str = datetime.utcnow().date().isoformat()
            
            for record in records:
                conn.execute("""
                    INSERT OR REPLACE INTO app_ranks 
                    (app_id, category, country, chart, rank, date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    record.app_id,
                    record.category,
                    record.country,
                    record.chart,
                    record.rank,
                    date_str
                ))
        
        logger.info(f"Stored {len(records)} rank records in cache")
    
    def get_rank_deltas(self, app_ids: List[str], days_back: int = 7) -> Dict[str, int]:
        """Get rank changes for apps over specified period.
        
        Args:
            app_ids: List of app IDs to check
            days_back: Number of days to look back
            
        Returns:
            Dict mapping app_id to rank delta (negative = rank improved)
        """
        deltas = {}
        cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).date().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            for app_id in app_ids:
                # Get current and historical ranks for this app
                cursor = conn.execute("""
                    SELECT rank, date 
                    FROM app_ranks 
                    WHERE app_id = ? AND date >= ?
                    ORDER BY date DESC
                    LIMIT 2
                """, (app_id, cutoff_date))
                
                rows = cursor.fetchall()
                if len(rows) >= 2:
                    current_rank = rows[0]['rank']
                    old_rank = rows[-1]['rank']
                    deltas[app_id] = current_rank - old_rank
        
        logger.debug(f"Computed rank deltas for {len(deltas)}/{len(app_ids)} apps")
        return deltas
    
    def store_html(self, app_id: str, country: str, html: str) -> None:
        """Store HTML content for app page.
        
        Args:
            app_id: App Store app ID
            country: Country code
            html: HTML content to cache
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO app_html_cache 
                (app_id, country, html, cached_at)
                VALUES (?, ?, ?, ?)
            """, (app_id, country, html, datetime.utcnow().isoformat()))
    
    def get_html(self, app_id: str, country: str, max_age_hours: int = 168) -> Optional[str]:
        """Get cached HTML if not too old.
        
        Args:
            app_id: App Store app ID
            country: Country code
            max_age_hours: Maximum age of cached content in hours
            
        Returns:
            Cached HTML or None if not found/too old
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT html, cached_at 
                FROM app_html_cache 
                WHERE app_id = ? AND country = ?
            """, (app_id, country))
            
            row = cursor.fetchone()
            if row:
                cached_at = datetime.fromisoformat(row['cached_at'])
                if cached_at > cutoff_time:
                    return row['html']
        
        return None
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> None:
        """Remove old cached data.
        
        Args:
            days_to_keep: Number of days of data to retain
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).date().isoformat()
        cutoff_time = (datetime.utcnow() - timedelta(days=days_to_keep)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Clean old ranks
            conn.execute("DELETE FROM app_ranks WHERE date < ?", (cutoff_date,))
            
            # Clean old HTML cache
            conn.execute("DELETE FROM app_html_cache WHERE cached_at < ?", (cutoff_time,))
            
            conn.commit()
        
        logger.info(f"Cleaned cache data older than {days_to_keep} days")


class SupabasePublisher:
    """Publisher for Supabase database."""
    
    def __init__(self, url: Optional[str] = None, service_key: Optional[str] = None):
        """Initialize Supabase client.
        
        Args:
            url: Supabase URL (defaults to SUPABASE_URL env var)
            service_key: Supabase service key (defaults to SUPABASE_SERVICE_KEY env var)
        """
        self.url = url or os.getenv("SUPABASE_URL")
        self.service_key = service_key or os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.url or not self.service_key:
            raise ValueError(
                "Supabase URL and service key required. "
                "Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables."
            )
        
        self.client: Client = create_client(self.url, self.service_key)
        logger.info("Initialized Supabase client")
    
    def convert_to_db_rows(self, scored_records: List[ScoredAppRecord]) -> List[dict]:
        """Convert scored records to database row format.
        
        Args:
            scored_records: List of scored app records
            
        Returns:
            List of dictionaries for database insertion
        """
        generated_at = datetime.utcnow()
        
        db_rows = []
        for record in scored_records:
            row = {
                "generated_at": generated_at.isoformat(),
                "category": record.category,
                "country": record.country,
                "chart": record.chart,
                "rank": record.rank,
                "app_id": record.app_id,
                "bundle_id": record.bundle_id,
                "name": record.name,
                "price": record.price,
                "has_iap": record.has_iap,
                "rating_count": record.rating_count,
                "rating_avg": record.rating_avg,
                "desc_len": record.desc_len,
                "rank_delta7d": record.rank_delta7d,
                "demand": record.demand,
                "monetization": record.monetization,
                "low_complexity": record.low_complexity,
                "moat_risk": record.moat_risk,
                "total": record.total,
                "raw": record.raw_data
            }
            db_rows.append(row)
        
        return db_rows
    
    def publish_results(self, scored_records: List[ScoredAppRecord]) -> bool:
        """Publish scored records to Supabase.
        
        Args:
            scored_records: List of scored app records to publish
            
        Returns:
            True if successful, False otherwise
        """
        if not scored_records:
            logger.warning("No records to publish")
            return True
        
        try:
            db_rows = self.convert_to_db_rows(scored_records)
            generated_at = db_rows[0]["generated_at"]
            
            # Delete any existing records with the same generated_at to ensure idempotency
            self.client.table("scout_results").delete().eq(
                "generated_at", generated_at
            ).execute()
            
            # Insert new records in batches
            batch_size = 100
            for i in range(0, len(db_rows), batch_size):
                batch = db_rows[i:i + batch_size]
                
                result = self.client.table("scout_results").insert(batch).execute()
                
                if not result.data:
                    logger.error(f"Failed to insert batch {i//batch_size + 1}")
                    return False
            
            logger.info(f"Successfully published {len(scored_records)} records to Supabase")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish results to Supabase: {e}")
            return False
    
    def check_connection(self) -> bool:
        """Check if Supabase connection is working.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try a simple query to test connection
            result = self.client.table("scout_results").select("id").limit(1).execute()
            logger.info("Supabase connection check successful")
            return True
        except Exception as e:
            logger.error(f"Supabase connection check failed: {e}")
            return False
    
    def get_latest_batch_time(self) -> Optional[datetime]:
        """Get the timestamp of the most recent batch.
        
        Returns:
            Datetime of latest batch or None if no data
        """
        try:
            result = self.client.table("scout_results").select(
                "generated_at"
            ).order("generated_at", desc=True).limit(1).execute()
            
            if result.data:
                return datetime.fromisoformat(result.data[0]["generated_at"].replace("Z", "+00:00"))
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get latest batch time: {e}")
            return None


class DataStore:
    """Combined data storage interface."""
    
    def __init__(
        self, 
        cache_path: str = "~/.trendscout/cache.db",
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None
    ):
        """Initialize data store with cache and publisher.
        
        Args:
            cache_path: Path to SQLite cache database
            supabase_url: Supabase URL (optional, uses env var)
            supabase_key: Supabase service key (optional, uses env var)
        """
        self.cache = SQLiteCache(cache_path)
        self.publisher = SupabasePublisher(supabase_url, supabase_key)
    
    def store_and_publish(self, scored_records: List[ScoredAppRecord]) -> bool:
        """Store records in cache and publish to Supabase.
        
        Args:
            scored_records: List of scored app records
            
        Returns:
            True if both operations successful, False otherwise
        """
        try:
            # Convert to raw records for cache storage
            raw_records = []
            for scored in scored_records:
                raw_record = RawAppRecord(
                    category=scored.category,
                    country=scored.country,
                    chart=scored.chart,
                    rank=scored.rank,
                    app_id=scored.app_id,
                    name=scored.name,
                    rss_url=scored.rss_url,
                    fetched_at=scored.fetched_at,
                    raw_data=scored.raw_data
                )
                raw_records.append(raw_record)
            
            # Store in cache
            self.cache.store_ranks(raw_records)
            
            # Publish to Supabase
            success = self.publisher.publish_results(scored_records)
            
            if success:
                logger.info("Successfully stored and published results")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to store and publish results: {e}")
            return False
    
    def check_health(self) -> Dict[str, bool]:
        """Check health of all storage components.
        
        Returns:
            Dict with health status of each component
        """
        health = {}
        
        # Check cache
        try:
            with sqlite3.connect(self.cache.db_path) as conn:
                conn.execute("SELECT 1").fetchone()
            health["cache"] = True
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            health["cache"] = False
        
        # Check Supabase
        health["supabase"] = self.publisher.check_connection()
        
        return health