#!/usr/bin/env python3
"""Quick debug script to test if API components work"""

import traceback
import sys

try:
    print("=" * 80)
    print("DEBUGGING API COMPONENTS")
    print("=" * 80)
    
    print("\n[1/5] Testing imports...")
    from route_optimizer import ParetoTrainRouter
    from optimization_engine import graph_builder
    import pandas as pd
    from datetime import datetime
    print("  OK - All imports successful")
    
    print("\n[2/5] Loading train data...")
    df = pd.read_csv('Train_details.csv', low_memory=False)
    print(f"  OK - Loaded {len(df):,} train detail records")
    
    print("\n[3/5] Building optimized graph...")
    graph_data = graph_builder.build_from_dataframe(df)
    print(f"  OK - Graph built with {len(graph_data['adjacency_list']):,} stations")
    
    print("\n[4/5] Creating Pareto router...")
    router = ParetoTrainRouter(
        graph=graph_data['adjacency_list'],
        station_maps={
            'station_to_id': graph_data['station_to_id'],
            'id_to_station': graph_data['id_to_station']
        },
        api_fetcher=None,
        journey_date=datetime.now(),
        train_df=df
    )
    print("  OK - Router instance created successfully")
    
    print("\n[5/5] Testing route finding...")
    print("  Finding routes from NDLS to KOTA with max_transfers=1...")
    routes = router.generate_all_routes('NDLS', 'KOTA', 1)
    
    if routes:
        pareto_optimal = router.pareto_optimize(routes)
        print(f"  OK - Found {len(routes)} total routes, {len(pareto_optimal)} Pareto-optimal")
    
    if routes:
        sample = routes[0]
        print(f"  Sample route structure:")
        print(f"    - route_id: {sample.get('route_id', 'N/A')}")
        print(f"    - segments: {len(sample.get('segments', []))} trains")
        print(f"    - total_time: {sample.get('total_time_hours', 'N/A')} hours")
        print(f"    - total_fare: {sample.get('total_fare', 'N/A')}")
    
    print("\n" + "=" * 80)
    print("SUCCESS: All API components working correctly!")
    print("=" * 80)
    
except Exception as e:
    print(f"\nERROR: {type(e).__name__}: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
