#!/usr/bin/env python3
"""
FINALTrip - Main Batch Route Processing Engine

Generates routes for long-distance station pairs:
1. Identifies 30 major station pairs
2. Generates all route options (0, 1, 2, 3 transfers)
3. Validates routes with train schedules
4. Stores in database with caching
5. Provides statistics and retrieval optimization
"""

import sys
from pathlib import Path
import time
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent))

from route_optimizer import BatchRouteGenerator, SimpleBFSRouteGenerator
from database_manager import get_db
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_and_cache_routes():
    """Main entry point: Generate routes for 30 long-distance pairs and cache them."""
    
    print("\n" + "="*100)
    print("FINALTRIP BATCH ROUTE GENERATION & CACHING SYSTEM")
    print("="*100)
    print(f"Start Time: {datetime.now()}\n")
    
    # Initialize database and generators
    db = get_db()
    batch_gen = BatchRouteGenerator(db)
    
    # Get long-distance station pairs
    print("STEP 1: Identifying Major Station Pairs")
    print("-" * 100)
    station_pairs = batch_gen.get_long_distance_pairs(count=30)
    
    print(f"Found {len(station_pairs)} station pairs for batch processing:")
    for idx, (origin, dest) in enumerate(station_pairs[:10], 1):
        print(f"  {idx:2}. {origin:12} -> {dest:12}")
    if len(station_pairs) > 10:
        print(f"  ... and {len(station_pairs) - 10} more pairs\n")
    else:
        print()
    
    # Generate routes for all pairs
    print("STEP 2: Generating Routes (0, 1, 2, 3 Transfers)")
    print("-" * 100)
    
    batch_start = time.time()
    results = batch_gen.generate_batch_routes(
        station_pairs,
        max_transfers=3,
        save_to_db=True,
        verbose=True
    )
    batch_time = (time.time() - batch_start) * 1000
    
    # Step 3: Summary and Statistics
    print("\n" + "="*100)
    print("STEP 3: BATCH PROCESSING SUMMARY")
    print("="*100 + "\n")
    
    total_routes = sum(r['total_routes'] for r in results)
    total_pairs = len(results)
    saved_count = sum(1 for r in results if r.get('saved_to_db', False))
    
    print(f"Pairs processed:       {total_pairs}")
    print(f"Total routes found:    {total_routes}")
    print(f"Saved to database:     {saved_count}/{total_pairs}")
    print(f"Total processing time: {batch_time:.0f}ms ({batch_time/1000:.2f}s)")
    print(f"Average per pair:      {batch_time/total_pairs:.0f}ms")
    print()
    
    # Detailed breakdown by transfer count
    print("ROUTE BREAKDOWN BY TRANSFER LEVEL:")
    print("-" * 100)
    
    transfer_stats = {0: 0, 1: 0, 2: 0, 3: 0}
    time_stats = {0: 0, 1: 0, 2: 0, 3: 0}
    
    for result in results:
        for transfers, level_data in result['routes_by_transfer_level'].items():
            transfer_stats[transfers] += level_data['count']
            time_stats[transfers] += level_data['time_ms']
    
    for transfers in range(4):
        count = transfer_stats[transfers]
        avg_time = time_stats[transfers] / len(results) if len(results) > 0 else 0
        print(f"  {transfers} transfer(s):  {count:6} routes total | {avg_time:7.2f}ms avg per pair")
    
    print()
    
    # Database cache statistics
    print("STEP 4: CACHE STATISTICS")
    print("-" * 100)
    
    cache_stats = db.get_cached_routes_stats()
    print(f"Total cached pairs:    {cache_stats['total_cached_pairs']}")
    print(f"Total routes cached:   {cache_stats['total_routes_cached']}")
    print(f"Total cache accesses:  {cache_stats['total_accesses']}")
    print(f"Avg search time:       {cache_stats['avg_search_time_ms']:.2f}ms")
    print()
    
    # Show some cached routes
    print("STEP 5: SAMPLE CACHED ROUTES")
    print("-" * 100)
    
    cached_routes = db.get_all_cached_routes(limit=10)
    for idx, route in enumerate(cached_routes[:5], 1):
        print(f"\n  {idx}. {route['origin']} → {route['destination']} (max {route['num_transfers']} transfers)")
        print(f"     Routes: {route['total_routes']} | Accesses: {route['access_count']} | Time: {route['search_time_ms']:.2f}ms")
    
    print("\n" + "="*100)
    print("BATCH PROCESSING COMPLETE - ALL ROUTES CACHED AND READY FOR RETRIEVAL")
    print("="*100 + "\n")
    
    return results


def retrieve_cached_route(origin: str, destination: str, max_transfers: int = 3):
    """Retrieve a pre-cached route."""
    
    db = get_db()
    
    print(f"\nRetrieving cached route: {origin} -> {destination}")
    print("-" * 80)
    
    cached_route = db.get_cached_route(origin, destination, max_transfers)
    
    if cached_route:
        print(f"✓ Found in cache!")
        print(f"  Total routes: {cached_route['total_routes_found']}")
        print(f"  Routes breakdown:")
        for transfers, count in cached_route['routes_breakdown'].items():
            print(f"    - {transfers}: {count} routes")
        print(f"  Cached at: {cached_route['cached_at']}")
        print(f"  Original search time: {cached_route['search_time_ms']:.2f}ms")
        return cached_route
    else:
        print(f"✗ Not found in cache. Run batch generation first.")
        return None


def main():
    """Main entry point."""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description="FINALTrip Batch Route Generation & Caching System"
    )
    parser.add_argument(
        '--mode',
        choices=['batch', 'retrieve', 'stats'],
        default='batch',
        help='Operation mode: batch (generate routes), retrieve (get cached route), stats (show cache stats)'
    )
    parser.add_argument(
        '--origin',
        help='Origin station code (for retrieve mode)'
    )
    parser.add_argument(
        '--destination',
        help='Destination station code (for retrieve mode)'
    )
    parser.add_argument(
        '--transfers',
        type=int,
        default=3,
        help='Max transfers to search'
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'batch':
            results = generate_and_cache_routes()
            # Save results to file
            results_file = Path(__file__).parent / 'batch_results.json'
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\nResults saved to: {results_file}\n")
        
        elif args.mode == 'retrieve':
            if not args.origin or not args.destination:
                print("Error: --origin and --destination required for retrieve mode")
                sys.exit(1)
            retrieve_cached_route(args.origin, args.destination, args.transfers)
        
        elif args.mode == 'stats':
            db = get_db()
            stats = db.get_cached_routes_stats()
            print("\nCache Statistics:")
            print("-" * 80)
            for key, value in stats.items():
                print(f"  {key}: {value}")
            
            cached = db.get_all_cached_routes(limit=10)
            print(f"\nTop 10 Most Accessed Routes:")
            print("-" * 80)
            for idx, route in enumerate(cached, 1):
                print(f"  {idx:2}. {route['origin']:12} -> {route['destination']:12} | Accesses: {route['access_count']:3} | Time: {route['search_time_ms']:7.2f}ms")
            print()
    
    except KeyboardInterrupt:
        print("\n\nBatch processing interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

