#!/usr/bin/env python
"""Debug the /api/routes endpoint"""

import sys
import os
import asyncio
from datetime import datetime

# Set up paths
os.chdir("c:/Users/Gaurav Nagar/OneDrive/Documents/testingfolder_v3/route-master-final")
sys.path.insert(0, ".")

print("[*] Loading modules...")
from route_optimizer import get_routes_data, ParetoTrainRouter
from real_time_api_wrapper import ApiLiveFetcher
from api import GLOBAL_TRAIN_DF, rappid_client

print(f"[✓] Train DF loaded: {len(GLOBAL_TRAIN_DF)} trains")

async def test_get_routes():
    """Test the get_routes_data function"""
    origin = "NDLS"
    destination = "KOTA"
    max_transfers = 1
    travel_date = datetime.strptime("25-01-2026", "%d-%m-%Y")
    
    print(f"\n[*] Testing get_routes_data({origin}, {destination}, {max_transfers}, ...)")
    print(f"    Travel date: {travel_date}")
    
    try:
        # Create API fetcher
        api_fetcher = ApiLiveFetcher(
            rappid_client=rappid_client,
            aiohttp_session=None
        )
        
        print("[*] Calling get_routes_data...")
        results, router = await get_routes_data(
            origin, destination, max_transfers, GLOBAL_TRAIN_DF, api_fetcher, travel_date
        )
        
        print(f"[✓] Got results!")
        if "error" in results:
            print(f"[✗] Error in results: {results['error']}")
        else:
            routes = results.get("optimal_routes", [])
            print(f"[✓] Found {len(routes)} optimal routes")
            
            if routes:
                first = routes[0]
                print(f"    First route: {len(first.get('segments', []))} segments")
                print(f"    Keys: {list(first.keys())}")
        
        return True
    except Exception as e:
        print(f"[✗] Error: {type(e).__name__}: {str(e)[:300]}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_get_routes())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n[*] Interrupted")
        sys.exit(1)
