"""Tests for Pydantic models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from trendscout.models import (
    RawAppRecord, AppPageData, ScoredAppRecord, 
    ScoutResultRow, CollectConfig
)


class TestRawAppRecord:
    """Test RawAppRecord model."""
    
    def test_valid_record(self):
        """Test creating a valid raw app record."""
        record = RawAppRecord(
            category="Utilities",
            country="US",
            chart="free",
            rank=1,
            app_id="123456789",
            name="Test App",
            rss_url="https://example.com/rss",
            fetched_at=datetime.utcnow()
        )
        
        assert record.category == "Utilities"
        assert record.rank == 1
        assert record.app_id == "123456789"
    
    def test_invalid_rank(self):
        """Test rank validation."""
        with pytest.raises(ValidationError):
            RawAppRecord(
                category="Utilities",
                country="US", 
                chart="free",
                rank=0,  # Invalid: must be >= 1
                app_id="123456789",
                name="Test App",
                rss_url="https://example.com/rss",
                fetched_at=datetime.utcnow()
            )
    
    def test_rank_upper_bound(self):
        """Test rank upper bound validation."""
        with pytest.raises(ValidationError):
            RawAppRecord(
                category="Utilities",
                country="US",
                chart="free", 
                rank=26,  # Invalid: must be <= 25
                app_id="123456789",
                name="Test App",
                rss_url="https://example.com/rss",
                fetched_at=datetime.utcnow()
            )


class TestAppPageData:
    """Test AppPageData model."""
    
    def test_valid_page_data(self):
        """Test creating valid app page data."""
        data = AppPageData(
            bundle_id="com.example.app",
            price=2.99,
            has_iap=True,
            rating_count=1500,
            rating_avg=4.2,
            desc_len=300
        )
        
        assert data.bundle_id == "com.example.app"
        assert data.price == 2.99
        assert data.has_iap is True
        assert data.rating_avg == 4.2
    
    def test_free_app(self):
        """Test free app with no IAP."""
        data = AppPageData(
            bundle_id="com.example.free",
            price=0.0,
            has_iap=False,
            rating_count=100,
            rating_avg=3.5,
            desc_len=150
        )
        
        assert data.price == 0.0
        assert data.has_iap is False
    
    def test_invalid_price(self):
        """Test negative price validation."""
        with pytest.raises(ValidationError):
            AppPageData(
                bundle_id="com.example.app",
                price=-1.0,  # Invalid: must be >= 0
                has_iap=False,
                rating_count=100,
                rating_avg=3.5,
                desc_len=150
            )
    
    def test_invalid_rating_avg(self):
        """Test rating average bounds."""
        with pytest.raises(ValidationError):
            AppPageData(
                bundle_id="com.example.app", 
                price=0.0,
                has_iap=False,
                rating_count=100,
                rating_avg=6.0,  # Invalid: must be <= 5
                desc_len=150
            )


class TestScoredAppRecord:
    """Test ScoredAppRecord model."""
    
    def test_valid_scored_record(self):
        """Test creating a valid scored record."""
        record = ScoredAppRecord(
            # Raw record fields
            category="Utilities",
            country="US",
            chart="free",
            rank=1,
            app_id="123456789",
            name="Test App",
            rss_url="https://example.com/rss",
            fetched_at=datetime.utcnow(),
            
            # App page fields
            bundle_id="com.example.app",
            price=0.0,
            has_iap=True,
            rating_count=1000,
            rating_avg=4.0,
            desc_len=250,
            rank_delta7d=-5,
            
            # Score fields
            demand=3.5,
            monetization=3.0,
            low_complexity=4.0,
            moat_risk=2.0,
            total=3.2
        )
        
        assert record.demand == 3.5
        assert record.total == 3.2
        assert record.rank_delta7d == -5
    
    def test_score_bounds(self):
        """Test score validation bounds."""
        with pytest.raises(ValidationError):
            ScoredAppRecord(
                category="Utilities",
                country="US",
                chart="free",
                rank=1,
                app_id="123456789", 
                name="Test App",
                rss_url="https://example.com/rss",
                fetched_at=datetime.utcnow(),
                bundle_id="com.example.app",
                price=0.0,
                has_iap=True,
                rating_count=1000,
                rating_avg=4.0,
                desc_len=250,
                demand=6.0,  # Invalid: must be <= 5
                monetization=3.0,
                low_complexity=4.0,
                moat_risk=2.0,
                total=3.2
            )


class TestCollectConfig:
    """Test CollectConfig model."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = CollectConfig.default()
        
        assert len(config.categories) == 10
        assert "Utilities" in config.categories
        assert "Entertainment" in config.categories
        assert len(config.countries) == 5
        assert "US" in config.countries
        assert "DE" in config.countries
        assert config.charts == ["free", "paid"]
        assert config.top_n == 25
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = CollectConfig(
            categories=["Utilities", "Games"],
            countries=["US", "CA"],
            charts=["free"],
            top_n=10
        )
        
        assert len(config.categories) == 2
        assert len(config.countries) == 2
        assert config.charts == ["free"]
        assert config.top_n == 10
    
    def test_invalid_top_n(self):
        """Test top_n validation."""
        with pytest.raises(ValidationError):
            CollectConfig(
                categories=["Utilities"],
                countries=["US"],
                charts=["free"],
                top_n=0  # Invalid: must be >= 1
            )