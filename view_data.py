#!/usr/bin/env python3
"""
Trend Scout Data Viewer
Simple script to view collected App Store data
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import json

def main():
    print("📱 TREND SCOUT DATA VIEWER")
    print("=" * 50)
    
    cache_path = Path.home() / '.trendscout' / 'cache.db'
    
    if not cache_path.exists():
        print("❌ No data found. Run collection first:")
        print("   python production_collect.py --test")
        return
    
    with sqlite3.connect(cache_path) as conn:
        conn.row_factory = sqlite3.Row
        
        # Get summary
        cursor = conn.execute("SELECT COUNT(*) as count FROM app_ranks")
        total_ranks = cursor.fetchone()['count']
        
        cursor = conn.execute("SELECT COUNT(*) as count FROM app_html_cache")
        total_html = cursor.fetchone()['count']
        
        print(f"📊 Data Summary:")
        print(f"   • App rankings: {total_ranks}")
        print(f"   • Cached pages: {total_html}")
        print(f"   • Database: {cache_path}")
        print()
        
        # Get latest rankings
        cursor = conn.execute('''
            SELECT app_id, category, country, chart, rank, date 
            FROM app_ranks 
            WHERE date = (SELECT MAX(date) FROM app_ranks)
            ORDER BY rank ASC
        ''')
        
        rankings = cursor.fetchall()
        if rankings:
            latest = rankings[0]
            print(f"🏆 Latest Rankings ({latest['date']}):")
            print(f"   📂 {latest['category']} | 🌍 {latest['country']} | 📈 {latest['chart']}")
            print("-" * 40)
            
            # App names
            app_names = {
                '284815942': 'Google',
                '535886823': 'Google Chrome', 
                '388497605': 'Google Authenticator',
                '1288723196': 'Microsoft Edge',
                '1510944943': 'Cleanup Storage Cleaner',
                '1178765645': 'Xfinity',
                '1476380919': 'Cleaner Guru',
                '416023011': 'My Verizon',
                '6448330325': 'AI Cleaner',
                '942608209': 'My Spectrum'
            }
            
            for row in rankings:
                app_name = app_names.get(row['app_id'], f"App {row['app_id']}")
                print(f"{row['rank']:2d}. {app_name}")
                print(f"    📱 {row['app_id']}")
        
        print()
        print("🔧 Available Commands:")
        print("   python view_data.py           - View this summary")
        print("   python production_collect.py --test  - Collect new data")
        print("   sqlite3 ~/.trendscout/cache.db       - Direct database access")

if __name__ == "__main__":
    main()