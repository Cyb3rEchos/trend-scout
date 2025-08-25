#!/usr/bin/env python3
"""Check Supabase database structure and data."""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def check_database():
    """Check database structure and data."""
    
    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
        print("Please check your .env file")
        return
    
    try:
        # Create client
        client = create_client(url, key)
        print("✅ Connected to Supabase successfully")
        
        # Check if scout_results table exists and get schema info
        print("\n🔍 Checking scout_results table...")
        
        # Get table info
        result = client.table("scout_results").select("*").limit(1).execute()
        print(f"✅ scout_results table exists")
        
        # Get count of records
        count_result = client.table("scout_results").select("id", count="exact").execute()
        total_count = count_result.count if hasattr(count_result, 'count') else 0
        print(f"📊 Total records: {total_count}")
        
        if total_count > 0:
            # Get sample data
            sample_result = client.table("scout_results").select("*").limit(3).execute()
            
            print("\n📋 Sample records:")
            for i, record in enumerate(sample_result.data[:3], 1):
                print(f"\nRecord {i}:")
                print(f"  ID: {record.get('id')}")
                print(f"  Generated At: {record.get('generated_at')}")
                print(f"  Category: {record.get('category')}")
                print(f"  Country: {record.get('country')}")
                print(f"  Chart: {record.get('chart')}")
                print(f"  Rank: {record.get('rank')}")
                print(f"  App ID: {record.get('app_id')}")
                print(f"  Bundle ID: {record.get('bundle_id')}")
                print(f"  Name: {record.get('name')}")
                print(f"  Price: {record.get('price')}")
                print(f"  Has IAP: {record.get('has_iap')}")
                print(f"  Rating Count: {record.get('rating_count')}")
                print(f"  Rating Avg: {record.get('rating_avg')}")
                print(f"  Total Score: {record.get('total')}")
            
            # Check categories
            categories_result = client.table("scout_results").select("category", count="exact").group("category").execute()
            print(f"\n📂 Categories in database:")
            categories = {}
            for record in sample_result.data:
                cat = record.get('category')
                if cat:
                    categories[cat] = categories.get(cat, 0) + 1
            
            for category, count in categories.items():
                print(f"  {category}: {count} records")
                
            # Check latest batch timestamp
            latest_result = client.table("scout_results").select("generated_at").order("generated_at", desc=True).limit(1).execute()
            if latest_result.data:
                latest_time = latest_result.data[0]['generated_at']
                print(f"\n⏰ Latest batch: {latest_time}")
        
        else:
            print("⚠️  No data found in scout_results table")
            print("The Python automation script may still be running or hasn't completed yet")
        
        # Check if views exist
        print("\n🔍 Checking database views...")
        views_to_check = ["latest_results", "trending_apps", "high_potential_apps", "micro_opportunities"]
        
        for view_name in views_to_check:
            try:
                view_result = client.table(view_name).select("*").limit(1).execute()
                view_count = len(view_result.data) if view_result.data else 0
                print(f"✅ {view_name} view exists ({view_count} sample records)")
            except Exception as e:
                print(f"❌ {view_name} view: {e}")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    check_database()