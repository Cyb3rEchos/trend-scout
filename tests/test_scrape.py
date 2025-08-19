"""Tests for app page scraping."""

import pytest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

from trendscout.scrape import AppScraper
from trendscout.models import AppPageData


class TestAppScraper:
    """Test AppScraper class."""
    
    def test_init(self):
        """Test scraper initialization."""
        scraper = AppScraper(user_agent="Test/1.0", rate_limit_delay=0.1)
        
        assert scraper.user_agent == "Test/1.0"
        assert scraper.rate_limit_delay == 0.1
        assert "Test/1.0" in scraper.session.headers["User-Agent"]
    
    def test_build_app_url(self):
        """Test building App Store URLs."""
        scraper = AppScraper()
        
        # Default country
        url = scraper.build_app_url("123456789")
        assert url == "https://apps.apple.com/us/app/id123456789"
        
        # Specific country
        url = scraper.build_app_url("987654321", "ca")
        assert url == "https://apps.apple.com/ca/app/id987654321"
    
    def test_parse_price_text(self):
        """Test price text parsing."""
        scraper = AppScraper()
        
        # Free indicators
        assert scraper._parse_price_text("Free") == 0.0
        assert scraper._parse_price_text("Get") == 0.0
        assert scraper._parse_price_text("Open") == 0.0
        
        # Paid prices
        assert scraper._parse_price_text("$2.99") == 2.99
        assert scraper._parse_price_text("$19.99") == 19.99
        assert scraper._parse_price_text("€4.99") == 4.99
        
        # Edge cases
        assert scraper._parse_price_text("") == 0.0
        assert scraper._parse_price_text("Invalid") == 0.0
    
    def test_extract_bundle_id(self):
        """Test bundle ID extraction from HTML."""
        scraper = AppScraper()
        
        # Test with JSON data in HTML
        html = '''
        <html>
        <script>
        var data = {"bundleId": "com.example.testapp", "adamId": "123456789"};
        </script>
        </html>
        '''
        soup = BeautifulSoup(html, 'lxml')
        bundle_id = scraper._extract_bundle_id(soup)
        assert bundle_id == "com.example.testapp"
    
    def test_extract_bundle_id_meta_tag_fallback(self):
        """Test bundle ID extraction from meta tag fallback."""
        scraper = AppScraper()
        
        html = '''
        <html>
        <head>
        <meta name="apple-itunes-app" content="app-id=123456789">
        </head>
        </html>
        '''
        soup = BeautifulSoup(html, 'lxml')
        bundle_id = scraper._extract_bundle_id(soup)
        assert bundle_id == "app.123456789"  # Fallback format
    
    def test_extract_bundle_id_not_found(self):
        """Test bundle ID extraction when not found."""
        scraper = AppScraper()
        
        html = '<html><body>No bundle ID here</body></html>'
        soup = BeautifulSoup(html, 'lxml')
        
        with pytest.raises(ValueError, match="Could not extract bundle ID"):
            scraper._extract_bundle_id(soup)
    
    def test_extract_has_iap_true(self):
        """Test IAP detection when present."""
        scraper = AppScraper()
        
        html = '''
        <html>
        <body>
        <div>This app offers In-App Purchases</div>
        </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'lxml')
        has_iap = scraper._extract_has_iap(soup)
        assert has_iap is True
    
    def test_extract_has_iap_false(self):
        """Test IAP detection when not present.""" 
        scraper = AppScraper()
        
        html = '<html><body>No IAP mentioned</body></html>'
        soup = BeautifulSoup(html, 'lxml')
        has_iap = scraper._extract_has_iap(soup)
        assert has_iap is False
    
    def test_extract_rating_count(self):
        """Test rating count extraction."""
        scraper = AppScraper()
        
        # Test with thousands notation
        html = '''
        <html>
        <body>
        <span>1.2k ratings</span>
        </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'lxml')
        count = scraper._extract_rating_count(soup)
        assert count == 1200
        
        # Test with regular number
        html = '''
        <html>
        <body>
        <span>1,234 ratings</span>
        </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'lxml')
        count = scraper._extract_rating_count(soup)
        assert count == 1234
    
    def test_extract_rating_avg(self):
        """Test rating average extraction."""
        scraper = AppScraper()
        
        # Test with JSON-LD data
        html = '''
        <html>
        <body>
        <div aria-label="4.5 out of 5 stars">Rating</div>
        </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'lxml')
        avg = scraper._extract_rating_avg(soup)
        assert avg == 4.5
    
    def test_extract_description_length(self):
        """Test description length extraction."""
        scraper = AppScraper()
        
        html = '''
        <html>
        <body>
        <div data-test-bcc="description">
        This is a test app description that should be counted for length.
        It has multiple sentences and should return the correct character count.
        </div>
        </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'lxml')
        desc_len = scraper._extract_description_length(soup)
        assert desc_len > 100  # Should count the text
    
    def test_extract_recent_reviews(self):
        """Test recent reviews extraction."""
        scraper = AppScraper()
        
        html = '''
        <html>
        <body>
        <div class="we-customer-review__body">Great app, very useful!</div>
        <div class="we-customer-review__body">Love the features and design.</div>
        <div class="we-customer-review__body">Could use some improvements but overall good.</div>
        </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'lxml')
        reviews = scraper._extract_recent_reviews(soup, limit=2)
        
        assert len(reviews) == 2
        assert "Great app" in reviews[0]
        assert "Love the features" in reviews[1]
    
    def test_parse_app_page_complete(self):
        """Test complete app page parsing."""
        scraper = AppScraper()
        
        # Create comprehensive HTML with all required data
        html = '''
        <html>
        <head>
        <script>
        var appData = {
            "bundleId": "com.example.calculator",
            "ratingValue": 4.3
        };
        </script>
        </head>
        <body>
        <div data-test-bcc="price">Free</div>
        <div>Offers In-App Purchases</div>
        <div>1,500 ratings</div>
        <div data-test-bcc="description">
        A powerful calculator app with advanced features for professionals and students.
        Includes scientific functions, graphing capabilities, and unit conversions.
        </div>
        <div class="we-customer-review__body">Excellent calculator app!</div>
        <div class="we-customer-review__body">Very helpful for my math classes.</div>
        </body>
        </html>
        '''
        
        app_data = scraper.parse_app_page(html, "123456789")
        
        assert isinstance(app_data, AppPageData)
        assert app_data.bundle_id == "com.example.calculator"
        assert app_data.price == 0.0  # Free
        assert app_data.has_iap is True
        assert app_data.rating_count == 1500
        assert app_data.rating_avg == 4.3
        assert app_data.desc_len > 100
        assert len(app_data.recent_reviews) == 2
    
    @patch('trendscout.scrape.time.sleep')
    def test_scrape_app_success(self, mock_sleep):
        """Test successful app scraping."""
        scraper = AppScraper()
        
        mock_html = '''
        <html>
        <script>{"bundleId": "com.test.app"}</script>
        <body>
        <div data-test-bcc="price">$1.99</div>
        <div>No In-App Purchases</div>
        <div>100 ratings</div> 
        <div aria-label="4.0 out of 5">Rating</div>
        <div data-test-bcc="description">Simple test app</div>
        </body>
        </html>
        '''
        
        with patch.object(scraper, 'fetch_app_page', return_value=mock_html):
            app_data = scraper.scrape_app("123456789", "us")
        
        assert app_data.bundle_id == "com.test.app"
        assert app_data.price == 1.99
        assert app_data.has_iap is False
        assert app_data.rating_count == 100
        assert app_data.rating_avg == 4.0
        
        # Verify rate limiting was applied
        mock_sleep.assert_called_once()