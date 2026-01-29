# models/route.py - Enhanced Route Management System
from sqlalchemy import Column, String, Integer, Boolean, DateTime, DECIMAL, ForeignKey, JSON, Index, CheckConstraint, text, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB, TSVECTOR
from sqlalchemy.orm import relationship, validates
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from connection import Base

class Route(Base):
    """Enhanced Route model with comprehensive route management features."""

    __tablename__ = "routes"

    # Primary Key (Responsibility 1-2)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core Route Information
    train_id = Column(UUID(as_uuid=True), ForeignKey("trains.id", ondelete='RESTRICT'), nullable=False, index=True)
    origin_station_id = Column(UUID(as_uuid=True), ForeignKey("stations.id", ondelete='RESTRICT'), nullable=False, index=True)
    dest_station_id = Column(UUID(as_uuid=True), ForeignKey("stations.id", ondelete='RESTRICT'), nullable=False, index=True)

    # Route Characteristics (Responsibility 51-70)
    distance_km = Column(DECIMAL(10,2), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    average_speed_kmph = Column(DECIMAL(6,2))

    # Stop Information (Responsibility 51-70)
    stops = Column(JSONB)  # Array of stop stations with times and details
    intermediate_stations = Column(JSONB)  # Station codes for quick lookup
    total_stops = Column(Integer, default=0)

    # Operational Schedule (Responsibility 111-130)
    days_of_operation = Column(ARRAY(Integer))  # [0,1,2,3,4,5,6] for Mon-Sun
    schedule_type = Column(String(50), default="regular")  # regular, seasonal, special
    seasonal_start = Column(DateTime(timezone=True))
    seasonal_end = Column(DateTime(timezone=True))

    # Route Classification (Responsibility 51-70)
    route_type = Column(String(50), default="direct")  # direct, connecting, circular
    priority = Column(Integer, default=0)  # 0=normal, 1=express, 2=slow
    category = Column(String(50))  # passenger, freight, mixed

    # Capacity and Utilization (Responsibility 59-60)
    max_passengers = Column(Integer)
    current_utilization = Column(DECIMAL(5,2))  # Percentage
    capacity_reservations = Column(JSONB)  # Reserved capacity by class

    # Performance Metrics (Responsibility 61-70)
    punctuality_rating = Column(DECIMAL(3,2))  # 0.00 to 1.00
    average_delay_minutes = Column(DECIMAL(6,2))
    cancellation_rate = Column(DECIMAL(5,2))  # Percentage

    # Cost and Revenue (Responsibility 131-150)
    operational_cost_per_km = Column(DECIMAL(8,2))
    revenue_per_km = Column(DECIMAL(8,2))
    profit_margin = Column(DECIMAL(5,2))

    # Environmental Impact (Responsibility 69-70)
    carbon_emissions_kg = Column(DECIMAL(10,2))  # kg CO2 per trip
    energy_consumption_kwh = Column(DECIMAL(10,2))

    # Status and Lifecycle
    is_active = Column(Boolean, default=True, index=True)
    operational_status = Column(String(50), default="operational")  # operational, suspended, cancelled
    activation_date = Column(DateTime(timezone=True), server_default=func.now())
    deactivation_date = Column(DateTime(timezone=True))
    is_deleted = Column(Boolean, default=False, index=True)

    # Maintenance and Planning (Responsibility 67-68)
    last_schedule_review = Column(DateTime(timezone=True))
    next_schedule_review = Column(DateTime(timezone=True))
    maintenance_windows = Column(JSONB)  # Scheduled maintenance periods

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Full-Text Search (Responsibility 17)
    search_vector = Column(TSVECTOR)

    # Additional Metadata
    additional_metadata = Column(JSONB)  # Flexible additional data

    # Relationships
    train = relationship("Train", back_populates="routes")
    origin_station = relationship("Station", foreign_keys=[origin_station_id], back_populates="originating_routes")
    dest_station = relationship("Station", foreign_keys=[dest_station_id], back_populates="destination_routes")
    schedules = relationship("Schedule", back_populates="route", cascade="all, delete-orphan")
    fares = relationship("Fare", back_populates="route", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("distance_km > 0", name='check_distance_positive'),
        CheckConstraint("duration_minutes > 0", name='check_duration_positive'),
        CheckConstraint("average_speed_kmph > 0", name='check_speed_positive'),
        CheckConstraint("max_passengers > 0", name='check_passengers_positive'),
        CheckConstraint("punctuality_rating >= 0 AND punctuality_rating <= 1", name='check_punctuality_range'),
        CheckConstraint("current_utilization >= 0 AND current_utilization <= 100", name='check_utilization_range'),
        CheckConstraint("cancellation_rate >= 0 AND cancellation_rate <= 100", name='check_cancellation_rate_range'),
        CheckConstraint("profit_margin >= -100 AND profit_margin <= 100", name='check_profit_margin_range'),
        CheckConstraint("carbon_emissions_kg >= 0", name='check_emissions_non_negative'),
        CheckConstraint("energy_consumption_kwh >= 0", name='check_energy_non_negative'),
        CheckConstraint("origin_station_id != dest_station_id", name='check_different_stations'),
        Index('idx_routes_train_active', 'train_id', 'is_active'),
        Index('idx_routes_stations', 'origin_station_id', 'dest_station_id'),
        Index('idx_routes_schedule', 'days_of_operation', 'is_active'),
        Index('idx_routes_performance', 'punctuality_rating', 'current_utilization'),
        Index('idx_routes_search_vector', 'search_vector', postgresql_using='gin'),
        Index('idx_routes_operational_status', 'operational_status'),
        Index('idx_routes_category', 'category'),
        Index('idx_routes_priority', 'priority'),
    )

    @validates('days_of_operation')
    def validate_days_of_operation(self, key, value):
        """Validate days of operation array."""
        if value:
            for day in value:
                if not (0 <= day <= 6):
                    raise ValueError("Days of operation must be between 0 (Monday) and 6 (Sunday)")
        return value

    @validates('route_type')
    def validate_route_type(self, key, value):
        """Validate route type."""
        valid_types = ['direct', 'connecting', 'circular', 'shuttle']
        if value and value.lower() not in valid_types:
            raise ValueError(f"Route type must be one of: {', '.join(valid_types)}")
        return value.lower() if value else value

    def to_dict(self) -> Dict[str, Any]:
        """Convert route to dictionary representation."""
        return {
            'id': str(self.id),
            'train_id': str(self.train_id),
            'origin_station_id': str(self.origin_station_id),
            'dest_station_id': str(self.dest_station_id),
            'distance_km': float(self.distance_km),
            'duration_minutes': self.duration_minutes,
            'stops': self.stops,
            'days_of_operation': self.days_of_operation,
            'route_type': self.route_type,
            'is_active': self.is_active,
            'operational_status': self.operational_status,
            'current_utilization': float(self.current_utilization) if self.current_utilization else None,
            'punctuality_rating': float(self.punctuality_rating) if self.punctuality_rating else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def update_search_vector(self):
        """Update the full-text search vector."""
        origin_code = self.origin_station.code if self.origin_station else ""
        dest_code = self.dest_station.code if self.dest_station else ""
        train_number = self.train.number if self.train else ""

        search_text = f"{origin_code} {dest_code} {train_number} {self.route_type or ''}"
        self.search_vector = func.to_tsvector('english', search_text)

    def calculate_average_speed(self) -> float:
        """Calculate average speed in km/h."""
        if self.duration_minutes and self.duration_minutes > 0:
            hours = self.duration_minutes / 60.0
            return float(self.distance_km) / hours
        return 0.0

    def get_stop_details(self) -> List[Dict[str, Any]]:
        """Get detailed stop information."""
        if not self.stops:
            return []

        stop_details = []
        for stop in self.stops:
            stop_details.append({
                'station_code': stop.get('code'),
                'station_name': stop.get('name'),
                'arrival_time': stop.get('arrival'),
                'departure_time': stop.get('departure'),
                'platform': stop.get('platform'),
                'stop_duration': stop.get('duration_minutes'),
            })
        return stop_details

    def runs_on_date(self, check_date: datetime) -> bool:
        """Check if route runs on a specific date."""
        if not self.days_of_operation:
            return False

        # Check if it's within seasonal dates
        if self.seasonal_start and check_date < self.seasonal_start:
            return False
        if self.seasonal_end and check_date > self.seasonal_end:
            return False

        # Check day of week (0 = Monday, 6 = Sunday)
        day_of_week = check_date.weekday()
        return day_of_week in self.days_of_operation

    def calculate_utilization_rate(self) -> float:
        """Calculate current utilization rate."""
        if not self.capacity_reservations or not self.max_passengers:
            return 0.0

        total_reserved = sum(self.capacity_reservations.values())
        return (total_reserved / self.max_passengers) * 100.0

    def get_schedule_for_date(self, check_date: datetime) -> Optional['Schedule']:
        """Get schedule for a specific date."""
        if not self.runs_on_date(check_date):
            return None

        # Find the most recent schedule before the check date
        for schedule in self.schedules:
            if schedule.is_active:
                return schedule

        return None

    def calculate_revenue_potential(self) -> Dict[str, float]:
        """Calculate revenue potential by class."""
        if not self.fares:
            return {}

        revenue_by_class = {}
        for fare in self.fares:
            if fare.is_active():
                class_type = fare.class_type
                base_revenue = float(fare.base_fare) * (self.max_passengers or 0) * 0.8  # 80% occupancy
                revenue_by_class[class_type] = base_revenue

        return revenue_by_class

    @classmethod
    def find_routes_between_stations(cls, session, origin_code: str, dest_code: str, date: Optional[datetime] = None):
        """Find all routes between two stations."""
        query = session.query(cls).join(cls.origin_station).join(cls.dest_station).filter(
            cls.origin_station.has(code=origin_code),
            cls.dest_station.has(code=dest_code),
            cls.is_active == True
        )

        if date:
            # This is a simplified check - in practice, you'd need more complex logic
            day_of_week = date.weekday()
            query = query.filter(cls.days_of_operation.contains([day_of_week]))

        return query.all()

    @classmethod
    def get_routes_by_train(cls, session, train_number: str):
        """Get all routes for a specific train."""
        return session.query(cls).join(cls.train).filter(
            cls.train.has(number=train_number),
            cls.is_active == True
        ).all()

    def __repr__(self):
        return f"<Route(train={self.train.number if self.train else 'None'}, {self.origin_station.code if self.origin_station else 'None'}->{self.dest_station.code if self.dest_station else 'None'})>"


class Schedule(Base):
    """Enhanced Schedule model with advanced scheduling features."""

    __tablename__ = "schedules"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Relationships
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False, index=True)

    # Schedule Details (Responsibility 111-130)
    departure_time = Column(String(8), nullable=False)  # HH:MM:SS format
    arrival_time = Column(String(8), nullable=False)  # HH:MM:SS format
    platform = Column(String(10))

    # Schedule Metadata
    schedule_type = Column(String(50), default="regular")  # regular, special, emergency
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))

    # Operational Details
    estimated_duration = Column(Integer)  # minutes
    buffer_time = Column(Integer, default=5)  # minutes buffer for delays

    # Status
    is_active = Column(Boolean, default=True, index=True)
    status = Column(String(50), default="scheduled")  # scheduled, delayed, cancelled

    # Performance Tracking
    average_delay = Column(DECIMAL(6,2), default=0)
    cancellation_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    route = relationship("Route", back_populates="schedules")

    # Constraints
    __table_args__ = (
        CheckConstraint("estimated_duration > 0", name='check_duration_positive'),
        CheckConstraint("buffer_time >= 0", name='check_buffer_positive'),
        CheckConstraint("average_delay >= 0", name='check_delay_positive'),
        Index('idx_schedules_route_active', 'route_id', 'is_active'),
        Index('idx_schedules_validity', 'valid_from', 'valid_to'),
    )

    def is_valid_on_date(self, check_date: datetime) -> bool:
        """Check if schedule is valid on a specific date."""
        if not self.valid_from or not self.valid_to:
            return self.is_active

        return self.valid_from <= check_date <= self.valid_to and self.is_active

    def get_departure_datetime(self, date: datetime) -> datetime:
        """Get departure datetime for a specific date."""
        time_parts = self.departure_time.split(':')
        return date.replace(
            hour=int(time_parts[0]),
            minute=int(time_parts[1]),
            second=int(time_parts[2]) if len(time_parts) > 2 else 0
        )

    def get_arrival_datetime(self, date: datetime) -> datetime:
        """Get arrival datetime for a specific date."""
        time_parts = self.arrival_time.split(':')
        arrival = date.replace(
            hour=int(time_parts[0]),
            minute=int(time_parts[1]),
            second=int(time_parts[2]) if len(time_parts) > 2 else 0
        )

        # Handle next day arrival
        if arrival < self.get_departure_datetime(date):
            arrival += timedelta(days=1)

        return arrival


class Fare(Base):
    """Enhanced Fare model with dynamic pricing and comprehensive fare management."""

    __tablename__ = "fares"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Relationships
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False, index=True)

    # Fare Details (Responsibility 131-150)
    class_type = Column(String(20), nullable=False)  # 1A, 2A, 3A, SL, 2S, etc.
    base_fare = Column(DECIMAL(10,2), nullable=False)
    reservation_charge = Column(DECIMAL(8,2), default=0)
    superfast_charge = Column(DECIMAL(8,2), default=0)
    tatkal_charge = Column(DECIMAL(8,2), default=0)
    service_charge = Column(DECIMAL(8,2), default=0)

    # Dynamic Pricing (Responsibility 131-150)
    dynamic_pricing_enabled = Column(Boolean, default=False)
    demand_multiplier = Column(DECIMAL(3,2), default=1.0)  # 0.5 to 2.0
    seasonal_multiplier = Column(DECIMAL(3,2), default=1.0)

    # Validity Period
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True))

    # Fare Rules
    minimum_fare = Column(DECIMAL(8,2))
    maximum_fare = Column(DECIMAL(8,2))
    cancellation_policy = Column(JSONB)  # Cancellation charges by time

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    route = relationship("Route", back_populates="fares")

    # Constraints
    __table_args__ = (
        CheckConstraint("base_fare > 0", name='check_base_fare_positive'),
        CheckConstraint("demand_multiplier >= 0.5 AND demand_multiplier <= 2.0", name='check_demand_multiplier_range'),
        CheckConstraint("seasonal_multiplier >= 0.5 AND seasonal_multiplier <= 2.0", name='check_seasonal_multiplier_range'),
        Index('idx_fares_route_class', 'route_id', 'class_type', 'is_active'),
        Index('idx_fares_effective_dates', 'effective_from', 'effective_to'),
    )

    def is_currently_active(self) -> bool:
        """Check if fare is currently active."""
        now = datetime.now()
        return (
            self.is_active and
            self.effective_from <= now and
            (self.effective_to is None or self.effective_to >= now)
        )

    def calculate_total_fare(self, passenger_count: int = 1, is_tatkal: bool = False) -> float:
        """Calculate total fare including all charges."""
        total = float(self.base_fare)

        total += float(self.reservation_charge)
        total += float(self.superfast_charge or 0)
        total += float(self.service_charge or 0)

        if is_tatkal:
            total += float(self.tatkal_charge or 0)

        # Apply dynamic pricing
        if self.dynamic_pricing_enabled:
            total *= float(self.demand_multiplier)
            total *= float(self.seasonal_multiplier)

        # Apply passenger count
        total *= passenger_count

        # Apply min/max bounds
        if self.minimum_fare:
            total = max(total, float(self.minimum_fare))
        if self.maximum_fare:
            total = min(total, float(self.maximum_fare))

        return total

    def get_cancellation_charge(self, hours_before_departure: int) -> float:
        """Calculate cancellation charge based on time before departure."""
        if not self.cancellation_policy:
            return 0.0

        # Find applicable cancellation rule
        for rule in self.cancellation_policy:
            if hours_before_departure >= rule.get('min_hours', 0):
                return float(rule.get('charge_percent', 0)) * float(self.base_fare) / 100.0

        return 0.0

    @classmethod
    def get_current_fare(cls, session, route_id: str, class_type: str) -> Optional['Fare']:
        """Get current fare for a route and class."""
        now = datetime.now()
        return session.query(cls).filter(
            cls.route_id == route_id,
            cls.class_type == class_type,
            cls.is_active == True,
            cls.effective_from <= now,
            func.coalesce(cls.effective_to, now) >= now
        ).first()