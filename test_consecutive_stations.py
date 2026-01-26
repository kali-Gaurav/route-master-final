#!/usr/bin/env python3
"""
Test: SimpleBFSRouteGenerator with consecutive stations
Find pairs that are actually consecutive in trains
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
    print("SIMPLE BFS ROUTE GENERATOR TEST - CONSECUTIVE STATIONS")
    print("="*80)
    print(f"Start: {datetime.now()}\n")
    
    # Step 1: Initialize
    print("STEP 1: Initializing system...")
    init_start = time.time()
    db = get_db()
    generator = SimpleBFSRouteGenerator(db)
    init_time = time.time() - init_start
    print(f"✅ System ready in {init_time*1000:.2f}ms\n")
    
    # Step 2: Get test pairs - stations that are CONSECUTIVE in trains
    print("STEP 2: Finding consecutive station pairs from database...")
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        WITH consecutive_pairs AS (
            SELECT 
                train_no,
                station_name as from_station,
                LEAD(station_name) OVER (PARTITION BY train_no ORDER BY station_sequence) as to_station,
                station_sequence
            FROM rappid_routes
        )
        SELECT DISTINCT from_station, to_station
        FROM consecutive_pairs
        WHERE to_station IS NOT NULL
        LIMIT 10
    """)
    
    test_pairs = []
    for from_station, to_station in cursor.fetchall():
        def to_code(name):
            return name.upper().replace(" ", "")[:10]
        
        test_pairs.append({
            'start': to_code(from_station),
            'end': to_code(to_station),
            'start_name': from_station,
            'end_name': to_station
        })
    
    conn.close()
    test_pairs = test_pairs[:5]  # Take first 5
    
    print(f"✅ Got {len(test_pairs)} consecutive station pairs:")
    for i, pair in enumerate(test_pairs, 1):
        print(f"   {i}. {pair['start']} ({pair['start_name']}) → {pair['end']} ({pair['end_name']})")
    print()
    
    # Step 3: Find routes
    print("STEP 3: Finding routes using SimpleBFSRouteGenerator (0 transfers)...")
    print()
    
    total_routes = 0
    total_time = 0
    
    for i, pair in enumerate(test_pairs, 1):
        print(f"  [{i}] {pair['start']} → {pair['end']}")
        
        search_start = time.time()
        result = generator.find_routes(pair['start'], pair['end'], max_transfers=0)
        search_time = time.time() - search_start
        total_time += search_time
        
        if 'error' in result:
            print(f"      ❌ {result['error']}")
        else:
            routes_found = result['total_routes_found']
            total_routes += routes_found
            
            if routes_found == 0:
                print(f"      ℹ️  No direct routes found - {search_time*1000:.2f}ms")
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
    if test_pairs:
        print(f"Average per pair:   {(total_time/len(test_pairs))*1000:8.2f} ms")
    print(f"\nTotal routes found: {total_routes}")
    print()
    print("="*80)
    print("✅ TEST COMPLETE")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
