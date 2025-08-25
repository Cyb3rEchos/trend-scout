-- Trend Scout Supabase Database Setup
-- Run this in your Supabase SQL editor to create tables and views

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create scout_results table
CREATE TABLE IF NOT EXISTS scout_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    generated_at TIMESTAMPTZ NOT NULL,
    category TEXT NOT NULL,
    country TEXT NOT NULL,
    chart TEXT NOT NULL,
    rank INTEGER NOT NULL CHECK (rank > 0),
    app_id TEXT NOT NULL,
    bundle_id TEXT NOT NULL,
    name TEXT NOT NULL,
    price NUMERIC(10,2) NOT NULL DEFAULT 0.00 CHECK (price >= 0),
    has_iap BOOLEAN NOT NULL DEFAULT FALSE,
    rating_count INTEGER NOT NULL DEFAULT 0 CHECK (rating_count >= 0),
    rating_avg NUMERIC(3,2) NOT NULL DEFAULT 0.00 CHECK (rating_avg >= 0 AND rating_avg <= 5),
    desc_len INTEGER NOT NULL DEFAULT 0 CHECK (desc_len >= 0),
    rank_delta7d INTEGER,
    demand NUMERIC(3,2) NOT NULL CHECK (demand >= 1 AND demand <= 5),
    monetization NUMERIC(3,2) NOT NULL CHECK (monetization >= 1 AND monetization <= 5),
    low_complexity NUMERIC(3,2) NOT NULL CHECK (low_complexity >= 1 AND low_complexity <= 5),
    moat_risk NUMERIC(3,2) NOT NULL CHECK (moat_risk >= 1 AND moat_risk <= 5),
    total NUMERIC(5,2) NOT NULL CHECK (total >= 0 AND total <= 5),
    raw JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_scout_results_generated_at ON scout_results(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_scout_results_total ON scout_results(total DESC);
CREATE INDEX IF NOT EXISTS idx_scout_results_category ON scout_results(category);
CREATE INDEX IF NOT EXISTS idx_scout_results_country ON scout_results(country);
CREATE INDEX IF NOT EXISTS idx_scout_results_chart ON scout_results(chart);
CREATE INDEX IF NOT EXISTS idx_scout_results_app_id ON scout_results(app_id);

-- Unique constraint for idempotency (prevent duplicate records for same batch/app/country/chart)
CREATE UNIQUE INDEX IF NOT EXISTS idx_scout_results_unique 
ON scout_results(generated_at, app_id, country, chart);

-- Create composite index for common queries
CREATE INDEX IF NOT EXISTS idx_scout_results_composite 
ON scout_results(generated_at DESC, total DESC, category, country);

-- Create view for latest results
CREATE OR REPLACE VIEW latest_results AS
SELECT *
FROM scout_results
WHERE generated_at = (
    SELECT MAX(generated_at) 
    FROM scout_results
)
ORDER BY total DESC, category, country, chart, rank;

-- Create view for trending apps (apps with positive rank movement)
CREATE OR REPLACE VIEW trending_apps AS
SELECT *
FROM scout_results sr
WHERE sr.generated_at = (
    SELECT MAX(generated_at) 
    FROM scout_results
)
AND sr.rank_delta7d IS NOT NULL
AND sr.rank_delta7d < 0  -- Negative delta means rank improved
ORDER BY sr.rank_delta7d ASC, sr.total DESC;

-- Create view for high-potential apps (high total score)
CREATE OR REPLACE VIEW high_potential_apps AS
SELECT *
FROM scout_results sr
WHERE sr.generated_at = (
    SELECT MAX(generated_at) 
    FROM scout_results
)
AND sr.total >= 3.5
ORDER BY sr.total DESC, sr.demand DESC;

-- Create view for micro-opportunities (clone candidates for rapid app development)
CREATE OR REPLACE VIEW micro_opportunities AS
SELECT 
    *,
    -- Clone difficulty assessment
    CASE 
        WHEN (name ILIKE '%google%' OR name ILIKE '%microsoft%' OR name ILIKE '%apple%' OR name ILIKE '%amazon%' OR name ILIKE '%facebook%' OR name ILIKE '%meta%') 
             AND moat_risk >= 3.0 THEN 'HIGH_RISK'
        WHEN desc_len > 5000 OR rating_count > 500000 THEN 'COMPLEX'
        WHEN low_complexity >= 2.0 AND moat_risk <= 2.0 AND desc_len <= 4000 THEN 'EASY_CLONE'
        ELSE 'MODERATE'
    END as clone_difficulty,
    -- Revenue opportunity assessment  
    CASE
        WHEN rating_count >= 50000 AND rating_avg >= 4.0 AND rank <= 15 THEN 'HIGH_REVENUE'
        WHEN rating_count >= 1000 AND rating_avg >= 3.5 AND rank <= 25 THEN 'GOOD_REVENUE'
        WHEN rank <= 50 THEN 'MODEST_REVENUE'
        ELSE 'LOW_REVENUE'
    END as revenue_potential
FROM scout_results sr
WHERE sr.generated_at = (
    SELECT MAX(generated_at) 
    FROM scout_results
)
-- Filter for micro-opportunity criteria:
AND sr.total >= 1.8  -- Lower threshold for realistic opportunities
AND sr.low_complexity >= 2.0  -- Must be reasonably simple to build
AND sr.moat_risk <= 3.0  -- Avoid high brand/trademark risk
-- Exclude obvious big tech that would be impossible to compete with
AND NOT (
    (name ILIKE '%google%' AND moat_risk >= 4.0) OR
    (name ILIKE '%microsoft%' AND moat_risk >= 4.0) OR  
    (name ILIKE '%apple%' AND moat_risk >= 4.0)
)
ORDER BY 
    -- Prioritize by clone feasibility and revenue potential
    CASE clone_difficulty
        WHEN 'EASY_CLONE' THEN 1
        WHEN 'MODERATE' THEN 2  
        WHEN 'COMPLEX' THEN 3
        ELSE 4
    END,
    sr.total DESC,
    sr.demand DESC;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
DROP TRIGGER IF EXISTS update_scout_results_updated_at ON scout_results;
CREATE TRIGGER update_scout_results_updated_at
    BEFORE UPDATE ON scout_results
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to clean old data (optional - for data retention)
CREATE OR REPLACE FUNCTION clean_old_scout_results(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM scout_results 
    WHERE generated_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Add helpful comments
COMMENT ON TABLE scout_results IS 'App Store trend analysis results with scoring metrics';
COMMENT ON COLUMN scout_results.generated_at IS 'Timestamp when this batch of data was generated';
COMMENT ON COLUMN scout_results.rank_delta7d IS 'Change in rank over 7 days (negative = rank improved)';
COMMENT ON COLUMN scout_results.demand IS 'Demand score (1-5) based on rank movement and reviews';
COMMENT ON COLUMN scout_results.monetization IS 'Monetization score (1-5) based on pricing and IAP';
COMMENT ON COLUMN scout_results.low_complexity IS 'Low complexity score (1-5, higher = easier to build)';
COMMENT ON COLUMN scout_results.moat_risk IS 'Moat risk score (1-5, higher = more trademark/brand risk)';
COMMENT ON COLUMN scout_results.total IS 'Weighted total score combining all metrics';

COMMENT ON VIEW latest_results IS 'Most recent batch of results ordered by total score';
COMMENT ON VIEW trending_apps IS 'Apps with positive rank movement from latest batch';
COMMENT ON VIEW high_potential_apps IS 'High-scoring apps from latest batch (total >= 3.5)';

-- Create Row Level Security (RLS) policies if needed
-- Uncomment and modify as needed for your security requirements

-- ALTER TABLE scout_results ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY "Enable read access for authenticated users" ON scout_results
--     FOR SELECT USING (auth.role() = 'authenticated');

-- CREATE POLICY "Enable insert access for service role" ON scout_results
--     FOR INSERT WITH CHECK (auth.role() = 'service_role');

-- Create daily_rankings table for processed trending selections with AI
CREATE TABLE IF NOT EXISTS daily_rankings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL,
    category TEXT NOT NULL,
    category_rank INTEGER NOT NULL CHECK (category_rank >= 1 AND category_rank <= 10),
    potential_level TEXT NOT NULL CHECK (potential_level IN ('HIGH', 'MEDIUM', 'LOW')),
    app_name TEXT NOT NULL,
    bundle_id TEXT NOT NULL,
    clone_score NUMERIC(5,2) NOT NULL CHECK (clone_score >= 0),
    ai_recommendation JSONB,
    build_estimate TEXT,
    key_features JSONB,
    monetization_tips JSONB,
    market_gap TEXT,
    risk_factors JSONB,
    source_id UUID REFERENCES scout_results(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for daily_rankings
CREATE INDEX IF NOT EXISTS idx_daily_rankings_date ON daily_rankings(date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_rankings_category ON daily_rankings(category);
CREATE INDEX IF NOT EXISTS idx_daily_rankings_potential ON daily_rankings(potential_level);
CREATE INDEX IF NOT EXISTS idx_daily_rankings_score ON daily_rankings(clone_score DESC);

-- Unique constraint for daily rankings (one entry per app per day per category)
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_rankings_unique 
ON daily_rankings(date, category, category_rank);

-- Create view for today's trending apps
CREATE OR REPLACE VIEW todays_trending AS
SELECT *
FROM daily_rankings
WHERE date = CURRENT_DATE
ORDER BY category, category_rank;

-- Create view for high potential daily selections
CREATE OR REPLACE VIEW daily_high_potential AS
SELECT *
FROM daily_rankings
WHERE date = CURRENT_DATE
AND potential_level = 'HIGH'
ORDER BY clone_score DESC;

-- Add comments for daily_rankings
COMMENT ON TABLE daily_rankings IS 'Daily trending app selections with AI recommendations';
COMMENT ON COLUMN daily_rankings.category_rank IS 'Ranking within category (1-10, 1 is best)';
COMMENT ON COLUMN daily_rankings.potential_level IS 'Clone potential: HIGH (top 3), MEDIUM (4-7), LOW (8-10)';
COMMENT ON COLUMN daily_rankings.ai_recommendation IS 'Full AI analysis JSON from GPT-OSS-120B';
COMMENT ON COLUMN daily_rankings.source_id IS 'Reference to original scout_results record';

-- Example query to test the setup
-- SELECT 
--     category,
--     country,
--     COUNT(*) as app_count,
--     AVG(total) as avg_score,
--     MAX(generated_at) as latest_batch
-- FROM scout_results 
-- GROUP BY category, country
-- ORDER BY avg_score DESC;