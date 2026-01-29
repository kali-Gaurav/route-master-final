# models/station.py - Enhanced Station Model
from sqlalchemy import Column, String, Integer, Boolean, DateTime, DECIMAL, Index, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from connection import Base

class Station(Base):
    """Enhanced Station model with comprehensive features."""

    __tablename__ = "stations"

    # Primary Key (Responsibility 1-2)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core Fields
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    latitude = Column(DECIMAL(10,8), nullable=False)
    longitude = Column(DECIMAL(11,8), nullable=False)

    # Geographic Information (Responsibility 91-110)
    state = Column(String(100), index=True)
    zone = Column(String(50), index=True)
    division = Column(String(100))
    district = Column(String(100))

    # Infrastructure Details (Responsibility 91-110)
    platform_count = Column(Integer, default=1)
    platform_types = Column(JSONB)  # Array of platform types and lengths
    track_count = Column(Integer, default=1)

    # Facilities (Responsibility 91-110)
    has_wifi = Column(Boolean, default=False)
    has_parking = Column(Boolean, default=False)
    has_food_court = Column(Boolean, default=False)
    has_atm = Column(Boolean, default=False)
    has_medical_facility = Column(Boolean, default=False)
    is_junction = Column(Boolean, default=False)

    # Accessibility (Responsibility 100)
    wheelchair_accessible = Column(Boolean, default=True)
    braille_signage = Column(Boolean, default=True)
    audio_announcements = Column(Boolean, default=True)

    # Operational Status
    is_active = Column(Boolean, default=True, index=True)
    operational_status = Column(String(50), default="operational")  # operational, maintenance, closed
    is_deleted = Column(Boolean, default=False, index=True)

    # Capacity and Analytics (Responsibility 91-110)
    daily_passenger_capacity = Column(Integer)
    peak_hour_capacity = Column(Integer)
    current_utilization = Column(DECIMAL(5,2))  # Percentage

    # Environmental Data (Responsibility 108)
    air_quality_index = Column(Integer)
    noise_level_db = Column(Integer)
    green_coverage_percent = Column(DECIMAL(5,2))

    # Contact Information
    contact_number = Column(String(20))
    emergency_contact = Column(String(20))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_inspection = Column(DateTime(timezone=True))

    # Full-Text Search (Responsibility 17)
    search_vector = Column(TSVECTOR)

    # Additional Metadata
    additional_metadata = Column(JSONB)  # Flexible additional data

    # Relationships
    originating_routes = relationship("Route", foreign_keys="Route.origin_station_id", back_populates="origin_station")
    destination_routes = relationship("Route", foreign_keys="Route.dest_station_id", back_populates="dest_station")

    # Constraints
    __table_args__ = (
        CheckConstraint('latitude >= -90 AND latitude <= 90', name='check_latitude_range'),
        CheckConstraint('longitude >= -180 AND longitude <= 180', name='check_longitude_range'),
        CheckConstraint('platform_count > 0', name='check_platform_count_positive'),
        CheckConstraint('daily_passenger_capacity > 0', name='check_passenger_capacity_positive'),
        Index('idx_stations_location', 'latitude', 'longitude'),
        Index('idx_stations_zone_state', 'zone', 'state'),
        Index('idx_stations_active_code', 'is_active', 'code'),
        Index('idx_stations_search_vector', 'search_vector', postgresql_using='gin'),
    )

    @validates('code')
    def validate_code(self, key, value):
        """Validate station code format."""
        if not value or len(value.strip()) == 0:
            raise ValueError("Station code cannot be empty")
        if len(value) > 10:
            raise ValueError("Station code cannot exceed 10 characters")
        return value.upper().strip()

    @validates('name')
    def validate_name(self, key, value):
        """Validate station name."""
        if not value or len(value.strip()) == 0:
            raise ValueError("Station name cannot be empty")
        return value.strip()

    @validates('latitude', 'longitude')
    def validate_coordinates(self, key, value):
        """Validate geographic coordinates."""
        if value is None:
            return value

        if key == 'latitude' and not (-90 <= float(value) <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if key == 'longitude' and not (-180 <= float(value) <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        return value

    def to_dict(self) -> Dict[str, Any]:
        """Convert station to dictionary representation."""
        return {
            'id': str(self.id),
            'code': self.code,
            'name': self.name,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'state': self.state,
            'zone': self.zone,
            'platform_count': self.platform_count,
            'is_active': self.is_active,
            'operational_status': self.operational_status,
            'facilities': {
                'wifi': self.has_wifi,
                'parking': self.has_parking,
                'food_court': self.has_food_court,
                'atm': self.has_atm,
                'medical_facility': self.has_medical_facility,
            },
            'accessibility': {
                'wheelchair': self.wheelchair_accessible,
                'braille': self.braille_signage,
                'audio': self.audio_announcements,
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def update_search_vector(self):
        """Update the full-text search vector."""
        search_text = f"{self.code} {self.name} {self.state or ''} {self.zone or ''}"
        self.search_vector = func.to_tsvector('english', search_text)

    def calculate_distance_to(self, other_station) -> float:
        """Calculate distance to another station using Haversine formula."""
        import math

        lat1, lon1 = math.radians(float(self.latitude)), math.radians(float(self.longitude))
        lat2, lon2 = math.radians(float(other_station.latitude)), math.radians(float(other_station.longitude))

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        # Earth's radius in kilometers
        radius = 6371
        return radius * c

    @classmethod
    def get_nearby_stations(cls, session, latitude: float, longitude: float, radius_km: float = 50):
        """Find stations within radius using PostGIS (if available) or approximation."""
        try:
            # Try PostGIS query first
            query = session.query(cls).filter(
                text(f"ST_DWithin(ST_MakePoint({longitude}, {latitude})::geography, ST_MakePoint(longitude, latitude)::geography, {radius_km * 1000})")
            )
            return query.all()
        except:
            # Fallback to simple bounding box approximation
            # This is a rough approximation, not accurate for large distances
            lat_range = radius_km / 111  # 1 degree ≈ 111 km
            lon_range = radius_km / (111 * abs(math.cos(math.radians(latitude))))

            return session.query(cls).filter(
                cls.latitude.between(latitude - lat_range, latitude + lat_range),
                cls.longitude.between(longitude - lon_range, longitude + lon_range),
                cls.is_active == True
            ).all()

    def __repr__(self):
        return f"<Station(code='{self.code}', name='{self.name}')>"