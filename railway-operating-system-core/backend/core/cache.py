# core/cache.py
import redis
import json
from typing import Any, Optional
from ..config import settings

class RedisCache:
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Set value in cache with TTL"""
        try:
            return self.redis_client.setex(key, ttl_seconds, json.dumps(value))
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception:
            return False

# Global cache instance
cache = RedisCache()

def get_cache() -> RedisCache:
    """Dependency to get cache instance"""
    return cache