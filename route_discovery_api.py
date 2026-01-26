"""
ROUTE DISCOVERY API - MAIN ENDPOINT

Central API for route discovery.

Core Endpoint:
POST /routes/discover → Find routes from origin to destination

Returns: 
- ACTIVE trains only
- Validated transfers
- Live seat availability  
- Real-time booking feasibility
- Pareto-optimal routes

Author: Route Master
Date: 2026-01-25
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

try:
    from database import DatabaseManager
    from advanced_route_generator import AdvancedRouteGenerator, DiscoveredRoute
    from transfer_validator import TransferValidator
    from live_seat_checker import LiveSeatChecker
    from active_only_router import ActiveOnlyRouter
    from logger import LoggerFactory
except ImportError:
    pass


# Request/Response models
class RouteDiscoveryRequest(BaseModel):
    """Route discovery request"""
    origin: str = Field(..., description="Source station code")
    destination: str = Field(..., description="Destination station code")
    date: str = Field(..., description="Travel date (YYYY-MM-DD)")
    max_transfers: int = Field(2, ge=0, le=3, description="Max transfers allowed")
    seat_class: Optional[str] = Field(None, description="Preferred seat class")
    limit: int = Field(10, ge=1, le=50, description="Max routes to return")


class RouteSegmentResponse(BaseModel):
    """Single segment in a route"""
    train_no: str
    source: str
    destination: str
    departure_time: str
    arrival_time: str
    distance: float
    duration_minutes: float
    seat_class: Optional[str] = None


class RouteDiscoveryResponse(BaseModel):
    """Complete route response"""
    route_id: str
    origin: str
    destination: str
    date: str
    segments: List[RouteSegmentResponse]
    
    # Metrics
    total_duration_hours: float
    total_distance_km: float
    transfers: int
    estimated_fare: float
    
    # Quality metrics
    seat_availability_score: float = Field(description="0-100")
    reliability_score: float = Field(description="0-100")
    
    # Booking info
    is_bookable: bool
    available_seats: int
    confidence_score: float = Field(description="0-100")
    
    # Route quality
    route_rank: int = Field(description="1=best, higher=worse")


class DiscoveryResultResponse(BaseModel):
    """Discovery result with multiple routes"""
    query: Dict[str, Any]
    timestamp: str
    total_routes_found: int
    routes: List[RouteDiscoveryResponse]
    status: str = Field(description="success, partial, error")
    message: Optional[str] = None


# Router
router = APIRouter(prefix="/routes", tags=["routes"])


# Global services
generator = None
transfer_validator = None
seat_checker = None
router_service = None
logger = None


def init_services():
    """Initialize all services"""
    global generator, transfer_validator, seat_checker, router_service, logger
    
    try:
        db = DatabaseManager()
        logger = LoggerFactory.get_logger("route_discovery_api")
    except:
        logger = logging.getLogger("route_discovery_api")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    try:
        generator = AdvancedRouteGenerator(db)
        transfer_validator = TransferValidator(db)
        seat_checker = LiveSeatChecker(db)
        router_service = ActiveOnlyRouter(db)
        logger.info("✓ Route Discovery services initialized")
    except Exception as e:
        logger.error(f"Error initializing services: {e}")


@router.post("/discover", response_model=DiscoveryResultResponse)
async def discover_routes(request: RouteDiscoveryRequest) -> DiscoveryResultResponse:
    """
    Core route discovery endpoint
    
    Find all routes from origin to destination using:
    1. ACTIVE trains only (from IRCTC validation)
    2. Multi-objective optimization (time, cost, transfers, seats)
    3. Transfer feasibility validation
    4. Live seat availability checking
    5. Real-time booking feasibility assessment
    
    Request example:
    {
        "origin": "NDLS",
        "destination": "KOTA",
        "date": "2026-02-20",
        "max_transfers": 2,
        "limit": 10
    }
    
    Response: List of bookable routes sorted by quality
    """
    
    if not generator:
        init_services()
    
    try:
        start_time = datetime.now()
        
        # Validate date format
        try:
            datetime.strptime(request.date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        # Validate stations exist
        db = DatabaseManager()
        origin_station = db.session.query(db.Station).filter(
            db.Station.station_code == request.origin
        ).first()
        dest_station = db.session.query(db.Station).filter(
            db.Station.station_code == request.destination
        ).first()
        
        if not origin_station or not dest_station:
            raise HTTPException(
                status_code=404,
                detail=f"Invalid station: {request.origin} or {request.destination}"
            )
        
        # Log request
        logger.info(
            f"Discovering routes: {request.origin}→{request.destination} "
            f"on {request.date} (max transfers: {request.max_transfers})"
        )
        
        # Find routes using generator
        discovered = generator.find_routes(
            origin=request.origin,
            destination=request.destination,
            date=request.date,
            max_transfers=request.max_transfers,
            limit=request.limit
        )
        
        if not discovered:
            logger.warning(f"No routes found for {request.origin}→{request.destination}")
            return DiscoveryResultResponse(
                query={
                    "origin": request.origin,
                    "destination": request.destination,
                    "date": request.date,
                    "max_transfers": request.max_transfers
                },
                timestamp=datetime.now().isoformat(),
                total_routes_found=0,
                routes=[],
                status="no_routes",
                message="No routes available for this search"
            )
        
        # Build response routes
        response_routes = []
        
        for rank, route in enumerate(discovered, 1):
            # Validate transfers
            transfer_valid = True
            transfer_results = None
            
            if len(route.segments) > 1:
                try:
                    segments = [
                        {
                            'train_no': s.train_no,
                            'destination': s.destination,
                            'arrival_time': s.arrival_time,
                            'source': s.source,
                            'departure_time': s.departure_time
                        }
                        for s in route.segments
                    ]
                    
                    transfer_valid, transfer_results = transfer_validator.validate_transfers_in_route(segments)
                except Exception as e:
                    logger.warning(f"Transfer validation error: {e}")
                    transfer_valid = False
            
            # Check seat availability
            try:
                bookable, seat_info = seat_checker.is_route_bookable(
                    [{'train_no': s.train_no, 'distance': s.distance} 
                     for s in route.segments],
                    request.date
                )
                
                available_seats = seat_info.get('min_available_seats', 0)
                estimated_fare = seat_info.get('estimated_fare', 0)
            except Exception as e:
                logger.warning(f"Seat checking error: {e}")
                bookable = False
                available_seats = 0
                estimated_fare = 0
            
            # Calculate overall confidence score
            confidence = (
                route.reliability_score * 0.4 +  # Train reliability
                route.seat_availability_score * 0.3 +  # Seat availability
                (100 if transfer_valid else 0) * 0.3  # Transfer feasibility
            )
            
            # Build segment responses
            segment_responses = [
                RouteSegmentResponse(
                    train_no=s.train_no,
                    source=s.source,
                    destination=s.destination,
                    departure_time=s.departure_time,
                    arrival_time=s.arrival_time,
                    distance=s.distance,
                    duration_minutes=s.duration_minutes,
                    seat_class=s.classes[0] if s.classes else None
                )
                for s in route.segments
            ]
            
            # Build route response
            route_response = RouteDiscoveryResponse(
                route_id=route.route_id,
                origin=request.origin,
                destination=request.destination,
                date=request.date,
                segments=segment_responses,
                total_duration_hours=route.total_duration_minutes / 60,
                total_distance_km=route.total_distance,
                transfers=route.transfer_count,
                estimated_fare=estimated_fare or route.total_cost_estimate,
                seat_availability_score=route.seat_availability_score,
                reliability_score=route.reliability_score,
                is_bookable=bookable and transfer_valid,
                available_seats=available_seats,
                confidence_score=confidence,
                route_rank=rank
            )
            
            response_routes.append(route_response)
        
        # Calculate elapsed time
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(
            f"✓ Discovered {len(response_routes)} routes in {elapsed_ms:.0f}ms"
        )
        
        return DiscoveryResultResponse(
            query={
                "origin": request.origin,
                "destination": request.destination,
                "date": request.date,
                "max_transfers": request.max_transfers
            },
            timestamp=datetime.now().isoformat(),
            total_routes_found=len(response_routes),
            routes=response_routes,
            status="success"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error discovering routes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=Dict[str, Any])
async def route_discovery_status() -> Dict[str, Any]:
    """Get route discovery service status"""
    
    if not generator:
        init_services()
    
    try:
        return {
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "generator": generator.get_status() if generator else {},
            "seat_cache": seat_checker.get_cache_stats() if seat_checker else {},
            "services_initialized": all([
                generator, transfer_validator, seat_checker, router_service
            ])
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def setup_route_discovery(app):
    """Setup route discovery API in FastAPI app"""
    init_services()
    app.include_router(router)
    return logger


if __name__ == "__main__":
    print("Route Discovery API")
    print("=" * 50)
    print("✓ POST /routes/discover - Main discovery endpoint")
    print("✓ GET /routes/status - Service status")
