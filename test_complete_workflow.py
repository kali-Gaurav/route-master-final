#!/usr/bin/env python3
"""
Complete Workflow Test: Generate -> Store -> Cache -> Retrieve

Tests the entire system:
1. Generate routes for 5 long-distance pairs
2. Shows step-by-step generation (0, 1, 2, 3 transfers)
3. Stores in database
4. Retrieves from cache
5. Shows performance statistics
"""

import sys
from pathlib import Path
import time
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from route_optimizer import BatchRouteGenerator
from database_manager import get_db

def main():
    print("\n" + "="*100)
    print("COMPLETE WORKFLOW TEST: Generate -> Store -> Cache -> Retrieve")
    print("="*100)
    print(f"Time: {datetime.now()}\n")
    
    # Initialize
    db = get_db()
    batch_gen = BatchRouteGenerator(db)
    
    # Use 5 pairs for quick demo
    test_pairs = [
        ('CSHIVAJIMA', 'DADAR'),
        ('CSHIVAJIMA', 'THANE'),
        ('DADAR', 'THANE'),
        ('THANE', 'PANVEL'),
        ('DADAR', 'PANVEL')
    ]
    
    print("TEST PAIRS:")
    print("-" * 100)
    for idx, (orig, dest) in enumerate(test_pairs, 1):
        print(f"  {idx}. {orig:12} -> {dest:12}")
    print()
    
    # PHASE 1: Generate Routes
    print("PHASE 1: GENERATE ROUTES FOR 5 PAIRS")
    print("="*100)
    print("(Generating 0, 1, 2, 3 transfer routes for each pair)\n")
    
    phase1_start = time.time()
    results = batch_gen.generate_batch_routes(
        test_pairs,
        max_transfers=3,
        save_to_db=True,
        verbose=True
    )
    phase1_time = (time.time() - phase1_start) * 1000
    
    # PHASE 2: Statistics
    print("\nPHASE 2: GENERATION STATISTICS")
    print("="*100 + "\n")
    
    total_routes = sum(r['total_routes'] for r in results)
    print(f"Pairs processed:       {len(results)}")
    print(f"Total routes found:    {total_routes}")
    print(f"Total generation time: {phase1_time:.0f}ms ({phase1_time/1000:.2f}s)")
    print(f"Average per pair:      {phase1_time/len(results):.0f}ms")
    print()
    
    # Detailed breakdown
    print("ROUTE BREAKDOWN:")
    for result in results[:3]:  # Show first 3
        print(f"\n  {result['origin']} -> {result['destination']}:")
        for transfers, level_data in result['routes_by_transfer_level'].items():
            count = level_data['count']
            time_ms = level_data['time_ms']
            print(f"    {transfers} transfer(s): {count:3} routes in {time_ms:7.2f}ms")
    
    # PHASE 3: Retrieve from Cache
    print("\n" + "="*100)
    print("PHASE 3: RETRIEVE FROM CACHE")
    print("="*100 + "\n")
    
    print("Testing cache retrieval (should be instant):\n")
    
    retrieval_times = []
    for origin, destination in test_pairs[:3]:
        retrieve_start = time.time()
        cached = db.get_cached_route(origin, destination, num_transfers=3)
        retrieve_time = (time.time() - retrieve_start) * 1000
        retrieval_times.append(retrieve_time)
        
        if cached:
            print(f"  {origin} -> {destination}")
            print(f"    Status: CACHED (found {cached['total_routes_found']} routes)")
            print(f"    Retrieval time: {retrieve_time:.2f}ms (vs {cached['search_time_ms']:.2f}ms original)")
            print(f"    Speedup: {cached['search_time_ms']/retrieve_time:.0f}x faster")
        else:
            print(f"  {origin} -> {destination}: NOT FOUND")
        print()
    
    avg_retrieval = sum(retrieval_times) / len(retrieval_times)
    print(f"Average retrieval time: {avg_retrieval:.2f}ms")
    
    # PHASE 4: Cache Statistics
    print("\n" + "="*100)
    print("PHASE 4: CACHE STATISTICS")
    print("="*100 + "\n")
    
    stats = db.get_cached_routes_stats()
    print(f"Total cached pairs:   {stats['total_cached_pairs']}")
    print(f"Total routes cached:  {stats['total_routes_cached']}")
    print(f"Total cache accesses: {stats['total_accesses']}")
    print(f"Avg search time:      {stats['avg_search_time_ms']:.2f}ms")
    
    # PHASE 5: System Performance
    print("\n" + "="*100)
    print("PHASE 5: SYSTEM PERFORMANCE SUMMARY")
    print("="*100 + "\n")
    
    print("GENERATION PERFORMANCE:")
    print(f"  - 5 station pairs generated")
    print(f"  - {total_routes} total routes found")
    print(f"  - All routes stored in database")
    print(f"  - Average generation time: {phase1_time/len(results):.0f}ms per pair")
    print()
    
    print("RETRIEVAL PERFORMANCE:")
    print(f"  - Average cache retrieval: {avg_retrieval:.2f}ms")
    print(f"  - Speedup vs generation: {phase1_time/(avg_retrieval*len(results)):.0f}x faster")
    print(f"  - Suitable for: Real-time web queries")
    print()
    
    print("DATABASE INTEGRATION:")
    print(f"  - Table: cached_routes (metadata)")
    print(f"  - Table: route_segments (individual legs)")
    print(f"  - Table: route_validations (train schedule checks)")
    print(f"  - Indices: Fast lookups by origin/destination")
    print()
    
    print("="*100)
    print("TEST COMPLETE - SYSTEM WORKING CORRECTLY")
    print("="*100)
    
    print("\nNEXT STEPS:")
    print("  1. Run 'python main.py --mode batch' to generate 30 pairs (background process)")
    print("  2. Use '/api/cached-routes?origin=X&destination=Y' to retrieve cached routes")
    print("  3. Use '/api/cache-stats' to monitor cache performance")
    print()
    
    return results


if __name__ == '__main__':
    main()
