"""Unified Infrastructure: Caching, Async Tasks, and Job Management.

Consolidates:
- Redis caching layer with fallback to in-memory
- Celery async task definitions
- Job queue management and persistence
- Task result tracking and monitoring

This module provides complete infrastructure for async processing,
caching, and background job execution for the Railway Operating System.
"""
import os
import json
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

from database_system import DatabaseConnection


# ============================================================================
# CACHING LAYER (Redis with In-Memory Fallback)
# ============================================================================

class CacheManager:
    """Unified caching with Redis primary and in-memory fallback."""
    
    # Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    DEFAULT_TTL = int(os.getenv('CACHE_TTL_SECONDS', '3600'))
    
    # In-memory cache (fallback)
    _memory_cache: Dict[str, Tuple[Any, float]] = {}
    _redis_client: Optional[Any] = None
    
    @classmethod
    def _init_redis(cls) -> Optional[Any]:
        """Lazily initialize Redis client."""
        if cls._redis_client is not None:
            return cls._redis_client
        
        if not REDIS_AVAILABLE:
            return None
        
        try:
            cls._redis_client = redis.Redis.from_url(cls.REDIS_URL, decode_responses=True)
            cls._redis_client.ping()
            return cls._redis_client
        except Exception as e:
            print(f"⚠️  Redis unavailable: {e} - using in-memory cache")
            return None
    
    @staticmethod
    def _make_key(*args) -> str:
        """Generate cache key from arguments."""
        key_str = ':'.join(str(arg) for arg in args)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    @classmethod
    def get(cls, key: str, namespace: str = 'default') -> Optional[Any]:
        """Get value from cache (Redis first, then memory)."""
        full_key = f"{namespace}:{key}"
        
        # Try Redis
        redis_client = cls._init_redis()
        if redis_client:
            try:
                value = redis_client.get(full_key)
                if value:
                    return json.loads(value)
            except Exception as e:
                print(f"Cache get error: {e}")
        
        # Try memory cache
        if full_key in cls._memory_cache:
            value, expiry = cls._memory_cache[full_key]
            if datetime.utcnow().timestamp() < expiry:
                return value
            else:
                del cls._memory_cache[full_key]
        
        return None
    
    @classmethod
    def set(cls, key: str, value: Any, ttl: Optional[int] = None, namespace: str = 'default') -> bool:
        """Set value in cache (Redis and memory)."""
        ttl = ttl or cls.DEFAULT_TTL
        full_key = f"{namespace}:{key}"
        serialized = json.dumps(value)
        
        # Set in Redis
        redis_client = cls._init_redis()
        if redis_client:
            try:
                redis_client.setex(full_key, ttl, serialized)
            except Exception as e:
                print(f"Cache set error: {e}")
        
        # Also set in memory cache
        expiry = datetime.utcnow().timestamp() + ttl
        cls._memory_cache[full_key] = (value, expiry)
        
        return True
    
    @classmethod
    def delete(cls, key: str, namespace: str = 'default') -> bool:
        """Delete key from cache."""
        full_key = f"{namespace}:{key}"
        
        # Delete from Redis
        redis_client = cls._init_redis()
        if redis_client:
            try:
                redis_client.delete(full_key)
            except Exception as e:
                print(f"Cache delete error: {e}")
        
        # Delete from memory cache
        if full_key in cls._memory_cache:
            del cls._memory_cache[full_key]
        
        return True
    
    @classmethod
    def clear(cls, namespace: str = 'default') -> bool:
        """Clear all keys in namespace."""
        redis_client = cls._init_redis()
        if redis_client:
            try:
                pattern = f"{namespace}:*"
                keys = redis_client.keys(pattern)
                if keys:
                    redis_client.delete(*keys)
            except Exception as e:
                print(f"Cache clear error: {e}")
        
        # Clear memory cache for namespace
        to_delete = [k for k in cls._memory_cache.keys() if k.startswith(f"{namespace}:")]
        for k in to_delete:
            del cls._memory_cache[k]
        
        return True


# ============================================================================
# ROUTE CACHING (Specific Cache Manager)
# ============================================================================

class RouteCache:
    """Specialized cache for route query results."""
    
    NAMESPACE = 'routes'
    TTL = int(os.getenv('ROUTE_CACHE_TTL', '3600'))
    
    @staticmethod
    def get(origin: str, destination: str, date: str) -> Optional[Dict[str, Any]]:
        """Get cached routes."""
        key = CacheManager._make_key(origin.upper(), destination.upper(), date)
        return CacheManager.get(key, namespace=RouteCache.NAMESPACE)
    
    @staticmethod
    def set(origin: str, destination: str, date: str, routes: Dict[str, Any]) -> bool:
        """Cache routes."""
        key = CacheManager._make_key(origin.upper(), destination.upper(), date)
        return CacheManager.set(key, routes, ttl=RouteCache.TTL, namespace=RouteCache.NAMESPACE)
    
    @staticmethod
    def clear():
        """Clear all route cache."""
        return CacheManager.clear(namespace=RouteCache.NAMESPACE)


# ============================================================================
# JOB QUEUE MANAGEMENT
# ============================================================================

class JobManager:
    """Manages background job queue with persistence and monitoring."""
    
    TABLE = 'system_jobs'
    
    @staticmethod
    def ensure_table():
        """Initialize jobs table."""
        with DatabaseConnection() as db:
            if not db.connect():
                return False
            db.execute_query(f"""
            CREATE TABLE IF NOT EXISTS {JobManager.TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE NOT NULL,
                command TEXT NOT NULL,
                payload TEXT,
                status TEXT DEFAULT 'queued',
                result TEXT,
                created_at TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                error_message TEXT
            )
            """)
            try:
                db.conn.commit()
                return True
            except Exception as e:
                import logging
                logging.error(f"Error committing job table: {e}")
                return False
    
    @staticmethod
    def enqueue(command: str, payload: Optional[Dict] = None) -> Optional[str]:
        """Enqueue a job. Returns job_id."""
        JobManager.ensure_table()
        import uuid
        job_id = str(uuid.uuid4())
        payload_json = json.dumps(payload or {})
        created = datetime.utcnow().isoformat()
        
        with DatabaseConnection() as db:
            if not db.connect():
                return None
            try:
                db.execute_query(
                    f"INSERT INTO {JobManager.TABLE} (job_id, command, payload, status, created_at) "
                    f"VALUES (?, ?, ?, ?, ?)",
                    (job_id, command, payload_json, 'queued', created)
                )
                db.conn.commit()
                return job_id
            except Exception as e:
                print(f"Error enqueuing job: {e}")
                return None
    
    @staticmethod
    def get_next() -> Optional[Dict[str, Any]]:
        """Fetch next queued job."""
        JobManager.ensure_table()
        with DatabaseConnection() as db:
            if not db.connect():
                return None
            row = db.execute_single(
                f"SELECT id, job_id, command, payload FROM {JobManager.TABLE} "
                f"WHERE status = 'queued' ORDER BY created_at LIMIT 1"
            )
            if not row:
                return None
            id_, job_id, command, payload = row
            return {
                'id': id_,
                'job_id': job_id,
                'command': command,
                'payload': json.loads(payload or '{}')
            }
    
    @staticmethod
    def get(job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details."""
        JobManager.ensure_table()
        with DatabaseConnection() as db:
            if not db.connect():
                return None
            row = db.execute_single(
                f"SELECT id, job_id, command, status, result, created_at, started_at, finished_at FROM {JobManager.TABLE} "
                f"WHERE job_id = ?",
                (job_id,)
            )
            if not row:
                return None
            id_, jid, cmd, status, result, created, started, finished = row
            return {
                'id': id_,
                'job_id': jid,
                'command': cmd,
                'status': status,
                'result': json.loads(result or '{}'),
                'created_at': created,
                'started_at': started,
                'finished_at': finished
            }
    
    @staticmethod
    def update_status(job_id: str, status: str, result: Optional[Dict] = None, error: Optional[str] = None) -> bool:
        """Update job status and result."""
        JobManager.ensure_table()
        result_json = json.dumps(result or {})
        
        with DatabaseConnection() as db:
            if not db.connect():
                return False
            try:
                now = datetime.utcnow().isoformat()
                if status == 'running' and not error:
                    db.execute_query(
                        f"UPDATE {JobManager.TABLE} SET status = ?, started_at = ? WHERE job_id = ?",
                        (status, now, job_id)
                    )
                elif status in ['completed', 'failed']:
                    db.execute_query(
                        f"UPDATE {JobManager.TABLE} SET status = ?, result = ?, finished_at = ?, error_message = ? WHERE job_id = ?",
                        (status, result_json, now, error, job_id)
                    )
                else:
                    db.execute_query(
                        f"UPDATE {JobManager.TABLE} SET status = ? WHERE job_id = ?",
                        (status, job_id)
                    )
                db.conn.commit()
                return True
            except Exception as e:
                print(f"Error updating job: {e}")
                return False
    
    @staticmethod
    def list_all(status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List jobs with optional status filter."""
        JobManager.ensure_table()
        with DatabaseConnection() as db:
            if not db.connect():
                return []
            if status:
                rows = db.execute_query(
                    f"SELECT id, job_id, command, status, created_at FROM {JobManager.TABLE} "
                    f"WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status, limit)
                )
            else:
                rows = db.execute_query(
                    f"SELECT id, job_id, command, status, created_at FROM {JobManager.TABLE} "
                    f"ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                )
            return [
                {
                    'id': row[0],
                    'job_id': row[1],
                    'command': row[2],
                    'status': row[3],
                    'created_at': row[4]
                }
                for row in (rows or [])
            ]


# ============================================================================
# CELERY ASYNC TASKS (Optional)
# ============================================================================

# Initialize Celery if available
if CELERY_AVAILABLE:
    app = Celery('railway_os')
    app.conf.broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    app.conf.result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
    app.conf.task_serializer = 'json'
    app.conf.accept_content = ['json']
    app.conf.timezone = 'UTC'
    
    @app.task(bind=True, name='generate-routes')
    def generate_routes_async(self, source: str, destination: str, date: str = None):
        """Async route generation task."""
        try:
            from route_finder import RouteFinder
            finder = RouteFinder()
            routes = finder.find_all_routes(source, destination)
            
            # Cache results
            if date:
                RouteCache.set(source, destination, date, routes)
            
            return {'status': 'success', 'routes_found': len(routes)}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    @app.task(name='batch-routes')
    def batch_routes(pairs: List[Tuple[str, str]]):
        """Batch route generation task."""
        results = []
        for source, dest in pairs:
            try:
                result = generate_routes_async.delay(source, dest)
                results.append({'origin': source, 'destination': dest, 'status': 'processing'})
            except Exception as e:
                results.append({'origin': source, 'destination': dest, 'error': str(e)})
        return results

else:
    # Dummy Celery app if not available
    class DummyCeleryApp:
        def task(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    
    app = DummyCeleryApp()
