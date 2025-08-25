#!/usr/bin/env python3
"""
Daily Brief Generator

Generates comprehensive daily briefs from collected data with:
- Top 10 trending apps per category
- Top 3 potentials per category with AI recommendations  
- Build priorities and actionable insights
- Trending analysis vs yesterday
"""

import argparse
import json
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from trendscout.store import SupabasePublisher


class DailyBriefGenerator:
    """Generates daily briefs from collected trend data."""
    
    def __init__(self):
        """Initialize brief generator."""
        self.publisher = SupabasePublisher()
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=1)
    
    def generate_brief(self, output_format: str = 'text') -> str:
        """
        Generate comprehensive daily brief.
        
        Args:
            output_format: 'text', 'json', or 'markdown'
            
        Returns:
            Formatted brief string
        """
        try:
            # Collect all data
            brief_data = self._collect_brief_data()
            
            # Format based on requested output
            if output_format == 'json':
                return self._format_as_json(brief_data)
            elif output_format == 'markdown':
                return self._format_as_markdown(brief_data)
            else:
                return self._format_as_text(brief_data)
                
        except Exception as e:
            return f"❌ Error generating brief: {e}"
    
    def _collect_brief_data(self) -> Dict:
        """Collect all data needed for daily brief."""
        
        # Get today's opportunities (top 10 per category)
        todays_result = self.publisher.client.table('todays_opportunities').select('*').execute()
        todays_apps = todays_result.data if todays_result.data else []
        
        # Get category leaders (top 3 per category with AI recommendations)
        leaders_result = self.publisher.client.table('category_leaders').select('*').execute()
        category_leaders = leaders_result.data if leaders_result.data else []
        
        # Get trending analysis
        trending_result = self.publisher.client.table('trending_analysis').select('*').execute()
        trending_data = trending_result.data if trending_data else []
        
        # Get daily brief summary stats
        try:
            brief_stats_result = self.publisher.client.rpc('get_daily_brief').execute()
            brief_stats = brief_stats_result.data if brief_stats_result.data else []
        except:
            brief_stats = []
        
        # Organize data by category
        categories = {}
        
        # Group today's apps by category
        for app in todays_apps:
            cat = app['category']
            if cat not in categories:
                categories[cat] = {
                    'name': cat,
                    'top_10': [],
                    'top_3_leaders': [],
                    'stats': {},
                    'trending_count': 0
                }
            categories[cat]['top_10'].append(app)
        
        # Add category leaders
        for leader in category_leaders:
            cat = leader['category']
            if cat in categories:
                categories[cat]['top_3_leaders'].append(leader)
        
        # Add trending info
        for trend in trending_data:
            cat = trend['category']
            if cat in categories and trend['trend_direction'] == 'TRENDING_UP':
                categories[cat]['trending_count'] += 1
        
        # Add stats
        for stat in brief_stats:
            cat = stat['category']
            if cat in categories:
                categories[cat]['stats'] = stat
        
        return {
            'date': self.today.isoformat(),
            'total_apps': len(todays_apps),
            'total_categories': len(categories),
            'total_leaders': len(category_leaders),
            'categories': categories,
            'trending_data': trending_data,
            'brief_stats': brief_stats
        }
    
    def _format_as_text(self, data: Dict) -> str:
        """Format brief as readable text."""
        
        output = []
        output.append("🎯 TREND SCOUT DAILY BRIEF")
        output.append("=" * 60)
        output.append(f"📅 Date: {data['date']}")
        output.append(f"🎯 Total Opportunities: {data['total_apps']} apps")
        output.append(f"📂 Categories Analyzed: {data['total_categories']}")
        output.append(f"👑 Category Leaders: {data['total_leaders']} (with AI recommendations)")
        output.append("")
        
        # Executive Summary
        tonight_priorities = []
        easy_clones_total = 0
        high_revenue_total = 0
        
        for cat_data in data['categories'].values():
            for leader in cat_data['top_3_leaders']:
                if leader.get('build_priority') == 'PRIORITY_1_TONIGHT':
                    tonight_priorities.append(leader)
                if leader.get('clone_difficulty') == 'EASY_CLONE':
                    easy_clones_total += 1
                if leader.get('revenue_potential') == 'HIGH_REVENUE':
                    high_revenue_total += 1
        
        output.append("📊 EXECUTIVE SUMMARY")
        output.append("-" * 30)
        output.append(f"🌙 Priority Tonight: {len(tonight_priorities)} apps ready to build")
        output.append(f"🟢 Easy Clone Candidates: {easy_clones_total} apps")
        output.append(f"💰 High Revenue Potential: {high_revenue_total} apps")
        output.append("")
        
        # Tonight's Build Recommendations
        if tonight_priorities:
            output.append("🌙 TONIGHT'S BUILD RECOMMENDATIONS")
            output.append("-" * 40)
            for app in tonight_priorities[:3]:  # Top 3
                output.append(f"🎯 {app['name']}")
                output.append(f"   Category: {app['category']} | Score: {app['total']:.2f}")
                output.append(f"   Bundle: {app['bundle_id']}")
                output.append(f"   Revenue: {app['revenue_potential']} | Difficulty: {app['clone_difficulty']}")
                
                # Extract AI recommendation summary
                if app.get('ai_recommendation'):
                    lines = app['ai_recommendation'].split('\n')
                    improvement = next((line.replace('IMPROVEMENT:', '').strip() 
                                     for line in lines if line.startswith('IMPROVEMENT:')), 'Available in full report')
                    build_time = next((line.replace('BUILD_TIME:', '').strip() 
                                     for line in lines if line.startswith('BUILD_TIME:')), 'TBD')
                    
                    output.append(f"   💡 Improvement: {improvement}")
                    output.append(f"   ⏱️  Build Time: {build_time}")
                output.append("")
        
        # Category Breakdown
        output.append("📂 CATEGORY BREAKDOWN")
        output.append("-" * 40)
        
        # Sort categories by number of easy clones
        sorted_categories = sorted(
            data['categories'].values(), 
            key=lambda x: len([l for l in x['top_3_leaders'] if l.get('clone_difficulty') == 'EASY_CLONE']),
            reverse=True
        )
        
        for cat_data in sorted_categories:
            cat_name = cat_data['name']
            leaders = cat_data['top_3_leaders']
            easy_clones = len([l for l in leaders if l.get('clone_difficulty') == 'EASY_CLONE'])
            avg_score = sum(l['total'] for l in leaders) / len(leaders) if leaders else 0
            
            output.append(f"{cat_name:15} | {len(cat_data['top_10']):2d} apps | {easy_clones:2d} easy clones | Avg: {avg_score:4.2f}")
            
            # Show top 3 with AI recommendations
            for i, leader in enumerate(leaders, 1):
                priority_icon = {
                    'PRIORITY_1_TONIGHT': '🌙',
                    'PRIORITY_2_THIS_WEEK': '📅', 
                    'PRIORITY_3_THIS_MONTH': '📆',
                    'PRIORITY_4_FUTURE': '⏳'
                }.get(leader.get('build_priority'), '📱')
                
                difficulty_icon = {
                    'EASY_CLONE': '🟢', 'MODERATE': '🟡', 
                    'COMPLEX': '🟠', 'HIGH_RISK': '🔴'
                }.get(leader.get('clone_difficulty'), '⚪')
                
                output.append(f"  {i}. {priority_icon} {difficulty_icon} {leader['name'][:45]}")
                output.append(f"     Score: {leader['total']:.2f} | Rank: #{leader['rank']} | "
                            f"⭐ {leader['rating_avg']} ({leader['rating_count']:,})")
                
                # Show AI recommendation snippet
                if leader.get('ai_recommendation'):
                    lines = leader['ai_recommendation'].split('\n')
                    improvement = next((line.replace('IMPROVEMENT:', '').strip() 
                                     for line in lines if line.startswith('IMPROVEMENT:')), '')
                    if improvement:
                        output.append(f"     💡 {improvement[:80]}...")
            
            output.append("")
        
        # Trending Analysis
        trending_up = [t for t in data.get('trending_data', []) if t['trend_direction'] == 'TRENDING_UP']
        if trending_up:
            output.append("📈 TRENDING UP (vs Yesterday)")
            output.append("-" * 30)
            for trend in trending_up[:5]:  # Top 5
                output.append(f"📈 {trend['app_name'][:40]} - {trend['category']} (+{trend['rank_change']})")
            output.append("")
        
        # Action Items
        output.append("✅ ACTION ITEMS")
        output.append("-" * 20)
        output.append("1. 🌙 Review tonight's build recommendations above")
        output.append("2. 📊 Check category_leaders view in Supabase for full AI recommendations")
        output.append("3. 📈 Monitor trending_analysis view for emerging opportunities")
        output.append("4. 🎯 Focus on EASY_CLONE apps for quick wins")
        output.append("")
        
        output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return '\n'.join(output)
    
    def _format_as_json(self, data: Dict) -> str:
        """Format brief as JSON for API consumption."""
        
        # Create structured JSON output
        json_data = {
            'brief_date': data['date'],
            'summary': {
                'total_apps': data['total_apps'],
                'total_categories': data['total_categories'],
                'total_leaders': data['total_leaders']
            },
            'tonight_priorities': [],
            'categories': {},
            'trending': []
        }
        
        # Extract tonight's priorities
        for cat_data in data['categories'].values():
            for leader in cat_data['top_3_leaders']:
                if leader.get('build_priority') == 'PRIORITY_1_TONIGHT':
                    json_data['tonight_priorities'].append({
                        'name': leader['name'],
                        'category': leader['category'],
                        'bundle_id': leader['bundle_id'],
                        'score': leader['total'],
                        'clone_difficulty': leader['clone_difficulty'],
                        'revenue_potential': leader['revenue_potential'],
                        'ai_recommendation': leader.get('ai_recommendation')
                    })
        
        # Process categories
        for cat_name, cat_data in data['categories'].items():
            json_data['categories'][cat_name] = {
                'total_apps': len(cat_data['top_10']),
                'top_3_leaders': [
                    {
                        'rank': leader['category_rank'],
                        'name': leader['name'],
                        'bundle_id': leader['bundle_id'],
                        'score': leader['total'],
                        'clone_difficulty': leader['clone_difficulty'],
                        'revenue_potential': leader['revenue_potential'],
                        'build_priority': leader.get('build_priority'),
                        'ai_recommendation': leader.get('ai_recommendation')
                    }
                    for leader in cat_data['top_3_leaders']
                ]
            }
        
        # Add trending data
        json_data['trending'] = [
            {
                'app_name': t.get('app_name', ''),
                'category': t['category'],
                'trend_direction': t['trend_direction'],
                'rank_change': t.get('rank_change', 0)
            }
            for t in data.get('trending_data', [])
            if t['trend_direction'] == 'TRENDING_UP'
        ][:10]  # Top 10
        
        return json.dumps(json_data, indent=2)
    
    def _format_as_markdown(self, data: Dict) -> str:
        """Format brief as Markdown for documentation."""
        
        output = []
        output.append("# 🎯 Trend Scout Daily Brief")
        output.append(f"**Date:** {data['date']}")
        output.append(f"**Total Opportunities:** {data['total_apps']} apps")
        output.append(f"**Categories:** {data['total_categories']}")
        output.append("")
        
        # Tonight's priorities
        tonight_priorities = []
        for cat_data in data['categories'].values():
            for leader in cat_data['top_3_leaders']:
                if leader.get('build_priority') == 'PRIORITY_1_TONIGHT':
                    tonight_priorities.append(leader)
        
        if tonight_priorities:
            output.append("## 🌙 Tonight's Build Recommendations")
            output.append("")
            
            for app in tonight_priorities[:3]:
                output.append(f"### {app['name']}")
                output.append(f"- **Category:** {app['category']}")
                output.append(f"- **Score:** {app['total']:.2f}")
                output.append(f"- **Bundle ID:** `{app['bundle_id']}`")
                output.append(f"- **Difficulty:** {app['clone_difficulty']}")
                output.append(f"- **Revenue Potential:** {app['revenue_potential']}")
                
                if app.get('ai_recommendation'):
                    lines = app['ai_recommendation'].split('\n')
                    improvement = next((line.replace('IMPROVEMENT:', '').strip() 
                                     for line in lines if line.startswith('IMPROVEMENT:')), '')
                    if improvement:
                        output.append(f"- **AI Recommendation:** {improvement}")
                
                output.append("")
        
        # Categories
        output.append("## 📂 Categories Overview")
        output.append("")
        output.append("| Category | Apps | Easy Clones | Avg Score |")
        output.append("|----------|------|-------------|-----------|")
        
        for cat_data in data['categories'].values():
            cat_name = cat_data['name']
            easy_clones = len([l for l in cat_data['top_3_leaders'] if l.get('clone_difficulty') == 'EASY_CLONE'])
            avg_score = sum(l['total'] for l in cat_data['top_3_leaders']) / len(cat_data['top_3_leaders']) if cat_data['top_3_leaders'] else 0
            
            output.append(f"| {cat_name} | {len(cat_data['top_10'])} | {easy_clones} | {avg_score:.2f} |")
        
        output.append("")
        output.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return '\n'.join(output)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate daily brief from collected data")
    parser.add_argument("--format", choices=['text', 'json', 'markdown'], 
                       default='text', help="Output format")
    parser.add_argument("--output", help="Output file (default: stdout)")
    
    args = parser.parse_args()
    
    generator = DailyBriefGenerator()
    brief = generator.generate_brief(args.format)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(brief)
        print(f"✅ Brief saved to {args.output}")
    else:
        print(brief)


if __name__ == "__main__":
    main()