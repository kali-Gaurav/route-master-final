"""
Enhanced Multi-Transfer Route Generator
Supports routes with up to 4 transfers (5 segments)
Optimized for performance and comprehensive route discovery
"""

import time
from collections import deque
from typing import List, Dict, Tuple
import json
from datetime import datetime
from database_manager import DatabaseManager
from route_optimizer import ParetoTrainRouter
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdvancedMultiTransferRouter:
    """
    Advanced router that generates comprehensive multi-transfer routes
    up to 4 transfers (5 journey segments)
    """
    
    def __init__(self, database_manager=None):
        """Initialize with database and route optimizer"""
        self.db = database_manager or DatabaseManager()
        self.router = ParetoTrainRouter(self.db)
        
    def generate_all_transfer_routes(self, source: str, destination: str, 
                                     max_transfers: int = 4, 
                                     max_routes_per_type: int = 200) -> Dict:
        """
        Generate routes with all transfer levels (0-4 transfers)
        
        Args:
            source: Source station code
            destination: Destination station code
            max_transfers: Maximum number of transfers (default 4)
            max_routes_per_type: Max routes per transfer level
            
        Returns:
            Dictionary with routes organized by transfer count
        """
        
        logger.info(f"\n{'='*80}")
        logger.info(f"ADVANCED MULTI-TRANSFER ROUTE GENERATION")
        logger.info(f"{'='*80}")
        logger.info(f"Source: {source} → Destination: {destination}")
        logger.info(f"Max Transfers: {max_transfers}")
        logger.info(f"Max Routes per Type: {max_routes_per_type}")
        
        start_time = time.time()
        
        try:
            # Get station IDs
            source_id = self.router.station_to_id.get(source)
            dest_id = self.router.station_to_id.get(destination)
            
            if not source_id or not dest_id:
                logger.error(f"Invalid stations: {source} or {destination}")
                return {}
            
            results = {
                'metadata': {
                    'source': source,
                    'destination': destination,
                    'generated_at': datetime.now().isoformat(),
                    'max_transfers': max_transfers,
                },
                'routes_by_transfer_count': {},
                'summary': {}
            }
            
            # Generate routes for each transfer count
            for transfer_count in range(max_transfers + 1):
                logger.info(f"\n[Phase {transfer_count + 1}] Generating routes with {transfer_count} transfer(s)...")
                
                if transfer_count == 0:
                    routes = self._find_zero_transfer_routes(source_id, dest_id, max_routes_per_type)
                elif transfer_count == 1:
                    routes = self._find_one_transfer_routes(source_id, dest_id, max_routes_per_type)
                elif transfer_count >= 2:
                    routes = self._find_n_transfer_routes(source_id, dest_id, transfer_count, max_routes_per_type)
                
                results['routes_by_transfer_count'][transfer_count] = routes
                results['summary'][f'{transfer_count}_transfer_routes'] = len(routes)
                
                logger.info(f"  ✓ Found {len(routes)} routes with {transfer_count} transfer(s)")
            
            # Calculate totals
            total_routes = sum(len(routes) for routes in results['routes_by_transfer_count'].values())
            results['summary']['total_routes'] = total_routes
            results['summary']['generation_time_seconds'] = time.time() - start_time
            
            logger.info(f"\n{'='*80}")
            logger.info(f"GENERATION COMPLETE")
            logger.info(f"{'='*80}")
            logger.info(f"Total Routes Generated: {total_routes}")
            logger.info(f"Generation Time: {results['summary']['generation_time_seconds']:.2f}s")
            logger.info(f"Routes by Transfer Count:")
            for tc, count in results['summary'].items():
                if 'transfer_routes' in tc:
                    logger.info(f"  {tc}: {count}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error generating routes: {e}")
            raise
    
    def _find_zero_transfer_routes(self, source_id, dest_id, max_routes=200) -> List[List[Dict]]:
        """Find direct routes (no transfers)"""
        return self.router._find_direct_routes(source_id, dest_id)
    
    def _find_one_transfer_routes(self, source_id, dest_id, max_routes=200) -> List[List[Dict]]:
        """Find single-transfer routes"""
        return self.router._find_single_transfer_routes(source_id, dest_id, max_routes)
    
    def _find_n_transfer_routes(self, source_id, dest_id, num_transfers: int, 
                               max_routes=200) -> List[List[Dict]]:
        """
        Find routes with n transfers (n >= 2) using BFS
        Enhanced to support up to 4 transfers
        """
        
        routes = []
        queue = deque([(source_id, [], 0, 0)])  # (station, path, transfers, distance)
        visited = {}  # station_id -> min_transfers_to_reach
        processed = 0
        max_queue_size = 50000  # Increased for 4-transfer search
        max_distance = 4000  # Increased distance limit for longer routes
        
        logger.info(f"      Starting BFS for {num_transfers}-transfer routes...")
        
        while queue and len(routes) < max_routes:
            processed += 1
            if processed % 5000 == 0:
                logger.info(f"      Processed {processed} paths, found {len(routes)} routes...")
            
            if len(queue) > max_queue_size:
                logger.info(f"      Queue limit reached ({len(queue)}), stopping...")
                break
            
            curr_id, path, transfers, total_dist = queue.popleft()
            
            # Check if we've reached destination with correct transfer count
            if curr_id == dest_id and transfers == num_transfers:
                routes.append(path)
                continue
            
            # Pruning: don't explore if we've exceeded transfer limit or distance
            if transfers > num_transfers or total_dist > max_distance:
                continue
            
            # Optimization: skip if we've visited this station with fewer transfers
            if curr_id in visited and visited[curr_id] <= transfers:
                continue
            visited[curr_id] = transfers
            
            # Get edges and limit branching
            edges = self.router.graph[curr_id]
            if len(edges) > 150:  # Slightly higher branching for comprehensive search
                edges = sorted(edges, key=lambda e: e['distance'])[:150]
            
            for edge in edges:
                # Calculate transfer details
                is_transfer = len(path) > 0
                wait_time = 0
                
                if is_transfer:
                    wait_time = self.router._calculate_wait_time(
                        path[-1]['arrival'], 
                        edge['departure_time']
                    )
                    # Realistic transfer window: 30 min to 12 hours
                    if wait_time < 0.5 or wait_time > 12:
                        continue
                
                # Calculate new transfer count
                new_transfers = transfers + (1 if is_transfer else 0)
                
                # Skip if exceeds desired transfer count
                if new_transfers > num_transfers:
                    continue
                
                # Create segment
                segment = {
                    'train_no': edge['train_no'],
                    'from': self.router.id_to_station[curr_id],
                    'to': self.router.id_to_station[edge['to_id']],
                    'departure': edge['departure_time'],
                    'arrival': edge['arrival_time'],
                    'distance': edge['distance'],
                    'duration': edge['duration_minutes'] / 60,
                    'wait_before': wait_time,
                    'live_fare': max(200, edge['distance'] * 5),
                }
                
                # Add to queue
                new_path = path + [segment]
                new_dist = total_dist + edge['distance']
                
                queue.append((
                    edge['to_id'],
                    new_path,
                    new_transfers,
                    new_dist
                ))
        
        logger.info(f"      Found {len(routes)} routes with {num_transfers} transfer(s)")
        return routes
    
    def analyze_multi_transfer_routes(self, routes_data: Dict) -> Dict:
        """
        Analyze the generated multi-transfer routes
        Calculate statistics and metrics
        """
        
        logger.info(f"\n{'='*80}")
        logger.info(f"ROUTE ANALYSIS")
        logger.info(f"{'='*80}")
        
        analysis = {
            'transfer_type_breakdown': {},
            'statistics': {},
            'sample_routes': {},
        }
        
        total_routes = 0
        
        for transfer_count, routes in routes_data['routes_by_transfer_count'].items():
            if routes:
                total_routes += len(routes)
                
                # Calculate statistics
                durations = []
                distances = []
                costs = []
                
                for route in routes:
                    duration = sum(seg['duration'] + seg['wait_before'] for seg in route)
                    distance = sum(seg['distance'] for seg in route)
                    cost = sum(seg['live_fare'] for seg in route)
                    
                    durations.append(duration)
                    distances.append(distance)
                    costs.append(cost)
                
                analysis['transfer_type_breakdown'][transfer_count] = {
                    'count': len(routes),
                    'percentage': 0,  # Will update after calculating total
                    'avg_duration_hours': sum(durations) / len(durations) if durations else 0,
                    'avg_distance_km': sum(distances) / len(distances) if distances else 0,
                    'avg_cost': sum(costs) / len(costs) if costs else 0,
                    'min_duration_hours': min(durations) if durations else 0,
                    'max_duration_hours': max(durations) if durations else 0,
                    'min_distance_km': min(distances) if distances else 0,
                    'max_distance_km': max(distances) if distances else 0,
                    'min_cost': min(costs) if costs else 0,
                    'max_cost': max(costs) if costs else 0,
                }
                
                # Store sample routes (first 3)
                analysis['sample_routes'][transfer_count] = []
                for i, route in enumerate(routes[:3]):
                    sample_route = {
                        'index': i + 1,
                        'segments': len(route),
                        'total_duration': sum(seg['duration'] + seg['wait_before'] for seg in route),
                        'total_distance': sum(seg['distance'] for seg in route),
                        'total_cost': sum(seg['live_fare'] for seg in route),
                        'segments_list': [
                            {
                                'train': seg['train_no'],
                                'from': seg['from'],
                                'to': seg['to'],
                                'distance_km': seg['distance'],
                                'duration_hours': seg['duration'],
                                'wait_before_hours': seg['wait_before'],
                            }
                            for seg in route
                        ]
                    }
                    analysis['sample_routes'][transfer_count].append(sample_route)
        
        # Update percentages
        if total_routes > 0:
            for tc in analysis['transfer_type_breakdown']:
                analysis['transfer_type_breakdown'][tc]['percentage'] = (
                    analysis['transfer_type_breakdown'][tc]['count'] / total_routes * 100
                )
        
        analysis['statistics']['total_routes'] = total_routes
        analysis['statistics']['generation_time'] = routes_data['summary'].get('generation_time_seconds', 0)
        
        # Log analysis
        logger.info(f"\nRoute Distribution:")
        for tc, stats in analysis['transfer_type_breakdown'].items():
            logger.info(f"  {tc} Transfer(s): {stats['count']} routes ({stats['percentage']:.1f}%)")
            if stats['count'] > 0:
                logger.info(f"    Avg Duration: {stats['avg_duration_hours']:.2f}h (min: {stats['min_duration_hours']:.2f}h, max: {stats['max_duration_hours']:.2f}h)")
                logger.info(f"    Avg Distance: {stats['avg_distance_km']:.0f}km (min: {stats['min_distance_km']:.0f}km, max: {stats['max_distance_km']:.0f}km)")
                logger.info(f"    Avg Cost: ₹{stats['avg_cost']:.0f} (min: ₹{stats['min_cost']:.0f}, max: ₹{stats['max_cost']:.0f})")
        
        return analysis
    
    def save_results(self, routes_data: Dict, analysis: Dict, output_file: str = None) -> str:
        """Save routes and analysis to JSON file"""
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            source = routes_data['metadata']['source']
            dest = routes_data['metadata']['destination']
            output_file = f"multi_transfer_routes_{source}_{dest}_{timestamp}.json"
        
        # Prepare data for JSON serialization
        json_data = {
            'metadata': routes_data['metadata'],
            'summary': routes_data['summary'],
            'routes_by_transfer_count': {},
            'analysis': analysis,
        }
        
        # Add route counts only (full routes are very large)
        for tc, routes in routes_data['routes_by_transfer_count'].items():
            json_data['routes_by_transfer_count'][tc] = {
                'total_count': len(routes),
                'sample_routes': []
            }
            
            # Add first 5 routes as samples
            for i, route in enumerate(routes[:5]):
                sample = {
                    'index': i + 1,
                    'segments': len(route),
                    'segments_detail': [
                        {
                            'train': seg['train_no'],
                            'from': seg['from'],
                            'to': seg['to'],
                            'distance': seg['distance'],
                            'duration_hours': seg['duration'],
                            'wait_before_hours': seg['wait_before'],
                        }
                        for seg in route
                    ]
                }
                json_data['routes_by_transfer_count'][tc]['sample_routes'].append(sample)
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        logger.info(f"\n✓ Results saved to: {output_file}")
        return output_file


def main():
    """Test the advanced multi-transfer router"""
    
    logger.info("\n" + "="*80)
    logger.info("ADVANCED MULTI-TRANSFER ROUTE GENERATION TEST")
    logger.info("="*80)
    
    # Initialize router
    db = DatabaseManager()
    advanced_router = AdvancedMultiTransferRouter(db)
    
    # Generate routes with up to 4 transfers
    routes = advanced_router.generate_all_transfer_routes(
        source="CSMT",
        destination="DADA",
        max_transfers=4,
        max_routes_per_type=100
    )
    
    # Analyze routes
    analysis = advanced_router.analyze_multi_transfer_routes(routes)
    
    # Save results
    advanced_router.save_results(routes, analysis)
    
    logger.info("\n" + "="*80)
    logger.info("TEST COMPLETE")
    logger.info("="*80)


if __name__ == "__main__":
    main()
