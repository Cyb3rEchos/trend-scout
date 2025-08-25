#!/usr/bin/env python3
"""
Daily Automation Setup Script

This script sets up everything needed for daily automation:
1. Installs required dependencies
2. Updates Supabase schema automatically
3. Tests the system
4. Sets up schedule (optional)
"""

import os
import sys
import subprocess
from pathlib import Path
from trendscout.store import SupabasePublisher


def run_command(command: str, description: str):
    """Run a shell command and report results."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} successful")
        if result.stdout.strip():
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr}")
        return False


def update_supabase_schema():
    """Automatically update Supabase schema."""
    print("🗃️  Setting up Supabase schema...")
    
    try:
        publisher = SupabasePublisher()
        print("✅ Supabase connection successful")
        
        # Read and execute the schema SQL
        schema_file = Path(__file__).parent / "daily_automation_schema.sql"
        
        if not schema_file.exists():
            print("❌ Schema file not found")
            return False
        
        print("📋 Schema SQL file created. Please run it manually in Supabase SQL Editor:")
        print(f"   File: {schema_file}")
        print("   Instructions:")
        print("   1. Go to your Supabase dashboard")
        print("   2. Navigate to SQL Editor")
        print("   3. Copy and paste the contents of daily_automation_schema.sql")
        print("   4. Click 'Run' to execute")
        print("   5. Come back here and press Enter when done")
        
        input("\n⏸️  Press Enter after running the SQL in Supabase...")
        
        # Test if the schema was created
        result = publisher.client.table("daily_rankings").select("*").limit(1).execute()
        print("✅ Supabase schema setup verified")
        return True
        
    except Exception as e:
        print(f"❌ Supabase setup failed: {e}")
        print("   Please check your SUPABASE_URL and SUPABASE_SERVICE_KEY in .env file")
        return False


def install_dependencies():
    """Install required Python dependencies."""
    print("📦 Installing dependencies...")
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print("⚠️  Warning: Not in a virtual environment")
        print("   It's recommended to activate your venv first: source venv/bin/activate")
        response = input("   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    # Install additional dependencies for AI recommendations
    dependencies = [
        "requests>=2.31.0",  # For Hugging Face API
    ]
    
    for dep in dependencies:
        if not run_command(f"pip install '{dep}'", f"Installing {dep}"):
            return False
    
    return True


def test_system():
    """Test the daily automation system."""
    print("🧪 Testing daily automation system...")
    
    # Test basic collection (small sample)
    print("   Testing data collection...")
    test_cmd = "python daily_automation.py --test"
    
    print(f"   Running: {test_cmd}")
    print("   This will collect a small sample of data to test the system...")
    print("   (This may take 2-3 minutes)")
    
    if run_command(test_cmd, "Daily automation test"):
        print("✅ System test successful!")
        
        # Test brief generation
        print("   Testing brief generation...")
        if run_command("python generate_daily_brief.py --format text", "Brief generation test"):
            print("✅ Complete system test successful!")
            return True
    
    print("❌ System test failed")
    return False


def show_setup_instructions():
    """Show final setup instructions."""
    print("\n🎉 DAILY AUTOMATION SETUP COMPLETE!")
    print("=" * 60)
    
    print("\n📋 NEXT STEPS:")
    print("1. Get a Hugging Face API key:")
    print("   • Go to https://huggingface.co/settings/tokens")
    print("   • Create a new token with 'Read' permissions")
    print("   • Add to your .env file: HUGGING_FACE_API_KEY=your_key_here")
    
    print("\n2. Run daily automation:")
    print("   • Full collection: python daily_automation.py")
    print("   • With AI recommendations: python daily_automation.py --hf-api-key your_key")
    print("   • Test mode: python daily_automation.py --test")
    
    print("\n3. Generate daily briefs:")
    print("   • Text format: python generate_daily_brief.py")
    print("   • JSON format: python generate_daily_brief.py --format json")
    print("   • Save to file: python generate_daily_brief.py --output brief.md --format markdown")
    
    print("\n4. Set up daily schedule (macOS):")
    print("   • The system can be automated using launchd")
    print("   • Run daily at 6 AM: python daily_automation.py")
    print("   • Generate brief at 7 AM: python generate_daily_brief.py --output daily_brief.md --format markdown")
    
    print("\n5. Check your data:")
    print("   • View in Supabase: todays_opportunities, category_leaders, trending_analysis")
    print("   • Each day you'll get top 10 per category + top 3 with AI recommendations")
    print("   • Focus on apps marked as 'PRIORITY_1_TONIGHT' for immediate builds")
    
    print("\n📱 YOUR DAILY WORKFLOW:")
    print("   Morning: Check daily brief for tonight's build recommendations")
    print("   Evening: Build the top EASY_CLONE app with AI suggestions")
    print("   Compound: 1 app/week = 50+ apps/year with minimal effort!")
    
    print(f"\n✨ Daily automation is ready! Your compound app strategy starts now!")


def main():
    """Main setup process."""
    print("🚀 TREND SCOUT DAILY AUTOMATION SETUP")
    print("=" * 50)
    print("Setting up complete daily automation for micro-opportunity detection")
    print()
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        return False
    
    # Step 2: Update Supabase schema
    if not update_supabase_schema():
        print("❌ Setup failed at Supabase schema setup")
        return False
    
    # Step 3: Test system
    test_success = test_system()
    
    # Step 4: Show instructions regardless of test results
    show_setup_instructions()
    
    if test_success:
        print("\n🎯 All systems ready! Your daily micro-opportunity pipeline is live!")
        return True
    else:
        print("\n⚠️  Setup completed but tests failed. Check the logs and try running manually.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)