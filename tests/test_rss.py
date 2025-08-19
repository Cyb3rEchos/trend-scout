"""Tests for RSS fetching and parsing."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from trendscout.rss import RSSFetcher
from trendscout.models import CollectConfig


class TestRSSFetcher:
    """Test RSSFetcher class."""
    
    def test_init(self):
        """Test fetcher initialization."""
        fetcher = RSSFetcher(user_agent="Test/1.0", rate_limit_delay=0.1)
        
        assert fetcher.user_agent == "Test/1.0"
        assert fetcher.rate_limit_delay == 0.1
        assert "Test/1.0" in fetcher.session.headers["User-Agent"]
    
    def test_build_rss_url_valid(self):
        """Test building valid RSS URLs."""
        fetcher = RSSFetcher()
        
        # Test free chart
        url = fetcher.build_rss_url("Utilities", "US", "free", 25)
        expected = "https://rss.applemarketingtools.com/api/v2/us/apps/top-free/25/utilities.json"
        assert url == expected
        
        # Test paid chart
        url = fetcher.build_rss_url("Photo & Video", "CA", "paid", 10)
        expected = "https://rss.applemarketingtools.com/api/v2/ca/apps/top-paid/10/photo-video.json"
        assert url == expected
    
    def test_build_rss_url_invalid_chart(self):
        """Test invalid chart type."""
        fetcher = RSSFetcher()
        
        with pytest.raises(ValueError, match="Invalid chart type"):
            fetcher.build_rss_url("Utilities", "US", "invalid", 25)
    
    def test_build_rss_url_invalid_category(self):
        """Test invalid category."""
        fetcher = RSSFetcher()
        
        with pytest.raises(ValueError, match="Invalid category"):
            fetcher.build_rss_url("Invalid Category", "US", "free", 25)
    
    def test_extract_app_id_valid(self):
        """Test extracting app ID from valid URLs."""
        fetcher = RSSFetcher()
        
        # Standard App Store URL
        url = "https://apps.apple.com/us/app/example-app/id123456789"
        app_id = fetcher._extract_app_id(url)
        assert app_id == "123456789"
        
        # URL with parameters
        url = "https://apps.apple.com/us/app/example-app/id987654321?mt=8"
        app_id = fetcher._extract_app_id(url)
        assert app_id == "987654321"
    
    def test_extract_app_id_invalid(self):
        """Test extracting app ID from invalid URLs."""
        fetcher = RSSFetcher()
        
        # No app ID
        assert fetcher._extract_app_id("https://example.com/") is None
        
        # Empty string
        assert fetcher._extract_app_id("") is None
        
        # Invalid format
        assert fetcher._extract_app_id("https://apps.apple.com/us/app/example") is None
    
    @patch('trendscout.rss.time.sleep')
    def test_collect_category_success(self, mock_sleep):
        """Test successful category collection."""
        fetcher = RSSFetcher()
        
        # Mock RSS data
        mock_rss_data = {
            "feed": {
                "results": [
                    {
                        "name": "Test App 1",
                        "url": "https://apps.apple.com/us/app/test1/id123456789"
                    },
                    {
                        "name": "Test App 2", 
                        "url": "https://apps.apple.com/us/app/test2/id987654321"
                    }
                ]
            }
        }
        
        with patch.object(fetcher, 'fetch_rss_data', return_value=mock_rss_data):
            records = fetcher.collect_category("Utilities", "US", "free", 25)
        
        assert len(records) == 2
        assert records[0].app_id == "123456789"
        assert records[0].name == "Test App 1"
        assert records[1].app_id == "987654321"
        assert records[1].name == "Test App 2"
        
        # Verify rate limiting was applied
        mock_sleep.assert_called_once()
    
    def test_parse_rss_entries(self):
        """Test parsing RSS entries into records."""
        fetcher = RSSFetcher()
        
        rss_data = {
            "feed": {
                "results": [
                    {
                        "name": "Calculator",
                        "url": "https://apps.apple.com/us/app/calculator/id123456789",
                        "artistName": "Example Developer"
                    },
                    {
                        "name": "Timer",
                        "url": "https://apps.apple.com/us/app/timer/id987654321", 
                        "artistName": "Another Developer"
                    }
                ]
            }
        }
        
        records = fetcher.parse_rss_entries(
            rss_data, "Utilities", "US", "free", "https://example.com/rss"
        )
        
        assert len(records) == 2
        
        # Check first record
        assert records[0].category == "Utilities"
        assert records[0].country == "US"
        assert records[0].chart == "free"
        assert records[0].rank == 1
        assert records[0].app_id == "123456789"
        assert records[0].name == "Calculator"
        
        # Check second record  
        assert records[1].rank == 2
        assert records[1].app_id == "987654321"
        assert records[1].name == "Timer"
    
    def test_parse_rss_entries_invalid_url(self):
        """Test parsing entries with invalid app URLs."""
        fetcher = RSSFetcher()
        
        rss_data = {
            "feed": {
                "results": [
                    {
                        "name": "Valid App",
                        "url": "https://apps.apple.com/us/app/valid/id123456789"
                    },
                    {
                        "name": "Invalid App",
                        "url": "https://invalid-url.com/no-app-id"
                    }
                ]
            }
        }
        
        records = fetcher.parse_rss_entries(
            rss_data, "Utilities", "US", "free", "https://example.com/rss"
        )
        
        # Should only return the valid record
        assert len(records) == 1
        assert records[0].app_id == "123456789"
    
    @patch('trendscout.rss.time.sleep')
    def test_collect_all(self, mock_sleep):
        """Test collecting all configured combinations."""
        fetcher = RSSFetcher()
        
        config = CollectConfig(
            categories=["Utilities", "Games"],
            countries=["US", "CA"],
            charts=["free"],
            top_n=2
        )
        
        # Mock successful collection for each combination
        mock_records = [
            Mock(app_id="123", name="App 1"),
            Mock(app_id="456", name="App 2")
        ]
        
        with patch.object(fetcher, 'collect_category', return_value=mock_records) as mock_collect:
            all_records = fetcher.collect_all(config)
        
        # Should have called collect_category 4 times (2 categories × 2 countries × 1 chart)
        assert mock_collect.call_count == 4
        
        # Should return 8 total records (4 calls × 2 records each)
        assert len(all_records) == 8