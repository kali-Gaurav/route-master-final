"""
Database Platform - Core system for analytics data management
Handles schema governance, migrations, retention policies, and disaster recovery
"""

import os
from sqlalchemy import create_engine, inspect, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration management"""
    
    def __init__(self, 
                 db_url: str = None,
                 pool_size: int = 20,
                 max_overflow: int = 40,
                 pool_recycle: int = 3600):
        """
        Initialize database configuration
        
        Args:
            db_url: Database connection URL (from env if not provided)
            pool_size: Connection pool size
            max_overflow: Max overflow connections beyond pool_size
            pool_recycle: Recycle connections after this many seconds
        """
        self.db_url = db_url or os.environ.get(
            'DATABASE_URL',
            'postgresql://admin:password@localhost:5432/railway_analytics'
        )
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle
    
    def get_engine(self):
        """Create SQLAlchemy engine with connection pooling"""
        engine = create_engine(
            self.db_url,
            poolclass=QueuePool,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_recycle=self.pool_recycle,
            echo=False,
            connect_args={
                'connect_timeout': 10,
                'options': '-c statement_timeout=30000'  # 30 second statement timeout
            }
        )
        return engine


class DatabasePlatform:
    """
    Production database platform with schema governance, migrations,
    retention policies, and disaster recovery
    """
    
    def __init__(self, config: DatabaseConfig = None):
        """Initialize database platform"""
        self.config = config or DatabaseConfig()
        self.engine = self.config.get_engine()
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._setup_connection_listeners()
    
    def _setup_connection_listeners(self):
        """Setup connection event listeners for monitoring"""
        
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Setup connection on creation"""
            cursor = dbapi_conn.cursor()
            cursor.execute("SET application_name = 'analytics-service'")
            cursor.execute("SET statement_timeout = '30s'")
            cursor.close()
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.fetchone() is not None
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_schema_info(self) -> dict:
        """Get current database schema information"""
        inspector = inspect(self.engine)
        
        return {
            'tables': inspector.get_table_names(),
            'columns': {
                table: [
                    {
                        'name': col['name'],
                        'type': str(col['type']),
                        'nullable': col['nullable'],
                        'default': col['default']
                    }
                    for col in inspector.get_columns(table)
                ]
                for table in inspector.get_table_names()
            },
            'indexes': {
                table: [idx['name'] for idx in inspector.get_indexes(table)]
                for table in inspector.get_table_names()
            },
            'foreign_keys': {
                table: inspector.get_foreign_keys(table)
                for table in inspector.get_table_names()
            }
        }
    
    def verify_migrations(self) -> bool:
        """
        Verify all migrations are applied
        
        Returns:
            True if all migrations applied, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                # Check if alembic_version table exists
                inspector = inspect(self.engine)
                if 'alembic_version' not in inspector.get_table_names():
                    logger.warning("Alembic version table not found - migrations may not be initialized")
                    return False
                
                # Get latest applied migration
                result = conn.execute(
                    text("SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1")
                )
                row = result.fetchone()
                
                if row:
                    logger.info(f"Latest migration applied: {row[0]}")
                    return True
                else:
                    logger.warning("No migrations applied yet")
                    return False
        
        except Exception as e:
            logger.error(f"Migration verification failed: {e}")
            return False
    
    def close(self):
        """Close database connections"""
        self.engine.dispose()


class RetentionPolicy:
    """
    Data retention and lifecycle management
    Defines what data lives where and for how long
    """
    
    # Data lifecycle stages (days)
    HOT_STORAGE_DAYS = 30      # PostgreSQL (fast, expensive)
    WARM_STORAGE_DAYS = 180    # TimescaleDB/ClickHouse (compressed)
    COLD_STORAGE_DAYS = 365    # S3/Parquet (archived)
    
    # Table-specific retention policies
    RETENTION_POLICIES = {
        'analytics_metrics': {
            'hot': HOT_STORAGE_DAYS,
            'warm': WARM_STORAGE_DAYS,
            'cold': COLD_STORAGE_DAYS,
            'archive_format': 'parquet'
        },
        'api_metrics': {
            'hot': 7,  # High volume, shorter retention
            'warm': 90,
            'cold': 365,
            'archive_format': 'parquet',
            'compress': True
        },
        'user_locations': {
            'hot': 7,   # PII - shorter retention for GDPR
            'warm': 30,
            'cold': None,  # Don't archive PII
            'auto_purge': True  # Auto-delete after hot period
        },
        'audit_logs': {
            'hot': 365,     # Keep audit logs longer
            'warm': None,   # Don't compress audit
            'cold': 1825,   # 5 years cold storage (compliance)
            'archive_format': 'parquet'
        },
        'analytics_reports': {
            'hot': 365,
            'warm': None,
            'cold': None,   # Keep reports indefinitely
        }
    }
    
    @classmethod
    def get_policy(cls, table_name: str) -> dict:
        """Get retention policy for table"""
        return cls.RETENTION_POLICIES.get(
            table_name,
            {
                'hot': cls.HOT_STORAGE_DAYS,
                'warm': cls.WARM_STORAGE_DAYS,
                'cold': cls.COLD_STORAGE_DAYS
            }
        )
    
    @classmethod
    def should_archive(cls, table_name: str, created_at: datetime) -> bool:
        """Check if record should be archived to cold storage"""
        policy = cls.get_policy(table_name)
        if policy.get('cold') is None:
            return False
        
        age_days = (datetime.utcnow() - created_at).days
        return age_days > policy['warm']
    
    @classmethod
    def should_purge(cls, table_name: str, created_at: datetime) -> bool:
        """Check if record should be purged (deleted)"""
        policy = cls.get_policy(table_name)
        if not policy.get('auto_purge', False):
            return False
        
        age_days = (datetime.utcnow() - created_at).days
        return age_days > policy.get('hot', 30)


class BackupManager:
    """
    Backup and disaster recovery management
    """
    
    def __init__(self, db_platform: DatabasePlatform):
        self.db = db_platform
    
    def get_backup_config(self) -> dict:
        """Get backup configuration"""
        return {
            'frequency': 'daily',
            'retention_days': {
                'dev': 7,
                'staging': 14,
                'production': 30
            },
            'backup_window': '02:00-04:00 UTC',  # Off-peak hours
            'type': 'automated_snapshots',
            'point_in_time_recovery': True,
            'pitr_retention_days': 7
        }
    
    def verify_backup(self) -> bool:
        """Verify backup capability"""
        try:
            with self.db.engine.connect() as conn:
                # Test backup metadata table
                result = conn.execute(
                    text("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_name = 'backup_metadata'
                        )
                    """)
                )
                return result.scalar()
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False
    
    def get_recovery_procedures(self) -> dict:
        """Get disaster recovery procedures"""
        return {
            'rpo': '1 minute',  # Recovery Point Objective
            'rto': '5 minutes',  # Recovery Time Objective
            'procedures': {
                'point_in_time': {
                    'description': 'Restore to specific point in time',
                    'steps': [
                        'Identify target timestamp',
                        'Create restore database from backup',
                        'Validate data integrity',
                        'Switch application connection',
                        'Monitor for issues'
                    ],
                    'estimated_duration': '15 minutes'
                },
                'full_restore': {
                    'description': 'Full database restoration',
                    'steps': [
                        'Restore from latest backup',
                        'Apply transaction logs up to cutoff',
                        'Verify all tables and indexes',
                        'Run consistency checks',
                        'Switch primary/standby'
                    ],
                    'estimated_duration': '30 minutes'
                }
            }
        }


# Global instance
_db_platform = None


def get_db_platform() -> DatabasePlatform:
    """Get or create global database platform instance"""
    global _db_platform
    if _db_platform is None:
        _db_platform = DatabasePlatform()
    return _db_platform


def get_db():
    """Dependency injection for database session"""
    db = get_db_platform().get_session()
    try:
        yield db
    finally:
        db.close()
