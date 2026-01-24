#!/usr/bin/env python3
"""Test Phase 1 admin endpoints"""
import requests
import json
import sys

# Fix encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:5000"

print("\n" + "="*80)
print("PHASE 1 ADMIN ENDPOINTS TEST")
print("="*80)

# Test 1: Health Check
print("\n[Test 1] GET /api/health")
try:
    r = requests.get(f"{BASE_URL}/api/health")
    data = r.json()
    print(f"Status: {r.status_code}")
    print(f"  - rappid_json_count: {data.get('rappid_json_count', 'N/A')}")
    print(f"  - rappid_last_refresh: {data.get('rappid_last_refresh', 'N/A')}")
    print("  [PASS]" if r.status_code == 200 else "  [FAIL]")
except Exception as e:
    print(f"  [ERROR]: {e}")

# Test 2: Get RAPPID data for a specific train
print("\n[Test 2] GET /api/rappid-data/16004 (stored JSON)")
try:
    r = requests.get(f"{BASE_URL}/api/rappid-data/16004")
    if r.status_code == 200:
        data = r.json()
        print(f"Status: {r.status_code}")
        print(f"  - fetched_at: {data.get('fetched_at', 'N/A')}")
        print(f"  - train_no: {data.get('train_no', 'N/A')}")
        print(f"  - has response: {bool(data.get('response', {}))}")
        print("  [PASS]")
    else:
        print(f"Status: {r.status_code}")
        print(f"  [FAIL] - Not Found")
except Exception as e:
    print(f"  [ERROR]: {e}")

# Test 3: Refresh single train
print("\n[Test 3] POST /admin/refresh-rappid/12970 (single train)")
try:
    r = requests.post(f"{BASE_URL}/admin/refresh-rappid/12970")
    data = r.json()
    print(f"Status: {r.status_code}")
    print(f"  - status: {data.get('status', 'N/A')}")
    print(f"  - train_no: {data.get('train_no', 'N/A')}")
    print("  [PASS]" if r.status_code == 200 else "  [FAIL]")
except Exception as e:
    print(f"  [ERROR]: {e}")

# Test 4: Bulk refresh
print("\n[Test 4] POST /admin/refresh-rappid-bulk (multiple trains)")
try:
    payload = {"train_numbers": ["14709", "18246", "22632"]}
    r = requests.post(f"{BASE_URL}/admin/refresh-rappid-bulk", json=payload)
    data = r.json()
    print(f"Status: {r.status_code}")
    print(f"  - total_requested: {data.get('total_requested', 0)}")
    print(f"  - successful: {data.get('successful', 0)}")
    print(f"  - failed: {data.get('failed', 0)}")
    print("  [PASS]" if r.status_code == 200 else "  [FAIL]")
except Exception as e:
    print(f"  [ERROR]: {e}")

# Test 5: RAPPID status
print("\n[Test 5] GET /admin/status/rappid (coverage stats)")
try:
    r = requests.get(f"{BASE_URL}/admin/status/rappid")
    data = r.json()
    print(f"Status: {r.status_code}")
    print(f"  - total_trains_in_dataset: {data.get('total_trains_in_dataset', 0)}")
    print(f"  - stored_json_files: {data.get('stored_json_files', 0)}")
    print(f"  - coverage_percent: {data.get('coverage_percent', 0)}%")
    print(f"  - missing_trains: {data.get('missing_trains', 0)}")
    print("  [PASS]" if r.status_code == 200 else "  [FAIL]")
except Exception as e:
    print(f"  [ERROR]: {e}")

# Test 6: Error handling - invalid train number
print("\n[Test 6] GET /api/rappid-data/invalid (error handling)")
try:
    r = requests.get(f"{BASE_URL}/api/rappid-data/invalid")
    print(f"Status: {r.status_code}")
    print("  [PASS] (correctly rejected)" if r.status_code == 400 else "  [FAIL]")
except Exception as e:
    print(f"  [ERROR]: {e}")

print("\n" + "="*80)
print("Test suite complete!")
print("="*80 + "\n")
