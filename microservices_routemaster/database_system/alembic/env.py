"""
Alembic migration environment script.
This handles both online and offline migrations with automatic schema detection.
"""

import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Load alembic configuration
config = context.config

# Set SQLAlchemy URL from environment
sqlalchemy_url = os.environ.get('DATABASE_URL', 'postgresql://localhost:5432/railway_analytics')
config.set_main_option('sqlalchemy.url', sqlalchemy_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your models here for 'autogenerate' support
try:
    from shared.models import Base
    target_metadata = Base.metadata
except ImportError:
    # Fallback if models not available
    target_metadata = None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (not connecting to database)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connecting to database)."""
    
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = os.environ.get('DATABASE_URL', configuration.get('sqlalchemy.url'))
    
    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
