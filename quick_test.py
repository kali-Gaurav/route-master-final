#!/usr/bin/env python
"""Quick test to identify API issues"""

import requests
import subprocess
import sys
import time
import json

BASE_URL = "http://127.0.0.1:5000"

def start_api():
    """Start API server in background"""
    proc = subprocess.Popen(
        [sys.executable, 'api.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(10)  # Wait for startup
    return proc

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    try:
        resp = requests.get(f"{BASE_URL}/api/health", timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("✓ Health endpoint working")
        return resp.status_code == 200
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_routes():
    """Test routes endpoint"""
    print("\n=== Testing Routes Endpoint ===")
    try:
        params = {
            'origin': 'NDLS',
            'destination': 'KOTA',
            'max_transfers': 1,
            'date': '25-01-2026'
        }
        resp = requests.get(f"{BASE_URL}/api/routes", params=params, timeout=60)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"Error response: {resp.text[:500]}")
            return False
        
        data = resp.json()
        print(f"Response keys: {list(data.keys())}")
        
        if "error" in data:
            print(f"API Error: {data['error']}")
            return False
        
        routes = data.get('optimal_routes', [])
        print(f"Routes found: {len(routes)}")
        
        if routes:
            first = routes[0]
            print(f"First route keys: {list(first.keys())}")
            print(f"First route transfers: {len(first.get('segments', []))}")
            print("✓ Routes endpoint working")
            return True
        else:
            print("⊘ No routes found (may be OK depending on data)")
            return True
            
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {str(e)[:200]}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 80)
    print(" QUICK API TEST")
    print("=" * 80)
    
    print("\n[*] Starting API server...")
    proc = start_api()
    
    try:
        success = True
        success = test_health() and success
        success = test_routes() and success
        
        print("\n" + "=" * 80)
        if success:
            print("✓ All tests passed!")
        else:
            print("✗ Some tests failed")
        print("=" * 80)
        
        return 0 if success else 1
    finally:
        print("\n[*] Stopping API server...")
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except:
            proc.kill()

if __name__ == "__main__":
    sys.exit(main())
