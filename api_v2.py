"""
FastAPI Application with Singleton Routing Engine

Optimized REST API for railway routing system using:
- Singleton routing engine (initialized once at startup)
- SQLite database with indexed queries
- Connection pooling for concurrent requests
- CORS for frontend integration

Endpoints:
- POST /api/routes - Search for routes
- GET /api/stations - List stations
- GET /api/trains - List trains
- GET /api/health - Health check
- GET /api/stats - System statistics
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import time
from functools import lru_cache
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database_manager import get_db, DatabaseManager

logger = logging.getLogger(__name__)

# =============================================================================
# Global Singleton Instances (Initialized Once at Startup)
# =============================================================================

_db_instance: Optional[DatabaseManager] = None
_routing_engine: Optional['RoutingEngine'] = None


def get_database_singleton() -> DatabaseManager:
    """Get or create singleton database manager."""
    global _db_instance
    if _db_instance is None:
        _db_instance = get_db()
    return _db_instance


class RoutingEngine:
    """
    Singleton routing engine.
    Loaded once at startup and shared across all requests.
    """
    
    def __init__(self, db: DatabaseManager):
        """Initialize routing engine with database.
        
        Args:
            db: DatabaseManager singleton instance
        """
        self.db = db
        self.request_count = 0
        self.total_search_time = 0
        logger.info("✓ RoutingEngine singleton initialized")
    
    def search(self, origin: str, destination: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for routes between two stations.

        Args:
            origin: Origin station code
            destination: Destination station code
            max_results: Maximum routes to return

        Returns:
            List of route dictionaries
        """
        start_time = time.time()
        self.request_count += 1

        logger.info(f"Route search: {origin} -> {destination} (req #{self.request_count})")

        try:
            # Normalize station codes
            origin = origin.upper().strip()
            destination = destination.upper().strip()

            # Validate that origin and destination are different
            if origin == destination:
                logger.warning(f"Origin equals destination: {origin}")
                return []

            # Validate stations exist
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM stations WHERE station_code = ?", (origin,))
            if not cursor.fetchone():
                logger.warning(f"Origin station not found: {origin}")
                conn.close()
                return []

            cursor.execute("SELECT id FROM stations WHERE station_code = ?", (destination,))
            if not cursor.fetchone():
                logger.warning(f"Destination station not found: {destination}")
                conn.close()
                return []

            # Query routes between stations
            cursor.execute("""
                SELECT DISTINCT
                    t.train_no,
                    t.train_name,
                    MIN(CASE WHEN ts1.sequence < ts2.sequence THEN ts1.sequence ELSE ts2.sequence END) as start_seq,
                    MAX(CASE WHEN ts1.sequence < ts2.sequence THEN ts2.sequence ELSE ts1.sequence END) as end_seq
                FROM trains t
                JOIN train_stations ts1 ON t.id = ts1.train_id
                JOIN train_stations ts2 ON t.id = ts2.train_id
                JOIN stations s1 ON ts1.station_id = s1.id
                JOIN stations s2 ON ts2.station_id = s2.id
                WHERE s1.station_code = ?
                  AND s2.station_code = ?
                  AND ts1.sequence < ts2.sequence
                ORDER BY start_seq ASC
                LIMIT ?
            """, (origin, destination, max_results))

            routes = cursor.fetchall()
            conn.close()

            if not routes:
                logger.info(f"No direct routes found: {origin} -> {destination}")
                return []

            # Format results with detailed segment information
            formatted_routes = []
            for train_no, train_name, start_seq, end_seq in routes:
                # Get detailed station information for this train segment
                conn = self.db.get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT s.station_code, s.station_name 
                    FROM train_stations ts
                    JOIN stations s ON ts.station_id = s.id
                    WHERE ts.train_id = (SELECT id FROM trains WHERE train_no = ?)
                    AND ts.sequence BETWEEN ? AND ?
                    ORDER BY ts.sequence ASC
                """, (train_no, start_seq, end_seq))
                
                stations_on_route = cursor.fetchall()
                conn.close()
                
                # Build segment with detailed information
                segment = {
                    "trainNumber": train_no,
                    "trainName": train_name,
                    "from": origin,
                    "to": destination,
                    "departure": "00:00",  # Would need actual timing from RAPPID
                    "arrival": "00:00",    # Would need actual timing from RAPPID
                    "distance": (end_seq - start_seq) * 100,  # Placeholder calculation
                    "duration": (end_seq - start_seq) * 60,   # Minutes placeholder
                    "waitBefore": 0,
                    "seatAvailable": True,
                    "category": "BALANCED"
                }
                
                route = {
                    "segments": [segment],
                    "totalTime": segment['duration'],
                    "totalCost": 500,  # Placeholder
                    "totalTransfers": 0,
                    "totalDistance": segment['distance'],
                    "liveFareTotal": 500,
                    "seatProbability": 75.0,
                    "safetyScore": 95.0,
                    "category": "BALANCED",
                    # Compatibility fields expected by Phase 2 tests
                    "num_trains": 1,
                    "total_duration_minutes": int(segment['duration']),
                    "departure": segment.get('departure', '00:00'),
                    "arrival": segment.get('arrival', '00:00'),
                    "confidence_score": float(segment.get('live_fare', 0)) / 1000.0 if segment.get('live_fare') else 0.0
                }
                
                formatted_routes.append(route)

            # Record statistics
            search_duration = time.time() - start_time
            self.total_search_time += search_duration

            self.db.log_search(
                origin=origin,
                destination=destination,
                travel_date=datetime.utcnow().strftime("%Y-%m-%d"),
                results_count=len(formatted_routes),
                response_time_ms=int(search_duration * 1000),
                cached=False
            )

            logger.info(f"✓ Found {len(formatted_routes)} routes in {search_duration:.3f}s")

            return formatted_routes

        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            return []


def get_routing_engine_singleton() -> RoutingEngine:
    """Get or create singleton routing engine."""
    global _routing_engine
    if _routing_engine is None:
        db = get_database_singleton()
        _routing_engine = RoutingEngine(db)
    return _routing_engine


# =============================================================================
# Pydantic Models (Request/Response Schemas)
# =============================================================================

class SearchRequest(BaseModel):
    """Route search request"""
    origin: str = Field(..., description="Origin station code (e.g., NDLS)")
    destination: str = Field(..., description="Destination station code (e.g., KOTA)")
    travel_date: Optional[str] = Field(None, description="Travel date (YYYY-MM-DD)")
    max_results: int = Field(10, ge=1, le=50, description="Max routes to return")
    category: str = Field("BALANCED", description="Route category filter")


class RouteInfo(BaseModel):
    """Route information"""
    train_no: str
    train_name: str
    from_station: str
    to_station: str
    segments: int = 1
    duration_minutes: int
    confidence: float


class SearchResponse(BaseModel):
    """Route search response"""
    success: bool
    optimal_routes: List[Dict[str, Any]] = []
    all_generated_routes: List[Dict[str, Any]] = []
    total_routes: int = 0
    search_time_ms: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StationInfo(BaseModel):
    """Station information"""
    code: str
    name: str
    city: Optional[str] = None
    state: Optional[str] = None


class TrainInfo(BaseModel):
    """Train information"""
    train_no: str
    train_name: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    database: str
    optimization_engine: str = "healthy"
    database_trains: int = 0
    database_stations: int = 0
    database_routes: int = 0
    routing_engine: str = "healthy"
    uptime_seconds: float = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StatsResponse(BaseModel):
    """System statistics"""
    total_searches: int = 0
    avg_search_time_ms: float = 0
    database_trains: int = 0
    database_stations: int = 0
    database_routes: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Create FastAPI Application
# =============================================================================

def create_app() -> FastAPI:
    """Create and configure FastAPI application with singleton routing."""
    
    app = FastAPI(
        title="FINALTrip Railway API",
        description="API for discovering optimal railway routes using AI",
        version="2.0.0"
    )
    
    # =========================================================================
    # CORS Middleware
    # =========================================================================
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",      # Vite dev server (main)
            "http://localhost:3000",       # Alternative dev server
            "http://localhost:8080",       # Vue dev server
            "http://127.0.0.1:5173",       # Localhost variant
            "http://127.0.0.1:3000",       # Localhost variant
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Get singletons once at startup
    db = get_database_singleton()
    routing_engine = get_routing_engine_singleton()
    
    # =========================================================================
    # Health & Status Endpoints
    # =========================================================================
    
    @app.get("/api/health", response_model=HealthResponse, tags=["Health"])
    async def health_check():
        """Health check endpoint - returns database and engine status."""
        try:
            stats = db.get_stats()
            
            return HealthResponse(
                status="healthy",
                database="healthy",
                optimization_engine="healthy",
                database_trains=stats.get("total_trains", 0),
                database_stations=stats.get("total_stations", 0),
                database_routes=stats.get("total_routes", 0),
                routing_engine="healthy",
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthResponse(
                status="degraded",
                database="unhealthy",
                optimization_engine="healthy",
                routing_engine="healthy",
                timestamp=datetime.utcnow()
            )
    
    @app.get("/api/stats", response_model=StatsResponse, tags=["Statistics"])
    async def get_statistics():
        """Get system statistics."""
        try:
            stats = db.get_stats()
            
            # Get average search time (mock for now)
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM search_logs")
            total_searches = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT AVG(response_time_ms) FROM search_logs WHERE response_time_ms > 0")
            avg_search = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return StatsResponse(
                total_searches=total_searches,
                avg_search_time_ms=float(avg_search),
                database_trains=stats["trains"],
                database_stations=stats["stations"],
                database_routes=stats["routes"],
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Stats request failed: {e}")
            return StatsResponse(timestamp=datetime.utcnow())
    
    # =========================================================================
    # Route Search Endpoint (Main Feature)
    # =========================================================================
    
    @app.post("/api/routes", response_model=SearchResponse, tags=["Search"])
    async def search_routes(request: SearchRequest):
        """
        Search for routes between two stations.

        Uses singleton routing engine for efficient computation.
        Results include optimal routes (top 3) and all found routes.
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

        try:
            # Search for routes
            routes = routing_engine.search(
                request.origin,
                request.destination,
                max_results=request.max_results
            )

            search_duration_ms = int((time.time() - search_start) * 1000)

            logger.info(f"Search completed: {len(routes)} routes in {search_duration_ms}ms")

            # Take top 3 as optimal, rest as all
            optimal = routes[:3]
            all_routes = routes

            return SearchResponse(
                success=True,
                optimal_routes=optimal,
                all_generated_routes=all_routes,
                total_routes=len(routes),
                search_time_ms=search_duration_ms,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Route search failed: {e}", exc_info=True)
            return SearchResponse(
                success=False,
                optimal_routes=[],
                all_generated_routes=[],
                total_routes=0,
                search_time_ms=0,
                timestamp=datetime.utcnow()
            )
    
    # =========================================================================
    # Station Listing Endpoint
    # =========================================================================
    
    @app.get("/api/stations", response_model=List[StationInfo], tags=["Data"])
    async def list_stations(limit: int = Query(100, ge=1, le=500)):
        """
        Get list of all stations in database.
        
        Returns station codes and names for frontend autocomplete.
        """
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT station_code, station_name, city, state
                FROM stations
                LIMIT ?
            """, (limit,))
            
            stations = cursor.fetchall()
            conn.close()
            
            return [
                StationInfo(
                    code=s[0],
                    name=s[1],
                    city=s[2],
                    state=s[3]
                )
                for s in stations
            ]
        except Exception as e:
            logger.error(f"Station list failed: {e}")
            return []
    
    # =========================================================================
    # Train Listing Endpoint
    # =========================================================================
    
    @app.get("/api/trains", response_model=List[TrainInfo], tags=["Data"])
    async def list_trains(limit: int = Query(100, ge=1, le=500)):
        """
        Get list of trains in database.
        
        Returns train numbers and names.
        """
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT train_no, train_name
                FROM trains
                LIMIT ?
            """, (limit,))
            
            trains = cursor.fetchall()
            conn.close()
            
            return [
                TrainInfo(train_no=t[0], train_name=t[1])
                for t in trains
            ]
        except Exception as e:
            logger.error(f"Train list failed: {e}")
            return []
    
    # =========================================================================
    # Startup/Shutdown Events
    # =========================================================================
    
    # @app.on_event("startup")
    # async def startup_event():
    #     """Initialize singletons at startup."""
    #     logger.info("="*60)
    #     logger.info("FastAPI Startup")
    #     logger.info("="*60)
    #
    #     # Initialize database
    #     db = get_database_singleton()
    #     stats = db.get_stats()
    #     logger.info(f"✓ Database: {stats['total_trains']} trains, {stats['total_stations']} stations, {stats['total_routes']} routes")
    #
    #     # Initialize routing engine
    #     routing_engine = get_routing_engine_singleton()
    #     logger.info(f"✓ Routing Engine: Ready")
    #
    #     logger.info("✓ All systems initialized")
    #     logger.info("="*60)
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup at shutdown."""
        logger.info("FastAPI Shutdown")
        # Database connections will be closed automatically
    
    return app


# =============================================================================
# ASGI Application Entry Point
# =============================================================================

app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting FastAPI server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5001,
        log_level="info"
    )
