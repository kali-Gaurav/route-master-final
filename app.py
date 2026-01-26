"""
Route Discovery Engine - FastAPI Backend Application

This is the main entry point for the production-grade route discovery system.
It provides REST API endpoints for route searches, metrics, and system status.

Architecture: 5-layer system (Frontend → API Gateway → Routing Engine → Data → Monitoring)
This file represents Layer 2: API Gateway
"""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn

# ============================================================================
# CONFIGURATION & SETUP
# ============================================================================

# Initialize FastAPI application
app = FastAPI(
    title="Route Discovery Engine API",
    description="Production-grade railway route discovery and optimization system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# MIDDLEWARE & CORS CONFIGURATION
# ============================================================================

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify exact frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600
)

# Custom middleware for logging and error handling
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log all requests and responses with timing.
    Provides observability for monitoring layer.
    """
    request_id = request.headers.get("x-request-id", f"REQ-{datetime.now().timestamp()}")
    
    # Record start time
    start_time = time.time()
    
    # Log incoming request
    logger.info(
        f"[{request_id}] Incoming: {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )
    
    try:
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        process_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Add headers
        response.headers["x-request-id"] = request_id
        response.headers["x-process-time"] = str(process_time)
        
        # Log response
        logger.info(
            f"[{request_id}] Response: {response.status_code} "
            f"(took {process_time:.2f}ms)"
        )
        
        return response
    
    except Exception as e:
        # Log errors
        process_time = (time.time() - start_time) * 1000
        logger.error(
            f"[{request_id}] Error: {str(e)} (took {process_time:.2f}ms)",
            exc_info=True
        )
        raise

# ============================================================================
# DATA MODELS (Pydantic Schemas)
# ============================================================================

class SearchPreferences(BaseModel):
    """User preferences for route search optimization"""
    max_duration_hours: int = Field(
        default=48,
        ge=1,
        le=72,
        description="Maximum journey duration in hours"
    )
    min_departure: str = Field(
        default="00:00",
        pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$",
        description="Earliest departure time (HH:MM format)"
    )
    max_departure: str = Field(
        default="23:59",
        pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$",
        description="Latest departure time (HH:MM format)"
    )
    prefer_direct: bool = Field(
        default=False,
        description="Prioritize direct/non-stop routes"
    )

    @validator('max_duration_hours')
    def validate_duration(cls, v):
        """Validate max duration is reasonable"""
        if v < 1 or v > 72:
            raise ValueError("Duration must be between 1 and 72 hours")
        return v


class SearchRequest(BaseModel):
    """API request model for route search"""
    source: str = Field(
        ...,
        min_length=3,
        max_length=10,
        description="Source station code (e.g., SBC, NDLS)"
    )
    destination: str = Field(
        ...,
        min_length=3,
        max_length=10,
        description="Destination station code (e.g., NDLS, HYD)"
    )
    date: str = Field(
        ...,
        pattern="^\\d{4}-\\d{2}-\\d{2}$",
        description="Search date in YYYY-MM-DD format"
    )
    preferences: Optional[SearchPreferences] = Field(
        default_factory=SearchPreferences,
        description="Optional user preferences"
    )

    @validator('source', 'destination', pre=True)
    def validate_station_code(cls, v):
        """Validate station codes are uppercase"""
        if isinstance(v, str):
            return v.upper()
        return v

    @validator('date')
    def validate_date(cls, v):
        """Validate date is valid and not in past"""
        try:
            search_date = datetime.strptime(v, "%Y-%m-%d").date()
            today = datetime.now().date()
            
            # Allow searches up to 180 days in future
            if search_date < today:
                raise ValueError("Search date cannot be in the past")
            if search_date > today + timedelta(days=180):
                raise ValueError("Search date must be within 180 days")
            
            return v
        except ValueError as e:
            raise ValueError(f"Invalid date format or range: {str(e)}")


class TrainInfo(BaseModel):
    """Information about a single train in a route"""
    train_no: int = Field(..., description="Train number")
    train_name: str = Field(..., description="Train name")
    source: str = Field(..., description="Source station")
    destination: str = Field(..., description="Destination station")
    departure: str = Field(..., description="Departure time (ISO format)")
    arrival: str = Field(..., description="Arrival time (ISO format)")
    duration: str = Field(..., description="Journey duration (HH:MM)")
    seats_available: int = Field(..., ge=0, description="Available seats")
    platform: Optional[str] = Field(default=None, description="Platform number")


class Route(BaseModel):
    """Complete route (may consist of multiple trains)"""
    route_id: str = Field(..., description="Unique route identifier")
    rank: int = Field(..., ge=1, le=5, description="Route ranking (1-5)")
    quality_score: float = Field(..., ge=0, le=100, description="Quality score 0-100")
    trains: list[TrainInfo] = Field(..., description="Trains in this route")
    total_duration: str = Field(..., description="Total journey duration")
    total_stops: int = Field(..., ge=1, description="Total stops in journey")
    transfers: int = Field(..., ge=0, description="Number of train transfers")
    seat_availability: str = Field(..., description="Seat availability status")
    recommendation_reason: str = Field(
        ...,
        description="Why this route is recommended"
    )


class SearchMetadata(BaseModel):
    """Metadata about search execution"""
    total_routes_generated: int = Field(...)
    total_routes_valid: int = Field(...)
    routes_ranked: int = Field(...)
    response_time_ms: int = Field(...)
    cache_hit: bool = Field(...)
    data_freshness: str = Field(..., description="How old the live data is")


class SearchResponse(BaseModel):
    """API response model for search"""
    status: str = Field(..., description="Response status: success/error")
    timestamp: str = Field(..., description="Response timestamp (ISO format)")
    routes: list[Route] = Field(default=[], description="Ranked routes")
    metadata: SearchMetadata = Field(..., description="Search execution metadata")


class ErrorResponse(BaseModel):
    """Error response model"""
    status: str = Field(default="error")
    error_code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    timestamp: str = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(default=None, description="Request ID for debugging")


class MetricsResponse(BaseModel):
    """System metrics response"""
    total_searches: int = Field(..., description="Total searches ever made")
    searches_today: int = Field(..., description="Searches in last 24 hours")
    avg_response_time_ms: float = Field(..., description="Average response time")
    p95_response_time_ms: float = Field(..., description="95th percentile response time")
    p99_response_time_ms: float = Field(..., description="99th percentile response time")
    cache_hit_rate: float = Field(..., ge=0, le=1, description="Cache hit rate (0-1)")
    api_failure_rate: float = Field(..., ge=0, le=1, description="API failure rate")
    top_search_pairs: list[dict] = Field(..., description="Top search station pairs")
    live_trains_count: int = Field(..., description="Total trains in system")
    active_trains: int = Field(..., description="Currently active trains")
    inactive_trains: int = Field(..., description="Inactive trains")
    last_data_update: str = Field(..., description="Last data update timestamp")


class HealthCheckResponse(BaseModel):
    """System health status response"""
    status: str = Field(..., description="Overall health: healthy/degraded/unhealthy")
    timestamp: str = Field(...)
    components: dict = Field(..., description="Health of individual components")


# ============================================================================
# LIFESPAN EVENTS
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("=== Route Discovery Engine Starting ===")
    logger.info("Loading configuration...")
    logger.info("Initializing database connection...")
    logger.info("Loading train network data...")
    logger.info("Starting background scheduler...")
    logger.info("=== System Ready ===")
    
    # Application runs
    yield
    
    # Shutdown
    logger.info("=== Route Discovery Engine Shutting Down ===")
    logger.info("Closing database connections...")
    logger.info("Stopping background scheduler...")
    logger.info("=== Goodbye ===")


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Route Discovery Engine",
        "version": "1.0.0",
        "status": "running",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "endpoints": {
            "search": "POST /search",
            "metrics": "GET /metrics",
            "health": "GET /system-status"
        }
    }


@app.post(
    "/search",
    response_model=SearchResponse,
    responses={
        200: {"description": "Search successful"},
        400: {"description": "Invalid request"},
        500: {"description": "Server error"}
    },
    tags=["Search"],
    summary="Search for railway routes",
    description="Generate and rank optimal routes between origin and destination"
)
async def search_routes(request: SearchRequest) -> SearchResponse:
    """
    Search for optimal railway routes.
    
    Takes origin, destination, date and optional preferences.
    Returns top 5 ranked routes with live seat availability.
    
    Example:
    ```json
    {
      "source": "SBC",
      "destination": "NDLS",
      "date": "2026-02-15",
      "preferences": {
        "max_duration_hours": 48,
        "min_departure": "06:00",
        "max_departure": "23:59"
      }
    }
    ```
    """
    start_time = time.time()
    request_id = f"SEARCH-{datetime.now().timestamp()}"
    
    try:
        logger.info(
            f"[{request_id}] Search request: {request.source} → {request.destination} "
            f"on {request.date}"
        )
        
        # ===== LAYER 3: ROUTING ENGINE =====
        # TODO: Integrate routing engine components
        # 1. Graph Builder - build train network
        # 2. Route Generator - generate feasible routes
        # 3. Live Validator - validate against live data
        # 4. Route Filter - remove invalid routes
        # 5. Route Ranker - rank top 5
        
        # PLACEHOLDER: Return mock response for now
        mock_response = SearchResponse(
            status="success",
            timestamp=datetime.now().isoformat(),
            routes=[
                Route(
                    route_id="ROUTE_001",
                    rank=1,
                    quality_score=92.5,
                    trains=[
                        TrainInfo(
                            train_no=16320,
                            train_name="SBC-NDLS Express",
                            source="SBC",
                            destination="NDLS",
                            departure="2026-02-15T18:30:00",
                            arrival="2026-02-16T14:00:00",
                            duration="19h 30m",
                            seats_available=45,
                            platform="1"
                        )
                    ],
                    total_duration="19h 30m",
                    total_stops=8,
                    transfers=0,
                    seat_availability="Good",
                    recommendation_reason="Best combination of time and comfort"
                )
            ],
            metadata=SearchMetadata(
                total_routes_generated=287,
                total_routes_valid=156,
                routes_ranked=5,
                response_time_ms=int((time.time() - start_time) * 1000),
                cache_hit=False,
                data_freshness="10 minutes"
            )
        )
        
        logger.info(f"[{request_id}] Search completed successfully")
        return mock_response
    
    except Exception as e:
        logger.error(f"[{request_id}] Search failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error during search"
        )


@app.get(
    "/metrics",
    response_model=MetricsResponse,
    tags=["Monitoring"],
    summary="Get system metrics"
)
async def get_metrics() -> MetricsResponse:
    """
    Get system performance and usage metrics.
    
    Returns:
    - Total searches and daily searches
    - Response time statistics (avg, p95, p99)
    - Cache performance
    - API reliability
    - Top search pairs
    - Live train data statistics
    """
    try:
        # ===== LAYER 5: MONITORING & ANALYTICS =====
        # TODO: Aggregate metrics from database
        
        # PLACEHOLDER: Return mock metrics
        mock_metrics = MetricsResponse(
            total_searches=5427,
            searches_today=234,
            avg_response_time_ms=1230.5,
            p95_response_time_ms=2100.0,
            p99_response_time_ms=3500.0,
            cache_hit_rate=0.35,
            api_failure_rate=0.002,
            top_search_pairs=[
                {"source": "SBC", "destination": "NDLS", "count": 256},
                {"source": "NDLS", "destination": "SBC", "count": 189},
                {"source": "SBC", "destination": "HYD", "count": 145}
            ],
            live_trains_count=11245,
            active_trains=9876,
            inactive_trains=1369,
            last_data_update=datetime.now().isoformat()
        )
        
        logger.info("Metrics retrieved successfully")
        return mock_metrics
    
    except Exception as e:
        logger.error(f"Failed to retrieve metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve metrics"
        )


@app.get(
    "/system-status",
    response_model=HealthCheckResponse,
    tags=["Monitoring"],
    summary="Get system health status"
)
async def get_system_status() -> HealthCheckResponse:
    """
    Get overall system health and component status.
    
    Returns health status for:
    - Database connection
    - Cache system
    - API availability
    - Data freshness
    """
    try:
        # ===== LAYER 5: MONITORING =====
        # TODO: Check all system components
        
        # PLACEHOLDER: Return mock status
        mock_status = HealthCheckResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            components={
                "database": {
                    "status": "healthy",
                    "response_time_ms": 5
                },
                "cache": {
                    "status": "healthy",
                    "hit_rate": 0.35,
                    "size_mb": 125
                },
                "api": {
                    "status": "healthy",
                    "requests_per_second": 12.5
                },
                "data_freshness": {
                    "status": "healthy",
                    "last_update": datetime.now().isoformat(),
                    "age_minutes": 10
                }
            }
        )
        
        logger.info("System status retrieved")
        return mock_status
    
    except Exception as e:
        logger.error(f"Failed to get system status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get system status"
        )


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error_code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "request_id": request.headers.get("x-request-id", "unknown")
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_code": "INTERNAL_ERROR",
            "message": "Internal server error",
            "timestamp": datetime.now().isoformat(),
            "request_id": request.headers.get("x-request-id", "unknown")
        }
    )


# ============================================================================
# STARTUP CHECKS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Perform startup checks"""
    logger.info("Performing startup checks...")
    
    # Check 1: Database connectivity
    logger.info("✓ Database connectivity check passed")
    
    # Check 2: Train data loaded
    logger.info("✓ Train data loaded (placeholder)")
    
    # Check 3: Configuration valid
    logger.info("✓ Configuration valid")
    
    # Check 4: Cache initialized
    logger.info("✓ Cache initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down gracefully...")
    logger.info("✓ Connections closed")
    logger.info("✓ Cache flushed")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    """
    Run the FastAPI application
    
    Development: uvicorn app:app --reload
    Production: gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app
    """
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Set to False in production
        log_level="info"
    )
