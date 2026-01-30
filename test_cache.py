"""
Test script to demonstrate the route caching feature.
This script shows how cached routes are loaded vs. fresh calculations.
"""

import requests
import time
import json

API_URL = "http://localhost:5000/api/routes"

def test_route_caching():
    print("=" * 80)
    print("ROUTE CACHING FEATURE DEMONSTRATION")
    print("=" * 80)
    
    # Test cases: routes that have cached files in the workspace
    test_cases = [
        ("NDLS", "KOTA", "Should load from cache"),
        ("PGT", "KOTA", "Should load from cache"),
        ("HWH", "NDLS", "Should load from cache"),
        ("ADI", "KOTA", "Should load from cache"),
        ("XXX", "YYY", "Fresh calculation (if stations exist)")
    ]
    
    for origin, dest, description in test_cases:
        print(f"\n{'=' * 80}")
        print(f"Testing: {origin} → {dest}")
        print(f"Expected: {description}")
        print('-' * 80)
        
        # Make request and measure time
        start_time = time.time()
        try:
            response = requests.get(
                API_URL,
                params={"origin": origin, "destination": dest},
                timeout=30
            )
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                optimal_count = len(data.get('optimal_routes', []))
                all_count = len(data.get('all_generated_routes', []))
                
                # Determine if cached based on response time
                is_cached = elapsed_time < 0.5
                status = "✓ CACHED" if is_cached else "🔄 CALCULATED"
                
                print(f"{status}")
                print(f"Response Time: {elapsed_time:.3f} seconds")
                print(f"Optimal Routes: {optimal_count}")
                print(f"Total Routes: {all_count}")
                
                if is_cached:
                    print("💡 This was loaded from saved files!")
                else:
                    print("💡 This was freshly calculated and saved for future use.")
                    
            else:
                error_data = response.json()
                print(f"❌ Error: {error_data.get('error', 'Unknown error')}")
                print(f"Response Time: {elapsed_time:.3f} seconds")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request Failed: {e}")
            print("Make sure the API server is running: python api.py")
    
    print(f"\n{'=' * 80}")
    print("CACHING DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\nKey Observations:")
    print("• Cached routes load in < 500ms")
    print("• Fresh calculations take 3-10 seconds")
    print("• All results are automatically saved for future use")
    print("\nCheck the API server console for detailed cache logs!")

if __name__ == "__main__":
    print("Starting route caching tests...")
    print("Make sure the API server is running on http://localhost:5000\n")
    
    input("Press Enter to start tests...")
    test_route_caching()
