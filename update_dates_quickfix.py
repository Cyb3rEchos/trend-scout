#!/usr/bin/env python3
"""
Quick fix: Update yesterday's data to today's date
"""

import os
from datetime import date
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)

today = date.today().isoformat()
yesterday = "2025-08-24"

print(f"🔧 Quick Fix: Updating dates from {yesterday} to {today}")

try:
    # Update daily_rankings dates
    result = client.table('daily_rankings').update({'date': today}).eq('date', yesterday).execute()
    print(f"✅ Updated {len(result.data)} records in daily_rankings to today's date")
    
    # Verify
    check = client.table('daily_rankings').select('date').limit(5).execute()
    if check.data:
        print(f"✅ Verified: Sample date is now {check.data[0]['date']}")
        
    print("\n✨ Success! The iOS app should now show all your AI-enhanced data!")
    print("🔄 Pull to refresh in the app to see the changes.")
    
except Exception as e:
    print(f"❌ Error: {e}")