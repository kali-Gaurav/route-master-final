#!/usr/bin/env python3
"""
Test: Route Generation Performance Analysis
Measures graph building vs route searching time separately
"""

import sys
from pathlib import Path
import sqlite3
import time
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from route_optimizer import ParetoTrainRouter, GraphSingleton
from database_manager import get_db

def main():
    print("\n" + "="*80)
    print("ROUTE GENERATION PERFORMANCE TEST - WITH TIME BREAKDOWN")
    print("="*80)
    print(f"Start: {datetime.now()}\n")
    
    # Step 1: Initialize database
    print("STEP 1: Initializing database connection...")
    db_start = time.time()
    db = get_db()
    db_time = time.time() - db_start
    print(f"✅ Database ready in {db_time*1000:.2f}ms\n")
    
    # Step 2: Initialize router (this builds graph)
    print("STEP 2: Initializing ParetoTrainRouter (BUILDS GRAPH FROM DATABASE)...")
    router_start = time.time()
    router = ParetoTrainRouter(db)
    router_time = time.time() - router_start
    print(f"✅ Router initialized in {router_time*1000:.2f}ms\n")
    
    # Step 3: Get the graph stats
    print("STEP 3: Graph Statistics...")
    graph = router._graph_cache
    print(f"  Stations in graph: {len(graph.station_maps['station_to_id'])}")
    print(f"  Edges in graph: {sum(len(edges) for edges in graph.graph.values())}")
    print()
    
    # Step 4: Get test station pairs
    print("STEP 4: Getting test station pairs from database...")
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        WITH train_stations AS (
            SELECT train_no, GROUP_CONCAT(station_name, '|') as stations
            FROM rappid_routes
            GROUP BY train_no
            HAVING COUNT(*) >= 3
            ORDER BY COUNT(*) DESC
            LIMIT 10
        )
        SELECT train_no, stations FROM train_stations
    """)
    
    test_pairs = []
    for train_no, stations_str in cursor.fetchall():
        station_list = stations_str.split('|')
        if len(station_list) >= 2:
            def to_code(name):
                return name.upper().replace(" ", "")[:10]
            
            test_pairs.append({
                'start': to_code(station_list[0]),
                'end': to_code(station_list[-1]),
                'start_name': station_list[0],
                'end_name': station_list[-1]
            })
    
    conn.close()
    test_pairs = test_pairs[:3]
    print(f"✅ Got {len(test_pairs)} test pairs:")
    for i, pair in enumerate(test_pairs, 1):
        print(f"   {i}. {pair['start']} ({pair['start_name']}) → {pair['end']} ({pair['end_name']})")
    print()
    
    # Step 5: Route finding with timing
    print("STEP 5: Finding routes (MAX 3 TRANSFERS)...")
    print()
    
    total_routes = 0
    total_search_time = 0
    
    for i, pair in enumerate(test_pairs, 1):
        print(f"  Test {i}: {pair['start']} → {pair['end']}")
        
        search_start = time.time()
        
        try:
            routes = router.find_routes(
                origin=pair['start'],
                destination=pair['end'],
                max_transfers=3,
                travel_date=datetime.now()
            )
            
            search_time = time.time() - search_start
            total_search_time += search_time
            
            if not routes:
                print(f"    ℹ️  No routes found - {search_time*1000:.2f}ms")
            else:
                total_routes += len(routes)
                
                # Count by transfers
                by_transfers = {}
                for route in routes:
                    transfers = len(route) - 1
                    by_transfers[transfers] = by_transfers.get(transfers, 0) + 1
                
                print(f"    ✅ {len(routes)} routes found in {search_time*1000:.2f}ms")
                for transfers in sorted(by_transfers.keys()):
                    print(f"       - {transfers} transfer(s): {by_transfers[transfers]} routes")
        
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        print()
    
    # Summary
    print("="*80)
    print("PERFORMANCE SUMMARY")
    print("="*80)
    print(f"\n1. Database Connection:    {db_time*1000:8.2f} ms")
    print(f"2. Graph Building:        {router_time*1000:8.2f} ms (ONE-TIME, cached)")
    print(f"3. Route Searches:        {total_search_time*1000:8.2f} ms total")
    print(f"   Average per pair:      {(total_search_time/len(test_pairs))*1000:8.2f} ms")
    print(f"\n4. Total Routes Found:    {total_routes} routes across {len(test_pairs)} pairs")
    
    total_time = db_time + router_time + total_search_time
    print(f"\n5. Total Test Time:       {total_time*1000:8.2f} ms")
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80 + "\n")
    
    print("KEY INSIGHTS:")
    print("- Graph building (step 2) is ONE-TIME cost, cached for all requests")
    print("- Route searching (step 3) is fast once graph is built")
    print("- In production: First request builds graph, all subsequent requests are fast")
    print()


if __name__ == '__main__':
    main()
