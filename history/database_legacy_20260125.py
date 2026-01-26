"""
Database Schema and ORM for Living Dataset Pipeline

Defines SQLAlchemy models for:
- Trains (train_no, name, status, metadata)
- Stations (station_code, name, location)
- Train-Station relationships (sequence, timings, platforms)
- Fetch logs (audit trail)
- Data quality metrics
"""

import sqlite3
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List

# SQLAlchemy imports
try:
    from sqlalchemy import (
        create_engine, Column, String, Integer, DateTime, 
        Float, Boolean, Text, ForeignKey, Enum as SQLEnum,
        JSON, Index, Table, UniqueConstraint
    )
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship, Session, sessionmaker
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False
    print("⚠️  SQLAlchemy not installed. Using basic SQLite schema.")

from config import DB_TYPE, DB_SQLITE_PATH, DB_POSTGRESQL_URL

Base = declarative_base() if HAS_SQLALCHEMY else None


# Enums for status tracking
class TrainStatus(Enum):
    """Train operational status"""
    ACTIVE = "ACTIVE"           # Confirmed active from API
    INACTIVE = "INACTIVE"       # API returned not found
    UNKNOWN = "UNKNOWN"         # Not yet validated
    SUSPENDED = "SUSPENDED"     # Temporarily not running
    DEPRECATED = "DEPRECATED"   # Legacy, replaced


class FetchStatus(Enum):
    """Fetch operation result"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"


if HAS_SQLALCHEMY:
    class Train(Base):
        """
        Train Master Table
        Tracks all trains and their operational status
        """
        __tablename__ = "trains"
        __table_args__ = (
            Index("idx_train_no", "train_no"),
            Index("idx_status", "status"),
            Index("idx_last_updated", "last_updated"),
        )
        
        id = Column(Integer, primary_key=True)
        train_no = Column(String(10), unique=True, nullable=False, index=True)
        train_name = Column(String(200), nullable=False)
        train_type = Column(String(20))  # EXPRESS, SUPERFAST, etc.
        status = Column(SQLEnum(TrainStatus), default=TrainStatus.UNKNOWN, nullable=False)
        
        # Source tracking
        source_dataset = Column(String(50))  # IRCTC, RAPPID, CSV
        last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
        last_fetched = Column(DateTime)
        
        # Data quality
        data_quality_score = Column(Float, default=0.0)  # 0-100
        is_verified = Column(Boolean, default=False)
        verification_timestamp = Column(DateTime)
        
        # Metadata
        total_stations = Column(Integer, default=0)
        distance_km = Column(Float)
        duration_hours = Column(Float)
        frequency = Column(String(50))  # DAILY, WEEKLY, etc.
        
        # Raw data storage
        raw_data_hash = Column(String(64))  # SHA256 hash for dedup
        metadata_json = Column(JSON)
        
        # Relationships
        stations = relationship("TrainStation", back_populates="train", cascade="all, delete-orphan")
        fetch_logs = relationship("FetchLog", back_populates="train", cascade="all, delete-orphan")
        
        def __repr__(self):
            return f"<Train {self.train_no}: {self.train_name} ({self.status.value})>"


    class Station(Base):
        """
        Station Master Table
        All railway stations with codes and locations
        """
        __tablename__ = "stations"
        __table_args__ = (
            Index("idx_station_code", "station_code"),
            Index("idx_station_name", "station_name"),
        )
        
        id = Column(Integer, primary_key=True)
        station_code = Column(String(10), unique=True, nullable=False, index=True)
        station_name = Column(String(200), nullable=False)
        station_zone = Column(String(50))  # NR, WR, SR, etc.
        
        # Location data
        latitude = Column(Float)
        longitude = Column(Float)
        state = Column(String(50))
        city = Column(String(100))
        
        # Operational info
        is_major_station = Column(Boolean, default=False)
        platforms_count = Column(Integer)
        
        # Relationships
        train_stations = relationship("TrainStation", back_populates="station", cascade="all, delete-orphan")
        
        def __repr__(self):
            return f"<Station {self.station_code}: {self.station_name}>"


    class TrainStation(Base):
        """
        Train-Station Association with Timings and Platforms
        Tracks arrival, departure, halt, platform for each station in a train's route
        """
        __tablename__ = "train_stations"
        __table_args__ = (
            UniqueConstraint("train_id", "station_sequence", name="unique_train_station_sequence"),
            Index("idx_train_id_sequence", "train_id", "station_sequence"),
            Index("idx_station_id", "station_id"),
        )
        
        id = Column(Integer, primary_key=True)
        train_id = Column(Integer, ForeignKey("trains.id"), nullable=False)
        station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
        
        # Route sequence
        station_sequence = Column(Integer, nullable=False)  # Order in the route
        distance_from_start_km = Column(Float)
        
        # Timing information
        arrival_time = Column(String(5))  # HH:MM format
        departure_time = Column(String(5))
        halt_minutes = Column(Integer, default=0)
        is_starting_station = Column(Boolean, default=False)
        is_ending_station = Column(Boolean, default=False)
        
        # Platform information
        platform_number = Column(String(20))
        platform_line = Column(String(20))
        
        # Speed tracking
        speed_kmh = Column(Float)  # Avg speed to this station
        
        # Data quality
        is_verified = Column(Boolean, default=False)
        verification_timestamp = Column(DateTime)
        
        # Relationships
        train = relationship("Train", back_populates="stations")
        station = relationship("Station", back_populates="train_stations")
        
        def __repr__(self):
            return f"<TrainStation {self.train_id}@{self.station_sequence}>"


    class FetchLog(Base):
        """
        Audit Log for All API Fetch Operations
        Complete audit trail for debugging and monitoring
        """
        __tablename__ = "fetch_logs"
        __table_args__ = (
            Index("idx_train_id_timestamp", "train_id", "timestamp"),
            Index("idx_status_timestamp", "status", "timestamp"),
        )
        
        id = Column(Integer, primary_key=True)
        train_id = Column(Integer, ForeignKey("trains.id"), nullable=True)
        
        # Request info
        fetch_type = Column(String(50))  # RAPPID, IRCTC, BATCH, VALIDATION
        source_api = Column(String(50))
        timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
        
        # Response info
        status = Column(SQLEnum(FetchStatus), nullable=False)
        http_status_code = Column(Integer)
        response_time_ms = Column(Integer)
        
        # Data metrics
        records_fetched = Column(Integer)
        records_processed = Column(Integer)
        data_size_bytes = Column(Integer)
        
        # Error tracking
        error_message = Column(Text)
        error_code = Column(String(50))
        retry_count = Column(Integer, default=0)
        
        # Rate limiting
        rate_limit_remaining = Column(Integer)
        rate_limit_reset_time = Column(DateTime)
        
        # Relationships
        train = relationship("Train", back_populates="fetch_logs")
        
        def __repr__(self):
            return f"<FetchLog {self.id}: {self.fetch_type} - {self.status.value}>"


    class DataQualityMetric(Base):
        """
        Track Data Quality Metrics Over Time
        Used for analytics and alerting
        """
        __tablename__ = "data_quality_metrics"
        __table_args__ = (
            Index("idx_timestamp", "timestamp"),
            Index("idx_metric_type", "metric_type"),
        )
        
        id = Column(Integer, primary_key=True)
        timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
        
        # Counts
        total_trains = Column(Integer)
        active_trains = Column(Integer)
        inactive_trains = Column(Integer)
        unknown_trains = Column(Integer)
        
        # Quality scores
        overall_freshness_score = Column(Float)  # 0-100
        data_completeness_percent = Column(Float)  # 0-100
        validation_error_count = Column(Integer)
        
        # Performance metrics
        avg_fetch_time_ms = Column(Float)
        api_success_rate = Column(Float)  # 0-1
        cache_hit_rate = Column(Float)
        
        # Alerts
        has_alerts = Column(Boolean, default=False)
        alert_details = Column(JSON)
        
        def __repr__(self):
            return f"<QualityMetric {self.timestamp}>"


class DatabaseManager:
    """
    Unified database interface
    Supports both SQLite (development) and PostgreSQL (production)
    """
    
    def __init__(self):
        self.db_type = DB_TYPE
        self.engine = None
        self.SessionLocal = None
        self._init_database()
    
    def _init_database(self):
        """Initialize database engine and create tables"""
        try:
            if self.db_type == "sqlite":
                db_url = f"sqlite:///{DB_SQLITE_PATH}"
                self.engine = create_engine(
                    db_url,
                    connect_args={"check_same_thread": False},
                    pool_pre_ping=True
                )
            elif self.db_type == "postgresql":
                self.engine = create_engine(
                    DB_POSTGRESQL_URL,
                    pool_pre_ping=True,
                    pool_size=10,
                    max_overflow=20
                )
            
            # Create all tables
            if HAS_SQLALCHEMY and Base:
                Base.metadata.create_all(self.engine)
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            print(f"✓ Database initialized: {self.db_type}")
        
        except Exception as e:
            print(f"✗ Database initialization failed: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def create_backup(self) -> bool:
        """Create a database backup"""
        try:
            if self.db_type == "sqlite":
                import shutil
                from datetime import datetime
                
                backup_dir = Path("data/backups")
                backup_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = backup_dir / f"train_master_{timestamp}.db"
                
                shutil.copy2(DB_SQLITE_PATH, backup_path)
                print(f"✓ Database backed up to {backup_path}")
                return True
            
            elif self.db_type == "postgresql":
                # PostgreSQL backup would use pg_dump
                print("PostgreSQL backup not implemented yet")
                return False
        
        except Exception as e:
            print(f"✗ Backup failed: {e}")
            return False


# Legacy SQL schema creation (for non-SQLAlchemy environments)
LEGACY_SCHEMA = """
CREATE TABLE IF NOT EXISTS trains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    train_no VARCHAR(10) UNIQUE NOT NULL,
    train_name VARCHAR(200) NOT NULL,
    train_type VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'UNKNOWN',
    source_dataset VARCHAR(50),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_fetched TIMESTAMP,
    data_quality_score FLOAT DEFAULT 0.0,
    is_verified BOOLEAN DEFAULT 0,
    total_stations INTEGER DEFAULT 0,
    distance_km FLOAT,
    duration_hours FLOAT,
    frequency VARCHAR(50),
    raw_data_hash VARCHAR(64),
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_code VARCHAR(10) UNIQUE NOT NULL,
    station_name VARCHAR(200) NOT NULL,
    station_zone VARCHAR(50),
    latitude FLOAT,
    longitude FLOAT,
    state VARCHAR(50),
    city VARCHAR(100),
    is_major_station BOOLEAN DEFAULT 0,
    platforms_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS train_stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    train_id INTEGER NOT NULL,
    station_id INTEGER NOT NULL,
    station_sequence INTEGER NOT NULL,
    distance_from_start_km FLOAT,
    arrival_time VARCHAR(5),
    departure_time VARCHAR(5),
    halt_minutes INTEGER DEFAULT 0,
    is_starting_station BOOLEAN DEFAULT 0,
    is_ending_station BOOLEAN DEFAULT 0,
    platform_number VARCHAR(20),
    platform_line VARCHAR(20),
    speed_kmh FLOAT,
    is_verified BOOLEAN DEFAULT 0,
    UNIQUE(train_id, station_sequence),
    FOREIGN KEY (train_id) REFERENCES trains(id),
    FOREIGN KEY (station_id) REFERENCES stations(id)
);

CREATE TABLE IF NOT EXISTS fetch_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    train_id INTEGER,
    fetch_type VARCHAR(50),
    source_api VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    http_status_code INTEGER,
    response_time_ms INTEGER,
    records_fetched INTEGER,
    records_processed INTEGER,
    data_size_bytes INTEGER,
    error_message TEXT,
    error_code VARCHAR(50),
    retry_count INTEGER DEFAULT 0,
    FOREIGN KEY (train_id) REFERENCES trains(id)
);

CREATE TABLE IF NOT EXISTS data_quality_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_trains INTEGER,
    active_trains INTEGER,
    inactive_trains INTEGER,
    unknown_trains INTEGER,
    overall_freshness_score FLOAT,
    data_completeness_percent FLOAT,
    validation_error_count INTEGER,
    avg_fetch_time_ms FLOAT,
    api_success_rate FLOAT,
    cache_hit_rate FLOAT,
    has_alerts BOOLEAN DEFAULT 0,
    alert_details TEXT
);

CREATE INDEX IF NOT EXISTS idx_train_no ON trains(train_no);
CREATE INDEX IF NOT EXISTS idx_train_status ON trains(status);
CREATE INDEX IF NOT EXISTS idx_train_updated ON trains(last_updated);
CREATE INDEX IF NOT EXISTS idx_station_code ON stations(station_code);
CREATE INDEX IF NOT EXISTS idx_train_station ON train_stations(train_id, station_sequence);
CREATE INDEX IF NOT EXISTS idx_fetch_timestamp ON fetch_logs(timestamp);
"""


def create_legacy_database():
    """Create database using raw SQL (for when SQLAlchemy is not available)"""
    try:
        conn = sqlite3.connect(str(DB_SQLITE_PATH))
        cursor = conn.cursor()
        cursor.executescript(LEGACY_SCHEMA)
        conn.commit()
        conn.close()
        print(f"✓ Legacy database created at {DB_SQLITE_PATH}")
    except Exception as e:
        print(f"✗ Legacy database creation failed: {e}")


# Initialize database on import
if HAS_SQLALCHEMY:
    db = DatabaseManager()
else:
    create_legacy_database()
    db = None
