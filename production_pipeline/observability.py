"""
Observability System - Logging & Metrics

Structured logging and metrics collection for monitoring and debugging.

Features:
- JSON structured logging
- Log rotation and archival
- Metrics collection and storage
- Performance tracking
- Error tracking and alerting
"""

import logging
import logging.handlers
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import traceback

from production_pipeline.config import get_config


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON
        
        Args:
            record: Log record
            
        Returns:
            JSON formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if provided
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
        
        return json.dumps(log_data)


class MetricsCollector:
    """Collects and tracks system metrics"""
    
    def __init__(self):
        """Initialize metrics collector"""
        self.metrics: Dict[str, list] = {}
        self.logger = logging.getLogger(__name__)
    
    def record(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a metric value
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags for categorization
        """
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        entry = {
            "timestamp": datetime.utcnow(),
            "value": value,
            "tags": tags or {}
        }
        
        self.metrics[metric_name].append(entry)
        
        # Keep only last 1000 entries per metric to avoid memory issues
        if len(self.metrics[metric_name]) > 1000:
            self.metrics[metric_name] = self.metrics[metric_name][-1000:]
    
    def get_metric_stats(self, metric_name: str) -> Optional[Dict[str, float]]:
        """Get statistics for a metric
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            Dictionary with min, max, avg, count
        """
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return None
        
        values = [entry["value"] for entry in self.metrics[metric_name]]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "sum": sum(values)
        }
    
    def get_all_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get stats for all metrics
        
        Returns:
            Dictionary with stats for each metric
        """
        return {
            name: self.get_metric_stats(name)
            for name in self.metrics.keys()
            if self.get_metric_stats(name) is not None
        }


def setup_logging():
    """Setup structured logging system
    
    Returns:
        Root logger
    """
    config = get_config()
    
    # Create logs directory
    logs_dir = Path(config.logging.logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    log_file = logs_dir / "application.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=config.logging.max_bytes,
        backupCount=config.logging.backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    json_formatter = JSONFormatter()
    file_handler.setFormatter(json_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler (separate file for errors)
    error_log_file = logs_dir / "errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=config.logging.max_bytes,
        backupCount=config.logging.backup_count
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    root_logger.addHandler(error_handler)
    
    root_logger.info("Logging system initialized")
    
    return root_logger


class PerformanceMonitor:
    """Monitors and logs performance metrics"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        """Initialize performance monitor
        
        Args:
            metrics_collector: MetricsCollector instance
        """
        self.metrics_collector = metrics_collector
        self.logger = logging.getLogger(__name__)
    
    def log_request(self, endpoint: str, method: str, duration_ms: float, status_code: int, success: bool):
        """Log API request metrics
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            duration_ms: Request duration in milliseconds
            status_code: HTTP status code
            success: Whether request succeeded
        """
        self.metrics_collector.record(
            "http_request_duration_ms",
            duration_ms,
            tags={
                "endpoint": endpoint,
                "method": method,
                "status": str(status_code),
                "success": str(success)
            }
        )
        
        self.logger.debug(
            f"Request: {method} {endpoint} - {status_code} - {duration_ms}ms"
        )
    
    def log_database_operation(self, operation: str, duration_ms: float, success: bool, table: Optional[str] = None):
        """Log database operation metrics
        
        Args:
            operation: Operation type (SELECT, INSERT, UPDATE, DELETE)
            duration_ms: Operation duration in milliseconds
            success: Whether operation succeeded
            table: Table name (optional)
        """
        self.metrics_collector.record(
            "db_operation_duration_ms",
            duration_ms,
            tags={
                "operation": operation,
                "table": table or "unknown",
                "success": str(success)
            }
        )
        
        if duration_ms > 1000:  # Log slow queries
            self.logger.warning(
                f"Slow database operation: {operation} on {table} - {duration_ms}ms"
            )
    
    def log_search_latency(self, origin: str, destination: str, num_routes: int, duration_ms: float):
        """Log route search latency
        
        Args:
            origin: Origin station code
            destination: Destination station code
            num_routes: Number of routes found
            duration_ms: Search duration in milliseconds
        """
        self.metrics_collector.record(
            "search_latency_ms",
            duration_ms,
            tags={
                "origin": origin,
                "destination": destination,
                "route_count": str(num_routes)
            }
        )
        
        if duration_ms > 5000:  # Log slow searches
            self.logger.warning(
                f"Slow search: {origin}->{destination} - {duration_ms}ms for {num_routes} routes"
            )
    
    def log_ingestion_metrics(self, source: str, records_processed: int, duration_ms: float, errors: int = 0):
        """Log data ingestion metrics
        
        Args:
            source: Data source
            records_processed: Number of records processed
            duration_ms: Ingestion duration in milliseconds
            errors: Number of errors
        """
        self.metrics_collector.record(
            "ingestion_duration_ms",
            duration_ms,
            tags={
                "source": source,
                "records": str(records_processed),
                "errors": str(errors)
            }
        )
        
        self.logger.info(
            f"Ingestion: {source} - {records_processed} records in {duration_ms}ms ({errors} errors)"
        )
    
    def log_cache_hit(self, cache_key: str, hit: bool):
        """Log cache operation
        
        Args:
            cache_key: Cache key
            hit: Whether it was a cache hit
        """
        self.metrics_collector.record(
            "cache_hit",
            1.0 if hit else 0.0,
            tags={
                "key": cache_key,
                "result": "hit" if hit else "miss"
            }
        )
    
    def get_report(self) -> str:
        """Generate performance report
        
        Returns:
            Formatted performance report
        """
        metrics = self.metrics_collector.get_all_metrics()
        
        report = "=== Performance Report ===\n"
        
        for metric_name, stats in metrics.items():
            if stats:
                report += f"\n{metric_name}:\n"
                report += f"  Count: {stats['count']}\n"
                report += f"  Min: {stats['min']:.2f}\n"
                report += f"  Max: {stats['max']:.2f}\n"
                report += f"  Avg: {stats['avg']:.2f}\n"
        
        return report


class ErrorTracker:
    """Tracks and analyzes errors"""
    
    def __init__(self):
        """Initialize error tracker"""
        self.errors: Dict[str, int] = {}
        self.logger = logging.getLogger(__name__)
    
    def record_error(self, error_type: str, message: str, context: Optional[Dict[str, Any]] = None):
        """Record an error
        
        Args:
            error_type: Type of error
            message: Error message
            context: Optional context information
        """
        if error_type not in self.errors:
            self.errors[error_type] = 0
        
        self.errors[error_type] += 1
        
        self.logger.error(
            f"Error: {error_type} - {message}",
            extra={"extra_data": context or {}}
        )
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get error summary
        
        Returns:
            Dictionary with error counts
        """
        return self.errors.copy()
    
    def get_top_errors(self, limit: int = 10) -> list:
        """Get top errors by frequency
        
        Args:
            limit: Maximum errors to return
            
        Returns:
            List of (error_type, count) tuples
        """
        return sorted(
            self.errors.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]


# Global instances
_metrics_collector = None
_performance_monitor = None
_error_tracker = None


def initialize_observability() -> tuple:
    """Initialize observability system
    
    Returns:
        Tuple of (metrics_collector, performance_monitor, error_tracker)
    """
    global _metrics_collector, _performance_monitor, _error_tracker
    
    setup_logging()
    
    _metrics_collector = MetricsCollector()
    _performance_monitor = PerformanceMonitor(_metrics_collector)
    _error_tracker = ErrorTracker()
    
    return _metrics_collector, _performance_monitor, _error_tracker


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance
    
    Returns:
        PerformanceMonitor instance
    """
    global _performance_monitor
    if _performance_monitor is None:
        initialize_observability()
    return _performance_monitor


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance
    
    Returns:
        MetricsCollector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        initialize_observability()
    return _metrics_collector


def get_error_tracker() -> ErrorTracker:
    """Get global error tracker instance
    
    Returns:
        ErrorTracker instance
    """
    global _error_tracker
    if _error_tracker is None:
        initialize_observability()
    return _error_tracker
