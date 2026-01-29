#!/usr/bin/env python3
import sys
from route_finder import RouteFinder
import inspect

rf = RouteFinder()
print(f"Type: {type(rf)}")
print(f"Has find_all_routes: {hasattr(rf, 'find_all_routes')}")

# Try to get the method
try:
    method = getattr(rf, 'find_all_routes')
    print(f"Got method: {method}")
except AttributeError as e:
    print(f"Error: {e}")

# Check class methods
print(f"\nClass methods:")
for name in dir(RouteFinder):
    if 'find' in name.lower() and not name.startswith('_'):
        attr = getattr(RouteFinder, name, None)
        print(f"  {name}: {type(attr)}")

# Check in source
print(f"\nChecking source code...")
source = inspect.getsource(RouteFinder)
if 'def find_all_routes' in source:
    print("  ✓ find_all_routes IS defined in source")
else:
    print("  ✗ find_all_routes NOT in source")
