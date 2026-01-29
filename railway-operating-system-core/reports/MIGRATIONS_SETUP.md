# Alembic Configuration File

This placeholder indicates that Alembic has been initialized for database migrations.

## Quick Start

```bash
# Install alembic and dependencies
pip install alembic sqlalchemy psycopg2-binary

# Initialize migrations folder (if not already done)
alembic init migrations

# Update migrations/env.py to use SQLAlchemy models from schema.py
# Then create initial migration:
alembic revision --autogenerate -m "Initial schema migration"

# Apply migrations to PostgreSQL
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

## Configuration

Set the database URL in environment variable or in `migrations/alembic.ini`:

```ini
sqlalchemy.url = postgresql://user:password@localhost:5432/railway_os
```

Or export environment variable:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/railway_os"
```

## Files Structure

```
migrations/
  ├── alembic.ini           # Alembic configuration
  ├── env.py                # Migration environment
  ├── script.py.mako        # Template for new migrations
  └── versions/             # Individual migration files
      ├── 001_initial_schema.py
      └── ...
```

## Usage

1. Define schema changes in `schema.py`
2. Generate migration: `alembic revision --autogenerate -m "Description"`
3. Review generated migration file
4. Apply: `alembic upgrade head`
5. Rollback if needed: `alembic downgrade -1`

---

See `schema.py` for ORM model definitions that Alembic will track.
