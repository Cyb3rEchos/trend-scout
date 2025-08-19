"""RSS feed fetching and parsing for Apple App Store charts."""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import quote

import feedparser
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from .models import CollectConfig, RawAppRecord

logger = logging.getLogger(__name__)


class RSSFetcher:
    """Fetches and parses Apple App Store RSS feeds."""
    
    # iTunes RSS endpoint templates (supports category filtering)
    # Format: https://itunes.apple.com/{country}/rss/top{chart}applications/limit={limit}/genre={genre_id}/xml
    RSS_TEMPLATES = {
        "free": "https://itunes.apple.com/{country}/rss/topfreeapplications/limit={limit}/genre={genre_id}/xml",
        "paid": "https://itunes.apple.com/{country}/rss/toppaidapplications/limit={limit}/genre={genre_id}/xml"
    }
    
    # Category mappings to iTunes genre IDs
    CATEGORY_MAPPINGS = {
        "All": None,  # No genre filter for all categories
        "Utilities": "6002",
        "Photo & Video": "6008", 
        "Productivity": "6007",
        "Health & Fitness": "6013",
        "Lifestyle": "6012",
        "Graphics & Design": "6027",
        "Music": "6011",
        "Education": "6017",
        "Finance": "6015",
        "Entertainment": "6016"
    }
    
    def __init__(self, user_agent: str = None, rate_limit_delay: float = 2.0):
        """Initialize RSS fetcher.
        
        Args:
            user_agent: User agent string for requests (defaults to legitimate browser)
            rate_limit_delay: Delay between requests in seconds (increased for Apple)
        """
        # Use a legitimate browser user agent to avoid blocking
        if user_agent is None:
            user_agent = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/120.0.0.0 Safari/537.36")
        
        self.user_agent = user_agent
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        
        # Set proper headers to mimic legitimate browser requests
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept": "application/xml, text/xml, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        })
    
    def build_rss_url(self, category: str, country: str, chart: str, top_n: int) -> str:
        """Build RSS feed URL for given parameters.
        
        Args:
            category: App Store category name
            country: Country code (US, CA, etc.)
            chart: Chart type (free or paid)
            top_n: Number of top apps to fetch
            
        Returns:
            RSS feed URL
            
        Raises:
            ValueError: If invalid parameters provided
        """
        if chart not in self.RSS_TEMPLATES:
            raise ValueError(f"Invalid chart type: {chart}. Must be 'free' or 'paid'")
        
        if category not in self.CATEGORY_MAPPINGS:
            raise ValueError(f"Invalid category: {category}. Must be one of {list(self.CATEGORY_MAPPINGS.keys())}")
        
        genre_id = self.CATEGORY_MAPPINGS[category]
        
        # Build URL based on whether we have a genre filter
        if genre_id is None:
            # For "All" category, use URL without genre parameter
            base_url = self.RSS_TEMPLATES[chart].replace("/genre={genre_id}", "")
            url = base_url.format(
                country=country.lower(),
                limit=top_n
            )
        else:
            url = self.RSS_TEMPLATES[chart].format(
                country=country.lower(),
                limit=top_n,
                genre_id=genre_id
            )
        
        logger.debug(f"Built RSS URL: {url}")
        return url
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=lambda retry_state: retry_state.outcome and 
              hasattr(retry_state.outcome.exception(), 'response') and
              retry_state.outcome.exception().response.status_code in [429, 503, 502, 504]
    )
    def fetch_rss_data(self, url: str) -> Dict:
        """Fetch and parse RSS data from URL with intelligent retries.
        
        Args:
            url: RSS feed URL to fetch
            
        Returns:
            Parsed RSS data as feedparser object converted to dict
            
        Raises:
            requests.RequestException: If request fails after retries
        """
        logger.info(f"Fetching RSS data from: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            
            # Handle rate limiting specifically
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After', '60')
                logger.warning(f"Rate limited. Waiting {retry_after} seconds")
                time.sleep(int(retry_after))
                raise requests.HTTPError(f"Rate limited (429)", response=response)
            
            # Handle other errors
            if response.status_code == 403:
                logger.error(f"Access forbidden (403) - possible rate limit or blocked user agent")
                raise requests.HTTPError(f"Access forbidden (403)", response=response)
            
            response.raise_for_status()
            
            # Parse XML RSS response using feedparser
            feed = feedparser.parse(response.text)
            
            if not feed.entries:
                raise ValueError(f"No entries found in RSS feed from {url}")
            
            entries_count = len(feed.entries)
            logger.info(f"Successfully fetched {entries_count} entries from RSS")
            
            # Convert feedparser object to dict for consistency
            return {
                "feed": {
                    "title": feed.feed.get("title", ""),
                    "entries": feed.entries
                }
            }
            
        except Exception as e:
            logger.error(f"Request failed for {url}: {e}")
            raise
    
    def parse_rss_entries(
        self,
        rss_data: Dict,
        category: str,
        country: str,
        chart: str,
        rss_url: str,
        max_results: int = 25
    ) -> List[RawAppRecord]:
        """Parse RSS data into RawAppRecord objects.
        
        Args:
            rss_data: Parsed RSS data dictionary from feedparser
            category: App Store category (already filtered by URL)
            country: Country code  
            chart: Chart type
            rss_url: Original RSS URL
            max_results: Maximum number of results to return
            
        Returns:
            List of RawAppRecord objects
        """
        records = []
        fetched_at = datetime.utcnow()
        
        feed = rss_data.get("feed", {})
        entries = feed.get("entries", [])
        
        for rank, entry in enumerate(entries[:max_results], 1):
            try:
                # Extract app ID from link
                app_url = entry.get("link", "")
                app_id = self._extract_app_id(app_url)
                
                if not app_id:
                    logger.warning(f"Could not extract app ID from URL: {app_url}")
                    continue
                
                # Convert feedparser entry to dict for raw_data
                raw_data = {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "published": entry.get("im_releasedate", {}).get("label", "") if entry.get("im_releasedate") else "",
                    "artist": entry.get("im_artist", {}).get("label", "") if entry.get("im_artist") else "",
                    "category": category,  # We already filtered by category in URL
                    "price": entry.get("im_price", {}).get("label", "") if entry.get("im_price") else "",
                    "content_type": entry.get("im_contenttype", {}).get("label", "") if entry.get("im_contenttype") else ""
                }
                
                record = RawAppRecord(
                    category=category,  # Use requested category from URL filter
                    country=country,
                    chart=chart,
                    rank=rank,
                    app_id=app_id,
                    name=entry.get("title", ""),
                    rss_url=rss_url,
                    fetched_at=fetched_at,
                    raw_data=raw_data
                )
                
                records.append(record)
                
            except Exception as e:
                logger.error(f"Error parsing RSS entry: {e}")
                continue
        
        logger.info(f"Parsed {len(records)} records from RSS feed for {category}")
        return records
    
    def _extract_app_id(self, app_url: str) -> Optional[str]:
        """Extract app ID from App Store URL.
        
        Args:
            app_url: App Store URL
            
        Returns:
            App ID string or None if not found
        """
        if not app_url:
            return None
        
        import re
        
        # Try different URL patterns
        patterns = [
            r'/id(\d+)',  # Standard: /id123456789
            r'app-id=(\d+)',  # iTunes format: app-id=123456789
            r'id(\d+)',  # Loose match: id123456789
        ]
        
        for pattern in patterns:
            match = re.search(pattern, app_url)
            if match:
                return match.group(1)
        
        return None
    
    def collect_category(
        self,
        category: str,
        country: str,
        chart: str,
        top_n: int
    ) -> List[RawAppRecord]:
        """Collect apps for a single category/country/chart combination.
        
        Args:
            category: App Store category
            country: Country code
            chart: Chart type (free or paid)
            top_n: Number of top apps to collect
            
        Returns:
            List of RawAppRecord objects
        """
        try:
            rss_url = self.build_rss_url(category, country, chart, top_n)
            rss_data = self.fetch_rss_data(rss_url)
            records = self.parse_rss_entries(rss_data, category, country, chart, rss_url, top_n)
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            return records
            
        except Exception as e:
            logger.error(f"Error collecting {category}/{country}/{chart}: {e}")
            return []
    
    def collect_all(self, config: CollectConfig) -> List[RawAppRecord]:
        """Collect apps for all configured categories, countries, and charts.
        
        Args:
            config: Collection configuration
            
        Returns:
            List of all collected RawAppRecord objects
        """
        all_records = []
        total_combinations = len(config.categories) * len(config.countries) * len(config.charts)
        current = 0
        
        logger.info(f"Starting collection for {total_combinations} combinations")
        
        for category in config.categories:
            for country in config.countries:
                for chart in config.charts:
                    current += 1
                    logger.info(
                        f"Collecting {category}/{country}/{chart} "
                        f"({current}/{total_combinations})"
                    )
                    
                    records = self.collect_category(category, country, chart, config.top_n)
                    all_records.extend(records)
                    
                    # Additional delay between different requests to be respectful
                    if current < total_combinations:
                        logger.debug(f"Waiting {self.rate_limit_delay} seconds before next combination")
                        time.sleep(self.rate_limit_delay)
        
        logger.info(f"Collection complete. Total records: {len(all_records)}")
        return all_records