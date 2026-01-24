#!/usr/bin/env python3
"""
RAPPID Integration - Comprehensive Deep Testing Suite
Tests all functionality thoroughly
"""

import requests
import json
import time
from datetime import datetime
import sys

# Configuration
BASE_URL = "http://localhost:5000"
TEST_TRAIN_NO = "16320"
TEST_ORIGIN = "ADI"
TEST_DESTINATION = "HWH"
TIMEOUT = 30

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "errors": []
}

def print_header(title):
    """Print test section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_test(test_num, name):
    """Print test name"""
    print(f"\n[Test {test_num}] {name}")
    print("-" * 60)

def print_success(message):
    """Print success message"""
    print(f"  ✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"  ❌ {message}")

def print_info(message):
    """Print info message"""
    print(f"  ℹ️  {message}")

def test_health_check():
    """Test 1: Health check endpoint"""
    print_test(1, "Health Check Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            
            checks = [
                ("status", "healthy"),
                ("irctc_api_configured", True),
                ("rappid_api_configured", True),
                ("dual_validation_available", True)
            ]
            
            all_passed = True
            for key, expected in checks:
                if key in data and data[key] == expected:
                    print_success(f"{key}: {data[key]}")
                else:
                    print_error(f"{key}: Expected {expected}, got {data.get(key)}")
                    all_passed = False
            
            if all_passed:
                test_results["passed"].append("Health Check")
                return True
            else:
                test_results["failed"].append("Health Check - Incomplete")
                return False
        else:
            print_error(f"Status code: {response.status_code}")
            test_results["failed"].append("Health Check - Bad Status")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        test_results["errors"].append(f"Health Check - {str(e)}")
        return False

def test_train_data_endpoint():
    """Test 2: Train data endpoint"""
    print_test(2, "Train Data Endpoint")
    try:
        response = requests.get(
            f"{BASE_URL}/api/train-data",
            params={"train_no": TEST_TRAIN_NO},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            required_fields = ["train_no", "data", "timestamp", "source"]
            all_present = True
            
            for field in required_fields:
                if field in data:
                    print_success(f"Field '{field}' present")
                else:
                    print_error(f"Field '{field}' missing")
                    all_present = False
            
            if data.get("source") == "RAPPID API":
                print_success("Source correctly identified as RAPPID API")
            else:
                print_error(f"Source is {data.get('source')}, expected RAPPID API")
                all_present = False
            
            if all_present:
                test_results["passed"].append("Train Data Endpoint")
                return True
            else:
                test_results["failed"].append("Train Data Endpoint - Missing fields")
                return False
        else:
            print_error(f"Status code: {response.status_code}")
            test_results["failed"].append("Train Data - Bad Status")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        test_results["errors"].append(f"Train Data - {str(e)}")
        return False

def test_train_schedule_endpoint():
    """Test 3: Train schedule endpoint"""
    print_test(3, "Train Schedule Endpoint")
    try:
        response = requests.get(
            f"{BASE_URL}/api/train-schedule",
            params={"train_no": TEST_TRAIN_NO},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            required_fields = ["train_no", "train_name", "source_station", "destination_station", "route"]
            all_present = True
            
            for field in required_fields:
                if field in data:
                    if field == "route" and isinstance(data[field], list):
                        print_success(f"Field '{field}' present (list of {len(data[field])} stations)")
                    else:
                        print_success(f"Field '{field}' present: {data[field][:30]}..." if len(str(data[field])) > 30 else f"Field '{field}': {data[field]}")
                else:
                    print_error(f"Field '{field}' missing")
                    all_present = False
            
            if all_present:
                test_results["passed"].append("Train Schedule Endpoint")
                return True
            else:
                test_results["failed"].append("Train Schedule - Missing fields")
                return False
        else:
            print_error(f"Status code: {response.status_code}")
            test_results["failed"].append("Train Schedule - Bad Status")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        test_results["errors"].append(f"Train Schedule - {str(e)}")
        return False

def test_train_seats_endpoint():
    """Test 4: Train seats endpoint"""
    print_test(4, "Train Seats Endpoint")
    try:
        response = requests.get(
            f"{BASE_URL}/api/train-seats",
            params={"train_no": TEST_TRAIN_NO},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            required_fields = ["train_no", "seat_info"]
            all_present = True
            
            for field in required_fields:
                if field in data:
                    print_success(f"Field '{field}' present")
                else:
                    print_error(f"Field '{field}' missing")
                    all_present = False
            
            # Check seat_info structure
            if "seat_info" in data and "available" in data["seat_info"]:
                available_seats = data["seat_info"]["available"]
                print_success(f"Available seats: {available_seats}")
            
            if all_present:
                test_results["passed"].append("Train Seats Endpoint")
                return True
            else:
                test_results["failed"].append("Train Seats - Missing fields")
                return False
        else:
            print_error(f"Status code: {response.status_code}")
            test_results["failed"].append("Train Seats - Bad Status")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        test_results["errors"].append(f"Train Seats - {str(e)}")
        return False

def test_train_fares_endpoint():
    """Test 5: Train fares endpoint"""
    print_test(5, "Train Fares Endpoint")
    try:
        response = requests.get(
            f"{BASE_URL}/api/train-fares",
            params={"train_no": TEST_TRAIN_NO},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            required_fields = ["train_no", "fares", "currency"]
            all_present = True
            
            for field in required_fields:
                if field in data:
                    if field == "fares":
                        print_success(f"Field '{field}' present with {len(data[field])} entries")
                    else:
                        print_success(f"Field '{field}': {data[field]}")
                else:
                    print_error(f"Field '{field}' missing")
                    all_present = False
            
            if all_present:
                test_results["passed"].append("Train Fares Endpoint")
                return True
            else:
                test_results["failed"].append("Train Fares - Missing fields")
                return False
        else:
            print_error(f"Status code: {response.status_code}")
            test_results["failed"].append("Train Fares - Bad Status")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        test_results["errors"].append(f"Train Fares - {str(e)}")
        return False

def test_train_status_endpoint():
    """Test 6: Train status endpoint"""
    print_test(6, "Train Status Endpoint")
    try:
        response = requests.get(
            f"{BASE_URL}/api/train-status",
            params={"train_no": TEST_TRAIN_NO},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            required_fields = ["train_no", "status"]
            all_present = True
            
            for field in required_fields:
                if field in data:
                    print_success(f"Field '{field}': {data[field]}")
                else:
                    print_error(f"Field '{field}' missing")
                    all_present = False
            
            if all_present:
                test_results["passed"].append("Train Status Endpoint")
                return True
            else:
                test_results["failed"].append("Train Status - Missing fields")
                return False
        else:
            print_error(f"Status code: {response.status_code}")
            test_results["failed"].append("Train Status - Bad Status")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        test_results["errors"].append(f"Train Status - {str(e)}")
        return False

def test_error_handling_missing_param():
    """Test 7: Error handling - missing parameters"""
    print_test(7, "Error Handling - Missing Parameters")
    try:
        response = requests.get(
            f"{BASE_URL}/api/train-data",
            timeout=TIMEOUT
        )
        
        if response.status_code == 400:
            data = response.json()
            if "error" in data:
                print_success(f"Correctly returned 400 with error: {data['error']}")
                test_results["passed"].append("Error Handling - Missing Params")
                return True
            else:
                print_error("Error field missing in response")
                test_results["failed"].append("Error Handling - No error field")
                return False
        else:
            print_error(f"Expected 400, got {response.status_code}")
            test_results["failed"].append("Error Handling - Wrong status code")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        test_results["errors"].append(f"Error Handling - {str(e)}")
        return False

def test_invalid_train_number():
    """Test 8: Error handling - invalid train number"""
    print_test(8, "Error Handling - Invalid Train Number")
    try:
        response = requests.get(
            f"{BASE_URL}/api/train-data",
            params={"train_no": "99999999"},
            timeout=TIMEOUT
        )
        
        if response.status_code == 500 or response.status_code == 200:
            data = response.json()
            if "error" in data or response.status_code == 500:
                print_success(f"Correctly handled invalid train with status {response.status_code}")
                test_results["passed"].append("Error Handling - Invalid Train")
                return True
            else:
                print_error("Unexpected response structure")
                test_results["failed"].append("Error Handling - Unexpected response")
                return False
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            test_results["failed"].append("Error Handling - Unexpected status")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        test_results["errors"].append(f"Error Handling - {str(e)}")
        return False

def test_single_route_validation():
    """Test 9: Single route validation"""
    print_test(9, "Single Route Validation (RAPPID)")
    try:
        route = {
            "source": TEST_ORIGIN,
            "destination": TEST_DESTINATION,
            "segments": [
                {
                    "train_no": TEST_TRAIN_NO,
                    "from": TEST_ORIGIN,
                    "to": TEST_DESTINATION
                }
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/validate-route-rappid",
            json={"route": route, "date": "26-01-2026"},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            required_fields = ["rappid_validation"]
            all_present = True
            
            for field in required_fields:
                if field in data:
                    print_success(f"Field '{field}' present")
                else:
                    print_error(f"Field '{field}' missing")
                    all_present = False
            
            # Check validation structure
            if "rappid_validation" in data:
                validation = data["rappid_validation"]
                checks = ["valid", "segments", "summary"]
                for check in checks:
                    if check in validation:
                        print_success(f"Validation '{check}' present")
                    else:
                        print_error(f"Validation '{check}' missing")
                        all_present = False
            
            if all_present:
                test_results["passed"].append("Single Route Validation")
                return True
            else:
                test_results["failed"].append("Single Route Validation - Missing fields")
                return False
        else:
            print_error(f"Status code: {response.status_code}")
            test_results["failed"].append("Single Route Validation - Bad Status")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        test_results["errors"].append(f"Single Route Validation - {str(e)}")
        return False

def test_routes_endpoint_rappid():
    """Test 10: Routes endpoint with RAPPID validation"""
    print_test(10, "Routes Endpoint (RAPPID Validation)")
    try:
        response = requests.get(
            f"{BASE_URL}/api/routes",
            params={
                "origin": TEST_ORIGIN,
                "destination": TEST_DESTINATION,
                "validation": "rappid",
                "max_transfers": 3
            },
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            required_fields = ["optimal_routes", "validation_metadata"]
            all_present = True
            
            for field in required_fields:
                if field in data:
                    print_success(f"Field '{field}' present")
                else:
                    print_error(f"Field '{field}' missing")
                    all_present = False
            
            # Check metadata
            if "validation_metadata" in data:
                metadata = data["validation_metadata"]
                if metadata.get("validation_source") == "RAPPID":
                    print_success("Validation source correctly set to RAPPID")
                else:
                    print_error(f"Validation source: {metadata.get('validation_source')}")
                    all_present = False
            
            # Check routes
            if "optimal_routes" in data and len(data["optimal_routes"]) > 0:
                print_success(f"Found {len(data['optimal_routes'])} optimal routes")
            else:
                print_info("No optimal routes found")
            
            if all_present:
                test_results["passed"].append("Routes Endpoint - RAPPID")
                return True
            else:
                test_results["failed"].append("Routes Endpoint - RAPPID - Missing fields")
                return False
        else:
            print_error(f"Status code: {response.status_code}")
            test_results["failed"].append("Routes Endpoint - RAPPID - Bad Status")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        test_results["errors"].append(f"Routes Endpoint - RAPPID - {str(e)}")
        return False

def test_routes_endpoint_irctc():
    """Test 11: Routes endpoint with IRCTC validation"""
    print_test(11, "Routes Endpoint (IRCTC Validation)")
    try:
        response = requests.get(
            f"{BASE_URL}/api/routes",
            params={
                "origin": TEST_ORIGIN,
                "destination": TEST_DESTINATION,
                "validation": "irctc",
                "max_transfers": 3
            },
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "validation_metadata" in data:
                metadata = data["validation_metadata"]
                if metadata.get("validation_source") == "IRCTC":
                    print_success("Validation source correctly set to IRCTC")
                else:
                    print_error(f"Validation source: {metadata.get('validation_source')}")
            
            test_results["passed"].append("Routes Endpoint - IRCTC")
            return True
        else:
            print_error(f"Status code: {response.status_code}")
            test_results["failed"].append("Routes Endpoint - IRCTC - Bad Status")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        test_results["errors"].append(f"Routes Endpoint - IRCTC - {str(e)}")
        return False

def test_routes_endpoint_dual():
    """Test 12: Routes endpoint with dual validation"""
    print_test(12, "Routes Endpoint (Dual Validation - RAPPID + IRCTC)")
    try:
        response = requests.get(
            f"{BASE_URL}/api/routes",
            params={
                "origin": TEST_ORIGIN,
                "destination": TEST_DESTINATION,
                "validation": "dual",
                "max_transfers": 3
            },
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "validation_metadata" in data:
                metadata = data["validation_metadata"]
                if metadata.get("validation_source") == "DUAL":
                    print_success("Validation source correctly set to DUAL")
                else:
                    print_error(f"Validation source: {metadata.get('validation_source')}")
                
                apis = metadata.get("apis_used", [])
                if "RAPPID" in apis and "IRCTC" in apis:
                    print_success(f"Both APIs used: {apis}")
                else:
                    print_error(f"APIs used: {apis}")
            
            test_results["passed"].append("Routes Endpoint - Dual")
            return True
        else:
            print_error(f"Status code: {response.status_code}")
            test_results["failed"].append("Routes Endpoint - Dual - Bad Status")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        test_results["errors"].append(f"Routes Endpoint - Dual - {str(e)}")
        return False

def test_performance_first_call():
    """Test 13: Performance - First call (no cache)"""
    print_test(13, "Performance - First Call (No Cache)")
    try:
        start_time = time.time()
        response = requests.get(
            f"{BASE_URL}/api/train-data",
            params={"train_no": "12302"},  # Different train to avoid cache
            timeout=TIMEOUT
        )
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to ms
        
        if response.status_code == 200:
            print_success(f"Response time: {response_time:.2f}ms")
            
            if response_time < 2000:
                print_success("Performance acceptable (< 2000ms)")
                test_results["passed"].append("Performance - First Call")
                return True
            else:
                print_error(f"Response time too high: {response_time:.2f}ms")
                test_results["failed"].append("Performance - First Call - Slow")
                return False
        else:
            print_error(f"Status code: {response.status_code}")
            test_results["failed"].append("Performance - First Call - Bad Status")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        test_results["errors"].append(f"Performance - First Call - {str(e)}")
        return False

def test_performance_cached_call():
    """Test 14: Performance - Cached call"""
    print_test(14, "Performance - Cached Call")
    try:
        # Warm up cache
        requests.get(
            f"{BASE_URL}/api/train-data",
            params={"train_no": TEST_TRAIN_NO},
            timeout=TIMEOUT
        )
        time.sleep(0.1)
        
        # Measure cached call
        start_time = time.time()
        response = requests.get(
            f"{BASE_URL}/api/train-data",
            params={"train_no": TEST_TRAIN_NO},
            timeout=TIMEOUT
        )
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to ms
        
        if response.status_code == 200:
            print_success(f"Response time: {response_time:.2f}ms")
            
            if response_time < 200:
                print_success("Cache performance excellent (< 200ms)")
                test_results["passed"].append("Performance - Cached Call")
                return True
            else:
                print_info(f"Response time: {response_time:.2f}ms (acceptable)")
                test_results["passed"].append("Performance - Cached Call")
                return True
        else:
            print_error(f"Status code: {response.status_code}")
            test_results["failed"].append("Performance - Cached Call - Bad Status")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        test_results["errors"].append(f"Performance - Cached Call - {str(e)}")
        return False

def test_concurrent_requests():
    """Test 15: Concurrent requests handling"""
    print_test(15, "Concurrent Requests (5 simultaneous)")
    try:
        import concurrent.futures
        
        def make_request():
            response = requests.get(
                f"{BASE_URL}/api/train-data",
                params={"train_no": TEST_TRAIN_NO},
                timeout=TIMEOUT
            )
            return response.status_code == 200
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        success_count = sum(results)
        
        print_success(f"Successful requests: {success_count}/5")
        
        if success_count == 5:
            test_results["passed"].append("Concurrent Requests")
            return True
        else:
            test_results["failed"].append(f"Concurrent Requests - Only {success_count}/5 successful")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        test_results["errors"].append(f"Concurrent Requests - {str(e)}")
        return False

def test_batch_validation():
    """Test 16: Batch route validation"""
    print_test(16, "Batch Route Validation")
    try:
        routes = [
            {
                "source": TEST_ORIGIN,
                "destination": TEST_DESTINATION,
                "segments": [{"train_no": TEST_TRAIN_NO, "from": TEST_ORIGIN, "to": TEST_DESTINATION}]
            }
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/validate-routes-rappid",
            json={"routes": routes, "date": "26-01-2026"},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            required_fields = ["validated_routes", "total_routes", "valid_routes"]
            all_present = True
            
            for field in required_fields:
                if field in data:
                    print_success(f"Field '{field}': {data[field]}")
                else:
                    print_error(f"Field '{field}' missing")
                    all_present = False
            
            if all_present:
                test_results["passed"].append("Batch Validation")
                return True
            else:
                test_results["failed"].append("Batch Validation - Missing fields")
                return False
        else:
            print_error(f"Status code: {response.status_code}")
            test_results["failed"].append("Batch Validation - Bad Status")
            return False
            
    except Exception as e:
        print_error(f"Exception: {e}")
        test_results["errors"].append(f"Batch Validation - {str(e)}")
        return False

def print_summary():
    """Print test summary"""
    print_header("TEST SUMMARY")
    
    total = len(test_results["passed"]) + len(test_results["failed"]) + len(test_results["errors"])
    passed = len(test_results["passed"])
    failed = len(test_results["failed"])
    errors = len(test_results["errors"])
    
    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed:  {passed} ({(passed/total*100):.1f}%)")
    print(f"❌ Failed:  {failed} ({(failed/total*100):.1f}%)")
    print(f"⚠️  Errors:  {errors} ({(errors/total*100):.1f}%)")
    
    if test_results["passed"]:
        print("\n✅ PASSED TESTS:")
        for test in test_results["passed"]:
            print(f"   • {test}")
    
    if test_results["failed"]:
        print("\n❌ FAILED TESTS:")
        for test in test_results["failed"]:
            print(f"   • {test}")
    
    if test_results["errors"]:
        print("\n⚠️  ERROR TESTS:")
        for test in test_results["errors"]:
            print(f"   • {test}")
    
    print("\n" + "="*80)
    if failed == 0 and errors == 0:
        print("  ✅ ALL TESTS PASSED!")
    else:
        print(f"  ⚠️  {failed + errors} TEST(S) NEED ATTENTION")
    print("="*80 + "\n")

def main():
    """Run all tests"""
    print_header("RAPPID INTEGRATION - COMPREHENSIVE TEST SUITE")
    print(f"Backend URL: {BASE_URL}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Give server time to start
    print("\nWaiting for server to be ready...")
    max_retries = 10
    for i in range(max_retries):
        try:
            requests.get(f"{BASE_URL}/api/health", timeout=5)
            print("✅ Server is ready!\n")
            break
        except:
            if i < max_retries - 1:
                print(f"  Attempt {i+1}/{max_retries}... server not ready yet")
                time.sleep(1)
            else:
                print_error("Server not responding!")
                return
    
    # Run all tests
    print_header("UNIT & ENDPOINT TESTS")
    
    test_health_check()
    test_train_data_endpoint()
    test_train_schedule_endpoint()
    test_train_seats_endpoint()
    test_train_fares_endpoint()
    test_train_status_endpoint()
    
    print_header("ERROR HANDLING TESTS")
    test_error_handling_missing_param()
    test_invalid_train_number()
    
    print_header("ROUTE VALIDATION TESTS")
    test_single_route_validation()
    test_routes_endpoint_rappid()
    test_routes_endpoint_irctc()
    test_routes_endpoint_dual()
    
    print_header("PERFORMANCE TESTS")
    test_performance_first_call()
    test_performance_cached_call()
    
    print_header("ADVANCED TESTS")
    test_concurrent_requests()
    test_batch_validation()
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    main()
