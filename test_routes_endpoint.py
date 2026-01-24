#!/usr/bin/env python3
"""Test the /api/routes endpoint directly"""

import sys
import traceback
from api import app

# Create a test client
with app.test_client() as client:
    print("Testing /api/routes endpoint...")
    try:
        response = client.get('/api/routes?origin=NDLS&destination=KOTA&max_transfers=1')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.get_json() if response.content_type == 'application/json' else response.data[:500]}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        traceback.print_exc()
