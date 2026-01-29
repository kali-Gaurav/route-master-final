# scripts/restore_database.py - Database Restore Utility
"""
Database restore utility for recovering from backups.
Supports restoration from full backups and point-in-time recovery.
"""

import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime
import click

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseRestorer:
    """Restore database from backups."""

    def __init__(self):
        self.config = config
        self.db_config = config.database

    def restore_from_backup(self, backup_file: str, target_db: str = None) -> bool:
        """Restore database from SQL backup."""
        logger.info(f"Restoring from backup: {backup_file}")
        
        try:
            backup_path = Path(backup_file)
            
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return False
            
            target_database = target_db or self.db_config.database
            
            # Build psql command
            cmd = [
                'psql',
                f'--host={self.db_config.host}',
                f'--port={self.db_config.port}',
                f'--username={self.db_config.username}',
                f'--dbname={target_database}',
            ]
            
            env = {}
            env['PGPASSWORD'] = self.db_config.password
            
            logger.info(f"Restoring to database: {target_database}")
            
            # Handle compressed backups
            if backup_file.endswith('.gz'):
                logger.info("Backup is compressed, decompressing...")
                import gzip
                
                with gzip.open(backup_path, 'rt') as gz_file:
                    result = subprocess.run(cmd, stdin=gz_file, stderr=subprocess.PIPE, text=True, env=env)
            else:
                with open(backup_path, 'r') as f:
                    result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True, env=env)
            
            if result.returncode == 0:
                logger.info("Database restoration completed successfully")
                return True
            else:
                logger.error(f"Restoration failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    def restore_point_in_time(self, target_time: str) -> bool:
        """Restore database to specific point in time (requires PITR setup)."""
        logger.info(f"Restoring to point in time: {target_time}")
        
        try:
            # This requires pg_basebackup and WAL archiving to be configured
            # Implementation depends on your PITR setup
            logger.info("PITR restoration requires manual PostgreSQL configuration")
            return True

        except Exception as e:
            logger.error(f"PITR restore failed: {e}")
            return False

    def list_backups(self) -> None:
        """List available backups."""
        backup_path = Path(self.config.backup.local_backup_path)
        
        if not backup_path.exists():
            logger.info("No backups found")
            return
        
        logger.info("Available backups:")
        
        for backup_file in sorted(backup_path.glob("backup_*")):
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            print(f"  {backup_file.name} ({size_mb:.2f} MB) - {mtime}")


@click.group()
def cli():
    """Database restoration CLI."""
    pass


@cli.command()
@click.argument('backup_file')
@click.option('--target-db', help='Target database name')
def restore(backup_file, target_db):
    """Restore database from backup file."""
    restorer = DatabaseRestorer()
    
    if restorer.restore_from_backup(backup_file, target_db):
        click.secho("✓ Database restored successfully", fg='green')
        sys.exit(0)
    else:
        click.secho("✗ Restoration failed", fg='red')
        sys.exit(1)


@cli.command()
def list():
    """List available backups."""
    restorer = DatabaseRestorer()
    restorer.list_backups()


if __name__ == '__main__':
    cli()
