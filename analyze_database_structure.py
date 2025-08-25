#!/usr/bin/env python3
"""
Analyze all Supabase tables and views structure
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

print("🔍 Analyzing Supabase database structure...")
print(f"URL: {url}")
print("=" * 60)

def analyze_table_structure(table_name, description=""):
    """Analyze a table/view structure"""
    try:
        print(f"\n📊 {table_name.upper()}")
        if description:
            print(f"Description: {description}")
        print("-" * 40)
        
        # Get sample data
        response = supabase.table(table_name).select("*").limit(3).execute()
        
        if response.data:
            print(f"✅ Found {len(response.data)} records")
            
            # Show first record structure
            first_record = response.data[0]
            print("\n🔑 Available fields:")
            for key, value in first_record.items():
                value_type = type(value).__name__
                sample_value = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                print(f"  - {key}: {value_type} = {sample_value}")
            
            # Show total count
            try:
                count_response = supabase.table(table_name).select("id", count="exact").execute()
                total_count = count_response.count if hasattr(count_response, 'count') else len(count_response.data)
                print(f"\n📈 Total records: {total_count}")
            except:
                print(f"\n📈 Total records: {len(response.data)} (sample)")
                
        else:
            print("⚠️ No data found")
            
    except Exception as e:
        print(f"❌ Failed to analyze {table_name}: {e}")

# Analyze known tables and views from IOS_BUILD_CONTEXT
tables_to_analyze = [
    ("scout_results", "Main data table with app rankings and scores"),
    ("daily_rankings", "Daily rankings with AI recommendations"),
    ("todays_opportunities", "Top 10 per category daily (VIEW)"),
    ("category_leaders", "Top 3 per category with AI recommendations (VIEW)"), 
    ("micro_opportunities", "Clone candidates from scout_results (VIEW)"),
    ("trending_analysis", "Compare today vs yesterday (VIEW)")
]

for table_name, description in tables_to_analyze:
    analyze_table_structure(table_name, description)

# Check what other tables exist
print(f"\n" + "=" * 60)
print("🗂️ CHECKING FOR OTHER TABLES...")
print("=" * 60)

try:
    # This is a PostgreSQL query to get all tables
    # Note: This might not work with all Supabase configurations
    print("Attempting to list all available tables...")
    
    # Try to query information_schema if available
    tables_query = """
    SELECT table_name, table_type 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name
    """
    
    print("Note: Direct table listing may not be available via Supabase client")
    
except Exception as e:
    print(f"Could not list tables directly: {e}")

print(f"\n" + "=" * 60)
print("✨ ANALYSIS COMPLETE!")
print("=" * 60)