#!/usr/bin/env python3
"""
Daily Automation System for Trend Scout

Complete daily workflow:
1. Collect top apps across all categories 
2. Rank top 10 per category
3. Generate AI recommendations for top 3 per category
4. Store everything in Supabase
5. Generate daily brief report

Run this daily to get fresh opportunities with AI-powered improvement suggestions.
"""

import argparse
import logging
import os
import time
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional

from trendscout.config import ProductionConfig
from trendscout.models import CollectConfig
from trendscout.rss import RSSFetcher
from trendscout.scrape import AppScraper
from trendscout.score import AppScorer
from trendscout.store import DataStore
from trendscout.ai_recommender import AIRecommender
from trendscout.local_storage import LocalDataStorage, save_automation_run


def setup_logging():
    """Set up comprehensive logging for daily automation."""
    log_dir = Path.home() / "Library" / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create daily log file
    log_file = log_dir / f"trendscout-daily-{date.today().isoformat()}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def get_full_category_list():
    """Get comprehensive list of categories for daily automation."""
    return [
        "Utilities",           # Storage cleaners, calculators, system tools
        "Productivity",        # Notes, tasks, organization apps
        "Photo & Video",       # Editors, filters, camera apps
        "Lifestyle",           # Trackers, lifestyle management
        "Health & Fitness",    # Activity trackers, health monitors
        "Finance",             # Budget trackers, calculators
        "Music",               # Players, creation tools
        "Education",           # Learning apps, references
        "Graphics & Design",   # Creative tools, design apps
        "Entertainment"        # Games, media, fun apps
    ]


class DailyAutomation:
    """Main daily automation controller."""
    
    def __init__(self, hf_api_key: Optional[str] = None):
        """Initialize daily automation system."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.fetcher = RSSFetcher(rate_limit_delay=ProductionConfig.RSS_RATE_LIMIT_DELAY)
        self.scraper = AppScraper(rate_limit_delay=ProductionConfig.SCRAPE_RATE_LIMIT_DELAY) 
        self.scorer = AppScorer()
        self.store = DataStore()
        
        # Initialize AI recommender (optional)
        self.ai_recommender = None
        if hf_api_key:
            try:
                self.ai_recommender = AIRecommender(hf_api_key)
                self.logger.info("✅ AI recommender initialized")
            except Exception as e:
                self.logger.warning(f"⚠️ AI recommender failed to initialize: {e}")
        
        self.today = date.today()
        
    def run_daily_collection(self, test_mode: bool = False) -> bool:
        """Run the complete daily collection and analysis."""
        
        start_time = datetime.now()
        self.logger.info("🚀 DAILY AUTOMATION STARTING")
        self.logger.info(f"📅 Date: {self.today}")
        
        try:
            # Step 1: Collect comprehensive data
            self.logger.info("Phase 1: 📥 Comprehensive data collection...")
            scored_records = self._collect_all_categories(test_mode)
            
            if not scored_records:
                self.logger.error("❌ No data collected")
                return False
            
            # Step 2: Rank and categorize
            self.logger.info("Phase 2: 📊 Ranking and categorization...")
            daily_rankings = self._create_daily_rankings(scored_records)
            
            # Step 3: Generate AI recommendations for top apps
            self.logger.info("Phase 3: 🤖 Generating AI recommendations...")
            if self.ai_recommender:
                daily_rankings = self._add_ai_recommendations(daily_rankings)
            else:
                self.logger.warning("⚠️ Skipping AI recommendations (no API key)")
            
            # Step 4: Store data locally and in Supabase
            self.logger.info("Phase 4: 💾 Storing data locally and in Supabase...")
            
            # Prepare data for local storage
            automation_data = {
                'scout_results': [self._serialize_record(r) for r in scored_records],
                'trending_selections': daily_rankings,
                'ai_recommendations': [r for r in daily_rankings if r.get('ai_recommendation')]
            }
            
            # Save locally with versioning
            timestamp_str = save_automation_run(automation_data, start_time)
            if timestamp_str:
                self.logger.info(f"📁 Saved locally as: {timestamp_str}")
            else:
                self.logger.warning("⚠️ Local storage failed")
            
            # Store in Supabase
            success = self._store_daily_rankings(daily_rankings)
            
            if not success:
                self.logger.error("❌ Failed to store daily rankings in Supabase")
                return False
            
            # Step 5: Generate daily brief
            self.logger.info("Phase 5: 📋 Generating daily brief...")
            self._generate_daily_brief(daily_rankings)
            
            elapsed = datetime.now() - start_time
            self.logger.info(f"✅ DAILY AUTOMATION COMPLETED in {elapsed}")
            self.logger.info(f"📈 Processed {len(scored_records)} total apps")
            self.logger.info(f"🎯 Generated {len(daily_rankings)} ranked opportunities")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Daily automation failed: {e}")
            return False
    
    def _collect_all_categories(self, test_mode: bool = False) -> List:
        """Collect data across all categories."""
        
        if test_mode:
            categories = ["Utilities", "Productivity"]  # Limited for testing
            countries = ["US"]
            top_n = 10
        else:
            categories = get_full_category_list()
            countries = ["US"]  # US market only per user requirements
            top_n = 25  # Top 25 per category for comprehensive data
        
        self.logger.info(f"Collecting from {len(categories)} categories in {len(countries)} countries")
        
        config = CollectConfig(
            categories=categories,
            countries=countries,
            charts=["free", "paid"],  # Both free and paid apps
            top_n=top_n
        )
        
        # Collect RSS data
        raw_records = self.fetcher.collect_all(config)
        self.logger.info(f"Collected {len(raw_records)} raw app records")
        
        if not raw_records:
            return []
        
        # Scrape app details with intelligent caching
        app_data_map = {}
        successful_scrapes = 0
        consecutive_failures = 0
        max_consecutive_failures = 10  # Fail fast if too many consecutive errors
        
        for i, record in enumerate(raw_records, 1):
            if i % 10 == 0:  # Progress logging
                self.logger.info(f"Scraping progress: {i}/{len(raw_records)} apps")
                
                # Check success rate and fail fast if too low
                success_rate = successful_scrapes / i if i > 0 else 0
                if i > 50 and success_rate < 0.5:  # Less than 50% success after 50 attempts
                    self.logger.error(f"❌ Low success rate ({success_rate:.1%}). Stopping to avoid rate limiting.")
                    break
            
            try:
                # Check cache first (24 hour cache for daily runs)
                cached_html = self.store.cache.get_html(
                    record.app_id, 
                    record.country, 
                    max_age_hours=24  # Shorter cache for daily freshness
                )
                
                if cached_html:
                    app_data = self.scraper.parse_app_page(cached_html, record.app_id)
                else:
                    html = self.scraper.fetch_app_page(record.app_id, record.country)
                    self.store.cache.store_html(record.app_id, record.country, html)
                    app_data = self.scraper.parse_app_page(html, record.app_id)
                
                app_data_map[record.app_id] = app_data
                successful_scrapes += 1
                consecutive_failures = 0  # Reset failure counter
                
                # Conservative rate limiting
                time.sleep(ProductionConfig.SCRAPE_RATE_LIMIT_DELAY)
                
            except Exception as e:
                consecutive_failures += 1
                self.logger.warning(f"Failed to scrape {record.app_id}: {e}")
                
                # Fail fast if too many consecutive failures (likely rate limited)
                if consecutive_failures >= max_consecutive_failures:
                    self.logger.error(f"❌ {consecutive_failures} consecutive failures. Likely rate limited. Stopping.")
                    break
                    
                continue
        
        self.logger.info(f"Successfully scraped {successful_scrapes}/{len(raw_records)} apps")
        
        # Check minimum success threshold
        if len(raw_records) > 0:
            success_rate = successful_scrapes / len(raw_records)
            if success_rate < 0.3:  # Less than 30% success
                self.logger.error(f"❌ Very low success rate ({success_rate:.1%}). Data collection failed.")
                return []
        
        # Score apps
        rank_deltas = self.store.cache.get_rank_deltas(list(app_data_map.keys()))
        scored_records = self.scorer.score_apps(raw_records, app_data_map, rank_deltas)
        
        # Store in main scout_results table too
        self.store.store_and_publish(scored_records)
        
        return scored_records
    
    def _create_daily_rankings(self, scored_records: List) -> List[Dict]:
        """Create ranked daily opportunities from scored records."""
        
        # Group by category
        category_groups = {}
        for record in scored_records:
            category = record.category
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(record)
        
        daily_rankings = []
        
        for category, records in category_groups.items():
            # Sort by total score (best opportunities first)
            records.sort(key=lambda x: x.total, reverse=True)
            
            # Take top 10 per category
            top_records = records[:10]
            
            for rank, record in enumerate(top_records, 1):
                # Assess clone difficulty
                clone_difficulty = self._assess_clone_difficulty(record)
                revenue_potential = self._assess_revenue_potential(record)
                
                ranking_data = {
                    'date': self.today.isoformat(),
                    'category': record.category,
                    'country': record.country,
                    'chart': record.chart,
                    'rank': record.rank,  # Original App Store rank
                    'app_id': record.app_id,
                    'bundle_id': record.bundle_id,
                    'name': record.name,
                    'price': float(record.price),
                    'has_iap': record.has_iap,
                    'rating_count': record.rating_count,
                    'rating_avg': float(record.rating_avg),
                    'desc_len': record.desc_len,
                    'demand': float(record.demand),
                    'monetization': float(record.monetization),
                    'low_complexity': float(record.low_complexity),
                    'moat_risk': float(record.moat_risk),
                    'total': float(record.total),
                    'clone_difficulty': clone_difficulty,
                    'revenue_potential': revenue_potential,
                    'category_rank': rank,  # Our daily rank within category
                    'ai_recommendation': None,  # Will be filled later
                    'recommendation_generated_at': None,
                    
                    # NEW FIELDS for perfect alignment:
                    'clone_name': self._generate_clone_name(record, clone_difficulty),
                    'clone_name_custom': None,  # User can edit later
                    'build_priority': self._map_build_priority(clone_difficulty, revenue_potential, rank)
                }
                
                daily_rankings.append(ranking_data)
        
        self.logger.info(f"Created daily rankings for {len(category_groups)} categories")
        return daily_rankings
    
    def _assess_clone_difficulty(self, record) -> str:
        """Assess how difficult this app would be to clone."""
        name_lower = record.name.lower()
        
        # Check for big tech brands
        big_tech_brands = ['google', 'microsoft', 'apple', 'amazon', 'facebook', 'meta']
        if any(brand in name_lower for brand in big_tech_brands) and record.moat_risk >= 3.0:
            return 'HIGH_RISK'
        
        # Check complexity indicators
        if record.desc_len > 5000 or record.rating_count > 500000:
            return 'COMPLEX'
        
        # Check if it's easy to clone
        if record.low_complexity >= 2.0 and record.moat_risk <= 2.0 and record.desc_len <= 4000:
            return 'EASY_CLONE'
        
        return 'MODERATE'
    
    def _generate_clone_name(self, record, clone_difficulty: str) -> str:
        """Generate AI-powered clone name for the app."""
        
        # Extract core app name (remove developer suffix)
        name = record.name.split(' - ')[0].strip()
        name = name.split(' by ')[0].strip()
        
        # Generate clone name based on category and difficulty
        category_suffixes = {
            'Utilities': ['Pro', 'Master', 'Plus', 'Elite'],
            'Photo & Video': ['Studio', 'Pro', 'Creator', 'Master'],
            'Productivity': ['Pro', 'Suite', 'Master', 'Elite'],
            'Health & Fitness': ['Pro', 'Tracker', 'Coach', 'Master'],
            'Finance': ['Pro', 'Manager', 'Tracker', 'Suite'],
            'Education': ['Academy', 'Pro', 'Master', 'Tutor'],
            'Entertainment': ['Plus', 'Pro', 'Studio', 'Elite'],
            'Lifestyle': ['Pro', 'Plus', 'Master', 'Elite'],
            'Music': ['Studio', 'Pro', 'Master', 'Creator'],
            'Graphics & Design': ['Studio', 'Pro', 'Creator', 'Master']
        }
        
        # Choose suffix based on difficulty (easier = simpler names)
        suffixes = category_suffixes.get(record.category, ['Pro', 'Plus', 'Master', 'Elite'])
        
        if clone_difficulty == 'EASY_CLONE':
            suffix = suffixes[0]  # Simple suffix for easy clones
        elif clone_difficulty == 'MODERATE':
            suffix = suffixes[1] if len(suffixes) > 1 else suffixes[0]
        else:
            suffix = suffixes[-1]  # More ambitious suffix for complex clones
            
        # Handle special cases for common app types
        name_lower = name.lower()
        if 'vpn' in name_lower or 'proxy' in name_lower:
            return f"Tunnel{suffix}"
        elif 'photo' in name_lower or 'camera' in name_lower:
            return f"Snap{suffix}"
        elif 'music' in name_lower or 'audio' in name_lower:
            return f"Audio{suffix}"
        elif 'fitness' in name_lower or 'health' in name_lower:
            return f"Fit{suffix}"
        elif 'finance' in name_lower or 'money' in name_lower:
            return f"Money{suffix}"
        else:
            # Default: use first word + suffix
            first_word = name.split()[0] if name.split() else name
            return f"{first_word}{suffix}"
    
    def _map_build_priority(self, clone_difficulty: str, revenue_potential: str, category_rank: int) -> str:
        """Map app characteristics to build priority."""
        
        # Tonight priority: Easy clones with good opportunity
        if (clone_difficulty == 'EASY_CLONE' and 
            revenue_potential in ['HIGH_REVENUE', 'GOOD_REVENUE'] and 
            category_rank <= 3):
            return 'TONIGHT'
        
        # This week: Easy/moderate clones with decent revenue
        elif (clone_difficulty in ['EASY_CLONE', 'MODERATE'] and 
              revenue_potential in ['GOOD_REVENUE', 'MODEST_REVENUE'] and 
              category_rank <= 5):
            return 'THIS_WEEK'
        
        # This month: More complex but worthwhile opportunities  
        elif (revenue_potential in ['HIGH_REVENUE', 'GOOD_REVENUE'] and 
              category_rank <= 7):
            return 'THIS_MONTH'
        
        # Future: Everything else
        else:
            return 'FUTURE'
    
    def _assess_revenue_potential(self, record) -> str:
        """Assess revenue potential of this app."""
        if record.rating_count >= 50000 and record.rating_avg >= 4.0 and record.rank <= 15:
            return 'HIGH_REVENUE'
        elif record.rating_count >= 1000 and record.rating_avg >= 3.5 and record.rank <= 25:
            return 'GOOD_REVENUE'
        elif record.rank <= 50:
            return 'MODEST_REVENUE'
        else:
            return 'LOW_REVENUE'
    
    def _add_ai_recommendations(self, daily_rankings: List[Dict]) -> List[Dict]:
        """Add AI recommendations to top 3 apps per category."""
        
        # Group by category and get top 3 per category
        category_groups = {}
        for ranking in daily_rankings:
            category = ranking['category']
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(ranking)
        
        apps_for_ai = []
        for category, rankings in category_groups.items():
            # Sort by category rank and take top 3
            rankings.sort(key=lambda x: x['category_rank'])
            top_3 = rankings[:3]
            apps_for_ai.extend(top_3)
        
        self.logger.info(f"Generating AI recommendations for {len(apps_for_ai)} apps")
        
        # Generate AI recommendations in batches
        recommendations = self.ai_recommender.generate_batch_recommendations(apps_for_ai)
        
        # Map recommendations back to rankings
        rec_map = {rec.app_id: rec for rec in recommendations}
        
        updated_rankings = []
        for ranking in daily_rankings:
            if ranking['app_id'] in rec_map:
                rec = rec_map[ranking['app_id']]
                # Format AI recommendation as structured text
                ai_text = self._format_ai_recommendation(rec)
                ranking['ai_recommendation'] = ai_text
                ranking['recommendation_generated_at'] = datetime.now().isoformat()
            
            updated_rankings.append(ranking)
        
        return updated_rankings
    
    def _format_ai_recommendation(self, rec) -> str:
        """Format AI recommendation as structured text."""
        return f"""IMPROVEMENT: {rec.improvement_summary}
FEATURES: {' | '.join(rec.key_features)}
MONETIZATION: {' | '.join(rec.monetization_tips)}
BUILD_TIME: {rec.build_estimate}
MARKET_GAP: {rec.market_gap}
RISKS: {' | '.join(rec.risk_factors)}
GENERATED: {rec.generated_at}"""
    
    def _store_daily_rankings(self, daily_rankings: List[Dict]) -> bool:
        """Store daily rankings in Supabase."""
        
        try:
            # Clear today's existing rankings
            self.store.publisher.client.table("daily_rankings").delete().eq(
                "date", self.today.isoformat()
            ).execute()
            
            # Insert new rankings in batches
            batch_size = 50
            for i in range(0, len(daily_rankings), batch_size):
                batch = daily_rankings[i:i + batch_size]
                
                result = self.store.publisher.client.table("daily_rankings").insert(batch).execute()
                
                if not result.data:
                    self.logger.error(f"Failed to insert batch {i//batch_size + 1}")
                    return False
            
            self.logger.info(f"Successfully stored {len(daily_rankings)} daily rankings")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store daily rankings: {e}")
            return False
    
    def _generate_daily_brief(self, daily_rankings: List[Dict]):
        """Generate and log daily brief summary."""
        
        # Category analysis
        category_stats = {}
        total_easy_clones = 0
        total_with_ai = 0
        
        for ranking in daily_rankings:
            cat = ranking['category']
            if cat not in category_stats:
                category_stats[cat] = {
                    'total': 0, 'easy_clones': 0, 'with_ai': 0, 
                    'avg_score': 0, 'top_app': None
                }
            
            stats = category_stats[cat]
            stats['total'] += 1
            stats['avg_score'] += ranking['total']
            
            if ranking['clone_difficulty'] == 'EASY_CLONE':
                stats['easy_clones'] += 1
                total_easy_clones += 1
            
            if ranking['ai_recommendation']:
                stats['with_ai'] += 1
                total_with_ai += 1
            
            # Track top app per category
            if stats['top_app'] is None or ranking['category_rank'] == 1:
                stats['top_app'] = ranking
        
        # Calculate averages
        for cat in category_stats:
            if category_stats[cat]['total'] > 0:
                category_stats[cat]['avg_score'] /= category_stats[cat]['total']
        
        # Generate brief
        self.logger.info("📋 DAILY BRIEF SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"📅 Date: {self.today}")
        self.logger.info(f"🎯 Total Opportunities: {len(daily_rankings)} apps")
        self.logger.info(f"🟢 Easy Clone Candidates: {total_easy_clones}")
        self.logger.info(f"🤖 AI Recommendations: {total_with_ai}")
        self.logger.info(f"📂 Categories Analyzed: {len(category_stats)}")
        
        self.logger.info("\n📊 CATEGORY BREAKDOWN:")
        for cat, stats in sorted(category_stats.items(), key=lambda x: x[1]['easy_clones'], reverse=True):
            top_app_name = stats['top_app']['name'][:30] if stats['top_app'] else "None"
            self.logger.info(f"  {cat:15} | {stats['total']:2d} apps | {stats['easy_clones']:2d} easy | "
                           f"Avg: {stats['avg_score']:4.2f} | Top: {top_app_name}")
        
        # Tonight's build recommendations
        tonight_candidates = [r for r in daily_rankings 
                            if r['category_rank'] <= 2 and r['clone_difficulty'] == 'EASY_CLONE' 
                            and r['ai_recommendation']]
        
        self.logger.info(f"\n🌙 TONIGHT'S BUILD CANDIDATES ({len(tonight_candidates)}):")
        for candidate in tonight_candidates[:5]:  # Top 5
            self.logger.info(f"  • {candidate['name'][:40]} - {candidate['category']} (Score: {candidate['total']:.2f})")
        
        self.logger.info(f"\n✨ Daily automation completed successfully!")
    
    def _serialize_record(self, record) -> Dict:
        """Convert a ScoutResult to a serializable dictionary."""
        return {
            'id': str(getattr(record, 'id', '')),
            'generated_at': getattr(record, 'generated_at', self.today).isoformat() if hasattr(getattr(record, 'generated_at', self.today), 'isoformat') else str(getattr(record, 'generated_at', self.today)),
            'category': record.category,
            'country': record.country,
            'chart': record.chart,
            'rank': record.rank,
            'app_id': record.app_id,
            'bundle_id': record.bundle_id,
            'name': record.name,
            'price': float(record.price),
            'has_iap': record.has_iap,
            'rating_count': record.rating_count,
            'rating_avg': float(record.rating_avg),
            'desc_len': record.desc_len,
            'rank_delta7d': getattr(record, 'rank_delta7d', None),
            'demand': float(record.demand),
            'monetization': float(record.monetization),
            'low_complexity': float(record.low_complexity),
            'moat_risk': float(record.moat_risk),
            'total': float(record.total),
            'raw': getattr(record, 'raw', {}),
            'created_at': getattr(record, 'created_at', datetime.now()).isoformat() if hasattr(getattr(record, 'created_at', datetime.now()), 'isoformat') else str(getattr(record, 'created_at', datetime.now())),
            'updated_at': getattr(record, 'updated_at', datetime.now()).isoformat() if hasattr(getattr(record, 'updated_at', datetime.now()), 'isoformat') else str(getattr(record, 'updated_at', datetime.now()))
        }
        self.logger.info(f"📱 Next: Check category_leaders view in Supabase for detailed recommendations")


def main():
    """Main entry point for daily automation."""
    parser = argparse.ArgumentParser(description="Daily Trend Scout automation")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    parser.add_argument("--hf-api-key", help="Hugging Face API key for AI recommendations")
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Get Hugging Face API key from args or environment
    hf_api_key = args.hf_api_key or os.getenv("HUGGING_FACE_API_KEY")
    if not hf_api_key:
        logger.warning("⚠️ No Hugging Face API key provided. AI recommendations will be skipped.")
        logger.warning("   Set HUGGING_FACE_API_KEY env var or use --hf-api-key argument")
    
    automation = DailyAutomation(hf_api_key)
    
    success = automation.run_daily_collection(test_mode=args.test)
    
    if success:
        logger.info("✅ Daily automation completed successfully")
        exit(0)
    else:
        logger.error("❌ Daily automation failed")
        exit(1)


if __name__ == "__main__":
    main()