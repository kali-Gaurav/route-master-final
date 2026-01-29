# ===============================================
# SHARED DATABASE MODELS AND UTILITIES
# ===============================================
# SQLAlchemy models and database utilities for multi-tenant system

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIME
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.pool import QueuePool
from typing import Optional, Dict, Any
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Base class for all models
Base = declarative_base()

# ===============================================
# SYSTEM SCHEMA MODELS (Shared across tenants)
# ===============================================

class Tenant(Base):
    """Tenant (client organization) model"""
    __tablename__ = 'tenants'
    __table_args__ = {'schema': 'system'}

    tenant_id = Column(UUID(as_uuid=True), primary_key=True, server_default='uuid_generate_v4()')
    tenant_name = Column(String(255), nullable=False, unique=True)
    tenant_domain = Column(String(255), unique=True)
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    is_active = Column(Boolean, default=True)
    subscription_plan = Column(String(50), default='basic')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    api_keys = relationship("APIKey", back_populates="tenant")
    audit_logs = relationship("AuditLog", back_populates="tenant")

class APIKey(Base):
    """API Key model for authentication"""
    __tablename__ = 'api_keys'
    __table_args__ = {'schema': 'system'}

    api_key_id = Column(UUID(as_uuid=True), primary_key=True, server_default='uuid_generate_v4()')
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('system.tenants.tenant_id', ondelete='CASCADE'), nullable=False)
    api_key_hash = Column(String(255), nullable=False, unique=True)
    api_key_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    rate_limit_per_minute = Column(Integer, default=1000)
    rate_limit_per_hour = Column(Integer, default=10000)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_used_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))

    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")

class AuditLog(Base):
    """System audit log"""
    __tablename__ = 'audit_log'
    __table_args__ = {'schema': 'system'}

    audit_id = Column(UUID(as_uuid=True), primary_key=True, server_default='uuid_generate_v4()')
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('system.tenants.tenant_id'))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(255))
    user_id = Column(String(255))
    ip_address = Column(String(43))  # IPv6 max length
    user_agent = Column(Text)
    details = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="audit_logs")

# ===============================================
# TENANT SCHEMA MODELS (Per-tenant tables)
# ===============================================

def create_tenant_models(schema_name: str):
    """Factory function to create tenant-specific models"""

    class StationsMaster(Base):
        """Stations master table for tenant"""
        __tablename__ = 'stations_master'
        __table_args__ = {'schema': schema_name}

        station_id = Column(Integer, primary_key=True, autoincrement=True)
        station_code = Column(String(10), nullable=False, unique=True)
        station_name = Column(String(255), nullable=False)
        city = Column(String(100))
        state = Column(String(100))
        latitude = Column(DECIMAL(10, 8))
        longitude = Column(DECIMAL(11, 8))
        is_junction = Column(Boolean, default=False)
        created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    class TrainsMaster(Base):
        """Trains master table for tenant"""
        __tablename__ = 'trains_master'
        __table_args__ = {'schema': schema_name}

        train_id = Column(Integer, primary_key=True, autoincrement=True)
        train_no = Column(Integer, nullable=False, unique=True)
        train_name = Column(String(255), nullable=False)
        train_type = Column(String(50))
        source_station = Column(String(10))
        destination_station = Column(String(10))
        distance = Column(Integer)
        duration_minutes = Column(Integer)
        created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    class TrainSchedule(Base):
        """Train schedule table for tenant"""
        __tablename__ = 'train_schedule'
        __table_args__ = {'schema': schema_name}

        schedule_id = Column(Integer, primary_key=True, autoincrement=True)
        train_no = Column(Integer, ForeignKey(f'{schema_name}.trains_master.train_no'), nullable=False)
        station_code = Column(String(10), nullable=False)
        station_name = Column(String(255))
        arrival_time = Column(TIME)
        departure_time = Column(TIME)
        day_of_journey = Column(Integer, default=0)
        distance_from_source = Column(Integer, default=0)
        created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

        # Relationships
        train = relationship("TrainsMaster")

    class TrainRunningDays(Base):
        """Train running days table for tenant"""
        __tablename__ = 'train_running_days'
        __table_args__ = {'schema': schema_name}

        train_no = Column(Integer, ForeignKey(f'{schema_name}.trains_master.train_no'), primary_key=True)
        mon = Column(Boolean, default=False)
        tue = Column(Boolean, default=False)
        wed = Column(Boolean, default=False)
        thu = Column(Boolean, default=False)
        fri = Column(Boolean, default=False)
        sat = Column(Boolean, default=False)
        sun = Column(Boolean, default=False)
        created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

        # Relationships
        train = relationship("TrainsMaster")

    class RouteCache(Base):
        """Route cache table for tenant"""
        __tablename__ = 'route_cache'
        __table_args__ = {'schema': schema_name}

        cache_id = Column(Integer, primary_key=True, autoincrement=True)
        cache_key = Column(String(255), nullable=False, unique=True)
        route_data = Column(JSONB, nullable=False)
        created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
        expires_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    class JobQueue(Base):
        """Job queue table for tenant"""
        __tablename__ = 'job_queue'
        __table_args__ = {'schema': schema_name}

        job_id = Column(UUID(as_uuid=True), primary_key=True, server_default='uuid_generate_v4()')
        job_type = Column(String(50), nullable=False)
        status = Column(String(20), default='pending')
        payload = Column(JSONB)
        result = Column(JSONB)
        error_message = Column(Text)
        priority = Column(Integer, default=1)
        created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
        started_at = Column(DateTime(timezone=True))
        completed_at = Column(DateTime(timezone=True))
        tenant_id = Column(UUID(as_uuid=True), nullable=False)

    return {
        'StationsMaster': StationsMaster,
        'TrainsMaster': TrainsMaster,
        'TrainSchedule': TrainSchedule,
        'TrainRunningDays': TrainRunningDays,
        'RouteCache': RouteCache,
        'JobQueue': JobQueue
    }

# ===============================================
# DATABASE CONNECTION MANAGEMENT
# ===============================================

class DatabaseManager:
    """Database connection manager with multi-tenant support"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        self.scoped_session = None

    def connect(self):
        """Initialize database connection"""
        try:
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600,
                echo=False  # Set to True for debugging
            )

            self.session_factory = sessionmaker(bind=self.engine)
            self.scoped_session = scoped_session(self.session_factory)

            logger.info("Database connection established")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.scoped_session:
            self.scoped_session.remove()
        if self.engine:
            self.engine.dispose()

    def get_session(self):
        """Get a database session"""
        return self.scoped_session()

    def create_tenant_schema(self, tenant_id: str, tenant_name: str) -> bool:
        """Create schema for a new tenant"""
        try:
            schema_name = f"tenant_{tenant_id.replace('-', '')}"

            with self.engine.connect() as conn:
                # Create schema
                conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")

                # Create tables in schema
                tenant_models = create_tenant_models(schema_name)

                # Create all tables
                for model in tenant_models.values():
                    model.__table__.create(conn, checkfirst=True)

                # Create indexes
                indexes = [
                    f"CREATE INDEX IF NOT EXISTS idx_stations_code ON {schema_name}.stations_master(station_code)",
                    f"CREATE INDEX IF NOT EXISTS idx_stations_name ON {schema_name}.stations_master(station_name)",
                    f"CREATE INDEX IF NOT EXISTS idx_trains_no ON {schema_name}.trains_master(train_no)",
                    f"CREATE INDEX IF NOT EXISTS idx_schedule_train ON {schema_name}.train_schedule(train_no)",
                    f"CREATE INDEX IF NOT EXISTS idx_schedule_station ON {schema_name}.train_schedule(station_code)",
                    f"CREATE INDEX IF NOT EXISTS idx_route_cache_key ON {schema_name}.route_cache(cache_key)",
                    f"CREATE INDEX IF NOT EXISTS idx_route_cache_expires ON {schema_name}.route_cache(expires_at)",
                    f"CREATE INDEX IF NOT EXISTS idx_jobs_status ON {schema_name}.job_queue(status)",
                    f"CREATE INDEX IF NOT EXISTS idx_jobs_tenant ON {schema_name}.job_queue(tenant_id)",
                    f"CREATE INDEX IF NOT EXISTS idx_jobs_created ON {schema_name}.job_queue(created_at)"
                ]

                for index_sql in indexes:
                    conn.execute(index_sql)

                conn.commit()

            logger.info(f"Created schema for tenant {tenant_name} ({tenant_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to create tenant schema: {e}")
            return False

    def get_tenant_schema_name(self, tenant_id: str) -> str:
        """Get schema name for tenant"""
        return f"tenant_{tenant_id.replace('-', '')}"

    def validate_api_key(self, api_key_hash: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return tenant info"""
        try:
            session = self.get_session()
            result = session.execute("""
                SELECT
                    t.tenant_id,
                    t.tenant_name,
                    t.is_active,
                    ak.rate_limit_per_minute,
                    ak.rate_limit_per_hour
                FROM system.api_keys ak
                JOIN system.tenants t ON ak.tenant_id = t.tenant_id
                WHERE ak.api_key_hash = :api_key_hash
                AND ak.is_active = true
                AND (ak.expires_at IS NULL OR ak.expires_at > CURRENT_TIMESTAMP)
                AND t.is_active = true
            """, {'api_key_hash': api_key_hash}).fetchone()

            session.close()

            if result:
                return {
                    'tenant_id': str(result[0]),
                    'tenant_name': result[1],
                    'is_active': result[2],
                    'rate_limit_per_minute': result[3],
                    'rate_limit_per_hour': result[4]
                }
            return None
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return None

# ===============================================
# UTILITY FUNCTIONS
# ===============================================

def get_database_url() -> str:
    """Get database URL from environment"""
    return os.getenv(
        'DATABASE_URL',
        'postgresql://railway_user:railway_password@localhost:5432/railway_os'
    )

def create_database_manager() -> DatabaseManager:
    """Create and connect database manager"""
    db_url = get_database_url()
    db_manager = DatabaseManager(db_url)

    if not db_manager.connect():
        raise Exception("Failed to connect to database")

    return db_manager