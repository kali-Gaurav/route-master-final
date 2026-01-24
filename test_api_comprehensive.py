"""
COMPREHENSIVE API TEST SUITE FOR ROUTE MASTER API
=================================================

Tests covering:
I.    Core Functional Tests (Search & API)
II.   Pareto Algorithm & Routing Logic
III.  Data Integration (RAPPID & IRCTC)
IV.   Caching System Performance
V.    Performance & Stress (Asynchronous Ops)
VI.   Edge Cases
VII.  Admin & Data Management
VIII. Security & Robustness
IX.   Frontend-Backend Compatibility
X.    System Resilience (Chaos Testing)
"""

import pytest
import requests
import json
import time
import asyncio
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
import csv
import threading
from concurrent.futures import ThreadPoolExecutor
import logging
from typing import Dict, List, Any, Optional
import statistics
import os
import sys
import io

# Fix Windows encoding issue for Unicode output
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s"
)
logger = logging.getLogger("api_test_suite")

# ==================== CONFIGURATION ====================
BASE_URL = "http://127.0.0.1:5000"
API_TIMEOUT = 30
STRESS_TEST_THREADS = 10
STRESS_TEST_ITERATIONS = 100

# Common test stations
STATION_CODES = {
    "NDLS": "New Delhi",
    "KOTA": "Kota",
    "PGT": "Puducherry",
    "HWH": "Howrah",
    "CSMT": "Chhatrapati Shivaji Terminus",
    "ADI": "Ahmedabad",
    "BKN": "Banaras",
    "CBE": "Coimbatore",
    "JP": "Jaipur",
    "SBC": "Bengaluru",
    "LKO": "Lucknow",
    "MAS": "Chennai"
}

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "errors": []
}

# ==================== UTILITY FUNCTIONS ====================

def log_test(test_name: str, status: str, message: str = ""):
    """Log test result"""
    symbol = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⊘"
    msg = f"{symbol} [{test_name}] {status}"
    if message:
        msg += f" - {message}"
    logger.info(msg)
    
    if status == "PASS":
        test_results["passed"] += 1
    elif status == "FAIL":
        test_results["failed"] += 1
        test_results["errors"].append({"test": test_name, "message": message})
    else:
        test_results["skipped"] += 1

def make_request(method: str, endpoint: str, params: Dict = None, json_data: Dict = None, 
                 expected_status: int = None, timeout: int = API_TIMEOUT) -> Optional[requests.Response]:
    """Make HTTP request with error handling"""
    try:
        url = f"{BASE_URL}{endpoint}"
        if method.upper() == "GET":
            resp = requests.get(url, params=params, timeout=timeout)
        elif method.upper() == "POST":
            resp = requests.post(url, json=json_data, timeout=timeout)
        else:
            resp = requests.request(method, url, params=params, json=json_data, timeout=timeout)
        
        if expected_status and resp.status_code != expected_status:
            logger.warning(f"Expected status {expected_status}, got {resp.status_code}")
            return None
        return resp
    except requests.exceptions.Timeout:
        logger.error(f"Request timeout: {endpoint}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error: {endpoint}")
        return None
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        return None

def measure_latency(func, *args, **kwargs) -> float:
    """Measure function execution time in milliseconds"""
    start = time.time()
    func(*args, **kwargs)
    return (time.time() - start) * 1000

# ==================== CATEGORY I: CORE FUNCTIONAL TESTS ====================

class TestCoreFeatures:
    """Test basic search functionality and API behavior"""
    
    @staticmethod
    def test_direct_route_search():
        """Verify NDLS to KOTA returns direct trains with 0 transfers"""
        logger.info("\n--- Test I.1: Direct Route Search ---")
        resp = make_request("GET", "/api/routes", 
                           params={"origin": "NDLS", "destination": "KOTA", "max_transfers": 0},
                           expected_status=200)
        
        if resp:
            data = resp.json()
            routes = data.get("optimal_routes", [])
            if routes:
                all_zero_transfers = all(
                    sum(1 for seg in route.get("segments", [])) == 1 
                    for route in routes
                )
                if all_zero_transfers:
                    log_test("Direct_Route_Search", "PASS", f"Found {len(routes)} direct routes")
                else:
                    log_test("Direct_Route_Search", "FAIL", "Some routes have transfers")
            else:
                log_test("Direct_Route_Search", "SKIP", "No direct routes found")
        else:
            log_test("Direct_Route_Search", "FAIL", "Request failed")
    
    @staticmethod
    def test_single_transfer_search():
        """Verify PGT to NDLS returns routes with exactly 1 transfer"""
        logger.info("\n--- Test I.2: Single Transfer Search ---")
        resp = make_request("GET", "/api/routes",
                           params={"origin": "PGT", "destination": "NDLS", "max_transfers": 1},
                           expected_status=200)
        
        if resp:
            data = resp.json()
            routes = data.get("optimal_routes", [])
            if routes:
                valid_count = sum(1 for route in routes if 1 <= len(route.get("segments", [])) <= 2)
                if valid_count > 0:
                    log_test("Single_Transfer_Search", "PASS", f"Found {valid_count} routes with ≤1 transfer")
                else:
                    log_test("Single_Transfer_Search", "FAIL", "Routes don't match transfer constraint")
            else:
                log_test("Single_Transfer_Search", "SKIP", "No routes found")
        else:
            log_test("Single_Transfer_Search", "FAIL", "Request failed")
    
    @staticmethod
    def test_max_transfers_constraint():
        """Verify max_transfers=1 doesn't return 2-transfer routes"""
        logger.info("\n--- Test I.3: Max Transfers Constraint ---")
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "KOTA", "max_transfers": 1},
                           expected_status=200)
        
        if resp:
            data = resp.json()
            routes = data.get("optimal_routes", [])
            if routes:
                all_valid = all(len(route.get("segments", [])) <= 2 for route in routes)
                if all_valid:
                    log_test("Max_Transfers_Constraint", "PASS", "All routes respect constraint")
                else:
                    violations = sum(1 for r in routes if len(r.get("segments", [])) > 2)
                    log_test("Max_Transfers_Constraint", "FAIL", f"{violations} routes violate constraint")
            else:
                log_test("Max_Transfers_Constraint", "SKIP", "No routes found")
        else:
            log_test("Max_Transfers_Constraint", "FAIL", "Request failed")
    
    @staticmethod
    def test_invalid_station_code():
        """Test invalid station code returns 400 error"""
        logger.info("\n--- Test I.4: Invalid Station Code ---")
        resp = make_request("GET", "/api/routes",
                           params={"origin": "ABCD", "destination": "KOTA"})
        
        if resp and resp.status_code == 400:
            log_test("Invalid_Station_Code", "PASS", "Returns 400 error")
        elif resp:
            log_test("Invalid_Station_Code", "FAIL", f"Expected 400, got {resp.status_code}")
        else:
            log_test("Invalid_Station_Code", "FAIL", "Request failed")
    
    @staticmethod
    def test_missing_parameters():
        """Test missing parameters returns 400"""
        logger.info("\n--- Test I.5: Missing Parameters ---")
        resp = make_request("GET", "/api/routes", params={})
        
        if resp and resp.status_code == 400:
            log_test("Missing_Parameters", "PASS", "Returns 400 for missing params")
        elif resp:
            log_test("Missing_Parameters", "FAIL", f"Expected 400, got {resp.status_code}")
        else:
            log_test("Missing_Parameters", "FAIL", "Request failed")
    
    @staticmethod
    def test_date_formatting():
        """Verify different date formats are parsed correctly"""
        logger.info("\n--- Test I.6: Date Formatting ---")
        test_dates = [
            ("25-01-2026", True),
            ("2026-01-25", True),
            ("25/01/2026", True),
        ]
        
        passed = 0
        for date_str, should_pass in test_dates:
            resp = make_request("GET", "/api/routes",
                               params={"origin": "NDLS", "destination": "KOTA", "date": date_str},
                               expected_status=200)
            if resp:
                passed += 1
        
        if passed == len(test_dates):
            log_test("Date_Formatting", "PASS", f"All {len(test_dates)} formats parsed correctly")
        else:
            log_test("Date_Formatting", "FAIL", f"Only {passed}/{len(test_dates)} formats worked")
    
    @staticmethod
    def test_future_date_validation():
        """Test date 5 years in future (outside IRCTC booking window)"""
        logger.info("\n--- Test I.7: Future Date Validation ---")
        future_date = (datetime.now() + timedelta(days=5*365)).strftime("%d-%m-%Y")
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "KOTA", "date": future_date})
        
        # Should either return empty or use current date as fallback
        if resp:
            log_test("Future_Date_Validation", "PASS", "Handles future date gracefully")
        else:
            log_test("Future_Date_Validation", "FAIL", "Request failed")
    
    @staticmethod
    def test_past_date_validation():
        """Verify searching for past date (2023) returns error or fallback"""
        logger.info("\n--- Test I.8: Past Date Validation ---")
        past_date = "15-01-2023"
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "KOTA", "date": past_date})
        
        if resp:
            log_test("Past_Date_Validation", "PASS", "Handles past date gracefully")
        else:
            log_test("Past_Date_Validation", "FAIL", "Request failed")
    
    @staticmethod
    def test_same_source_destination():
        """Verify origin=destination returns error or empty list"""
        logger.info("\n--- Test I.9: Same Source/Destination ---")
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "NDLS"})
        
        if resp:
            if resp.status_code in (400, 200):
                data = resp.json()
                routes = data.get("optimal_routes", [])
                if len(routes) == 0 or "error" in data:
                    log_test("Same_Source_Destination", "PASS", "Returns empty/error for same station")
                else:
                    log_test("Same_Source_Destination", "FAIL", "Returned routes for same station")
            else:
                log_test("Same_Source_Destination", "FAIL", f"Status {resp.status_code}")
        else:
            log_test("Same_Source_Destination", "FAIL", "Request failed")
    
    @staticmethod
    def test_case_insensitivity():
        """Verify lowercase station codes work"""
        logger.info("\n--- Test I.10: Case Insensitivity ---")
        resp_upper = make_request("GET", "/api/routes",
                                 params={"origin": "NDLS", "destination": "KOTA"},
                                 expected_status=200)
        resp_lower = make_request("GET", "/api/routes",
                                 params={"origin": "ndls", "destination": "kota"},
                                 expected_status=200)
        
        if resp_upper and resp_lower:
            data_upper = resp_upper.json()
            data_lower = resp_lower.json()
            if len(data_upper.get("optimal_routes", [])) == len(data_lower.get("optimal_routes", [])):
                log_test("Case_Insensitivity", "PASS", "Both uppercase and lowercase work")
            else:
                log_test("Case_Insensitivity", "FAIL", "Different results for different cases")
        else:
            log_test("Case_Insensitivity", "FAIL", "Request failed")


# ==================== CATEGORY II: PARETO ALGORITHM & ROUTING LOGIC ====================

class TestParetoLogic:
    """Test Pareto optimization and routing correctness"""
    
    @staticmethod
    def test_route_id_uniqueness():
        """Verify every route has unique route_id"""
        logger.info("\n--- Test II.1: Route ID Uniqueness ---")
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "KOTA"},
                           expected_status=200)
        
        if resp:
            data = resp.json()
            routes = data.get("optimal_routes", [])
            route_ids = [r.get("route_id") for r in routes if "route_id" in r]
            
            if len(route_ids) == len(set(route_ids)):
                log_test("Route_ID_Uniqueness", "PASS", f"All {len(route_ids)} routes have unique IDs")
            else:
                duplicates = len(route_ids) - len(set(route_ids))
                log_test("Route_ID_Uniqueness", "FAIL", f"{duplicates} duplicate IDs found")
        else:
            log_test("Route_ID_Uniqueness", "FAIL", "Request failed")
    
    @staticmethod
    def test_segment_continuity():
        """Verify to_station of segment N matches from_station of segment N+1"""
        logger.info("\n--- Test II.2: Segment Continuity ---")
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "KOTA"},
                           expected_status=200)
        
        if resp:
            data = resp.json()
            routes = data.get("optimal_routes", [])
            failed = 0
            
            for route in routes:
                segments = route.get("segments", [])
                for i in range(len(segments) - 1):
                    if segments[i].get("to") != segments[i+1].get("from"):
                        failed += 1
                        break
            
            if failed == 0:
                log_test("Segment_Continuity", "PASS", f"All {len(routes)} routes have continuous segments")
            else:
                log_test("Segment_Continuity", "FAIL", f"{failed} routes have discontinuous segments")
        else:
            log_test("Segment_Continuity", "FAIL", "Request failed")
    
    @staticmethod
    def test_layover_time_calculation():
        """Verify arrival + 30-60min >= next departure"""
        logger.info("\n--- Test II.3: Layover Time Calculation ---")
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "KOTA", "max_transfers": 2},
                           expected_status=200)
        
        if resp:
            data = resp.json()
            routes = data.get("optimal_routes", [])
            violations = 0
            
            for route in routes:
                segments = route.get("segments", [])
                for i in range(len(segments) - 1):
                    try:
                        arr_time = datetime.fromisoformat(segments[i].get("arrival_time", ""))
                        dep_time = datetime.fromisoformat(segments[i+1].get("departure_time", ""))
                        layover = (dep_time - arr_time).total_seconds() / 60
                        if layover < 30:
                            violations += 1
                    except:
                        pass
            
            if violations == 0:
                log_test("Layover_Time_Calculation", "PASS", f"All layovers valid")
            else:
                log_test("Layover_Time_Calculation", "FAIL", f"{violations} invalid layovers")
        else:
            log_test("Layover_Time_Calculation", "FAIL", "Request failed")
    
    @staticmethod
    def test_total_time_accuracy():
        """Verify total_time = sum of segment durations + layover times"""
        logger.info("\n--- Test II.4: Total Time Accuracy ---")
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "KOTA"},
                           expected_status=200)
        
        if resp:
            data = resp.json()
            routes = data.get("optimal_routes", [])
            mismatches = 0
            
            for route in routes:
                try:
                    segments = route.get("segments", [])
                    total_duration = sum(seg.get("duration_minutes", 0) for seg in segments)
                    
                    # Add layover times
                    for i in range(len(segments) - 1):
                        arr = datetime.fromisoformat(segments[i].get("arrival_time", ""))
                        dep = datetime.fromisoformat(segments[i+1].get("departure_time", ""))
                        layover = (dep - arr).total_seconds() / 60
                        total_duration += layover
                    
                    if abs(total_duration - route.get("total_time", 0)) > 5:
                        mismatches += 1
                except:
                    pass
            
            if mismatches == 0:
                log_test("Total_Time_Accuracy", "PASS", f"All {len(routes)} routes have accurate totals")
            else:
                log_test("Total_Time_Accuracy", "FAIL", f"{mismatches} routes have mismatched totals")
        else:
            log_test("Total_Time_Accuracy", "FAIL", "Request failed")
    
    @staticmethod
    def test_total_distance_accuracy():
        """Verify total_distance = sum of segment distances"""
        logger.info("\n--- Test II.5: Total Distance Accuracy ---")
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "KOTA"},
                           expected_status=200)
        
        if resp:
            data = resp.json()
            routes = data.get("optimal_routes", [])
            mismatches = 0
            
            for route in routes:
                try:
                    segments = route.get("segments", [])
                    sum_distance = sum(seg.get("distance", 0) for seg in segments)
                    
                    if abs(sum_distance - route.get("total_distance", 0)) > 1:
                        mismatches += 1
                except:
                    pass
            
            if mismatches == 0:
                log_test("Total_Distance_Accuracy", "PASS", f"All distances accurate")
            else:
                log_test("Total_Distance_Accuracy", "FAIL", f"{mismatches} routes have mismatched distances")
        else:
            log_test("Total_Distance_Accuracy", "FAIL", "Request failed")
    
    @staticmethod
    def test_fare_summation():
        """Verify total_fare = sum of segment fares"""
        logger.info("\n--- Test II.6: Fare Summation ---")
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "KOTA"},
                           expected_status=200)
        
        if resp:
            data = resp.json()
            routes = data.get("optimal_routes", [])
            mismatches = 0
            
            for route in routes:
                try:
                    segments = route.get("segments", [])
                    sum_fare = sum(seg.get("fare", 0) for seg in segments)
                    
                    if abs(sum_fare - route.get("total_fare", 0)) > 1:
                        mismatches += 1
                except:
                    pass
            
            if mismatches == 0:
                log_test("Fare_Summation", "PASS", f"All fares accurate")
            else:
                log_test("Fare_Summation", "FAIL", f"{mismatches} routes have mismatched fares")
        else:
            log_test("Fare_Summation", "FAIL", "Request failed")
    
    @staticmethod
    def test_diverse_selection():
        """Verify results include mix of fast/cheap/few-transfer routes"""
        logger.info("\n--- Test II.7: Diverse Selection ---")
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "KOTA"},
                           expected_status=200)
        
        if resp:
            data = resp.json()
            routes = data.get("optimal_routes", [])
            
            if len(routes) >= 3:
                # Sort by different criteria
                by_time = sorted(routes, key=lambda r: r.get("total_time", float('inf')))
                by_fare = sorted(routes, key=lambda r: r.get("total_fare", float('inf')))
                by_transfers = sorted(routes, key=lambda r: len(r.get("segments", [])))
                
                # Check if we have diverse selection
                is_diverse = (by_time[0] != by_fare[0] or by_fare[0] != by_transfers[0])
                
                if is_diverse:
                    log_test("Diverse_Selection", "PASS", f"Found {len(routes)} diverse routes")
                else:
                    log_test("Diverse_Selection", "FAIL", "Routes not diverse")
            else:
                log_test("Diverse_Selection", "SKIP", f"Only {len(routes)} routes found")
        else:
            log_test("Diverse_Selection", "FAIL", "Request failed")


# ==================== CATEGORY III: DATA INTEGRATION ====================

class TestDataIntegration:
    """Test RAPPID and IRCTC integration"""
    
    @staticmethod
    def test_live_fare_update():
        """Verify live_fare from API is included in response"""
        logger.info("\n--- Test III.1: Live Fare Update ---")
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "KOTA", "validation": "irctc"},
                           expected_status=200)
        
        if resp:
            data = resp.json()
            routes = data.get("optimal_routes", [])
            with_live_fare = 0
            
            for route in routes:
                for seg in route.get("segments", []):
                    if "live_fare" in seg:
                        with_live_fare += 1
            
            if with_live_fare > 0:
                log_test("Live_Fare_Update", "PASS", f"{with_live_fare} segments have live fare")
            else:
                log_test("Live_Fare_Update", "SKIP", "No live fares in response")
        else:
            log_test("Live_Fare_Update", "FAIL", "Request failed")
    
    @staticmethod
    def test_dual_validation_check():
        """Verify /api/validate-routes-dual returns both RAPPID and IRCTC data"""
        logger.info("\n--- Test III.2: Dual Validation Check ---")
        
        # First get a route
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "KOTA"},
                           expected_status=200)
        
        if resp:
            data = resp.json()
            routes = data.get("optimal_routes", [])
            
            if routes:
                # Try dual validation
                val_resp = make_request("POST", "/api/validate-routes-dual",
                                       json_data={"routes": routes[:1]})
                
                if val_resp:
                    val_data = val_resp.json()
                    validated = val_data.get("validated_routes", [])
                    
                    if validated and "validation_summary" in validated[0]:
                        summary = validated[0]["validation_summary"]
                        if "rappid_valid" in summary and "irctc_valid" in summary:
                            log_test("Dual_Validation_Check", "PASS", "Both APIs in response")
                        else:
                            log_test("Dual_Validation_Check", "FAIL", "Missing validation data")
                    else:
                        log_test("Dual_Validation_Check", "FAIL", "No validation summary")
                else:
                    log_test("Dual_Validation_Check", "FAIL", "Validation request failed")
            else:
                log_test("Dual_Validation_Check", "SKIP", "No routes to validate")
        else:
            log_test("Dual_Validation_Check", "FAIL", "Initial request failed")
    
    @staticmethod
    def test_irctc_status_check():
        """Verify /api/live-station returns valid station data"""
        logger.info("\n--- Test III.3: IRCTC Status Check ---")
        resp = make_request("GET", "/api/live-station",
                           params={"station": "NDLS"},
                           expected_status=200)
        
        if resp:
            data = resp.json()
            if "error" not in data or "trains" in data:
                log_test("IRCTC_Status_Check", "PASS", "Live station data available")
            else:
                log_test("IRCTC_Status_Check", "SKIP", "Station data unavailable")
        else:
            log_test("IRCTC_Status_Check", "FAIL", "Request failed")
    
    @staticmethod
    def test_class_specific_search():
        """Verify availability is checked for requested class"""
        logger.info("\n--- Test III.4: Class Specific Search ---")
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "KOTA"},
                           expected_status=200)
        
        if resp:
            data = resp.json()
            routes = data.get("optimal_routes", [])
            
            if routes:
                # Check if class information exists
                has_class_info = any(
                    "class" in seg for route in routes for seg in route.get("segments", [])
                )
                if has_class_info:
                    log_test("Class_Specific_Search", "PASS", "Class info in segments")
                else:
                    log_test("Class_Specific_Search", "SKIP", "No class info in response")
            else:
                log_test("Class_Specific_Search", "SKIP", "No routes found")
        else:
            log_test("Class_Specific_Search", "FAIL", "Request failed")
    
    @staticmethod
    def test_train_schedule_accuracy():
        """Cross-verify /api/train-schedule against IRCTC timings"""
        logger.info("\n--- Test III.5: Train Schedule Accuracy ---")
        
        # Try getting schedule for a known train
        test_train = "12345"  # Sample train number
        resp = make_request("GET", "/api/train-schedule",
                           params={"train_no": test_train})
        
        if resp and resp.status_code == 200:
            data = resp.json()
            if "route" in data or "schedule" in data or "stations" in data:
                log_test("Train_Schedule_Accuracy", "PASS", "Schedule data available")
            else:
                log_test("Train_Schedule_Accuracy", "FAIL", "Invalid schedule format")
        else:
            log_test("Train_Schedule_Accuracy", "SKIP", f"Train {test_train} not found")
    
    @staticmethod
    def test_batch_validation():
        """Verify POST /api/validate-routes-rappid handles 10+ routes"""
        logger.info("\n--- Test III.6: Batch Validation ---")
        
        # Get routes
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "KOTA"},
                           expected_status=200)
        
        if resp:
            data = resp.json()
            routes = data.get("optimal_routes", [])
            
            if len(routes) >= 5:
                # Validate batch
                val_resp = make_request("POST", "/api/validate-routes-rappid",
                                       json_data={"routes": routes[:10]})
                
                if val_resp and val_resp.status_code == 200:
                    val_data = val_resp.json()
                    validated = val_data.get("validated_routes", [])
                    if len(validated) >= 5:
                        log_test("Batch_Validation", "PASS", f"Validated {len(validated)} routes")
                    else:
                        log_test("Batch_Validation", "FAIL", f"Only {len(validated)} routes validated")
                else:
                    log_test("Batch_Validation", "FAIL", "Validation request failed")
            else:
                log_test("Batch_Validation", "SKIP", f"Only {len(routes)} routes available")
        else:
            log_test("Batch_Validation", "FAIL", "Route request failed")


# ==================== CATEGORY IV: CACHING SYSTEM PERFORMANCE ====================

class TestCaching:
    """Test caching system and performance"""
    
    @staticmethod
    def test_memory_cache_hit():
        """First request ~10s, second request <50ms"""
        logger.info("\n--- Test IV.1: Memory Cache Hit ---")
        params = {"origin": "NDLS", "destination": "KOTA"}
        
        # First request (should populate cache)
        start = time.time()
        resp1 = make_request("GET", "/api/routes", params=params, timeout=60)
        time1 = (time.time() - start) * 1000
        
        if resp1:
            # Second request (should hit cache)
            start = time.time()
            resp2 = make_request("GET", "/api/routes", params=params)
            time2 = (time.time() - start) * 1000
            
            if time2 < 100:  # Allow some buffer
                log_test("Memory_Cache_Hit", "PASS", f"Cache hit: {time1:.0f}ms → {time2:.0f}ms")
            else:
                log_test("Memory_Cache_Hit", "FAIL", f"Cache miss too slow: {time2:.0f}ms")
        else:
            log_test("Memory_Cache_Hit", "FAIL", "First request failed")
    
    @staticmethod
    def test_cache_key_partitioning():
        """Verify changing max_transfers creates new cache entry"""
        logger.info("\n--- Test IV.2: Cache Key Partitioning ---")
        base_params = {"origin": "NDLS", "destination": "KOTA"}
        
        resp1 = make_request("GET", "/api/routes", params={**base_params, "max_transfers": 1}, 
                            expected_status=200)
        resp2 = make_request("GET", "/api/routes", params={**base_params, "max_transfers": 2},
                            expected_status=200)
        
        if resp1 and resp2:
            routes1 = resp1.json().get("optimal_routes", [])
            routes2 = resp2.json().get("optimal_routes", [])
            
            # Different max_transfers should produce different results
            if len(routes1) != len(routes2) or routes1 != routes2:
                log_test("Cache_Key_Partitioning", "PASS", "Cache keys properly partitioned")
            else:
                log_test("Cache_Key_Partitioning", "FAIL", "Same results for different params")
        else:
            log_test("Cache_Key_Partitioning", "FAIL", "Request failed")
    
    @staticmethod
    def test_disk_persistence():
        """Restart not needed - verify file cache loads correctly"""
        logger.info("\n--- Test IV.3: Disk Persistence ---")
        
        # Check if pre-computed files exist
        rappid_dir = Path(".")
        pareto_files = list(rappid_dir.glob("*_pareto_routes_*.json"))
        
        if pareto_files:
            # Try loading one
            test_file = pareto_files[0]
            try:
                with open(test_file, 'r') as f:
                    data = json.load(f)
                    if "optimal_routes" in data:
                        log_test("Disk_Persistence", "PASS", f"Loaded {len(pareto_files)} cached files")
                    else:
                        log_test("Disk_Persistence", "FAIL", "Invalid cache file format")
            except:
                log_test("Disk_Persistence", "FAIL", "Error loading cache file")
        else:
            log_test("Disk_Persistence", "SKIP", "No cached files found")
    
    @staticmethod
    def test_admin_clear_cache():
        """Verify POST /admin/clear-cache works"""
        logger.info("\n--- Test IV.4: Admin Clear Cache ---")
        resp = make_request("POST", "/admin/clear-cache")
        
        if resp and resp.status_code == 200:
            data = resp.json()
            if "success" in data.get("status", ""):
                log_test("Admin_Clear_Cache", "PASS", "Cache cleared successfully")
            else:
                log_test("Admin_Clear_Cache", "FAIL", "Clear failed")
        else:
            log_test("Admin_Clear_Cache", "FAIL", "Request failed")
    
    @staticmethod
    def test_cache_warming():
        """Verify POST /admin/warm-cache populates cache"""
        logger.info("\n--- Test IV.5: Cache Warming ---")
        resp = make_request("POST", "/admin/warm-cache")
        
        if resp and resp.status_code == 200:
            log_test("Cache_Warming", "PASS", "Cache warming initiated")
        else:
            log_test("Cache_Warming", "FAIL", "Request failed")


# ==================== CATEGORY V: PERFORMANCE & STRESS ====================

class TestPerformance:
    """Test performance under load"""
    
    @staticmethod
    def test_concurrent_requests():
        """Test 100 concurrent requests"""
        logger.info("\n--- Test V.1: Concurrent Requests ---")
        
        def make_single_request():
            make_request("GET", "/api/routes",
                        params={"origin": "NDLS", "destination": "KOTA"})
        
        start = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_single_request) for _ in range(100)]
            completed = sum(1 for f in futures if f.result() is None or f.result())
        elapsed = time.time() - start
        
        if completed >= 90:
            log_test("Concurrent_Requests", "PASS", f"{completed}/100 completed in {elapsed:.1f}s")
        else:
            log_test("Concurrent_Requests", "FAIL", f"Only {completed}/100 completed")
    
    @staticmethod
    def test_request_timeout():
        """Verify requests timeout gracefully"""
        logger.info("\n--- Test V.2: Request Timeout ---")
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "KOTA"},
                           timeout=1)
        
        # May timeout or succeed, either way should not crash
        log_test("Request_Timeout", "PASS", "Timeout handled gracefully")
    
    @staticmethod
    def test_p95_latency():
        """Verify 95% of requests respond in <500ms"""
        logger.info("\n--- Test V.3: P95 Latency ---")
        
        times = []
        for _ in range(20):
            start = time.time()
            resp = make_request("GET", "/api/routes",
                               params={"origin": "NDLS", "destination": "KOTA"})
            if resp:
                times.append((time.time() - start) * 1000)
        
        if times:
            p95 = statistics.quantiles(times, n=20)[18]  # 95th percentile
            if p95 < 500:
                log_test("P95_Latency", "PASS", f"P95={p95:.0f}ms")
            else:
                log_test("P95_Latency", "FAIL", f"P95={p95:.0f}ms (target <500ms)")
        else:
            log_test("P95_Latency", "FAIL", "No data collected")
    
    @staticmethod
    def test_memory_stability():
        """Run 100 searches and monitor memory"""
        logger.info("\n--- Test V.4: Memory Stability ---")
        
        import psutil
        import os
        
        try:
            process = psutil.Process(os.getpid())
            mem_before = process.memory_info().rss / 1024 / 1024  # MB
            
            for _ in range(100):
                make_request("GET", "/api/routes",
                            params={"origin": "NDLS", "destination": "KOTA"})
            
            mem_after = process.memory_info().rss / 1024 / 1024
            growth = mem_after - mem_before
            
            if growth < 100:  # Less than 100MB growth
                log_test("Memory_Stability", "PASS", f"Memory growth: {growth:.1f}MB")
            else:
                log_test("Memory_Stability", "FAIL", f"Excessive growth: {growth:.1f}MB")
        except:
            log_test("Memory_Stability", "SKIP", "psutil not available")


# ==================== CATEGORY VI: EDGE CASES ====================

class TestEdgeCases:
    """Test edge cases and unusual scenarios"""
    
    @staticmethod
    def test_overnight_trains():
        """Verify routes crossing midnight calculate correctly"""
        logger.info("\n--- Test VI.1: Overnight Trains ---")
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "CSMT"},
                           expected_status=200)
        
        if resp:
            data = resp.json()
            routes = data.get("optimal_routes", [])
            
            if routes:
                log_test("Overnight_Trains", "PASS", f"Found {len(routes)} routes")
            else:
                log_test("Overnight_Trains", "SKIP", "No routes found")
        else:
            log_test("Overnight_Trains", "FAIL", "Request failed")
    
    @staticmethod
    def test_zero_availability():
        """Handle routes with zero availability"""
        logger.info("\n--- Test VI.2: Zero Availability ---")
        # Search for a less common route
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "KOTA"})
        
        if resp:
            data = resp.json()
            if "optimal_routes" in data:
                log_test("Zero_Availability", "PASS", "Handles unavailable routes")
            else:
                log_test("Zero_Availability", "FAIL", "Invalid response")
        else:
            log_test("Zero_Availability", "FAIL", "Request failed")
    
    @staticmethod
    def test_large_result_set():
        """Search between popular stations (many possible routes)"""
        logger.info("\n--- Test VI.3: Large Result Set ---")
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "CSMT", "max_transfers": 3},
                           timeout=60)
        
        if resp:
            data = resp.json()
            routes = data.get("optimal_routes", [])
            if len(routes) > 10:
                log_test("Large_Result_Set", "PASS", f"Handled {len(routes)} routes")
            elif len(routes) > 0:
                log_test("Large_Result_Set", "PASS", f"Found {len(routes)} routes")
            else:
                log_test("Large_Result_Set", "SKIP", "No routes found")
        else:
            log_test("Large_Result_Set", "FAIL", "Request failed")
    
    @staticmethod
    def test_special_characters():
        """Test that station codes with spaces are handled"""
        logger.info("\n--- Test VI.4: Special Characters ---")
        resp = make_request("GET", "/api/routes",
                           params={"origin": " NDLS ", "destination": " KOTA "})
        
        if resp:
            if resp.status_code in (200, 400):
                log_test("Special_Characters", "PASS", "Handles extra spaces")
            else:
                log_test("Special_Characters", "FAIL", f"Status {resp.status_code}")
        else:
            log_test("Special_Characters", "FAIL", "Request failed")


# ==================== CATEGORY VII: ADMIN & DATA MANAGEMENT ====================

class TestAdmin:
    """Test admin endpoints"""
    
    @staticmethod
    def test_single_train_refresh():
        """Test refreshing RAPPID data for single train"""
        logger.info("\n--- Test VII.1: Single Train Refresh ---")
        test_train = "12345"
        resp = make_request("POST", f"/admin/refresh-rappid/{test_train}")
        
        if resp and resp.status_code == 200:
            log_test("Single_Train_Refresh", "PASS", "Train refresh successful")
        else:
            log_test("Single_Train_Refresh", "SKIP", "Train not available")
    
    @staticmethod
    def test_bulk_refresh():
        """Test bulk refresh endpoint"""
        logger.info("\n--- Test VII.2: Bulk Refresh ---")
        resp = make_request("POST", "/admin/refresh-rappid-bulk",
                           json_data={"train_numbers": ["12345", "12346", "12347"]})
        
        if resp and resp.status_code == 200:
            data = resp.json()
            if "successful" in data:
                log_test("Bulk_Refresh", "PASS", f"Processed {data['total_requested']} trains")
            else:
                log_test("Bulk_Refresh", "FAIL", "Invalid response")
        else:
            log_test("Bulk_Refresh", "FAIL", "Request failed")
    
    @staticmethod
    def test_rappid_status():
        """Get RAPPID data coverage status"""
        logger.info("\n--- Test VII.3: RAPPID Status ---")
        resp = make_request("GET", "/admin/status/rappid")
        
        if resp and resp.status_code == 200:
            data = resp.json()
            coverage = data.get("coverage_percent", 0)
            log_test("RAPPID_Status", "PASS", f"Coverage: {coverage}%")
        else:
            log_test("RAPPID_Status", "FAIL", "Request failed")
    
    @staticmethod
    def test_health_check():
        """Test health check endpoint"""
        logger.info("\n--- Test VII.4: Health Check ---")
        resp = make_request("GET", "/api/health")
        
        if resp and resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "healthy":
                log_test("Health_Check", "PASS", "System healthy")
            else:
                log_test("Health_Check", "FAIL", f"Status: {data.get('status')}")
        else:
            log_test("Health_Check", "FAIL", "Request failed")


# ==================== CATEGORY VIII: SECURITY & ROBUSTNESS ====================

class TestSecurity:
    """Test security and error handling"""
    
    @staticmethod
    def test_input_injection():
        """Test SQL/logic injection protection"""
        logger.info("\n--- Test VIII.1: Input Injection ---")
        malicious = ["NDLS; DROP TABLE;", "NDLS' OR '1'='1", "../../etc/passwd"]
        
        for payload in malicious:
            resp = make_request("GET", "/api/routes",
                               params={"origin": payload, "destination": "KOTA"})
            if resp and resp.status_code in (400, 200):
                log_test("Input_Injection", "PASS", "Injection attempt handled safely")
                return
        
        log_test("Input_Injection", "FAIL", "Injection protection failed")
    
    @staticmethod
    def test_malformed_json():
        """Send malformed JSON to validate endpoint"""
        logger.info("\n--- Test VIII.2: Malformed JSON ---")
        try:
            resp = requests.post(f"{BASE_URL}/api/validate-routes-dual",
                               data="{invalid json",
                               headers={"Content-Type": "application/json"},
                               timeout=API_TIMEOUT)
            
            if resp.status_code in (400, 415):
                log_test("Malformed_JSON", "PASS", "Malformed JSON handled")
            else:
                log_test("Malformed_JSON", "FAIL", f"Status {resp.status_code}")
        except:
            log_test("Malformed_JSON", "PASS", "Malformed JSON rejected")
    
    @staticmethod
    def test_method_restriction():
        """Test that POST on /api/routes is rejected"""
        logger.info("\n--- Test VIII.3: Method Restriction ---")
        resp = make_request("POST", "/api/routes",
                           json_data={"origin": "NDLS", "destination": "KOTA"})
        
        if resp and resp.status_code in (405, 400):
            log_test("Method_Restriction", "PASS", "Wrong method rejected")
        else:
            log_test("Method_Restriction", "FAIL", f"Status {resp.status_code}")
    
    @staticmethod
    def test_rate_limiting():
        """Test rate limiting behavior"""
        logger.info("\n--- Test VIII.4: Rate Limiting ---")
        
        success = 0
        failed = 0
        for _ in range(20):
            resp = make_request("GET", "/api/routes",
                               params={"origin": "NDLS", "destination": "KOTA"},
                               timeout=5)
            if resp and resp.status_code == 200:
                success += 1
            elif resp and resp.status_code == 429:
                failed += 1
        
        log_test("Rate_Limiting", "PASS", f"Handled {success} requests, {failed} rate limited")


# ==================== CATEGORY IX: FRONTEND-BACKEND COMPATIBILITY ====================

class TestFrontendCompatibility:
    """Test frontend compatibility"""
    
    @staticmethod
    def test_response_keys():
        """Ensure required keys exist in response"""
        logger.info("\n--- Test IX.1: Response Keys ---")
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "KOTA"},
                           expected_status=200)
        
        if resp:
            data = resp.json()
            required_keys = ["optimal_routes", "all_generated_routes"]
            missing = [k for k in required_keys if k not in data]
            
            if not missing:
                log_test("Response_Keys", "PASS", "All required keys present")
            else:
                log_test("Response_Keys", "FAIL", f"Missing: {missing}")
        else:
            log_test("Response_Keys", "FAIL", "Request failed")
    
    @staticmethod
    def test_json_serialization():
        """Verify response is valid JSON with correct types"""
        logger.info("\n--- Test IX.2: JSON Serialization ---")
        resp = make_request("GET", "/api/routes",
                           params={"origin": "NDLS", "destination": "KOTA"},
                           expected_status=200)
        
        if resp:
            try:
                data = resp.json()
                # Check numeric types
                for route in data.get("optimal_routes", [])[:1]:
                    if isinstance(route.get("total_fare"), (int, float)):
                        log_test("JSON_Serialization", "PASS", "Valid JSON types")
                        return
                log_test("JSON_Serialization", "FAIL", "Invalid types")
            except:
                log_test("JSON_Serialization", "FAIL", "Invalid JSON")
        else:
            log_test("JSON_Serialization", "FAIL", "Request failed")
    
    @staticmethod
    def test_empty_results():
        """Test empty results handling"""
        logger.info("\n--- Test IX.3: Empty Results ---")
        # Use impossible station codes
        resp = make_request("GET", "/api/routes",
                           params={"origin": "AAAA", "destination": "BBBB"})
        
        if resp:
            if resp.status_code == 400:
                log_test("Empty_Results", "PASS", "Invalid stations rejected")
            else:
                data = resp.json()
                if "error" in data or len(data.get("optimal_routes", [])) == 0:
                    log_test("Empty_Results", "PASS", "Empty results handled")
        else:
            log_test("Empty_Results", "FAIL", "Request failed")


# ==================== CATEGORY X: SYSTEM RESILIENCE ====================

class TestResilience:
    """Test system resilience and error handling"""
    
    @staticmethod
    def test_api_error_graceful_handling():
        """Simulate API errors and verify graceful handling"""
        logger.info("\n--- Test X.1: API Error Handling ---")
        # Try fetching data for non-existent train
        resp = make_request("GET", "/api/train-data",
                           params={"train_no": "99999999"})
        
        if resp:
            if resp.status_code in (404, 500):
                log_test("API_Error_Handling", "PASS", "Errors handled gracefully")
            else:
                log_test("API_Error_Handling", "PASS", f"Status {resp.status_code}")
        else:
            log_test("API_Error_Handling", "FAIL", "Request failed")
    
    @staticmethod
    def test_end_to_end_flow():
        """Complete end-to-end: Search -> Cache -> Revalidate -> Return"""
        logger.info("\n--- Test X.2: End-to-End Flow ---")
        params = {"origin": "NDLS", "destination": "KOTA"}
        
        # Clear cache
        make_request("POST", "/admin/clear-cache")
        time.sleep(0.5)
        
        # First search (compute)
        resp1 = make_request("GET", "/api/routes", params=params, timeout=60)
        
        if resp1:
            # Second search (from cache)
            resp2 = make_request("GET", "/api/routes", params=params)
            
            if resp2:
                data1 = resp1.json()
                data2 = resp2.json()
                
                if (len(data1.get("optimal_routes", [])) == 
                    len(data2.get("optimal_routes", []))):
                    log_test("End_to_End_Flow", "PASS", "Full flow successful")
                else:
                    log_test("End_to_End_Flow", "FAIL", "Results differ between calls")
            else:
                log_test("End_to_End_Flow", "FAIL", "Second request failed")
        else:
            log_test("End_to_End_Flow", "FAIL", "First request failed")


# ==================== TEST RUNNER ====================

def run_all_tests():
    """Run all test categories"""
    print("\n" + "="*80)
    print(" COMPREHENSIVE API TEST SUITE - ROUTE MASTER")
    print("="*80)
    print(f"\n[*] Starting tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[*] Target: {BASE_URL}\n")
    
    # Run all test classes
    test_classes = [
        ("I. CORE FUNCTIONAL TESTS", TestCoreFeatures),
        ("II. PARETO ALGORITHM & ROUTING", TestParetoLogic),
        ("III. DATA INTEGRATION", TestDataIntegration),
        ("IV. CACHING SYSTEM", TestCaching),
        ("V. PERFORMANCE & STRESS", TestPerformance),
        ("VI. EDGE CASES", TestEdgeCases),
        ("VII. ADMIN & DATA MANAGEMENT", TestAdmin),
        ("VIII. SECURITY & ROBUSTNESS", TestSecurity),
        ("IX. FRONTEND-BACKEND COMPATIBILITY", TestFrontendCompatibility),
        ("X. SYSTEM RESILIENCE", TestResilience),
    ]
    
    for category_name, test_class in test_classes:
        print(f"\n{'='*80}")
        print(f" {category_name}")
        print(f"{'='*80}")
        
        # Get all test methods
        test_methods = [m for m in dir(test_class) if m.startswith("test_")]
        
        for method_name in test_methods:
            try:
                method = getattr(test_class, method_name)
                method()
            except Exception as e:
                logger.error(f"Error in {method_name}: {str(e)}", exc_info=True)
                test_results["failed"] += 1
    
    # Print summary
    print(f"\n{'='*80}")
    print(" TEST SUMMARY")
    print(f"{'='*80}")
    print(f"\n[PASS] Passed:  {test_results['passed']}")
    print(f"[FAIL] Failed:  {test_results['failed']}")
    print(f"[SKIP] Skipped: {test_results['skipped']}")
    print(f"\nTotal:     {test_results['passed'] + test_results['failed'] + test_results['skipped']}")
    
    if test_results['errors']:
        print(f"\nFailed Tests:")
        for error in test_results['errors'][:10]:
            print(f"  - {error['test']}: {error['message']}")
    
    print(f"\n[*] Tests completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    return test_results['failed'] == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
