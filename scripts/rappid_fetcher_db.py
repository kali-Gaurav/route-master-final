"""
RAPPID Fetcher Integration with SQLite Database

Updated version that pushes fetched data directly to the database
instead of just storing raw JSON files.

Features:
- Fetches train data from RAPPID API
- Stores raw responses as JSON (backup)
- Pushes structured data to SQLite database
- Circuit breaker pattern for resilience
- Rate limiting and exponential backoff

Usage:
    fetcher = RAPPIDFetcherDB()
    success, data, error = fetcher.fetch_and_store_train("16320")
"""

import json
import requests
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import logging

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from database_manager import get_db

logger = logging.getLogger(__name__)

# Configuration
RAPPID_API_BASE = "https://api.rappid.co.in/train"
RAPPID_API_TIMEOUT = 10
RAPPID_API_MAX_RETRIES = 3
RAPPID_API_BACKOFF_FACTOR = 2
RAW_RAPPID_DIR = Path("data/raw_rappid")
RATE_LIMIT = {
    "requests_per_second": 2.0,
    "burst_limit": 10,
    "circuit_breaker_threshold": 5,
    "circuit_breaker_timeout": 60
}


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """Circuit Breaker Pattern Implementation"""
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
        self.last_failure_time = None
        self._lock = threading.Lock()
    
    def record_success(self):
        """Record successful request"""
        with self._lock:
            self.failure_count = 0
            self.state = CircuitBreakerState.CLOSED
    
    def record_failure(self):
        """Record failed request"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")
    
    def is_available(self) -> bool:
        """Check if circuit breaker allows requests"""
        with self._lock:
            if self.state == CircuitBreakerState.CLOSED:
                return True
            
            if self.state == CircuitBreakerState.OPEN:
                if datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.timeout_seconds):
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.failure_count = 0
                    logger.info("Circuit breaker HALF_OPEN - testing recovery")
                    return True
                return False
            
            return self.state == CircuitBreakerState.HALF_OPEN


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, requests_per_second: float = 2.0, burst_limit: int = 10):
        self.requests_per_second = requests_per_second
        self.burst_limit = burst_limit
        self.tokens = burst_limit
        self.last_refill_time = time.time()
        self._lock = threading.Lock()
    
    def _refill_tokens(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill_time
        tokens_to_add = elapsed * self.requests_per_second
        
        self.tokens = min(self.burst_limit, self.tokens + tokens_to_add)
        self.last_refill_time = now
    
    def acquire(self, blocking: bool = True, timeout: float = 60) -> bool:
        """Acquire a token for making a request"""
        with self._lock:
            start_time = time.time()
            
            while True:
                self._refill_tokens()
                
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True
                
                if not blocking:
                    return False
                
                if time.time() - start_time > timeout:
                    return False
                
                wait_time = 1.0 / self.requests_per_second
                time.sleep(min(wait_time, 0.1))


class RAPPIDFetcherDB:
    """
    RAPPID Fetcher with Database Integration
    
    Fetches data from RAPPID API and stores in SQLite database.
    Replaces simple JSON file storage with structured database records.
    """
    
    def __init__(self, db=None):
        """Initialize fetcher.
        
        Args:
            db: DatabaseManager instance (uses singleton if None)
        """
        self.base_url = RAPPID_API_BASE
        self.timeout = RAPPID_API_TIMEOUT
        self.max_retries = RAPPID_API_MAX_RETRIES
        self.backoff_factor = RAPPID_API_BACKOFF_FACTOR
        self.db = db or get_db()
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            requests_per_second=RATE_LIMIT["requests_per_second"],
            burst_limit=RATE_LIMIT["burst_limit"]
        )
        
        # Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=RATE_LIMIT["circuit_breaker_threshold"],
            timeout_seconds=RATE_LIMIT["circuit_breaker_timeout"]
        )
        
        # Session for connection pooling
        self.session = requests.Session()
        
        # Create raw data directory if it doesn't exist
        RAW_RAPPID_DIR.mkdir(parents=True, exist_ok=True)
    
    def fetch_and_store_train(self, train_no: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Fetch train data from RAPPID API and store in database.
        
        Args:
            train_no: Train number (e.g., "16320")
        
        Returns:
            (success, data, error_message)
        """
        # Check circuit breaker
        if not self.circuit_breaker.is_available():
            error_msg = "Circuit breaker OPEN - API temporarily unavailable"
            logger.warning(f"{error_msg} for train {train_no}")
            return False, None, error_msg
        
        # Request rate token
        if not self.rate_limiter.acquire(blocking=True, timeout=30):
            error_msg = "Rate limiter timeout - too many requests"
            logger.warning(f"{error_msg} for train {train_no}")
            return False, None, error_msg
        
        # Attempt to fetch with retries
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching train {train_no} (attempt {attempt + 1}/{self.max_retries})")
                
                url = f"{self.base_url}/{train_no}"
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                
                # Store raw response as JSON backup
                self._save_raw_response(train_no, data)
                
                # Store in database
                self._store_in_database(train_no, data)
                
                # Record success
                self.circuit_breaker.record_success()
                logger.info(f"✓ Successfully fetched and stored train {train_no}")
                
                return True, data, None
            
            except requests.exceptions.RequestException as e:
                logger.warning(f"Fetch failed for train {train_no}: {e}")
                
                if attempt < self.max_retries - 1:
                    wait_time = self.backoff_factor ** attempt
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    self.circuit_breaker.record_failure()
                    error_msg = f"Failed to fetch train {train_no} after {self.max_retries} retries"
                    return False, None, error_msg
            
            except Exception as e:
                logger.error(f"Unexpected error fetching train {train_no}: {e}")
                self.circuit_breaker.record_failure()
                return False, None, str(e)
        
        return False, None, "Unknown error"
    
    def _save_raw_response(self, train_no: str, data: Dict) -> None:
        """Save raw API response as JSON file for backup.
        
        Args:
            train_no: Train number
            data: Raw API response data
        """
        try:
            file_path = RAW_RAPPID_DIR / f"{train_no}.json"
            with open(file_path, 'w') as f:
                json.dump({
                    'train_no': train_no,
                    'timestamp': datetime.utcnow().isoformat(),
                    'data': data
                }, f, indent=2)
            logger.debug(f"Saved raw response to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save raw response for train {train_no}: {e}")
    
    def _store_in_database(self, train_no: str, data: Dict) -> None:
        """
        Store fetched data in SQLite database.
        
        Args:
            train_no: Train number
            data: API response data
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Extract train-level information
            train_name = data.get('train_name', 'Unknown')
            
            # Upsert train record
            cursor.execute("""
                INSERT OR REPLACE INTO trains
                (train_no, train_name, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (train_no, train_name))
            
            # Extract and store station information
            stations = data.get('stations', [])
            for idx, station in enumerate(stations):
                station_code = station.get('code', '').upper()
                station_name = station.get('name', '')
                
                if not station_code or not station_name:
                    continue
                
                # Insert or ignore station
                cursor.execute("""
                    INSERT OR IGNORE INTO stations
                    (station_code, station_name, created_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (station_code, station_name))
                
                # Get station ID
                cursor.execute("SELECT id FROM stations WHERE station_code = ?", (station_code,))
                station_id_row = cursor.fetchone()
                if not station_id_row:
                    continue
                station_id = station_id_row[0]
                
                # Get train ID
                cursor.execute("SELECT id FROM trains WHERE train_no = ?", (train_no,))
                train_id_row = cursor.fetchone()
                if not train_id_row:
                    continue
                train_id = train_id_row[0]
                
                # Insert or ignore route
                cursor.execute("""
                    INSERT OR IGNORE INTO train_stations
                    (train_id, station_id, sequence, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (train_id, station_id, idx))
            
            conn.commit()
            logger.info(f"Stored train {train_no} in database")
        
        except Exception as e:
            logger.error(f"Failed to store train {train_no} in database: {e}")
            if 'conn' in locals():
                conn.rollback()
    
    def fetch_batch(self, train_numbers: List[str], delay_between_requests: float = 0.5) -> Tuple[int, int]:
        """
        Fetch multiple trains in batch.
        
        Args:
            train_numbers: List of train numbers to fetch
            delay_between_requests: Delay between requests in seconds
        
        Returns:
            (successful_count, failed_count)
        """
        successful = 0
        failed = 0
        
        for train_no in train_numbers:
            success, data, error = self.fetch_and_store_train(train_no)
            
            if success:
                successful += 1
                logger.info(f"✓ Batch: {successful} successful, {failed} failed")
            else:
                failed += 1
                logger.warning(f"✗ Batch: {successful} successful, {failed} failed")
            
            if delay_between_requests > 0:
                time.sleep(delay_between_requests)
        
        logger.info(f"Batch complete: {successful} successful, {failed} failed")
        return successful, failed


def main():
    """CLI entry point for testing fetcher."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fetch and store RAPPID train data in SQLite"
    )
    parser.add_argument('train_no', help='Train number to fetch')
    parser.add_argument('--batch', nargs='+', help='Multiple train numbers')
    
    args = parser.parse_args()
    
    fetcher = RAPPIDFetcherDB()
    
    if args.batch:
        # Batch mode
        logger.info(f"Fetching batch of {len(args.batch)} trains...")
        successful, failed = fetcher.fetch_batch(args.batch)
        print(f"\nResults: {successful} successful, {failed} failed")
    else:
        # Single train
        success, data, error = fetcher.fetch_and_store_train(args.train_no)
        if success:
            print(f"✓ Successfully fetched train {args.train_no}")
            print(json.dumps(data, indent=2))
        else:
            print(f"✗ Failed to fetch train {args.train_no}: {error}")


if __name__ == "__main__":
    main()
