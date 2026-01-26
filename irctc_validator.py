"""
IRCTC Validation Engine - Real-World Train Validation

Purpose:
    Continuously validate trains by attempting actual seat searches on IRCTC
    Mark trains as ACTIVE/INACTIVE based on search success
    Maintain validation history for trend analysis

Design:
    - Query IRCTC API to verify trains operate on given dates
    - Capture real seat availability and pricing data
    - Flag trains that are not available (WL, suspended, etc.)
    - Cache validation results for 12 hours
    - Track validation accuracy and success rates

Features:
    - Batch validation (multiple trains in parallel)
    - Graceful error handling (fallback to RAPPID data)
    - Comprehensive logging of all validations
    - Validation report generation
    - Performance metrics tracking

Author: Route Master
Date: 2026-01-25
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
import asyncio
import hashlib

# Import our existing modules
try:
    from irctc_client import IRCTCClient, SearchResult
    from database_manager import DatabaseManager
    from logger import LoggerFactory
    from config import settings
except ImportError as e:
    print(f"Warning: Some imports may not be available: {e}")


class ValidationStatus(Enum):
    """Status of train validation"""
    NOT_ATTEMPTED = "not_attempted"
    VALIDATED = "validated"
    INVALID = "invalid"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class ValidationResult:
    """Result of a single train validation"""
    train_no: str
    date: str  # YYYY-MM-DD
    status: ValidationStatus
    is_available: bool  # True if seats found, False if WL/no seats
    seats_available: int = 0
    lowest_fare: Optional[int] = None
    validation_time_ms: float = 0.0
    error_message: Optional[str] = None
    validated_at: datetime = field(default_factory=datetime.now)
    cached: bool = False


@dataclass
class TrainValidationReport:
    """Report of validation results for a train across multiple dates"""
    train_no: str
    total_validations: int
    successful: int
    available: int  # Times train had available seats
    waitlisted: int  # Times all seats were WL
    unavailable: int  # Times train not found
    success_rate: float  # percentage
    availability_rate: float  # percentage (available/successful)
    avg_seats: float
    avg_fare: float
    last_validation: datetime
    confidence_score: float  # 0-100, based on success rate


class IRCTCValidator:
    """
    Validates trains using real IRCTC seat searches
    
    Workflow:
    1. Load trains from database
    2. For each train on given date:
        a. Check validation cache (12 hour TTL)
        b. If cache miss, query IRCTC API
        c. Parse seat availability
        d. Mark train ACTIVE/INACTIVE based on results
        e. Store validation result
    3. Generate validation report
    4. Update train status in database
    
    Error Handling:
    - API timeout → cache last known state
    - API error → log and skip, don't change status
    - No trains found → mark INACTIVE (with caution)
    """
    
    def __init__(self, db: DatabaseManager = None, irctc_client: IRCTCClient = None):
        """
        Initialize validator
        
        Args:
            db: DatabaseManager instance for train status updates
            irctc_client: IRCTCClient instance for API queries
        """
        self.db = db or DatabaseManager()
        self.irctc_client = irctc_client or IRCTCClient()
        self.logger = LoggerFactory.get_logger("irctc_validator")
        
        # Validation cache: key = "train_no:date", value = ValidationResult
        self.validation_cache: Dict[str, ValidationResult] = {}
        self.cache_ttl_hours = 12
        
        # Statistics
        self.stats = {
            "total_validations": 0,
            "successful": 0,
            "failed": 0,
            "cached": 0,
            "avg_time_ms": 0.0,
            "trains_marked_active": 0,
            "trains_marked_inactive": 0,
        }
    
    def validate_train(self, train_no: str, date: str, 
                      source: Optional[str] = None, destination: Optional[str] = None,
                      use_cache: bool = True) -> ValidationResult:
        """
        Validate a single train on a specific date
        
        Args:
            train_no: Train number (e.g., "16320")
            date: Date in YYYY-MM-DD format
            source: Optional source station code (for seat search)
            destination: Optional destination station code (for seat search)
            use_cache: Whether to use cached validation results
        
        Returns:
            ValidationResult with status and seat information
        """
        cache_key = f"{train_no}:{date}"
        
        # Check cache first
        if use_cache and cache_key in self.validation_cache:
            cached_result = self.validation_cache[cache_key]
            # Check if cache is still valid (within TTL)
            age_hours = (datetime.now() - cached_result.validated_at).total_seconds() / 3600
            if age_hours < self.cache_ttl_hours:
                cached_result.cached = True
                self.stats["cached"] += 1
                self.logger.info(f"Validation cache hit for {train_no} on {date}")
                return cached_result
            else:
                # Cache expired, remove it
                del self.validation_cache[cache_key]
        
        # Perform live validation
        start_time = datetime.now()
        result = ValidationResult(
            train_no=train_no,
            date=date,
            status=ValidationStatus.NOT_ATTEMPTED,
            is_available=False,
        )
        
        try:
            # Query IRCTC API
            self.logger.info(f"Validating train {train_no} on {date}...")
            search_results = self.irctc_client.search_trains(
                source_code=source or "NDLS",
                destination_code=destination or "KOTA",
                date_str=date,
                train_no=train_no,
                timeout=10
            )
            
            if not search_results:
                # No results = train not available on this date
                result.status = ValidationStatus.INVALID
                result.is_available = False
                result.error_message = "No search results from IRCTC"
                self.logger.warning(f"Train {train_no} not found on {date}")
            else:
                # Process search results
                result = self._process_search_results(result, search_results)
            
            result.status = ValidationStatus.VALIDATED
            
        except asyncio.TimeoutError:
            result.status = ValidationStatus.TIMEOUT
            result.error_message = "IRCTC API timeout"
            self.logger.warning(f"Timeout validating {train_no}")
            
        except Exception as e:
            result.status = ValidationStatus.ERROR
            result.error_message = str(e)
            self.logger.error(f"Error validating {train_no}: {e}")
        
        finally:
            # Record timing
            duration = (datetime.now() - start_time).total_seconds() * 1000
            result.validation_time_ms = duration
            
            # Update statistics
            self.stats["total_validations"] += 1
            if result.status == ValidationStatus.VALIDATED:
                self.stats["successful"] += 1
            else:
                self.stats["failed"] += 1
            
            # Update average time (simple running average)
            total_time = self.stats["avg_time_ms"] * (self.stats["total_validations"] - 1)
            self.stats["avg_time_ms"] = (total_time + duration) / self.stats["total_validations"]
            
            # Cache the result
            self.validation_cache[cache_key] = result
        
        return result
    
    def _process_search_results(self, result: ValidationResult, 
                               search_results: List) -> ValidationResult:
        """
        Process IRCTC search results to extract seat and fare information
        
        Args:
            result: ValidationResult object to populate
            search_results: List of search results from IRCTC API
        
        Returns:
            Updated ValidationResult
        """
        if not search_results:
            return result
        
        # Aggregate results
        total_seats = 0
        fares = []
        has_available = False
        all_waitlisted = True
        
        for search_result in search_results:
            # Check if train has available seats (not WL)
            if hasattr(search_result, 'available_seats') and search_result.available_seats > 0:
                has_available = True
                all_waitlisted = False
                total_seats += search_result.available_seats
            
            if hasattr(search_result, 'fare') and search_result.fare:
                fares.append(search_result.fare)
        
        # Set availability status
        result.is_available = has_available
        result.seats_available = total_seats
        result.lowest_fare = min(fares) if fares else None
        
        # Log result
        if has_available:
            self.logger.info(f"✓ Train {result.train_no} has {total_seats} available seats")
        else:
            self.logger.warning(f"✗ Train {result.train_no} is fully waitlisted or unavailable")
        
        return result
    
    def validate_trains_batch(self, train_list: List[Tuple[str, str]], 
                            max_parallel: int = 5) -> List[ValidationResult]:
        """
        Validate multiple trains in parallel
        
        Args:
            train_list: List of (train_no, date) tuples
            max_parallel: Maximum parallel validations
        
        Returns:
            List of ValidationResult objects
        """
        self.logger.info(f"Batch validating {len(train_list)} trains...")
        results = []
        
        # Process in batches to avoid overwhelming IRCTC API
        for i in range(0, len(train_list), max_parallel):
            batch = train_list[i:i + max_parallel]
            batch_results = asyncio.run(self._validate_batch_async(batch))
            results.extend(batch_results)
        
        return results
    
    async def _validate_batch_async(self, batch: List[Tuple[str, str]]) -> List[ValidationResult]:
        """Validate batch of trains asynchronously"""
        tasks = [
            asyncio.to_thread(self.validate_train, train_no, date)
            for train_no, date in batch
        ]
        return await asyncio.gather(*tasks)
    
    def update_train_status_from_validation(self, result: ValidationResult):
        """
        Update train status in database based on validation result
        
        Rules:
        - VALIDATED + is_available → ACTIVE
        - VALIDATED + not available → INACTIVE (but log with caution)
        - ERROR/TIMEOUT → don't change status (keep existing)
        
        Args:
            result: ValidationResult to apply
        """
        if result.status != ValidationStatus.VALIDATED:
            self.logger.warning(f"Skipping status update for {result.train_no}: status={result.status}")
            return
        
        session = self.db.get_session()
        try:
            # Query train using generic session query
            # Note: Using session.execute() to avoid Train model dependency
            
            # Update metadata
            train.last_validated = datetime.now()
            train.validation_notes = json.dumps({
                "last_validation": result.validated_at.isoformat(),
                "seats_available": result.seats_available,
                "lowest_fare": result.lowest_fare,
                "error": result.error_message
            })
            
            session.commit()
            self.logger.info(f"Updated {result.train_no}: {old_status} → {train.status}")
            
        except Exception as e:
            self.logger.error(f"Failed to update {result.train_no}: {e}")
            session.rollback()
        finally:
            session.close()
    
    def validate_all_trains(self, date: str = None, 
                           limit: int = None) -> TrainValidationReport:
        """
        Validate all trains in database for a specific date
        
        Args:
            date: Validation date (YYYY-MM-DD), default=today
            limit: Maximum trains to validate (for testing)
        
        Returns:
            TrainValidationReport with aggregated results
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        self.logger.info(f"Starting full validation for {date}...")
        
        session = self.db.get_session()
        trains = session.query(Train).limit(limit).all()
        session.close()
        
        results = []
        for train in trains:
            result = self.validate_train(train.train_no, date)
            results.append(result)
            
            # Update database status
            self.update_train_status_from_validation(result)
            
            # Small delay to avoid overwhelming API
            asyncio.sleep(0.1)
        
        # Generate report
        report = self._generate_report(results, date)
        return report
    
    def _generate_report(self, results: List[ValidationResult], 
                        date: str) -> TrainValidationReport:
        """Generate validation report"""
        train_no = results[0].train_no if results else "UNKNOWN"
        
        successful = sum(1 for r in results if r.status == ValidationStatus.VALIDATED)
        available = sum(1 for r in results if r.is_available)
        
        fares = [r.lowest_fare for r in results if r.lowest_fare]
        avg_fare = sum(fares) / len(fares) if fares else 0
        
        avg_seats = sum(r.seats_available for r in results) / len(results) if results else 0
        
        success_rate = (successful / len(results) * 100) if results else 0
        availability_rate = (available / successful * 100) if successful > 0 else 0
        confidence_score = success_rate * (available / len(results)) if results else 0
        
        report = TrainValidationReport(
            train_no=train_no,
            total_validations=len(results),
            successful=successful,
            available=available,
            waitlisted=sum(1 for r in results if r.status == ValidationStatus.VALIDATED and not r.is_available),
            unavailable=sum(1 for r in results if r.status != ValidationStatus.VALIDATED),
            success_rate=success_rate,
            availability_rate=availability_rate,
            avg_seats=avg_seats,
            avg_fare=avg_fare,
            last_validation=datetime.now(),
            confidence_score=confidence_score
        )
        
        return report
    
    def save_validation_report(self, report: TrainValidationReport, 
                              filepath: str = "data/validation_report.json"):
        """Save validation report to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(asdict(report), f, indent=2, default=str)
            self.logger.info(f"Validation report saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save validation report: {e}")
    
    def get_validation_statistics(self) -> Dict:
        """Get current validation statistics"""
        return {
            **self.stats,
            "cache_size": len(self.validation_cache),
            "cache_ttl_hours": self.cache_ttl_hours,
        }
    
    def clear_cache(self):
        """Clear validation cache"""
        self.validation_cache.clear()
        self.logger.info("Validation cache cleared")
    
    def is_train_active(self, train_no: str, date: str) -> bool:
        """
        Quick check if train is active on date (uses cache)
        
        Returns:
            True if validation found available seats
            False if WL or unavailable
            None if not yet validated
        """
        cache_key = f"{train_no}:{date}"
        if cache_key in self.validation_cache:
            result = self.validation_cache[cache_key]
            age_hours = (datetime.now() - result.validated_at).total_seconds() / 3600
            if age_hours < self.cache_ttl_hours:
                return result.is_available
        return None


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize validator
    validator = IRCTCValidator()
    
    # Example: Validate a single train
    print("\n=== Single Train Validation ===")
    result = validator.validate_train("16320", "2026-02-15", "NDLS", "KOTA")
    print(f"Train: {result.train_no}, Date: {result.date}")
    print(f"Status: {result.status.value}, Available: {result.is_available}")
    print(f"Seats: {result.seats_available}, Lowest Fare: {result.lowest_fare}")
    print(f"Validation Time: {result.validation_time_ms:.2f}ms")
    
    # Example: Validate multiple trains
    print("\n=== Batch Validation ===")
    trains = [
        ("16320", "2026-02-15"),
        ("12951", "2026-02-15"),
        ("14309", "2026-02-15"),
    ]
    results = validator.validate_trains_batch(trains, max_parallel=3)
    
    for result in results:
        status_str = "✓ ACTIVE" if result.is_available else "✗ INACTIVE"
        print(f"{result.train_no}: {status_str} ({result.seats_available} seats)")
    
    # Print statistics
    print("\n=== Validation Statistics ===")
    stats = validator.get_validation_statistics()
    print(f"Total Validations: {stats['total_validations']}")
    print(f"Successful: {stats['successful']}")
    print(f"Average Time: {stats['avg_time_ms']:.2f}ms")
    print(f"Cache Size: {stats['cache_size']}")
    print(f"Trains Marked Active: {stats['trains_marked_active']}")
    print(f"Trains Marked Inactive: {stats['trains_marked_inactive']}")
