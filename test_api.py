#!/usr/bin/env python3
"""
Quick test script for the station search API
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_health():
    """Test health check endpoint"""
    print("=" * 60)
    print("Testing /api/health")
    print("=" * 60)
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_stations(query):
    """Test station search endpoint"""
    print("=" * 60)
    print(f"Testing /api/stations?q={query}")
    print("=" * 60)
    response = requests.get(f"{BASE_URL}/api/stations", params={"q": query, "limit": 20})
    data = response.json()
    print(f"Status: {response.status_code}")
    print(f"Success: {data.get('success')}")
    print(f"Total available: {data.get('total_available')}")
    print(f"Results found: {data.get('count')}")
    
    if data.get('stations'):
        print("\nStations:")
        for station in data.get('stations', []):
            print(f"  - {station['code']}: {station['name']} ({station['city']}, {station['state']})")
    else:
        print("No stations found")
    print()

if __name__ == "__main__":
    try:
        test_health()
        test_stations("delhi")
        test_stations("mumbai")
        test_stations("jaipur")
        test_stations("kota")
    except Exception as e:
        print(f"Error: {e}")
