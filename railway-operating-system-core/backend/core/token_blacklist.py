# core/token_blacklist.py
"""Token blacklist management for logout functionality"""

from datetime import datetime
import hashlib
import logging
import redis
import json
from typing import Optional
from ..config import settings

logger = logging.getLogger(__name__)

class TokenBlacklist:
    """Manage blacklisted tokens using Redis for persistence"""

    _redis_client: Optional[redis.Redis] = None

    @classmethod
    def _get_redis_client(cls) -> redis.Redis:
        """Get Redis client with lazy initialization"""
        if cls._redis_client is None:
            try:
                cls._redis_client = redis.from_url(settings.redis_url)
                # Test connection
                cls._redis_client.ping()
                logger.info("Redis connection established for token blacklist")
            except Exception as e:
                logger.warning(f"Redis connection failed, falling back to in-memory: {e}")
                cls._redis_client = None
        return cls._redis_client

    @staticmethod
    def get_token_hash(token: str) -> str:
        """Get hash of token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()

    @classmethod
    def revoke_token(cls, token: str, ttl_seconds: int = 86400) -> bool:
        """Add token to blacklist with TTL"""
        try:
            token_hash = cls.get_token_hash(token)

            redis_client = cls._get_redis_client()
            if redis_client:
                # Store in Redis with TTL
                blacklist_data = {
                    "revoked_at": datetime.utcnow().isoformat(),
                    "ttl": ttl_seconds
                }
                redis_client.setex(f"blacklist:{token_hash}", ttl_seconds, json.dumps(blacklist_data))
                logger.info(f"Token revoked in Redis: {token_hash[:8]}...")
            else:
                # Fallback to in-memory (for development/testing)
                if not hasattr(cls, '_fallback_blacklist'):
                    cls._fallback_blacklist = {}
                cls._fallback_blacklist[token_hash] = {
                    "revoked_at": datetime.utcnow(),
                    "ttl": ttl_seconds
                }
                logger.warning(f"Token revoked in memory (Redis unavailable): {token_hash[:8]}...")

            return True
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False

    @classmethod
    def is_blacklisted(cls, token: str) -> bool:
        """Check if token is blacklisted"""
        try:
            token_hash = cls.get_token_hash(token)

            redis_client = cls._get_redis_client()
            if redis_client:
                # Check Redis
                key = f"blacklist:{token_hash}"
                data = redis_client.get(key)
                if data:
                    try:
                        entry = json.loads(data)
                        revoked_at = datetime.fromisoformat(entry["revoked_at"])
                        ttl = entry["ttl"]

                        # Check if TTL has expired
                        elapsed = (datetime.utcnow() - revoked_at).total_seconds()
                        if elapsed > ttl:
                            # Remove expired entry
                            redis_client.delete(key)
                            return False
                        return True
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.error(f"Invalid blacklist data for {token_hash}: {e}")
                        redis_client.delete(key)  # Clean up corrupted data
                        return False
                return False
            else:
                # Fallback to in-memory check
                if hasattr(cls, '_fallback_blacklist') and token_hash in cls._fallback_blacklist:
                    entry = cls._fallback_blacklist[token_hash]
                    elapsed = (datetime.utcnow() - entry["revoked_at"]).total_seconds()
                    if elapsed > entry["ttl"]:
                        del cls._fallback_blacklist[token_hash]
                        return False
                    return True
                return False

        except Exception as e:
            logger.error(f"Error checking token blacklist: {e}")
            return False  # Fail safe - allow token if check fails

    @classmethod
    def cleanup_expired_tokens(cls) -> int:
        """Clean up expired tokens (maintenance function)"""
        try:
            redis_client = cls._get_redis_client()
            if redis_client:
                # Redis handles TTL automatically, but we can scan for cleanup
                # This is a maintenance function that can be called periodically
                pattern = "blacklist:*"
                cleaned = 0
                for key in redis_client.scan_iter(pattern):
                    if not redis_client.exists(key):
                        cleaned += 1
                if cleaned > 0:
                    logger.info(f"Cleaned up {cleaned} expired blacklist entries")
                return cleaned
            return 0
        except Exception as e:
            logger.error(f"Error during blacklist cleanup: {e}")
            return 0
            logger.error(f"Error checking blacklist: {e}")
            return False
    
    @staticmethod
    def clear_expired() -> int:
        """Remove expired tokens from blacklist"""
        expired_count = 0
        token_hashes_to_delete = []
        
        for token_hash, entry in TokenBlacklist._blacklist.items():
            elapsed = (datetime.utcnow() - entry["revoked_at"]).total_seconds()
            if elapsed > entry["ttl"]:
                token_hashes_to_delete.append(token_hash)
                expired_count += 1
        
        for token_hash in token_hashes_to_delete:
            del TokenBlacklist._blacklist[token_hash]
        
        if expired_count > 0:
            logger.info(f"Cleared {expired_count} expired tokens")
        
        return expired_count

# For production, use Redis instead:
# class RedisTokenBlacklist:
#     def __init__(self, redis_client):
#         self.redis = redis_client
#     
#     def revoke_token(self, token: str, ttl: int = 86400):
#         token_hash = TokenBlacklist.get_token_hash(token)
#         self.redis.setex(f"blacklist:{token_hash}", ttl, "revoked")
#     
#     def is_blacklisted(self, token: str) -> bool:
#         token_hash = TokenBlacklist.get_token_hash(token)
#         return self.redis.exists(f"blacklist:{token_hash}")
