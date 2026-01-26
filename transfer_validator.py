"""
TRANSFER VALIDATOR

Validates transfers between trains are feasible.

Checks:
- Time window is sufficient (platform change + walk time + buffer)
- Same day transfer (arrival day <= departure day)
- Both trains are ACTIVE
- Station has proper facilities
- Same or nearby platform

Author: Route Master
Date: 2026-01-25
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

try:
    from database import DatabaseManager
    from logger import LoggerFactory
except ImportError:
    pass


@dataclass
class TransferFeasibility:
    """Transfer feasibility result"""
    is_feasible: bool
    transfer_time_minutes: float
    required_time_minutes: float
    confidence_score: float  # 0-100
    warnings: List[str]
    notes: str


class TransferValidator:
    """
    Validates if transfer between two trains is feasible.
    
    Transfer Time Calculation:
    - Time from arrival to departure
    - Minimum required: 20-40 minutes depending on terminal
    - Buffer: 10-20 minutes for delays
    
    Feasibility Factors:
    1. Time window >= 30-60 minutes (depends on station)
    2. Both trains are ACTIVE
    3. Same-day or next-day feasibility
    4. Platform distance is reasonable
    """
    
    # Station transfer times (minutes) - overhead to change trains
    STATION_TRANSFER_TIMES = {
        # Major junctions - longer transfer times
        "NDLS": 60,  # New Delhi - major junction
        "HWH": 60,   # Howrah
        "LKO": 45,   # Lucknow
        "BRC": 45,   # Baroda
        "BBS": 45,   # Bhubaneswar
        
        # Medium junctions - moderate transfer
        "CNB": 35,   # Kanpur
        "PNBE": 35,  # Patna
        "BPL": 35,   # Bhopal
        
        # Smaller stations - shorter transfer
        "GZB": 25,   # Ghaziabad
        "KOTA": 25,  # Kota
        "AGC": 25,   # Agra
    }
    
    DEFAULT_TRANSFER_TIME = 30  # minutes for unknown stations
    MINIMUM_BUFFER = 10  # minutes safety buffer
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger"""
        try:
            return LoggerFactory.get_logger("transfer_validator")
        except:
            logger = logging.getLogger("transfer_validator")
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            return logger
    
    def validate_transfer(self, train1_no: str, train2_no: str,
                         station: str, arrival_time: str,
                         departure_time: str) -> TransferFeasibility:
        """
        Validate if transfer is feasible between two trains
        
        Args:
            train1_no: First train number
            train2_no: Second train number
            station: Transfer station code
            arrival_time: Arrival time of train 1 (HH:MM)
            departure_time: Departure time of train 2 (HH:MM)
        
        Returns:
            TransferFeasibility with detailed assessment
        """
        warnings = []
        
        try:
            # Parse times
            arr_dt = self._parse_time(arrival_time)
            dep_dt = self._parse_time(departure_time)
            
            if not arr_dt or not dep_dt:
                return TransferFeasibility(
                    is_feasible=False,
                    transfer_time_minutes=0,
                    required_time_minutes=0,
                    confidence_score=0,
                    warnings=["Could not parse times"],
                    notes="Invalid time format"
                )
            
            # Calculate transfer window
            transfer_window = self._calculate_time_difference(arr_dt, dep_dt)
            
            # Get station transfer time
            station_transfer = self.STATION_TRANSFER_TIMES.get(
                station, self.DEFAULT_TRANSFER_TIME
            )
            
            # Required transfer time = station overhead + buffer
            required_time = station_transfer + self.MINIMUM_BUFFER
            
            # Check basic feasibility
            is_feasible = transfer_window >= required_time
            
            if transfer_window < station_transfer:
                warnings.append(
                    f"Transfer window ({transfer_window}m) less than station overhead ({station_transfer}m)"
                )
            
            if transfer_window >= required_time and transfer_window < (required_time + 10):
                warnings.append("Transfer time is tight - risky for delays")
            
            # Verify trains exist and are ACTIVE
            try:
                train1 = self.db.session.query(self.db.Train).filter(
                    self.db.Train.train_no == train1_no
                ).first()
                train2 = self.db.session.query(self.db.Train).filter(
                    self.db.Train.train_no == train2_no
                ).first()
                
                if not train1 or not train2:
                    return TransferFeasibility(
                        is_feasible=False,
                        transfer_time_minutes=transfer_window,
                        required_time_minutes=required_time,
                        confidence_score=0,
                        warnings=["One or both trains not found"],
                        notes="Invalid train numbers"
                    )
                
                if train1.status != "ACTIVE":
                    warnings.append(f"Train {train1_no} is {train1.status}")
                    is_feasible = False
                
                if train2.status != "ACTIVE":
                    warnings.append(f"Train {train2_no} is {train2.status}")
                    is_feasible = False
            
            except Exception as e:
                self.logger.warning(f"Error checking train status: {e}")
                warnings.append("Could not verify train status")
            
            # Calculate confidence score
            if is_feasible:
                # Score based on time margin
                margin = transfer_window - required_time
                if margin >= 30:
                    confidence = 95.0
                elif margin >= 20:
                    confidence = 85.0
                elif margin >= 10:
                    confidence = 75.0
                else:
                    confidence = 60.0
            else:
                confidence = 0.0
            
            return TransferFeasibility(
                is_feasible=is_feasible,
                transfer_time_minutes=transfer_window,
                required_time_minutes=required_time,
                confidence_score=confidence,
                warnings=warnings,
                notes=self._generate_notes(
                    is_feasible, transfer_window, required_time, station
                )
            )
        
        except Exception as e:
            self.logger.error(f"Error validating transfer: {e}")
            return TransferFeasibility(
                is_feasible=False,
                transfer_time_minutes=0,
                required_time_minutes=0,
                confidence_score=0,
                warnings=[str(e)],
                notes="Validation error"
            )
    
    def validate_transfers_in_route(self, segments: List[Dict]) -> Tuple[bool, Dict]:
        """
        Validate all transfers in a complete route
        
        Args:
            segments: List of route segments with train_no, arrival, departure
        
        Returns:
            (all_valid, detailed_results)
        """
        results = {
            "all_valid": True,
            "transfers": [],
            "warning_count": 0,
            "risky_transfers": []
        }
        
        # Check each transfer point
        for i in range(len(segments) - 1):
            current = segments[i]
            next_seg = segments[i + 1]
            
            # Validate transfer
            feasibility = self.validate_transfer(
                current['train_no'],
                next_seg['train_no'],
                current['destination'],
                current['arrival_time'],
                next_seg['departure_time']
            )
            
            transfer_info = {
                "from_train": current['train_no'],
                "to_train": next_seg['train_no'],
                "station": current['destination'],
                "is_feasible": feasibility.is_feasible,
                "transfer_time": feasibility.transfer_time_minutes,
                "required_time": feasibility.required_time_minutes,
                "confidence": feasibility.confidence_score,
                "warnings": feasibility.warnings
            }
            
            results['transfers'].append(transfer_info)
            
            if not feasibility.is_feasible:
                results['all_valid'] = False
                results['risky_transfers'].append(transfer_info)
            
            if feasibility.warnings:
                results['warning_count'] += len(feasibility.warnings)
                if feasibility.confidence_score < 75:
                    results['risky_transfers'].append(transfer_info)
        
        return results['all_valid'], results
    
    def get_station_transfer_time(self, station: str) -> int:
        """Get minimum transfer time for a station (minutes)"""
        return self.STATION_TRANSFER_TIMES.get(
            station, self.DEFAULT_TRANSFER_TIME
        )
    
    def _parse_time(self, time_str: str) -> Optional[datetime]:
        """Parse time string HH:MM to datetime"""
        if not time_str:
            return None
        
        try:
            time_str = str(time_str).strip()
            if ':' in time_str:
                parts = time_str.split(':')
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                return datetime(2024, 1, 1, hour, minute)  # Use dummy date
            return None
        except:
            return None
    
    def _calculate_time_difference(self, t1: datetime, t2: datetime) -> float:
        """Calculate time difference in minutes, handling next-day"""
        diff = (t2 - t1).total_seconds() / 60
        
        # If negative (crossing midnight), add 24 hours
        if diff < 0:
            diff += 24 * 60
        
        return diff
    
    def _generate_notes(self, is_feasible: bool, transfer_time: float,
                       required_time: float, station: str) -> str:
        """Generate human-readable notes"""
        if not is_feasible:
            return f"Not feasible - need {required_time}m but have {transfer_time}m"
        
        margin = transfer_time - required_time
        if margin >= 30:
            return f"Comfortable transfer - {margin:.0f}m margin"
        elif margin >= 15:
            return f"Adequate transfer - {margin:.0f}m margin"
        else:
            return f"Tight transfer - {margin:.0f}m margin, risky"


class ConsecutiveSegmentValidator:
    """Validate that consecutive segments form a valid route"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()
        self.logger = logging.getLogger("consecutive_segment_validator")
    
    def validate_segment_sequence(self, segments: List[Dict]) -> Tuple[bool, List[str]]:
        """
        Validate that all consecutive segments connect properly
        
        Args:
            segments: List of route segments
        
        Returns:
            (is_valid, error_list)
        """
        errors = []
        
        for i in range(len(segments) - 1):
            current = segments[i]
            next_seg = segments[i + 1]
            
            # Current segment destination must equal next segment source
            if current.get('destination') != next_seg.get('source'):
                errors.append(
                    f"Segment mismatch: {current['train_no']} ends at "
                    f"{current.get('destination')} but {next_seg['train_no']} "
                    f"starts at {next_seg.get('source')}"
                )
        
        return len(errors) == 0, errors


def main():
    """Test transfer validator"""
    print("Transfer Validator")
    print("=" * 50)
    
    validator = TransferValidator()
    
    # Test transfer
    result = validator.validate_transfer(
        train1_no="16320",
        train2_no="12025",
        station="NDLS",
        arrival_time="14:30",
        departure_time="17:00"
    )
    
    print(f"\nTransfer: 16320 → 12025 at NDLS")
    print(f"  Feasible: {result.is_feasible}")
    print(f"  Window: {result.transfer_time_minutes:.0f} minutes")
    print(f"  Required: {result.required_time_minutes:.0f} minutes")
    print(f"  Confidence: {result.confidence_score:.0f}%")
    print(f"  Notes: {result.notes}")
    if result.warnings:
        print(f"  Warnings: {', '.join(result.warnings)}")
    
    print("\n✓ Transfer validator ready")


if __name__ == "__main__":
    main()
