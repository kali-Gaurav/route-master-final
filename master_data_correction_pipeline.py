"""
Master Data Correction Pipeline
================================

Treats RAPPID API as the source of truth. 
Automatically corrects and validates the CSV dataset against live authoritative data.

This is how Google Maps, Uber, and FlightRadar maintain data quality.
"""

import asyncio
import aiohttp
import pandas as pd
import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import traceback
from collections import defaultdict
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfidenceLevel(Enum):
    """Confidence scores for corrections"""
    HIGH = 0.95      # Exact match with API
    MEDIUM = 0.75    # Partial match, inferred
    LOW = 0.5        # Best effort guess
    UNVERIFIED = 0.0 # Could not verify


@dataclass
class StationRecord:
    """Represents a station in a train route"""
    station_code: str
    station_name: str
    distance_km: Optional[float]
    arrival_time: Optional[str]  # HH:MM format
    departure_time: Optional[str]
    platform: Optional[str]
    halt_minutes: Optional[int]
    sequence: Optional[int]
    source: str  # 'CSV' or 'API'


@dataclass
class TrainCorrectionRecord:
    """Represents a single correction made"""
    train_no: str
    field: str
    old_value: Any
    new_value: Any
    confidence: ConfidenceLevel
    timestamp: str
    api_source: str


@dataclass
class TrainValidationResult:
    """Result of validating a train against API"""
    train_no: str
    status: str  # 'MATCHED', 'CORRECTED', 'UNVERIFIED', 'INVALID'
    csv_stations: int
    api_stations: int
    corrections_made: int
    warnings: List[str]
    errors: List[str]
    records: List[TrainCorrectionRecord]
    confidence_score: float
    api_response_time_ms: float


class RAPPIDMasterClient:
    """Client for RAPPID Master Data API"""
    
    # Using same RAPPID base from project, but can be overridden
    BASE_URL = "https://rappid.in/apis"
    
    def __init__(self, session: aiohttp.ClientSession, rate_limit: int = 100):
        """
        Initialize RAPPID client.
        
        Args:
            session: aiohttp ClientSession
            rate_limit: requests per second (RAPPID free: 100/sec)
        """
        self.session = session
        self.rate_limit = rate_limit
        self.request_times = []
        self.cache = {}
        self.stats = {
            'successful_calls': 0,
            'failed_calls': 0,
            'cached_calls': 0,
            'rate_limit_hits': 0
        }
    
    async def _rate_limit_check(self):
        """Implement token bucket rate limiting"""
        now = time.time()
        self.request_times = [t for t in self.request_times if now - t < 1.0]
        
        if len(self.request_times) >= self.rate_limit:
            self.stats['rate_limit_hits'] += 1
            wait_time = 1.0 - (now - self.request_times[0])
            await asyncio.sleep(wait_time)
    
    async def fetch_train_data(self, train_no: str) -> Optional[Dict[str, Any]]:
        """
        Fetch train data from RAPPID API.
        
        Returns:
            Dict with 'stations' list, or None if failed
        """
        # Check cache first
        if train_no in self.cache:
            self.stats['cached_calls'] += 1
            return self.cache[train_no]
        
        await self._rate_limit_check()
        
        try:
            url = f"{self.BASE_URL}/train.php"
            params = {'train_no': train_no}
            
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                self.request_times.append(time.time())
                
                if resp.status == 404:
                    logger.warning(f"Train {train_no} not found in RAPPID API")
                    self.stats['failed_calls'] += 1
                    return None
                
                if resp.status != 200:
                    logger.warning(f"RAPPID API returned {resp.status} for train {train_no}")
                    self.stats['failed_calls'] += 1
                    return None
                
                data = await resp.json()
                self.stats['successful_calls'] += 1
                
                # Cache for this session
                self.cache[train_no] = data
                return data
                
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {train_no} from RAPPID")
            self.stats['failed_calls'] += 1
            return None
        except Exception as e:
            logger.error(f"Error fetching {train_no}: {e}")
            self.stats['failed_calls'] += 1
            return None


class DataNormalizer:
    """Normalizes data from different sources to standard format"""
    
    @staticmethod
    def parse_time(time_str: Optional[str]) -> Optional[str]:
        """
        Parse various time formats to HH:MM.
        
        Handles:
        - "19:00"
        - "19.00"
        - "1900"
        - "19:0019:00" (malformed)
        """
        if not time_str:
            return None
        
        # Remove whitespace
        time_str = str(time_str).strip()
        
        # Handle malformed times like "19:0019:00"
        if len(time_str) > 5 and ':' in time_str:
            parts = time_str.split(':')
            if len(parts) > 2:
                time_str = f"{parts[0]}:{parts[1]}"
        
        # Replace dots with colons
        time_str = time_str.replace('.', ':')
        
        # Extract HH:MM
        match = re.match(r'(\d{1,2}):?(\d{2})', time_str)
        if match:
            hh, mm = match.groups()
            hh = int(hh)
            mm = int(mm)
            if 0 <= hh <= 23 and 0 <= mm <= 59:
                return f"{hh:02d}:{mm:02d}"
        
        return None
    
    @staticmethod
    def parse_distance(distance_str: Optional[str]) -> Optional[float]:
        """
        Parse distance in various formats.
        
        Handles:
        - "1023 km"
        - "1023km"
        - "1023"
        - "1023.5"
        """
        if not distance_str:
            return None
        
        # Extract numeric part
        match = re.search(r'(\d+\.?\d*)', str(distance_str))
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        
        return None
    
    @staticmethod
    def normalize_station_code(code: Optional[str]) -> Optional[str]:
        """Normalize station code to uppercase"""
        if not code:
            return None
        return str(code).strip().upper()
    
    @staticmethod
    def normalize_station_name(name: Optional[str]) -> Optional[str]:
        """Normalize station name"""
        if not name:
            return None
        return str(name).strip().title()
    
    @staticmethod
    def extract_stations_from_api(api_data: Dict[str, Any]) -> List[StationRecord]:
        """Extract and normalize stations from RAPPID API response"""
        stations = []
        
        # Handle various API response formats
        stations_data = api_data.get('stations') or api_data.get('route') or []
        
        if not isinstance(stations_data, list):
            return stations
        
        for idx, station in enumerate(stations_data):
            if not isinstance(station, dict):
                continue
            
            record = StationRecord(
                station_code=DataNormalizer.normalize_station_code(
                    station.get('code') or station.get('stationCode')
                ),
                station_name=DataNormalizer.normalize_station_name(
                    station.get('name') or station.get('stationName')
                ),
                distance_km=DataNormalizer.parse_distance(station.get('distance')),
                arrival_time=DataNormalizer.parse_time(station.get('arrival')),
                departure_time=DataNormalizer.parse_time(station.get('departure')),
                platform=str(station.get('platform', '')).strip() or None,
                halt_minutes=int(station.get('halt', 0)) if station.get('halt') else None,
                sequence=idx,
                source='API'
            )
            stations.append(record)
        
        return stations
    
    @staticmethod
    def extract_stations_from_csv(csv_rows: List[Dict[str, Any]]) -> List[StationRecord]:
        """Extract and normalize stations from CSV data"""
        stations = []
        
        for row in csv_rows:
            record = StationRecord(
                station_code=DataNormalizer.normalize_station_code(row.get('Station Code')),
                station_name=DataNormalizer.normalize_station_name(row.get('Station Name')),
                distance_km=DataNormalizer.parse_distance(row.get('Distance')),
                arrival_time=DataNormalizer.parse_time(row.get('Arrival Time')),
                departure_time=DataNormalizer.parse_time(row.get('Departure Time')),
                platform=str(row.get('Platform', '')).strip() or None,
                halt_minutes=int(row.get('Halt', 0)) if row.get('Halt') else None,
                sequence=int(row.get('SEQ', 0)) if row.get('SEQ') else None,
                source='CSV'
            )
            stations.append(record)
        
        return stations


class DataComparator:
    """Compares CSV data with API data and identifies mismatches"""
    
    @staticmethod
    def match_stations(csv_stations: List[StationRecord], 
                       api_stations: List[StationRecord]) -> Tuple[List[str], List[str], List[str]]:
        """
        Match CSV stations with API stations.
        
        Returns:
            (matched_codes, missing_in_csv, extra_in_csv)
        """
        csv_codes = {s.station_code for s in csv_stations if s.station_code}
        api_codes = {s.station_code for s in api_stations if s.station_code}
        
        matched = csv_codes & api_codes
        missing = api_codes - csv_codes
        extra = csv_codes - api_codes
        
        return list(matched), list(missing), list(extra)
    
    @staticmethod
    def compare_station_fields(csv_station: StationRecord, 
                               api_station: StationRecord) -> Dict[str, Tuple[Any, Any, ConfidenceLevel]]:
        """
        Compare fields between two station records.
        
        Returns:
            Dict[field_name] = (csv_value, api_value, confidence)
        """
        mismatches = {}
        
        fields = ['distance_km', 'arrival_time', 'departure_time', 'platform', 'halt_minutes']
        
        for field in fields:
            csv_val = getattr(csv_station, field)
            api_val = getattr(api_station, field)
            
            if csv_val != api_val:
                # Determine confidence based on field type
                if api_val is None:
                    confidence = ConfidenceLevel.LOW  # API missing data
                elif csv_val is None:
                    confidence = ConfidenceLevel.HIGH  # API has data, CSV missing
                else:
                    confidence = ConfidenceLevel.HIGH  # Clear mismatch
                
                mismatches[field] = (csv_val, api_val, confidence)
        
        return mismatches


class MasterDataCorrectionPipeline:
    """Main pipeline for master data correction"""
    
    def __init__(self, csv_path: str, rappid_client: RAPPIDMasterClient):
        self.csv_path = csv_path
        self.rappid_client = rappid_client
        self.normalizer = DataNormalizer()
        self.comparator = DataComparator()
        self.results = []
        self.all_corrections = []
        self.invalid_trains = []
    
    async def process_all_trains(self, sample_size: Optional[int] = None) -> List[TrainValidationResult]:
        """
        Process all unique trains in CSV.
        
        Args:
            sample_size: If specified, process only first N trains
        
        Returns:
            List of validation results
        """
        logger.info(f"Loading CSV from {self.csv_path}")
        df = pd.read_csv(self.csv_path, low_memory=False)
        
        unique_trains = df['Train No'].unique()[:sample_size] if sample_size else df['Train No'].unique()
        
        # Filter out invalid train numbers (non-numeric)
        valid_trains = [t for t in unique_trains if str(t).strip() and str(t).isdigit()]
        invalid_count = len(unique_trains) - len(valid_trains)
        
        logger.info(f"Found {len(unique_trains)} unique trains ({invalid_count} invalid/non-numeric)")
        logger.info(f"Processing {len(valid_trains)} valid trains")
        
        # Process in batches for better async handling
        batch_size = 50
        for i in range(0, len(valid_trains), batch_size):
            batch = valid_trains[i:i+batch_size]
            batch_results = await asyncio.gather(
                *[self._process_train(df, train_no) for train_no in batch],
                return_exceptions=True
            )
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Error in batch: {result}")
                else:
                    self.results.append(result)
            
            logger.info(f"Processed {min(i+batch_size, len(valid_trains))}/{len(valid_trains)} trains")
        
        return self.results
    
    async def _process_train(self, df: pd.DataFrame, train_no: str) -> TrainValidationResult:
        """Process a single train"""
        start_time = time.time()
        
        try:
            # Get CSV data for this train
            csv_rows = df[df['Train No'] == train_no].to_dict('records')
            csv_stations = self.normalizer.extract_stations_from_csv(csv_rows)
            
            # Fetch from RAPPID API
            api_data = await self.rappid_client.fetch_train_data(train_no)
            api_response_time = (time.time() - start_time) * 1000
            
            if api_data is None:
                return TrainValidationResult(
                    train_no=train_no,
                    status='UNVERIFIED',
                    csv_stations=len(csv_stations),
                    api_stations=0,
                    corrections_made=0,
                    warnings=['Could not fetch data from RAPPID API'],
                    errors=['API returned None'],
                    records=[],
                    confidence_score=0.0,
                    api_response_time_ms=api_response_time
                )
            
            # Extract API stations
            api_stations = self.normalizer.extract_stations_from_api(api_data)
            
            if not api_stations:
                return TrainValidationResult(
                    train_no=train_no,
                    status='INVALID',
                    csv_stations=len(csv_stations),
                    api_stations=0,
                    corrections_made=0,
                    warnings=['API returned empty station list'],
                    errors=['Invalid train data from API'],
                    records=[],
                    confidence_score=0.0,
                    api_response_time_ms=api_response_time
                )
            
            # Compare stations
            matched, missing, extra = self.comparator.match_stations(csv_stations, api_stations)
            
            # Analyze mismatches
            corrections = []
            warnings = []
            
            if missing:
                warnings.append(f"Missing stations in CSV: {missing}")
            if extra:
                warnings.append(f"Extra stations in CSV: {extra}")
            
            # Compare matched stations field by field
            csv_by_code = {s.station_code: s for s in csv_stations}
            api_by_code = {s.station_code: s for s in api_stations}
            
            for code in matched:
                csv_station = csv_by_code[code]
                api_station = api_by_code[code]
                
                mismatches = self.comparator.compare_station_fields(csv_station, api_station)
                
                for field, (csv_val, api_val, confidence) in mismatches.items():
                    corrections.append(TrainCorrectionRecord(
                        train_no=train_no,
                        field=f"{code}.{field}",
                        old_value=csv_val,
                        new_value=api_val,
                        confidence=confidence,
                        timestamp=datetime.now().isoformat(),
                        api_source='RAPPID'
                    ))
            
            # Determine overall status
            if not corrections and not missing and not extra:
                status = 'MATCHED'
                confidence_score = 1.0
            elif corrections and not missing and not extra:
                status = 'CORRECTED'
                confidence_score = sum(c.confidence.value for c in corrections) / len(corrections)
            else:
                status = 'CORRECTED'
                confidence_score = 0.75  # Partial match
            
            self.all_corrections.extend(corrections)
            
            return TrainValidationResult(
                train_no=train_no,
                status=status,
                csv_stations=len(csv_stations),
                api_stations=len(api_stations),
                corrections_made=len(corrections),
                warnings=warnings,
                errors=[],
                records=corrections,
                confidence_score=confidence_score,
                api_response_time_ms=api_response_time
            )
        
        except Exception as e:
            logger.error(f"Error processing train {train_no}: {e}\n{traceback.format_exc()}")
            return TrainValidationResult(
                train_no=train_no,
                status='UNVERIFIED',
                csv_stations=0,
                api_stations=0,
                corrections_made=0,
                warnings=[],
                errors=[str(e)],
                records=[],
                confidence_score=0.0,
                api_response_time_ms=(time.time() - start_time) * 1000
            )
    
    def generate_reports(self, output_dir: str = "."):
        """Generate output artifacts"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Reconciliation Report (detailed corrections)
        reconciliation_data = []
        for correction in self.all_corrections:
            reconciliation_data.append({
                'Train No': correction.train_no,
                'Field': correction.field,
                'Old Value': correction.old_value,
                'New Value': correction.new_value,
                'Confidence': correction.confidence.name,
                'Confidence Score': correction.confidence.value,
                'Timestamp': correction.timestamp,
                'Source': correction.api_source
            })
        
        if reconciliation_data:
            df_reconciliation = pd.DataFrame(reconciliation_data)
            recon_path = os.path.join(output_dir, 'reconciliation_report.csv')
            df_reconciliation.to_csv(recon_path, index=False)
            logger.info(f"Reconciliation report saved: {recon_path}")
        
        # 2. Summary Report (by train)
        summary_data = []
        for result in self.results:
            summary_data.append({
                'Train No': result.train_no,
                'Status': result.status,
                'CSV Stations': result.csv_stations,
                'API Stations': result.api_stations,
                'Corrections': result.corrections_made,
                'Confidence Score': result.confidence_score,
                'API Response Time (ms)': result.api_response_time_ms,
                'Warnings': ' | '.join(result.warnings)
            })
        
        if summary_data:
            df_summary = pd.DataFrame(summary_data)
            summary_path = os.path.join(output_dir, 'correction_summary.csv')
            df_summary.to_csv(summary_path, index=False)
            logger.info(f"Summary report saved: {summary_path}")
        
        # 3. Invalid Trains Report
        invalid_trains = [r for r in self.results if r.status in ['UNVERIFIED', 'INVALID']]
        if invalid_trains:
            invalid_data = []
            for result in invalid_trains:
                invalid_data.append({
                    'Train No': result.train_no,
                    'Status': result.status,
                    'Error': ' | '.join(result.errors),
                    'Warnings': ' | '.join(result.warnings)
                })
            
            df_invalid = pd.DataFrame(invalid_data)
            invalid_path = os.path.join(output_dir, 'invalid_trains.csv')
            df_invalid.to_csv(invalid_path, index=False)
            logger.info(f"Invalid trains report saved: {invalid_path}")
        
        return {
            'reconciliation_report': reconciliation_data,
            'summary_report': summary_data,
            'invalid_trains': invalid_trains
        }
    
    def print_statistics(self):
        """Print summary statistics"""
        total = len(self.results)
        matched = len([r for r in self.results if r.status == 'MATCHED'])
        corrected = len([r for r in self.results if r.status == 'CORRECTED'])
        unverified = len([r for r in self.results if r.status == 'UNVERIFIED'])
        
        logger.info(f"\n{'='*60}")
        logger.info(f"MASTER DATA CORRECTION PIPELINE - FINAL REPORT")
        logger.info(f"{'='*60}")
        logger.info(f"Total trains processed: {total}")
        logger.info(f"  ✅ Matched (no corrections): {matched} ({100*matched/total:.1f}%)")
        logger.info(f"  🔧 Corrected: {corrected} ({100*corrected/total:.1f}%)")
        logger.info(f"  ⚠️  Unverified/Invalid: {unverified} ({100*unverified/total:.1f}%)")
        logger.info(f"\nTotal corrections made: {len(self.all_corrections)}")
        
        if self.all_corrections:
            confidence_scores = [c.confidence.value for c in self.all_corrections]
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            logger.info(f"Average confidence: {avg_confidence:.2%}")
        
        logger.info(f"\nAPI Statistics:")
        logger.info(f"  Successful calls: {self.rappid_client.stats['successful_calls']}")
        logger.info(f"  Failed calls: {self.rappid_client.stats['failed_calls']}")
        logger.info(f"  Cached calls: {self.rappid_client.stats['cached_calls']}")
        logger.info(f"  Rate limit hits: {self.rappid_client.stats['rate_limit_hits']}")
        logger.info(f"{'='*60}\n")


async def main():
    """Example usage"""
    csv_path = "Clean_Dataset.csv"
    
    async with aiohttp.ClientSession() as session:
        rappid_client = RAPPIDMasterClient(session)
        pipeline = MasterDataCorrectionPipeline(csv_path, rappid_client)
        
        # Process first 100 trains as example
        results = await pipeline.process_all_trains(sample_size=100)
        
        # Generate reports
        pipeline.generate_reports(output_dir="correction_outputs")
        
        # Print statistics
        pipeline.print_statistics()


if __name__ == "__main__":
    asyncio.run(main())
