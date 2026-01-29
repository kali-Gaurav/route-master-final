"""
Observability Stack
Prometheus metrics, OpenTelemetry tracing, structured logging
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import logging
import json
import time
from datetime import datetime
from typing import Optional
from fastapi import Request
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class PrometheusMetrics:
    """Prometheus metrics for API endpoints and services"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        
        # Request metrics
        self.request_duration = Histogram(
            'request_duration_seconds',
            'HTTP request latency',
            labelnames=['method', 'endpoint', 'status'],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            registry=self.registry
        )
        
        self.request_errors = Counter(
            'request_errors_total',
            'Total HTTP request errors',
            labelnames=['method', 'endpoint', 'error_type'],
            registry=self.registry
        )
        
        self.active_requests = Gauge(
            'active_requests',
            'Currently active requests',
            labelnames=['method', 'endpoint'],
            registry=self.registry
        )
        
        # Database metrics
        self.db_query_duration = Histogram(
            'database_query_duration_seconds',
            'Database query latency',
            labelnames=['operation', 'table'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            registry=self.registry
        )
        
        self.db_connection_pool = Gauge(
            'database_connection_pool_size',
            'Current database connection pool size',
            labelnames=['pool'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            'cache_hits_total',
            'Total cache hits',
            labelnames=['cache_name'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'cache_misses_total',
            'Total cache misses',
            labelnames=['cache_name'],
            registry=self.registry
        )
        
        # Circuit breaker metrics
        self.circuit_breaker_state = Gauge(
            'circuit_breaker_state',
            'Circuit breaker state (0=closed, 1=open, 2=half_open)',
            labelnames=['service'],
            registry=self.registry
        )
    
    def get_metrics(self) -> bytes:
        """Get metrics in Prometheus format"""
        return generate_latest(self.registry)


class OpenTelemetryTracer:
    """Distributed tracing with OpenTelemetry"""
    
    def __init__(self, service_name: str, jaeger_host: str = 'localhost', jaeger_port: int = 6831):
        """
        Initialize tracer
        
        Args:
            service_name: Name of this service
            jaeger_host: Jaeger collector host
            jaeger_port: Jaeger collector port
        """
        self.service_name = service_name
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        
        # In production: initialize real tracer
        # from opentelemetry.exporter.jaeger.thrift import JaegerExporter
        # from opentelemetry.sdk.trace import TracerProvider
        # from opentelemetry.sdk.trace.export import BatchSpanProcessor
        
        # For now: simple in-memory tracing
        self.traces = []
    
    @contextmanager
    def span(self, operation_name: str, attributes: dict = None):
        """
        Create a span for distributed tracing
        
        Usage:
            with tracer.span('database_query', {'table': 'metrics'}):
                result = db.query()
        """
        span_data = {
            'operation': operation_name,
            'start_time': time.time(),
            'attributes': attributes or {},
            'status': 'ok'
        }
        
        try:
            yield span_data
        except Exception as e:
            span_data['status'] = 'error'
            span_data['error'] = str(e)
            raise
        finally:
            span_data['duration_ms'] = (time.time() - span_data['start_time']) * 1000
            self.traces.append(span_data)
            
            if len(self.traces) > 10000:  # Prevent memory issues
                self.traces = self.traces[-5000:]


class StructuredLogger:
    """JSON structured logging for easy parsing"""
    
    class JSONFormatter(logging.Formatter):
        """Format logs as JSON"""
        
        def format(self, record):
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            
            # Add extra fields
            if hasattr(record, 'tenant_id'):
                log_entry['tenant_id'] = record.tenant_id
            if hasattr(record, 'user_id'):
                log_entry['user_id'] = record.user_id
            if hasattr(record, 'trace_id'):
                log_entry['trace_id'] = record.trace_id
            if hasattr(record, 'request_id'):
                log_entry['request_id'] = record.request_id
            
            # Add exception info
            if record.exc_info:
                log_entry['exception'] = self.formatException(record.exc_info)
            
            return json.dumps(log_entry)
    
    @staticmethod
    def configure(logger_name: str = 'analytics', level: int = logging.INFO):
        """Configure structured logging"""
        logger_obj = logging.getLogger(logger_name)
        logger_obj.setLevel(level)
        
        handler = logging.StreamHandler()
        formatter = StructuredLogger.JSONFormatter()
        handler.setFormatter(formatter)
        
        logger_obj.addHandler(handler)
        
        return logger_obj


class ObservabilityMiddleware:
    """FastAPI middleware for observability"""
    
    def __init__(self, app, metrics: PrometheusMetrics, tracer: OpenTelemetryTracer):
        self.app = app
        self.metrics = metrics
        self.tracer = tracer
    
    async def __call__(self, request: Request, call_next):
        """Process request with observability"""
        
        # Start timing
        start_time = time.time()
        method = request.method
        endpoint = request.url.path
        
        # Increment active requests
        self.metrics.active_requests.labels(method=method, endpoint=endpoint).inc()
        
        # Start trace
        with self.tracer.span('http_request', {
            'method': method,
            'path': endpoint,
            'remote_addr': request.client.host if request.client else 'unknown'
        }):
            try:
                response = await call_next(request)
                status = response.status_code
                
                # Record metrics
                duration = time.time() - start_time
                self.metrics.request_duration.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).observe(duration)
                
                return response
            
            except Exception as e:
                self.metrics.request_errors.labels(
                    method=method,
                    endpoint=endpoint,
                    error_type=type(e).__name__
                ).inc()
                raise
            
            finally:
                # Decrement active requests
                self.metrics.active_requests.labels(method=method, endpoint=endpoint).dec()


class ServiceLevelObjective:
    """SLO definitions for services"""
    
    SLOs = {
        'analytics-service': {
            'availability': 0.999,      # 99.9% uptime
            'latency_p99': 1.0,         # p99 latency < 1 second
            'error_rate': 0.001,        # < 0.1% errors
        },
        'route-service': {
            'availability': 0.9995,     # 99.95% uptime
            'latency_p99': 0.5,         # p99 latency < 500ms
            'error_rate': 0.0005,       # < 0.05% errors
        },
        'auth-service': {
            'availability': 0.99999,    # 99.999% uptime
            'latency_p99': 0.2,         # p99 latency < 200ms
            'error_rate': 0.00001,      # < 0.001% errors
        }
    }
    
    @classmethod
    def get_slo(cls, service_name: str) -> dict:
        """Get SLO for service"""
        return cls.SLOs.get(service_name, {})


class MetricsExporter:
    """Export metrics to external systems"""
    
    @staticmethod
    def export_to_prometheus(metrics: PrometheusMetrics) -> bytes:
        """Export metrics in Prometheus format"""
        return metrics.get_metrics()
    
    @staticmethod
    def export_to_cloudwatch(metrics_data: dict, namespace: str = 'Analytics'):
        """Export metrics to AWS CloudWatch"""
        # Implementation for CloudWatch export
        logger.info(f"Exporting metrics to CloudWatch/{namespace}")
    
    @staticmethod
    def export_to_datadog(metrics_data: dict, api_key: str):
        """Export metrics to Datadog"""
        # Implementation for Datadog export
        logger.info("Exporting metrics to Datadog")
