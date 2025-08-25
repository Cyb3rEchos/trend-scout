#!/usr/bin/env python3
"""
Check and fix database issues for Trend Scout
"""

import os
from datetime import datetime, date
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)

print("=" * 60)
print("🔍 TREND SCOUT DATABASE DIAGNOSTIC")
print("=" * 60)

# 1. Check daily_rankings table
print("\n📊 Checking daily_rankings table...")
try:
    result = client.table('daily_rankings').select('*').limit(5).execute()
    print(f"✅ Daily rankings count: {len(result.data)}")
    
    if result.data:
        sample = result.data[0]
        print(f"📅 Sample date: {sample.get('date')}")
        print(f"📱 Sample app: {sample.get('name')}")
        print(f"🏷️ Sample category: {sample.get('category')}")
        print(f"🤖 Has clone_name: {'clone_name' in sample and sample['clone_name'] is not None}")
        print(f"🎯 Has build_priority: {'build_priority' in sample and sample['build_priority'] is not None}")
        
        # Check if data is from today
        today = date.today().isoformat()
        print(f"\n📅 Today's date: {today}")
        print(f"📅 Data date: {sample.get('date')}")
        
        if sample.get('date') != today:
            print(f"⚠️ WARNING: Data is from {sample.get('date')}, not today ({today})")
            print("This is why the app shows empty results!")
    else:
        print("❌ No data in daily_rankings table!")
except Exception as e:
    print(f"❌ Error checking daily_rankings: {e}")

# 2. Check scout_results table (backup)
print("\n📊 Checking scout_results table (backup)...")
try:
    result = client.table('scout_results').select('*').limit(5).execute()
    print(f"✅ Scout results count: {len(result.data)}")
    
    if result.data:
        sample = result.data[0]
        print(f"📅 Sample date: {sample.get('generated_at', 'N/A')[:10] if sample.get('generated_at') else 'N/A'}")
        print(f"📱 Sample app: {sample.get('name')}")
except Exception as e:
    print(f"❌ Error checking scout_results: {e}")

# 3. Check if views exist
print("\n🔍 Checking database views...")
views_to_check = ['todays_opportunities', 'tonight_opportunities', 'category_leaders']

for view_name in views_to_check:
    try:
        result = client.table(view_name).select('*').limit(1).execute()
        print(f"✅ View '{view_name}' exists")
    except Exception as e:
        if "relation" in str(e).lower() and "does not exist" in str(e).lower():
            print(f"❌ View '{view_name}' does NOT exist - needs to be created")
        else:
            print(f"⚠️ View '{view_name}' error: {e}")

# 4. Get unique dates in daily_rankings
print("\n📅 Checking dates in daily_rankings...")
try:
    result = client.table('daily_rankings').select('date').execute()
    if result.data:
        dates = list(set(row['date'] for row in result.data if row.get('date')))
        dates.sort(reverse=True)
        print(f"Found {len(dates)} unique dates:")
        for d in dates[:5]:  # Show latest 5 dates
            print(f"  - {d}")
    else:
        print("No dates found")
except Exception as e:
    print(f"❌ Error checking dates: {e}")

# 5. Count apps with AI data
print("\n🤖 Checking AI-enhanced data...")
try:
    # Count apps with clone names
    result = client.table('daily_rankings').select('clone_name').not_.is_('clone_name', 'null').execute()
    clone_name_count = len(result.data)
    
    # Count apps with build priority
    result = client.table('daily_rankings').select('build_priority').not_.is_('build_priority', 'null').execute()
    priority_count = len(result.data)
    
    print(f"✅ Apps with clone_name: {clone_name_count}")
    print(f"✅ Apps with build_priority: {priority_count}")
    
    if clone_name_count == 0:
        print("⚠️ No AI clone names found - automation may not have completed")
    
except Exception as e:
    print(f"❌ Error checking AI data: {e}")

print("\n" + "=" * 60)
print("📋 DIAGNOSIS SUMMARY")
print("=" * 60)

# Provide actionable recommendations
print("\n🔧 RECOMMENDED ACTIONS:")
print("\n1. If data date doesn't match today, the app won't show any data")
print("   Solution: Re-run daily_automation.py to generate today's data")
print("\n2. If views don't exist, create them using schema_alignment_update.sql")
print("   Solution: Run the SQL in Supabase dashboard")
print("\n3. If no AI data (clone_name, build_priority), re-run automation")
print("   Solution: python daily_automation.py")

print("\n💡 Quick fix command:")
print("   python daily_automation.py")
print("\nThis will generate fresh data for today with all AI enhancements.")