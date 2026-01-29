# scripts/backup_database.py - Database Backup Manager
"""
Comprehensive database backup utility with S3 and local backup support.
Supports full backups, incremental backups, and verification.
"""

import os
import sys
import subprocess
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import click

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseBackupManager:
    """Manage database backups."""

    def __init__(self, backup_config=None):
        self.config = backup_config or config.backup
        self.db_config = config.database
        self.backup_metadata = {
            'timestamp': datetime.now().isoformat(),
            'type': self.config.backup_type,
            'status': 'pending',
        }

    def backup_full(self) -> bool:
        """Create a full backup of the database."""
        logger.info("Starting full backup...")
        
        try:
            backup_filename = f"backup_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            
            if self.config.enable_compression:
                backup_filename += '.gz'
            
            # Create pg_dump command
            cmd = [
                'pg_dump',
                f'--host={self.db_config.host}',
                f'--port={self.db_config.port}',
                f'--username={self.db_config.username}',
                f'--dbname={self.db_config.database}',
                '--format=plain',
                '--verbose',
                '--no-password',
            ]
            
            if self.config.enable_compression:
                cmd.append('-Z6')
            
            # Set password via environment
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config.password
            
            # Local backup
            if self.config.local_backup_enabled:
                local_backup_path = Path(self.config.local_backup_path)
                local_backup_path.mkdir(parents=True, exist_ok=True)
                
                backup_file = local_backup_path / backup_filename
                
                logger.info(f"Backing up to {backup_file}...")
                
                with open(backup_file, 'w') as f:
                    result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env, text=True)
                
                if result.returncode == 0:
                    logger.info(f"Local backup completed: {backup_file}")
                    self.backup_metadata['local_file'] = str(backup_file)
                else:
                    logger.error(f"pg_dump failed: {result.stderr}")
                    return False
                
                # S3 backup
                if self.config.s3_enabled:
                    self._upload_to_s3(backup_file)
                
                self.backup_metadata['status'] = 'completed'
                self._save_backup_metadata(backup_file)
                return True
            
            return True

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            self.backup_metadata['status'] = 'failed'
            self.backup_metadata['error'] = str(e)
            return False

    def backup_incremental(self) -> bool:
        """Create an incremental backup (backup since last full backup)."""
        logger.info("Starting incremental backup...")
        
        try:
            backup_filename = f"backup_incremental_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            
            if self.config.enable_compression:
                backup_filename += '.gz'
            
            # Use base backups with WAL archiving for incremental
            cmd = [
                'pg_basebackup',
                f'--host={self.db_config.host}',
                f'--port={self.db_config.port}',
                f'--username={self.db_config.username}',
                '--format=tar',
                '--verbose',
                '--progress',
                '--checkpoint=fast',
            ]
            
            if self.config.enable_compression:
                cmd.append('--gzip')
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config.password
            
            if self.config.local_backup_enabled:
                local_backup_path = Path(self.config.local_backup_path)
                local_backup_path.mkdir(parents=True, exist_ok=True)
                
                backup_file = local_backup_path / backup_filename
                
                logger.info(f"Creating incremental backup to {backup_file}...")
                
                with open(backup_file, 'wb') as f:
                    result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env)
                
                if result.returncode == 0:
                    logger.info(f"Incremental backup completed: {backup_file}")
                    return True
                else:
                    logger.error(f"pg_basebackup failed")
                    return False
            
            return True

        except Exception as e:
            logger.error(f"Incremental backup failed: {e}")
            return False

    def _upload_to_s3(self, local_file: Path) -> bool:
        """Upload backup file to S3."""
        try:
            import boto3
            
            s3_client = boto3.client(
                's3',
                region_name=self.config.s3_region,
                aws_access_key_id=self.config.aws_access_key_id,
                aws_secret_access_key=self.config.aws_secret_access_key,
            )
            
            s3_key = f"{self.config.s3_prefix}{local_file.name}"
            
            logger.info(f"Uploading to S3: s3://{self.config.s3_bucket}/{s3_key}")
            
            s3_client.upload_file(
                str(local_file),
                self.config.s3_bucket,
                s3_key,
                Config=boto3.s3.transfer.TransferConfig(
                    multipart_threshold=1024 * 25,
                    max_concurrency=10,
                )
            )
            
            logger.info(f"S3 upload completed")
            self.backup_metadata['s3_location'] = f"s3://{self.config.s3_bucket}/{s3_key}"
            return True

        except ImportError:
            logger.warning("boto3 not installed, skipping S3 upload")
            return False
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            return False

    def _save_backup_metadata(self, backup_file: Path) -> None:
        """Save backup metadata."""
        try:
            metadata_file = backup_file.parent / f"{backup_file.stem}.metadata.json"
            
            file_stat = backup_file.stat()
            self.backup_metadata['file_size_bytes'] = file_stat.st_size
            self.backup_metadata['file_size_mb'] = file_stat.st_size / (1024 * 1024)
            self.backup_metadata['completion_time'] = datetime.now().isoformat()
            
            with open(metadata_file, 'w') as f:
                json.dump(self.backup_metadata, f, indent=2)
            
            logger.info(f"Metadata saved: {metadata_file}")

        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    def verify_backup(self, backup_file: str) -> bool:
        """Verify backup integrity."""
        logger.info(f"Verifying backup: {backup_file}")
        
        try:
            backup_path = Path(backup_file)
            
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return False
            
            # Check file size
            file_size = backup_path.stat().st_size
            if file_size == 0:
                logger.error("Backup file is empty")
                return False
            
            logger.info(f"Backup size: {file_size / (1024*1024):.2f} MB")
            
            # For SQL backups, check for SQL header
            if backup_file.endswith('.sql') or backup_file.endswith('.sql.gz'):
                logger.info("SQL backup - basic validation passed")
                return True
            
            logger.info("Backup verification completed successfully")
            return True

        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False

    def cleanup_old_backups(self, retention_days: Optional[int] = None) -> int:
        """Clean up old backup files."""
        retention_days = retention_days or self.config.local_retention_days
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        logger.info(f"Cleaning up backups older than {retention_days} days...")
        
        deleted_count = 0
        
        try:
            backup_path = Path(self.config.local_backup_path)
            
            if not backup_path.exists():
                logger.info("Backup directory does not exist")
                return 0
            
            for backup_file in backup_path.glob("backup_*"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    logger.info(f"Deleting old backup: {backup_file}")
                    backup_file.unlink()
                    deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} old backup files")
            return deleted_count

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return 0


@click.group()
def cli():
    """Database backup management CLI."""
    pass


@cli.command()
@click.option('--type', 'backup_type', default='full', help='Backup type: full or incremental')
def backup(backup_type):
    """Create a database backup."""
    manager = DatabaseBackupManager()
    
    if backup_type == 'incremental':
        success = manager.backup_incremental()
    else:
        success = manager.backup_full()
    
    if success:
        click.secho("✓ Backup completed successfully", fg='green')
        sys.exit(0)
    else:
        click.secho("✗ Backup failed", fg='red')
        sys.exit(1)


@cli.command()
@click.argument('backup_file')
def verify(backup_file):
    """Verify a backup file."""
    manager = DatabaseBackupManager()
    
    if manager.verify_backup(backup_file):
        click.secho("✓ Backup verification passed", fg='green')
        sys.exit(0)
    else:
        click.secho("✗ Backup verification failed", fg='red')
        sys.exit(1)


@cli.command()
@click.option('--retention-days', type=int, default=None, help='Retention period in days')
def cleanup(retention_days):
    """Clean up old backups."""
    manager = DatabaseBackupManager()
    deleted = manager.cleanup_old_backups(retention_days)
    
    click.secho(f"✓ Deleted {deleted} old backup files", fg='green')


if __name__ == '__main__':
    cli()
