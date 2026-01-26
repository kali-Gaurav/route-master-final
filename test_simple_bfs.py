#!/usr/bin/env python3
"""
Test: Simple BFS Route Generator (Fast)
Tests the new SimpleBFSRouteGenerator with 2 random stations
"""

import sys
from pathlib import Path
import sqlite3
import time
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from route_optimizer import SimpleBFSRouteGenerator
from database_manager import get_db

def main():
    print("\n" + "="*80)
    print("SIMPLE BFS ROUTE GENERATOR TEST (3 TRANSFERS MAX)")
    print("="*80)
    print(f"Start: {datetime.now()}\n")
    
    # Step 1: Initialize
    print("STEP 1: Initializing system...")
    init_start = time.time()
    db = get_db()
    generator = SimpleBFSRouteGenerator(db)
    init_time = time.time() - init_start
    print(f"✅ System ready in {init_time*1000:.2f}ms\n")
    
    # Step 2: Get test pairs
    print("STEP 2: Getting test station pairs...")
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        WITH train_stations AS (
            SELECT train_no, GROUP_CONCAT(station_name, '|') as stations
            FROM rappid_routes
            GROUP BY train_no
            HAVING COUNT(*) >= 3
            ORDER BY COUNT(*) DESC
            LIMIT 20
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
    
    # Step 3: Find routes
    print("STEP 3: Finding routes using SimpleBFSRouteGenerator...")
    print()
    
    total_routes = 0
    total_time = 0
    
    for i, pair in enumerate(test_pairs, 1):
        print(f"  [{i}] {pair['start']} → {pair['end']}")
        
        search_start = time.time()
        result = generator.find_routes(pair['start'], pair['end'], max_transfers=3)
        search_time = time.time() - search_start
        total_time += search_time
        
        if 'error' in result:
            print(f"      ❌ {result['error']}")
        else:
            routes_found = result['total_routes_found']
            total_routes += routes_found
            
            if routes_found == 0:
                print(f"      ℹ️  No routes found - {search_time*1000:.2f}ms")
            else:
                print(f"      ✅ {routes_found} routes in {search_time*1000:.2f}ms")
                
                for transfers in sorted(result['routes_by_transfers'].keys()):
                    count = len(result['routes_by_transfers'][transfers])
                    print(f"         - {transfers} transfer(s): {count} routes")
        print()
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\nSystem Init:        {init_time*1000:8.2f} ms")
    print(f"Route Searches:     {total_time*1000:8.2f} ms total")
    print(f"Average per pair:   {(total_time/len(test_pairs))*1000:8.2f} ms")
    print(f"\nTotal routes found: {total_routes}")
    print()
    print("="*80)
    print("✅ TEST COMPLETE")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
