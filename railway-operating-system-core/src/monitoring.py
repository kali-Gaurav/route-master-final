"""Unified Monitoring: Metrics, Logging, Rate Limiting, and Observability.

Consolidates:
- Request/error/latency tracking
- Rate limiting with sliding window
- Prometheus metrics export
- Structured logging
- Health checks and diagnostics

This module provides complete observability and monitoring for
the Railway Operating System API and background services.
"""
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
from functools import wraps
import logging


# ============================================================================
# CONFIGURATION
# ============================================================================

class MonitoringConfig:
    """Monitoring and rate-limiting configuration."""
    
    # Rate Limiting
    RATE_LIMIT_WINDOW = 60  # seconds
    RATE_LIMIT_MAX = int(100)  # requests per window
    
    # Metrics
    LATENCY_SAMPLE_SIZE = 1000
    
    # Logging
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s - %(message)s'


# ============================================================================
# METRICS COLLECTION
# ============================================================================

class MetricsCollector:
    """Centralized metrics collection for monitoring and alerting."""
    
    # Per-key tracking
    _request_timestamps: Dict[str, List[float]] = defaultdict(list)
    _error_counts: Dict[str, int] = defaultdict(int)
    _latencies: Dict[str, List[float]] = defaultdict(list)
    _request_total: int = 0
    _error_total: int = 0
    
    # Success/failure tracking
    _success_counts: Dict[str, int] = defaultdict(int)
    _failure_counts: Dict[str, int] = defaultdict(int)
    
    @classmethod
    def track_request(cls, api_key: str):
        """Record request timestamp for rate-limiting."""
        now = time.time()
        cls._request_timestamps[api_key].append(now)
        cls._request_total += 1
        
        # Cleanup old entries
        cls._request_timestamps[api_key] = [
            t for t in cls._request_timestamps[api_key]
            if now - t < MonitoringConfig.RATE_LIMIT_WINDOW
        ]
    
    @classmethod
    def track_error(cls, api_key: str, error_type: str = 'unknown'):
        """Record an error for this API key."""
        cls._error_counts[api_key] += 1
        cls._error_total += 1
    
    @classmethod
    def track_latency(cls, api_key: str, latency_ms: float):
        """Record response latency in milliseconds."""
        cls._latencies[api_key].append(latency_ms)
        
        # Keep only recent samples
        if len(cls._latencies[api_key]) > MonitoringConfig.LATENCY_SAMPLE_SIZE:
            cls._latencies[api_key] = cls._latencies[api_key][-MonitoringConfig.LATENCY_SAMPLE_SIZE:]
    
    @classmethod
    def track_success(cls, api_key: str):
        """Track successful operation."""
        cls._success_counts[api_key] += 1
    
    @classmethod
    def track_failure(cls, api_key: str):
        """Track failed operation."""
        cls._failure_counts[api_key] += 1
    
    @classmethod
    def is_rate_limited(cls, api_key: str) -> Tuple[bool, int, int]:
        """Check if API key has exceeded rate limit.
        
        Returns:
            (is_limited, current_count, limit)
        """
        requests_in_window = len(cls._request_timestamps[api_key])
        is_limited = requests_in_window >= MonitoringConfig.RATE_LIMIT_MAX
        return is_limited, requests_in_window, MonitoringConfig.RATE_LIMIT_MAX
    
    @classmethod
    def get_key_metrics(cls, api_key: str) -> Dict[str, Any]:
        """Get all metrics for a specific API key."""
        latencies = cls._latencies.get(api_key, [])
        
        return {
            'api_key': api_key[:8] + '...',
            'requests_total': len(cls._request_timestamps.get(api_key, [])),
            'requests_per_minute': len(cls._request_timestamps.get(api_key, [])),
            'errors_total': cls._error_counts.get(api_key, 0),
            'success_count': cls._success_counts.get(api_key, 0),
            'failure_count': cls._failure_counts.get(api_key, 0),
            'latency_avg': sum(latencies) / len(latencies) if latencies else 0,
            'latency_p95': cls._percentile(latencies, 0.95) if latencies else 0,
            'latency_p99': cls._percentile(latencies, 0.99) if latencies else 0,
            'latency_max': max(latencies) if latencies else 0,
            'rate_limited': cls.is_rate_limited(api_key)[0]
        }
    
    @classmethod
    def get_all_metrics(cls) -> Dict[str, Any]:
        """Get all system metrics."""
        all_keys = set(
            list(cls._request_timestamps.keys()) +
            list(cls._error_counts.keys()) +
            list(cls._latencies.keys())
        )
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_requests': cls._request_total,
            'total_errors': cls._error_total,
            'success_rate': (cls._request_total - cls._error_total) / cls._request_total
                          if cls._request_total > 0 else 1.0,
            'active_keys': len(all_keys),
            'per_key': {key: cls.get_key_metrics(key) for key in all_keys}
        }
    
    @classmethod
    def get_prometheus_metrics(cls) -> str:
        """Export metrics in Prometheus text format."""
        lines = []
        
        # Request counts
        lines.append("# HELP ros_requests_total Total API requests")
        lines.append("# TYPE ros_requests_total counter")
        lines.append(f"ros_requests_total {cls._request_total}")
        
        lines.append("")
        lines.append("# HELP ros_errors_total Total API errors")
        lines.append("# TYPE ros_errors_total counter")
        lines.append(f"ros_errors_total {cls._error_total}")
        
        lines.append("")
        lines.append("# HELP ros_latency_ms Response latency distribution")
        lines.append("# TYPE ros_latency_ms histogram")
        for key in cls._latencies:
            latencies = cls._latencies[key]
            if latencies:
                avg = sum(latencies) / len(latencies)
                p95 = cls._percentile(latencies, 0.95)
                p99 = cls._percentile(latencies, 0.99)
                
                lines.append(f'ros_latency_ms{{api_key="{key}",quantile="avg"}} {avg:.2f}')
                lines.append(f'ros_latency_ms{{api_key="{key}",quantile="p95"}} {p95:.2f}')
                lines.append(f'ros_latency_ms{{api_key="{key}",quantile="p99"}} {p99:.2f}')
        
        lines.append("")
        lines.append("# HELP ros_rate_limit_violations_total Rate limit violations")
        lines.append("# TYPE ros_rate_limit_violations_total counter")
        limited_count = sum(
            1 for key in cls._request_timestamps
            if cls.is_rate_limited(key)[0]
        )
        lines.append(f"ros_rate_limit_violations_total {limited_count}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _percentile(data: List[float], p: float) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0
        sorted_data = sorted(data)
        idx = int(len(sorted_data) * p)
        return sorted_data[min(idx, len(sorted_data) - 1)]
    
    @classmethod
    def reset(cls):
        """Reset all metrics (useful for testing)."""
        cls._request_timestamps.clear()
        cls._error_counts.clear()
        cls._latencies.clear()
        cls._request_total = 0
        cls._error_total = 0
        cls._success_counts.clear()
        cls._failure_counts.clear()


# ============================================================================
# RATE LIMITING DECORATOR
# ============================================================================

def rate_limit_check(func):
    """Decorator to enforce rate limiting on functions."""
    @wraps(func)
    def wrapper(api_key: str, *args, **kwargs):
        is_limited, current, limit = MetricsCollector.is_rate_limited(api_key)
        
        if is_limited:
            error_msg = f"Rate limit exceeded: {current}/{limit} requests/min"
            MetricsCollector.track_error(api_key, 'rate_limit')
            raise RuntimeError(error_msg)
        
        MetricsCollector.track_request(api_key)
        
        try:
            start_time = time.time()
            result = func(api_key, *args, **kwargs)
            elapsed_ms = (time.time() - start_time) * 1000
            
            MetricsCollector.track_latency(api_key, elapsed_ms)
            MetricsCollector.track_success(api_key)
            return result
        except Exception as e:
            MetricsCollector.track_error(api_key)
            MetricsCollector.track_failure(api_key)
            raise
    
    return wrapper


# ============================================================================
# LOGGING SYSTEM
# ============================================================================

class StructuredLogger:
    """Structured logging with JSON support."""
    
    def __init__(self, name: str):
        """Initialize logger."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(MonitoringConfig.LOG_LEVEL)
        
        # Console handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter(MonitoringConfig.LOG_FORMAT)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_request(self, api_key: str, endpoint: str, method: str, **kwargs):
        """Log API request."""
        self.logger.info(
            f"API Request | Key: {api_key[:8]}... | {method} {endpoint} | {json.dumps(kwargs)}"
        )
    
    def log_error(self, api_key: str, error: str, **kwargs):
        """Log error."""
        self.logger.error(
            f"Error | Key: {api_key[:8]}... | {error} | {json.dumps(kwargs)}"
        )
    
    def log_operation(self, operation: str, status: str, **kwargs):
        """Log operation."""
        self.logger.info(
            f"{operation} | Status: {status} | {json.dumps(kwargs)}"
        )


# ============================================================================
# HEALTH CHECKS
# ============================================================================

class HealthCheck:
    """System health checking."""
    
    @staticmethod
    def check_database() -> Dict[str, bool]:
        """Check database connectivity."""
        from database import DatabaseConnection
        try:
            with DatabaseConnection() as db:
                if db.connect():
                    db.execute_single("SELECT 1")
                    return {'database': True, 'type': 'postgres' if db.is_postgres else 'sqlite'}
        except Exception as e:
            return {'database': False, 'error': str(e)}
        return {'database': False}
    
    @staticmethod
    def check_cache() -> Dict[str, bool]:
        """Check cache (Redis) connectivity."""
        from infrastructure import CacheManager
        try:
            client = CacheManager._init_redis()
            if client:
                client.ping()
                return {'cache': True, 'type': 'redis'}
            else:
                return {'cache': True, 'type': 'in-memory'}
        except Exception as e:
            return {'cache': False, 'error': str(e)}
    
    @staticmethod
    def get_system_health() -> Dict[str, Any]:
        """Get overall system health."""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'database': HealthCheck.check_database(),
            'cache': HealthCheck.check_cache(),
            'metrics': {
                'total_requests': MetricsCollector._request_total,
                'total_errors': MetricsCollector._error_total,
                'active_api_keys': len(MetricsCollector._request_timestamps)
            }
        }


# ============================================================================
# CONVENIENCE EXPORTS
# ============================================================================

# Create global logger instance
logger = StructuredLogger(__name__)

# Shorthand functions
def track_request(api_key: str):
    """Track a request."""
    return MetricsCollector.track_request(api_key)

def track_error(api_key: str):
    """Track an error."""
    return MetricsCollector.track_error(api_key)

def is_rate_limited(api_key: str) -> bool:
    """Check if rate limited."""
    return MetricsCollector.is_rate_limited(api_key)[0]

def get_metrics() -> str:
    """Get Prometheus metrics."""
    return MetricsCollector.get_prometheus_metrics()

def get_health() -> Dict[str, Any]:
    """Get system health."""
    return HealthCheck.get_system_health()
