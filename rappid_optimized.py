"""
Optimized RAPPID Train API Integration Module
Provides real-time validation with connection pooling and performance optimization
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import time
from threading import Lock
import random # Added for jitter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedRAPPIDClient:
    """Optimized RAPPID API Client with connection pooling and intelligent caching"""
    
    BASE_URL = "https://rappid.in/apis/train.php"
    CACHE_TTL = 300  # 5 minutes
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 10
    POOL_CONNECTIONS = 10
    POOL_MAXSIZE = 10
    
    def __init__(self, timeout: int = 10, retry_attempts: int = 3):
        """
        Initialize optimized RAPPID API Client
        
        Args:
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts
        """
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.session = self._create_session()
        
        # Local cache
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_lock = Lock()
        
        # Performance metrics
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'api_calls': 0,
            'failed_requests': 0,
            'total_response_time': 0.0,
            'min_response_time': float('inf'),
            'max_response_time': 0.0
        }
    
    def _create_session(self) -> requests.Session:
        """Create requests session with connection pooling and retry strategy"""
        session = requests.Session()
        
        # Define retry strategy
        retry_strategy = Retry(
            total=self.MAX_RETRIES,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=0.5,  # 0.5s, 1s, 2s, 4s backoff
            raise_on_status=False
        )
        
        # Configure HTTP adapter with pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.POOL_CONNECTIONS,
            pool_maxsize=self.POOL_MAXSIZE,
            pool_block=False  # Non-blocking pool
        )
        
        # Mount adapter for both http and https
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _is_cache_fresh(self, key: str) -> bool:
        """Check if cache entry is fresh"""
        if key not in self.cache_timestamps:
            return False
        age = (datetime.now() - self.cache_timestamps[key]).total_seconds()
        return age < self.CACHE_TTL
    
    def _get_cached(self, key: str) -> Optional[Dict]:
        """Get data from cache if fresh"""
        with self.cache_lock:
            if key in self.cache and self._is_cache_fresh(key):
                self.stats['cache_hits'] += 1
                logger.debug(f"Cache hit for train {key}")
                return self.cache[key]
            
            self.stats['cache_misses'] += 1
            return None
    
    def _set_cached(self, key: str, data: Dict) -> None:
        """Store data in cache"""
        with self.cache_lock:
            self.cache[key] = data
            self.cache_timestamps[key] = datetime.now()
    
    def _record_response_time(self, response_time: float) -> None:
        """Record response time statistics"""
        self.stats['total_response_time'] += response_time
        self.stats['min_response_time'] = min(self.stats['min_response_time'], response_time)
        self.stats['max_response_time'] = max(self.stats['max_response_time'], response_time)
    
    def get_train_data(self, train_no: str, use_cache: bool = True) -> Optional[Dict]:
        """
        Fetch train data with intelligent caching
        
        Args:
            train_no: Train number
            use_cache: Whether to use cached data
            
        Returns:
            Train data dict or None
        """
        self.stats['total_requests'] += 1
        
        # Check cache first
        if use_cache:
            cached = self._get_cached(train_no)
            if cached:
                return cached
        
        # Fetch from API
        start_time = time.time()
        try:
            data = self._fetch_from_api(train_no)
            response_time = time.time() - start_time
            self._record_response_time(response_time)
            
            if data:
                self._set_cached(train_no, data)
                logger.info(f"Train {train_no}: {response_time*1000:.1f}ms")
            
            return data
        except Exception as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Error fetching train {train_no}: {e}")
            return None
    
    def _fetch_from_api(self, train_no: str) -> Optional[Dict]:
        """Fetch from API with exponential backoff"""
        self.stats['api_calls'] += 1
        params = {'train_no': train_no}
        
        for attempt in range(self.retry_attempts):
            try:
                response = self.session.get(
                    self.BASE_URL,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                data = response.json()
                if data:
                    return data
            
            except requests.exceptions.Timeout:
                # Add jitter to backoff
                wait_time = (2 ** attempt) + random.uniform(0, 1) # Add random jitter up to 1 second
                logger.warning(f"Timeout train {train_no}, retry in {wait_time:.2f}s")
                time.sleep(wait_time)
            
            except requests.exceptions.RequestException as e:
                # Add jitter to backoff
                wait_time = (2 ** attempt) + random.uniform(0, 1) # Add random jitter up to 1 second
                logger.warning(f"Request error train {train_no}: {e}, retry in {wait_time:.2f}s")
                time.sleep(wait_time)
            
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from API for train {train_no}")
                return None
        
        return None
    
    def get_stats(self) -> Dict:
        """Get performance statistics"""
        with self.cache_lock:
            cache_hit_rate = (
                self.stats['cache_hits'] / (self.stats['cache_hits'] + self.stats['cache_misses']) * 100
                if (self.stats['cache_hits'] + self.stats['cache_misses']) > 0 else 0
            )
            
            avg_response_time = (
                self.stats['total_response_time'] / self.stats['api_calls']
                if self.stats['api_calls'] > 0 else 0
            )
            
            return {
                'total_requests': self.stats['total_requests'],
                'cache_hits': self.stats['cache_hits'],
                'cache_misses': self.stats['cache_misses'],
                'cache_hit_rate': f"{cache_hit_rate:.1f}%",
                'api_calls': self.stats['api_calls'],
                'failed_requests': self.stats['failed_requests'],
                'avg_response_time_ms': f"{avg_response_time*1000:.1f}",
                'min_response_time_ms': f"{self.stats['min_response_time']*1000:.1f}" if self.stats['min_response_time'] != float('inf') else "N/A",
                'max_response_time_ms': f"{self.stats['max_response_time']*1000:.1f}",
                'cache_size': len(self.cache)
            }
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        with self.cache_lock:
            self.cache.clear()
            self.cache_timestamps.clear()
            logger.info("Cache cleared")
    
    def warm_cache(self, train_numbers: List[str]) -> Dict:
        """
        Pre-warm cache with specified trains
        
        Args:
            train_numbers: List of train numbers to pre-fetch
            
        Returns:
            Dict with success/failure counts
        """
        logger.info(f"Warming cache for {len(train_numbers)} trains...")
        results = {'success': 0, 'failed': 0}
        
        for train_no in train_numbers:
            try:
                data = self.get_train_data(train_no, use_cache=False)
                if data:
                    results['success'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                logger.error(f"Error warming cache for {train_no}: {e}")
                results['failed'] += 1
        
        logger.info(f"Cache warming complete: {results['success']} success, {results['failed']} failed")
        return results
    
    def __del__(self):
        """Close session on cleanup"""
        try:
            self.session.close()
            logger.debug("Session closed")
        except:
            pass


# Backward compatibility alias
class RAPPIDAPIClient(OptimizedRAPPIDClient):
    """Backward compatible RAPPID client using optimized implementation"""
    pass


class CacheWarmer:
    """Pre-warm cache with high-frequency trains on startup"""
    
    # Top 50 most frequent trains (by popular routes)
    HIGH_FREQUENCY_TRAINS = [
        # Delhi-based trains
        "12970", "14709", "12956", "12952", "12951", "12948", "12947",
        "12941", "12940", "12939", "12938", "12937", "12936", "12935",
        
        # Mumbai-based trains
        "22632", "22631", "22629", "22627", "22625", "22624", "22623",
        "22622", "22621", "22620", "22619", "22618", "22617", "22616",
        
        # Chennai-based trains
        "12678", "12677", "12676", "12675", "16032", "16031",
        "16029", "16028", "16027", "16026", "16025", "16024", "16023",
        
        # Other major trains
        "14004", "14005", "14006", "14007", "14008", "14009", "14010",
        "18246", "18245", "18244", "18243", "18242", "18241", "18240"
    ]
    
    @staticmethod
    def warm_on_startup(client: OptimizedRAPPIDClient) -> Dict:
        """
        Warm cache on server startup
        
        Args:
            client: OptimizedRAPPIDClient instance
            
        Returns:
            Warming results
        """
        logger.info("=" * 60)
        logger.info("CACHE WARMING ON STARTUP")
        logger.info("=" * 60)
        
        start_time = time.time()
        results = client.warm_cache(CacheWarmer.HIGH_FREQUENCY_TRAINS)
        elapsed = time.time() - start_time
        
        logger.info(f"Warming completed in {elapsed:.1f}s")
        logger.info(f"Success: {results['success']}, Failed: {results['failed']}")
        logger.info("=" * 60)
        
        return results


if __name__ == "__main__":
    # Test optimized client
    client = OptimizedRAPPIDClient()
    
    print("\n" + "=" * 60)
    print("RAPPID OPTIMIZED CLIENT TEST")
    print("=" * 60)
    
    # Test single fetch
    print("\n[Test 1] Single train fetch")
    data = client.get_train_data("12970")
    print(f"Status: {'✓ SUCCESS' if data else '✗ FAILED'}")
    
    # Test cache hit
    print("\n[Test 2] Cache hit (same train)")
    data = client.get_train_data("12970")
    print(f"Status: {'✓ SUCCESS' if data else '✗ FAILED'}")
    
    # Show stats
    print("\n[Stats]")
    stats = client.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
