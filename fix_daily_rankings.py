#!/usr/bin/env python3
"""Fix daily rankings by reprocessing existing scout_results data."""

import logging
from datetime import date
from daily_automation import DailyAutomation

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Reprocess existing scout_results to create daily_rankings."""
    
    logger.info("🔧 Starting daily rankings fix...")
    
    # Create automation instance
    automation = DailyAutomation()
    
    # Get all existing data from scout_results
    logger.info("📊 Fetching existing scout_results data...")
    results = automation.store.publisher.client.table('scout_results').select('*').execute()
    
    logger.info(f"Found {len(results.data)} existing records")
    
    # Convert to mock scored records for processing
    scored_records = []
    for record in results.data:
        # Create a mock scored record object
        class MockRecord:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)
        
        scored_records.append(MockRecord(record))
    
    # Create daily rankings
    logger.info("📈 Creating daily rankings...")
    daily_rankings = automation._create_daily_rankings(scored_records)
    
    logger.info(f"Created {len(daily_rankings)} daily rankings across categories")
    
    # Store daily rankings
    logger.info("💾 Storing daily rankings...")
    success = automation._store_daily_rankings(daily_rankings)
    
    if success:
        logger.info("✅ Daily rankings successfully stored!")
        
        # Verify storage
        count_result = automation.store.publisher.client.table('daily_rankings').select('*', count='exact').execute()
        logger.info(f"📊 Total daily rankings in database: {count_result.count}")
        
        # Show sample by category
        categories = {}
        for ranking in daily_rankings:
            cat = ranking['category']
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1
        
        logger.info("📋 Rankings by category:")
        for category, count in sorted(categories.items()):
            logger.info(f"  {category}: {count} rankings")
            
    else:
        logger.error("❌ Failed to store daily rankings")
        return False
    
    logger.info("🎉 Daily rankings fix completed successfully!")
    return True

if __name__ == "__main__":
    main()