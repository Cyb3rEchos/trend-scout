#!/usr/bin/env python3
"""
Test script to verify Supabase connection and data structure
"""

import os
import json
from supabase import create_client, Client

# Load environment variables
from pathlib import Path
env_path = Path('.env')
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# Get Supabase credentials
url = os.environ.get('SUPABASE_URL')
service_key = os.environ.get('SUPABASE_SERVICE_KEY')

if not url or not service_key:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
    exit(1)

# Create Supabase client
supabase: Client = create_client(url, service_key)

print("🔍 Testing Supabase connection...")
print(f"URL: {url}")
print("-" * 50)

try:
    # Test query - get 5 records
    response = supabase.table('scout_results').select("*").limit(5).execute()
    
    if response.data:
        print(f"✅ Successfully connected! Found {len(response.data)} records")
        print("\n📊 Sample data structure:")
        
        # Show first record structure
        if response.data:
            first_record = response.data[0]
            print(json.dumps(first_record, indent=2, default=str))
            
            # Show available fields
            print("\n🔑 Available fields:")
            for key in first_record.keys():
                print(f"  - {key}: {type(first_record[key]).__name__}")
    else:
        print("⚠️ Connected but no data found in scout_results table")
        
    # Test category query
    print("\n📂 Testing category query...")
    categories_response = supabase.table('scout_results').select("category").execute()
    if categories_response.data:
        unique_categories = set(item['category'] for item in categories_response.data)
        print(f"Found {len(unique_categories)} categories:")
        for cat in sorted(unique_categories):
            print(f"  - {cat}")
            
except Exception as e:
    print(f"❌ Connection failed: {e}")
    
print("\n✨ Test complete!")