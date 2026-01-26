"""
LIVE SEAT AVAILABILITY CHECKER

Real-time seat availability verification via IRCTC API.

Features:
- Check available seats by class
- Waitlist status checking
- Fare information
- Booking feasibility validation
- Cache-aware updates

Author: Route Master
Date: 2026-01-25
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from pathlib import Path

try:
    from irctc_validator import IRCTCValidator, ValidationResult
    from database_manager import DatabaseManager
    from logger import LoggerFactory
except ImportError:
    pass


@dataclass
class SeatAvailability:
    """Seat availability for a specific train-date-class"""
    train_no: str
    date: str
    seat_class: str
    available_count: int
    waitlist_count: Optional[int] = None
    fare_per_seat: float = 0.0
    is_available: bool = False
    confidence: float = 0.0  # 0-100 based on recency
    last_checked: str = ""
    can_book: bool = False


@dataclass
class RouteSeats:
    """Seat availability for complete route"""
    route_id: str
    segments_availability: List[Dict]
    min_available_seats: int  # Lowest across all segments
    all_available: bool  # True if all segments have seats
    estimated_fare: float
    booking_feasible: bool


class LiveSeatChecker:
    """
    Check real-time seat availability for routes.
    
    Workflow:
    1. For each train in route, call IRCTC API
    2. Get available seats by class
    3. Check if seats exist (not waitlist-only)
    4. Calculate minimum seats across all segments
    5. Estimate total fare
    6. Return feasibility assessment
    """
    
    # Class mappings
    SEAT_CLASSES = {
        "AC_FIRST": "1A",
        "AC_TWO_TIER": "2A",
        "AC_THREE_TIER": "3A",
        "FIRST": "1",
        "SLEEPER": "SL",
        "GENERAL": "GN"
    }
    
    # Minimum seats to consider "bookable"
    MIN_SEATS_REQUIRED = 1
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()
        self.validator = IRCTCValidator()
        self.logger = self._setup_logger()
        self.availability_cache = {}
    
    def _setup_logger(self):
        """Setup logger"""
        try:
            return LoggerFactory.get_logger("live_seat_checker")
        except:
            logger = logging.getLogger("live_seat_checker")
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            return logger
    
    def check_seat_availability(self, train_no: str, date: str,
                               seat_class: Optional[str] = None) -> SeatAvailability:
        """
        Check seat availability for a train on specific date
        
        Args:
            train_no: Train number
            date: Travel date (YYYY-MM-DD)
            seat_class: Seat class (optional, checks all if not specified)
        
        Returns:
            SeatAvailability object with current status
        """
        # Check cache first
        cache_key = f"{train_no}-{date}-{seat_class}"
        if cache_key in self.availability_cache:
            cached = self.availability_cache[cache_key]
            # Cache valid for 30 minutes
            if (datetime.now() - cached['checked_at']).total_seconds() < 1800:
                return cached['availability']
        
        try:
            # Get IRCTC validation (which checks real seats)
            result = self.validator.validate_train(train_no, date)
            
            if not result:
                return SeatAvailability(
                    train_no=train_no,
                    date=date,
                    seat_class=seat_class or "UNKNOWN",
                    available_count=0,
                    is_available=False,
                    confidence=0,
                    last_checked=datetime.now().isoformat(),
                    can_book=False
                )
            
            # Build availability from validation result
            availability = SeatAvailability(
                train_no=train_no,
                date=date,
                seat_class=seat_class or result.seat_class,
                available_count=result.availability_count or 0,
                is_available=result.has_available_seats,
                confidence=self._calculate_confidence(result),
                last_checked=datetime.now().isoformat(),
                can_book=(
                    result.has_available_seats and 
                    result.availability_count >= self.MIN_SEATS_REQUIRED
                )
            )
            
            # Cache result
            self.availability_cache[cache_key] = {
                'availability': availability,
                'checked_at': datetime.now()
            }
            
            return availability
        
        except Exception as e:
            self.logger.error(f"Error checking seats for {train_no}: {e}")
            return SeatAvailability(
                train_no=train_no,
                date=date,
                seat_class=seat_class or "ERROR",
                available_count=0,
                is_available=False,
                confidence=0,
                last_checked=datetime.now().isoformat(),
                can_book=False
            )
    
    def check_route_availability(self, route_segments: List[Dict],
                                date: str) -> RouteSeats:
        """
        Check seat availability for complete route
        
        Args:
            route_segments: List of segments with 'train_no' key
            date: Travel date
        
        Returns:
            RouteSeats with consolidated availability
        """
        try:
            route_id = f"{date}_{'-'.join([s.get('train_no') for s in route_segments])}"
            
            segments_info = []
            min_seats = float('inf')
            all_available = True
            total_fare = 0.0
            
            # Check each segment
            for segment in route_segments:
                train_no = segment.get('train_no')
                
                availability = self.check_seat_availability(train_no, date)
                
                segment_info = {
                    "train_no": train_no,
                    "available_seats": availability.available_count,
                    "seat_class": availability.seat_class,
                    "is_available": availability.is_available,
                    "can_book": availability.can_book,
                    "confidence": availability.confidence
                }
                
                segments_info.append(segment_info)
                
                if availability.available_count < min_seats:
                    min_seats = availability.available_count
                
                if not availability.is_available:
                    all_available = False
                
                # Add to fare estimate
                total_fare += availability.fare_per_seat
            
            # Reset min_seats if no valid values
            if min_seats == float('inf'):
                min_seats = 0
            
            # Determine booking feasibility
            booking_feasible = (
                all_available and 
                min_seats >= self.MIN_SEATS_REQUIRED
            )
            
            route_seats = RouteSeats(
                route_id=route_id,
                segments_availability=segments_info,
                min_available_seats=int(min_seats),
                all_available=all_available,
                estimated_fare=total_fare,
                booking_feasible=booking_feasible
            )
            
            self.logger.info(
                f"Route {date} availability: {min_seats} seats, "
                f"bookable={booking_feasible}"
            )
            
            return route_seats
        
        except Exception as e:
            self.logger.error(f"Error checking route availability: {e}")
            return RouteSeats(
                route_id="",
                segments_availability=[],
                min_available_seats=0,
                all_available=False,
                estimated_fare=0.0,
                booking_feasible=False
            )
    
    def _calculate_confidence(self, result: ValidationResult) -> float:
        """
        Calculate confidence score based on validation freshness
        
        Confidence = 100% if checked < 30 min ago
                    = 50% if checked 30-120 min ago
                    = 25% if older
        """
        if not result or not hasattr(result, 'last_checked'):
            return 50.0
        
        try:
            if isinstance(result.last_checked, str):
                checked_time = datetime.fromisoformat(result.last_checked)
            else:
                checked_time = result.last_checked
            
            age_minutes = (datetime.now() - checked_time).total_seconds() / 60
            
            if age_minutes < 30:
                return 100.0
            elif age_minutes < 120:
                return 50.0
            else:
                return 25.0
        
        except:
            return 50.0
    
    def get_seat_availability_by_class(self, train_no: str, date: str) -> Dict[str, int]:
        """
        Get available seats breakdown by class
        
        Returns:
            {class_code: available_count}
        """
        availability_by_class = {}
        
        for class_code in self.SEAT_CLASSES.values():
            availability = self.check_seat_availability(
                train_no, date, seat_class=class_code
            )
            
            if availability.is_available:
                availability_by_class[class_code] = availability.available_count
        
        return availability_by_class
    
    def estimate_total_fare(self, route_segments: List[Dict], date: str) -> float:
        """
        Estimate total fare for route
        
        Args:
            route_segments: List of segments
            date: Travel date
        
        Returns:
            Estimated total fare in rupees
        """
        total_fare = 0.0
        
        for segment in route_segments:
            train_no = segment.get('train_no')
            distance = segment.get('distance', 0)
            
            # Simplified fare model: ~1.5 rupees per km per train
            segment_fare = distance * 1.5
            total_fare += segment_fare
        
        return total_fare
    
    def is_route_bookable(self, route_segments: List[Dict], date: str) -> Tuple[bool, Dict]:
        """
        Determine if route is immediately bookable
        
        Returns:
            (is_bookable, details)
        """
        try:
            route_seats = self.check_route_availability(route_segments, date)
            
            details = {
                "is_bookable": route_seats.booking_feasible,
                "min_available_seats": route_seats.min_available_seats,
                "all_trains_available": route_seats.all_available,
                "estimated_fare": route_seats.estimated_fare,
                "segments": route_seats.segments_availability
            }
            
            return route_seats.booking_feasible, details
        
        except Exception as e:
            self.logger.error(f"Error checking route bookability: {e}")
            return False, {"error": str(e)}
    
    def clear_cache(self):
        """Clear availability cache"""
        self.availability_cache.clear()
        self.logger.info("Availability cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cached_entries": len(self.availability_cache),
            "cache_memory_estimate_mb": len(json.dumps(self.availability_cache)) / (1024 * 1024)
        }


class SeatAvailabilityMonitor:
    """Monitor seat availability trends"""
    
    def __init__(self):
        self.history = []
        self.logger = logging.getLogger("seat_monitor")
    
    def record_availability(self, train_no: str, date: str,
                          seat_class: str, available_count: int):
        """Record availability snapshot"""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "train_no": train_no,
            "date": date,
            "seat_class": seat_class,
            "available": available_count
        })
    
    def get_availability_trend(self, train_no: str,
                             hours: int = 24) -> List[Dict]:
        """Get availability trend for train in last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        trend = [
            entry for entry in self.history
            if entry['train_no'] == train_no and
            datetime.fromisoformat(entry['timestamp']) >= cutoff
        ]
        
        return trend


def main():
    """Test seat checker"""
    print("Live Seat Availability Checker")
    print("=" * 50)
    
    checker = LiveSeatChecker()
    
    print("\n✓ Seat checker initialized")
    print("  - IRCTC validation integrated")
    print("  - Real-time seat checking enabled")
    print("  - Caching enabled (30-minute TTL)")
    
    cache_stats = checker.get_cache_stats()
    print(f"\nCache Stats:")
    for key, value in cache_stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
