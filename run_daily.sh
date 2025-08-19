#!/bin/bash

# Trend Scout Daily Run Script
# This script sequences the daily collection, scoring, and publishing workflow

set -euo pipefail  # Exit on any error, undefined variables, or pipe failures

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$HOME/Library/Logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TEMP_DIR="$SCRIPT_DIR/temp"

# File paths
RAW_FILE="$TEMP_DIR/raw_$TIMESTAMP.json"
SCORED_FILE="$TEMP_DIR/scored_$TIMESTAMP.json"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_DIR/trendscout.log"
}

# Error handling function
handle_error() {
    local exit_code=$?
    log "ERROR: Daily run failed with exit code $exit_code"
    log "ERROR: Failed at line $1"
    
    # Cleanup temp files on error
    cleanup_temp_files
    
    exit $exit_code
}

# Cleanup function
cleanup_temp_files() {
    if [[ -d "$TEMP_DIR" ]]; then
        log "Cleaning up temporary files..."
        rm -rf "$TEMP_DIR"
    fi
}

# Trap errors
trap 'handle_error $LINENO' ERR

# Main execution
main() {
    log "========================================="
    log "Starting Trend Scout daily run"
    log "Timestamp: $TIMESTAMP"
    log "Script directory: $SCRIPT_DIR"
    log "========================================="
    
    # Create temp directory
    mkdir -p "$TEMP_DIR"
    mkdir -p "$LOG_DIR"
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Load environment variables if .env exists
    if [[ -f ".env" ]]; then
        log "Loading environment variables from .env"
        set -a  # Automatically export all variables
        source .env
        set +a
    else
        log "WARNING: No .env file found. Ensure SUPABASE_URL and SUPABASE_SERVICE_KEY are set."
    fi
    
    # Check if ts command is available
    if ! command -v ts &> /dev/null; then
        log "ERROR: 'ts' command not found. Is trendscout installed?"
        log "Try: pipx install -e . or pip install -e ."
        exit 1
    fi
    
    # Step 1: Collect raw data
    log "Step 1: Collecting raw app data..."
    ts collect \
        --countries "US,CA,GB,AU,DE" \
        --charts "free,paid" \
        --top 25 \
        --out "$RAW_FILE"
    
    if [[ ! -f "$RAW_FILE" ]]; then
        log "ERROR: Raw data collection failed - output file not created"
        exit 1
    fi
    
    raw_count=$(jq length "$RAW_FILE" 2>/dev/null || echo "0")
    log "Collected $raw_count raw records"
    
    if [[ "$raw_count" -eq 0 ]]; then
        log "ERROR: No raw data collected"
        exit 1
    fi
    
    # Step 2: Score the data
    log "Step 2: Scoring app data..."
    ts score "$RAW_FILE" --out "$SCORED_FILE"
    
    if [[ ! -f "$SCORED_FILE" ]]; then
        log "ERROR: Scoring failed - output file not created"
        exit 1
    fi
    
    scored_count=$(jq length "$SCORED_FILE" 2>/dev/null || echo "0")
    log "Scored $scored_count records"
    
    if [[ "$scored_count" -eq 0 ]]; then
        log "ERROR: No scored data generated"
        exit 1
    fi
    
    # Step 3: Publish to Supabase
    log "Step 3: Publishing to Supabase..."
    ts publish "$SCORED_FILE"
    
    log "Publishing completed successfully"
    
    # Step 4: Generate summary stats
    log "Step 4: Generating summary statistics..."
    
    # Calculate some basic stats using jq
    if command -v jq &> /dev/null; then
        avg_total=$(jq '[.[].total] | add / length | . * 100 | round / 100' "$SCORED_FILE" 2>/dev/null || echo "N/A")
        max_total=$(jq '[.[].total] | max | . * 100 | round / 100' "$SCORED_FILE" 2>/dev/null || echo "N/A")
        high_potential=$(jq '[.[] | select(.total >= 3.5)] | length' "$SCORED_FILE" 2>/dev/null || echo "N/A")
        
        log "Summary Statistics:"
        log "  - Total apps processed: $scored_count"
        log "  - Average total score: $avg_total"
        log "  - Maximum total score: $max_total" 
        log "  - High potential apps (≥3.5): $high_potential"
        
        # Log top 5 apps by total score
        log "Top 5 apps by total score:"
        jq -r '.[] | select(.total >= 3.0) | [.name, .total, .category, .country] | @tsv' "$SCORED_FILE" 2>/dev/null | \
            sort -k2 -nr | head -5 | while IFS=$'\t' read -r name total category country; do
            log "  - $name ($category, $country): $total"
        done 2>/dev/null || log "  Could not generate top apps list"
    fi
    
    # Step 5: Cleanup
    log "Step 5: Cleaning up..."
    cleanup_temp_files
    
    # Cache cleanup (keep last 30 days)
    log "Performing cache cleanup..."
    python3 -c "
from trendscout.store import SQLiteCache
cache = SQLiteCache()
cache.cleanup_old_data(days_to_keep=30)
" 2>/dev/null || log "Cache cleanup skipped (optional)"
    
    log "========================================="
    log "Daily run completed successfully!"
    log "Next run scheduled for tomorrow at 07:30"
    log "========================================="
}

# Health check function (can be called independently)
health_check() {
    log "Running health check..."
    ts doctor || {
        log "ERROR: Health check failed"
        exit 1
    }
}

# Handle command line arguments
case "${1:-}" in
    "health"|"check"|"doctor")
        health_check
        ;;
    "test"|"dry-run")
        log "Running in test mode (no publishing)..."
        # Run without publishing step
        main() {
            log "TEST MODE: Would run collect -> score -> publish sequence"
            ts doctor
        }
        main
        ;;
    *)
        main
        ;;
esac