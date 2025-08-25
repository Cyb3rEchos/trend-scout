#!/usr/bin/env python3
"""Local data storage with versioning for Trend Scout automation runs."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import shutil

logger = logging.getLogger(__name__)

class LocalDataStorage:
    """Manages local data storage with timestamp versioning."""
    
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.archive_path = self.base_path / "archive"
        self.base_path.mkdir(exist_ok=True)
        self.archive_path.mkdir(exist_ok=True)
    
    def create_run_directory(self, timestamp: Optional[datetime] = None) -> Path:
        """Create a timestamped directory for a data run."""
        if timestamp is None:
            timestamp = datetime.now()
        
        dir_name = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        run_path = self.base_path / dir_name
        run_path.mkdir(exist_ok=True)
        
        logger.info(f"📁 Created run directory: {run_path}")
        return run_path
    
    def save_run_data(self, run_path: Path, data: Dict) -> bool:
        """Save all data for a single automation run."""
        try:
            # Save scout results (raw collected data)
            if 'scout_results' in data:
                scout_file = run_path / "scout_results.json"
                with open(scout_file, 'w') as f:
                    json.dump(data['scout_results'], f, indent=2, default=str)
                logger.info(f"💾 Saved {len(data['scout_results'])} scout results")
            
            # Save trending selections
            if 'trending_selections' in data:
                trending_file = run_path / "trending_selections.json"
                with open(trending_file, 'w') as f:
                    json.dump(data['trending_selections'], f, indent=2, default=str)
                logger.info(f"💾 Saved {len(data['trending_selections'])} trending selections")
            
            # Save AI recommendations
            if 'ai_recommendations' in data:
                ai_file = run_path / "ai_recommendations.json"
                with open(ai_file, 'w') as f:
                    json.dump(data['ai_recommendations'], f, indent=2, default=str)
                logger.info(f"💾 Saved {len(data['ai_recommendations'])} AI recommendations")
            
            # Save run metadata
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'total_apps': len(data.get('scout_results', [])),
                'trending_apps': len(data.get('trending_selections', [])),
                'ai_recommendations': len(data.get('ai_recommendations', [])),
                'categories': list(set(app.get('category') for app in data.get('scout_results', []))),
                'automation_version': '1.0'
            }
            
            metadata_file = run_path / "run_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            logger.info(f"✅ Saved complete run data to {run_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save run data: {e}")
            return False
    
    def list_runs(self) -> List[Dict]:
        """List all stored runs with metadata."""
        runs = []
        
        for run_dir in self.base_path.iterdir():
            if run_dir.is_dir() and run_dir.name != "archive":
                try:
                    # Parse timestamp from directory name
                    timestamp = datetime.strptime(run_dir.name, "%Y-%m-%d_%H-%M-%S")
                    
                    # Load metadata if available
                    metadata_file = run_dir / "run_metadata.json"
                    metadata = {}
                    if metadata_file.exists():
                        with open(metadata_file) as f:
                            metadata = json.load(f)
                    
                    runs.append({
                        'directory': str(run_dir),
                        'timestamp': timestamp,
                        'timestamp_str': run_dir.name,
                        'metadata': metadata
                    })
                    
                except ValueError:
                    # Skip directories that don't match timestamp format
                    continue
        
        # Sort by timestamp (newest first)
        runs.sort(key=lambda x: x['timestamp'], reverse=True)
        return runs
    
    def get_latest_run(self) -> Optional[Dict]:
        """Get the most recent run data."""
        runs = self.list_runs()
        return runs[0] if runs else None
    
    def remove_run_by_timestamp(self, timestamp_str: str) -> bool:
        """Remove a specific run by timestamp string (YYYY-MM-DD_HH-MM-SS)."""
        run_path = self.base_path / timestamp_str
        
        if not run_path.exists():
            logger.error(f"❌ Run directory not found: {timestamp_str}")
            return False
        
        try:
            # Move to archive first (safer than immediate deletion)
            archive_path = self.archive_path / f"deleted_{timestamp_str}"
            shutil.move(str(run_path), str(archive_path))
            logger.info(f"🗑️ Moved run to archive: {timestamp_str}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to remove run {timestamp_str}: {e}")
            return False
    
    def cleanup_old_runs(self, keep_months: int = 6) -> int:
        """Remove runs older than specified months. Returns count of removed runs."""
        cutoff_date = datetime.now() - timedelta(days=keep_months * 30)
        runs = self.list_runs()
        
        removed_count = 0
        for run in runs:
            if run['timestamp'] < cutoff_date:
                if self.remove_run_by_timestamp(run['timestamp_str']):
                    removed_count += 1
        
        logger.info(f"🧹 Cleaned up {removed_count} old runs (older than {keep_months} months)")
        return removed_count
    
    def load_run_data(self, timestamp_str: str) -> Optional[Dict]:
        """Load all data from a specific run."""
        run_path = self.base_path / timestamp_str
        
        if not run_path.exists():
            logger.error(f"❌ Run directory not found: {timestamp_str}")
            return None
        
        try:
            data = {}
            
            # Load scout results
            scout_file = run_path / "scout_results.json"
            if scout_file.exists():
                with open(scout_file) as f:
                    data['scout_results'] = json.load(f)
            
            # Load trending selections
            trending_file = run_path / "trending_selections.json"
            if trending_file.exists():
                with open(trending_file) as f:
                    data['trending_selections'] = json.load(f)
            
            # Load AI recommendations
            ai_file = run_path / "ai_recommendations.json"
            if ai_file.exists():
                with open(ai_file) as f:
                    data['ai_recommendations'] = json.load(f)
            
            # Load metadata
            metadata_file = run_path / "run_metadata.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    data['metadata'] = json.load(f)
            
            logger.info(f"📂 Loaded run data from {timestamp_str}")
            return data
            
        except Exception as e:
            logger.error(f"❌ Failed to load run data from {timestamp_str}: {e}")
            return None
    
    def get_storage_summary(self) -> Dict:
        """Get summary of local storage usage."""
        runs = self.list_runs()
        
        total_size = 0
        for run_dir in self.base_path.iterdir():
            if run_dir.is_dir():
                for file_path in run_dir.rglob("*.json"):
                    total_size += file_path.stat().st_size
        
        return {
            'total_runs': len(runs),
            'latest_run': runs[0]['timestamp_str'] if runs else None,
            'oldest_run': runs[-1]['timestamp_str'] if runs else None,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'storage_path': str(self.base_path)
        }

# Convenience functions for integration with existing code
def save_automation_run(data: Dict, timestamp: Optional[datetime] = None) -> Optional[str]:
    """Save an automation run and return the timestamp string."""
    storage = LocalDataStorage()
    run_path = storage.create_run_directory(timestamp)
    
    if storage.save_run_data(run_path, data):
        return run_path.name
    return None

def remove_dataset_by_timestamp(timestamp_str: str) -> bool:
    """Remove a dataset by timestamp string."""
    storage = LocalDataStorage()
    return storage.remove_run_by_timestamp(timestamp_str)

def cleanup_old_datasets(keep_months: int = 6) -> int:
    """Clean up old datasets."""
    storage = LocalDataStorage()
    return storage.cleanup_old_runs(keep_months)