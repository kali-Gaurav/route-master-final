"""
FastAPI Application Layer

REST API for the railway routing system.

Endpoints:
- POST /api/v1/search - Search for routes
- GET /api/v1/routes/{id} - Get route details
- GET /api/v1/health - Health check
- GET /api/v1/metrics - System metrics
- GET /api/v1/stations - List stations
- GET /api/v1/trains - List trains
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

from production_pipeline.config import get_config
try:
    from production_pipeline.database import (
        DatabaseManager, Station, Train, SearchLog, PerformanceLog, ErrorLog
    )
except ImportError:
    DatabaseManager = None
    Station = None
    Train = None
    SearchLog = None
    PerformanceLog = None
    ErrorLog = None
from production_pipeline.routing_engine import RoutingEngine
from production_pipeline.ingestion import CacheManager

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models (Request/Response Schemas)
# ============================================================================

class RouteStopSchema(BaseModel):
    """Route stop information"""
    code: str
    name: str
    arrival: Optional[str] = None
    departure: Optional[str] = None
    halt_minutes: int = 0


class RouteSegmentSchema(BaseModel):
    """Single train segment in a route"""
    train_no: str
    train_name: str
    from_station: str
    to_station: str
    departure: str
    arrival: str
    duration_minutes: int
    stops: List[RouteStopSchema] = []


class RouteSchema(BaseModel):
    """Complete route from origin to destination"""
    segments: List[RouteSegmentSchema]
    num_trains: int
    total_duration_minutes: int
    departure: str
    arrival: str
    confidence_score: float = 1.0


class SearchRequest(BaseModel):
    """Route search request"""
    origin: str = Field(..., description="Origin station code (e.g., NDLS)")
    destination: str = Field(..., description="Destination station code (e.g., KOTA)")
    travel_date: Optional[str] = Field(None, description="Travel date (YYYY-MM-DD)")
    max_results: int = Field(10, ge=1, le=50, description="Max routes to return")


class SearchResponse(BaseModel):
    """Route search response"""
    success: bool
    routes: List[RouteSchema] = []
    total_routes: int
    search_duration_ms: int
    timestamp: datetime


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    database: str
    cache: str
    timestamp: datetime


class MetricsResponse(BaseModel):
    """System metrics response"""
    searches_total: int
    searches_success: int
    searches_failed: int
    avg_search_time_ms: float
    routes_generated_total: int
    errors_total: int
    uptime_seconds: float


class StationSchema(BaseModel):
    """Station information"""
    code: str
    name: str
    city: str
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class TrainSchema(BaseModel):
    """Train information"""
    train_no: str
    train_name: str
    source: str
    destination: str
    days_running: str


# ============================================================================
# FastAPI Application Factory
# ============================================================================

def create_app(db_manager: DatabaseManager, routing_engine: RoutingEngine, cache_manager: CacheManager) -> FastAPI:
    """Create and configure FastAPI application
    
    Args:
        db_manager: Database manager instance
        routing_engine: Routing engine instance
        cache_manager: Cache manager instance
        
    Returns:
        Configured FastAPI application
    """
    config = get_config()
    
    app = FastAPI(
        title="Railway Route Master API",
        description="API for discovering optimal railway routes",
        version="1.0.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request timing
    request_start_time = None
    
    # ========================================================================
    # Health & Metrics Endpoints
    # ========================================================================
    
    @app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
    async def health_check():
        """Check API health status"""
        logger.info("Health check called")
        
        # Check database
        try:
            session = db_manager.get_session()
            session.execute("SELECT 1")
            db_status = "healthy"
            session.close()
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = "unhealthy"
        
        # Check cache
        cache_status = "healthy"  # TODO: Add cache status check
        
        return HealthResponse(
            status="healthy" if db_status == "healthy" else "degraded",
            database=db_status,
            cache=cache_status,
            timestamp=datetime.utcnow()
        )
    
    @app.get("/api/v1/metrics", response_model=MetricsResponse, tags=["Metrics"])
    async def get_metrics():
        """Get system metrics"""
        logger.info("Metrics requested")
        
        session = db_manager.get_session()
        
        try:
            # Count searches
            total_searches = session.query(SearchLog).count()
            successful_searches = session.query(SearchLog).filter_by(success=True).count()
            failed_searches = total_searches - successful_searches
            
            # Average search time
            from sqlalchemy import func
            avg_time = session.query(
                func.avg(SearchLog.search_duration_ms)
            ).filter(SearchLog.search_duration_ms.isnot(None)).scalar() or 0
            
            # Count errors
            total_errors = session.query(ErrorLog).count()
            
            # Routes generated (approximation from searches * avg routes)
            routes_generated = total_searches * 5  # Approximation
            
            return MetricsResponse(
                searches_total=total_searches,
                searches_success=successful_searches,
                searches_failed=failed_searches,
                avg_search_time_ms=float(avg_time),
                routes_generated_total=routes_generated,
                errors_total=total_errors,
                uptime_seconds=3600.0  # TODO: Track actual uptime
            )
        
        finally:
            session.close()
    
    # ========================================================================
    # Search Endpoint (Main Feature)
    # ========================================================================
    
    @app.post("/api/v1/search", response_model=SearchResponse, tags=["Search"])
    async def search_routes(request: SearchRequest, background_tasks: BackgroundTasks):
        """Search for routes between two stations
        
        Args:
            request: Search request with origin and destination
            background_tasks: Background tasks for async operations
            
        Returns:
            SearchResponse with routes and metadata
        """
        import time
        search_start = time.time()
        
        logger.info(f"Route search: {request.origin} -> {request.destination}")
        
        # Validate input
        if not request.origin or not request.destination:
            logger.warning("Missing origin or destination")
            raise HTTPException(status_code=400, detail="Origin and destination required")
        
        if request.origin == request.destination:
            logger.warning(f"Origin equals destination: {request.origin}")
            raise HTTPException(status_code=400, detail="Origin cannot equal destination")
        
        session = db_manager.get_session()
        
        try:
            # Search for routes
            routes = routing_engine.search(
                request.origin,
                request.destination,
                max_results=request.max_results
            )
            
            search_duration_ms = int((time.time() - search_start) * 1000)
            
            # Convert routes to schema
            route_schemas = []
            for route in routes:
                route_dict = route.to_dict()
                route_schemas.append(RouteSchema(**route_dict["summary"]))
            
            # Log search
            search_log = SearchLog(
                origin=request.origin,
                destination=request.destination,
                travel_date=request.travel_date or datetime.utcnow().strftime("%Y-%m-%d"),
                routes_returned=len(route_schemas),
                search_duration_ms=search_duration_ms,
                success=True
            )
            session.add(search_log)
            
            # Log performance metric
            perf_log = PerformanceLog(
                metric_name="search_latency_ms",
                metric_value=search_duration_ms,
                metric_unit="ms",
                component="API",
                operation="search",
                status="success"
            )
            session.add(perf_log)
            
            session.commit()
            
            logger.info(f"Search completed: {len(route_schemas)} routes in {search_duration_ms}ms")
            
            return SearchResponse(
                success=True,
                routes=route_schemas,
                total_routes=len(route_schemas),
                search_duration_ms=search_duration_ms,
                timestamp=datetime.utcnow()
            )
        
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            
            # Log error
            search_log = SearchLog(
                origin=request.origin,
                destination=request.destination,
                travel_date=request.travel_date or datetime.utcnow().strftime("%Y-%m-%d"),
                routes_returned=0,
                search_duration_ms=int((time.time() - search_start) * 1000),
                success=False,
                error_message=str(e)
            )
            session.add(search_log)
            
            error_log = ErrorLog(
                error_type="SearchError",
                error_message=str(e),
                component="API",
                operation="search",
                severity="ERROR"
            )
            session.add(error_log)
            
            session.commit()
            
            raise HTTPException(status_code=500, detail="Search failed")
        
        finally:
            session.close()
    
    # ========================================================================
    # Stations Endpoint
    # ========================================================================
    
    @app.get("/api/v1/stations", response_model=List[StationSchema], tags=["Stations"])
    async def get_stations(
        city: Optional[str] = Query(None, description="Filter by city"),
        limit: int = Query(100, ge=1, le=1000, description="Result limit")
    ):
        """Get list of stations
        
        Args:
            city: Optional city filter
            limit: Result limit
            
        Returns:
            List of stations
        """
        session = db_manager.get_session()
        
        try:
            query = session.query(Station)
            
            if city:
                query = query.filter(Station.city.ilike(f"%{city}%"))
            
            stations = query.limit(limit).all()
            
            return [
                StationSchema(
                    code=s.code,
                    name=s.name,
                    city=s.city,
                    state=s.state,
                    latitude=s.latitude,
                    longitude=s.longitude
                )
                for s in stations
            ]
        
        finally:
            session.close()
    
    # ========================================================================
    # Trains Endpoint
    # ========================================================================
    
    @app.get("/api/v1/trains", response_model=List[TrainSchema], tags=["Trains"])
    async def get_trains(
        limit: int = Query(100, ge=1, le=1000, description="Result limit")
    ):
        """Get list of trains
        
        Args:
            limit: Result limit
            
        Returns:
            List of trains
        """
        session = db_manager.get_session()
        
        try:
            trains = session.query(Train).limit(limit).all()
            
            return [
                TrainSchema(
                    train_no=t.train_no,
                    train_name=t.train_name,
                    source=t.source_station_code,
                    destination=t.destination_station_code,
                    days_running=t.days_running
                )
                for t in trains
            ]
        
        finally:
            session.close()
    
    # ========================================================================
    # Error Handlers
    # ========================================================================
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        """Handle HTTP exceptions"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        """Handle general exceptions"""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return app
