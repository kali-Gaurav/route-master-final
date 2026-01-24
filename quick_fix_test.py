#!/usr/bin/env python3
"""Quick test to verify fixes"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"
TEST_TRAIN = "16320"

print("\n" + "="*70)
print("  QUICK VERIFICATION TEST - RAPPID FIXES")
print("="*70)

# Test 1: Train Schedule (was 500, should now work)
print("\n[Test 1] Train Schedule Endpoint")
try:
    response = requests.get(
        f"{BASE_URL}/api/train-schedule",
        params={"train_no": TEST_TRAIN},
        timeout=10
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Train: {data.get('train_name', 'N/A')}")
        print(f"  ✓ Route stations: {data.get('total_stations', 'N/A')}")
    else:
        print(f"  ✗ Error: {response.text[:100]}")
except Exception as e:
    print(f"  ✗ Exception: {e}")

# Test 2: Train Seats
print("\n[Test 2] Train Seats Endpoint")
try:
    response = requests.get(
        f"{BASE_URL}/api/train-seats",
        params={"train_no": TEST_TRAIN},
        timeout=10
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Available seats: {data.get('seat_info', {}).get('available', 'N/A')}")
    else:
        print(f"  ✗ Error: {response.text[:100]}")
except Exception as e:
    print(f"  ✗ Exception: {e}")

# Test 3: Train Fares
print("\n[Test 3] Train Fares Endpoint")
try:
    response = requests.get(
        f"{BASE_URL}/api/train-fares",
        params={"train_no": TEST_TRAIN},
        timeout=10
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Currency: {data.get('currency', 'N/A')}")
        print(f"  ✓ Has fares data: {bool(data.get('fares'))}")
    else:
        print(f"  ✗ Error: {response.text[:100]}")
except Exception as e:
    print(f"  ✗ Exception: {e}")

# Test 4: Train Status
print("\n[Test 4] Train Status Endpoint")
try:
    response = requests.get(
        f"{BASE_URL}/api/train-status",
        params={"train_no": TEST_TRAIN},
        timeout=10
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Status: {data.get('status', 'N/A')}")
    else:
        print(f"  ✗ Error: {response.text[:100]}")
except Exception as e:
    print(f"  ✗ Exception: {e}")

# Test 5: Routes with validation_metadata
print("\n[Test 5] Routes Endpoint (Check metadata)")
try:
    start = time.time()
    response = requests.get(
        f"{BASE_URL}/api/routes",
        params={
            "origin": "ADI",
            "destination": "HWH",
            "validation": "rappid"
        },
        timeout=30
    )
    elapsed = (time.time() - start) * 1000
    print(f"  Status: {response.status_code}")
    print(f"  Response time: {elapsed:.0f}ms")
    
    if response.status_code == 200:
        data = response.json()
        if 'validation_metadata' in data:
            print(f"  ✓ validation_metadata present")
            print(f"    - validation_source: {data['validation_metadata'].get('validation_source')}")
            print(f"    - routes_validated: {data['validation_metadata'].get('routes_validated')}")
        else:
            print(f"  ✗ validation_metadata MISSING")
        print(f"  ✓ Routes found: {len(data.get('optimal_routes', []))}")
    else:
        print(f"  ✗ Error: {response.text[:100]}")
except Exception as e:
    print(f"  ✗ Exception: {e}")

print("\n" + "="*70)
print("  Verification Complete")
print("="*70 + "\n")
