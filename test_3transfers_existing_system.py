#!/usr/bin/env python3
"""
Test: Route Generation with Up to 3 Transfers

Tests the existing ParetoTrainRouter system with any two stations
from the database to verify 3-transfer route generation.
"""

import sys
from pathlib import Path
import sqlite3
import time
import random
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from route_optimizer import ParetoTrainRouter, GraphSingleton
from database_manager import get_db

def get_test_stations(num_pairs=3):
    """Get station pairs from trains that actually connect them"""
    try:
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()
        
        # Get trains with multiple stations (these are guaranteed to connect)
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
        
        pairs = []
        for train_no, stations_str in cursor.fetchall():
            station_list = stations_str.split('|')
            if len(station_list) >= 2:
                # Convert to codes: UPPER + remove spaces + limit to 10 chars
                # This matches what route_optimizer.py does
                def to_code(name):
                    return name.upper().replace(" ", "")[:10]
                
                # Start to end
                pairs.append((to_code(station_list[0]), to_code(station_list[-1])))
                # Start to middle
                if len(station_list) >= 4:
                    pairs.append((to_code(station_list[0]), to_code(station_list[len(station_list)//2])))
                # Different segment
                if len(station_list) >= 6:
                    pairs.append((to_code(station_list[len(station_list)//3]), to_code(station_list[-1])))
        
        conn.close()
        return pairs[:num_pairs]
    except Exception as e:
        print(f"Error getting stations: {e}")
        return []

def test_route_generation():
    """Test route generation with 3 transfers"""
    
    print("\n" + "="*80)
    print("TESTING ROUTE GENERATION (UP TO 3 TRANSFERS)")
    print("="*80)
    print(f"Timestamp: {datetime.now()}")
    
    try:
        # Initialize database
        print("\n1️⃣  INITIALIZING SYSTEM...")
        db = get_db()
        router = ParetoTrainRouter(db)
        print("✅ ParetoTrainRouter initialized")
        
        # Get test station pairs
        print("\n2️⃣  GETTING TEST STATION PAIRS FROM DATABASE...")
        station_pairs = get_test_stations(num_pairs=3)
        
        if not station_pairs:
            print("❌ No station pairs found")
            return
        
        print(f"✅ Found {len(station_pairs)} station pairs:")
        for i, (start, end) in enumerate(station_pairs, 1):
            print(f"   {i}. {start} → {end}")
        
        # Test each pair
        print("\n3️⃣  TESTING ROUTE GENERATION (MAX 3 TRANSFERS)...")
        print()
        
        all_results = []
        
        for start, end in station_pairs:
            print(f"\n{'='*80}")
            print(f"Testing: {start} → {end}")
            print(f"{'='*80}")
            
            test_start = time.time()
            
            try:
                # Call the existing find_routes method from ParetoTrainRouter
                routes = router.find_routes(
                    origin=start,
                    destination=end,
                    max_transfers=3,
                    travel_date=datetime.now()
                )
                
                search_time = time.time() - test_start
                
                if not routes:
                    print(f"  ℹ️  No routes found")
                    result = {
                        'pair': f"{start} → {end}",
                        'status': 'NO_ROUTES',
                        'search_time_ms': round(search_time * 1000, 2)
                    }
                else:
                    # Count routes by transfers
                    transfers_count = {}
                    for route in routes:
                        transfers = len(route) - 1
                        if transfers not in transfers_count:
                            transfers_count[transfers] = 0
                        transfers_count[transfers] += 1
                    
                    total_routes = len(routes)
                    
                    print(f"  ✅ Found {total_routes} routes in {search_time*1000:.2f}ms")
                    print(f"\n  Routes by transfers:")
                    
                    for transfers in sorted(transfers_count.keys()):
                        count = transfers_count[transfers]
                        print(f"    - {transfers} transfer(s): {count} routes")
                        
                        # Show first route as example
                        example_routes = [r for r in routes if len(r) - 1 == transfers]
                        if example_routes:
                            example = example_routes[0]
                            path_str = " → ".join([seg['from'] if isinstance(seg, dict) else str(seg) for seg in example[:min(3, len(example))]])
                            if len(example) > 3:
                                path_str += f" → ... ({len(example)} segments total)"
                            print(f"      Example: {path_str}")
                    
                    result = {
                        'pair': f"{start} → {end}",
                        'status': 'SUCCESS',
                        'total_routes': total_routes,
                        'routes_by_transfers': transfers_count,
                        'search_time_ms': round(search_time * 1000, 2)
                    }
                
                all_results.append(result)
                
            except Exception as e:
                import traceback
                print(f"  ❌ Error: {e}")
                print("\n  Full Traceback:")
                traceback.print_exc()
                result = {
                    'pair': f"{start} → {end}",
                    'status': 'ERROR',
                    'error': str(e),
                    'search_time_ms': round((time.time() - test_start) * 1000, 2)
                }
                all_results.append(result)
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        
        successful = sum(1 for r in all_results if r['status'] == 'SUCCESS')
        total = len(all_results)
        
        print(f"\nTest Pairs: {total}")
        print(f"Successful: {successful}")
        print(f"Success Rate: {100*successful/total if total > 0 else 0:.1f}%")
        
        if all_results:
            avg_time = sum(r['search_time_ms'] for r in all_results) / len(all_results)
            max_time = max(r['search_time_ms'] for r in all_results)
            min_time = min(r['search_time_ms'] for r in all_results)
            
            print(f"\nPerformance Metrics:")
            print(f"  Avg Search Time: {avg_time:.2f}ms")
            print(f"  Min Search Time: {min_time:.2f}ms")
            print(f"  Max Search Time: {max_time:.2f}ms")
        
        total_routes_found = sum(r.get('total_routes', 0) for r in all_results)
        print(f"\nTotal Routes Found: {total_routes_found}")
        
        print("\n✅ Testing Complete")
        print("="*80 + "\n")
        
        return all_results
        
    except Exception as e:
        print(f"\n❌ System Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    results = test_route_generation()
