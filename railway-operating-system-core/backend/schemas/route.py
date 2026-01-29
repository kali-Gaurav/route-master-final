# schemas/route.py
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal
import re

class StationBase(BaseModel):
    code: str
    name: str
    latitude: Decimal
    longitude: Decimal
    state: Optional[str] = None
    zone: Optional[str] = None
    platform_count: int = 1

    @field_validator('code')
    def validate_station_code(cls, v):
        """Validate station code format"""
        if not re.match(r'^[A-Z]{2,5}$', v.upper()):
            raise ValueError('Station code must be 2-5 uppercase letters')
        return v.upper()

    @field_validator('name')
    def validate_station_name(cls, v):
        """Validate station name"""
        if len(v.strip()) < 2:
            raise ValueError('Station name must be at least 2 characters')
        if len(v) > 100:
            raise ValueError('Station name must be less than 100 characters')
        return v.strip()

    @field_validator('latitude')
    def validate_latitude(cls, v):
        """Validate latitude range"""
        if not (-90 <= float(v) <= 90):
            raise ValueError('Latitude must be between -90 and 90 degrees')
        return v

    @field_validator('longitude')
    def validate_longitude(cls, v):
        """Validate longitude range"""
        if not (-180 <= float(v) <= 180):
            raise ValueError('Longitude must be between -180 and 180 degrees')
        return v

    @field_validator('platform_count')
    def validate_platform_count(cls, v):
        """Validate platform count"""
        if v < 1 or v > 50:
            raise ValueError('Platform count must be between 1 and 50')
        return v

class StationCreate(StationBase):
    pass

class StationUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    state: Optional[str] = None
    zone: Optional[str] = None
    platform_count: Optional[int] = None
    is_active: Optional[bool] = None

    @field_validator('code')
    def validate_station_code(cls, v):
        """Validate station code format"""
        if v is not None and not re.match(r'^[A-Z]{2,5}$', v.upper()):
            raise ValueError('Station code must be 2-5 uppercase letters')
        return v.upper() if v else v

    @field_validator('name')
    def validate_station_name(cls, v):
        """Validate station name"""
        if v is not None:
            if len(v.strip()) < 2:
                raise ValueError('Station name must be at least 2 characters')
            if len(v) > 100:
                raise ValueError('Station name must be less than 100 characters')
            return v.strip()
        return v

    @field_validator('latitude')
    def validate_latitude(cls, v):
        """Validate latitude range"""
        if v is not None and not (-90 <= float(v) <= 90):
            raise ValueError('Latitude must be between -90 and 90 degrees')
        return v

    @field_validator('longitude')
    def validate_longitude(cls, v):
        """Validate longitude range"""
        if v is not None and not (-180 <= float(v) <= 180):
            raise ValueError('Longitude must be between -180 and 180 degrees')
        return v

    @field_validator('platform_count')
    def validate_platform_count(cls, v):
        """Validate platform count"""
        if v is not None and (v < 1 or v > 50):
            raise ValueError('Platform count must be between 1 and 50')
        return v

class Station(StationBase):
    id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class RouteBase(BaseModel):
    train_id: UUID
    origin_station_id: UUID
    dest_station_id: UUID
    distance_km: Decimal
    duration_minutes: int
    stops: Optional[dict] = None
    days_of_operation: List[int]

    @field_validator('distance_km')
    def validate_distance(cls, v):
        """Validate distance is positive"""
        if float(v) <= 0:
            raise ValueError('Distance must be greater than 0 km')
        if float(v) > 5000:  # Longest railway route in world is ~5000km
            raise ValueError('Distance cannot exceed 5000 km')
        return v

    @field_validator('duration_minutes')
    def validate_duration(cls, v):
        """Validate duration is reasonable"""
        if v <= 0:
            raise ValueError('Duration must be greater than 0 minutes')
        if v > 10080:  # Max 7 days
            raise ValueError('Duration cannot exceed 7 days (10080 minutes)')
        return v

    @field_validator('days_of_operation')
    def validate_days_of_operation(cls, v):
        """Validate days of operation"""
        if not v:
            raise ValueError('At least one day of operation must be specified')
        if len(v) > 7:
            raise ValueError('Cannot specify more than 7 days')
        invalid_days = [day for day in v if not (0 <= day <= 6)]
        if invalid_days:
            raise ValueError('Days must be between 0 (Monday) and 6 (Sunday)')
        if len(set(v)) != len(v):
            raise ValueError('Duplicate days of operation not allowed')
        return sorted(v)

    @model_validator(mode='after')
    def validate_route_logic(self):
        """Validate business logic constraints"""
        # Origin and destination must be different
        if self.origin_station_id == self.dest_station_id:
            raise ValueError('Origin and destination stations must be different')

        # Distance should be reasonable for duration
        if self.distance_km and self.duration_minutes:
            # Calculate reasonable speed (km/h)
            hours = self.duration_minutes / 60
            if hours > 0:
                speed_kmh = float(self.distance_km) / hours
                # Train speeds typically 50-300 km/h
                if speed_kmh < 10:
                    raise ValueError('Route speed too slow (minimum 10 km/h)')
                if speed_kmh > 350:
                    raise ValueError('Route speed too fast (maximum 350 km/h)')

        return self

class RouteCreate(RouteBase):
    pass

class RouteUpdate(BaseModel):
    train_id: Optional[UUID] = None
    origin_station_id: Optional[UUID] = None
    dest_station_id: Optional[UUID] = None
    distance_km: Optional[Decimal] = None
    duration_minutes: Optional[int] = None
    stops: Optional[dict] = None
    days_of_operation: Optional[List[int]] = None
    is_active: Optional[bool] = None

    @field_validator('distance_km')
    def validate_distance(cls, v):
        """Validate distance is positive"""
        if v is not None:
            if float(v) <= 0:
                raise ValueError('Distance must be greater than 0 km')
            if float(v) > 5000:
                raise ValueError('Distance cannot exceed 5000 km')
        return v

    @field_validator('duration_minutes')
    def validate_duration(cls, v):
        """Validate duration is reasonable"""
        if v is not None:
            if v <= 0:
                raise ValueError('Duration must be greater than 0 minutes')
            if v > 10080:
                raise ValueError('Duration cannot exceed 7 days (10080 minutes)')
        return v

    @field_validator('days_of_operation')
    def validate_days_of_operation(cls, v):
        """Validate days of operation"""
        if v is not None:
            if not v:
                raise ValueError('At least one day of operation must be specified')
            if len(v) > 7:
                raise ValueError('Cannot specify more than 7 days')
            invalid_days = [day for day in v if not (0 <= day <= 6)]
            if invalid_days:
                raise ValueError('Days must be between 0 (Monday) and 6 (Sunday)')
            if len(set(v)) != len(v):
                raise ValueError('Duplicate days of operation not allowed')
            return sorted(v)
        return v

    @model_validator(mode='after')
    def validate_route_update_logic(self):
        """Validate business logic constraints for updates"""
        # If both origin and destination are provided, they must be different
        if (self.origin_station_id is not None and
            self.dest_station_id is not None and
            self.origin_station_id == self.dest_station_id):
            raise ValueError('Origin and destination stations must be different')

        # If both distance and duration are provided, validate speed
        if (self.distance_km is not None and
            self.duration_minutes is not None and
            self.duration_minutes > 0):
            hours = self.duration_minutes / 60
            speed_kmh = float(self.distance_km) / hours
            if speed_kmh < 10:
                raise ValueError('Route speed too slow (minimum 10 km/h)')
            if speed_kmh > 350:
                raise ValueError('Route speed too fast (maximum 350 km/h)')

        return self

class Route(RouteBase):
    id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class RouteSearch(BaseModel):
    origin_station: Optional[str] = None
    dest_station: Optional[str] = None
    date: Optional[str] = None
    limit: int = 50
    offset: int = 0

    @field_validator('limit')
    def validate_limit(cls, v):
        """Validate pagination limit"""
        if v < 1:
            raise ValueError('Limit must be at least 1')
        if v > 500:  # Increased from 100 to 500 but still reasonable
            raise ValueError('Limit cannot exceed 500')
        return v

    @field_validator('offset')
    def validate_offset(cls, v):
        """Validate pagination offset"""
        if v < 0:
            raise ValueError('Offset cannot be negative')
        return v

class Route(RouteBase):
    id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class RouteSearch(BaseModel):
    origin_station: Optional[str] = None
    dest_station: Optional[str] = None
    date: Optional[str] = None
    limit: int = 50
    offset: int = 0