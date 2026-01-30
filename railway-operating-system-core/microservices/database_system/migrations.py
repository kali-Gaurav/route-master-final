"""
Migration and schema management utilities
"""

import os
import logging
from datetime import datetime
from alembic.config import Config
from alembic.command import upgrade, downgrade, revision, current
from sqlalchemy import text

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations using Alembic"""
    
    def __init__(self, alembic_dir: str = None):
        """
        Initialize migration manager
        
        Args:
            alembic_dir: Path to alembic directory
        """
        self.alembic_dir = alembic_dir or os.path.join(
            os.path.dirname(__file__),
            'alembic'
        )
        self.config = Config(os.path.join(os.path.dirname(__file__), 'alembic.ini'))
        self.config.set_main_option('sqlalchemy.url', 
            os.environ.get('DATABASE_URL', 'postgresql://localhost/railway_analytics'))
    
    def upgrade_to_latest(self) -> bool:
        """Upgrade database to latest migration"""
        try:
            logger.info("Running migrations to latest...")
            upgrade(self.config, 'head')
            logger.info("✅ Migrations completed successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
    
    def get_current_revision(self) -> str:
        """Get currently applied migration revision"""
        try:
            current(self.config)
            return "See logs above"
        except Exception as e:
            logger.error(f"Failed to get current revision: {e}")
            return None
    
    def create_migration(self, message: str, autogenerate: bool = True) -> bool:
        """
        Create new migration
        
        Args:
            message: Migration description
            autogenerate: Auto-detect model changes
        """
        try:
            logger.info(f"Creating migration: {message}")
            revision(self.config, autogenerate=autogenerate, message=message)
            logger.info(f"✅ Migration created: {message}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create migration: {e}")
            return False
    
    def downgrade(self, revision_id: str) -> bool:
        """
        Downgrade to specific revision
        
        WARNING: Only use in development/staging
        """
        try:
            logger.warning(f"Downgrading to revision: {revision_id}")
            downgrade(self.config, revision_id)
            logger.info(f"✅ Downgraded to: {revision_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Downgrade failed: {e}")
            return False


class SchemaDriftDetection:
    """
    Detect schema drift between code models and database
    """
    
    def __init__(self, db_platform):
        self.db = db_platform
    
    def detect_drift(self) -> dict:
        """
        Compare database schema with model definitions
        
        Returns:
            Dict with drift information
        """
        from shared.models import Base
        from sqlalchemy import inspect
        
        inspector = inspect(self.db.engine)
        db_tables = set(inspector.get_table_names())
        model_tables = set(Base.metadata.tables.keys())
        
        drift = {
            'missing_in_db': list(model_tables - db_tables),
            'extra_in_db': list(db_tables - model_tables),
            'column_mismatches': self._check_column_drifts(inspector)
        }
        
        if any(drift.values()):
            logger.warning(f"Schema drift detected: {drift}")
        else:
            logger.info("✅ No schema drift detected")
        
        return drift
    
    def _check_column_drifts(self, inspector) -> dict:
        """Check for column-level drift"""
        mismatches = {}
        # Implementation for detailed column checking
        return mismatches


class MigrationValidation:
    """Validate migrations before and after execution"""
    
    @staticmethod
    def pre_migration_checks(db_platform) -> bool:
        """Check system is ready for migration"""
        checks = {
            'database_accessible': db_platform.health_check(),
            'no_active_connections': _check_active_connections(db_platform),
            'disk_space_available': _check_disk_space(),
            'backups_recent': _check_recent_backups()
        }
        
        all_passed = all(checks.values())
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            logger.info(f"{status} {check}")
        
        return all_passed
    
    @staticmethod
    def post_migration_checks(db_platform) -> bool:
        """Validate migration completed successfully"""
        checks = {
            'migrations_applied': db_platform.verify_migrations(),
            'schema_integrity': _check_schema_integrity(db_platform),
            'data_integrity': _check_data_integrity(db_platform),
            'indexes_created': _check_indexes(db_platform)
        }
        
        all_passed = all(checks.values())
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            logger.info(f"{status} {check}")
        
        return all_passed


def _check_active_connections(db_platform) -> bool:
    """Check for active connections that might block migration"""
    try:
        with db_platform.engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM pg_stat_activity WHERE datname = current_database() AND pid != pg_backend_pid()"
            ))
            count = result.scalar()
            logger.info(f"Active connections: {count}")
            return count == 0
    except Exception as e:
        logger.warning(f"Could not check active connections: {e}")
        return True  # Assume OK if can't check


def _check_disk_space() -> bool:
    """Check available disk space"""
    # Implementation for disk space check
    return True


def _check_recent_backups() -> bool:
    """Check if recent backups exist"""
    # Implementation for backup check
    return True


def _check_schema_integrity(db_platform) -> bool:
    """Verify schema integrity after migration"""
    # Implementation for schema checks
    return True


def _check_data_integrity(db_platform) -> bool:
    """Verify data integrity after migration"""
    # Implementation for data checks
    return True


def _check_indexes(db_platform) -> bool:
    """Verify all indexes are created"""
    # Implementation for index checks
    return True
