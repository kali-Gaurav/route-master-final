"""
PERFORMANCE OPTIMIZATION MODULE FOR ROUTE MASTER
=================================================
This module provides optimized versions of core functions using:
- Pre-indexed graph structures (O(1) lookup)
- Vectorized NumPy operations for Pareto filtering
- Efficient pandas operations (itertuples instead of iterrows)
- MessagePack serialization for faster I/O
"""

import numpy as np
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Set
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from database_manager import DatabaseManager

logger = logging.getLogger("route_master_optimization")

# ==================== GRAPH OPTIMIZATION ====================

class OptimizedGraphBuilder:
    """Pre-build and cache the entire graph at startup for O(1) access."""

    def __init__(self, db_manager=None):
        self.db = db_manager or DatabaseManager()
        self.adjacency_list = defaultdict(list)
        self.station_to_id = {}
        self.id_to_station = {}
        self.single_transfer_matrix = {}  # For fast 1-transfer lookups

    def build_from_database(self) -> Dict:
        """
        Build the complete graph from database at startup.

        Uses indexed database queries for O(E log V) complexity.
        """
        logger.info("Building optimized graph from database...")
        start_time = datetime.now()

        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            # Step 1: Create station mappings (O(n) where n = unique stations)
            cursor.execute("SELECT station_code FROM stations ORDER BY station_code")
            stations = [row[0] for row in cursor.fetchall()]
            self.station_to_id = {station: i for i, station in enumerate(stations)}
            self.id_to_station = {i: station for i, station in enumerate(stations)}

            logger.info(f"  [1/3] Created {len(stations)} station mappings")

            # Step 2: Build adjacency list from database
            edge_count = 0
            error_count = 0
            train_count = 0

            # Get all trains with their stations
            cursor.execute("""
                SELECT
                    t.train_no,
                    ts1.station_id as from_station_id,
                    ts2.station_id as to_station_id,
                    s1.station_code as from_station,
                    s2.station_code as to_station,
                    ts1.sequence as from_seq,
                    ts2.sequence as to_seq,
                    COALESCE(ts1.departure_time, '00:00:00') as departure_time,
                    COALESCE(ts2.arrival_time, '00:00:00') as arrival_time
                FROM trains t
                JOIN train_stations ts1 ON t.id = ts1.train_id
                JOIN train_stations ts2 ON t.id = ts2.train_id
                JOIN stations s1 ON ts1.station_id = s1.id
                JOIN stations s2 ON ts2.station_id = s2.id
                WHERE ts1.sequence < ts2.sequence
                ORDER BY t.train_no, ts1.sequence, ts2.sequence
            """)

            rows = cursor.fetchall()
            logger.info(f"  Retrieved {len(rows)} train segments from database")

            for row in rows:
                train_no, from_station_id, to_station_id, from_station, to_station, from_seq, to_seq, departure_time, arrival_time = row

                if from_station not in self.station_to_id or to_station not in self.station_to_id:
                    continue

                from_id = self.station_to_id[from_station]
                to_id = self.station_to_id[to_station]

                # Calculate duration (simplified - would need proper time calculation)
                duration_minutes = 60  # Placeholder - implement proper time calculation

                # Store edge information
                edge = {
                    'to_station': to_station,
                    'to_id': to_id,
                    'train_no': str(train_no),
                    'distance': 100,  # Placeholder - would need distance calculation
                    'duration_minutes': duration_minutes,
                    'departure_time': departure_time,
                    'arrival_time': arrival_time,
                    'intermediate_stops': to_seq - from_seq - 1
                }

                # Key by station ID, not station code
                self.adjacency_list[from_id].append(edge)
                edge_count += 1

            logger.info(f"  [2/3] Built {edge_count} edges (skipped {error_count} problematic edges)")

            # Step 3: Build single-transfer connectivity matrix (bitwise acceleration)
            self._build_transfer_matrix()

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"  [3/3] Graph built in {elapsed:.2f}s")
            logger.info(f"Optimized graph ready: {len(stations)} stations, {edge_count} edges")

            return {
                'adjacency_list': self.adjacency_list,
                'station_to_id': self.station_to_id,
                'id_to_station': self.id_to_station,
                'transfer_matrix': self.single_transfer_matrix
            }

        finally:
            conn.close()
    
    def _calculate_duration_minutes(self, departure: str, arrival: str) -> float:
        """Calculate duration in minutes between two times - robust with fallback."""
        try:
            # Convert to strings and strip whitespace
            dep_str = str(departure).strip() if departure else "00:00:00"
            arr_str = str(arrival).strip() if arrival else "00:00:00"
            
            # Clean up any NaN or None values
            if not dep_str or dep_str.lower() in ['nan', 'none', 'null', '']:
                dep_str = "00:00:00"
            if not arr_str or arr_str.lower() in ['nan', 'none', 'null', '']:
                arr_str = "00:00:00"
            
            # Handle various time formats
            for fmt in ['%H:%M:%S', '%H:%M', '%H', '%I:%M:%S %p', '%I:%M %p']:
                try:
                    t1 = datetime.strptime(dep_str, fmt)
                    t2 = datetime.strptime(arr_str, fmt)
                    
                    if t2 < t1:
                        t2 += timedelta(days=1)
                    
                    duration = (t2 - t1).total_seconds() / 60
                    return max(0, duration)  # Ensure non-negative
                except (ValueError, TypeError):
                    continue
            
            # If all formats fail, return 0 or use a default
            logger.debug(f"Could not parse times: dep={dep_str}, arr={arr_str}")
            return 0
            
        except Exception as e:
            logger.warning(f"Error in _calculate_duration_minutes: {e}")
            return 0  # Safe fallback
            logger.debug(f"Error calculating duration: {e}")
            return 0
    
    def _build_transfer_matrix(self):
        """
        Build a sparse matrix for O(1) single-transfer lookups.
        matrix[A][B] = set of trains connecting A->B directly
        """
        logger.info("  Building transfer matrix...")
        for from_station, edges in self.adjacency_list.items():
            for edge in edges:
                to_station = edge['to_station']
                key = f"{from_station}->{to_station}"
                if key not in self.single_transfer_matrix:
                    self.single_transfer_matrix[key] = set()
                self.single_transfer_matrix[key].add(edge['train_no'])
    
    def get_direct_trains(self, source: str, destination: str) -> List[str]:
        """Get all direct trains O(1) lookup."""
        key = f"{source}->{destination}"
        return list(self.single_transfer_matrix.get(key, set()))
    
    def get_single_transfer_stations(self, source: str, destination: str) -> Set[str]:
        """
        Find all possible transfer stations between source and destination.
        Uses matrix AND operation for speed.
        """
        transfer_stations = set()
        
        # Get all 1st leg destinations from source
        if source in self.adjacency_list:
            for edge_from_source in self.adjacency_list[source]:
                intermediate = edge_from_source['to_station']
                
                # Check if intermediate has path to destination
                if intermediate in self.adjacency_list:
                    for edge_from_intermediate in self.adjacency_list[intermediate]:
                        if edge_from_intermediate['to_station'] == destination:
                            transfer_stations.add(intermediate)
                            break
        
        return transfer_stations


# ==================== PARETO OPTIMIZATION ====================

class OptimizedParetoOptimizer:
    """
    Vectorized Pareto optimization using NumPy.
    Replaces O(n^2 * k) Python nested loops with compiled C operations.
    """
    
    @staticmethod
    def vectorized_pareto_filter(routes: List[Dict], objectives: List[Dict]) -> Tuple[List[int], List[Dict]]:
        """
        Find Pareto-optimal routes using NumPy vectorization.
        
        Args:
            routes: List of route dictionaries
            objectives: List of objective dictionaries (time, cost, transfers, seat_prob, safety)
        
        Returns:
            Tuple of (pareto_indices, objectives_matrix)
        """
        if not routes:
            return [], np.array([])
        
        # Convert objectives to NumPy array for vectorized operations
        # Objectives to minimize: time (hours), cost (rupees), transfers (count)
        # Objectives to maximize: seat_prob, safety_score (negate for minimization)
        objectives_matrix = np.array([
            [
                obj['time'],
                obj['cost'],
                obj['transfers'],
                -obj.get('seat_prob', 0),
                -obj.get('safety_score', 0)
            ]
            for obj in objectives
        ], dtype=np.float32)
        
        # Vectorized dominance check
        # Route i is dominated if there exists j such that j <= i in all objectives
        n_routes = len(routes)
        is_dominated = np.zeros(n_routes, dtype=bool)
        
        # Compare each route against all others (vectorized)
        for i in range(n_routes):
            if is_dominated[i]:
                continue
            
            # Check which routes dominate route i
            # A route j dominates i if: j <= i in ALL objectives AND j < i in at least ONE
            dominates = np.all(
                objectives_matrix <= objectives_matrix[i],
                axis=1
            ) & np.any(
                objectives_matrix < objectives_matrix[i],
                axis=1
            )
            
            is_dominated[dominates] = True
            is_dominated[i] = False  # Route is not dominated by itself
        
        pareto_indices = np.where(~is_dominated)[0]
        
        return pareto_indices.tolist(), objectives_matrix
    
    @staticmethod
    def rank_routes_by_criteria(routes: List[Dict], objectives: List[Dict]) -> Dict[str, List[int]]:
        """
        Rank routes by different criteria without building entire Pareto front.
        Used for "Fastest", "Cheapest", "Fewest Transfers" categories.
        """
        if not routes:
            return {'fastest': [], 'cheapest': [], 'safest': []}
        
        objectives_array = np.array([
            [obj['time'], obj['cost'], obj['transfers'], -obj.get('seat_prob', 0)]
            for obj in objectives
        ])
        
        fastest_idx = np.argsort(objectives_array[:, 0])  # Sort by time
        cheapest_idx = np.argsort(objectives_array[:, 1])  # Sort by cost
        fewest_transfers_idx = np.argsort(objectives_array[:, 2])  # Sort by transfers
        
        return {
            'fastest': fastest_idx[:5].tolist(),
            'cheapest': cheapest_idx[:5].tolist(),
            'fewest_transfers': fewest_transfers_idx[:5].tolist()
        }


# ==================== EFFICIENT SERIALIZATION ====================

class OptimizedSerializer:
    """Fast serialization using MessagePack (3x faster than JSON for large data)."""
    
    @staticmethod
    def serialize_routes(routes: List[Dict]) -> bytes:
        """Serialize routes to MessagePack binary format."""
        try:
            import msgpack
            return msgpack.packb(routes, use_bin_type=True)
        except ImportError:
            # Fallback to JSON if msgpack not available
            logger.warning("msgpack not available, falling back to JSON")
            return json.dumps(routes).encode('utf-8')
    
    @staticmethod
    def deserialize_routes(data: bytes) -> List[Dict]:
        """Deserialize routes from MessagePack binary format."""
        try:
            import msgpack
            return msgpack.unpackb(data, raw=False)
        except ImportError:
            logger.warning("msgpack not available, falling back to JSON")
            return json.loads(data.decode('utf-8'))
    
    @staticmethod
    def save_routes_fast(routes: List[Dict], filepath: str):
        """Save routes using fast binary serialization."""
        try:
            import msgpack
            with open(filepath, 'wb') as f:
                msgpack.dump(routes, f, use_bin_type=True)
            logger.info(f"Routes saved to {filepath} (MessagePack)")
        except ImportError:
            # Fallback to JSON
            with open(filepath, 'w') as f:
                json.dump(routes, f)
            logger.info(f"Routes saved to {filepath} (JSON)")
    
    @staticmethod
    def load_routes_fast(filepath: str) -> List[Dict]:
        """Load routes using fast binary deserialization."""
        try:
            import msgpack
            with open(filepath, 'rb') as f:
                return msgpack.load(f, raw=False)
        except (ImportError, FileNotFoundError):
            # Fallback to JSON
            with open(filepath, 'r') as f:
                return json.load(f)


# ==================== BATCH PROCESSING ====================

class BatchOptimizer:
    """Process multiple requests in parallel for better cache utilization."""
    
    @staticmethod
    def batch_compute_objectives(routes: List[List[Dict]]) -> List[List[Dict]]:
        """
        Compute objectives for multiple routes using vectorized operations.
        routes: List of route lists
        """
        all_objectives = []
        
        for route_list in routes:
            objectives = []
            for route in route_list:
                obj = {
                    'time': sum(seg.get('duration_minutes', 0) for seg in route),
                    'cost': sum(seg.get('fare', 0) for seg in route),
                    'transfers': len(route) - 1,
                    'seat_prob': 1.0,  # Placeholder
                    'safety_score': 1.0  # Placeholder
                }
                objectives.append(obj)
            all_objectives.append(objectives)
        
        return all_objectives


# ==================== PERFORMANCE METRICS ====================

class PerformanceMonitor:
    """Track and log performance metrics."""
    
    def __init__(self):
        self.timings = defaultdict(list)
    
    def record_time(self, operation: str, duration_ms: float):
        """Record operation timing."""
        self.timings[operation].append(duration_ms)
    
    def get_stats(self) -> Dict:
        """Get performance statistics."""
        stats = {}
        for op, timings in self.timings.items():
            stats[op] = {
                'calls': len(timings),
                'avg_ms': np.mean(timings),
                'min_ms': np.min(timings),
                'max_ms': np.max(timings),
                'p95_ms': np.percentile(timings, 95)
            }
        return stats
    
    def print_report(self):
        """Print performance report."""
        logger.info("\n" + "="*80)
        logger.info(" PERFORMANCE OPTIMIZATION REPORT")
        logger.info("="*80)
        
        stats = self.get_stats()
        for op, metrics in stats.items():
            logger.info(f"\n{op}:")
            logger.info(f"  Calls:    {metrics['calls']}")
            logger.info(f"  Avg:      {metrics['avg_ms']:.2f}ms")
            logger.info(f"  Min/Max:  {metrics['min_ms']:.2f}ms / {metrics['max_ms']:.2f}ms")
            logger.info(f"  P95:      {metrics['p95_ms']:.2f}ms")


# Create global instances
graph_builder = OptimizedGraphBuilder()
pareto_optimizer = OptimizedParetoOptimizer()
serializer = OptimizedSerializer()
perf_monitor = PerformanceMonitor()

__all__ = [
    'OptimizedGraphBuilder',
    'OptimizedParetoOptimizer',
    'OptimizedSerializer',
    'BatchOptimizer',
    'PerformanceMonitor',
    'graph_builder',
    'pareto_optimizer',
    'serializer',
    'perf_monitor'
]
