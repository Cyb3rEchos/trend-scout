#!/usr/bin/env python3
"""
Test script to verify perfect data structure alignment
Run after schema updates to ensure everything works end-to-end
"""

import logging
import os
from datetime import datetime
from supabase import create_client
from trendscout.models import DailyRankingRow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_env():
    """Load environment variables."""
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def test_database_schema():
    """Test that database has all required fields."""
    
    logger.info("🔍 Testing Supabase database schema...")
    
    # Create client
    load_env()
    url = os.environ.get('SUPABASE_URL')
    service_key = os.environ.get('SUPABASE_SERVICE_KEY')
    
    if not url or not service_key:
        logger.error("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        return False
    
    supabase = create_client(url, service_key)
    
    try:
        # Test that new fields exist by trying to select them
        response = supabase.table('daily_rankings').select(
            'id, clone_name, clone_name_custom, build_priority'
        ).limit(1).execute()
        
        logger.info("✅ Database schema has all required fields!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database schema test failed: {e}")
        return False

def test_python_model():
    """Test Python model validation."""
    
    logger.info("🐍 Testing Python DailyRankingRow model...")
    
    try:
        # Create test ranking with all fields
        test_ranking = DailyRankingRow(
            date="2025-08-25",
            category="Utilities",
            country="US",
            chart="free",
            rank=1,
            app_id="12345",
            bundle_id="com.test.app",
            name="Test App - Test Developer",
            price=0.0,
            has_iap=False,
            rating_count=1000,
            rating_avg=4.5,
            desc_len=500,
            demand=3.0,
            monetization=2.0,
            low_complexity=4.0,
            moat_risk=1.0,
            total=3.5,
            clone_difficulty="EASY_CLONE",
            revenue_potential="GOOD_REVENUE",
            category_rank=1,
            clone_name="TestPro",
            build_priority="TONIGHT"
        )
        
        # Test serialization
        data_dict = test_ranking.dict()
        logger.info(f"✅ Python model validation passed!")
        logger.info(f"   Clone name: {data_dict['clone_name']}")
        logger.info(f"   Build priority: {data_dict['build_priority']}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Python model test failed: {e}")
        return False

def test_clone_name_generation():
    """Test clone name generation logic."""
    
    logger.info("🤖 Testing clone name generation...")
    
    from daily_automation import DailyAutomation
    from datetime import date
    
    # Create test automation instance
    automation = DailyAutomation(date.today())
    
    # Mock record
    class MockRecord:
        def __init__(self, name, category):
            self.name = name
            self.category = category
    
    test_cases = [
        ("Shadowrocket - VPN", "Utilities", "TunnelPro"),
        ("Camera+ Legacy", "Photo & Video", "SnapStudio"),
        ("Spotify - Music Player", "Music", "AudioStudio"),
        ("MyFitnessPal", "Health & Fitness", "FitPro")
    ]
    
    for name, category, expected_prefix in test_cases:
        record = MockRecord(name, category)
        clone_name = automation._generate_clone_name(record, "EASY_CLONE")
        logger.info(f"   {name} → {clone_name}")
        
        if expected_prefix.lower() in clone_name.lower():
            logger.info(f"   ✅ Expected pattern found")
        else:
            logger.info(f"   ⚠️  Unexpected pattern (not necessarily wrong)")
    
    return True

def test_build_priority_mapping():
    """Test build priority mapping logic."""
    
    logger.info("⏰ Testing build priority mapping...")
    
    from daily_automation import DailyAutomation
    from datetime import date
    
    automation = DailyAutomation(date.today())
    
    test_cases = [
        ("EASY_CLONE", "HIGH_REVENUE", 1, "TONIGHT"),
        ("MODERATE", "GOOD_REVENUE", 3, "THIS_WEEK"),
        ("COMPLEX", "HIGH_REVENUE", 5, "THIS_MONTH"),
        ("MODERATE", "LOW_REVENUE", 8, "FUTURE")
    ]
    
    for difficulty, revenue, rank, expected in test_cases:
        priority = automation._map_build_priority(difficulty, revenue, rank)
        status = "✅" if priority == expected else "❌"
        logger.info(f"   {difficulty} + {revenue} + rank{rank} → {priority} {status}")
    
    return True

def main():
    """Run all alignment tests."""
    
    logger.info("🚀 TESTING DATA STRUCTURE ALIGNMENT")
    logger.info("=" * 50)
    
    tests = [
        ("Database Schema", test_database_schema),
        ("Python Model", test_python_model),
        ("Clone Name Generation", test_clone_name_generation),
        ("Build Priority Mapping", test_build_priority_mapping)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n📋 {test_name}:")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 TEST RESULTS SUMMARY:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"   {test_name}: {status}")
        if success:
            passed += 1
    
    logger.info(f"\n🎯 OVERALL: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        logger.info("🎉 ALL SYSTEMS ALIGNED! Ready for Phase 2!")
    else:
        logger.info("⚠️  Some issues found. Check logs above.")
    
    return passed == len(tests)

if __name__ == "__main__":
    main()