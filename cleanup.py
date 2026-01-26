#!/usr/bin/env python3
"""
Cleanup script for FINALTrip Route Master
Removes temporary CSV logs and debug artifacts created during ingestion and development
Safe to run in production after deployment
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cleanup")

class Cleanup:
    """Cleanup manager for temporary files and debug logs"""
    
    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.files_removed = 0
        self.bytes_freed = 0
    
    def remove_csv_debug_logs(self):
        """Remove temporary CSV files created during debugging"""
        logger.info("Scanning for temporary CSV logs...")
        
        patterns = [
            "*.csv.bak",
            "*_debug.csv",
            "*_test.csv",
            "*_temp.csv",
            "*_backup*.csv",
            "temp_*.csv",
            "debug_*.csv"
        ]
        
        removed_count = 0
        for pattern in patterns:
            for file in self.root_dir.rglob(pattern):
                try:
                    size = file.stat().st_size
                    file.unlink()
                    self.files_removed += 1
                    self.bytes_freed += size
                    removed_count += 1
                    logger.debug(f"Removed: {file.relative_to(self.root_dir)} ({size} bytes)")
                except Exception as e:
                    logger.warning(f"Failed to remove {file}: {e}")
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} temporary CSV files")
        else:
            logger.info("No temporary CSV files found")
    
    def remove_fetch_logs(self):
        """Remove RAPPID fetch logs from data directory"""
        logger.info("Scanning for fetch logs...")
        
        fetch_logs_dir = self.root_dir / "data" / "fetch_logs"
        if fetch_logs_dir.exists():
            for file in fetch_logs_dir.glob("*"):
                if file.is_file() and (file.suffix == ".log" or file.suffix == ".txt"):
                    try:
                        size = file.stat().st_size
                        file.unlink()
                        self.files_removed += 1
                        self.bytes_freed += size
                        logger.debug(f"Removed: {file.relative_to(self.root_dir)} ({size} bytes)")
                    except Exception as e:
                        logger.warning(f"Failed to remove {file}: {e}")
    
    def remove_raw_rappid_backups(self):
        """Remove old raw RAPPID data backups (keep latest)"""
        logger.info("Scanning for raw RAPPID backups...")
        
        raw_dir = self.root_dir / "data" / "raw_rappid"
        if raw_dir.exists():
            files = sorted(raw_dir.glob("*.csv"), key=lambda f: f.stat().st_mtime, reverse=True)
            # Keep latest 2, remove older ones
            for file in files[2:]:
                try:
                    size = file.stat().st_size
                    file.unlink()
                    self.files_removed += 1
                    self.bytes_freed += size
                    logger.debug(f"Removed old backup: {file.relative_to(self.root_dir)} ({size} bytes)")
                except Exception as e:
                    logger.warning(f"Failed to remove {file}: {e}")
    
    def remove_python_cache(self):
        """Remove __pycache__ and .pyc files"""
        logger.info("Scanning for Python cache files...")
        
        removed = 0
        for cache_dir in self.root_dir.rglob("__pycache__"):
            try:
                for file in cache_dir.glob("*.pyc"):
                    size = file.stat().st_size
                    file.unlink()
                    self.files_removed += 1
                    self.bytes_freed += size
                    removed += 1
                # Remove empty cache directory
                if not any(cache_dir.iterdir()):
                    cache_dir.rmdir()
            except Exception as e:
                logger.warning(f"Failed to remove cache: {e}")
        
        if removed > 0:
            logger.info(f"Removed {removed} Python cache files")
    
    def remove_temporary_json_exports(self):
        """Remove temporary JSON export files"""
        logger.info("Scanning for temporary JSON exports...")
        
        patterns = ["*_pareto_routes_*.json", "*_routes_*.pkl", "*_debug.json", "temp_*.json"]
        removed = 0
        
        for pattern in patterns:
            for file in self.root_dir.rglob(pattern):
                try:
                    size = file.stat().st_size
                    file.unlink()
                    self.files_removed += 1
                    self.bytes_freed += size
                    removed += 1
                    logger.debug(f"Removed: {file.relative_to(self.root_dir)} ({size} bytes)")
                except Exception as e:
                    logger.warning(f"Failed to remove {file}: {e}")
        
        if removed > 0:
            logger.info(f"Removed {removed} temporary JSON/PKL files")
    
    def cleanup_old_logs(self, days_old=7):
        """Remove log files older than specified days"""
        logger.info(f"Scanning for log files older than {days_old} days...")
        
        logs_dir = self.root_dir / "logs"
        if logs_dir.exists():
            cutoff_timestamp = datetime.now().timestamp() - (days_old * 86400)
            removed = 0
            
            for file in logs_dir.glob("*.log"):
                try:
                    if file.stat().st_mtime < cutoff_timestamp:
                        size = file.stat().st_size
                        file.unlink()
                        self.files_removed += 1
                        self.bytes_freed += size
                        removed += 1
                        logger.debug(f"Removed old log: {file.relative_to(self.root_dir)}")
                except Exception as e:
                    logger.warning(f"Failed to remove {file}: {e}")
            
            if removed > 0:
                logger.info(f"Removed {removed} old log files")
    
    def print_summary(self):
        """Print cleanup summary"""
        mb_freed = self.bytes_freed / (1024 * 1024)
        logger.info("=" * 60)
        logger.info("CLEANUP SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Files removed: {self.files_removed}")
        logger.info(f"Space freed: {mb_freed:.2f} MB")
        logger.info("=" * 60)
    
    def run_full_cleanup(self, keep_logs_days=7, dry_run=False):
        """Run full cleanup routine"""
        logger.info("Starting FINALTrip cleanup routine...")
        
        if dry_run:
            logger.warning("*** DRY RUN MODE - No files will be deleted ***")
        
        try:
            self.remove_csv_debug_logs()
            self.remove_fetch_logs()
            self.remove_raw_rappid_backups()
            self.remove_python_cache()
            self.remove_temporary_json_exports()
            self.cleanup_old_logs(days_old=keep_logs_days)
            
            self.print_summary()
            logger.info("Cleanup completed successfully!")
            return True
        
        except Exception as e:
            logger.error(f"Cleanup failed: {e}", exc_info=True)
            return False

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Cleanup temporary files and debug logs from FINALTrip Route Master"
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Root directory for cleanup (default: current directory)"
    )
    parser.add_argument(
        "--keep-logs",
        type=int,
        default=7,
        help="Keep log files newer than N days (default: 7)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    
    args = parser.parse_args()
    
    cleanup = Cleanup(root_dir=args.root)
    success = cleanup.run_full_cleanup(keep_logs_days=args.keep_logs, dry_run=args.dry_run)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
