#!/usr/bin/env python3
"""
Test the Flask API locally
"""

import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

# Now test imports
try:
    from api.index import app
    print("✓ Flask app imported successfully")
    
    # Test that app is configured
    print(f"✓ App name: {app.name}")
    
    # List registered routes
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(f"{rule.endpoint}: {rule.rule}")
    
    print(f"✓ Registered {len(routes)} routes:")
    for route in sorted(routes):
        print(f"  - {route}")
    
    # Test the app context
    with app.test_client() as client:
        # Test health endpoint
        response = client.get('/api/health')
        print(f"\n✓ GET /api/health: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.get_json()}")
        
        # Test stations endpoint
        response = client.get('/api/stations')
        print(f"✓ GET /api/stations: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"  Stations count: {data.get('count', 0)}")
        
        # Test routes endpoint
        response = client.post('/api/routes', json={
            'source': 'NDLS',
            'destination': 'CSMT'
        })
        print(f"✓ POST /api/routes: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"  Response: {data}")
    
    print("\n✅ All API tests passed!")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
