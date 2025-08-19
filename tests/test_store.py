"""Tests for data storage and caching."""

import pytest
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from trendscout.store import SQLiteCache, SupabasePublisher, DataStore
from trendscout.models import RawAppRecord, ScoredAppRecord, AppPageData


class TestSQLiteCache:
    """Test SQLiteCache class."""
    
    @pytest.fixture
    def temp_cache(self):
        """Create a temporary cache for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            cache = SQLiteCache(f.name)
            yield cache
            Path(f.name).unlink(missing_ok=True)
    
    def test_init_creates_tables(self, temp_cache):
        """Test cache initialization creates required tables."""
        with sqlite3.connect(temp_cache.db_path) as conn:
            cursor = conn.cursor()
            
            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert "app_ranks" in tables
            assert "app_html_cache" in tables
    
    def test_store_ranks(self, temp_cache):
        """Test storing rank data."""
        records = [
            RawAppRecord(
                category="Utilities", country="US", chart="free", rank=1,
                app_id="123", name="App 1", rss_url="https://example.com",
                fetched_at=datetime.utcnow()
            ),
            RawAppRecord(
                category="Games", country="CA", chart="paid", rank=2,
                app_id="456", name="App 2", rss_url="https://example.com",
                fetched_at=datetime.utcnow()
            )
        ]
        
        temp_cache.store_ranks(records)
        
        # Verify data was stored
        with sqlite3.connect(temp_cache.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM app_ranks")
            count = cursor.fetchone()[0]
            assert count == 2
            
            # Check specific record
            cursor.execute("SELECT * FROM app_ranks WHERE app_id = '123'")
            row = cursor.fetchone()
            assert row[0] == "123"  # app_id
            assert row[1] == "Utilities"  # category
            assert row[4] == 1  # rank
    
    def test_get_rank_deltas(self, temp_cache):
        """Test rank delta calculation."""
        # Store historical data
        with sqlite3.connect(temp_cache.db_path) as conn:
            today = datetime.utcnow().date().isoformat()
            week_ago = (datetime.utcnow() - timedelta(days=7)).date().isoformat()
            
            # App improved from rank 10 to rank 5
            conn.execute("""
                INSERT INTO app_ranks (app_id, category, country, chart, rank, date)
                VALUES ('123', 'Utilities', 'US', 'free', 10, ?)
            """, (week_ago,))
            
            conn.execute("""
                INSERT INTO app_ranks (app_id, category, country, chart, rank, date)
                VALUES ('123', 'Utilities', 'US', 'free', 5, ?)
            """, (today,))
            
            # App declined from rank 3 to rank 8
            conn.execute("""
                INSERT INTO app_ranks (app_id, category, country, chart, rank, date)
                VALUES ('456', 'Games', 'CA', 'paid', 3, ?)
            """, (week_ago,))
            
            conn.execute("""
                INSERT INTO app_ranks (app_id, category, country, chart, rank, date)
                VALUES ('456', 'Games', 'CA', 'paid', 8, ?)
            """, (today,))
        
        deltas = temp_cache.get_rank_deltas(["123", "456"])
        
        assert deltas["123"] == -5  # Improved (current 5 - old 10 = -5)
        assert deltas["456"] == 5   # Declined (current 8 - old 3 = 5)
    
    def test_store_and_get_html(self, temp_cache):
        """Test HTML caching."""
        app_id = "123456789"
        country = "us"
        html_content = "<html><body>Test app page</body></html>"
        
        # Store HTML
        temp_cache.store_html(app_id, country, html_content)
        
        # Retrieve fresh HTML (should work)
        retrieved = temp_cache.get_html(app_id, country, max_age_hours=24)
        assert retrieved == html_content
        
        # Retrieve old HTML (should return None)
        retrieved_old = temp_cache.get_html(app_id, country, max_age_hours=0)
        assert retrieved_old is None
    
    def test_cleanup_old_data(self, temp_cache):
        """Test cleaning up old cache data."""
        with sqlite3.connect(temp_cache.db_path) as conn:
            # Insert old data
            old_date = (datetime.utcnow() - timedelta(days=40)).date().isoformat()
            old_time = (datetime.utcnow() - timedelta(days=40)).isoformat()
            
            conn.execute("""
                INSERT INTO app_ranks (app_id, category, country, chart, rank, date)
                VALUES ('old_app', 'Utilities', 'US', 'free', 1, ?)
            """, (old_date,))
            
            conn.execute("""
                INSERT INTO app_html_cache (app_id, country, html, cached_at)
                VALUES ('old_app', 'us', '<html></html>', ?)
            """, (old_time,))
            
            # Insert recent data
            recent_date = datetime.utcnow().date().isoformat()
            recent_time = datetime.utcnow().isoformat()
            
            conn.execute("""
                INSERT INTO app_ranks (app_id, category, country, chart, rank, date)
                VALUES ('new_app', 'Utilities', 'US', 'free', 1, ?)
            """, (recent_date,))
            
            conn.execute("""
                INSERT INTO app_html_cache (app_id, country, html, cached_at)
                VALUES ('new_app', 'us', '<html></html>', ?)
            """, (recent_time,))
        
        # Cleanup old data (keep last 30 days)
        temp_cache.cleanup_old_data(days_to_keep=30)
        
        # Verify old data is gone
        with sqlite3.connect(temp_cache.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM app_ranks WHERE app_id = 'old_app'")
            assert cursor.fetchone()[0] == 0
            
            cursor.execute("SELECT COUNT(*) FROM app_html_cache WHERE app_id = 'old_app'")
            assert cursor.fetchone()[0] == 0
            
            # Verify recent data remains
            cursor.execute("SELECT COUNT(*) FROM app_ranks WHERE app_id = 'new_app'")
            assert cursor.fetchone()[0] == 1
            
            cursor.execute("SELECT COUNT(*) FROM app_html_cache WHERE app_id = 'new_app'")
            assert cursor.fetchone()[0] == 1


class TestSupabasePublisher:
    """Test SupabasePublisher class."""
    
    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        with patch.dict('os.environ', {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_KEY': 'test-key'
        }):
            publisher = SupabasePublisher()
            assert publisher.url == 'https://test.supabase.co'
            assert publisher.service_key == 'test-key'
    
    def test_init_with_params(self):
        """Test initialization with explicit parameters."""
        publisher = SupabasePublisher(
            url='https://custom.supabase.co',
            service_key='custom-key'
        )
        assert publisher.url == 'https://custom.supabase.co'
        assert publisher.service_key == 'custom-key'
    
    def test_init_missing_credentials(self):
        """Test initialization fails without credentials."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="Supabase URL and service key required"):
                SupabasePublisher()
    
    def test_convert_to_db_rows(self):
        """Test converting scored records to database format."""
        publisher = SupabasePublisher(
            url='https://test.supabase.co',
            service_key='test-key'
        )
        
        scored_records = [
            ScoredAppRecord(
                category="Utilities", country="US", chart="free", rank=1,
                app_id="123", name="Test App", rss_url="https://example.com",
                fetched_at=datetime.utcnow(), bundle_id="com.test.app",
                price=0.0, has_iap=True, rating_count=1000, rating_avg=4.0,
                desc_len=200, rank_delta7d=-5, demand=3.5, monetization=3.0,
                low_complexity=4.0, moat_risk=2.0, total=3.2
            )
        ]
        
        db_rows = publisher.convert_to_db_rows(scored_records)
        
        assert len(db_rows) == 1
        row = db_rows[0]
        
        assert row["app_id"] == "123"
        assert row["bundle_id"] == "com.test.app"
        assert row["total"] == 3.2
        assert "generated_at" in row
    
    @patch('trendscout.store.create_client')
    def test_publish_results_success(self, mock_create_client):
        """Test successful result publishing."""
        # Mock Supabase client
        mock_client = Mock()
        mock_table = Mock()
        mock_delete = Mock()
        mock_insert = Mock()
        
        mock_create_client.return_value = mock_client
        mock_client.table.return_value = mock_table
        mock_table.delete.return_value = mock_delete
        mock_delete.eq.return_value = mock_delete
        mock_delete.execute.return_value = None
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = Mock(data=[{"id": "test"}])
        
        publisher = SupabasePublisher(
            url='https://test.supabase.co',
            service_key='test-key'
        )
        
        scored_records = [
            ScoredAppRecord(
                category="Utilities", country="US", chart="free", rank=1,
                app_id="123", name="Test App", rss_url="https://example.com",
                fetched_at=datetime.utcnow(), bundle_id="com.test.app",
                price=0.0, has_iap=True, rating_count=1000, rating_avg=4.0,
                desc_len=200, rank_delta7d=-5, demand=3.5, monetization=3.0,
                low_complexity=4.0, moat_risk=2.0, total=3.2
            )
        ]
        
        result = publisher.publish_results(scored_records)
        
        assert result is True
        mock_client.table.assert_called_with("scout_results")
        mock_table.insert.assert_called_once()
    
    @patch('trendscout.store.create_client')
    def test_check_connection_success(self, mock_create_client):
        """Test successful connection check."""
        mock_client = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_limit = Mock()
        
        mock_create_client.return_value = mock_client
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.limit.return_value = mock_limit
        mock_limit.execute.return_value = Mock(data=[])
        
        publisher = SupabasePublisher(
            url='https://test.supabase.co',
            service_key='test-key'
        )
        
        result = publisher.check_connection()
        
        assert result is True
        mock_client.table.assert_called_with("scout_results")


class TestDataStore:
    """Test DataStore integration class."""
    
    @pytest.fixture
    def temp_store(self):
        """Create a temporary data store for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            with patch.dict('os.environ', {
                'SUPABASE_URL': 'https://test.supabase.co',
                'SUPABASE_SERVICE_KEY': 'test-key'
            }):
                store = DataStore(cache_path=f.name)
                yield store
                Path(f.name).unlink(missing_ok=True)
    
    def test_init(self, temp_store):
        """Test data store initialization."""
        assert isinstance(temp_store.cache, SQLiteCache)
        assert isinstance(temp_store.publisher, SupabasePublisher)
    
    @patch('trendscout.store.create_client')
    def test_store_and_publish_success(self, mock_create_client):
        """Test successful store and publish operation."""
        # Mock Supabase operations first
        mock_client = Mock()
        mock_table = Mock()
        mock_delete = Mock()
        mock_insert = Mock()
        
        mock_create_client.return_value = mock_client
        mock_client.table.return_value = mock_table
        mock_table.delete.return_value = mock_delete
        mock_delete.eq.return_value = mock_delete
        mock_delete.execute.return_value = None
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = Mock(data=[{"id": "test"}])
        
        # Now create the data store with mocked Supabase
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            with patch.dict('os.environ', {
                'SUPABASE_URL': 'https://test.supabase.co',
                'SUPABASE_SERVICE_KEY': 'test-key'
            }):
                store = DataStore(cache_path=f.name)
                
                # Create test data
                scored_records = [
                    ScoredAppRecord(
                        category="Utilities", country="US", chart="free", rank=1,
                        app_id="123", name="Test App", rss_url="https://example.com",
                        fetched_at=datetime.utcnow(), bundle_id="com.test.app",
                        price=0.0, has_iap=True, rating_count=1000, rating_avg=4.0,
                        desc_len=200, rank_delta7d=-5, demand=3.5, monetization=3.0,
                        low_complexity=4.0, moat_risk=2.0, total=3.2
                    )
                ]
                
                result = store.store_and_publish(scored_records)
                
                assert result is True
                
                # Verify data was cached
                with sqlite3.connect(store.cache.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM app_ranks")
                    assert cursor.fetchone()[0] == 1
                
                # Cleanup
                Path(f.name).unlink(missing_ok=True)
    
    def test_check_health(self, temp_store):
        """Test health check functionality."""
        with patch.object(temp_store.publisher, 'check_connection', return_value=True):
            health = temp_store.check_health()
            
            assert "cache" in health
            assert "supabase" in health
            assert health["cache"] is True
            assert health["supabase"] is True