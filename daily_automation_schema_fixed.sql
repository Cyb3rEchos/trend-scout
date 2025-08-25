-- Trend Scout Daily Automation Schema (FIXED)
-- Run this ONCE in your Supabase SQL editor to enable full daily automation

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create daily rankings table for tracking top apps per category
CREATE TABLE IF NOT EXISTS daily_rankings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL,
    category TEXT NOT NULL,
    country TEXT NOT NULL,
    chart TEXT NOT NULL,
    rank INTEGER NOT NULL,
    app_id TEXT NOT NULL,
    bundle_id TEXT NOT NULL,
    name TEXT NOT NULL,
    price NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    has_iap BOOLEAN NOT NULL DEFAULT FALSE,
    rating_count INTEGER NOT NULL DEFAULT 0,
    rating_avg NUMERIC(3,2) NOT NULL DEFAULT 0.00,
    desc_len INTEGER NOT NULL DEFAULT 0,
    demand NUMERIC(3,2) NOT NULL,
    monetization NUMERIC(3,2) NOT NULL,
    low_complexity NUMERIC(3,2) NOT NULL,
    moat_risk NUMERIC(3,2) NOT NULL,
    total NUMERIC(5,2) NOT NULL,
    clone_difficulty TEXT,
    revenue_potential TEXT,
    category_rank INTEGER NOT NULL,  -- Daily rank within category (1-10)
    ai_recommendation TEXT,  -- AI-generated improvement suggestion
    recommendation_generated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_daily_rankings_date_category ON daily_rankings(date DESC, category);
CREATE INDEX IF NOT EXISTS idx_daily_rankings_category_rank ON daily_rankings(category, category_rank);
CREATE INDEX IF NOT EXISTS idx_daily_rankings_total ON daily_rankings(total DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_rankings_unique 
ON daily_rankings(date, app_id, category, country, chart);

-- Create micro_opportunities view (clone candidates) - FIXED
CREATE OR REPLACE VIEW micro_opportunities AS
WITH assessed_apps AS (
    SELECT 
        *,
        -- Clone difficulty assessment
        CASE 
            WHEN (name ILIKE '%google%' OR name ILIKE '%microsoft%' OR name ILIKE '%apple%' OR name ILIKE '%amazon%' OR name ILIKE '%facebook%' OR name ILIKE '%meta%') 
                 AND moat_risk >= 3.0 THEN 'HIGH_RISK'
            WHEN desc_len > 5000 OR rating_count > 500000 THEN 'COMPLEX'
            WHEN low_complexity >= 2.0 AND moat_risk <= 2.0 AND desc_len <= 4000 THEN 'EASY_CLONE'
            ELSE 'MODERATE'
        END as clone_difficulty_calc,
        -- Revenue opportunity assessment  
        CASE
            WHEN rating_count >= 50000 AND rating_avg >= 4.0 AND rank <= 15 THEN 'HIGH_REVENUE'
            WHEN rating_count >= 1000 AND rating_avg >= 3.5 AND rank <= 25 THEN 'GOOD_REVENUE'
            WHEN rank <= 50 THEN 'MODEST_REVENUE'
            ELSE 'LOW_REVENUE'
        END as revenue_potential_calc
    FROM scout_results sr
    WHERE sr.generated_at = (
        SELECT MAX(generated_at) 
        FROM scout_results
    )
    -- Filter for micro-opportunity criteria:
    AND sr.total >= 1.8  -- Lower threshold for realistic opportunities
    AND sr.low_complexity >= 2.0  -- Must be reasonably simple to build
    AND sr.moat_risk <= 3.0  -- Avoid high brand/trademark risk
    AND NOT (
        (name ILIKE '%google%' AND moat_risk >= 4.0) OR
        (name ILIKE '%microsoft%' AND moat_risk >= 4.0) OR  
        (name ILIKE '%apple%' AND moat_risk >= 4.0)
    )
)
SELECT 
    *,
    clone_difficulty_calc as clone_difficulty,
    revenue_potential_calc as revenue_potential
FROM assessed_apps
ORDER BY 
    -- Prioritize by clone feasibility and revenue potential
    CASE clone_difficulty_calc
        WHEN 'EASY_CLONE' THEN 1
        WHEN 'MODERATE' THEN 2  
        WHEN 'COMPLEX' THEN 3
        ELSE 4
    END,
    total DESC,
    demand DESC;

-- Create view for today's top 10 per category - FIXED
CREATE OR REPLACE VIEW todays_opportunities AS
WITH ranked_today AS (
    SELECT 
        *,
        -- Add trending indicators
        CASE 
            WHEN category_rank <= 3 THEN '🥇 TOP 3'
            WHEN category_rank <= 5 THEN '🥈 TOP 5' 
            WHEN category_rank <= 10 THEN '🥉 TOP 10'
            ELSE '📊 OTHER'
        END as rank_tier
    FROM daily_rankings
    WHERE date = CURRENT_DATE
    AND category_rank <= 10  -- Top 10 per category
)
SELECT * FROM ranked_today
ORDER BY category, category_rank;

-- Create view for category leaders (top 3 per category with AI recommendations) - FIXED
CREATE OR REPLACE VIEW category_leaders AS
WITH leaders_today AS (
    SELECT 
        *,
        -- Priority level for tonight's build
        CASE 
            WHEN category_rank = 1 AND clone_difficulty = 'EASY_CLONE' THEN 'PRIORITY_1_TONIGHT'
            WHEN category_rank <= 2 AND clone_difficulty = 'EASY_CLONE' THEN 'PRIORITY_2_THIS_WEEK'
            WHEN category_rank <= 3 AND clone_difficulty IN ('EASY_CLONE', 'MODERATE') THEN 'PRIORITY_3_THIS_MONTH'
            ELSE 'PRIORITY_4_FUTURE'
        END as build_priority
    FROM daily_rankings
    WHERE date = CURRENT_DATE
    AND category_rank <= 3  -- Top 3 per category
)
SELECT * FROM leaders_today
ORDER BY category, category_rank;

-- Create view for trending analysis (compare with yesterday) - FIXED
CREATE OR REPLACE VIEW trending_analysis AS
WITH yesterday AS (
    SELECT app_id, category, category_rank as prev_rank
    FROM daily_rankings 
    WHERE date = CURRENT_DATE - INTERVAL '1 day'
),
today AS (
    SELECT app_id, category, category_rank as curr_rank, name
    FROM daily_rankings 
    WHERE date = CURRENT_DATE
)
SELECT 
    t.*,
    COALESCE(y.prev_rank, 999) as previous_rank,
    CASE 
        WHEN y.prev_rank IS NULL THEN 'NEW_ENTRY'
        WHEN t.curr_rank < y.prev_rank THEN 'TRENDING_UP'
        WHEN t.curr_rank > y.prev_rank THEN 'TRENDING_DOWN'
        ELSE 'STABLE'
    END as trend_direction,
    COALESCE(y.prev_rank - t.curr_rank, 0) as rank_change
FROM today t
LEFT JOIN yesterday y ON t.app_id = y.app_id AND t.category = y.category
ORDER BY t.category, t.curr_rank;

-- Create trigger for daily rankings updated_at
DROP TRIGGER IF EXISTS update_daily_rankings_updated_at ON daily_rankings;
CREATE TRIGGER update_daily_rankings_updated_at
    BEFORE UPDATE ON daily_rankings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to get daily brief data - FIXED
CREATE OR REPLACE FUNCTION get_daily_brief()
RETURNS TABLE(
    category TEXT,
    total_opportunities INTEGER,
    top_3_with_recommendations INTEGER,
    easy_clone_count INTEGER,
    avg_score NUMERIC(3,2),
    priority_tonight INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dr.category,
        COUNT(*)::INTEGER as total_opportunities,
        COUNT(CASE WHEN dr.category_rank <= 3 AND dr.ai_recommendation IS NOT NULL THEN 1 END)::INTEGER as top_3_with_recommendations,
        COUNT(CASE WHEN dr.clone_difficulty = 'EASY_CLONE' THEN 1 END)::INTEGER as easy_clone_count,
        AVG(dr.total)::NUMERIC(3,2) as avg_score,
        COUNT(CASE WHEN dr.category_rank = 1 AND dr.clone_difficulty = 'EASY_CLONE' THEN 1 END)::INTEGER as priority_tonight
    FROM daily_rankings dr
    WHERE dr.date = CURRENT_DATE
    GROUP BY dr.category
    ORDER BY priority_tonight DESC, easy_clone_count DESC, avg_score DESC;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON TABLE daily_rankings IS 'Daily top 10 apps per category with rankings and AI recommendations';
COMMENT ON COLUMN daily_rankings.category_rank IS 'Rank within category (1-10) for this date';
COMMENT ON COLUMN daily_rankings.ai_recommendation IS 'AI-generated improvement suggestion for cloning this app';
COMMENT ON COLUMN daily_rankings.clone_difficulty IS 'Assessment of how difficult this app would be to clone';

COMMENT ON VIEW todays_opportunities IS 'Today''s top 10 apps per category with ranking tiers';
COMMENT ON VIEW category_leaders IS 'Today''s top 3 apps per category with build priorities and AI recommendations';
COMMENT ON VIEW trending_analysis IS 'Trending analysis comparing today vs yesterday rankings';
COMMENT ON VIEW micro_opportunities IS 'Clone candidates from latest scout_results with difficulty assessment';

-- Test the schema setup
SELECT 'Daily automation schema setup complete! ✅' as status;

-- Show what views are available
SELECT 'Available views: micro_opportunities, todays_opportunities, category_leaders, trending_analysis' as views_created;