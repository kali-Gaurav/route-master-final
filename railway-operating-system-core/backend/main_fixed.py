# main.py - Fixed and Comprehensive Backend Entry Point
import sys
import os
import time
import uuid
import logging
from typing import Dict, Any

# Add the project root to the path
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(backend_dir)
sys.path.insert(0, project_dir)

# Core imports
from fastapi import FastAPI, Request, Depends, HTTPException, status, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge
import time
import structlog
from sqlalchemy.orm import Session
from sqlalchemy import text

# OpenTelemetry imports
try:
    from opentelemetry import trace
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter  # type: ignore
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor  # type: ignore
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False

# Backend imports
from backend.config import settings
from backend.db_connection import get_engine, get_db
from backend.models import Base
from backend.core.audit_middleware import AuditMiddleware
from backend.core.rate_limiting import AdvancedRateLimitMiddleware
from backend.core.csrf import CSRFProtection

# API routers
from backend.api.v1 import auth, routes, jobs

# Configure structured logging
def configure_logging():
    """Configure structured logging with structlog"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

configure_logging()
logger = structlog.get_logger()

# Initialize database tables (skip in tests)
def initialize_database():
    """Create database tables and schema"""
    if os.getenv("TESTING") != "1":
        try:
            engine = get_engine()
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

initialize_database()

# Create FastAPI app
app = FastAPI(
    title="Railway Operating System API",
    description="REST API for Railway Operating System with enterprise-grade security and reliability",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

DB_CONNECTIONS = Gauge(
    'db_connections_active',
    'Number of active database connections'
)

# OpenTelemetry setup
if OPENTELEMETRY_AVAILABLE:
    try:
        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name="localhost",
            agent_port=6831,
        )

        # Set up tracer provider
        trace.set_tracer_provider(TracerProvider())
        tracer = trace.get_tracer_provider().get_tracer(__name__)

        # Add span processor
        span_processor = BatchSpanProcessor(jaeger_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)

        logger.info("OpenTelemetry tracing configured with Jaeger")
    except Exception as e:
        logger.error(f"Failed to configure OpenTelemetry: {e}")
        OPENTELEMETRY_AVAILABLE = False
else:
    logger.warning("OpenTelemetry not available, tracing disabled")

# Add CORS middleware
try:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        max_age=3600,
    )
    logger.info("CORS middleware configured")
except Exception as e:
    logger.error(f"Failed to configure CORS: {e}")

# Add Trusted Host middleware
try:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_hosts
    )
    logger.info("Trusted Host middleware configured")
except Exception as e:
    logger.error(f"Failed to configure Trusted Host: {e}")

# Add Audit Middleware
try:
    from backend.core.audit_middleware import AuditMiddleware
    app.add_middleware(AuditMiddleware)
    logger.info("Audit middleware configured")
except Exception as e:
    logger.error(f"Failed to configure Audit middleware: {e}")

# Add Advanced Rate Limiting
try:
    from backend.core.rate_limiting import AdvancedRateLimitMiddleware
    app.add_middleware(AdvancedRateLimitMiddleware)
    logger.info("Rate limiting middleware configured")
except Exception as e:
    logger.error(f"Failed to configure Rate limiting: {e}")

# Instrument FastAPI and SQLAlchemy for tracing
if OPENTELEMETRY_AVAILABLE:
    try:
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented for tracing")

        # Instrument SQLAlchemy
        SQLAlchemyInstrumentor().instrument()
        logger.info("SQLAlchemy instrumented for tracing")
    except Exception as e:
        logger.error(f"Failed to instrument for tracing: {e}")

# Request/Response logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and responses with correlation ID and metrics"""
    start_time = time.time()
    correlation_id = request.headers.get("X-Correlation-ID", f"req-{str(uuid.uuid4())[:8]}")
    
    # Store correlation_id in request state
    request.state.correlation_id = correlation_id
    
    # Log request
    logger.info(
        "request_start",
        method=request.method,
        path=request.url.path,
        query=str(request.url.query),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=correlation_id,
        user_agent=request.headers.get("user-agent", "unknown")
    )
    
    try:
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Update Prometheus metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=str(response.status_code)
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(time.time() - start_time)
        
        # Log response
        logger.info(
            "request_complete",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration, 2),
            correlation_id=correlation_id
        )
        
        response.headers["X-Correlation-ID"] = correlation_id
        return response
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        
        # Update Prometheus metrics for errors
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code="500"
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(time.time() - start_time)
        
        logger.error(
            "request_error",
            method=request.method,
            path=request.url.path,
            duration_ms=round(duration, 2),
            error=str(e),
            correlation_id=correlation_id,
            exc_info=True
        )
        raise

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response

# Global exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions"""
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    logger.error(
        "unhandled_exception",
        correlation_id=correlation_id,
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "correlation_id": correlation_id,
            "timestamp": time.time()
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed information"""
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    logger.warning(
        "validation_error",
        correlation_id=correlation_id,
        path=request.url.path,
        error_count=len(exc.errors())
    )
    
    details = []
    for error in exc.errors():
        loc = error.get("loc", ())
        field = loc[-1] if loc else "unknown"
        details.append({
            "field": str(field),
            "message": error.get("msg", ""),
            "type": error.get("type", "")
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": details,
            "correlation_id": correlation_id,
            "timestamp": time.time()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "correlation_id": correlation_id,
            "timestamp": time.time()
        }
    )

# API Routers
try:
    app.include_router(
        auth.router,
        prefix=f"{settings.api_version}/auth",
        tags=["authentication"]
    )
    logger.info("Auth router configured")
except Exception as e:
    logger.error(f"Failed to configure Auth router: {e}")

try:
    app.include_router(
        routes.router,
        prefix=f"{settings.api_version}/routes",
        tags=["routes"]
    )
    logger.info("Routes router configured")
except Exception as e:
    logger.error(f"Failed to configure Routes router: {e}")

try:
    app.include_router(
        jobs.router,
        prefix=f"{settings.api_version}/jobs",
        tags=["jobs"]
    )
    logger.info("Jobs router configured")
except Exception as e:
    logger.error(f"Failed to configure Jobs router: {e}")

# Health check endpoint
@app.get("/health", name="Health Check", tags=["monitoring"])
async def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Comprehensive health check including database connectivity
    
    Returns:
        dict: Health status with database and service status
    """
    try:
        # Check database connectivity
        db.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "database": "connected",
            "services": {
                "api": "operational",
                "database": "operational"
            },
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "database": "disconnected",
                "error": str(e)
            }
        )

# Readiness check endpoint
@app.get("/ready", name="Readiness Check", tags=["monitoring"])
async def readiness_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Readiness check with database verification
    
    Returns:
        dict: Readiness status
    """
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "error": str(e),
                "timestamp": time.time()
            }
        )

# Prometheus metrics endpoint
@app.get("/metrics", name="Metrics", tags=["monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# Root endpoint
@app.get("/", name="Root", tags=["info"])
async def root() -> Dict[str, Any]:
    """API root endpoint with documentation links
    
    Returns:
        dict: API information and documentation links
    """
    return {
        "message": "Railway Operating System API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "ready": "/ready"
    }

# Startup event handler
@app.on_event("startup")
async def startup_event():
    """Application startup event handler"""
    logger.info(
        "application_startup",
        version="1.0.0",
        environment=settings.environment,
        debug=settings.debug
    )

# Shutdown event handler
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler"""
    logger.info("application_shutdown")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_fixed:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
