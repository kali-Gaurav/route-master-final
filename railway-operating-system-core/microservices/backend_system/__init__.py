"""
Backend Platform
Production-grade backend system with API versioning, RBAC, circuit breakers, and observability
"""

from .api_versioning import (
    APIVersioningPolicy,
    APIGateway,
    RateLimiter,
    ErrorResponseStandardization,
    VersionedAPIRouter,
    APIVersion
)

from .resilience import (
    CircuitBreaker,
    CircuitBreakerOpen,
    CircuitBreakerDecorator,
    BulkheadPattern,
    RetryPolicy,
    CircuitState
)

from .rbac import (
    Role,
    TokenPayload,
    AuthorizationManager,
    RBACDependencies,
    AuditLogger,
    ServiceAccountAuthenticator
)

from .observability import (
    PrometheusMetrics,
    OpenTelemetryTracer,
    StructuredLogger,
    ObservabilityMiddleware,
    ServiceLevelObjective,
    MetricsExporter
)

__all__ = [
    # API Versioning
    'APIVersioningPolicy',
    'APIGateway',
    'RateLimiter',
    'ErrorResponseStandardization',
    'VersionedAPIRouter',
    'APIVersion',
    
    # Resilience
    'CircuitBreaker',
    'CircuitBreakerOpen',
    'CircuitBreakerDecorator',
    'BulkheadPattern',
    'RetryPolicy',
    'CircuitState',
    
    # RBAC
    'Role',
    'TokenPayload',
    'AuthorizationManager',
    'RBACDependencies',
    'AuditLogger',
    'ServiceAccountAuthenticator',
    
    # Observability
    'PrometheusMetrics',
    'OpenTelemetryTracer',
    'StructuredLogger',
    'ObservabilityMiddleware',
    'ServiceLevelObjective',
    'MetricsExporter'
]

__version__ = '1.0.0'
