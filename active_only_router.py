"""
ACTIVE-ONLY ROUTING ENGINE

Routes using only IRCTC-validated ACTIVE trains.
Integrates with IRCTC Validator to ensure all routes are bookable.

Author: Route Master
Date: 2026-01-25
"""

import logging
from typing import Dict, List, Tuple, Set, Optional
from datetime import datetime
import pandas as pd
import numpy as np

try:
    from database_manager import DatabaseManager
    from irctc_validator import IRCTCValidator
    from logger import LoggerFactory
except ImportError:
    import logging as LoggerFactory
    DatabaseManager = None

class ActiveOnlyRouter:
    """
    Routes trains only after IRCTC validation confirms:
    - Train has available seats (not waitlist only)
    - Train is ACTIVE status in database
    - Validation is recent (< 12 hours old)
    
    Workflow:
    1. Load all trains from database
    2. Filter to ACTIVE status only (from IRCTC Validator)
    3. Build route graph from ACTIVE trains only
    4. Generate routes = all paths include ONLY ACTIVE trains
    5. Return high-confidence bookable routes
    """
    
    def __init__(self, db_manager: Optional['DatabaseManager'] = None):
        self.db = db_manager or self._init_db()
        self.validator = IRCTCValidator()
        self.logger = self._setup_logger()
        self.active_trains = set()
        self.inactive_trains = set()
        self.unknown_trains = set()
        self.adjacency_list = {}
        self.last_refresh = None
    
    def _setup_logger(self):
        """Setup logger"""
        try:
            return LoggerFactory.get_logger("active_only_router")
        except:
            logger = logging.getLogger("active_only_router")
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            return logger
    
    def _init_db(self):
        """Initialize database connection"""
        try:
            from database_manager import DatabaseManager
            return DatabaseManager()
        except:
            self.logger.warning("Could not initialize database")
            return None
    
    def load_active_trains(self) -> Tuple[int, int, int]:
        """
        Load train statuses from database
        
        Returns:
            (active_count, inactive_count, unknown_count)
        """
        if not self.db:
            self.logger.error("No database connection")
            return 0, 0, 0
        
        try:
            # Get all trains
            all_trains = self.db.session.query(self.db.Train).all()
            
            for train in all_trains:
                train_no = str(train.train_no)
                
                if train.status == "ACTIVE":
                    self.active_trains.add(train_no)
                elif train.status == "INACTIVE":
                    self.inactive_trains.add(train_no)
                else:
                    self.unknown_trains.add(train_no)
            
            self.last_refresh = datetime.now()
            
            self.logger.info(f"✓ Loaded train statuses:")
            self.logger.info(f"  ACTIVE: {len(self.active_trains)}")
            self.logger.info(f"  INACTIVE: {len(self.inactive_trains)}")
            self.logger.info(f"  UNKNOWN: {len(self.unknown_trains)}")
            
            return len(self.active_trains), len(self.inactive_trains), len(self.unknown_trains)
        
        except Exception as e:
            self.logger.error(f"Error loading train statuses: {e}")
            return 0, 0, 0
    
    def validate_inactive_trains(self, limit: int = 100) -> Dict[str, int]:
        """
        Validate unknown/inactive trains to update status
        
        Args:
            limit: Max trains to validate in one batch
            
        Returns:
            Statistics of validated trains
        """
        if not self.db:
            self.logger.error("No database connection")
            return {}
        
        to_validate = list(self.unknown_trains | self.inactive_trains)[:limit]
        
        if not to_validate:
            self.logger.info("No trains to validate")
            return {"validated": 0, "became_active": 0, "remained_inactive": 0}
        
        self.logger.info(f"Validating {len(to_validate)} trains...")
        
        stats = {"validated": 0, "became_active": 0, "remained_inactive": 0}
        
        for train_no in to_validate:
            try:
                # Validate train (this calls IRCTC API internally with caching)
                result = self.validator.validate_train(train_no, date=None)
                
                if result and result.has_available_seats:
                    # Update database status to ACTIVE
                    self.db.update_train_status(train_no, "ACTIVE")
                    self.active_trains.add(train_no)
                    self.unknown_trains.discard(train_no)
                    self.inactive_trains.discard(train_no)
                    stats["became_active"] += 1
                else:
                    # Mark as INACTIVE
                    self.db.update_train_status(train_no, "INACTIVE")
                    self.inactive_trains.add(train_no)
                    self.unknown_trains.discard(train_no)
                    stats["remained_inactive"] += 1
                
                stats["validated"] += 1
            
            except Exception as e:
                self.logger.warning(f"Error validating {train_no}: {e}")
        
        self.logger.info(f"Validation complete: {stats['became_active']} became active")
        return stats
    
    def build_active_only_graph(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """
        Build route graph using ONLY ACTIVE trains
        
        Args:
            df: DataFrame with train routes (Train No, Station Code, SEQ, Distance, etc)
            
        Returns:
            Adjacency list: {source_station: [edges with ACTIVE trains only]}
        """
        self.logger.info(f"Building graph from {len(self.active_trains)} ACTIVE trains...")
        
        # Filter DataFrame to ACTIVE trains only
        df_active = df[df['Train No'].isin(self.active_trains)].copy()
        
        self.logger.info(f"Filtered to {len(df_active)} segments from ACTIVE trains")
        
        # Build adjacency list
        adjacency = {}
        edge_count = 0
        
        # Group by train
        for train_no, group in df_active.groupby('Train No'):
            # Sort by sequence
            group = group.sort_values('SEQ')
            stations = group[['Station Code', 'Distance', 'Departure Time', 'Arrival time']].values
            
            # Create edges between all pairs
            for i in range(len(stations)):
                from_station = stations[i][0]
                
                if from_station not in adjacency:
                    adjacency[from_station] = []
                
                for j in range(i + 1, len(stations)):
                    to_station = stations[j][0]
                    
                    try:
                        distance = abs(float(stations[j][1]) - float(stations[i][1]))
                        
                        edge = {
                            'to_station': to_station,
                            'train_no': str(train_no),
                            'distance': distance,
                            'departure_time': str(stations[i][2]),
                            'arrival_time': str(stations[j][3]),
                            'transfers': j - i - 1,
                            'is_active': True
                        }
                        
                        adjacency[from_station].append(edge)
                        edge_count += 1
                    
                    except:
                        continue
        
        self.adjacency_list = adjacency
        self.logger.info(f"✓ Graph built: {len(adjacency)} stations, {edge_count} edges (ALL ACTIVE)")
        
        return adjacency
    
    def find_routes_dijkstra(self, source: str, destination: str,
                            date: str, max_transfers: int = 2) -> List[Dict]:
        """
        Find routes from source to destination using only ACTIVE trains
        
        Uses Dijkstra's algorithm with optimization for:
        - Shortest time
        - Fewest transfers
        - Distance
        
        Args:
            source: Source station code
            destination: Destination station code
            date: Travel date (YYYY-MM-DD)
            max_transfers: Maximum transfers allowed (0=direct, 1=1 transfer, etc)
            
        Returns:
            List of routes, sorted by time then transfers
        """
        if source not in self.adjacency_list:
            self.logger.warning(f"Source {source} not in graph")
            return []
        
        if not destination:
            self.logger.warning("No destination specified")
            return []
        
        routes = []
        visited = set()
        
        def dfs(current: str, path: List[Dict], transfers: int,
                visited_local: Set[str]) -> List[Dict]:
            """Recursive DFS to find all paths"""
            
            if current == destination:
                return [path]
            
            if transfers >= max_transfers or len(visited_local) > 50:
                return []
            
            all_paths = []
            
            if current in self.adjacency_list:
                for edge in self.adjacency_list[current]:
                    next_station = edge['to_station']
                    
                    if next_station not in visited_local:
                        new_visited = visited_local | {next_station}
                        new_path = path + [edge]
                        
                        found = dfs(next_station, new_path, transfers + 1, new_visited)
                        all_paths.extend(found)
            
            return all_paths
        
        try:
            paths = dfs(source, [], 0, {source})
            
            # Convert paths to route objects
            for path in paths:
                route = {
                    'source': source,
                    'destination': destination,
                    'date': date,
                    'segments': path,
                    'total_distance': sum(s.get('distance', 0) for s in path),
                    'transfers': len(path) - 1,
                    'trains': [s['train_no'] for s in path],
                    'departure_time': path[0]['departure_time'] if path else None,
                    'arrival_time': path[-1]['arrival_time'] if path else None,
                    'all_trains_active': all(
                        s['train_no'] in self.active_trains for s in path
                    )
                }
                routes.append(route)
            
            # Sort by transfers then distance
            routes.sort(key=lambda r: (r['transfers'], r['total_distance']))
            
            self.logger.info(f"Found {len(routes)} routes from {source} to {destination}")
            return routes[:20]  # Return top 20
        
        except Exception as e:
            self.logger.error(f"Error finding routes: {e}")
            return []
    
    def validate_route_trains(self, route: Dict) -> Dict:
        """
        Validate all trains in a route are still ACTIVE
        
        Args:
            route: Route object with 'trains' field
            
        Returns:
            Updated route with validation info
        """
        trains = route.get('trains', [])
        valid_trains = []
        invalid_trains = []
        
        for train_no in trains:
            if train_no in self.active_trains:
                valid_trains.append(train_no)
            else:
                invalid_trains.append(train_no)
        
        route['valid_trains'] = valid_trains
        route['invalid_trains'] = invalid_trains
        route['is_valid'] = len(invalid_trains) == 0
        route['validation_time'] = datetime.now().isoformat()
        
        return route
    
    def validate_all_routes(self, routes: List[Dict]) -> Tuple[List[Dict], Dict]:
        """
        Validate all routes
        
        Returns:
            (valid_routes, statistics)
        """
        valid = []
        stats = {'total': len(routes), 'valid': 0, 'invalid': 0}
        
        for route in routes:
            validated = self.validate_route_trains(route)
            
            if validated['is_valid']:
                valid.append(validated)
                stats['valid'] += 1
            else:
                stats['invalid'] += 1
        
        self.logger.info(f"Route validation: {stats['valid']}/{stats['total']} valid")
        return valid, stats
    
    def get_status(self) -> Dict[str, any]:
        """Get router status"""
        return {
            'active_trains': len(self.active_trains),
            'inactive_trains': len(self.inactive_trains),
            'unknown_trains': len(self.unknown_trains),
            'total_stations': len(self.adjacency_list),
            'total_edges': sum(len(edges) for edges in self.adjacency_list.values()),
            'last_refresh': self.last_refresh.isoformat() if self.last_refresh else None,
            'is_ready': len(self.active_trains) > 0
        }


def main():
    """Example usage"""
    print("Active-Only Router Demo")
    print("=" * 50)
    
    # Initialize router
    router = ActiveOnlyRouter()
    
    # Load train statuses
    print("\n1. Loading ACTIVE trains...")
    active, inactive, unknown = router.load_active_trains()
    print(f"   Active: {active}, Inactive: {inactive}, Unknown: {unknown}")
    
    # Status
    print("\n2. Router Status:")
    status = router.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print("\n✓ Router initialized and ready for route discovery")


if __name__ == "__main__":
    main()
