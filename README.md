# Trend Scout

A production-grade Python 3.11 package for App Store trend analysis and scoring. Collects top 25 apps per category/country from Apple RSS feeds, enriches with page-level data, computes opportunity scores, and publishes to Supabase.

## Features

- **RSS Collection**: Fetches top 25 free/paid apps across 10 categories and 5 countries
- **App Enrichment**: Scrapes bundle ID, price, IAP status, ratings, and description length
- **Smart Scoring**: Combines demand, monetization, complexity, and moat risk metrics
- **Production Ready**: Caching, retries, logging, error handling, and idempotent operations
- **Automated Scheduling**: Daily runs via macOS launchd with comprehensive logging

## Quick Start

### 1. Installation

Using pipx (recommended):
```bash
pipx install -e .
```

Using pip:
```bash
pip install -e .
```

Using uv:
```bash
uv pip install -e .
```

### 2. Environment Setup

Create a `.env` file in the project root:
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

### 3. Database Setup

Run the SQL migration in your Supabase SQL editor:
```bash
cat supabase.sql
```

### 4. Health Check

Verify system configuration:
```bash
ts doctor
```

### 5. Manual Run

Complete workflow:
```bash
# Collect raw data
ts collect --countries US,CA,GB,AU,DE --charts free,paid --top 25 --out raw.json

# Score the data  
ts score raw.json --out scored.json

# Publish to Supabase
ts publish scored.json
```

## Automated Scheduling

### macOS launchd Setup

1. **Install the launch agent**:
   ```bash
   cp com.trendscout.daily.plist ~/Library/LaunchAgents/
   ```

2. **Load the agent**:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.trendscout.daily.plist
   ```

3. **Start immediately** (optional):
   ```bash
   launchctl start com.trendscout.daily
   ```

4. **Check status**:
   ```bash
   launchctl list | grep trendscout
   ```

### Schedule Details

- **Time**: Daily at 07:30 local time
- **Logs**: `~/Library/Logs/trendscout-daily.log`
- **Errors**: `~/Library/Logs/trendscout-daily-error.log`
- **Timeout**: 1 hour maximum runtime

### Manual Script Execution

Test the daily workflow:
```bash
# Full run
./run_daily.sh

# Health check only
./run_daily.sh health

# Test mode (no publishing)
./run_daily.sh test
```

## CLI Commands

### collect
Fetch app data from RSS feeds:
```bash
ts collect [options] --out OUTPUT_FILE

Options:
  --cats "Category1,Category2"    # Specific categories (default: all)
  --countries US,CA,GB,AU,DE      # Country codes
  --charts free,paid              # Chart types  
  --top 25                        # Apps per chart
```

### score
Enrich and score raw app data:
```bash
ts score INPUT_FILE --out OUTPUT_FILE
```

### publish
Upload scored data to Supabase:
```bash
ts publish INPUT_FILE
```

### backfill
Collect historical data:
```bash
ts backfill 2025-07-01..2025-08-01
```

### doctor
System health diagnostics:
```bash
ts doctor
```

## Data Flow

```
RSS Feeds → Raw JSON → App Pages → Scored JSON → Supabase
    ↓           ↓          ↓           ↓          ↓
  Collect    Cache     Scrape      Score     Publish
```

### Raw Data Schema
```json
{
  "category": "Utilities",
  "country": "US", 
  "chart": "free",
  "rank": 1,
  "app_id": "123456789",
  "name": "Example App",
  "rss_url": "https://...",
  "fetched_at": "2025-01-01T00:00:00Z"
}
```

### Scored Data Schema
```json
{
  // All raw fields plus:
  "bundle_id": "com.example.app",
  "price": 0.0,
  "has_iap": true,
  "rating_count": 1234,
  "rating_avg": 4.5,
  "desc_len": 500,
  "rank_delta7d": -5,
  "demand": 3.2,
  "monetization": 4.0, 
  "low_complexity": 2.5,
  "moat_risk": 1.8,
  "total": 3.47
}
```

## Scoring Algorithm

**Total Score = 0.35×Demand + 0.25×Monetization + 0.25×LowComplexity + 0.15×(5-MoatRisk)**

### Demand (1-5)
- Rank improvement over 7 days (primary)
- Rating volume (secondary)
- Review velocity (bonus)

### Monetization (1-5)  
- Free + No IAP: 1.0
- Free + IAP: 3.0-4.0
- Paid + No IAP: 3.0
- Paid + IAP: 5.0

### Low Complexity (1-5)
Keywords: counter, timer, widget, filter, scanner, QR, PDF, etc.
- Higher score = easier to build

### Moat Risk (1-5)
Keywords: official, Disney, Marvel, Snapchat, TikTok, etc.
- Higher score = more trademark risk
- Formula inverts this (5-MoatRisk) so lower risk gets higher weight

## Supabase Views

Access results through these pre-built views:

### latest_results
Most recent batch, ordered by total score:
```sql
SELECT * FROM latest_results WHERE total >= 3.5;
```

### trending_apps  
Apps with positive rank movement:
```sql
SELECT * FROM trending_apps LIMIT 10;
```

### high_potential_apps
High-scoring opportunities:
```sql
SELECT * FROM high_potential_apps WHERE category = 'Utilities';
```

## Configuration

### Categories
- Utilities
- Photo & Video
- Productivity  
- Health & Fitness
- Lifestyle
- Graphics & Design
- Music
- Education
- Finance
- Entertainment

### Countries
- US (United States)
- CA (Canada)
- GB (United Kingdom)
- AU (Australia)  
- DE (Germany)

### Rate Limiting
- RSS: 0.5s between requests
- Scraping: 1.0s between requests
- Automatic retries with exponential backoff

## Caching

Local SQLite cache (`~/.trendscout/cache.db`):
- **HTML Pages**: 24-hour TTL
- **Rank History**: Used for delta calculations
- **Auto-cleanup**: Retains 30 days of data

## Logging

Rotating log files in `~/Library/Logs/`:
- `trendscout.log` - Application logs (10MB max, 5 backups)
- `trendscout-daily.log` - Scheduled run output
- `trendscout-daily-error.log` - Scheduled run errors

Log levels: DEBUG, INFO, WARNING, ERROR

## Error Handling

- **Individual failures**: Continue processing, log errors
- **Partial results**: Save what succeeded
- **Idempotent publishing**: Safe to re-run same data
- **Comprehensive summary**: Reports failures at completion

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=trendscout --cov-report=html
```

Type checking:
```bash
mypy trendscout/
```

Code formatting:
```bash
black trendscout/ tests/
isort trendscout/ tests/
```

## Troubleshooting

### Common Issues

**"ts command not found"**
- Ensure package is installed: `pipx install -e .`
- Check PATH includes pipx bin directory

**"Supabase connection failed"**  
- Verify SUPABASE_URL and SUPABASE_SERVICE_KEY in .env
- Run `ts doctor` to diagnose

**"RSS endpoint unreachable"**
- Check internet connection
- Verify firewall/proxy settings
- Apple RSS feeds may have rate limits

**"Permission denied on log files"**
- Ensure `~/Library/Logs/` is writable
- Check launchd agent user permissions

### Debug Mode

Enable verbose logging:
```bash
ts --log-level DEBUG collect --out debug.json
```

### Manual Cache Management

Clear cache:
```bash
rm -rf ~/.trendscout/cache.db
```

View cache stats:
```bash
sqlite3 ~/.trendscout/cache.db ".tables"
sqlite3 ~/.trendscout/cache.db "SELECT COUNT(*) FROM app_ranks;"
```

## Development

### Project Structure
```
trendscout/
├── trendscout/          # Main package
│   ├── cli.py          # Command interface
│   ├── models.py       # Pydantic data models
│   ├── rss.py          # RSS fetching
│   ├── scrape.py       # App page scraping  
│   ├── score.py        # Scoring algorithms
│   └── store.py        # SQLite cache + Supabase
├── tests/              # Test suite
├── pyproject.toml      # Package configuration
├── supabase.sql        # Database schema
└── run_daily.sh        # Automation script
```

### Adding New Categories

1. Update `CATEGORY_MAPPINGS` in `rss.py`
2. Add to default config in `models.py`
3. Update README documentation

### Extending Scoring

Modify scoring components in `score.py`:
- `compute_demand_score()`
- `compute_monetization_score()`  
- `compute_low_complexity_score()`
- `compute_moat_risk_score()`

## License

MIT License - see LICENSE file for details.