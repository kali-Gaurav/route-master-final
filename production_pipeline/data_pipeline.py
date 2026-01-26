"""
Data Validation & Clean Data Pipeline

Validates incoming data, handles deduplication, normalization, and
produces clean operational data ready for the routing engine.

Features:
- Schema validation
- Data deduplication
- Field normalization
- Relationship extraction
- Quality scoring
- Error tracking
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from sqlalchemy.orm import Session
import hashlib
import re

try:
    from production_pipeline.database import (
        Train, Station, TrainStation, RawPayload, CleanDataset,
        TrainStatus
    )
except ImportError:
    Train = None
    Station = None
    TrainStation = None
    RawPayload = None
    CleanDataset = None
    TrainStatus = None

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    data: Optional[Dict[str, Any]] = None


class DataValidator:
    """Validates train and station data"""
    
    # Station code format: 2-4 capital letters
    STATION_CODE_PATTERN = re.compile(r"^[A-Z]{2,4}$")
    
    # Train number format: 1-4 digits
    TRAIN_NUMBER_PATTERN = re.compile(r"^\d{1,4}$")
    
    # Time format: HH:MM
    TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")
    
    # Days format: SMTWTFS (7 characters)
    DAYS_PATTERN = re.compile(r"^[Y|N]{7}$")
    
    def __init__(self):
        """Initialize validator"""
        logger.info("DataValidator initialized")
    
    def validate_station_code(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate station code format
        
        Args:
            code: Station code
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not code or not isinstance(code, str):
            return False, "Station code is required and must be string"
        
        code = code.upper().strip()
        
        if not self.STATION_CODE_PATTERN.match(code):
            return False, f"Invalid station code format: {code}"
        
        return True, None
    
    def validate_train_number(self, train_no: str) -> Tuple[bool, Optional[str]]:
        """Validate train number format
        
        Args:
            train_no: Train number
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not train_no or not isinstance(train_no, str):
            return False, "Train number is required and must be string"
        
        train_no = train_no.strip()
        
        if not self.TRAIN_NUMBER_PATTERN.match(train_no):
            return False, f"Invalid train number format: {train_no}"
        
        return True, None
    
    def validate_time(self, time_str: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Validate time format
        
        Args:
            time_str: Time string in HH:MM format
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if time_str is None:
            return True, None  # Optional
        
        if not isinstance(time_str, str):
            return False, "Time must be string"
        
        if not self.TIME_PATTERN.match(time_str):
            return False, f"Invalid time format: {time_str}"
        
        # Check valid hours and minutes
        parts = time_str.split(":")
        hours, minutes = int(parts[0]), int(parts[1])
        
        if not (0 <= hours < 24):
            return False, f"Invalid hours: {hours}"
        
        if not (0 <= minutes < 60):
            return False, f"Invalid minutes: {minutes}"
        
        return True, None
    
    def validate_days_running(self, days: str) -> Tuple[bool, Optional[str]]:
        """Validate days running format
        
        Args:
            days: Days in SMTWTFS format (Y/N for each day)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not days or not isinstance(days, str):
            return False, "Days running is required and must be string"
        
        days = days.upper().strip()
        
        if not self.DAYS_PATTERN.match(days):
            return False, f"Days running must be 7 chars (Y/N): {days}"
        
        # At least one day must be selected
        if "Y" not in days:
            return False, "Train must run on at least one day"
        
        return True, None
    
    def validate_train_data(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate train data
        
        Args:
            data: Train data dictionary
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True, data=data)
        
        # Required fields
        required_fields = ["train_no", "train_name", "source", "destination", "days"]
        for field_name in required_fields:
            if field_name not in data or not data[field_name]:
                result.errors.append(f"Missing required field: {field_name}")
                result.is_valid = False
        
        if not result.is_valid:
            return result
        
        # Validate train number
        is_valid, error = self.validate_train_number(data["train_no"])
        if not is_valid:
            result.errors.append(error)
            result.is_valid = False
        
        # Validate source and destination
        for field_name in ["source", "destination"]:
            is_valid, error = self.validate_station_code(data[field_name])
            if not is_valid:
                result.errors.append(f"Invalid {field_name}: {error}")
                result.is_valid = False
        
        # Validate days
        is_valid, error = self.validate_days_running(data["days"])
        if not is_valid:
            result.errors.append(error)
            result.is_valid = False
        
        # Validate optional times
        if "departure_time" in data:
            is_valid, error = self.validate_time(data.get("departure_time"))
            if not is_valid:
                result.errors.append(f"Invalid departure_time: {error}")
                result.is_valid = False
        
        if "arrival_time" in data:
            is_valid, error = self.validate_time(data.get("arrival_time"))
            if not is_valid:
                result.errors.append(f"Invalid arrival_time: {error}")
                result.is_valid = False
        
        # Validate numeric fields
        if "duration_minutes" in data:
            try:
                duration = int(data["duration_minutes"])
                if duration <= 0:
                    result.errors.append(f"Duration must be positive: {duration}")
                    result.is_valid = False
            except (ValueError, TypeError):
                result.errors.append(f"Invalid duration: {data['duration_minutes']}")
                result.is_valid = False
        
        return result
    
    def validate_station_data(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate station data
        
        Args:
            data: Station data dictionary
            
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True, data=data)
        
        # Required fields
        required_fields = ["code", "name", "city"]
        for field_name in required_fields:
            if field_name not in data or not data[field_name]:
                result.errors.append(f"Missing required field: {field_name}")
                result.is_valid = False
        
        if not result.is_valid:
            return result
        
        # Validate station code
        is_valid, error = self.validate_station_code(data["code"])
        if not is_valid:
            result.errors.append(error)
            result.is_valid = False
        
        # Validate coordinates if present
        if "latitude" in data and "longitude" in data:
            try:
                lat = float(data["latitude"])
                lon = float(data["longitude"])
                if not (-90 <= lat <= 90):
                    result.warnings.append(f"Invalid latitude: {lat}")
                if not (-180 <= lon <= 180):
                    result.warnings.append(f"Invalid longitude: {lon}")
            except (ValueError, TypeError):
                result.warnings.append("Invalid coordinates")
        
        return result


class DataNormalizer:
    """Normalizes and cleans data"""
    
    def __init__(self):
        """Initialize normalizer"""
        logger.info("DataNormalizer initialized")
    
    def normalize_station_code(self, code: str) -> str:
        """Normalize station code to uppercase
        
        Args:
            code: Station code
            
        Returns:
            Normalized code
        """
        return code.upper().strip() if code else code
    
    def normalize_train_number(self, train_no: str) -> str:
        """Normalize train number
        
        Args:
            train_no: Train number
            
        Returns:
            Normalized number
        """
        return train_no.strip() if train_no else train_no
    
    def normalize_name(self, name: str) -> str:
        """Normalize name field
        
        Args:
            name: Name string
            
        Returns:
            Normalized name
        """
        # Remove extra spaces, title case
        return " ".join(name.split()).title() if name else ""
    
    def normalize_time(self, time_str: Optional[str]) -> Optional[str]:
        """Normalize time format
        
        Args:
            time_str: Time string
            
        Returns:
            Normalized time or None
        """
        if not time_str:
            return None
        
        # Ensure HH:MM format
        parts = time_str.split(":")
        if len(parts) != 2:
            return None
        
        try:
            hour = int(parts[0])
            minute = int(parts[1])
            return f"{hour:02d}:{minute:02d}"
        except ValueError:
            return None


class DeduplicationEngine:
    """Detects and handles duplicate data"""
    
    def __init__(self):
        """Initialize deduplication engine"""
        logger.info("DeduplicationEngine initialized")
    
    @staticmethod
    def get_train_signature(train_data: Dict[str, Any]) -> str:
        """Generate signature for train data
        
        Args:
            train_data: Train data
            
        Returns:
            SHA256 signature
        """
        key_fields = [
            train_data.get("train_no"),
            train_data.get("source"),
            train_data.get("destination"),
            train_data.get("days"),
        ]
        signature_str = "|".join(str(f) for f in key_fields)
        return hashlib.sha256(signature_str.encode()).hexdigest()
    
    @staticmethod
    def get_station_signature(station_data: Dict[str, Any]) -> str:
        """Generate signature for station data
        
        Args:
            station_data: Station data
            
        Returns:
            SHA256 signature
        """
        key_fields = [station_data.get("code"), station_data.get("city")]
        signature_str = "|".join(str(f) for f in key_fields)
        return hashlib.sha256(signature_str.encode()).hexdigest()
    
    def is_duplicate_train(self, train_data: Dict[str, Any], session: Session) -> bool:
        """Check if train already exists
        
        Args:
            train_data: Train data to check
            session: Database session
            
        Returns:
            True if duplicate found
        """
        train_no = train_data.get("train_no")
        if not train_no:
            return False
        
        existing = session.query(Train).filter_by(train_no=train_no).first()
        return existing is not None
    
    def is_duplicate_station(self, station_data: Dict[str, Any], session: Session) -> bool:
        """Check if station already exists
        
        Args:
            station_data: Station data to check
            session: Database session
            
        Returns:
            True if duplicate found
        """
        code = station_data.get("code")
        if not code:
            return False
        
        existing = session.query(Station).filter_by(code=code).first()
        return existing is not None


class CleanDataPipeline:
    """Complete pipeline for data validation and cleaning"""
    
    def __init__(self, session: Session):
        """Initialize clean data pipeline
        
        Args:
            session: Database session
        """
        self.session = session
        self.validator = DataValidator()
        self.normalizer = DataNormalizer()
        self.deduplication = DeduplicationEngine()
        logger.info("CleanDataPipeline initialized")
    
    def process_train(self, raw_data: Dict[str, Any], raw_payload_id: int) -> Tuple[bool, Optional[Train]]:
        """Process raw train data into clean train record
        
        Args:
            raw_data: Raw train data
            raw_payload_id: Raw payload record ID
            
        Returns:
            Tuple of (success, train_record_or_none)
        """
        # Validate
        validation_result = self.validator.validate_train_data(raw_data)
        if not validation_result.is_valid:
            logger.warning(f"Train validation failed: {validation_result.errors}")
            return False, None
        
        # Check for duplicates
        if self.deduplication.is_duplicate_train(raw_data, self.session):
            logger.debug(f"Duplicate train: {raw_data.get('train_no')}")
            return False, None
        
        # Normalize
        normalized_data = {
            "train_no": self.normalizer.normalize_train_number(raw_data["train_no"]),
            "train_name": self.normalizer.normalize_name(raw_data.get("train_name", "")),
            "source_station_code": self.normalizer.normalize_station_code(raw_data["source"]),
            "destination_station_code": self.normalizer.normalize_station_code(raw_data["destination"]),
            "days_running": raw_data["days"],
            "journey_duration_minutes": int(raw_data.get("duration_minutes", 0)),
            "status": TrainStatus.ACTIVE,
            "last_verified_at": datetime.utcnow(),
        }
        
        # Create record
        train = Train(**normalized_data)
        self.session.add(train)
        
        logger.info(f"Created train record: {train.train_no}")
        return True, train
    
    def process_station(self, raw_data: Dict[str, Any], raw_payload_id: int) -> Tuple[bool, Optional[Station]]:
        """Process raw station data into clean station record
        
        Args:
            raw_data: Raw station data
            raw_payload_id: Raw payload record ID
            
        Returns:
            Tuple of (success, station_record_or_none)
        """
        # Validate
        validation_result = self.validator.validate_station_data(raw_data)
        if not validation_result.is_valid:
            logger.warning(f"Station validation failed: {validation_result.errors}")
            return False, None
        
        # Check for duplicates
        if self.deduplication.is_duplicate_station(raw_data, self.session):
            logger.debug(f"Duplicate station: {raw_data.get('code')}")
            return False, None
        
        # Normalize
        normalized_data = {
            "code": self.normalizer.normalize_station_code(raw_data["code"]),
            "name": self.normalizer.normalize_name(raw_data.get("name", "")),
            "city": self.normalizer.normalize_name(raw_data.get("city", "")),
            "state": raw_data.get("state"),
            "latitude": float(raw_data.get("latitude")) if raw_data.get("latitude") else None,
            "longitude": float(raw_data.get("longitude")) if raw_data.get("longitude") else None,
            "zone": raw_data.get("zone"),
            "division": raw_data.get("division"),
        }
        
        # Create record
        station = Station(**normalized_data)
        self.session.add(station)
        
        logger.info(f"Created station record: {station.code}")
        return True, station
