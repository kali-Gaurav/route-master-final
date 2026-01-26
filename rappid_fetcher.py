"""
Raw Fetch Layer for RAPPID API

Stores raw API responses as immutable JSON files:
- 16320.json (train 16320 raw response)
- 12951.json (train 12951 raw response)
- etc.

Features:
- Rate limiting and throttling
- Circuit breaker pattern for API failures
- Exponential backoff for retries
- Complete audit trail in fetch_logs
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

from config import (
    RAPPID_API_BASE, RAPPID_API_TIMEOUT, RAPPID_API_MAX_RETRIES,
    RAPPID_API_BACKOFF_FACTOR, RAW_RAPPID_DIR, RATE_LIMIT
)
from logger import logger, audit_logger, LoggerFactory
from database import Train, TrainStation, Station, FetchLog, FetchStatus, TrainStatus


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"          # Normal operation
    OPEN = "OPEN"              # API failing, reject calls
    HALF_OPEN = "HALF_OPEN"   # Testing recovery


@dataclass
class RateLimitInfo:
    """Rate limit tracking"""
    requests_made: int = 0
    requests_limit: int = 100
    reset_time: Optional[datetime] = None
    last_request_time: Optional[datetime] = None


class CircuitBreaker:
    """
    Circuit Breaker Pattern Implementation
    Prevents cascading failures from APIs
    """
    
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
                logger.warning(
                    f"Circuit breaker OPEN after {self.failure_count} failures",
                    extra={"circuit_breaker_state": "OPEN"}
                )
    
    def is_available(self) -> bool:
        """Check if circuit breaker allows requests"""
        with self._lock:
            if self.state == CircuitBreakerState.CLOSED:
                return True
            
            if self.state == CircuitBreakerState.OPEN:
                # Check if timeout has passed
                if datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.timeout_seconds):
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.failure_count = 0
                    logger.info("Circuit breaker HALF_OPEN - testing recovery")
                    return True
                return False
            
            return self.state == CircuitBreakerState.HALF_OPEN


class RateLimiter:
    """
    Token bucket rate limiter
    Respects API rate limits and spreads requests
    """
    
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
        """
        Acquire a token for making a request
        
        Args:
            blocking: Wait if no tokens available
            timeout: Maximum time to wait (seconds)
        
        Returns:
            True if token acquired, False otherwise
        """
        with self._lock:
            start_time = time.time()
            
            while True:
                self._refill_tokens()
                
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True
                
                if not blocking:
                    return False
                
                # Check timeout
                if time.time() - start_time > timeout:
                    return False
                
                # Sleep and retry
                wait_time = 1.0 / self.requests_per_second
                time.sleep(min(wait_time, 0.1))


class RAPPIDFetcher:
    """
    Main fetcher for RAPPID API
    Manages all raw data fetching with resilience and audit logging
    """
    
    def __init__(self):
        self.base_url = RAPPID_API_BASE
        self.timeout = RAPPID_API_TIMEOUT
        self.max_retries = RAPPID_API_MAX_RETRIES
        self.backoff_factor = RAPPID_API_BACKOFF_FACTOR
        
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
        
        self.logger = LoggerFactory.get_logger("rappid_fetcher")
    
    def fetch_train_details(self, train_no: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Fetch train details from RAPPID API
        
        Args:
            train_no: Train number (e.g., "16320")
        
        Returns:
            (success, data, error_message)
        """
        # Check circuit breaker
        if not self.circuit_breaker.is_available():
            error_msg = "Circuit breaker OPEN - API temporarily unavailable"
            self.logger.warning(error_msg, extra={"train_no": train_no})
            return False, None, error_msg
        
        # Acquire rate limit token
        if not self.rate_limiter.acquire(blocking=True, timeout=30):
            error_msg = "Rate limit timeout - could not acquire token"
            self.logger.warning(error_msg, extra={"train_no": train_no})
            return False, None, error_msg
        
        # Retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                # Construct API endpoint
                url = f"{self.base_url}/api/v1/trains/{train_no}"
                
                # Make request
                response = self.session.get(url, timeout=self.timeout)
                response_time_ms = (time.time() - start_time) * 1000
                
                # Log API call
                audit_logger.log_api_call(
                    api_name="RAPPID",
                    method="GET",
                    endpoint=f"/api/v1/trains/{train_no}",
                    status_code=response.status_code,
                    response_time_ms=response_time_ms,
                    records_count=1 if response.status_code == 200 else 0
                )
                
                # Check response
                if response.status_code == 200:
                    data = response.json()
                    self.circuit_breaker.record_success()
                    
                    self.logger.info(
                        f"Train fetched successfully: {train_no}",
                        extra={
                            "train_no": train_no,
                            "status_code": 200,
                            "response_time_ms": response_time_ms,
                            "attempt": attempt + 1
                        }
                    )
                    
                    return True, data, None
                
                elif response.status_code == 404:
                    # Train not found
                    error_msg = f"Train {train_no} not found (404)"
                    self.logger.warning(error_msg, extra={"train_no": train_no})
                    self.circuit_breaker.record_success()
                    return False, None, error_msg
                
                elif response.status_code == 429:
                    # Rate limited
                    error_msg = f"Rate limited (429) on attempt {attempt + 1}"
                    self.logger.warning(error_msg, extra={"train_no": train_no, "attempt": attempt + 1})
                    
                    # Extract wait time if provided
                    retry_after = response.headers.get("Retry-After", str(int(self.backoff_factor ** attempt)))
                    wait_time = int(retry_after)
                    
                    if attempt < self.max_retries - 1:
                        self.logger.info(f"Waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                    continue
                
                else:
                    # Other errors
                    error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                    self.logger.warning(error_msg, extra={"train_no": train_no})
                    self.circuit_breaker.record_failure()
                    
                    if attempt < self.max_retries - 1:
                        wait_time = self.backoff_factor ** attempt
                        self.logger.info(f"Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    continue
            
            except requests.Timeout:
                error_msg = f"Timeout on attempt {attempt + 1}"
                self.logger.warning(error_msg, extra={"train_no": train_no})
                self.circuit_breaker.record_failure()
                
                if attempt < self.max_retries - 1:
                    wait_time = self.backoff_factor ** attempt
                    time.sleep(wait_time)
                continue
            
            except requests.ConnectionError as e:
                error_msg = f"Connection error: {str(e)}"
                self.logger.error(error_msg, extra={"train_no": train_no}, exc_info=True)
                self.circuit_breaker.record_failure()
                
                if attempt < self.max_retries - 1:
                    wait_time = self.backoff_factor ** attempt
                    time.sleep(wait_time)
                continue
            
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                self.logger.error(error_msg, extra={"train_no": train_no}, exc_info=True)
                self.circuit_breaker.record_failure()
                return False, None, error_msg
        
        return False, None, f"Failed after {self.max_retries} retries"
    
    def save_raw_response(self, train_no: str, data: Dict) -> Path:
        """
        Save raw API response as immutable JSON
        
        Args:
            train_no: Train number
            data: API response data
        
        Returns:
            Path to saved file
        """
        file_path = RAW_RAPPID_DIR / f"{train_no}.json"
        
        try:
            # Add metadata
            wrapped_data = {
                "train_no": train_no,
                "fetched_at": datetime.utcnow().isoformat(),
                "data": data
            }
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(wrapped_data, f, indent=2)
            
            self.logger.info(f"Raw data saved: {file_path}")
            return file_path
        
        except Exception as e:
            self.logger.error(f"Failed to save raw data: {e}", exc_info=True)
            raise
    
    def load_raw_response(self, train_no: str) -> Optional[Dict]:
        """Load saved raw response"""
        file_path = RAW_RAPPID_DIR / f"{train_no}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                wrapped_data = json.load(f)
            return wrapped_data.get("data")
        except Exception as e:
            self.logger.error(f"Failed to load raw data: {e}", exc_info=True)
            return None
    
    def fetch_batch(self, train_numbers: List[str]) -> Dict[str, Tuple[bool, Optional[Dict]]]:
        """
        Fetch multiple trains
        
        Args:
            train_numbers: List of train numbers
        
        Returns:
            Dict mapping train_no -> (success, data)
        """
        results = {}
        
        for train_no in train_numbers:
            success, data, error = self.fetch_train_details(train_no)
            
            if success and data:
                self.save_raw_response(train_no, data)
            
            results[train_no] = (success, data)
        
        self.logger.info(
            f"Batch fetch completed: {len([r for r in results.values() if r[0]])}/{len(train_numbers)} successful"
        )
        
        return results
    
    def calculate_data_hash(self, data: Dict) -> str:
        """Calculate SHA256 hash of data for deduplication"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def close(self):
        """Close session"""
        self.session.close()


# Global fetcher instance
fetcher = RAPPIDFetcher()
