"""Configuration settings for Trend Scout production deployment."""

import os
from typing import Dict, Any


class ProductionConfig:
    """Production configuration for legitimate data collection."""
    
    # Rate limiting settings (conservative for Apple's APIs)
    RSS_RATE_LIMIT_DELAY = float(os.getenv("RSS_RATE_LIMIT_DELAY", "3.0"))
    SCRAPE_RATE_LIMIT_DELAY = float(os.getenv("SCRAPE_RATE_LIMIT_DELAY", "5.0"))
    
    # Cache settings (longer caching to reduce API calls)
    HTML_CACHE_HOURS = int(os.getenv("HTML_CACHE_HOURS", "168"))  # 1 week
    RANK_CACHE_DAYS = int(os.getenv("RANK_CACHE_DAYS", "30"))
    
    # Request settings
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
    
    # User agents (rotate to avoid blocking)
    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
    ]
    
    # Collection limits (be conservative)
    MAX_CATEGORIES_PER_RUN = int(os.getenv("MAX_CATEGORIES_PER_RUN", "3"))
    MAX_COUNTRIES_PER_RUN = int(os.getenv("MAX_COUNTRIES_PER_RUN", "2"))
    
    @classmethod
    def get_conservative_config(cls) -> Dict[str, Any]:
        """Get conservative configuration for production use."""
        return {
            "rss_rate_limit": cls.RSS_RATE_LIMIT_DELAY,
            "scrape_rate_limit": cls.SCRAPE_RATE_LIMIT_DELAY,
            "html_cache_hours": cls.HTML_CACHE_HOURS,
            "max_retries": cls.MAX_RETRIES,
            "request_timeout": cls.REQUEST_TIMEOUT,
            "max_categories": cls.MAX_CATEGORIES_PER_RUN,
            "max_countries": cls.MAX_COUNTRIES_PER_RUN
        }
    
    @classmethod
    def get_user_agent(cls, index: int = 0) -> str:
        """Get a user agent string, rotating through available options."""
        return cls.USER_AGENTS[index % len(cls.USER_AGENTS)]


class DevelopmentConfig:
    """Development configuration with faster rates for testing."""
    
    RSS_RATE_LIMIT_DELAY = 0.5
    SCRAPE_RATE_LIMIT_DELAY = 1.0
    HTML_CACHE_HOURS = 1
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 15
    

# Default to production config
Config = ProductionConfig