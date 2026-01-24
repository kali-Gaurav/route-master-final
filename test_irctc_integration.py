#!/usr/bin/env python3
"""
Test script for IRCTC API integration
Tests all endpoints and validates the integration
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"

def test_live_station():
    """Test live station endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Live Station Data")
    print("="*60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/live-station",
            params={'station': 'PGT', 'hours': 1}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Live station data retrieved")
            data = response.json()
            print(json.dumps(data, indent=2)[:500] + "...")
        else:
            print("✗ Failed to retrieve live station data")
            print(response.text)
    except Exception as e:
        print(f"✗ Error: {e}")

def test_seat_availability():
    """Test seat availability endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Seat Availability")
    print("="*60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/seat-availability",
            params={
                'train': '12345',
                'source': 'PGT',
                'destination': 'KOTA',
                'date': (datetime.now() + timedelta(days=1)).strftime('%d-%m-%Y')
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Seat availability data retrieved")
            data = response.json()
            print(json.dumps(data, indent=2)[:500] + "...")
        else:
            print("✗ Failed to retrieve seat availability")
            print(response.text)
    except Exception as e:
        print(f"✗ Error: {e}")

def test_fare():
    """Test fare endpoint"""
    print("\n" + "="*60)
    print("TEST 3: Train Fare")
    print("="*60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/fare",
            params={
                'train': '12345',
                'source': 'PGT',
                'destination': 'KOTA',
                'date': (datetime.now() + timedelta(days=1)).strftime('%d-%m-%Y')
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Fare data retrieved")
            data = response.json()
            print(json.dumps(data, indent=2)[:500] + "...")
        else:
            print("✗ Failed to retrieve fare")
            print(response.text)
    except Exception as e:
        print(f"✗ Error: {e}")

def test_routes_with_validation():
    """Test main routes endpoint with IRCTC validation"""
    print("\n" + "="*60)
    print("TEST 4: Routes with IRCTC Validation")
    print("="*60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/routes",
            params={
                'origin': 'PGT',
                'destination': 'KOTA',
                'max_transfers': 2,
                'date': (datetime.now() + timedelta(days=1)).strftime('%d-%m-%Y')
            },
            timeout=120  # Long timeout for route calculation
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Routes retrieved with IRCTC validation")
            data = response.json()
            
            # Print metadata
            if 'validation_metadata' in data:
                print(f"\n📊 Validation Metadata:")
                for key, value in data['validation_metadata'].items():
                    print(f"  - {key}: {value}")
            
            # Print route count
            optimal_routes = data.get('optimal_routes', [])
            print(f"\n📋 Retrieved {len(optimal_routes)} optimal routes")
            
            # Print first route details
            if optimal_routes:
                route = optimal_routes[0]
                print(f"\n🚂 First Route Details:")
                print(f"  - Route ID: {route.get('route_id')}")
                print(f"  - Category: {route.get('category')}")
                
                objectives = route.get('objectives', {})
                print(f"  - Time: {objectives.get('time')} min")
                print(f"  - Cost: ₹{objectives.get('cost')}")
                print(f"  - Transfers: {objectives.get('transfers')}")
                
                # Check IRCTC validation
                irctc_val = route.get('irctc_validation', {})
                print(f"\n✓ IRCTC Validation: {irctc_val.get('valid')}")
                if irctc_val.get('errors'):
                    print(f"  Errors: {irctc_val.get('errors')}")
        else:
            print("✗ Failed to retrieve routes")
            print(response.text)
    except requests.exceptions.Timeout:
        print("⏱️  Request timed out - route calculation took too long")
    except Exception as e:
        print(f"✗ Error: {e}")

def test_validate_routes():
    """Test validate routes endpoint"""
    print("\n" + "="*60)
    print("TEST 5: Validate Routes Endpoint")
    print("="*60)
    
    sample_routes = [
        {
            "route_id": "TEST_01",
            "segments": [
                {
                    "train_no": "12345",
                    "from": "PGT",
                    "to": "KOTA",
                    "departure": "10:00:00",
                    "arrival": "18:00:00"
                }
            ]
        }
    ]
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/validate-routes",
            json={
                'routes': sample_routes,
                'date': (datetime.now() + timedelta(days=1)).strftime('%d-%m-%Y')
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Routes validated successfully")
            data = response.json()
            print(json.dumps(data, indent=2)[:500] + "...")
        else:
            print("✗ Failed to validate routes")
            print(response.text)
    except Exception as e:
        print(f"✗ Error: {e}")

def main():
    print("\n" + "="*60)
    print("IRCTC API Integration Test Suite")
    print("="*60)
    print(f"Testing backend at: {BASE_URL}")
    print(f"Test time: {datetime.now().isoformat()}")
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/api/routes", params={'origin': 'PGT', 'destination': 'KOTA'}, timeout=5)
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to backend at {BASE_URL}")
        print("Make sure the Flask backend is running: python api.py")
        return
    
    # Run tests
    test_live_station()
    test_seat_availability()
    test_fare()
    test_routes_with_validation()
    test_validate_routes()
    
    print("\n" + "="*60)
    print("Test Suite Complete")
    print("="*60)

if __name__ == "__main__":
    main()
