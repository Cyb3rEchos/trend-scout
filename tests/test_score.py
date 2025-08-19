"""Tests for scoring algorithms."""

import pytest
from datetime import datetime
from unittest.mock import Mock

from trendscout.score import AppScorer
from trendscout.models import RawAppRecord, AppPageData, ScoredAppRecord


class TestAppScorer:
    """Test AppScorer class."""
    
    def test_init(self):
        """Test scorer initialization."""
        scorer = AppScorer()
        assert isinstance(scorer.LOW_COMPLEXITY_KEYWORDS, list)
        assert isinstance(scorer.HIGH_MOAT_KEYWORDS, list)
        assert "counter" in scorer.LOW_COMPLEXITY_KEYWORDS
        assert "disney" in scorer.HIGH_MOAT_KEYWORDS
    
    def test_compute_demand_score_rank_improvement(self):
        """Test demand scoring with rank improvement."""
        scorer = AppScorer()
        
        # Significant improvement
        score = scorer.compute_demand_score(rank_delta7d=-15, rating_count=1000)
        assert score >= 3.0  # Base 1.0 + 2.0 improvement + 0.5 ratings
        
        # Moderate improvement
        score = scorer.compute_demand_score(rank_delta7d=-7, rating_count=1000)
        assert score >= 2.5  # Base 1.0 + 1.5 improvement + 0.5 ratings
        
        # Slight improvement
        score = scorer.compute_demand_score(rank_delta7d=-2, rating_count=1000)
        assert score >= 2.0  # Base 1.0 + 1.0 improvement + 0.5 ratings
    
    def test_compute_demand_score_rank_decline(self):
        """Test demand scoring with rank decline."""
        scorer = AppScorer()
        
        # Significant decline
        score = scorer.compute_demand_score(rank_delta7d=10, rating_count=100)
        assert score <= 2.0  # Base 1.0 - 0.5 decline + 0.25 ratings
        
        # No change
        score = scorer.compute_demand_score(rank_delta7d=0, rating_count=100)
        assert score >= 1.5  # Base 1.0 + 0.5 no change + 0.25 ratings
    
    def test_compute_demand_score_rating_volume(self):
        """Test demand scoring with different rating volumes."""
        scorer = AppScorer()
        
        # High volume
        score_high = scorer.compute_demand_score(rank_delta7d=0, rating_count=15000)
        
        # Medium volume
        score_med = scorer.compute_demand_score(rank_delta7d=0, rating_count=5000)
        
        # Low volume
        score_low = scorer.compute_demand_score(rank_delta7d=0, rating_count=50)
        
        assert score_high > score_med > score_low
    
    def test_compute_demand_score_review_velocity(self):
        """Test demand scoring with review velocity bonus."""
        scorer = AppScorer()
        
        recent_reviews = ["Review 1", "Review 2", "Review 3", "Review 4"]
        
        score_with_reviews = scorer.compute_demand_score(
            rank_delta7d=0, rating_count=1000, recent_reviews=recent_reviews
        )
        
        score_without_reviews = scorer.compute_demand_score(
            rank_delta7d=0, rating_count=1000, recent_reviews=None
        )
        
        assert score_with_reviews > score_without_reviews
    
    def test_compute_monetization_score_free_no_iap(self):
        """Test monetization scoring for free app without IAP."""
        scorer = AppScorer()
        
        score = scorer.compute_monetization_score(price=0.0, has_iap=False)
        assert score == 1.0
    
    def test_compute_monetization_score_free_with_iap(self):
        """Test monetization scoring for free app with IAP."""
        scorer = AppScorer()
        
        # Basic IAP
        score = scorer.compute_monetization_score(price=0.0, has_iap=True)
        assert score == 3.0
        
        # IAP with premium indicators
        description = "Premium features available. Upgrade to Pro for advanced tools. Subscription plans available."
        score = scorer.compute_monetization_score(price=0.0, has_iap=True, description=description)
        assert score == 4.0
    
    def test_compute_monetization_score_paid(self):
        """Test monetization scoring for paid apps."""
        scorer = AppScorer()
        
        # Paid without IAP
        score = scorer.compute_monetization_score(price=2.99, has_iap=False)
        assert score == 3.0
        
        # Paid with IAP
        score = scorer.compute_monetization_score(price=4.99, has_iap=True)
        assert score == 5.0
    
    def test_compute_low_complexity_score_simple_app(self):
        """Test complexity scoring for simple utility apps."""
        scorer = AppScorer()
        
        # Very simple - multiple keywords
        score = scorer.compute_low_complexity_score(
            name="QR Code Scanner Timer",
            description="Simple QR scanner and timer widget"
        )
        assert score >= 4.0
        
        # Moderately simple - one keyword
        score = scorer.compute_low_complexity_score(
            name="PDF Reader",
            description="Read PDF documents easily"
        )
        assert score >= 3.0
    
    def test_compute_low_complexity_score_complex_app(self):
        """Test complexity scoring for complex apps."""
        scorer = AppScorer()
        
        # Complex - AI/ML keywords
        score = scorer.compute_low_complexity_score(
            name="AI Photo Editor Pro",
            description="Advanced machine learning algorithms for professional photo editing"
        )
        assert score <= 2.0
        
        # Very complex - multiple complexity indicators
        score = scorer.compute_low_complexity_score(
            name="Enterprise Analytics Platform",
            description="Advanced AI-powered business analytics with complex workflow integration"
        )
        assert score == 1.0
    
    def test_compute_low_complexity_score_default(self):
        """Test complexity scoring for apps without clear indicators."""
        scorer = AppScorer()
        
        score = scorer.compute_low_complexity_score(
            name="Regular App",
            description="A normal app without specific technical indicators"
        )
        assert score == 2.5  # Default moderate complexity
    
    def test_compute_moat_risk_score_low_risk(self):
        """Test moat risk scoring for generic apps."""
        scorer = AppScorer()
        
        score = scorer.compute_moat_risk_score(
            name="Timer App",
            description="A simple timer for productivity"
        )
        assert score == 1.0  # Low risk
    
    def test_compute_moat_risk_score_high_risk(self):
        """Test moat risk scoring for branded apps."""
        scorer = AppScorer()
        
        # Multiple brand mentions (official + disney = 2 matches = 5.0)
        score = scorer.compute_moat_risk_score(
            name="Official Disney Game",
            description="Play with your favorite Disney characters"
        )
        assert score == 5.0
        
        # Multiple brand mentions
        score = scorer.compute_moat_risk_score(
            name="Official Marvel Disney Heroes",
            description="Official Marvel and Disney superhero game"
        )
        assert score == 5.0
    
    def test_compute_moat_risk_score_trademark_indicators(self):
        """Test moat risk scoring with trademark indicators."""
        scorer = AppScorer()
        
        score = scorer.compute_moat_risk_score(
            name="Licensed App™",
            description="This is a trademark® protected application"
        )
        assert score == 3.0  # Moderate risk
    
    def test_compute_total_score(self):
        """Test total weighted score calculation."""
        scorer = AppScorer()
        
        # Test with known values
        demand = 4.0
        monetization = 3.0
        low_complexity = 5.0
        moat_risk = 2.0
        
        total = scorer.compute_total_score(demand, monetization, low_complexity, moat_risk)
        
        # Expected: 0.35*4.0 + 0.25*3.0 + 0.25*5.0 + 0.15*(5-2.0)
        # = 1.4 + 0.75 + 1.25 + 0.45 = 3.85
        assert total == 3.85
    
    def test_score_app_complete(self):
        """Test complete app scoring workflow."""
        scorer = AppScorer()
        
        # Create test data
        raw_record = RawAppRecord(
            category="Utilities",
            country="US",
            chart="free",
            rank=5,
            app_id="123456789",
            name="Simple Timer Counter",
            rss_url="https://example.com/rss",
            fetched_at=datetime.utcnow()
        )
        
        app_data = AppPageData(
            bundle_id="com.example.timer",
            price=0.0,
            has_iap=True,
            rating_count=5000,
            rating_avg=4.2,
            desc_len=200,
            recent_reviews=["Great app!", "Very useful", "Love it"]
        )
        
        rank_delta7d = -3  # Rank improved
        
        scored_record = scorer.score_app(raw_record, app_data, rank_delta7d)
        
        # Verify all fields are populated
        assert isinstance(scored_record, ScoredAppRecord)
        assert scored_record.app_id == "123456789"
        assert scored_record.bundle_id == "com.example.timer"
        assert scored_record.rank_delta7d == -3
        
        # Verify scores are in valid ranges
        assert 1.0 <= scored_record.demand <= 5.0
        assert 1.0 <= scored_record.monetization <= 5.0
        assert 1.0 <= scored_record.low_complexity <= 5.0
        assert 1.0 <= scored_record.moat_risk <= 5.0
        assert 0.0 <= scored_record.total <= 5.0
        
        # Verify this should be a high-scoring app (simple utility, improved rank, good reviews)
        assert scored_record.low_complexity >= 4.0  # Simple timer/counter
        assert scored_record.demand >= 2.0  # Rank improved + good ratings
        assert scored_record.monetization >= 3.0  # Free + IAP
        assert scored_record.moat_risk <= 2.0  # Generic concept
    
    def test_score_apps_batch(self):
        """Test batch scoring of multiple apps."""
        scorer = AppScorer()
        
        # Create test data
        raw_records = [
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
        
        app_data_map = {
            "123": AppPageData(
                bundle_id="com.app1", price=0.0, has_iap=False,
                rating_count=100, rating_avg=3.0, desc_len=100
            ),
            "456": AppPageData(
                bundle_id="com.app2", price=2.99, has_iap=True,
                rating_count=500, rating_avg=4.5, desc_len=300
            )
        }
        
        rank_deltas = {"123": -2, "456": 1}
        
        scored_records = scorer.score_apps(raw_records, app_data_map, rank_deltas)
        
        assert len(scored_records) == 2
        assert scored_records[0].app_id == "123"
        assert scored_records[1].app_id == "456"
        assert scored_records[0].rank_delta7d == -2
        assert scored_records[1].rank_delta7d == 1
    
    def test_score_apps_missing_data(self):
        """Test batch scoring with missing app data."""
        scorer = AppScorer()
        
        raw_records = [
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
        
        # Only provide data for one app
        app_data_map = {
            "123": AppPageData(
                bundle_id="com.app1", price=0.0, has_iap=False,
                rating_count=100, rating_avg=3.0, desc_len=100
            )
        }
        
        scored_records = scorer.score_apps(raw_records, app_data_map)
        
        # Should only return records for apps with data
        assert len(scored_records) == 1
        assert scored_records[0].app_id == "123"