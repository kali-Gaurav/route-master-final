# main.py
import sys
import os

# Add the project root to the path
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(backend_dir)
sys.path.insert(0, project_dir)

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app, Counter, Histogram
import time
import structlog
import uuid
from sqlalchemy.orm import Session
from backend.core.audit_middleware import AuditMiddleware
from backend.config import Settings
from backend.core.rate_limiting import AdvancedRateLimitMiddleware
from backend.db_connection import get_engine, Base, get_db
from backend.core.csrf import CSRFProtection, CSRFMiddleware
from backend.api.v1 import auth_router, routes_router, jobs_router

# Create database tables (skip in tests)
if os.getenv("TESTING") != "1":
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

# Rate limiting (now handled by AdvancedRateLimitMiddleware)
# from slowapi import Limiter, _rate_limit_exceeded_handler
# from slowapi.util import get_remote_address
# from slowapi.middleware import SlowAPIMiddleware

# Configure structured logging
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

# Load settings
settings = Settings()

# Create FastAPI app
app = FastAPI(
    title="Railway Operating System API",
    description="REST API for Railway Operating System with multi-tenancy support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Advanced Rate Limiting
app.add_middleware(AdvancedRateLimitMiddleware, redis_client=None)  # Will use Redis if available

# CSRF Protection
csrf_protection = CSRFProtection(secret_key=settings.csrf_secret_key)
csrf_middleware = CSRFMiddleware(csrf_protection)
app.add_middleware(csrf_middleware)

# Audit Middleware
audit_middleware = AuditMiddleware()
app.add_middleware(audit_middleware)

# Request/Response logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and responses with correlation ID"""
    start_time = time.time()
    correlation_id = request.headers.get("X-Correlation-ID", f"req-{str(uuid.uuid4())}")
    
    logger = structlog.get_logger()
    
    # Log request
    logger.info(
        "request_start",
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=correlation_id
    )
    
    try:
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Log response
        logger.info(
            "request_complete",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration, 2),
            correlation_id=correlation_id
        )
        
        return response
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(
            "request_error",
            method=request.method,
            path=request.url.path,
            duration_ms=round(duration, 2),
            error=str(e),
            correlation_id=correlation_id
        )
        raise

# Prometheus metrics
# from prometheus_client import CollectorRegistry, Counter, Histogram

# Create a custom registry to avoid conflicts
# registry = CollectorRegistry()

# REQUEST_COUNT = Counter(
#     'http_requests_total',
#     'Total HTTP requests',
#     ['method', 'endpoint', 'http_status'],
#     registry=registry
# )

# REQUEST_LATENCY = Histogram(
#     'http_request_duration_seconds',
#     'HTTP request latency',
#     ['method', 'endpoint'],
#     registry=registry
# )

# @app.middleware("http")
# async def add_prometheus_metrics(request: Request, call_next):
#     start_time = time.time()

#     response = await call_next(request)

#     REQUEST_COUNT.labels(
#         method=request.method,
#         endpoint=request.url.path,
#         http_status=response.status_code
#     ).inc()

#     REQUEST_LATENCY.labels(
#         method=request.method,
#         endpoint=request.url.path
#     ).observe(time.time() - start_time)

#     return response

# Add security headers middleware
import uuid

# Global exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions"""
    correlation_id = request.headers.get("X-Correlation-ID", f"req-{uuid.uuid4()}")
    import traceback
    error_traceback = traceback.format_exc()
    
    logger = structlog.get_logger()
    logger.error(
        "unhandled_exception",
        correlation_id=correlation_id,
        path=request.url.path,
        method=request.method,
        error=str(exc),
        traceback=error_traceback
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "correlation_id": correlation_id,
            "timestamp": time.time()
        }
    )

from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    correlation_id = request.headers.get("X-Correlation-ID", f"req-{uuid.uuid4()}")
    
    logger = structlog.get_logger()
    logger.warning(
        "validation_error",
        correlation_id=correlation_id,
        path=request.url.path,
        errors=[{**err, 'ctx': str(err.get('ctx', ''))} for err in exc.errors()]
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "details": [
                {
                    "field": err.get("loc", ["unknown"])[1] if len(err.get("loc", [])) > 1 else err.get("loc", ["unknown"])[0],
                    "message": err.get("msg", str(err))
                }
                for err in exc.errors()
            ],
            "correlation_id": correlation_id,
            "timestamp": time.time()
        }
    )

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    # Handle correlation ID
    correlation_id = request.headers.get("X-Correlation-ID", f"req-{uuid.uuid4()}")
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-Correlation-ID"] = correlation_id
    return response

# Include API routers
app.include_router(
    auth_router,
    prefix=f"{settings.api_version}/auth",
    tags=["authentication"]
)

app.include_router(
    routes_router,
    prefix=f"{settings.api_version}/routes",
    tags=["routes"]
)

app.include_router(
    jobs_router,
    prefix=f"{settings.api_version}/jobs",
    tags=["jobs"]
)

# Health check endpoint
@app.api_route("/health", methods=["GET", "OPTIONS"])
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check including database connectivity"""
    try:
        # Check database connectivity
        result = db.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "database": "connected",
            "services": {
                "api": "operational",
                "database": "operational"
            }
        }
    except Exception as e:
        logger = structlog.get_logger()
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "database": "disconnected",
                "error": str(e)
            }
        )

# Readiness check endpoint
@app.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness check with database verification"""
    try:
        db.execute("SELECT 1")
        return {"status": "ready", "timestamp": time.time()}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)}
        )

# Metrics endpoint
# from prometheus_client import make_asgi_app
# metrics_app = make_asgi_app(registry=registry)
# app.mount("/metrics", metrics_app)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Railway Operating System API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,  # Disable reload to avoid Prometheus conflicts
        log_level=settings.log_level.lower()
    )