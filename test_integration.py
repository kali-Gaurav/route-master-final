#!/usr/bin/env python3
"""Integration test for Phase 5.1"""
from route_optimizer import get_routes_data
from database_manager import get_db
import json

# First, get some stations from the database
db = get_db()
stations = db.search_stations('', 50)
print(f"Total sample stations retrieved: {len(stations)}")
print("\nFirst 10 stations:")
for s in stations[:10]:
    print(f"  {s['code']}: {s['name']}")

# Try a route between first two stations
if len(stations) >= 2:
    origin = stations[0]['code']
    destination = stations[1]['code']
    print(f"\nTesting route: {origin} ({stations[0]['name']}) -> {destination} ({stations[1]['name']})")
    
    result = get_routes_data(origin, destination, max_transfers=2)
    print(f"\nResult:")
    print(json.dumps(result, indent=2, default=str))
