#!/usr/bin/env python3
"""Get available categories from Supabase."""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def get_categories():
    """Get all available categories from the database."""
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        print("❌ Missing environment variables")
        return
    
    try:
        client = create_client(url, key)
        
        # Get all records to analyze categories
        result = client.table("scout_results").select("category, country, chart, rank, name, bundle_id, total").order("total", desc=True).execute()
        
        categories = {}
        for record in result.data:
            cat = record.get('category', 'Unknown')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                'name': record.get('name', '').replace('â', '').replace(' on the AppÂ Store', ''),
                'bundle_id': record.get('bundle_id', ''),
                'rank': record.get('rank', 0),
                'total': record.get('total', 0),
                'country': record.get('country', ''),
                'chart': record.get('chart', '')
            })
        
        print(f"📊 Found {len(result.data)} total records across {len(categories)} categories\n")
        
        for category, apps in categories.items():
            print(f"📂 {category} ({len(apps)} apps)")
            # Show top 3 apps in each category
            for app in sorted(apps, key=lambda x: x['total'], reverse=True)[:3]:
                print(f"  #{app['rank']} {app['name']} - Score: {app['total']} ({app['chart']})")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_categories()