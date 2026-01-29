# core/rate_limiting.py
"""Advanced Rate Limiting with Multiple Strategies"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
import time
import asyncio
from collections import defaultdict
import redis
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class RateLimitStrategy(Enum):
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"

class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    def __init__(self, retry_after: int, limit: int, remaining: int):
        self.retry_after = retry_after
        self.limit = limit
        self.remaining = remaining
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds")

class RateLimiter:
    """Advanced rate limiter with multiple strategies"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.local_limits: Dict[str, List[float]] = defaultdict(list)

    def _get_key(self, identifier: str, endpoint: str) -> str:
        """Generate Redis key for rate limiting"""
        return f"ratelimit:{identifier}:{endpoint}"

    def _clean_old_entries(self, timestamps: List[float], window_seconds: int) -> List[float]:
        """Remove timestamps outside the current window"""
        cutoff = time.time() - window_seconds
        return [ts for ts in timestamps if ts > cutoff]

    async def check_fixed_window(
        self,
        identifier: str,
        endpoint: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Fixed window rate limiting
        Returns: (allowed, remaining, retry_after)
        """
        now = time.time()
        key = self._get_key(identifier, endpoint)

        if self.redis:
            # Redis-based implementation
            try:
                # Use Redis pipeline for atomic operations
                with self.redis.pipeline() as pipe:
                    pipe.zremrangebyscore(key, 0, now - window_seconds)
                    pipe.zcard(key)
                    pipe.zadd(key, {str(now): now})
                    pipe.expire(key, window_seconds)
                    results = pipe.execute()

                current_count = results[1] + 1  # +1 for the request we just added
                remaining = max(0, limit - current_count)
                allowed = current_count <= limit

                if not allowed:
                    retry_after = int(window_seconds - (now - float(self.redis.zrange(key, 0, 0)[0])))
                    retry_after = max(1, retry_after)
                else:
                    retry_after = 0

                return allowed, remaining, retry_after

            except Exception as e:
                logger.warning(f"Redis rate limiting failed, falling back to local: {e}")
                # Fall back to local implementation

        # Local implementation
        timestamps = self.local_limits[key]
        timestamps = self._clean_old_entries(timestamps, window_seconds)
        timestamps.append(now)
        self.local_limits[key] = timestamps

        current_count = len(timestamps)
        remaining = max(0, limit - current_count)
        allowed = current_count <= limit

        if not allowed:
            oldest_timestamp = min(timestamps) if timestamps else now
            retry_after = int(window_seconds - (now - oldest_timestamp))
            retry_after = max(1, retry_after)
        else:
            retry_after = 0

        return allowed, remaining, retry_after

    async def check_sliding_window(
        self,
        identifier: str,
        endpoint: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Sliding window rate limiting (more accurate than fixed window)
        """
        now = time.time()
        key = self._get_key(identifier, endpoint)

        if self.redis:
            try:
                # Remove old entries
                self.redis.zremrangebyscore(key, 0, now - window_seconds)

                # Count current requests in window
                current_count = self.redis.zcard(key) + 1  # +1 for current request

                if current_count <= limit:
                    # Add current request
                    self.redis.zadd(key, {str(now): now})
                    self.redis.expire(key, window_seconds)
                    return True, limit - current_count, 0
                else:
                    # Find when we can retry (when oldest request expires)
                    oldest = self.redis.zrange(key, 0, 0, withscores=True)
                    if oldest:
                        retry_after = int(window_seconds - (now - oldest[0][1]))
                        retry_after = max(1, retry_after)
                    else:
                        retry_after = 1
                    return False, 0, retry_after

            except Exception as e:
                logger.warning(f"Redis sliding window failed: {e}")

        # Local sliding window implementation
        timestamps = self.local_limits[key]
        timestamps = self._clean_old_entries(timestamps, window_seconds)

        if len(timestamps) < limit:
            timestamps.append(now)
            self.local_limits[key] = timestamps
            return True, limit - len(timestamps), 0
        else:
            oldest_timestamp = min(timestamps)
            retry_after = int(window_seconds - (now - oldest_timestamp))
            retry_after = max(1, retry_after)
            return False, 0, retry_after

class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting middleware with endpoint-specific limits"""

    def __init__(self, app, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        self.limiter = RateLimiter(redis_client)
        self.endpoint_limits = {
            # Authentication endpoints - stricter limits
            "/v1/auth/login": (5, 60, RateLimitStrategy.FIXED_WINDOW),  # 5 per minute
            "/v1/auth/register": (3, 60, RateLimitStrategy.FIXED_WINDOW),  # 3 per minute
            "/v1/auth/refresh": (10, 60, RateLimitStrategy.FIXED_WINDOW),  # 10 per minute

            # General API endpoints
            "/v1/routes": (100, 60, RateLimitStrategy.SLIDING_WINDOW),  # 100 per minute
            "/v1/jobs": (50, 60, RateLimitStrategy.SLIDING_WINDOW),  # 50 per minute

            # Default for all other endpoints
            "default": (200, 60, RateLimitStrategy.SLIDING_WINDOW),  # 200 per minute
        }

    def _get_client_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting (IP + User ID if authenticated)"""
        client_ip = request.client.host if request.client else "unknown"

        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"

        return f"ip:{client_ip}"

    def _get_endpoint_limit(self, path: str) -> Tuple[int, int, RateLimitStrategy]:
        """Get rate limit for specific endpoint"""
        for endpoint, limit in self.endpoint_limits.items():
            if endpoint != "default" and path.startswith(endpoint):
                return limit
        return self.endpoint_limits["default"]

    async def dispatch(self, request: Request, call_next):
        """Process the request with rate limiting"""
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/ready", "/docs", "/redoc", "/openapi.json", "/metrics"]:
            return await call_next(request)

        # Skip rate limiting for OPTIONS requests
        if request.method == "OPTIONS":
            return await call_next(request)

        identifier = self._get_client_identifier(request)
        limit, window_seconds, strategy = self._get_endpoint_limit(request.url.path)

        try:
            if strategy == RateLimitStrategy.FIXED_WINDOW:
                allowed, remaining, retry_after = await self.limiter.check_fixed_window(
                    identifier, request.url.path, limit, window_seconds
                )
            elif strategy == RateLimitStrategy.SLIDING_WINDOW:
                allowed, remaining, retry_after = await self.limiter.check_sliding_window(
                    identifier, request.url.path, limit, window_seconds
                )
            else:
                # Default to sliding window
                allowed, remaining, retry_after = await self.limiter.check_sliding_window(
                    identifier, request.url.path, limit, window_seconds
                )

            if not allowed:
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "retry_after": retry_after,
                        "limit": limit,
                        "remaining": remaining
                    }
                )
                response.headers["Retry-After"] = str(retry_after)
                response.headers["X-RateLimit-Limit"] = str(limit)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Reset"] = str(int(time.time()) + retry_after)
                return response

            # Add rate limit headers to successful response
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            return response

        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # On error, allow the request to proceed
            return await call_next(request)