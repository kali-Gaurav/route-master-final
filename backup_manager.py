"""
Backup & Disaster Recovery Manager

Comprehensive backup strategy:
- Daily automated backups
- 30-day retention policy
- Redundant storage
- Recovery testing
- Backup verification
"""

import shutil
import sqlite3
import gzip
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib

from config import DB_SQLITE_PATH, BACKUP_CONFIG, LOGS_DIR
from logger import logger, LoggerFactory, audit_logger

backup_logger = LoggerFactory.get_logger("backup_manager")


class BackupManager:
    """Manage database and data backups"""
    
    def __init__(self):
        self.logger = LoggerFactory.get_logger("backup_manager")
        self.backup_dir = BACKUP_CONFIG["backup_location"]
        self.retention_days = BACKUP_CONFIG["retention_days"]
        self.compression_enabled = BACKUP_CONFIG["compression_enabled"]
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, source_path: Path = DB_SQLITE_PATH) -> Optional[Path]:
        """
        Create backup of database
        
        Args:
            source_path: Path to database file
        
        Returns:
            Path to backup file, or None if failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if self.compression_enabled:
                backup_name = f"train_master_{timestamp}.db.gz"
                backup_path = self.backup_dir / backup_name
                
                # Compress while copying
                with open(source_path, 'rb') as f_in:
                    with gzip.open(backup_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            
            else:
                backup_name = f"train_master_{timestamp}.db"
                backup_path = self.backup_dir / backup_name
                shutil.copy2(source_path, backup_path)
            
            # Create backup metadata
            metadata = {
                "timestamp": datetime.utcnow().isoformat(),
                "source": str(source_path),
                "backup_file": str(backup_path),
                "compressed": self.compression_enabled,
                "file_size_bytes": backup_path.stat().st_size,
                "checksum": self._calculate_checksum(backup_path)
            }
            
            # Save metadata
            metadata_path = self.backup_dir / f"{backup_name}.meta.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(
                f"Backup created successfully",
                extra={
                    "backup_file": backup_path.name,
                    "size_mb": metadata["file_size_bytes"] / (1024 * 1024),
                    "compressed": self.compression_enabled
                }
            )
            
            # Log audit event
            audit_logger.log_data_modification(
                operation="backup_create",
                table="database",
                records_affected=1,
                changes={"backup_file": backup_path.name}
            )
            
            return backup_path
        
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}", exc_info=True)
            audit_logger.log_error_event(
                error_type="BACKUP_FAILURE",
                message=f"Failed to create backup: {str(e)}",
                context={"source": str(source_path)},
                severity="CRITICAL"
            )
            return None
    
    def cleanup_old_backups(self) -> Tuple[int, int]:
        """
        Remove backups older than retention period
        
        Returns:
            (backups_deleted, backups_kept)
        """
        try:
            now = datetime.now()
            deleted = 0
            kept = 0
            
            for backup_file in self.backup_dir.glob("train_master_*.db*"):
                # Skip metadata files
                if backup_file.name.endswith(".meta.json"):
                    continue
                
                # Get file modification time
                mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                age_days = (now - mtime).days
                
                if age_days > self.retention_days:
                    try:
                        backup_file.unlink()
                        
                        # Also delete metadata file
                        metadata_file = self.backup_dir / f"{backup_file.name}.meta.json"
                        if metadata_file.exists():
                            metadata_file.unlink()
                        
                        deleted += 1
                        self.logger.info(f"Deleted old backup: {backup_file.name}")
                    
                    except Exception as e:
                        self.logger.error(f"Failed to delete {backup_file}: {e}")
                
                else:
                    kept += 1
            
            self.logger.info(
                f"Backup cleanup completed",
                extra={"deleted": deleted, "kept": kept}
            )
            
            return deleted, kept
        
        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {e}", exc_info=True)
            return 0, 0
    
    def list_backups(self) -> List[Dict]:
        """
        List all available backups
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob("train_master_*.db*"), reverse=True):
            if backup_file.name.endswith(".meta.json"):
                continue
            
            try:
                stat = backup_file.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime)
                
                # Try to load metadata
                metadata_file = self.backup_dir / f"{backup_file.name}.meta.json"
                metadata = {}
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                
                backup_info = {
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "size_mb": stat.st_size / (1024 * 1024),
                    "created": mtime.isoformat(),
                    "age_days": (datetime.now() - mtime).days,
                    "compressed": backup_file.name.endswith(".gz"),
                    "metadata": metadata
                }
                
                backups.append(backup_info)
            
            except Exception as e:
                self.logger.warning(f"Error reading backup info for {backup_file}: {e}")
        
        return backups
    
    def verify_backup(self, backup_path: Path) -> bool:
        """
        Verify backup integrity
        
        Args:
            backup_path: Path to backup file
        
        Returns:
            True if backup is valid
        """
        try:
            # Check file exists
            if not backup_path.exists():
                self.logger.warning(f"Backup file not found: {backup_path}")
                return False
            
            # Load metadata
            metadata_file = self.backup_dir / f"{backup_path.name}.meta.json"
            if not metadata_file.exists():
                self.logger.warning(f"Metadata file not found for {backup_path}")
                return False
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Verify checksum
            current_checksum = self._calculate_checksum(backup_path)
            stored_checksum = metadata.get("checksum")
            
            if current_checksum != stored_checksum:
                self.logger.error(
                    f"Checksum mismatch for {backup_path}",
                    extra={
                        "stored": stored_checksum,
                        "current": current_checksum
                    }
                )
                return False
            
            # Try to open as database (if not compressed)
            if not backup_path.name.endswith(".gz"):
                try:
                    conn = sqlite3.connect(str(backup_path))
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    conn.close()
                    
                    if not tables:
                        self.logger.warning(f"Backup appears to be empty: {backup_path}")
                        return False
                except Exception as e:
                    self.logger.error(f"Failed to open backup as database: {e}")
                    return False
            
            self.logger.info(f"Backup verification successful: {backup_path.name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Backup verification failed: {e}", exc_info=True)
            return False
    
    def restore_backup(self, backup_path: Path,
                      restore_path: Path = DB_SQLITE_PATH) -> bool:
        """
        Restore database from backup
        
        Args:
            backup_path: Path to backup file
            restore_path: Path to restore to
        
        Returns:
            True if successful
        """
        try:
            # Verify backup first
            if not self.verify_backup(backup_path):
                self.logger.error("Backup verification failed - refusing to restore")
                return False
            
            # Create safety backup of current database
            if restore_path.exists():
                safety_backup = self.backup_dir / f"pre_restore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(restore_path, safety_backup)
                self.logger.info(f"Created safety backup: {safety_backup}")
            
            # Decompress if needed
            if backup_path.name.endswith(".gz"):
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp_path = Path(tmp.name)
                
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(tmp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                source = tmp_path
            else:
                source = backup_path
            
            # Restore
            shutil.copy2(source, restore_path)
            
            if backup_path.name.endswith(".gz"):
                tmp_path.unlink()
            
            self.logger.info(
                f"Database restored successfully",
                extra={"from": backup_path.name, "to": str(restore_path)}
            )
            
            audit_logger.log_error_event(
                error_type="BACKUP_RESTORE",
                message="Database restored from backup",
                context={"backup_file": backup_path.name, "restore_path": str(restore_path)},
                severity="WARNING"
            )
            
            return True
        
        except Exception as e:
            self.logger.error(f"Backup restoration failed: {e}", exc_info=True)
            return False
    
    def _calculate_checksum(self, filepath: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256 = hashlib.sha256()
        
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def export_backup_list(self, output_path: Optional[Path] = None) -> str:
        """Export list of backups to text file"""
        backups = self.list_backups()
        
        report = f"""
BACKUP STATUS REPORT
====================
Generated: {datetime.now().isoformat()}

Configuration:
  Retention Days: {self.retention_days}
  Compression Enabled: {self.compression_enabled}
  Backup Location: {self.backup_dir}

Backups ({len(backups)} total):
"""
        
        for i, backup in enumerate(backups, 1):
            report += f"\n{i}. {backup['filename']}\n"
            report += f"   Size: {backup['size_mb']:.2f} MB\n"
            report += f"   Created: {backup['created']}\n"
            report += f"   Age: {backup['age_days']} days\n"
            report += f"   Compressed: {backup['compressed']}\n"
        
        if output_path is None:
            output_path = self.backup_dir / "backup_list.txt"
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        return report


# Global backup manager instance
backup_manager = BackupManager()
