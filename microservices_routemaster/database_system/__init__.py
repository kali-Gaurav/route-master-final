"""
Database Platform
Production-grade database system with schema governance, migrations, and disaster recovery
"""

from .platform import (
    DatabaseConfig,
    DatabasePlatform,
    RetentionPolicy,
    BackupManager,
    get_db_platform,
    get_db
)

from .migrations import (
    MigrationManager,
    SchemaDriftDetection,
    MigrationValidation
)

from .backup import BackupManager as BackupScript

__all__ = [
    'DatabaseConfig',
    'DatabasePlatform',
    'RetentionPolicy',
    'BackupManager',
    'MigrationManager',
    'SchemaDriftDetection',
    'MigrationValidation',
    'BackupScript',
    'get_db_platform',
    'get_db'
]

__version__ = '1.0.0'
