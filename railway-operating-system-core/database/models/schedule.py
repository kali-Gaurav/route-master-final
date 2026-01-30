# models/schedule.py - Enhanced Schedule Management System
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Time, ForeignKey, Index, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime, time
from typing import Optional, Dict, Any
from base import Base

class Schedule(Base):
    """Enhanced Schedule model for train operations."""

    __tablename__ = "schedules"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Route Reference
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id", ondelete='CASCADE'), nullable=False, index=True)

    # Time Information
    departure_time = Column(Time, nullable=False)
    arrival_time = Column(Time, nullable=False)
    departure_day_offset = Column(Integer, default=0)  # 0=same day, 1=next day, etc.
    arrival_day_offset = Column(Integer, default=0)

    # Platform and Track Information
    departure_platform = Column(String(10))
    arrival_platform = Column(String(10))
    departure_track = Column(String(10))
    arrival_track = Column(String(10))

    # Schedule Pattern
    effective_from = Column(DateTime(timezone=True), nullable=False, index=True)
    effective_to = Column(DateTime(timezone=True))
    
    # Days of Operation (0=Monday, 6=Sunday)
    days_of_operation = Column(ARRAY(Integer), default=[0, 1, 2, 3, 4, 5, 6])  # Default: all days
    
    # Special Schedule Information
    is_seasonal = Column(Boolean, default=False)
    season_type = Column(String(50))  # summer, winter, monsoon, etc.
    special_remarks = Column(String(500))  # Special notes about schedule

    # Operational Status
    is_active = Column(Boolean, default=True, index=True)
    operational_status = Column(String(50), default="operational")  # operational, suspended, cancelled
    is_deleted = Column(Boolean, default=False, index=True)

    # Frequency Information
    frequency_type = Column(String(50), default="daily")  # daily, weekly, monthly, etc.
    frequency_days = Column(JSONB, default={})  # Additional frequency details

    # Performance Metrics
    average_actual_departure = Column(Time)  # Actual average departure time
    average_actual_arrival = Column(Time)    # Actual average arrival time
    on_time_percentage = Column(Integer, default=100)  # Percentage of runs on time
    average_delay_minutes = Column(Integer, default=0)

    # Halt Information
    intermediate_halts = Column(JSONB)  # Details of intermediate halts
    halt_duration_minutes = Column(Integer, default=0)  # Total halt duration

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Additional Metadata
    additional_metadata = Column(JSONB)  # Flexible additional data

    # Relationships
    route = relationship("Route", back_populates="schedules")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "departure_day_offset >= 0 AND arrival_day_offset >= 0",
            name='check_day_offset_non_negative'
        ),
        CheckConstraint(
            "on_time_percentage >= 0 AND on_time_percentage <= 100",
            name='check_on_time_percentage_range'
        ),
        CheckConstraint(
            "average_delay_minutes >= 0",
            name='check_average_delay_non_negative'
        ),
        Index('idx_schedules_route_effective', 'route_id', 'effective_from', 'effective_to'),
        Index('idx_schedules_active_status', 'is_active', 'operational_status'),
        Index('idx_schedules_days_operation', 'days_of_operation', postgresql_using='gin'),
        Index('idx_schedules_deleted', 'is_deleted'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert schedule to dictionary representation."""
        return {
            'id': str(self.id),
            'route_id': str(self.route_id),
            'departure_time': str(self.departure_time),
            'arrival_time': str(self.arrival_time),
            'departure_platform': self.departure_platform,
            'arrival_platform': self.arrival_platform,
            'effective_from': self.effective_from.isoformat() if self.effective_from else None,
            'effective_to': self.effective_to.isoformat() if self.effective_to else None,
            'days_of_operation': self.days_of_operation,
            'is_active': self.is_active,
            'operational_status': self.operational_status,
            'frequency_type': self.frequency_type,
            'performance': {
                'on_time_percentage': self.on_time_percentage,
                'average_delay_minutes': self.average_delay_minutes,
            },
        }

    def is_running_on_date(self, check_date) -> bool:
        """Check if schedule is active on given date."""
        from datetime import date as date_class
        
        if isinstance(check_date, str):
            check_date = date_class.fromisoformat(check_date)
        
        # Check if date is within effective range
        if self.effective_from and check_date < self.effective_from.date():
            return False
        if self.effective_to and check_date > self.effective_to.date():
            return False
        
        # Check if running on this day of week
        day_of_week = check_date.weekday()  # 0=Monday, 6=Sunday
        if self.days_of_operation and day_of_week not in self.days_of_operation:
            return False
        
        # Check if active
        if not self.is_active or self.operational_status != "operational":
            return False
        
        return True
