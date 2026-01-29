# integration_api.py - External Integration API Endpoints
"""
REST API endpoints for external system integration.
Provides standardized interfaces for backend and microservices.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from dataclasses import asdict

from autonomous_system import autonomous_system
from database_core import db_core
from connection import db_manager
from models.route import Route
from models.station import Station
from models.train import Train
from models.system import AuditLog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Railway Database Integration API",
    description="Autonomous Railway Operating System Database API",
    version="1.0.0"
)

# Pydantic models for request/response
class RouteSearchRequest(BaseModel):
    origin: str = Field(..., description="Origin station code")
    destination: str = Field(..., description="Destination station code")
    date: Optional[str] = Field(None, description="Travel date (YYYY-MM-DD)")
    max_transfers: int = Field(3, ge=0, le=3, description="Maximum transfers allowed")
    optimize_for: str = Field("duration", description="Optimization criteria")

class ServiceRegistrationRequest(BaseModel):
    service_type: str = Field(..., description="Type of service (backend, microservice)")
    service_name: str = Field(..., description="Service name")
    host: str = Field(..., description="Service host")
    port: int = Field(..., description="Service port")
    endpoints: List[str] = Field(default_factory=list, description="Service endpoints")
    health_check_url: str = Field(..., description="Health check URL")

class RouteResponse(BaseModel):
    segments: List[Dict[str, Any]]
    total_distance: float
    total_duration: int
    total_transfers: int
    total_fare: float
    path: List[str]

class StationInfo(BaseModel):
    id: str
    code: str
    name: str
    latitude: float
    longitude: float
    state: Optional[str]
    zone: Optional[str]
    is_junction: bool
    facilities: Dict[str, bool]

class SystemHealth(BaseModel):
    database_status: str
    graph_status: str
    services_registered: int
    active_connections: int
    memory_usage: float
    cpu_usage: float
    last_route_generated: Optional[datetime]
    total_routes_cached: int
    uptime_seconds: int

# Dependency to ensure system is initialized
async def get_system_dependency():
    """Ensure autonomous system is initialized."""
    if not autonomous_system.running:
        raise HTTPException(status_code=503, detail="System not initialized")
    return autonomous_system

# Routes API
@app.post("/api/v1/routes/search", response_model=List[RouteResponse])
async def search_routes(
    request: RouteSearchRequest,
    system: Any = Depends(get_system_dependency)
):
    """Search for optimal routes between stations."""
    try:
        routes = await db_core.find_optimal_routes(
            request.origin,
            request.destination,
            max_transfers=request.max_transfers,
            optimize_for=request.optimize_for
        )
        return [RouteResponse(**asdict(route)) for route in routes]
    except Exception as e:
        logger.error(f"Route search error: {e}")
        raise HTTPException(status_code=500, detail="Route search failed")

@app.get("/api/v1/routes/{route_id}")
async def get_route_details(
    route_id: str,
    system: Any = Depends(get_system_dependency)
):
    """Get detailed information about a specific route."""
    try:
        with db_manager.session_scope() as session:
            route = session.query(Route).filter(Route.id == route_id).first()
            if not route:
                raise HTTPException(status_code=404, detail="Route not found")

            return {
                "id": str(route.id),
                "train_id": str(route.train_id),
                "origin_station_id": str(route.origin_station_id),
                "dest_station_id": str(route.dest_station_id),
                "distance_km": route.distance_km,
                "duration_minutes": route.duration_minutes,
                "is_active": route.is_active,
                "route_type": route.route_type
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Route details error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get route details")

# Stations API
@app.get("/api/v1/stations/{code}", response_model=StationInfo)
async def get_station_info(
    code: str,
    system: Any = Depends(get_system_dependency)
):
    """Get information about a specific station."""
    try:
        station_id = await db_core._get_station_id_by_code(code)
        if not station_id:
            raise HTTPException(status_code=404, detail="Station not found")

        with db_manager.session_scope() as session:
            station = session.query(Station).filter(Station.id == station_id).first()
            if not station:
                raise HTTPException(status_code=404, detail="Station not found")

            return StationInfo(
                id=str(station.id),
                code=station.code,
                name=station.name,
                latitude=station.latitude,
                longitude=station.longitude,
                state=station.state,
                zone=station.zone,
                is_junction=station.is_junction,
                facilities={
                    "wifi": station.has_wifi,
                    "parking": station.has_parking,
                    "food_court": station.has_food_court,
                    "atm": station.has_atm,
                    "medical": station.has_medical_facility
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Station info error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get station info")

@app.get("/api/v1/stations")
async def list_stations(
    limit: int = 100,
    offset: int = 0,
    system: Any = Depends(get_system_dependency)
):
    """List all active stations."""
    try:
        with db_manager.session_scope() as session:
            stations = session.query(Station).filter(
                Station.is_active == True,
                Station.is_deleted == False
            ).limit(limit).offset(offset).all()

            return [
                {
                    "id": str(s.id),
                    "code": s.code,
                    "name": s.name,
                    "latitude": s.latitude,
                    "longitude": s.longitude,
                    "state": s.state,
                    "zone": s.zone,
                    "is_junction": s.is_junction
                }
                for s in stations
            ]
    except Exception as e:
        logger.error(f"List stations error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list stations")

# Trains API
@app.get("/api/v1/trains/{number}")
async def get_train_info(
    number: str,
    system: Any = Depends(get_system_dependency)
):
    """Get information about a specific train."""
    try:
        with db_manager.session_scope() as session:
            train = session.query(Train).filter(Train.number == number).first()
            if not train:
                raise HTTPException(status_code=404, detail="Train not found")

            return {
                "id": str(train.id),
                "number": train.number,
                "name": train.name,
                "type": train.type,
                "operator": train.operator,
                "max_speed_kmph": train.max_speed_kmph,
                "total_coaches": train.total_coaches,
                "classes_available": train.classes_available,
                "is_active": train.is_active
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Train info error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get train info")

# Service Discovery API
@app.post("/api/v1/services/register")
async def register_service(
    request: ServiceRegistrationRequest,
    system: Any = Depends(get_system_dependency)
):
    """Register an external service."""
    try:
        from autonomous_system import ServiceRegistration
        registration = ServiceRegistration(**request.dict())
        service_id = await autonomous_system.service_discovery.register_service(registration)
        return {"service_id": service_id, "status": "registered"}
    except Exception as e:
        logger.error(f"Service registration error: {e}")
        raise HTTPException(status_code=500, detail="Service registration failed")

@app.get("/api/v1/services")
async def discover_services(
    service_type: Optional[str] = None,
    system: Any = Depends(get_system_dependency)
):
    """Discover available services."""
    try:
        services = await autonomous_system.service_discovery.discover_services(service_type)
        return [
            {
                "service_id": s.service_id,
                "service_type": s.service_type,
                "service_name": s.service_name,
                "host": s.host,
                "port": s.port,
                "status": s.status,
                "endpoints": s.endpoints
            }
            for s in services
        ]
    except Exception as e:
        logger.error(f"Service discovery error: {e}")
        raise HTTPException(status_code=500, detail="Service discovery failed")

# System Management API
@app.get("/api/v1/system/health", response_model=SystemHealth)
async def get_system_health(
    system: Any = Depends(get_system_dependency)
):
    """Get comprehensive system health status."""
    try:
        health = await autonomous_system.autonomous_optimizer._get_system_health()
        return health
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.get("/api/v1/system/status")
async def get_system_status(
    system: Any = Depends(get_system_dependency)
):
    """Get comprehensive system status."""
    try:
        return await autonomous_system.get_system_status()
    except Exception as e:
        logger.error(f"System status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")

@app.post("/api/v1/system/optimize")
async def trigger_optimization(
    background_tasks: BackgroundTasks,
    system: Any = Depends(get_system_dependency)
):
    """Trigger autonomous system optimization."""
    try:
        background_tasks.add_task(autonomous_system.autonomous_optimizer.optimize_performance)
        return {"status": "optimization_started"}
    except Exception as e:
        logger.error(f"Optimization trigger error: {e}")
        raise HTTPException(status_code=500, detail="Optimization trigger failed")

@app.post("/api/v1/system/schema-sync")
async def trigger_schema_sync(
    background_tasks: BackgroundTasks,
    system: Any = Depends(get_system_dependency)
):
    """Trigger schema synchronization."""
    try:
        background_tasks.add_task(autonomous_system.schema_synchronizer.synchronize_schemas)
        return {"status": "schema_sync_started"}
    except Exception as e:
        logger.error(f"Schema sync trigger error: {e}")
        raise HTTPException(status_code=500, detail="Schema sync trigger failed")

# Analytics API
@app.get("/api/v1/analytics/performance")
async def get_performance_analytics(
    system: Any = Depends(get_system_dependency)
):
    """Get system performance analytics."""
    try:
        return await db_core.analyze_system_performance()
    except Exception as e:
        logger.error(f"Performance analytics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance analytics")

@app.get("/api/v1/analytics/station/{code}/connectivity")
async def get_station_connectivity(
    code: str,
    system: Any = Depends(get_system_dependency)
):
    """Get connectivity analysis for a station."""
    try:
        return await db_core.get_station_connectivity_report(code)
    except Exception as e:
        logger.error(f"Station connectivity error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get station connectivity")

# Security API
@app.get("/api/v1/security/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    system: Any = Depends(get_system_dependency)
):
    """Get recent audit logs."""
    try:
        with db_manager.session_scope() as session:
            logs = session.query(AuditLog).filter(
                AuditLog.is_deleted == False
            ).order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset).all()

            return [
                {
                    "id": str(log.id),
                    "tenant_id": str(log.tenant_id),
                    "user_id": str(log.user_id) if log.user_id else None,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": str(log.resource_id) if log.resource_id else None,
                    "timestamp": log.timestamp.isoformat(),
                    "ip_address": str(log.ip_address) if log.ip_address else None
                }
                for log in logs
            ]
    except Exception as e:
        logger.error(f"Audit logs error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get audit logs")

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return {"detail": "Internal server error", "status_code": 500}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)