"""
Data Validation Pipeline

Validates data integrity before using it:
- Check for duplicates
- Check for missing required fields
- Validate date/time formats
- Check platform consistency
- Check station sequence validity
- Generate validation reports

Output: validation_report.json with detailed findings
"""

import json
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
import re

from config import VALIDATION_CONFIG
from logger import logger, LoggerFactory, audit_logger

logger = LoggerFactory.get_logger("data_validator")


class ValidationSeverity(Enum):
    """Severity of validation issues"""
    ERROR = "ERROR"         # Data unusable
    WARNING = "WARNING"     # Data usable but problematic
    INFO = "INFO"           # Informational


@dataclass
class ValidationIssue:
    """Single validation issue"""
    severity: ValidationSeverity
    field: str
    train_no: Optional[str] = None
    station_code: Optional[str] = None
    message: str = ""
    value: Any = None
    expected: Any = None


@dataclass
class ValidationReport:
    """Complete validation report"""
    timestamp: datetime
    records_checked: int = 0
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    info_items: List[ValidationIssue] = field(default_factory=list)
    
    # Statistics
    total_issues: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    
    # Pass/fail
    is_valid: bool = False
    validation_duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "records_checked": self.records_checked,
            "total_issues": self.total_issues,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "is_valid": self.is_valid,
            "duration_seconds": self.validation_duration_seconds,
            "errors": [
                {
                    "severity": e.severity.value,
                    "field": e.field,
                    "train_no": e.train_no,
                    "station_code": e.station_code,
                    "message": e.message,
                    "value": str(e.value),
                    "expected": str(e.expected)
                }
                for e in self.errors[:100]  # Limit to 100 errors
            ],
            "warnings": [
                {
                    "severity": w.severity.value,
                    "field": w.field,
                    "train_no": w.train_no,
                    "message": w.message
                }
                for w in self.warnings[:50]
            ]
        }


class DataValidator:
    """Main data validation engine"""
    
    def __init__(self):
        self.logger = LoggerFactory.get_logger("data_validator")
        self.max_errors = VALIDATION_CONFIG.get("max_allowed_errors", 100)
    
    def validate_trains(self, trains: List[Dict]) -> ValidationReport:
        """
        Validate list of trains
        
        Args:
            trains: List of train dictionaries
        
        Returns:
            ValidationReport with findings
        """
        start_time = datetime.utcnow()
        report = ValidationReport(timestamp=datetime.utcnow())
        report.records_checked = len(trains)
        
        # Check for duplicates
        if VALIDATION_CONFIG.get("check_duplicates", True):
            self._check_duplicates(trains, report)
        
        # Validate each train
        for train in trains:
            if VALIDATION_CONFIG.get("check_missing_fields", True):
                self._check_required_fields(train, report)
            
            if VALIDATION_CONFIG.get("check_invalid_dates", True):
                self._check_date_fields(train, report)
            
            # Stop if too many errors
            if len(report.errors) > self.max_errors:
                report.errors.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field="validation",
                    message=f"Too many errors (>{self.max_errors}), stopping validation"
                ))
                break
        
        # Update summary
        report.total_issues = len(report.errors) + len(report.warnings) + len(report.info_items)
        report.error_count = len(report.errors)
        report.warning_count = len(report.warnings)
        report.info_count = len(report.info_items)
        report.is_valid = report.error_count == 0
        report.validation_duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        
        # Log audit
        audit_logger.log_data_validation(
            operation="validate_trains",
            records_checked=report.records_checked,
            errors_found=report.error_count,
            warnings=report.warning_count
        )
        
        self.logger.info(
            f"Validation completed: {report.records_checked} records, "
            f"{report.error_count} errors, {report.warning_count} warnings",
            extra={
                "records_checked": report.records_checked,
                "errors": report.error_count,
                "warnings": report.warning_count,
                "duration_seconds": report.validation_duration_seconds
            }
        )
        
        return report
    
    def validate_train_stations(self, train_no: str, 
                               stations: List[Dict]) -> ValidationReport:
        """Validate train station sequence"""
        start_time = datetime.utcnow()
        report = ValidationReport(timestamp=datetime.utcnow())
        report.records_checked = len(stations)
        
        # Check station sequence validity
        if VALIDATION_CONFIG.get("check_station_sequence", True):
            self._check_station_sequence(train_no, stations, report)
        
        # Check platform consistency
        if VALIDATION_CONFIG.get("check_platform_consistency", True):
            self._check_platform_consistency(train_no, stations, report)
        
        # Check timing validity
        self._check_timing_validity(train_no, stations, report)
        
        # Update summary
        report.total_issues = len(report.errors) + len(report.warnings)
        report.error_count = len(report.errors)
        report.warning_count = len(report.warnings)
        report.is_valid = report.error_count == 0
        report.validation_duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        
        return report
    
    def _check_duplicates(self, trains: List[Dict], report: ValidationReport):
        """Check for duplicate trains"""
        seen = set()
        
        for train in trains:
            train_no = train.get("train_no")
            
            if train_no in seen:
                report.warnings.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field="train_no",
                    train_no=train_no,
                    message="Duplicate train number found",
                    value=train_no
                ))
            
            seen.add(train_no)
    
    def _check_required_fields(self, train: Dict, report: ValidationReport):
        """Check for required fields"""
        required_fields = ["train_no", "train_name", "status"]
        
        for field in required_fields:
            value = train.get(field)
            
            if value is None or (isinstance(value, str) and len(value.strip()) == 0):
                report.errors.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field=field,
                    train_no=train.get("train_no"),
                    message=f"Missing required field: {field}",
                    value=value
                ))
    
    def _check_date_fields(self, train: Dict, report: ValidationReport):
        """Validate date/time fields"""
        date_fields = ["last_updated", "last_fetched", "created_at"]
        time_pattern = re.compile(r'^\d{1,2}:\d{2}$')  # HH:MM format
        
        for field in date_fields:
            value = train.get(field)
            if value is None:
                continue
            
            # Check if it's a valid datetime string or datetime object
            if isinstance(value, str):
                try:
                    datetime.fromisoformat(value.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    report.warnings.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field=field,
                        train_no=train.get("train_no"),
                        message=f"Invalid datetime format: {value}",
                        value=value,
                        expected="ISO format or datetime object"
                    ))
    
    def _check_station_sequence(self, train_no: str, 
                               stations: List[Dict], report: ValidationReport):
        """Check station sequence is valid"""
        if not stations:
            report.errors.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                field="stations",
                train_no=train_no,
                message="No stations found for train"
            ))
            return
        
        # Check sequence numbers are consecutive
        sequences = sorted([s.get("station_sequence", 0) for s in stations])
        
        for i, seq in enumerate(sequences):
            if i > 0 and seq != sequences[i-1] + 1 and seq != sequences[i-1]:
                report.warnings.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field="station_sequence",
                    train_no=train_no,
                    message=f"Non-consecutive station sequence: {sequences}",
                    value=sequences
                ))
                break
        
        # Check distances are increasing
        distances = [s.get("distance_from_start_km", 0) for s in stations]
        if distances != sorted(distances):
            report.warnings.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                field="distance_from_start_km",
                train_no=train_no,
                message="Distances not in increasing order"
            ))
    
    def _check_platform_consistency(self, train_no: str,
                                   stations: List[Dict], report: ValidationReport):
        """Check platform data is consistent"""
        for station in stations:
            platform = station.get("platform_number")
            platform_line = station.get("platform_line")
            
            if platform and not str(platform).isdigit() and not str(platform).isalnum():
                report.warnings.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field="platform_number",
                    train_no=train_no,
                    station_code=station.get("station_code"),
                    message=f"Invalid platform format: {platform}",
                    value=platform
                ))
    
    def _check_timing_validity(self, train_no: str,
                              stations: List[Dict], report: ValidationReport):
        """Check arrival/departure times are valid"""
        time_pattern = re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
        
        for station in stations:
            arrival = station.get("arrival_time")
            departure = station.get("departure_time")
            
            # Validate format
            if arrival and not time_pattern.match(str(arrival)):
                report.warnings.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field="arrival_time",
                    train_no=train_no,
                    station_code=station.get("station_code"),
                    message=f"Invalid arrival time: {arrival}",
                    value=arrival
                ))
            
            if departure and not time_pattern.match(str(departure)):
                report.warnings.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field="departure_time",
                    train_no=train_no,
                    station_code=station.get("station_code"),
                    message=f"Invalid departure time: {departure}",
                    value=departure
                ))
    
    def save_report(self, report: ValidationReport, 
                   filepath: Path = Path("data/validation_report.json")):
        """Save validation report to JSON"""
        try:
            with open(filepath, 'w') as f:
                json.dump(report.to_dict(), f, indent=2)
            
            self.logger.info(f"Validation report saved: {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save validation report: {e}", exc_info=True)


# Global validator instance
validator = DataValidator()
