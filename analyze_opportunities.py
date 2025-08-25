#!/usr/bin/env python3
"""
Micro-Opportunities Analysis Script

Analyze collected data to identify the best clone candidates for rapid app development.
This script provides actionable insights for the compound app portfolio strategy.
"""

import argparse
from datetime import datetime
from trendscout.store import SupabasePublisher


def analyze_clone_opportunities(min_score=1.8, show_all=False):
    """
    Analyze and rank clone opportunities from collected data.
    
    Args:
        min_score: Minimum total score to consider
        show_all: If True, show all opportunities, not just top ones
    """
    publisher = SupabasePublisher()
    
    print("🎯 MICRO-OPPORTUNITIES ANALYSIS")
    print("=" * 70)
    print("Finding clone-worthy apps for rapid development & revenue generation")
    print()
    
    # Try to get from micro_opportunities view first (if SQL was run)
    try:
        result = publisher.client.table('micro_opportunities').select('*').execute()
        
        if result.data:
            print("📋 USING MICRO_OPPORTUNITIES VIEW (Optimized Results)")
            opportunities = result.data
        else:
            raise Exception("No data in micro_opportunities view")
            
    except:
        print("📋 USING LATEST_RESULTS (Manual Analysis)")
        # Fallback to manual analysis
        result = publisher.client.table('latest_results').select('*').execute()
        opportunities = []
        
        for app in result.data:
            # Apply micro-opportunity filters manually
            if (app['total'] >= min_score and 
                app['low_complexity'] >= 2.0 and 
                app['moat_risk'] <= 3.0):
                
                # Add clone difficulty assessment
                if ('google' in app['name'].lower() or 
                    'microsoft' in app['name'].lower() or
                    app['moat_risk'] >= 3.0):
                    clone_difficulty = 'HIGH_RISK'
                elif (app['desc_len'] > 5000 or app['rating_count'] > 500000):
                    clone_difficulty = 'COMPLEX'
                elif (app['low_complexity'] >= 2.0 and app['moat_risk'] <= 2.0 and app['desc_len'] <= 4000):
                    clone_difficulty = 'EASY_CLONE'
                else:
                    clone_difficulty = 'MODERATE'
                
                # Add revenue potential assessment
                if (app['rating_count'] >= 50000 and app['rating_avg'] >= 4.0 and app['rank'] <= 15):
                    revenue_potential = 'HIGH_REVENUE'
                elif (app['rating_count'] >= 1000 and app['rating_avg'] >= 3.5 and app['rank'] <= 25):
                    revenue_potential = 'GOOD_REVENUE'
                elif app['rank'] <= 50:
                    revenue_potential = 'MODEST_REVENUE'
                else:
                    revenue_potential = 'LOW_REVENUE'
                
                app['clone_difficulty'] = clone_difficulty
                app['revenue_potential'] = revenue_potential
                opportunities.append(app)
    
    if not opportunities:
        print("❌ No micro-opportunities found. Try running collection first.")
        return
    
    # Sort by clone difficulty (easiest first), then by score
    priority_order = {'EASY_CLONE': 1, 'MODERATE': 2, 'COMPLEX': 3, 'HIGH_RISK': 4}
    opportunities.sort(key=lambda x: (
        priority_order.get(x.get('clone_difficulty', 'MODERATE'), 2),
        -x['total']
    ))
    
    # Analyze by category
    category_stats = {}
    for app in opportunities:
        cat = app['category']
        if cat not in category_stats:
            category_stats[cat] = {
                'count': 0, 'easy_clones': 0, 'avg_score': 0, 
                'paid_apps': 0, 'high_revenue': 0
            }
        
        stats = category_stats[cat]
        stats['count'] += 1
        stats['avg_score'] += app['total']
        
        if app.get('clone_difficulty') == 'EASY_CLONE':
            stats['easy_clones'] += 1
        if app['price'] > 0:
            stats['paid_apps'] += 1
        if app.get('revenue_potential') in ['HIGH_REVENUE', 'GOOD_REVENUE']:
            stats['high_revenue'] += 1
    
    # Calculate averages
    for cat in category_stats:
        if category_stats[cat]['count'] > 0:
            category_stats[cat]['avg_score'] /= category_stats[cat]['count']
    
    print(f"📊 CATEGORY BREAKDOWN:")
    print("-" * 70)
    for cat, stats in sorted(category_stats.items(), key=lambda x: x[1]['easy_clones'], reverse=True):
        print(f"{cat:15} | {stats['count']:2d} apps | {stats['easy_clones']:2d} easy clones | "
              f"Avg: {stats['avg_score']:4.2f} | {stats['paid_apps']} paid | {stats['high_revenue']} high-rev")
    
    print(f"\n🎯 TOP CLONE OPPORTUNITIES:")
    print("-" * 70)
    
    limit = 20 if show_all else 10
    for i, app in enumerate(opportunities[:limit], 1):
        name = app['name'][:45]
        category = app['category'][:12]
        difficulty = app.get('clone_difficulty', 'MODERATE')
        revenue = app.get('revenue_potential', 'MODEST_REVENUE')
        
        # Color coding for quick assessment
        difficulty_icon = {
            'EASY_CLONE': '🟢', 'MODERATE': '🟡', 'COMPLEX': '🟠', 'HIGH_RISK': '🔴'
        }.get(difficulty, '⚪')
        
        revenue_icon = {
            'HIGH_REVENUE': '💰', 'GOOD_REVENUE': '💵', 'MODEST_REVENUE': '💴', 'LOW_REVENUE': '💸'
        }.get(revenue, '💴')
        
        print(f"{i:2d}. {difficulty_icon} {name:<45} | {category:<12}")
        print(f"    Bundle: {app['bundle_id'][:55]}")
        print(f"    💯 Score: {app['total']:4.2f} | Rank #{app['rank']} | "
              f"⭐ {app['rating_avg']} ({app['rating_count']:,} ratings)")
        print(f"    💰 ${app['price']:.2f} | 📝 {app['desc_len']} chars | "
              f"Clone: {difficulty} | Revenue: {revenue_icon} {revenue}")
        print()
    
    # Provide actionable recommendations
    print("💡 ACTIONABLE INSIGHTS:")
    print("-" * 70)
    
    easy_clones = [app for app in opportunities if app.get('clone_difficulty') == 'EASY_CLONE']
    paid_apps = [app for app in opportunities if app['price'] > 0]
    good_revenue = [app for app in opportunities if app.get('revenue_potential') in ['HIGH_REVENUE', 'GOOD_REVENUE']]
    
    print(f"🟢 IMMEDIATE CLONE CANDIDATES: {len(easy_clones)} apps")
    if easy_clones:
        print("   Recommendations for tonight's build:")
        for app in easy_clones[:3]:
            print(f"   • {app['name'][:50]} (Score: {app['total']:.2f})")
    
    print(f"\n💰 PAID APP OPPORTUNITIES: {len(paid_apps)} apps")
    if paid_apps:
        print("   Consider freemium versions of:")
        for app in paid_apps[:3]:
            print(f"   • {app['name'][:40]} - ${app['price']:.2f} (Score: {app['total']:.2f})")
    
    print(f"\n📈 HIGH REVENUE POTENTIAL: {len(good_revenue)} apps")
    if good_revenue:
        print("   Focus on these markets:")
        for app in good_revenue[:3]:
            print(f"   • {app['name'][:40]} - {app['rating_count']:,} users (Score: {app['total']:.2f})")
    
    # Build schedule recommendations
    print(f"\n📅 BUILD SCHEDULE RECOMMENDATIONS:")
    print("   Week 1-4 (Learning Phase): Focus on EASY_CLONE apps")
    print("   Week 5-12: Mix of MODERATE complexity apps")
    print("   Month 4+: Expand to higher revenue categories")
    
    total_opportunities = len(opportunities)
    print(f"\n✨ TOTAL MICRO-OPPORTUNITIES: {total_opportunities} apps ready for cloning")
    print("   Target: 1 app/week = 3+ months of opportunities identified!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze micro-opportunities for app cloning")
    parser.add_argument("--min-score", type=float, default=1.8, help="Minimum score threshold")
    parser.add_argument("--show-all", action="store_true", help="Show all opportunities")
    
    args = parser.parse_args()
    
    try:
        analyze_clone_opportunities(min_score=args.min_score, show_all=args.show_all)
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        print("Make sure you've run data collection first and created the micro_opportunities view.")


if __name__ == "__main__":
    main()