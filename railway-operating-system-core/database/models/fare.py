# models/fare.py - Comprehensive Fare Management System
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, DECIMAL, ForeignKey, Index, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime, date
from typing import Optional, Dict, Any
from base import Base

class Fare(Base):
    """Comprehensive Fare model for managing ticket prices and surcharges."""

    __tablename__ = "fares"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Route Reference
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id", ondelete='CASCADE'), nullable=False, index=True)

    # Passenger Class
    class_type = Column(String(20), nullable=False, index=True)  # 1A, 2A, 3A, SL, 2S, GN, etc.
    
    # Base Fare Information
    base_fare = Column(DECIMAL(10,2), nullable=False)  # Base ticket price
    distance_km = Column(DECIMAL(10,2))  # Distance-based calculation reference
    
    # Standard Charges
    reservation_charge = Column(DECIMAL(8,2), default=0)  # Booking/reservation charge
    platform_charge = Column(DECIMAL(8,2), default=0)    # Platform/ticket counter charge
    catering_charge = Column(DECIMAL(8,2), default=0)    # Catering facility charge
    
    # Train Type Surcharges
    superfast_charge = Column(DECIMAL(8,2), default=0)   # Superfast train surcharge
    express_charge = Column(DECIMAL(8,2), default=0)     # Express train surcharge
    rajdhani_charge = Column(DECIMAL(8,2), default=0)    # Premium train surcharge
    duronto_charge = Column(DECIMAL(8,2), default=0)     # Duronto train surcharge
    
    # Time-Based Charges
    tatkal_charge = Column(DECIMAL(8,2), default=0)      # Last-minute booking surcharge
    advance_booking_discount = Column(DECIMAL(8,2), default=0)  # Discount for advance booking
    
    # Passenger Type Discounts
    child_discount = Column(DECIMAL(5,2), default=0)     # Child ticket discount percentage
    senior_citizen_discount = Column(DECIMAL(5,2), default=0)  # Senior discount percentage
    student_discount = Column(DECIMAL(5,2), default=0)   # Student discount percentage
    military_discount = Column(DECIMAL(5,2), default=0)  # Military personnel discount
    disabled_discount = Column(DECIMAL(5,2), default=0)  # Disabled persons discount
    
    # Effective Date Range
    effective_from = Column(Date, nullable=False, index=True)
    effective_to = Column(Date)  # NULL means ongoing
    
    # Special Conditions
    is_holiday_applicable = Column(Boolean, default=True)  # Apply on holidays?
    holiday_surcharge = Column(DECIMAL(8,2), default=0)    # Holiday surcharge
    weekend_surcharge = Column(DECIMAL(8,2), default=0)    # Weekend surcharge
    
    # Load-based Pricing
    peak_season_surcharge = Column(DECIMAL(8,2), default=0)
    off_season_discount = Column(DECIMAL(8,2), default=0)
    
    # GST and Taxes
    gst_percentage = Column(DECIMAL(5,2), default=5)   # GST rate percentage
    other_taxes = Column(JSONB, default={})            # Other tax details
    
    # Pricing Strategy
    dynamic_pricing = Column(Boolean, default=False)   # Is dynamic pricing enabled?
    min_fare = Column(DECIMAL(10,2))                   # Minimum price floor
    max_fare = Column(DECIMAL(10,2))                   # Maximum price ceiling
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_published = Column(Boolean, default=True)  # Is this fare publicly available?
    is_deleted = Column(Boolean, default=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))
    
    # Additional Metadata
    additional_metadata = Column(JSONB)  # Flexible additional data, remarks, etc.

    # Relationships
    route = relationship("Route", back_populates="fares")

    # Constraints
    __table_args__ = (
        CheckConstraint("base_fare > 0", name='check_base_fare_positive'),
        CheckConstraint("reservation_charge >= 0", name='check_reservation_charge_non_negative'),
        CheckConstraint("effective_from <= effective_to OR effective_to IS NULL", name='check_effective_date_range'),
        CheckConstraint("gst_percentage >= 0 AND gst_percentage <= 100", name='check_gst_range'),
        CheckConstraint("child_discount >= 0 AND child_discount <= 100", name='check_child_discount_range'),
        CheckConstraint("senior_citizen_discount >= 0 AND senior_citizen_discount <= 100", name='check_senior_discount_range'),
        CheckConstraint("student_discount >= 0 AND student_discount <= 100", name='check_student_discount_range'),
        CheckConstraint("military_discount >= 0 AND military_discount <= 100", name='check_military_discount_range'),
        CheckConstraint("disabled_discount >= 0 AND disabled_discount <= 100", name='check_disabled_discount_range'),
        Index('idx_fares_route_class', 'route_id', 'class_type'),
        Index('idx_fares_effective_date', 'effective_from', 'effective_to'),
        Index('idx_fares_active_published', 'is_active', 'is_published'),
        Index('idx_fares_deleted', 'is_deleted'),
    )

    def calculate_total_fare(self, 
                            is_tatkal: bool = False,
                            passenger_type: str = "adult",  # adult, child, senior, student, military, disabled
                            is_holiday: bool = False,
                            advance_days: int = 0,
                            is_peak_season: bool = False) -> Dict[str, float]:
        """
        Calculate total fare with all applicable charges and discounts.
        
        Args:
            is_tatkal: Whether this is a Tatkal (last-minute) booking
            passenger_type: Type of passenger
            is_holiday: Whether booking is for a holiday date
            advance_days: Number of days in advance
            is_peak_season: Whether it's peak season
            
        Returns:
            Dictionary with fare breakdown
        """
        fare_breakdown = {
            'base_fare': float(self.base_fare),
            'charges': {},
            'discounts': {},
            'total_before_tax': 0,
            'gst': 0,
            'total_fare': 0,
        }

        # Add applicable charges
        charges_total = 0
        
        charges_total += float(self.reservation_charge or 0)
        charges_total += float(self.platform_charge or 0)
        
        if is_tatkal:
            charges_total += float(self.tatkal_charge or 0)
            fare_breakdown['charges']['tatkal'] = float(self.tatkal_charge or 0)
        
        if is_holiday and self.is_holiday_applicable:
            charges_total += float(self.holiday_surcharge or 0)
            fare_breakdown['charges']['holiday'] = float(self.holiday_surcharge or 0)
        
        if is_peak_season:
            charges_total += float(self.peak_season_surcharge or 0)
            fare_breakdown['charges']['peak_season'] = float(self.peak_season_surcharge or 0)
        
        # Apply passenger type discounts
        discount_total = 0
        if passenger_type == "child":
            discount_pct = float(self.child_discount or 0)
            discount_amt = (float(self.base_fare) * discount_pct) / 100
            discount_total += discount_amt
            fare_breakdown['discounts']['child'] = discount_amt
        elif passenger_type == "senior":
            discount_pct = float(self.senior_citizen_discount or 0)
            discount_amt = (float(self.base_fare) * discount_pct) / 100
            discount_total += discount_amt
            fare_breakdown['discounts']['senior'] = discount_amt
        elif passenger_type == "student":
            discount_pct = float(self.student_discount or 0)
            discount_amt = (float(self.base_fare) * discount_pct) / 100
            discount_total += discount_amt
            fare_breakdown['discounts']['student'] = discount_amt
        elif passenger_type == "military":
            discount_pct = float(self.military_discount or 0)
            discount_amt = (float(self.base_fare) * discount_pct) / 100
            discount_total += discount_amt
            fare_breakdown['discounts']['military'] = discount_amt
        elif passenger_type == "disabled":
            discount_pct = float(self.disabled_discount or 0)
            discount_amt = (float(self.base_fare) * discount_pct) / 100
            discount_total += discount_amt
            fare_breakdown['discounts']['disabled'] = discount_amt
        
        # Apply advance booking discount
        if advance_days >= 30:
            adv_discount = float(self.advance_booking_discount or 0)
            discount_total += adv_discount
            fare_breakdown['discounts']['advance'] = adv_discount
        
        # Calculate total before tax
        subtotal = float(self.base_fare) + charges_total - discount_total
        fare_breakdown['charges']['base'] = float(self.reservation_charge or 0)
        fare_breakdown['charges']['platform'] = float(self.platform_charge or 0)
        fare_breakdown['total_charges'] = charges_total
        fare_breakdown['total_discounts'] = discount_total
        fare_breakdown['total_before_tax'] = subtotal

        # Calculate GST
        gst_amount = (subtotal * float(self.gst_percentage or 5)) / 100
        fare_breakdown['gst'] = round(gst_amount, 2)

        # Final total
        total_fare = subtotal + gst_amount
        
        # Apply min/max fare limits
        if self.min_fare and total_fare < float(self.min_fare):
            total_fare = float(self.min_fare)
        if self.max_fare and total_fare > float(self.max_fare):
            total_fare = float(self.max_fare)
        
        fare_breakdown['total_fare'] = round(total_fare, 2)
        return fare_breakdown

    def is_applicable(self, check_date: Optional[date] = None) -> bool:
        """Check if this fare is currently applicable."""
        if not self.is_active or not self.is_published:
            return False
        
        if check_date is None:
            check_date = date.today()
        
        if check_date < self.effective_from:
            return False
        if self.effective_to and check_date > self.effective_to:
            return False
        
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert fare to dictionary representation."""
        return {
            'id': str(self.id),
            'route_id': str(self.route_id),
            'class': self.class_type,
            'base_fare': float(self.base_fare),
            'charges': {
                'reservation': float(self.reservation_charge or 0),
                'platform': float(self.platform_charge or 0),
                'superfast': float(self.superfast_charge or 0),
                'tatkal': float(self.tatkal_charge or 0),
            },
            'discounts': {
                'child': float(self.child_discount or 0),
                'senior': float(self.senior_citizen_discount or 0),
                'student': float(self.student_discount or 0),
            },
            'effective_from': str(self.effective_from),
            'effective_to': str(self.effective_to) if self.effective_to else None,
            'gst_percentage': float(self.gst_percentage or 5),
            'is_active': self.is_active,
            'is_published': self.is_published,
        }
