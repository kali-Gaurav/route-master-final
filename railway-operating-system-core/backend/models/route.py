# models/route.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db_connection import Base

class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey("trains.id"), nullable=False, index=True)
    origin_station_id = Column(Integer, ForeignKey("stations.id"), nullable=False, index=True)
    dest_station_id = Column(Integer, ForeignKey("stations.id"), nullable=False, index=True)
    distance_km = Column(Float, nullable=False)
    duration_minutes = Column(Integer, nullable=False)  # in minutes
    stops = Column(JSON, nullable=True)  # List of stop stations
    days_of_operation = Column(JSON, default=[0,1,2,3,4,5,6])  # Days 0-6
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)  # Soft delete support
    version = Column(Integer, default=1, nullable=False)  # Optimistic locking

    # Relationships
    train = relationship("Train", back_populates="routes")
    origin_station = relationship("Station", foreign_keys=[origin_station_id], back_populates="routes_from")
    destination_station = relationship("Station", foreign_keys=[dest_station_id], back_populates="routes_to")
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_route_stations', 'origin_station_id', 'dest_station_id'),
        Index('idx_route_train_active', 'train_id', 'is_active'),
        Index('idx_route_distance', 'distance_km'),
        Index('idx_route_duration', 'duration_minutes'),
        Index('idx_route_active_deleted', 'is_active', 'deleted_at'),
        Index('idx_route_created_deleted', 'created_at', 'deleted_at'),
    )

class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    city = Column(String, index=True)
    state = Column(String, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    zone = Column(String, nullable=True)
    platform_count = Column(Integer, default=1)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)  # Soft delete support

    # Relationships
    routes_from = relationship("Route", foreign_keys="Route.origin_station_id", back_populates="origin_station")
    routes_to = relationship("Route", foreign_keys="Route.dest_station_id", back_populates="destination_station")

class Train(Base):
    __tablename__ = "trains"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    type = Column(String, index=True)  # passenger, freight, express, etc.
    capacity = Column(Integer, nullable=True)
    max_speed_kmh = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    routes = relationship("Route", back_populates="train")
