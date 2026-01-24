# QUICK TEST REFERENCE - ROUTE MASTER API

## Installation & Setup (2 minutes)

```bash
# Navigate to project directory
cd c:\Users\Gaurav Nagar\OneDrive\Documents\testingfolder_v3\route-master-final

# Install dependencies
pip install requests pytest pytest-asyncio psutil

# Terminal 1: Start API server
python api.py

# Terminal 2: Run tests
python test_api_comprehensive.py
```

## Common Test Scenarios

### Scenario 1: Quick Smoke Test (All Categories)
```bash
# Runs all tests with brief summary
python test_api_comprehensive.py

# Expected: ~80 tests covering all categories
# Duration: ~5-10 minutes
```

### Scenario 2: Focus on Route Search (Category I)
```python
# Python script
from test_api_comprehensive import TestCoreFeatures

print("\n=== CORE FUNCTIONAL TESTS ===\n")
TestCoreFeatures.test_direct_route_search()
TestCoreFeatures.test_single_transfer_search()
TestCoreFeatures.test_max_transfers_constraint()
TestCoreFeatures.test_invalid_station_code()
TestCoreFeatures.test_missing_parameters()
TestCoreFeatures.test_date_formatting()
TestCoreFeatures.test_future_date_validation()
TestCoreFeatures.test_past_date_validation()
TestCoreFeatures.test_same_source_destination()
TestCoreFeatures.test_case_insensitivity()
```

### Scenario 3: Validate Algorithm (Category II)
```python
# Python script
from test_api_comprehensive import TestParetoLogic

print("\n=== PARETO ALGORITHM VALIDATION ===\n")
TestParetoLogic.test_route_id_uniqueness()
TestParetoLogic.test_segment_continuity()
TestParetoLogic.test_layover_time_calculation()
TestParetoLogic.test_total_time_accuracy()
TestParetoLogic.test_total_distance_accuracy()
TestParetoLogic.test_fare_summation()
TestParetoLogic.test_diverse_selection()
```

### Scenario 4: API Integration Check (Category III)
```python
# Python script
from test_api_comprehensive import TestDataIntegration

print("\n=== DATA INTEGRATION TESTS ===\n")
TestDataIntegration.test_live_fare_update()
TestDataIntegration.test_dual_validation_check()
TestDataIntegration.test_irctc_status_check()
TestDataIntegration.test_class_specific_search()
TestDataIntegration.test_train_schedule_accuracy()
TestDataIntegration.test_batch_validation()
```

### Scenario 5: Performance Testing (Category V)
```python
# Python script
from test_api_comprehensive import TestPerformance

print("\n=== PERFORMANCE TESTS ===\n")
TestPerformance.test_concurrent_requests()
TestPerformance.test_request_timeout()
TestPerformance.test_p95_latency()
TestPerformance.test_memory_stability()
```

### Scenario 6: Cache Testing (Category IV)
```python
# Python script
from test_api_comprehensive import TestCaching
import requests

print("\n=== CACHE PERFORMANCE TESTS ===\n")

# Clear cache first
requests.post("http://127.0.0.1:5000/admin/clear-cache")
print("✓ Cache cleared\n")

# Test cache hit
TestCaching.test_memory_cache_hit()
TestCaching.test_cache_key_partitioning()
TestCaching.test_disk_persistence()
TestCaching.test_admin_clear_cache()
TestCaching.test_cache_warming()
```

### Scenario 7: Admin Operations (Category VII)
```python
# Python script
from test_api_comprehensive import TestAdmin

print("\n=== ADMIN OPERATIONS ===\n")
TestAdmin.test_single_train_refresh()
TestAdmin.test_bulk_refresh()
TestAdmin.test_rappid_status()
TestAdmin.test_health_check()
```

### Scenario 8: Security Testing (Category VIII)
```python
# Python script
from test_api_comprehensive import TestSecurity

print("\n=== SECURITY TESTS ===\n")
TestSecurity.test_input_injection()
TestSecurity.test_malformed_json()
TestSecurity.test_method_restriction()
TestSecurity.test_rate_limiting()
```

### Scenario 9: Edge Cases (Category VI)
```python
# Python script
from test_api_comprehensive import TestEdgeCases

print("\n=== EDGE CASE TESTS ===\n")
TestEdgeCases.test_overnight_trains()
TestEdgeCases.test_zero_availability()
TestEdgeCases.test_large_result_set()
TestEdgeCases.test_special_characters()
```

### Scenario 10: Frontend Compatibility (Category IX)
```python
# Python script
from test_api_comprehensive import TestFrontendCompatibility

print("\n=== FRONTEND COMPATIBILITY ===\n")
TestFrontendCompatibility.test_response_keys()
TestFrontendCompatibility.test_json_serialization()
TestFrontendCompatibility.test_empty_results()
```

## Manual cURL Tests

### Test 1: Basic Route Search
```bash
curl "http://localhost:5000/api/routes?origin=NDLS&destination=KOTA&max_transfers=1&date=25-01-2026"
```

### Test 2: Route Validation (RAPPID)
```bash
curl -X POST "http://localhost:5000/api/validate-routes-rappid" \
  -H "Content-Type: application/json" \
  -d '{"routes": [...route objects...], "date": "25-01-2026"}'
```

### Test 3: Dual Validation (RAPPID + IRCTC)
```bash
curl -X POST "http://localhost:5000/api/validate-routes-dual" \
  -H "Content-Type: application/json" \
  -d '{"routes": [...route objects...], "date": "25-01-2026"}'
```

### Test 4: Live Station Data
```bash
curl "http://localhost:5000/api/live-station?station=NDLS&hours=2"
```

### Test 5: Seat Availability
```bash
curl "http://localhost:5000/api/seat-availability?train=12345&source=NDLS&destination=KOTA&date=25-01-2026"
```

### Test 6: Fare Information
```bash
curl "http://localhost:5000/api/fare?train=12345&source=NDLS&destination=KOTA&date=25-01-2026"
```

### Test 7: Train Schedule
```bash
curl "http://localhost:5000/api/train-schedule?train_no=12345"
```

### Test 8: Health Check
```bash
curl "http://localhost:5000/api/health"
```

### Test 9: Admin Clear Cache
```bash
curl -X POST "http://localhost:5000/admin/clear-cache"
```

### Test 10: Admin Warm Cache
```bash
curl -X POST "http://localhost:5000/admin/warm-cache"
```

### Test 11: RAPPID Status
```bash
curl "http://localhost:5000/admin/status/rappid"
```

### Test 12: Single Train Refresh
```bash
curl -X POST "http://localhost:5000/admin/refresh-rappid/12345"
```

### Test 13: Bulk Train Refresh
```bash
curl -X POST "http://localhost:5000/admin/refresh-rappid-bulk" \
  -H "Content-Type: application/json" \
  -d '{"train_numbers": ["12345", "12346", "12347"]}'
```

## Performance Check (Load Testing)

### Using Apache Bench
```bash
# Install
pip install apache2-utils  # On Windows, use different tool or WSL

# Test 100 requests, 10 concurrent
ab -n 100 -c 10 "http://localhost:5000/api/routes?origin=NDLS&destination=KOTA"
```

### Using Python requests
```python
import requests
import time

print("=== LOAD TEST ===\n")

times = []
for i in range(50):
    start = time.time()
    resp = requests.get(
        "http://localhost:5000/api/routes",
        params={"origin": "NDLS", "destination": "KOTA"},
        timeout=30
    )
    elapsed = (time.time() - start) * 1000
    times.append(elapsed)
    print(f"Request {i+1}: {elapsed:.1f}ms")

print(f"\nAverage: {sum(times)/len(times):.1f}ms")
print(f"Min: {min(times):.1f}ms")
print(f"Max: {max(times):.1f}ms")
```

## Debugging Tips

### Check API Logs
```bash
# On Windows, tail equivalent
Get-Content api.log -Tail 100 -Wait
```

### Test with Different Stations
```bash
# All valid station codes
STATIONS = ["NDLS", "KOTA", "PGT", "HWH", "CSMT", "ADI", "BKN", 
            "CBE", "JP", "SBC", "LKO", "MAS"]

# Test each pair
for s1 in STATIONS:
    for s2 in STATIONS:
        if s1 != s2:
            # Test s1 -> s2
            pass
```

### Monitor System During Tests
```bash
# PowerShell: Monitor process
while($true) { 
    ps -Name python | Select-Object -Property Name, CPU, Memory
    Start-Sleep -Seconds 1
}

# List files (check for file handle leaks)
Get-Item -Path "*.json" | Measure-Object
```

## Test Results Interpretation

### Passing Test
```
✓ [Cache_Hit_Performance] PASS - Cache hit: 8520ms → 23ms
```

### Failing Test
```
✗ [Fare_Summation] FAIL - 3 routes have mismatched fares
```

### Skipped Test
```
⊘ [Direct_Route_Search] SKIP - No direct routes found
```

## Expected Test Results

### Full Run (All 80+ Tests)
- **Duration:** 5-15 minutes
- **Pass Rate:** >90%
- **Common Skips:** Tests for routes with zero availability

### Category-wise Expectations

| Category | Tests | Expected Pass Rate |
|----------|-------|-------------------|
| I. Core Functional | 10 | 95%+ |
| II. Pareto Logic | 7 | 90%+ |
| III. Data Integration | 6 | 85%+ |
| IV. Caching | 5 | 95%+ |
| V. Performance | 4 | 80%+ |
| VI. Edge Cases | 4 | 90%+ |
| VII. Admin | 4 | 95%+ |
| VIII. Security | 4 | 90%+ |
| IX. Frontend Compat | 3 | 95%+ |
| X. Resilience | 2 | 85%+ |

## Continuous Integration

### Weekly Test Run
```bash
#!/bin/bash
# run_weekly_tests.sh
set -e

echo "Starting weekly API test suite..."
date

# Start server in background
python api.py > /tmp/api.log 2>&1 &
SERVER_PID=$!
sleep 5

# Run tests
python test_api_comprehensive.py | tee test_results.txt

# Stop server
kill $SERVER_PID

# Archive results
cp test_results.txt "test_results_$(date +%Y%m%d).txt"

echo "Tests completed. Results saved."
```

## Troubleshooting Common Issues

### Issue: "Connection refused"
```bash
# Check if server is running
curl http://127.0.0.1:5000/api/health

# Or check process
ps aux | grep api.py
```

### Issue: "Timeout"
```bash
# Increase timeout in test_api_comprehensive.py
API_TIMEOUT = 60  # Change from 30 to 60
```

### Issue: "Out of memory"
```bash
# Reduce concurrent test load
STRESS_TEST_THREADS = 5  # Reduce from 10
STRESS_TEST_ITERATIONS = 50  # Reduce from 100
```

### Issue: "Station not found"
```bash
# Verify station exists in data
python -c "import pandas as pd; df = pd.read_csv('Train_details.csv'); print(df['Station'].unique())"
```

## Success Criteria

✓ All core functional tests pass  
✓ All algorithm tests pass  
✓ Integration with RAPPID & IRCTC successful  
✓ Cache hit rate >90%  
✓ P95 latency <500ms  
✓ Zero security vulnerabilities  
✓ No memory leaks (stable growth)  
✓ Response structure valid (frontend compatible)  

---

**For detailed information, see:** [API_TEST_GUIDE.md](API_TEST_GUIDE.md)
