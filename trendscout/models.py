"""Pydantic models for Trend Scout data structures."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class RawAppRecord(BaseModel):
    """Raw app record from RSS feed with basic metadata."""
    
    category: str = Field(..., description="App Store category")
    country: str = Field(..., description="Country code (US, CA, etc.)")
    chart: str = Field(..., description="Chart type (free or paid)")
    rank: int = Field(..., description="Current rank in chart", ge=1, le=25)
    app_id: str = Field(..., description="App Store app ID")
    name: str = Field(..., description="App name")
    rss_url: HttpUrl = Field(..., description="RSS feed URL")
    fetched_at: datetime = Field(..., description="When this record was fetched")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw RSS entry data")


class AppPageData(BaseModel):
    """Data extracted from app page HTML."""
    
    bundle_id: str = Field(..., description="App bundle identifier")
    price: float = Field(..., description="App price (0.0 for free)", ge=0)
    has_iap: bool = Field(..., description="Has in-app purchases")
    rating_count: int = Field(..., description="Number of ratings", ge=0)
    rating_avg: float = Field(..., description="Average rating", ge=0, le=5)
    desc_len: int = Field(..., description="Description length in characters", ge=0)
    recent_reviews: Optional[List[str]] = Field(None, description="Sample recent reviews")
    

class ScoredAppRecord(RawAppRecord):
    """Complete app record with page data and computed scores."""
    
    bundle_id: str = Field(..., description="App bundle identifier")
    price: float = Field(..., description="App price (0.0 for free)", ge=0)
    has_iap: bool = Field(..., description="Has in-app purchases")
    rating_count: int = Field(..., description="Number of ratings", ge=0)
    rating_avg: float = Field(..., description="Average rating", ge=0, le=5)
    desc_len: int = Field(..., description="Description length in characters", ge=0)
    rank_delta7d: Optional[int] = Field(None, description="Rank change over 7 days")
    
    # Scoring components
    demand: float = Field(..., description="Demand score (1-5)", ge=1, le=5)
    monetization: float = Field(..., description="Monetization score (1-5)", ge=1, le=5)
    low_complexity: float = Field(..., description="Low complexity score (1-5)", ge=1, le=5)
    moat_risk: float = Field(..., description="Moat risk score (1-5)", ge=1, le=5)
    total: float = Field(..., description="Total weighted score", ge=0, le=5)


class ScoutResultRow(BaseModel):
    """Database row for scout_results table."""
    
    id: Optional[str] = Field(None, description="UUID primary key")
    generated_at: datetime = Field(..., description="When this batch was generated")
    category: str = Field(..., description="App Store category")
    country: str = Field(..., description="Country code")
    chart: str = Field(..., description="Chart type (free or paid)")
    rank: int = Field(..., description="Current rank in chart", ge=1, le=25)
    app_id: str = Field(..., description="App Store app ID")
    bundle_id: str = Field(..., description="App bundle identifier")
    name: str = Field(..., description="App name")
    price: float = Field(..., description="App price", ge=0)
    has_iap: bool = Field(..., description="Has in-app purchases")
    rating_count: int = Field(..., description="Number of ratings", ge=0)
    rating_avg: float = Field(..., description="Average rating", ge=0, le=5)
    desc_len: int = Field(..., description="Description length", ge=0)
    rank_delta7d: Optional[int] = Field(None, description="Rank change over 7 days")
    demand: float = Field(..., description="Demand score", ge=1, le=5)
    monetization: float = Field(..., description="Monetization score", ge=1, le=5)
    low_complexity: float = Field(..., description="Low complexity score", ge=1, le=5)
    moat_risk: float = Field(..., description="Moat risk score", ge=1, le=5)
    total: float = Field(..., description="Total weighted score", ge=0, le=5)
    raw: Optional[Dict[str, Any]] = Field(None, description="Raw data as JSONB")


class DailyRankingRow(BaseModel):
    """Database row for daily_rankings table with perfect field alignment."""
    
    id: Optional[str] = Field(None, description="UUID primary key")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    category: str = Field(..., description="App Store category")
    country: str = Field(..., description="Country code")
    chart: str = Field(..., description="Chart type (free or paid)")
    rank: int = Field(..., description="Original App Store rank", ge=1)
    app_id: str = Field(..., description="App Store app ID")
    bundle_id: str = Field(..., description="App bundle identifier")
    name: str = Field(..., description="Original app name")
    price: float = Field(..., description="App price", ge=0)
    has_iap: bool = Field(..., description="Has in-app purchases")
    rating_count: int = Field(..., description="Number of ratings", ge=0)
    rating_avg: float = Field(..., description="Average rating", ge=0, le=5)
    desc_len: int = Field(..., description="Description length", ge=0)
    demand: float = Field(..., description="Demand score", ge=1, le=5)
    monetization: float = Field(..., description="Monetization score", ge=1, le=5)
    low_complexity: float = Field(..., description="Low complexity score", ge=1, le=5)
    moat_risk: float = Field(..., description="Moat risk score", ge=1, le=5)
    total: float = Field(..., description="Total weighted score", ge=0, le=5)
    clone_difficulty: str = Field(..., description="Clone difficulty: EASY_CLONE, MODERATE, COMPLEX, HIGH_RISK")
    revenue_potential: str = Field(..., description="Revenue potential: HIGH_REVENUE, GOOD_REVENUE, MODEST_REVENUE, LOW_REVENUE")
    category_rank: int = Field(..., description="Daily rank within category (1-10)", ge=1, le=10)
    ai_recommendation: Optional[str] = Field(None, description="AI-generated improvement recommendation text")
    recommendation_generated_at: Optional[str] = Field(None, description="When AI recommendation was generated")
    
    # NEW FIELDS for perfect alignment:
    clone_name: Optional[str] = Field(None, description="AI-generated clone app name")
    clone_name_custom: Optional[str] = Field(None, description="User-customized clone app name")
    build_priority: Optional[str] = Field(None, description="Build priority: TONIGHT, THIS_WEEK, THIS_MONTH, FUTURE")
    
    created_at: Optional[str] = Field(None, description="Record creation timestamp")
    updated_at: Optional[str] = Field(None, description="Record update timestamp")


class CollectConfig(BaseModel):
    """Configuration for data collection."""
    
    categories: List[str] = Field(..., description="Categories to collect")
    countries: List[str] = Field(..., description="Countries to collect")
    charts: List[str] = Field(..., description="Charts to collect (free, paid)")
    top_n: int = Field(25, description="Number of top apps per chart", ge=1, le=200)
    
    @classmethod
    def default(cls) -> "CollectConfig":
        """Return default configuration."""
        return cls(
            categories=[
                "Utilities",
                "Photo & Video", 
                "Productivity",
                "Health & Fitness",
                "Lifestyle",
                "Graphics & Design",
                "Music",
                "Education", 
                "Finance",
                "Entertainment"
            ],
            countries=["US", "CA", "GB", "AU", "DE"],
            charts=["free", "paid"],
            top_n=25
        )