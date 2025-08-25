#!/usr/bin/env python3
"""
Debug script to test HTML scraping and identify decompression issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from trendscout.scrape import AppScraper

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

def main():
    print("🔍 SCRAPER DEBUG TEST")
    print("=" * 50)
    
    scraper = AppScraper(rate_limit_delay=1.0)  # Faster for testing
    
    # Test with Google app (known working app_id)
    test_app_id = "284815942"  # Google
    test_country = "us"
    
    print(f"Testing app_id: {test_app_id}")
    print(f"Country: {test_country}")
    
    try:
        # Step 1: Test HTML fetching
        print("\n📥 Fetching HTML...")
        html = scraper.fetch_app_page(test_app_id, test_country)
        
        print(f"✅ HTML fetched successfully")
        print(f"   Length: {len(html)} characters")
        print(f"   Type: {type(html)}")
        
        # Check if HTML looks valid
        if html.startswith('<!DOCTYPE html') or html.startswith('<html'):
            print("✅ HTML appears to be valid")
        else:
            print("⚠️  HTML doesn't start with DOCTYPE or <html>")
            print(f"   First 200 chars: {repr(html[:200])}")
        
        # Step 2: Test HTML parsing
        print("\n🔍 Parsing HTML...")
        app_data = scraper.parse_app_page(html, test_app_id)
        
        print("✅ HTML parsed successfully")
        print(f"   Bundle ID: {app_data.bundle_id}")
        print(f"   Price: ${app_data.price}")
        print(f"   Has IAP: {app_data.has_iap}")
        print(f"   Rating Count: {app_data.rating_count}")
        print(f"   Rating Avg: {app_data.rating_avg}")
        print(f"   Description Length: {app_data.desc_len}")
        print(f"   Recent Reviews: {len(app_data.recent_reviews) if app_data.recent_reviews else 0}")
        
        # Step 3: Check for specific patterns in HTML
        print("\n🔍 HTML Content Analysis...")
        patterns_to_check = {
            "bundleId": "bundleId" in html,
            "com.google": "com.google" in html, 
            "price": "price" in html.lower(),
            "rating": "rating" in html.lower(),
            "description": "description" in html.lower(),
            "script_tags": "<script" in html,
            "json_data": "{" in html and "}" in html
        }
        
        for pattern, found in patterns_to_check.items():
            status = "✅" if found else "❌"
            print(f"   {status} {pattern}: {found}")
        
        # Step 4: Try to find bundle ID manually
        if "bundleId" in html:
            print("\n🔍 Manual Bundle ID Search...")
            import re
            
            # Try different patterns
            patterns = [
                r'"bundleId"\s*:\s*"([^"]+)"',
                r'bundleId["\s]*:\s*["\s]*([^"]+)["\s]*',
                r'com\.[a-zA-Z0-9.]+\.google'
            ]
            
            for i, pattern in enumerate(patterns):
                matches = re.findall(pattern, html, re.IGNORECASE)
                print(f"   Pattern {i+1}: {len(matches)} matches")
                if matches:
                    print(f"      First match: {matches[0]}")
        
        # Check if this looks like fallback data
        if app_data.bundle_id.startswith("com.unknown.app"):
            print("\n⚠️  USING FALLBACK BUNDLE ID - This indicates scraping issue")
        else:
            print("\n✅ Real bundle ID extracted successfully")
            
    except Exception as e:
        print(f"\n❌ Error during scraping test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()