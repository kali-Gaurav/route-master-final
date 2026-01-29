# models/train.py - Enhanced Train Model
from sqlalchemy import Column, String, Integer, Boolean, DateTime, DECIMAL, Index, CheckConstraint, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY, TSVECTOR
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from connection import Base

class Train(Base):
    """Enhanced Train model with comprehensive features."""

    __tablename__ = "trains"

    # Primary Key (Responsibility 1-2)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core Identification
    number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), index=True)

    # Classification (Responsibility 71-90)
    type = Column(String(50), nullable=False)  # passenger, freight, express, superfast, etc.
    category = Column(String(50))  # mail, express, passenger, goods
    operator = Column(String(100), index=True)  # Railway zone/operator

    # Physical Characteristics
    total_coaches = Column(Integer)
    max_speed_kmph = Column(Integer)
    length_meters = Column(DECIMAL(8,2))
    weight_tons = Column(DECIMAL(8,2))

    # Coach Configuration (Responsibility 71-90)
    coach_types = Column(JSONB)  # Array of coach types and counts
    total_seats = Column(Integer)
    classes_available = Column(ARRAY(String))  # ['1A', '2A', '3A', 'SL', '2S']

    # Operational Status
    is_active = Column(Boolean, default=True, index=True)
    operational_status = Column(String(50), default="operational")  # operational, maintenance, retired
    is_deleted = Column(Boolean, default=False, index=True)

    # Maintenance Information (Responsibility 73-76)
    last_maintenance = Column(DateTime(timezone=True))
    next_maintenance_due = Column(DateTime(timezone=True))
    maintenance_schedule = Column(JSONB)  # Maintenance schedule details

    # Performance Metrics (Responsibility 77-80)
    average_speed_kmph = Column(DECIMAL(6,2))
    punctuality_rating = Column(DECIMAL(3,2))  # 0.00 to 1.00
    fuel_efficiency = Column(DECIMAL(6,2))  # liters per 100 km
    carbon_footprint = Column(DECIMAL(8,2))  # kg CO2 per km

    # Capacity and Utilization (Responsibility 74)
    passenger_capacity = Column(Integer)
    freight_capacity_tons = Column(DECIMAL(8,2))
    current_utilization = Column(DECIMAL(5,2))  # Percentage

    # Amenities (Responsibility 81-85)
    has_ac = Column(Boolean, default=True)
    has_wifi = Column(Boolean, default=False)
    has_food_service = Column(Boolean, default=True)
    has_entertainment = Column(Boolean, default=False)
    wheelchair_accessible = Column(Boolean, default=True)

    # Technical Specifications
    engine_type = Column(String(50))  # electric, diesel, etc.
    power_rating_kw = Column(Integer)
    manufactured_year = Column(Integer)
    manufacturer = Column(String(100))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Full-Text Search (Responsibility 17)
    search_vector = Column(TSVECTOR)

    # Additional Metadata
    additional_metadata = Column(JSONB)  # Flexible additional data

    # Relationships
    routes = relationship("Route", back_populates="train")

    # Constraints
    __table_args__ = (
        CheckConstraint("total_coaches > 0", name='check_total_coaches_positive'),
        CheckConstraint("max_speed_kmph > 0 AND max_speed_kmph <= 200", name='check_max_speed_range'),
        CheckConstraint("length_meters > 0", name='check_length_positive'),
        CheckConstraint("weight_tons > 0", name='check_weight_positive'),
        CheckConstraint("punctuality_rating >= 0 AND punctuality_rating <= 1", name='check_punctuality_rating_range'),
        CheckConstraint("current_utilization >= 0 AND current_utilization <= 100", name='check_utilization_range'),
        Index('idx_trains_type_operator', 'type', 'operator'),
        Index('idx_trains_active_status', 'is_active', 'operational_status'),
        Index('idx_trains_maintenance_due', 'next_maintenance_due'),
        Index('idx_trains_search_vector', 'search_vector', postgresql_using='gin'),
    )

    @validates('number')
    def validate_number(self, key, value):
        """Validate train number format."""
        if not value or len(value.strip()) == 0:
            raise ValueError("Train number cannot be empty")
        if not value.replace('-', '').replace(' ', '').isdigit():
            raise ValueError("Train number must contain only digits, spaces, and hyphens")
        return value.strip()

    @validates('type')
    def validate_type(self, key, value):
        """Validate train type."""
        valid_types = ['passenger', 'freight', 'express', 'superfast', 'mail', 'goods', 'shatabdi', 'rajdhani', 'duronto']
        if value and value.lower() not in valid_types:
            raise ValueError(f"Train type must be one of: {', '.join(valid_types)}")
        return value.lower() if value else value

    @validates('max_speed_kmph')
    def validate_max_speed(self, key, value):
        """Validate maximum speed."""
        if value is not None and (value <= 0 or value > 200):
            raise ValueError("Maximum speed must be between 1 and 200 km/h")
        return value

    def to_dict(self) -> Dict[str, Any]:
        """Convert train to dictionary representation."""
        return {
            'id': str(self.id),
            'number': self.number,
            'name': self.name,
            'type': self.type,
            'category': self.category,
            'operator': self.operator,
            'total_coaches': self.total_coaches,
            'max_speed_kmph': self.max_speed_kmph,
            'classes_available': self.classes_available,
            'is_active': self.is_active,
            'operational_status': self.operational_status,
            'passenger_capacity': self.passenger_capacity,
            'current_utilization': self.current_utilization,
            'amenities': {
                'ac': self.has_ac,
                'wifi': self.has_wifi,
                'food_service': self.has_food_service,
                'entertainment': self.has_entertainment,
                'wheelchair_accessible': self.wheelchair_accessible,
            },
            'performance': {
                'average_speed': float(self.average_speed_kmph) if self.average_speed_kmph else None,
                'punctuality_rating': float(self.punctuality_rating) if self.punctuality_rating else None,
                'fuel_efficiency': float(self.fuel_efficiency) if self.fuel_efficiency else None,
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def update_search_vector(self):
        """Update the full-text search vector."""
        search_text = f"{self.number} {self.name or ''} {self.type or ''} {self.operator or ''}"
        self.search_vector = func.to_tsvector('english', search_text)

    def calculate_coach_capacity(self) -> Dict[str, int]:
        """Calculate capacity by coach type."""
        if not self.coach_types:
            return {}

        capacity_map = {
            '1A': 18, '2A': 48, '3A': 64, 'SL': 72, '2S': 100,
            'CC': 72, 'EC': 56, 'EA': 46, 'VG': 24
        }

        total_capacity = {}
        for coach_type, count in self.coach_types.items():
            capacity_per_coach = capacity_map.get(coach_type.upper(), 0)
            total_capacity[coach_type] = capacity_per_coach * count

        return total_capacity

    def get_maintenance_status(self) -> Dict[str, Any]:
        """Get maintenance status information."""
        now = datetime.now()
        days_until_maintenance = None

        if self.next_maintenance_due:
            days_until_maintenance = (self.next_maintenance_due - now).days

        return {
            'last_maintenance': self.last_maintenance.isoformat() if self.last_maintenance else None,
            'next_maintenance_due': self.next_maintenance_due.isoformat() if self.next_maintenance_due else None,
            'days_until_maintenance': days_until_maintenance,
            'needs_maintenance': days_until_maintenance is not None and days_until_maintenance <= 0,
            'maintenance_overdue': days_until_maintenance is not None and days_until_maintenance < -30,
        }

    def calculate_efficiency_score(self) -> float:
        """Calculate overall efficiency score (0.0 to 1.0)."""
        scores = []

        if self.punctuality_rating is not None:
            scores.append(float(self.punctuality_rating))

        if self.fuel_efficiency is not None:
            # Higher fuel efficiency = better score
            efficiency_score = min(1.0, 10.0 / float(self.fuel_efficiency)) if self.fuel_efficiency > 0 else 0
            scores.append(efficiency_score)

        if self.current_utilization is not None:
            # Optimal utilization around 80-90%
            utilization = float(self.current_utilization)
            if utilization <= 90:
                utilization_score = utilization / 90.0
            else:
                utilization_score = max(0, 1.0 - (utilization - 90) / 20.0)
            scores.append(utilization_score)

        return sum(scores) / len(scores) if scores else 0.0

    @classmethod
    def get_trains_by_type(cls, session, train_type: str):
        """Get all trains of a specific type."""
        return session.query(cls).filter(
            cls.type == train_type.lower(),
            cls.is_active == True
        ).all()

    @classmethod
    def get_trains_due_maintenance(cls, session, days_ahead: int = 30):
        """Get trains due for maintenance within specified days."""
        from datetime import timedelta
        due_date = datetime.now() + timedelta(days=days_ahead)

        return session.query(cls).filter(
            cls.next_maintenance_due <= due_date,
            cls.is_active == True
        ).all()

    def __repr__(self):
        return f"<Train(number='{self.number}', name='{self.name}', type='{self.type}')>"