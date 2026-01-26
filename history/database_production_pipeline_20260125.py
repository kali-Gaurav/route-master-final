"""
Production Database Models & Schema

Defines the complete data model for the railway routing platform.

Tables:
- trains: Train master data
- stations: Station master data
- train_stations: Train's route through stations
- raw_payloads: Immutable raw API responses
- clean_dataset: Validated, processed train data
- routes_cache: Cached route search results
- search_logs: User search history
- performance_logs: System performance metrics
- error_logs: System errors and failures
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, 
    Text, Boolean, ForeignKey, Index, UniqueConstraint, Table,
    Enum as SQLEnum, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from datetime import datetime
from typing import Optional
import enum

Base = declarative_base()


class TrainStatus(enum.Enum):
    """Train operational status"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    DECOMMISSIONED = "DECOMMISSIONED"


class Train(Base):
    """Train master data"""
    __tablename__ = "trains"
    
    id = Column(Integer, primary_key=True)
    train_no = Column(String(10), unique=True, nullable=False, index=True)
    train_name = Column(String(255), nullable=False)
    
    # Route information
    source_station_code = Column(String(10), nullable=False, index=True)
    destination_station_code = Column(String(10), nullable=False, index=True)
    
    # Schedule
    days_running = Column(String(7), nullable=False)  # SMTWTFS format
    journey_duration_minutes = Column(Integer, nullable=False)
    
    # Operational
    status = Column(SQLEnum(TrainStatus), default=TrainStatus.ACTIVE, index=True)
    
    # Data tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_verified_at = Column(DateTime)
    
    # Relationships
    train_stations = relationship("TrainStation", back_populates="train", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_train_route", "source_station_code", "destination_station_code"),
        Index("idx_train_status_days", "status", "days_running"),
    )
    
    def __repr__(self):
        return f"<Train {self.train_no}: {self.train_name}>"


class Station(Base):
    """Station master data"""
    __tablename__ = "stations"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # Location
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Station info
    zone = Column(String(50))
    division = Column(String(100))
    
    # Data tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    train_stops = relationship("TrainStation", back_populates="station")
    
    __table_args__ = (
        Index("idx_station_city", "city"),
        Index("idx_station_zone", "zone"),
    )
    
    def __repr__(self):
        return f"<Station {self.code}: {self.name}>"


class TrainStation(Base):
    """Train's stops at stations (Route)"""
    __tablename__ = "train_stations"
    
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    train_id = Column(Integer, ForeignKey("trains.id"), nullable=False, index=True)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False, index=True)
    
    # Sequence
    sequence = Column(Integer, nullable=False)  # Order in route
    
    # Times
    arrival_time = Column(String(5))  # HH:MM format, None for first station
    departure_time = Column(String(5))  # HH:MM format, None for last station
    halt_minutes = Column(Integer, default=0)
    
    # Distance
    distance_from_source_km = Column(Float)
    
    # Operational
    is_originating = Column(Boolean, default=False)
    is_terminating = Column(Boolean, default=False)
    
    # Data tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    train = relationship("Train", back_populates="train_stations")
    station = relationship("Station", back_populates="train_stops")
    
    __table_args__ = (
        UniqueConstraint("train_id", "station_id", name="unique_train_station"),
        Index("idx_train_route_sequence", "train_id", "sequence"),
    )
    
    def __repr__(self):
        return f"<TrainStation Train:{self.train_id} Station:{self.station_id} Seq:{self.sequence}>"


class RawPayload(Base):
    """Immutable raw API responses"""
    __tablename__ = "raw_payloads"
    
    id = Column(Integer, primary_key=True)
    
    # Source tracking
    source = Column(String(50), nullable=False, index=True)  # RAPPID, IRCTC, etc
    api_endpoint = Column(String(255), nullable=False)
    request_type = Column(String(50), nullable=False)  # GET, POST
    
    # Entity reference
    entity_type = Column(String(50), nullable=False, index=True)  # train, station
    entity_id = Column(String(100), nullable=False, index=True)
    
    # Payload storage
    raw_data = Column(JSON, nullable=False)  # Full API response
    
    # Status
    http_status = Column(Integer)
    is_valid = Column(Boolean, default=True)
    parse_error = Column(Text)
    
    # Versioning
    version = Column(String(20))  # API version
    
    # Data tracking
    received_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime)
    
    # Immutable
    checksum = Column(String(64), unique=True)  # SHA256 of raw_data
    
    __table_args__ = (
        Index("idx_raw_source_entity", "source", "entity_type", "entity_id"),
        Index("idx_raw_received_at", "received_at"),
    )
    
    def __repr__(self):
        return f"<RawPayload {self.source}:{self.entity_id}>"


class CleanDataset(Base):
    """Validated and processed operational data"""
    __tablename__ = "clean_dataset"
    
    id = Column(Integer, primary_key=True)
    
    # Train reference
    train_id = Column(Integer, ForeignKey("trains.id"), nullable=False, index=True)
    
    # Denormalized data for fast queries
    train_no = Column(String(10), nullable=False, index=True)
    train_name = Column(String(255), nullable=False)
    
    # Route
    source_code = Column(String(10), nullable=False, index=True)
    destination_code = Column(String(10), nullable=False, index=True)
    
    # Schedule data
    days_running = Column(String(7), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    
    # Availability (as of last check)
    general_available = Column(Integer, default=0)
    sleeper_available = Column(Integer, default=0)
    ac_3_tier_available = Column(Integer, default=0)
    ac_2_tier_available = Column(Integer, default=0)
    ac_first_available = Column(Integer, default=0)
    
    # Quality metrics
    confidence_score = Column(Float, default=1.0)  # 0-1, based on data freshness
    validation_passed = Column(Boolean, default=True)
    
    # Data freshness
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_as_of = Column(DateTime)  # When this data represents
    
    __table_args__ = (
        Index("idx_clean_route", "source_code", "destination_code"),
        Index("idx_clean_updated_at", "updated_at"),
    )
    
    def __repr__(self):
        return f"<CleanDataset {self.train_no}>"


class RoutesCache(Base):
    """Cached route search results"""
    __tablename__ = "routes_cache"
    
    id = Column(Integer, primary_key=True)
    
    # Search parameters
    origin = Column(String(10), nullable=False, index=True)
    destination = Column(String(10), nullable=False, index=True)
    travel_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    
    # Results
    routes_json = Column(JSON, nullable=False)
    route_count = Column(Integer, default=0)
    
    # Cache control
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_stale = Column(Boolean, default=False, index=True)
    
    __table_args__ = (
        UniqueConstraint("origin", "destination", "travel_date", name="unique_search"),
        Index("idx_cache_expires_at", "expires_at"),
    )
    
    def __repr__(self):
        return f"<RoutesCache {self.origin}->{self.destination} ({self.travel_date})>"


class SearchLog(Base):
    """User search history and analytics"""
    __tablename__ = "search_logs"
    
    id = Column(Integer, primary_key=True)
    
    # Search parameters
    origin = Column(String(10), nullable=False, index=True)
    destination = Column(String(10), nullable=False, index=True)
    travel_date = Column(String(10), nullable=False, index=True)
    
    # Results
    routes_returned = Column(Integer, default=0)
    search_duration_ms = Column(Integer)
    
    # Client info
    client_id = Column(String(50))
    api_version = Column(String(20))
    
    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("idx_search_date_range", "created_at"),
        Index("idx_search_route", "origin", "destination"),
    )
    
    def __repr__(self):
        return f"<SearchLog {self.origin}->{self.destination}>"


class PerformanceLog(Base):
    """System performance metrics"""
    __tablename__ = "performance_logs"
    
    id = Column(Integer, primary_key=True)
    
    # Metric
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50))
    
    # Context
    component = Column(String(100), index=True)  # API, Database, Ingestion, etc
    operation = Column(String(100))
    
    # Labels
    status = Column(String(50))  # success, failure
    
    # Timestamp
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("idx_perf_metric_time", "metric_name", "recorded_at"),
        Index("idx_perf_component", "component"),
    )
    
    def __repr__(self):
        return f"<PerformanceLog {self.metric_name}={self.metric_value}>"


class ErrorLog(Base):
    """System errors and failures"""
    __tablename__ = "error_logs"
    
    id = Column(Integer, primary_key=True)
    
    # Error details
    error_type = Column(String(100), nullable=False, index=True)
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text)
    
    # Context
    component = Column(String(100), nullable=False, index=True)  # API, Ingestion, etc
    operation = Column(String(100))
    
    # Related data
    related_entity = Column(String(255))
    request_id = Column(String(100))
    
    # Severity
    severity = Column(String(20), default="ERROR")  # ERROR, WARNING, CRITICAL
    
    # Resolution
    is_resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime)
    
    __table_args__ = (
        Index("idx_error_type_time", "error_type", "created_at"),
        Index("idx_error_unresolved", "is_resolved"),
    )
    
    def __repr__(self):
        return f"<ErrorLog {self.error_type}: {self.error_message[:50]}>"


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, connection_string: str, echo_sql: bool = False):
        """Initialize database manager"""
        self.engine = create_engine(
            connection_string,
            echo=echo_sql,
            pool_size=20,
            max_overflow=40,
            pool_recycle=3600,
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_all_tables(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)
    
    def drop_all_tables(self):
        """Drop all tables (for testing only)"""
        Base.metadata.drop_all(self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()
