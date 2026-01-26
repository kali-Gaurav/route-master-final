#!/usr/bin/env python3
"""Show actual cached routes in database."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database_manager import get_db

db = get_db()
cached = db.get_all_cached_routes(limit=10)

print("\nCACHED ROUTES IN DATABASE:")
print("="*100)
for idx, route in enumerate(cached, 1):
    print(f"{idx:2}. {route['origin']:12} -> {route['destination']:12} | Routes: {route['total_routes']:6} | Accesses: {route['access_count']:3}")

stats = db.get_cached_routes_stats()
print("\n" + "="*100)
print("CACHE STATISTICS:")
print(f"  Total cached pairs: {stats['total_cached_pairs']}")
print(f"  Total routes cached: {stats['total_routes_cached']}")
print(f"  Total accesses: {stats['total_accesses']}")
print(f"  Avg search time: {stats['avg_search_time_ms']:.2f}ms")
print()
