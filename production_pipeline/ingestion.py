"""
Data Ingestion Layer

Handles fetching, validating, and caching of train data from external APIs.
Implements rate limiting, retry logic, and caching with TTL.

Features:
- AsyncIO-based HTTP client
- Rate limiting (10 RPS configurable)
- Exponential backoff retry logic
- TTL-based caching with disk backing
- Comprehensive error handling
- Immutable raw payload storage
"""

import asyncio
import aiohttp
import time
import json
import hashlib
import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque
import pickle

from production_pipeline.config import get_config


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class RateLimitWindow:
    """Tracks requests for rate limiting"""
    requests: deque = None  # timestamps of requests
    max_requests: int = 10  # RPS
    window_seconds: int = 1
    
    def __post_init__(self):
        if self.requests is None:
            self.requests = deque()
    
    def is_rate_limited(self) -> bool:
        """Check if rate limit exceeded"""
        now = time.time()
        # Remove old requests outside window
        while self.requests and self.requests[0] < now - self.window_seconds:
            self.requests.popleft()
        return len(self.requests) >= self.max_requests
    
    def record_request(self):
        """Record a request"""
        self.requests.append(time.time())
    
    async def wait_if_needed(self):
        """Wait if rate limited"""
        while self.is_rate_limited():
            await asyncio.sleep(0.01)
        self.record_request()


class CacheManager:
    """Manages caching with TTL and disk backing"""
    
    def __init__(self, cache_dir: Path, ttl_seconds: int = 3600):
        """Initialize cache manager
        
        Args:
            cache_dir: Directory for disk cache
            ttl_seconds: Time to live in seconds
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self.memory_cache = {}
    
    def _get_cache_key(self, source: str, entity_id: str) -> str:
        """Generate cache key"""
        key = f"{source}:{entity_id}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get disk cache file path"""
        return self.cache_dir / f"{cache_key}.cache"
    
    def get(self, source: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get from cache (memory first, then disk)
        
        Args:
            source: Data source (e.g., RAPPID)
            entity_id: Entity identifier
            
        Returns:
            Cached data or None if expired/missing
        """
        cache_key = self._get_cache_key(source, entity_id)
        
        # Check memory cache
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if entry["expires_at"] > datetime.utcnow():
                logger.debug(f"Cache hit (memory): {cache_key}")
                return entry["data"]
            else:
                del self.memory_cache[cache_key]
        
        # Check disk cache
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                with open(cache_path, "rb") as f:
                    entry = pickle.load(f)
                if entry["expires_at"] > datetime.utcnow():
                    logger.debug(f"Cache hit (disk): {cache_key}")
                    # Promote to memory cache
                    self.memory_cache[cache_key] = entry
                    return entry["data"]
                else:
                    cache_path.unlink()  # Delete expired cache
            except Exception as e:
                logger.warning(f"Error reading cache: {e}")
                cache_path.unlink(missing_ok=True)
        
        return None
    
    def set(self, source: str, entity_id: str, data: Dict[str, Any]):
        """Store in cache (memory and disk)
        
        Args:
            source: Data source
            entity_id: Entity identifier
            data: Data to cache
        """
        cache_key = self._get_cache_key(source, entity_id)
        entry = {
            "data": data,
            "expires_at": datetime.utcnow() + timedelta(seconds=self.ttl_seconds),
            "created_at": datetime.utcnow(),
        }
        
        # Store in memory
        self.memory_cache[cache_key] = entry
        
        # Store on disk
        try:
            cache_path = self._get_cache_path(cache_key)
            with open(cache_path, "wb") as f:
                pickle.dump(entry, f)
            logger.debug(f"Cached: {cache_key}")
        except Exception as e:
            logger.warning(f"Error writing cache: {e}")
    
    def clear_expired(self):
        """Clean up expired cache files"""
        now = datetime.utcnow()
        
        # Memory cache
        expired_keys = [k for k, v in self.memory_cache.items() 
                       if v["expires_at"] < now]
        for key in expired_keys:
            del self.memory_cache[key]
        
        # Disk cache
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                with open(cache_file, "rb") as f:
                    entry = pickle.load(f)
                if entry["expires_at"] < now:
                    cache_file.unlink()
            except Exception as e:
                logger.debug(f"Error cleaning cache: {e}")


class AsyncHTTPClient:
    """Async HTTP client with rate limiting, retries, and caching"""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """Initialize HTTP client
        
        Args:
            cache_manager: Optional cache manager for response caching
        """
        config = get_config()
        self.rate_limiter = RateLimitWindow(
            max_requests=config.ingestion.rate_limit_rps,
            window_seconds=1
        )
        self.max_retries = config.ingestion.max_retries
        self.retry_backoff_factor = config.ingestion.retry_backoff_factor
        self.cache_manager = cache_manager
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_timeout = aiohttp.ClientTimeout(total=30)
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()
    
    async def start(self):
        """Start HTTP session"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.request_timeout,
            headers={"User-Agent": "RailwayRouteMaster/1.0"}
        )
        logger.info("HTTP client started")
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            logger.info("HTTP client closed")
    
    async def fetch(
        self,
        url: str,
        method: str = "GET",
        use_cache: bool = True,
        cache_key: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Fetch from URL with rate limiting, retries, and caching
        
        Args:
            url: URL to fetch
            method: HTTP method (GET, POST)
            use_cache: Whether to use cache
            cache_key: Cache key (source:entity_id). If None, cache disabled
            **kwargs: Additional arguments for aiohttp
            
        Returns:
            Response data as dict
            
        Raises:
            Exception: If all retries exhausted
        """
        if not self.session:
            raise RuntimeError("HTTP client not started. Use 'async with' context manager.")
        
        # Check cache first
        if use_cache and cache_key:
            source, entity_id = cache_key.split(":")
            cached_data = self.cache_manager.get(source, entity_id) if self.cache_manager else None
            if cached_data:
                return cached_data
        
        # Perform request with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Rate limit
                await self.rate_limiter.wait_if_needed()
                
                # Make request
                async with self.session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Cache successful response
                        if use_cache and cache_key and self.cache_manager:
                            source, entity_id = cache_key.split(":")
                            self.cache_manager.set(source, entity_id, data)
                        
                        logger.info(f"Fetched: {url} (attempt {attempt + 1})")
                        return data
                    else:
                        last_error = f"HTTP {response.status}"
                        if attempt < self.max_retries - 1:
                            logger.warning(f"Request failed: {url} ({response.status}). Retrying...")
                
            except asyncio.TimeoutError:
                last_error = "Timeout"
                if attempt < self.max_retries - 1:
                    logger.warning(f"Request timeout: {url}. Retrying...")
            
            except Exception as e:
                last_error = str(e)
                if attempt < self.max_retries - 1:
                    logger.warning(f"Request error: {url}. Retrying... ({e})")
            
            # Exponential backoff
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt * self.retry_backoff_factor
                logger.debug(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        logger.error(f"Failed to fetch {url} after {self.max_retries} retries: {last_error}")
        raise Exception(f"Failed to fetch {url}: {last_error}")
    
    async def fetch_batch(self, requests: List[Dict[str, Any]], max_concurrent: int = 5) -> List[Dict[str, Any]]:
        """Fetch multiple URLs concurrently with controlled concurrency
        
        Args:
            requests: List of request specs with keys: url, method, cache_key, etc
            max_concurrent: Max concurrent requests
            
        Returns:
            List of response data
        """
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(req: Dict[str, Any]):
            async with semaphore:
                try:
                    result = await self.fetch(**req)
                    return {"success": True, "data": result}
                except Exception as e:
                    logger.error(f"Batch fetch failed: {req.get('url')}: {e}")
                    return {"success": False, "error": str(e)}
        
        tasks = [fetch_with_semaphore(req) for req in requests]
        results = await asyncio.gather(*tasks)
        return results


class RAPPIDFetcher:
    """Fetches data from RAPPID API"""
    
    def __init__(self, http_client: AsyncHTTPClient):
        """Initialize RAPPID fetcher
        
        Args:
            http_client: AsyncHTTPClient instance
        """
        self.http_client = http_client
        self.base_url = "https://rappid.example.com/api/v1"  # Placeholder
        logger.info("RAPPID Fetcher initialized")
    
    async def fetch_trains(self, source_code: str, destination_code: str) -> Dict[str, Any]:
        """Fetch trains for a route
        
        Args:
            source_code: Source station code
            destination_code: Destination station code
            
        Returns:
            Train data dict
        """
        url = f"{self.base_url}/trains"
        params = {
            "from": source_code,
            "to": destination_code
        }
        
        cache_key = f"RAPPID:{source_code}-{destination_code}"
        return await self.http_client.fetch(
            url,
            params=params,
            use_cache=True,
            cache_key=cache_key
        )
    
    async def fetch_stations(self) -> Dict[str, Any]:
        """Fetch all stations
        
        Returns:
            Stations data dict
        """
        url = f"{self.base_url}/stations"
        cache_key = "RAPPID:stations"
        return await self.http_client.fetch(
            url,
            use_cache=True,
            cache_key=cache_key
        )
    
    async def fetch_train_details(self, train_no: str) -> Dict[str, Any]:
        """Fetch details for a specific train
        
        Args:
            train_no: Train number
            
        Returns:
            Train details dict
        """
        url = f"{self.base_url}/trains/{train_no}"
        cache_key = f"RAPPID:{train_no}"
        return await self.http_client.fetch(
            url,
            use_cache=True,
            cache_key=cache_key
        )


class IngestionOrchestrator:
    """Orchestrates data ingestion from multiple sources"""
    
    def __init__(self, http_client: AsyncHTTPClient):
        """Initialize ingestion orchestrator
        
        Args:
            http_client: AsyncHTTPClient instance
        """
        self.http_client = http_client
        self.rappid_fetcher = RAPPIDFetcher(http_client)
        logger.info("Ingestion Orchestrator initialized")
    
    async def ingest_all_data(self) -> Dict[str, Any]:
        """Ingest all data from sources
        
        Returns:
            Ingestion results summary
        """
        logger.info("Starting data ingestion...")
        results = {
            "success": True,
            "sources_completed": [],
            "errors": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Fetch stations
            logger.info("Fetching stations...")
            stations_data = await self.rappid_fetcher.fetch_stations()
            results["sources_completed"].append("stations")
            
            # TODO: Fetch trains for common routes
            # This would need a list of important routes from config
            
            logger.info("Data ingestion completed successfully")
        
        except Exception as e:
            logger.error(f"Ingestion error: {e}")
            results["success"] = False
            results["errors"].append(str(e))
        
        return results
