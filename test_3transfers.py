#!/usr/bin/env python3
"""
Performance Test: Graph Building & Route Generation (3 Transfers Max)

Tests graph building from database and generates routes with up to 3 transfers
for sample station pairs.
"""

import sqlite3
import time
import json
from collections import defaultdict, deque
from datetime import datetime

class RoutePerformanceTester:
    def __init__(self, db_path='production.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.graph = defaultdict(list)
        self.stations = set()
        
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
    
    def build_graph(self):
        """Build graph from database"""
        print("\n=== BUILDING GRAPH ===")
        start_time = time.time()
        
        # Get all trains with station sequences
        self.cursor.execute("""
            SELECT train_no, GROUP_CONCAT(station_name, '|') as stations
            FROM rappid_routes
            GROUP BY train_no
        """)
        
        trains = self.cursor.fetchall()
        print(f"Processing {len(trains)} trains...")
        
        edges = 0
        for train_no, stations_str in trains:
            station_list = stations_str.split('|') if stations_str else []
            
            # Build edges
            for i in range(len(station_list) - 1):
                start = station_list[i]
                end = station_list[i + 1]
                self.stations.add(start)
                self.stations.add(end)
                self.graph[start].append({'to': end, 'train': train_no})
                edges += 1
        
        build_time = time.time() - start_time
        print(f"✅ Graph built in {build_time:.4f}s")
        print(f"   Stations: {len(self.stations)}, Edges: {edges}")
        return build_time
    
    def get_sample_pairs(self):
        """Get sample station pairs"""
        self.cursor.execute("""
            WITH pairs AS (
                SELECT DISTINCT 
                    (SELECT MIN(station_name) FROM rappid_routes r2 WHERE r2.train_no = r.train_no) as start_station,
                    (SELECT MAX(station_name) FROM rappid_routes r3 WHERE r3.train_no = r.train_no) as end_station
                FROM rappid_routes r
                LIMIT 5
            )
            SELECT DISTINCT start_station, end_station FROM pairs 
            WHERE start_station IS NOT NULL AND end_station IS NOT NULL LIMIT 3
        """)
        
        pairs = self.cursor.fetchall()
        print(f"\n📍 Testing routes for {len(pairs)} station pairs:")
        for i, (start, end) in enumerate(pairs, 1):
            print(f"   {i}. {start} → {end}")
        return pairs
    
    def find_routes_with_transfers(self, start, end, max_transfers=3):
        """Find routes with transfers using BFS"""
        print(f"\n🔍 Searching {start} → {end} (max {max_transfers} transfers)...")
        search_start = time.time()
        
        queue = deque([(start, [start], 0)])
        found_routes = []
        visited = set()
        
        while queue:
            current, path, transfers = queue.popleft()
            
            if transfers > max_transfers or len(path) > 15:
                continue
            
            state = (current, len(path))
            if state in visited:
                continue
            visited.add(state)
            
            # Check if reached destination
            if current == end and len(path) > 1:
                found_routes.append({
                    'path': path.copy(),
                    'transfers': transfers,
                    'hops': len(path) - 1
                })
                continue
            
            # Explore neighbors
            if current in self.graph:
                for edge in self.graph[current]:
                    next_st = edge['to']
                    if next_st not in path[-3:]:
                        new_transfers = transfers + 1 if len(path) > 1 else 0
                        if new_transfers <= max_transfers:
                            queue.append((next_st, path + [next_st], new_transfers))
        
        search_time = time.time() - search_start
        
        # Group by transfers
        by_transfers = defaultdict(list)
        for route in found_routes:
            by_transfers[route['transfers']].append(route)
        
        print(f"   ✅ Found {len(found_routes)} routes in {search_time:.4f}s")
        for transfers in sorted(by_transfers.keys()):
            print(f"      {transfers} transfer(s): {len(by_transfers[transfers])} routes")
            # Show first route as example
            if by_transfers[transfers]:
                sample = by_transfers[transfers][0]
                route_str = " → ".join(sample['path'][:min(5, len(sample['path']))])
                if len(sample['path']) > 5:
                    route_str += f" → ... → {sample['path'][-1]}"
                print(f"         Example: {route_str}")
        
        return found_routes, search_time
    
    def run_test(self):
        """Run complete test"""
        print("="*70)
        print("RAPPID GRAPH BUILDING & ROUTE GENERATION TEST (3 TRANSFERS MAX)")
        print("="*70)
        print(f"Start: {datetime.now()}")
        
        if not self.connect():
            return
        
        # Build graph
        build_time = self.build_graph()
        
        # Get sample pairs
        pairs = self.get_sample_pairs()
        
        # Test route generation
        all_results = []
        total_search_time = 0
        total_routes = 0
        
        for start, end in pairs:
            routes, search_time = self.find_routes_with_transfers(start, end, max_transfers=3)
            total_search_time += search_time
            total_routes += len(routes)
            all_results.append({
                'start': start,
                'end': end,
                'routes_found': len(routes),
                'search_time': search_time
            })
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Graph build time: {build_time:.4f}s")
        print(f"Total routes found: {total_routes}")
        print(f"Total search time: {total_search_time:.4f}s")
        print(f"Avg search time per pair: {total_search_time / len(pairs):.4f}s")
        print(f"\n✅ Test complete at {datetime.now()}")
        
        return all_results


if __name__ == '__main__':
    tester = RoutePerformanceTester()
    results = tester.run_test()
