# api/v1/routes.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from ...db_connection import get_db
from ...models import Route, Station, User
from ...schemas.route import RouteCreate, RouteUpdate, RouteSearch, Route as RouteSchema, Station as StationSchema
from ...services.route_service import RouteService
from ...core.auth import get_current_active_user, require_operator

router = APIRouter()

@router.get("/search", response_model=List[RouteSchema])
async def search_routes(
    origin_station: Optional[str] = Query(None, description="Origin station code or name"),
    dest_station: Optional[str] = Query(None, description="Destination station code or name"),
    date: Optional[str] = Query(None, description="Travel date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Search routes with filters"""
    route_service = RouteService(db)
    search = RouteSearch(
        origin_station=origin_station,
        dest_station=dest_station,
        date=date,
        limit=limit,
        offset=offset
    )
    return route_service.search_routes(search)

@router.get("/{route_id}", response_model=RouteSchema)
async def get_route(
    route_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get route details"""
    route_service = RouteService(db)
    route = route_service.get_route(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route

@router.get("/", response_model=List[RouteSchema])
async def get_routes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),  # Reduced from 100, max now 500
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all routes with pagination"""
    route_service = RouteService(db)
    return route_service.get_routes(skip=skip, limit=limit)

@router.post("/", response_model=RouteSchema)
async def create_route(
    route: RouteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """Create new route (operator+)"""
    route_service = RouteService(db)
    return route_service.create_route(route)

@router.put("/{route_id}", response_model=RouteSchema)
async def update_route(
    route_id: UUID,
    route_update: RouteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """Update route (operator+)"""
    route_service = RouteService(db)
    updated_route = route_service.update_route(route_id, route_update)
    if not updated_route:
        raise HTTPException(status_code=404, detail="Route not found")
    return updated_route

@router.delete("/{route_id}")
async def delete_route(
    route_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """Delete route (operator+)"""
    route_service = RouteService(db)
    if not route_service.delete_route(route_id):
        raise HTTPException(status_code=404, detail="Route not found")
    return {"message": "Route deleted successfully"}

# Station endpoints
@router.get("/stations/", response_model=List[StationSchema])
async def get_stations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),  # Reduced from 100, max now 500
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all stations"""
    route_service = RouteService(db)
    return route_service.get_stations(skip=skip, limit=limit)

@router.get("/stations/{station_id}", response_model=StationSchema)
async def get_station(
    station_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get station details"""
    route_service = RouteService(db)
    station = route_service.get_station(station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    return station

@router.post("/stations/", response_model=StationSchema)
async def create_station(
    station: dict,  # Using dict for now, should use StationCreate schema
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator)
):
    """Create new station (operator+)"""
    route_service = RouteService(db)
    return route_service.create_station(station)