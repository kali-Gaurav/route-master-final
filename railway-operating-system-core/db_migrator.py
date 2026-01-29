# db_migrator.py
"""Database Migration Utilities"""

from database_system import DatabaseMigrator

def migrate_sqlite_to_postgres(postgres_url: str, sqlite_db: str = None, dry_run: bool = False, backup_first: bool = True):
    """Migrate data from SQLite to PostgreSQL."""
    return DatabaseMigrator.migrate(
        postgres_url=postgres_url,
        sqlite_db=sqlite_db,
        dry_run=dry_run,
        backup_first=backup_first
    )

def verify_migration(postgres_url: str, sqlite_db: str = None):
    """Verify migration consistency."""
    return DatabaseMigrator.verify(
        postgres_url=postgres_url,
        sqlite_db=sqlite_db
    )