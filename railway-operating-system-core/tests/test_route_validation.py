import sys
sys.path.insert(0, '.')
from database.database_manager import db_manager_instance as db_mgr

test_scenarios = [
    {'origin': 'NDLS', 'dest': 'BCT', 'description': 'Major route'},
    {'origin': 'HWH', 'dest': 'MAS', 'description': 'Long distance'},
    {'origin': 'PUNE', 'dest': 'LKO', 'description': 'Cross-country'}
]

for scenario in test_scenarios:
    try:
        routes = db_mgr.find_routes_comprehensive(scenario['origin'], scenario['dest'])
        print(f"{scenario['description']}: {len(routes)} routes found")

        if routes:
            # Validate route structure
            valid_routes = []
            for route in routes:
                is_valid = (
                    'route_id' in route and
                    'train' in route and
                    'origin' in route and
                    'destination' in route and
                    'distance_km' in route and
                    route.get('distance_km', 0) > 0 and
                    'duration_minutes' in route and
                    route.get('duration_minutes', 0) > 0
                )
                if is_valid:
                    valid_routes.append(route)

            print(f"  Valid routes: {len(valid_routes)}/{len(routes)}")
            all_valid = len(valid_routes) == len(routes) and len(routes) > 0
            print(f"  All valid: {all_valid}")
        else:
            print("  No routes found - this will cause test failure")

    except Exception as e:
        print(f"{scenario['description']}: Error - {e}")
        import traceback
        traceback.print_exc()