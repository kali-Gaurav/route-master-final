#!/usr/bin/env python3
"""
Migration script to populate PostgreSQL with railway data from SQLite.
"""

import sys
import os

# Add database module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'database'))

from database_system import DatabaseMigrator

def main():
    postgres_url = os.getenv('DATABASE_URL', 'postgresql://railway_user:secure_password@postgres:5432/railway_db')
    sqlite_db = '/app/data/production.db'

    print("Starting railway data migration...")
    print(f"Source: {sqlite_db}")
    print(f"Target: {postgres_url}")

    result = DatabaseMigrator.migrate(
        postgres_url=postgres_url,
        sqlite_db=sqlite_db
    )

    print("Migration result:", result)
    return result

if __name__ == "__main__":
    main()