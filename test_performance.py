#!/usr/bin/env python3
"""
Performance Testing Script for RAPPID Graph Building and Route Generation

Tests:
1. Graph building from database (timing and metrics)
2. Route generation for any 2 stations
3. Multi-transfer route generation (up to 4 transfers)
4. Performance metrics and bottleneck analysis
"""

import sqlite3
import time
import json
from collections import defaultdict, deque
from datetime import datetime
from typing import List, Dict, Tuple, Set
import traceback

class DatabaseGraphPerformanceTester:
    def __init__(self, db_path='production.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.graph = defaultdict(list)
        self.stations = set()
        self.routes_cache = {}
        self.test_results = {
            'database_check': {},
            'graph_building': {},
            'route_generation': {},
            'transfer_routes': {},
            'performance_summary': {}
        }
        
    def connect(self):
        """Connect to SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            print("✅ Connected to database")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def check_database_structure(self):
        """Check if required tables exist and have data"""
        print("\n=== DATABASE STRUCTURE CHECK ===")
        
        try:
            # Get all tables
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in self.cursor.fetchall()]
            
            print(f"Total tables: {len(tables)}")
            for table in sorted(tables):
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = self.cursor.fetchone()[0]
                print(f"  {table}: {count} rows")
                
                if table == 'rappid_routes':
                    # Check schema
                    self.cursor.execute("PRAGMA table_info(rappid_routes)")
                    columns = [col[1] for col in self.cursor.fetchall()]
                    print(f"    Columns: {', '.join(columns[:5])}...")
                    
                    # Count unique trains and stations
                    self.cursor.execute("SELECT COUNT(DISTINCT train_no) FROM rappid_routes")
                    trains = self.cursor.fetchone()[0]
                    
                    self.cursor.execute("SELECT COUNT(DISTINCT station_name) FROM rappid_routes")
                    stations = self.cursor.fetchone()[0]
                    
                    print(f"    - Unique trains: {trains}")
                    print(f"    - Unique stations: {stations}")
            
            self.test_results['database_check']['tables'] = len(tables)
            self.test_results['database_check']['status'] = 'OK'
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            self.test_results['database_check']['error'] = str(e)
            return False
    
    def get_sample_stations(self):
        """Get sample stations for testing"""
        try:
            # Get unique stations that have both arrivals and departures
            self.cursor.execute("""
                WITH station_pairs AS (
                    SELECT DISTINCT 
                        (SELECT MIN(station_name) FROM rappid_routes r2 
                         WHERE r2.train_no = r.train_no) as start_station,
                        (SELECT MAX(station_name) FROM rappid_routes r3 
                         WHERE r3.train_no = r.train_no) as end_station
                    FROM rappid_routes r
                    LIMIT 10
                )
                SELECT DISTINCT start_station, end_station 
                FROM station_pairs 
                WHERE start_station IS NOT NULL AND end_station IS NOT NULL
                LIMIT 5
            """)
            
            samples = self.cursor.fetchall()
            print(f"\n📍 Sample station pairs (first 5):")
            for i, (start, end) in enumerate(samples, 1):
                print(f"  {i}. {start} → {end}")
            
            return samples
        except Exception as e:
            print(f"❌ Error getting samples: {e}")
            traceback.print_exc()
            return []
    
    def build_graph_from_database(self) -> Dict:
        """Build graph from database and measure performance"""
        print("\n=== GRAPH BUILDING FROM DATABASE ===")
        
        start_time = time.time()
        graph = defaultdict(list)
        stations = set()
        trains_loaded = 0
        station_edges = 0
        
        try:
            # Get all trains with their station sequences
            self.cursor.execute("""
                SELECT train_no, GROUP_CONCAT(station_name, '|') as stations,
                       GROUP_CONCAT(timing, '|') as timings,
                       GROUP_CONCAT(station_sequence, '|') as sequences
                FROM rappid_routes
                GROUP BY train_no
                ORDER BY train_no
            """)
            
            trains = self.cursor.fetchall()
            trains_loaded = len(trains)
            
            print(f"Loading {trains_loaded} trains with stations...")
            
            for train_no, stations_str, timings_str, sequences_str in trains:
                try:
                    station_list = stations_str.split('|') if stations_str else []
                    timing_list = timings_str.split('|') if timings_str else []
                    
                    if len(station_list) < 2:
                        continue
                    
                    # Build edges for each consecutive station pair
                    for i in range(len(station_list) - 1):
                        start = station_list[i]
                        end = station_list[i + 1]
                        
                        stations.add(start)
                        stations.add(end)
                        
                        graph[start].append({
                            'to': end,
                            'train': train_no,
                            'departure': timing_list[i] if i < len(timing_list) else None,
                            'arrival': timing_list[i+1] if i+1 < len(timing_list) else None,
                        })
                        station_edges += 1
                        
                except Exception as e:
                    continue
            
            build_time = time.time() - start_time
            
            # Store results
            self.graph = graph
            self.stations = stations
            
            stats = {
                'trains_loaded': trains_loaded,
                'total_stations': len(stations),
                'total_edges': station_edges,
                'build_time_seconds': round(build_time, 4),
                'avg_edges_per_station': round(station_edges / len(stations), 2) if stations else 0
            }
            
            print(f"\n✅ Graph built successfully:")
            print(f"  Trains loaded: {stats['trains_loaded']}")
            print(f"  Total stations: {stats['total_stations']}")
            print(f"  Total edges: {stats['total_edges']}")
            print(f"  Build time: {stats['build_time_seconds']}s")
            print(f"  Avg edges/station: {stats['avg_edges_per_station']}")
            
            self.test_results['graph_building'] = stats
            return stats
            
        except Exception as e:
            print(f"❌ Error building graph: {e}")
            traceback.print_exc()
            self.test_results['graph_building']['error'] = str(e)
            return {'error': str(e)}
    
    def find_direct_routes(self, start: str, end: str) -> List[Dict]:
        """Find direct routes between two stations"""
        try:
            self.cursor.execute("""
                SELECT train_no, GROUP_CONCAT(station_name, '|') as stations,
                       GROUP_CONCAT(timing, '|') as timings
                FROM rappid_routes
                WHERE train_no IN (
                    SELECT DISTINCT train_no FROM rappid_routes 
                    WHERE station_name = ?
                )
                AND train_no IN (
                    SELECT DISTINCT train_no FROM rappid_routes 
                    WHERE station_name = ?
                )
                GROUP BY train_no
            """, (start, end))
            
            routes = []
            for row in self.cursor.fetchall():
                try:
                    train_num, stations_str, timings_str = row
                    station_list = stations_str.split('|') if stations_str else []
                    timing_list = timings_str.split('|') if timings_str else []
                    
                    # Check if this train goes from start to end
                    try:
                        start_idx = station_list.index(start)
                        end_idx = station_list.index(end)
                        if start_idx < end_idx:
                            routes.append({
                                'train': train_num,
                                'path': station_list,
                                'timings': timing_list,
                                'stations_count': len(station_list),
                                'type': 'direct',
                                'segment': f"{start}({start_idx}) → {end}({end_idx})"
                            })
                    except ValueError:
                        continue
                except:
                    continue
            
            return routes
        except Exception as e:
            print(f"Error finding direct routes: {e}")
            return []
    
    def find_transfer_routes(self, start: str, end: str, max_transfers: int = 4) -> Dict:
        """Find routes with transfers using BFS"""
        print(f"\n🔍 Finding routes from {start} to {end} (max {max_transfers} transfers)...")
        
        start_time = time.time()
        all_routes = []
        
        try:
            # BFS to find paths
            queue = deque([(start, [start], 0, 0)])  # (current, path, transfers, time)
            visited_states = set()
            
            while queue:
                current, path, transfers, current_time = queue.popleft()
                
                # Limit search
                if transfers > max_transfers or len(path) > 20:
                    continue
                
                # Check if we reached destination
                if current == end and len(path) > 1:
                    all_routes.append({
                        'path': path.copy(),
                        'transfers': transfers,
                        'hops': len(path) - 1
                    })
                    continue
                
                # Avoid infinite loops
                state = (current, tuple(path))
                if state in visited_states:
                    continue
                visited_states.add(state)
                
                # Find next stations
                if current in self.graph:
                    for edge in self.graph[current]:
                        next_station = edge['to']
                        if next_station not in path[-3:]:  # Avoid immediate loops
                            new_transfers = transfers + (1 if edge.get('is_transfer') else 0)
                            if new_transfers <= max_transfers:
                                queue.append((next_station, path + [next_station], new_transfers, current_time))
            
            search_time = time.time() - start_time
            
            # Group routes by number of transfers
            routes_by_transfers = defaultdict(list)
            for route in all_routes:
                routes_by_transfers[route['transfers']].append(route)
            
            result = {
                'start': start,
                'end': end,
                'search_time_seconds': round(search_time, 4),
                'total_routes_found': len(all_routes),
                'routes_by_transfers': {
                    transfers: len(routes) for transfers, routes in routes_by_transfers.items()
                },
                'sample_routes': {
                    transfers: routes[:2] for transfers, routes in routes_by_transfers.items()
                }
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Error: {e}")
            traceback.print_exc()
            return {'error': str(e)}
    
    def test_multiple_routes(self):
        """Test route generation for multiple station pairs"""
        print("\n=== ROUTE GENERATION TEST (MULTIPLE STATION PAIRS) ===")
        
        samples = self.get_sample_stations()
        if not samples:
            print("❌ No sample stations found")
            return
        
        results = []
        for start, end in samples[:3]:  # Test first 3 pairs
            start_time = time.time()
            
            # Direct routes
            direct = self.find_direct_routes(start, end)
            
            # Transfer routes
            transfer_result = self.find_transfer_routes(start, end, max_transfers=4)
            
            test_time = time.time() - start_time
            
            result = {
                'pair': f"{start} → {end}",
                'direct_routes': len(direct),
                'total_transfer_routes': transfer_result.get('total_routes_found', 0),
                'routes_by_transfers': transfer_result.get('routes_by_transfers', {}),
                'search_time': round(test_time, 4),
            }
            
            print(f"\n  📍 {start} → {end}")
            print(f"    Direct routes: {result['direct_routes']}")
            print(f"    Transfer routes: {result['total_transfer_routes']}")
            if result.get('routes_by_transfers'):
                for transfers, count in sorted(result['routes_by_transfers'].items()):
                    print(f"      {transfers} transfers: {count} routes")
            print(f"    Search time: {result['search_time']}s")
            
            results.append(result)
        
        self.test_results['route_generation'] = results
    
    def run_all_tests(self):
        """Run complete performance test suite"""
        print("\n" + "="*60)
        print("RAPPID GRAPH BUILDING & ROUTE GENERATION PERFORMANCE TEST")
        print("="*60)
        print(f"Timestamp: {datetime.now()}")
        print(f"Database: {self.db_path}")
        
        # 1. Check database
        if not self.connect():
            return
        
        self.check_database_structure()
        
        # 2. Build graph
        self.build_graph_from_database()
        
        # 3. Test route generation
        self.test_multiple_routes()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        if self.test_results['graph_building']:
            gb = self.test_results['graph_building']
            print("\n📊 Graph Building:")
            if 'error' not in gb:
                print(f"  ✅ Routes loaded: {gb.get('routes_loaded', 'N/A')}")
                print(f"  ✅ Stations: {gb.get('total_stations', 'N/A')}")
                print(f"  ✅ Edges: {gb.get('total_edges', 'N/A')}")
                print(f"  ✅ Build time: {gb.get('build_time_seconds', 'N/A')}s")
            else:
                print(f"  ❌ Error: {gb['error']}")
        
        if self.test_results['route_generation']:
            print(f"\n📊 Route Generation (tested {len(self.test_results['route_generation'])} pairs):")
            for result in self.test_results['route_generation']:
                print(f"\n  {result['pair']}")
                print(f"    Direct: {result['direct_routes']}")
                print(f"    With transfers: {result['total_transfer_routes']}")
                print(f"    Time: {result['search_time']}s")
        
        print("\n" + "="*60)
        print("✅ Testing complete\n")
        
        return self.test_results


if __name__ == '__main__':
    tester = DatabaseGraphPerformanceTester()
    results = tester.run_all_tests()
    
    # Save results to file
    with open('performance_test_results.json', 'w') as f:
        # Convert sets to lists for JSON serialization
        import json
        json.dump(results, f, indent=2, default=str)
    
    print("Results saved to: performance_test_results.json")
