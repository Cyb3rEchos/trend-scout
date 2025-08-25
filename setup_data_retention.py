#!/usr/bin/env python3
"""Setup data retention rules and cleanup schedule for Trend Scout."""

import logging
from datetime import datetime
from trendscout.local_storage import LocalDataStorage
from trendscout.store import DataStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_data_retention():
    """Setup data retention rules for local and Supabase storage."""
    
    logger.info("🧹 Setting up data retention rules...")
    
    # Initialize storage systems
    local_storage = LocalDataStorage()
    data_store = DataStore()
    
    # Clean up local storage (6 months)
    logger.info("📁 Cleaning up local storage...")
    removed_local = local_storage.cleanup_old_runs(keep_months=6)
    logger.info(f"📁 Removed {removed_local} old local runs")
    
    # Clean up Supabase data (6 months)
    logger.info("☁️ Cleaning up Supabase data...")
    
    try:
        # Clean old scout_results (keep last 6 months)
        cutoff_date = datetime.now().date()
        cutoff_timestamp = datetime.now().replace(
            month=max(1, cutoff_date.month - 6), 
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        
        # Delete old scout_results
        scout_result = data_store.publisher.client.table('scout_results').delete().lt(
            'generated_at', cutoff_timestamp.isoformat()
        ).execute()
        
        scout_deleted = len(scout_result.data) if scout_result.data else 0
        logger.info(f"☁️ Removed {scout_deleted} old scout_results records")
        
        # Delete old daily_rankings
        rankings_result = data_store.publisher.client.table('daily_rankings').delete().lt(
            'date', cutoff_timestamp.date().isoformat()
        ).execute()
        
        rankings_deleted = len(rankings_result.data) if rankings_result.data else 0
        logger.info(f"☁️ Removed {rankings_deleted} old daily_rankings records")
        
    except Exception as e:
        logger.error(f"❌ Failed to clean Supabase data: {e}")
    
    # Show storage summary
    storage_summary = local_storage.get_storage_summary()
    logger.info("📊 STORAGE SUMMARY:")
    logger.info(f"  Local runs: {storage_summary['total_runs']}")
    logger.info(f"  Latest: {storage_summary['latest_run']}")
    logger.info(f"  Storage size: {storage_summary['total_size_mb']} MB")
    logger.info(f"  Path: {storage_summary['storage_path']}")
    
    # Show database summary
    try:
        scout_count = data_store.publisher.client.table('scout_results').select('id', count='exact').execute()
        rankings_count = data_store.publisher.client.table('daily_rankings').select('id', count='exact').execute()
        
        logger.info("☁️ SUPABASE SUMMARY:")
        logger.info(f"  Scout results: {scout_count.count} records")
        logger.info(f"  Daily rankings: {rankings_count.count} records")
        
    except Exception as e:
        logger.warning(f"⚠️ Could not get Supabase summary: {e}")
    
    logger.info("✅ Data retention setup complete")
    return True

if __name__ == "__main__":
    success = setup_data_retention()
    if success:
        print("\n🎉 Data retention rules configured successfully!")
        print("📋 Run this script monthly to maintain clean storage")
    else:
        print("\n❌ Data retention setup failed")