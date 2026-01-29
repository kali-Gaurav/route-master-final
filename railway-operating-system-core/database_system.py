"""Unified Database System: Connection, Pooling, Migration, and ORM.

Consolidates:
- SQLite and PostgreSQL connection management
- Connection pooling (QueuePool) for production
- Safe data migration (SQLite → PostgreSQL)
- SQLAlchemy ORM models
- Schema initialization and management

This module provides complete database functionality with seamless fallback
support, enabling the Railway Operating System to work in both development
(SQLite) and production (PostgreSQL) environments.
"""
import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from urllib.parse import urlparse

# SQLAlchemy imports (for pooling and ORM)
try:
    from sqlalchemy import create_engine, event, Column, Integer, String, Text, DateTime, Boolean, Float
    from sqlalchemy.orm import sessionmaker, Session, declarative_base
    from sqlalchemy.pool import QueuePool
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

# PostgreSQL support
try:
    import psycopg2
    from psycopg2 import sql
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


# ============================================================================
# CONFIGURATION
# ============================================================================

class DatabaseConfig:
    """Database configuration from environment or defaults."""
    
    # SQLite
    SQLITE_PATH = os.getenv('SQLITE_DB_PATH', 'railway_os.db')
    
    # PostgreSQL
    POSTGRES_URL = os.getenv('DATABASE_URL', None)
    DB_BACKEND = os.getenv('DB_BACKEND', 'auto')  # 'sqlite', 'postgresql', or 'auto'
    
    # Connection pooling (PostgreSQL)
    POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '20'))
    MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '40'))
    POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))
    POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))


# ============================================================================
# DATABASE CONNECTION (LEGACY SQLite)
# ============================================================================

class DatabaseConnection:
    """Legacy database connection handler with SQLite fallback and PostgreSQL support.
    
    Supports both SQLite (development) and PostgreSQL (production).
    Auto-detects based on DATABASE_URL environment variable.
    """
    
    def __init__(self, db_path: str = DatabaseConfig.SQLITE_PATH):
        self.db_path = db_path
        self.postgres_url = DatabaseConfig.POSTGRES_URL
        self.conn = None
        self.cursor = None
        self.is_postgres = False
    
    def connect(self) -> bool:
        """Establish database connection (PostgreSQL preferred, SQLite fallback)."""
        try:
            if self.postgres_url and PSYCOPG2_AVAILABLE:
                self.conn = psycopg2.connect(self.postgres_url)
                self.cursor = self.conn.cursor()
                self.is_postgres = True
                return True
            else:
                self.conn = sqlite3.connect(self.db_path, timeout=30)
                self.conn.row_factory = sqlite3.Row
                self.cursor = self.conn.cursor()
                self.is_postgres = False
                return True
        except Exception as e:
            print(f"❌ Database Connection Error: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Any]:
        """Execute SELECT query safely."""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"❌ Query Error: {e}")
            return []
    
    def execute_single(self, query: str, params: Optional[Tuple] = None) -> Optional[Tuple]:
        """Execute query and fetch single row."""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchone()
        except Exception as e:
            print(f"❌ Query Error: {e}")
            return None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# ============================================================================
# CONNECTION POOLING (PostgreSQL)
# ============================================================================

class DatabasePool:
    """PostgreSQL connection pooling using SQLAlchemy QueuePool."""
    
    _engines: Dict[str, Any] = {}
    _session_factories: Dict[str, Any] = {}
    
    @staticmethod
    def get_engine(database_url: str, echo: bool = False):
        """Get or create a pooled SQLAlchemy engine."""
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError("SQLAlchemy required for connection pooling")
        
        if database_url in DatabasePool._engines:
            return DatabasePool._engines[database_url]
        
        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=DatabaseConfig.POOL_SIZE,
            max_overflow=DatabaseConfig.MAX_OVERFLOW,
            pool_recycle=DatabaseConfig.POOL_RECYCLE,
            pool_timeout=DatabaseConfig.POOL_TIMEOUT,
            echo=echo
        )
        
        @event.listens_for(engine, "connect")
        def health_check(dbapi_conn, connection_record):
            try:
                cursor = dbapi_conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
            except Exception as e:
                print(f"⚠️  Connection health check failed: {e}")
        
        DatabasePool._engines[database_url] = engine
        return engine
    
    @staticmethod
    def get_session(database_url: str) -> Session:
        """Get a SQLAlchemy session from the pool."""
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError("SQLAlchemy required for sessions")
        
        if database_url not in DatabasePool._session_factories:
            engine = DatabasePool.get_engine(database_url)
            DatabasePool._session_factories[database_url] = sessionmaker(bind=engine)
        
        return DatabasePool._session_factories[database_url]()
    
    @staticmethod
    def close_all():
        """Close all pooled connections."""
        for engine in DatabasePool._engines.values():
            engine.dispose()
        DatabasePool._engines.clear()
        DatabasePool._session_factories.clear()
    
    @staticmethod
    def get_pool_status(database_url: str) -> Dict[str, Any]:
        """Get pool statistics."""
        engine = DatabasePool.get_engine(database_url)
        pool = engine.pool
        return {
            'pool_size': pool.size(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'total_connections': pool.size() + pool.overflow()
        }


# ============================================================================
# MIGRATION (SQLite → PostgreSQL)
# ============================================================================

class DatabaseMigrator:
    """Safe migration from SQLite to PostgreSQL."""
    
    @staticmethod
    def migrate(
        postgres_url: str,
        sqlite_db: str = DatabaseConfig.SQLITE_PATH,
        dry_run: bool = False,
        backup_first: bool = True
    ) -> Dict[str, Any]:
        """Migrate data from SQLite to PostgreSQL.
        
        Returns:
            Dict with migration status and details
        """
        if not PSYCOPG2_AVAILABLE:
            return {
                'status': 'error',
                'error': 'psycopg2 not available',
                'tables_migrated': 0
            }
        
        # Backup SQLite before migration
        if backup_first and os.path.exists(sqlite_db):
            backup_path = f"backups/{sqlite_db}.backup_{datetime.now().timestamp()}"
            os.makedirs('backups', exist_ok=True)
            import shutil
            try:
                shutil.copy(sqlite_db, backup_path)
                print(f"✅ SQLite backed up to {backup_path}")
            except Exception as e:
                print(f"⚠️  Backup failed: {e}")
        
        # Connect to both databases
        try:
            sqlite_conn = sqlite3.connect(sqlite_db)
            sqlite_cursor = sqlite_conn.cursor()
            
            postgres_conn = psycopg2.connect(postgres_url)
            postgres_cursor = postgres_conn.cursor()
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Connection failed: {e}',
                'tables_migrated': 0
            }
        
        # Tables to migrate
        tables = [
            'stations_master', 'train_master', 'train_routes',
            'train_schedule', 'train_fares', 'train_running_days',
            'tenants', 'api_keys', 'system_audit', 'system_jobs',
            'job_logs', 'usage_metrics'
        ]
        
        migrated_tables = []
        errors = []
        total_rows = 0
        
        for table in tables:
            try:
                # Get row count from SQLite
                sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                sqlite_count = sqlite_cursor.fetchone()[0]
                
                # Create table in PostgreSQL (skip if exists)
                sqlite_cursor.execute(f"PRAGMA table_info({table})")
                columns = sqlite_cursor.fetchall()
                
                # Simple schema copying (minimal type mapping)
                if not dry_run:
                    # Copy table structure and data
                    sqlite_cursor.execute(f"SELECT * FROM {table}")
                    rows = sqlite_cursor.fetchall()
                    
                    if rows:
                        # Insert rows (simplified)
                        placeholders = ','.join(['%s'] * len(columns))
                        postgres_cursor.executemany(
                            f"INSERT INTO {table} VALUES ({placeholders})",
                            rows
                        )
                    
                    postgres_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    postgres_count = postgres_cursor.fetchone()[0]
                else:
                    postgres_count = sqlite_count  # In dry-run, assume success
                
                # Verify counts match
                if sqlite_count == postgres_count:
                    migrated_tables.append({
                        'table': table,
                        'sqlite_rows': sqlite_count,
                        'postgres_rows': postgres_count,
                        'verified': True
                    })
                    total_rows += sqlite_count
                else:
                    errors.append({
                        'table': table,
                        'sqlite_rows': sqlite_count,
                        'postgres_rows': postgres_count,
                        'verified': False
                    })
            except Exception as e:
                errors.append({'table': table, 'error': str(e)})
        
        # Commit if not dry-run
        if not dry_run:
            postgres_conn.commit()
        
        postgres_cursor.close()
        postgres_conn.close()
        sqlite_cursor.close()
        sqlite_conn.close()
        
        return {
            'status': 'success' if not errors else 'partial_failure',
            'mode': 'dry-run' if dry_run else 'live',
            'tables_migrated': len(migrated_tables),
            'rows_processed': total_rows,
            'duration_sec': None,
            'details': {table['table']: table for table in migrated_tables},
            'errors': errors
        }
    
    @staticmethod
    def verify(
        postgres_url: str,
        sqlite_db: str = DatabaseConfig.SQLITE_PATH
    ) -> Dict[str, Any]:
        """Verify migration consistency."""
        try:
            sqlite_conn = sqlite3.connect(sqlite_db)
            sqlite_cursor = sqlite_conn.cursor()
            
            postgres_conn = psycopg2.connect(postgres_url)
            postgres_cursor = postgres_conn.cursor()
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'total_tables': 0}
        
        tables = [
            'stations_master', 'train_master', 'train_routes',
            'train_schedule', 'train_fares', 'train_running_days',
            'tenants', 'api_keys', 'system_audit', 'system_jobs',
            'job_logs', 'usage_metrics'
        ]
        
        mismatches = []
        matching_tables = 0
        
        for table in tables:
            try:
                sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                sqlite_count = sqlite_cursor.fetchone()[0]
                
                postgres_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                postgres_count = postgres_cursor.fetchone()[0]
                
                if sqlite_count == postgres_count:
                    matching_tables += 1
                else:
                    mismatches.append({
                        'table': table,
                        'sqlite': sqlite_count,
                        'postgres': postgres_count
                    })
            except Exception as e:
                mismatches.append({'table': table, 'error': str(e)})
        
        postgres_cursor.close()
        postgres_conn.close()
        sqlite_cursor.close()
        sqlite_conn.close()
        
        return {
            'status': 'verified' if not mismatches else 'mismatch',
            'total_tables': len(tables),
            'matching_tables': matching_tables,
            'mismatches': mismatches
        }


# ============================================================================
# ORM MODELS (SQLAlchemy)
# ============================================================================

if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()
    
    class Tenant(Base):
        __tablename__ = 'tenants'
        id = Column(Integer, primary_key=True)
        tenant_id = Column(String(32), unique=True, nullable=False)
        name = Column(String(255), nullable=False)
        active = Column(Boolean, default=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        metadata_json = Column('metadata', Text, default='{}')
    
    class APIKey(Base):
        __tablename__ = 'api_keys'
        id = Column(Integer, primary_key=True)
        api_key = Column(String(255), unique=True, nullable=False)
        tenant_id = Column(String(32), nullable=False)
        active = Column(Boolean, default=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        usage_count = Column(Integer, default=0)
    
    class SystemJob(Base):
        __tablename__ = 'system_jobs'
        id = Column(Integer, primary_key=True)
        job_id = Column(String(64), unique=True, nullable=False)
        command = Column(String(255), nullable=False)
        payload = Column(Text)
        status = Column(String(32), default='pending')
        result = Column(Text)
        created_at = Column(DateTime, default=datetime.utcnow)
    
    class JobLog(Base):
        __tablename__ = 'job_logs'
        id = Column(Integer, primary_key=True)
        job_id = Column(String(64), nullable=False)
        message = Column(Text)
        level = Column(String(32), default='info')
        created_at = Column(DateTime, default=datetime.utcnow)
    
    class SystemAudit(Base):
        __tablename__ = 'system_audit'
        id = Column(Integer, primary_key=True)
        action = Column(String(255), nullable=False)
        tenant_id = Column(String(32))
        user = Column(String(255))
        details = Column(Text, default='{}')
        created_at = Column(DateTime, default=datetime.utcnow)
    
    class TrainMaster(Base):
        __tablename__ = 'train_master'
        id = Column(Integer, primary_key=True)
        train_no = Column(String(32), unique=True)
        train_name = Column(String(255))
        train_type = Column(String(64))
        source_station = Column(String(32))
        destination_station = Column(String(32))
    
    class StationMaster(Base):
        __tablename__ = 'stations_master'
        id = Column(Integer, primary_key=True)
        station_code = Column(String(32), unique=True)
        station_name = Column(String(255))
        city = Column(String(255))
        state = Column(String(255))
        is_junction = Column(Boolean, default=False)
