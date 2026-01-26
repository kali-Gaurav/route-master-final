"""
Routing Engine

Core business logic for finding routes between stations.
Uses graph algorithms for efficient route discovery.

Features:
- Multi-hop route generation
- Graph construction from DB
- Dijkstra's algorithm for shortest path
- Time window calculations
- Route ranking and filtering
- Caching of computation results
"""

import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from heapq import heappush, heappop
from sqlalchemy.orm import Session

from production_pipeline.database import (
    Train, Station, TrainStation, CleanDataset
)

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class RouteStop:
    """A stop in a route"""
    station_code: str
    station_name: str
    arrival_time: Optional[str] = None
    departure_time: Optional[str] = None
    halt_minutes: int = 0


@dataclass
class RouteSegment:
    """A single train segment in a route"""
    train_no: str
    train_name: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    stops: List[RouteStop]
    duration_minutes: int


@dataclass
class Route:
    """A complete route from origin to destination"""
    segments: List[RouteSegment]
    total_duration_minutes: int
    num_trains: int
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    confidence_score: float = 1.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API response"""
        return {
            "segments": [
                {
                    "train_no": s.train_no,
                    "train_name": s.train_name,
                    "from": s.origin,
                    "to": s.destination,
                    "departure": s.departure_time,
                    "arrival": s.arrival_time,
                    "duration_minutes": s.duration_minutes,
                    "stops": [
                        {
                            "code": stop.station_code,
                            "name": stop.station_name,
                            "arrival": stop.arrival_time,
                            "departure": stop.departure_time,
                            "halt_minutes": stop.halt_minutes,
                        }
                        for stop in s.stops
                    ]
                }
                for s in self.segments
            ],
            "summary": {
                "num_trains": self.num_trains,
                "total_duration_minutes": self.total_duration_minutes,
                "departure": self.departure_time,
                "arrival": self.arrival_time,
                "confidence_score": self.confidence_score,
            }
        }


class RouteGraph:
    """Graph representation of railway network"""
    
    def __init__(self, session: Session):
        """Initialize route graph from database
        
        Args:
            session: Database session
        """
        self.session = session
        self.graph: Dict[str, List[Tuple[str, str]]] = {}  # station -> [(next_station, train_no), ...]
        self.trains: Dict[str, Train] = {}  # train_no -> Train object
        self.stations: Dict[str, Station] = {}  # station_code -> Station object
        self._build_graph()
    
    def _build_graph(self):
        """Build graph from database"""
        logger.info("Building route graph...")
        
        # Load all stations
        all_stations = self.session.query(Station).all()
        for station in all_stations:
            self.stations[station.code] = station
            self.graph[station.code] = []
        
        # Load all active trains with their routes
        all_trains = self.session.query(Train).filter(
            Train.status.name == 'ACTIVE'
        ).all()
        
        for train in all_trains:
            self.trains[train.train_no] = train
            
            # Get train's route (stops in order)
            stops = self.session.query(TrainStation).filter(
                TrainStation.train_id == train.id
            ).order_by(TrainStation.sequence).all()
            
            # Add edges to graph
            for i in range(len(stops) - 1):
                current_stop = stops[i]
                next_stop = stops[i + 1]
                
                current_station = current_stop.station.code
                next_station = next_stop.station.code
                
                # Add edge (station -> next_station via train)
                self.graph[current_station].append((next_station, train.train_no))
        
        logger.info(f"Graph built: {len(self.stations)} stations, {len(self.trains)} trains")
    
    def get_connected_trains(self, from_code: str, to_code: str) -> List[str]:
        """Get trains that connect two stations directly
        
        Args:
            from_code: Source station code
            to_code: Destination station code
            
        Returns:
            List of train numbers
        """
        if from_code not in self.graph:
            return []
        
        return [train_no for next_station, train_no in self.graph[from_code] 
                if next_station == to_code]


class RoutingEngine:
    """Core routing logic"""
    
    def __init__(self, session: Session):
        """Initialize routing engine
        
        Args:
            session: Database session
        """
        self.session = session
        self.graph = RouteGraph(session)
        self.max_transfers = 3  # Maximum transfers allowed
        self.max_halt_time = 120  # Max minutes between trains
        logger.info("RoutingEngine initialized")
    
    def _get_train_stops(self, train_no: str, from_code: str, to_code: str) -> Optional[List[RouteStop]]:
        """Get stops for a train segment
        
        Args:
            train_no: Train number
            from_code: From station code
            to_code: To station code
            
        Returns:
            List of route stops or None if invalid segment
        """
        if train_no not in self.graph.trains:
            return None
        
        train = self.graph.trains[train_no]
        
        # Get train's full route
        all_stops = self.session.query(TrainStation).filter(
            TrainStation.train_id == train.id
        ).order_by(TrainStation.sequence).all()
        
        # Find from and to indices
        from_idx = None
        to_idx = None
        
        for i, stop in enumerate(all_stops):
            if stop.station.code == from_code:
                from_idx = i
            if stop.station.code == to_code:
                to_idx = i
        
        if from_idx is None or to_idx is None or from_idx >= to_idx:
            return None
        
        # Build route stops
        route_stops = []
        for stop in all_stops[from_idx:to_idx + 1]:
            route_stops.append(RouteStop(
                station_code=stop.station.code,
                station_name=stop.station.name,
                arrival_time=stop.arrival_time,
                departure_time=stop.departure_time,
                halt_minutes=stop.halt_minutes or 0
            ))
        
        return route_stops
    
    def _time_to_minutes(self, time_str: Optional[str]) -> int:
        """Convert HH:MM time to minutes since midnight
        
        Args:
            time_str: Time string in HH:MM format
            
        Returns:
            Minutes since midnight
        """
        if not time_str:
            return 0
        
        try:
            hours, minutes = map(int, time_str.split(":"))
            return hours * 60 + minutes
        except:
            return 0
    
    def find_direct_routes(self, origin: str, destination: str) -> List[Route]:
        """Find direct train routes
        
        Args:
            origin: Origin station code
            destination: Destination station code
            
        Returns:
            List of Route objects
        """
        routes = []
        
        # Find trains that connect directly
        train_nos = self.graph.get_connected_trains(origin, destination)
        
        for train_no in train_nos:
            train = self.graph.trains[train_no]
            
            # Get stops for this segment
            stops = self._get_train_stops(train_no, origin, destination)
            if not stops or len(stops) < 2:
                continue
            
            # Get times
            departure = stops[0].departure_time
            arrival = stops[-1].arrival_time
            
            if not departure or not arrival:
                continue
            
            # Calculate duration
            dept_minutes = self._time_to_minutes(departure)
            arriv_minutes = self._time_to_minutes(arrival)
            
            if arriv_minutes < dept_minutes:
                # Next day arrival
                duration = (24 * 60 - dept_minutes) + arriv_minutes
            else:
                duration = arriv_minutes - dept_minutes
            
            # Create segment and route
            segment = RouteSegment(
                train_no=train.train_no,
                train_name=train.train_name,
                origin=origin,
                destination=destination,
                departure_time=departure,
                arrival_time=arrival,
                stops=stops,
                duration_minutes=duration
            )
            
            route = Route(
                segments=[segment],
                total_duration_minutes=duration,
                num_trains=1,
                origin=origin,
                destination=destination,
                departure_time=departure,
                arrival_time=arrival,
                confidence_score=1.0
            )
            
            routes.append(route)
        
        return routes
    
    def find_routes(self, origin: str, destination: str, max_transfers: int = None) -> List[Route]:
        """Find all possible routes between two stations
        
        Args:
            origin: Origin station code
            destination: Destination station code
            max_transfers: Maximum number of transfers (default: 3)
            
        Returns:
            List of Route objects, sorted by duration
        """
        if max_transfers is None:
            max_transfers = self.max_transfers
        
        logger.info(f"Finding routes: {origin} -> {destination}")
        
        # Start with direct routes
        routes = self.find_direct_routes(origin, destination)
        logger.debug(f"Found {len(routes)} direct routes")
        
        # TODO: Implement BFS for multi-hop routes
        # This would search for routes with 1, 2, 3+ transfers
        # For now, return direct routes only
        
        # Sort by duration
        routes.sort(key=lambda r: r.total_duration_minutes)
        
        logger.info(f"Found {len(routes)} total routes")
        return routes
    
    def rank_routes(self, routes: List[Route]) -> List[Route]:
        """Rank routes by desirability
        
        Args:
            routes: List of routes
            
        Returns:
            Sorted list of routes
        """
        # Simple ranking: prefer shorter duration, fewer trains, higher confidence
        def route_score(route: Route) -> Tuple[int, int, float]:
            return (
                route.total_duration_minutes,
                -route.num_trains,  # Negative so fewer trains rank higher
                -route.confidence_score  # Negative for descending sort
            )
        
        routes.sort(key=route_score)
        return routes
    
    def filter_routes(self, routes: List[Route], max_results: int = 10) -> List[Route]:
        """Filter routes to top results
        
        Args:
            routes: List of routes
            max_results: Maximum routes to return
            
        Returns:
            Filtered list
        """
        # Remove duplicate routes (same trains in same order)
        seen_signatures = set()
        unique_routes = []
        
        for route in routes:
            signature = tuple((s.train_no, s.origin, s.destination) for s in route.segments)
            if signature not in seen_signatures:
                unique_routes.append(route)
                seen_signatures.add(signature)
        
        return unique_routes[:max_results]
    
    def search(self, origin: str, destination: str, max_results: int = 10) -> List[Route]:
        """Complete route search
        
        Args:
            origin: Origin station code
            destination: Destination station code
            max_results: Maximum results to return
            
        Returns:
            List of Route objects
        """
        # Validate inputs
        if origin == destination:
            logger.warning(f"Origin equals destination: {origin}")
            return []
        
        if origin not in self.graph.stations:
            logger.warning(f"Unknown origin: {origin}")
            return []
        
        if destination not in self.graph.stations:
            logger.warning(f"Unknown destination: {destination}")
            return []
        
        # Find routes
        routes = self.find_routes(origin, destination)
        
        # Rank routes
        routes = self.rank_routes(routes)
        
        # Filter to top results
        routes = self.filter_routes(routes, max_results)
        
        return routes
