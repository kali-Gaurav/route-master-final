# services/route_service.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional
from uuid import UUID
from ..models import Route, Station, Train
from ..schemas.route import RouteCreate, RouteUpdate, RouteSearch
from ..core.cache import cache
import json
import logging

logger = logging.getLogger(__name__)

class RouteService:
    def __init__(self, db: Session):
        self.db = db

    def get_route(self, route_id: UUID) -> Optional[Route]:
        """Get route by ID"""
        return self.db.query(Route).filter(Route.id == route_id).first()

    def get_routes(self, skip: int = 0, limit: int = 100) -> List[Route]:
        """Get all routes with optimized queries"""
        return self.db.query(Route).options(
            joinedload(Route.train),
            joinedload(Route.origin_station),
            joinedload(Route.destination_station)
        ).filter(Route.is_active == True).offset(skip).limit(limit).all()

    def search_routes(self, search: RouteSearch) -> List[Route]:
        """Search routes based on criteria with caching"""
        # Create cache key from search parameters
        cache_key = f"routes:search:{json.dumps(search.dict(), sort_keys=True, default=str)}"
        
        # Check cache first
        cached_results = cache.get(cache_key)
        if cached_results is not None:
            logger.info(f"Cache hit for route search: {cache_key[:50]}...")
            return cached_results
        
        # Build query with eager loading
        query = self.db.query(Route).options(
            joinedload(Route.train),
            joinedload(Route.origin_station),
            joinedload(Route.destination_station)
        ).filter(Route.is_active == True)

        if search.origin_station:
            # Find station by code or name
            origin_stations = self.db.query(Station.id).filter(
                or_(
                    Station.code.ilike(f"%{search.origin_station}%"),
                    Station.name.ilike(f"%{search.origin_station}%")
                ),
                Station.is_active == True
            ).subquery()
            query = query.filter(Route.origin_station_id.in_(origin_stations))

        if search.dest_station:
            # Find station by code or name
            dest_stations = self.db.query(Station.id).filter(
                or_(
                    Station.code.ilike(f"%{search.dest_station}%"),
                    Station.name.ilike(f"%{search.dest_station}%")
                ),
                Station.is_active == True
            ).subquery()
            query = query.filter(Route.dest_station_id.in_(dest_stations))

        results = query.offset(search.offset).limit(search.limit).all()
        
        # Cache results for 1 hour
        cache.set(cache_key, results, ttl_seconds=3600)
        logger.info(f"Cached route search results: {len(results)} routes")
        
        return results

    def create_route(self, route: RouteCreate) -> Route:
        """Create new route"""
        db_route = Route(**route.model_dump())
        self.db.add(db_route)
        self.db.commit()
        self.db.refresh(db_route)
        return db_route

    def update_route(self, route_id: UUID, route_update: RouteUpdate) -> Optional[Route]:
        """Update existing route"""
        db_route = self.get_route(route_id)
        if not db_route:
            return None

        update_data = route_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_route, field, value)

        self.db.commit()
        self.db.refresh(db_route)
        return db_route

    def delete_route(self, route_id: UUID) -> bool:
        """Delete route"""
        db_route = self.get_route(route_id)
        if not db_route:
            return False

        self.db.delete(db_route)
        self.db.commit()
        return True

    def get_stations(self, skip: int = 0, limit: int = 100) -> List[Station]:
        """Get all stations"""
        return self.db.query(Station).offset(skip).limit(limit).all()

    def get_station(self, station_id: UUID) -> Optional[Station]:
        """Get station by ID"""
        return self.db.query(Station).filter(Station.id == station_id).first()

    def create_station(self, station_data: dict) -> Station:
        """Create new station"""
        db_station = Station(**station_data)
        self.db.add(db_station)
        self.db.commit()
        self.db.refresh(db_station)
        return db_station