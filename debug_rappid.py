#!/usr/bin/env python3
"""Debug RAPPID API response structure"""
import requests
import json

# Make direct API call
print("\n[*] Testing RAPPID API directly...")
print("="*70)

try:
    response = requests.get(
        'https://rappid.in/apis/train.php',
        params={'train_no': '16320'},
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    
    data = response.json()
    
    print(f"\nResponse Keys: {list(data.keys())}")
    print(f"\nFull Response Structure:")
    print(json.dumps(data, indent=2)[:1000])
    
except requests.exceptions.Timeout:
    print("TIMEOUT - API not responding")
except requests.exceptions.ConnectionError:
    print("CONNECTION ERROR - Cannot reach API")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "="*70)
