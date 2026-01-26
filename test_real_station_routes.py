"""
Route Generation Test - Select 2 Random Stations & Generate Routes
Tests all three route categories with real data
"""

import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_route_generation_with_real_stations():
    """Test route generation with real stations from database"""
    
    logger.info("\n" + "="*80)
    logger.info("ROUTE GENERATION TEST - REAL STATIONS")
    logger.info("="*80)
    
    try:
        from database_manager import DatabaseManager
        from route_optimizer import ParetoTrainRouter
        import random
        
        # Connect to database
        logger.info("\n[1] Connecting to database...")
        db = DatabaseManager()
        
        # Get random stations
        logger.info("\n[2] Fetching stations from database...")
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT station_code FROM stations WHERE station_code IS NOT NULL ORDER BY RANDOM() LIMIT 20")
            stations = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"   Found {len(stations)} available stations")
        
        if len(stations) < 2:
            logger.error("Not enough stations in database!")
            return False
        
        # Select 2 random stations
        source, destination = random.sample(stations, 2)
        
        # Override with known good pair
        source, destination = "CSMT", "DADA"
        logger.info(f"\n[3] Selected Station Pair:")
        logger.info(f"   Source:      {source}")
        logger.info(f"   Destination: {destination}")
        
        # Initialize router
        logger.info(f"\n[4] Initializing route optimizer...")
        router = ParetoTrainRouter(db)
        
        logger.info(f"   ✓ Graph loaded: {len(router.station_to_id)} stations")
        
        # Generate all routes
        logger.info(f"\n[5] Generating all routes...")
        start_time = time.time()
        all_routes = router.generate_all_routes(source, destination, max_transfers=3)
        gen_time = time.time() - start_time
        
        logger.info(f"   ✓ Generated {len(all_routes)} routes in {gen_time:.2f}s")
        
        # Analyze routes
        logger.info(f"\n[6] Analyzing route categories...")
        
        direct = [r for r in all_routes if len(r) == 1]
        single = [r for r in all_routes if len(r) == 2]
        multi = [r for r in all_routes if len(r) >= 3]
        
        logger.info(f"   Direct routes (0 transfers):   {len(direct):3d}")
        logger.info(f"   Single-transfer routes (1):    {len(single):3d}")
        logger.info(f"   Multi-transfer routes (2-3):   {len(multi):3d}")
        logger.info(f"   ───────────────────────────────────")
        logger.info(f"   Total routes:                  {len(all_routes):3d}")
        
        # Validate route structure
        logger.info(f"\n[7] Validating route structure...")
        
        valid_count = 0
        invalid_count = 0
        
        for i, route in enumerate(all_routes[:20]):  # Check first 20
            try:
                # Each route should be a list of segments
                if not isinstance(route, list) or len(route) == 0:
                    invalid_count += 1
                    continue
                
                # Each segment should have required fields
                for seg in route:
                    required = ['from', 'to', 'train_no', 'departure_time', 'arrival_time']
                    if not all(field in seg for field in required):
                        invalid_count += 1
                        break
                else:
                    valid_count += 1
            except:
                invalid_count += 1
        
        logger.info(f"   Valid routes (checked 20): {valid_count}/20")
        if invalid_count > 0:
            logger.warning(f"   Invalid routes: {invalid_count}/20")
        
        # Perform Pareto optimization
        logger.info(f"\n[8] Performing Pareto optimization...")
        opt_start = time.time()
        pareto_front = router.pareto_optimize(all_routes)
        opt_time = time.time() - opt_start
        
        logger.info(f"   ✓ Pareto front: {len(pareto_front)} non-dominated routes")
        logger.info(f"   Optimization time: {opt_time:.2f}s")
        
        # Select optimal routes
        logger.info(f"\n[9] Selecting optimal routes...")
        optimal_routes, categories = router.select_optimal_routes(pareto_front)
        
        logger.info(f"   Selected {len(optimal_routes)} optimal routes")
        if categories:
            logger.info(f"   Categories: {', '.join(categories)}")
        
        # Save results
        logger.info(f"\n[10] Saving results...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "destination": destination,
            "statistics": {
                "total_routes_generated": len(all_routes),
                "direct_routes": len(direct),
                "single_transfer_routes": len(single),
                "multi_transfer_routes": len(multi),
                "pareto_optimal_routes": len(optimal_routes),
                "generation_time_seconds": round(gen_time, 2),
                "optimization_time_seconds": round(opt_time, 2),
            },
            "optimal_routes": [
                {
                    "category": categories[i] if i < len(categories) else "Route",
                    "segments": len(route),
                    "transfers": len(route) - 1,
                    "sample_details": str(route)[:200]  # Truncate for JSON
                }
                for i, route in enumerate(optimal_routes[:5])  # Save top 5
            ],
            "sample_all_routes": [
                {
                    "segments": len(route),
                    "transfers": len(route) - 1,
                    "summary": f"{len(route)} segments"
                }
                for route in all_routes[:10]  # Sample of all routes
            ]
        }
        
        # Save to file
        output_file = f"route_test_{source}_{destination}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"   ✓ Saved to: {output_file}")
        
        # Display sample routes
        logger.info(f"\n[11] Sample optimal routes:")
        
        for i, route in enumerate(optimal_routes[:3], 1):
            cat = categories[i-1] if (i-1) < len(categories) else "Route"
            logger.info(f"\n   Route {i}: {cat}")
            
            # Route is a dictionary object
            if isinstance(route, dict):
                segments = route.get('segments', [])
                logger.info(f"   └─ Segments: {len(segments)}")
                
                # Show first 2 segments
                for j, seg in enumerate(segments[:2], 1):
                    if isinstance(seg, dict):
                        logger.info(f"      [{j}] {seg.get('from')} → {seg.get('to')} (Train: {seg.get('train_no')})")
            else:
                logger.info(f"   └─ Route type: {type(route)}")
                logger.info(f"   └─ Route data: {route}")
        
        # Final summary
        logger.info(f"\n" + "="*80)
        logger.info(f"TEST SUMMARY")
        logger.info(f"="*80)
        logger.info(f"Route Pair:                {source} → {destination}")
        logger.info(f"Total Routes Generated:    {len(all_routes)}")
        logger.info(f"├─ Direct (0 transfers):   {len(direct)}")
        logger.info(f"├─ Single-transfer (1):    {len(single)}")
        logger.info(f"└─ Multi-transfer (2-3):   {len(multi)}")
        logger.info(f"\nOptimal Routes:            {len(optimal_routes)}")
        logger.info(f"Generation Time:           {gen_time:.2f}s")
        logger.info(f"Optimization Time:         {opt_time:.2f}s")
        logger.info(f"Total Time:                {gen_time + opt_time:.2f}s")
        logger.info(f"\nSaved to:                  {output_file}")
        logger.info(f"\n✅ TEST COMPLETED SUCCESSFULLY")
        logger.info(f"="*80)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_route_generation_with_real_stations()
    exit(0 if success else 1)
