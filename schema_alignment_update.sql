-- Schema Alignment Updates for Perfect Sync
-- Run this in your Supabase SQL Editor

-- Add missing fields to daily_rankings table
ALTER TABLE daily_rankings ADD COLUMN IF NOT EXISTS clone_name TEXT;
ALTER TABLE daily_rankings ADD COLUMN IF NOT EXISTS clone_name_custom TEXT;
ALTER TABLE daily_rankings ADD COLUMN IF NOT EXISTS build_priority TEXT CHECK (build_priority IN ('TONIGHT', 'THIS_WEEK', 'THIS_MONTH', 'FUTURE'));

-- Add comments for documentation
COMMENT ON COLUMN daily_rankings.clone_name IS 'AI-generated clone app name';
COMMENT ON COLUMN daily_rankings.clone_name_custom IS 'User-customized clone app name';
COMMENT ON COLUMN daily_rankings.build_priority IS 'Build priority: TONIGHT (3-4h), THIS_WEEK, THIS_MONTH, FUTURE';

-- Create index for build priority queries
CREATE INDEX IF NOT EXISTS idx_daily_rankings_build_priority ON daily_rankings(build_priority);

-- Drop and recreate views to handle schema changes
DROP VIEW IF EXISTS todays_opportunities CASCADE;
DROP VIEW IF EXISTS tonight_opportunities CASCADE;

-- Create updated views with new fields
CREATE VIEW todays_opportunities AS
SELECT *,
  CASE 
    WHEN category_rank <= 3 THEN 'TOP'
    WHEN category_rank <= 7 THEN 'MIDDLE' 
    ELSE 'LOWER'
  END as rank_tier
FROM daily_rankings
WHERE date = CURRENT_DATE
ORDER BY category, category_rank
LIMIT 10;

-- Create view for tonight's buildable apps
CREATE VIEW tonight_opportunities AS
SELECT *
FROM daily_rankings
WHERE date = CURRENT_DATE 
  AND build_priority = 'TONIGHT'
  AND clone_difficulty = 'EASY_CLONE'
ORDER BY total DESC, category_rank ASC;

-- Verify schema changes
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'daily_rankings' 
  AND table_schema = 'public'
ORDER BY ordinal_position;