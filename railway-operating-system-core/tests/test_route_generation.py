#!/usr/bin/env python3
"""
Simple route generation test - generates routes from database
Tests core functionality of valid route generation
"""

import sys
import json
from datetime import datetime, timedelta
from route_finder import RouteFinder
from database import get_all_stations, get_database_stats

def main():
    print("=" * 70)
    print("RAILWAY ROUTE GENERATION TEST")
    print("=" * 70)
    
    # 1. Check database status
    print("\n1. CHECKING DATABASE STATUS...")
    stats = get_database_stats()
    print(f"   ✓ Total Stations: {stats.get('total_stations', 0)}")
    print(f"   ✓ Total Trains: {stats.get('total_trains', 0)}")
    print(f"   ✓ Total Routes: {stats.get('total_routes', 0)}")
    print(f"   ✓ Total Schedules: {stats.get('total_schedules', 0)}")
    print(f"   ✓ Train Types: {stats.get('train_types', {})}")
    
    if not stats.get('total_stations') or not stats.get('total_trains'):
        print("\n❌ ERROR: Database appears to be empty!")
        return False
    
    # 2. Get some major stations (Indian railway codes)
    print("\n2. SELECTING ROUTES TO TEST...")
    stations = get_all_stations()
    station_codes = [s[0] for s in stations]
    
    # Test routes between major stations
    test_routes = [
        ('NDLS', 'BCT'),      # Delhi to Mumbai
        ('NDLS', 'BBS'),      # Delhi to Bhubaneswar
        ('MAS', 'BCT'),       # Chennai to Mumbai
        ('HWH', 'NDLS'),      # Kolkata to Delhi
        ('SBC', 'BCT'),       # Bangalore to Mumbai
    ]
    
    # Filter to only routes that exist in database
    valid_routes = []
    for src, dst in test_routes:
        if src in station_codes and dst in station_codes:
            valid_routes.append((src, dst))
    
    if not valid_routes:
        print("   ⚠ Major stations not found, using first available...")
        valid_routes = [(station_codes[0], station_codes[1])]
    
    print(f"   Testing {len(valid_routes)} route(s):")
    for src, dst in valid_routes:
        print(f"     • {src} → {dst}")
    
    # 3. Generate routes
    print("\n3. GENERATING ROUTES FROM DATABASE...")
    finder = RouteFinder()
    
    results_summary = {
        'total_routes': 0,
        'direct_routes': 0,
        'transfer_routes': 0,
        'routes_by_transfers': {},
        'generated_at': datetime.now().isoformat()
    }
    
    for i, (source, destination) in enumerate(valid_routes, 1):
        print(f"\n   Route {i}: {source} → {destination}")
        
        try:
            # Find routes (None for any date)
            routes = finder.find_all_routes(
                source, 
                destination, 
                start_date=None,
                max_transfers=3,
                max_results=20,
                verbose=True
            )
            
            total = 0
            for transfer_level, route_list in routes.items():
                if isinstance(route_list, list):
                    count = len(route_list)
                    total += count
                    if count > 0:
                        print(f"      ✓ {transfer_level}: {count} route(s)")
                        if transfer_level == 'direct':
                            results_summary['direct_routes'] += count
                        else:
                            results_summary['transfer_routes'] += count
                        
                        results_summary['routes_by_transfers'][transfer_level] = count
            
            if total > 0:
                results_summary['total_routes'] += total
                print(f"      → TOTAL: {total} route(s) found")
            else:
                print(f"      ✗ No routes found")
                
        except Exception as e:
            print(f"      ✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # 4. Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✓ Routes Generated: {results_summary['total_routes']}")
    print(f"  • Direct Routes: {results_summary['direct_routes']}")
    print(f"  • Transfer Routes: {results_summary['transfer_routes']}")
    print(f"  • Generated At: {results_summary['generated_at']}")
    
    if results_summary['total_routes'] > 0:
        print("\n✅ SUCCESS: Route generation working correctly!")
        return True
    else:
        print("\n⚠ WARNING: No routes were generated. Check database content.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
