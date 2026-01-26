# COMPREHENSIVE API TEST SUITE - TESTING GUIDE

## Overview

This document provides a complete guide for running the comprehensive API test suite (`test_api_comprehensive.py`) covering all aspects of the Route Master API.

## Quick Start

### 1. Prerequisites
```bash
# Install required packages
pip install requests pytest pytest-asyncio psutil
```

### 2. Start the API Server
```bash
# In the route-master-final directory
python api.py
```

The API should start on `http://127.0.0.1:5000`

### 3. Run the Test Suite
```bash
# Full test suite
python test_api_comprehensive.py

# Or with pytest (more detailed output)
pytest test_api_comprehensive.py -v -s
```

## Test Categories

### I. CORE FUNCTIONAL TESTS (Search & API)
**Location:** `TestCoreFeatures` class

Tests basic search functionality and API behavior:

1. **Direct Route Search** (I.1)
   - Verifies NDLS → KOTA returns direct trains with 0 transfers
   - Example: `GET /api/routes?origin=NDLS&destination=KOTA&max_transfers=0`

2. **Single Transfer Search** (I.2)
   - Verifies PGT → NDLS returns routes with exactly 1 transfer
   - Validates that segment count ≤ 2

3. **Max Transfers Constraint** (I.3)
   - Ensures `max_transfers=1` doesn't return 2+ transfer routes
   - Validates all routes have ≤ 2 segments

4. **Invalid Station Code** (I.4)
   - Tests that invalid codes (e.g., ABCD) return 400 error
   - Validates error handling

5. **Missing Parameters** (I.5)
   - Tests GET /api/routes with no parameters
   - Should return 400 error

6. **Date Formatting** (I.6)
   - Verifies multiple date formats are parsed:
     - DD-MM-YYYY (25-01-2026)
     - YYYY-MM-DD (2026-01-25)
     - YYYY/MM/DD (2026/01/25)

7. **Future Date Validation** (I.7)
   - Tests date 5 years in future (outside IRCTC booking window)
   - Should handle gracefully or use fallback

8. **Past Date Validation** (I.8)
   - Tests date in 2023 (past)
   - Should return error or current date fallback

9. **Same Source/Destination** (I.9)
   - Tests `origin=NDLS&destination=NDLS`
   - Should return error or empty list

10. **Case Insensitivity** (I.10)
    - Verifies `ndls` works same as `NDLS`
    - Tests uppercase vs lowercase normalization

#### Running Category I Tests:
```python
from test_api_comprehensive import TestCoreFeatures
TestCoreFeatures.test_direct_route_search()
TestCoreFeatures.test_case_insensitivity()
# etc...
```

### II. PARETO ALGORITHM & ROUTING LOGIC
**Location:** `TestParetoLogic` class

Tests optimization algorithm and route correctness:

1. **Route ID Uniqueness** (II.1)
   - Verifies every route has unique `route_id`
   - No duplicate IDs in response

2. **Segment Continuity** (II.2)
   - Validates `to_station` of segment N = `from_station` of segment N+1
   - Ensures routes are valid paths

3. **Layover Time Calculation** (II.3)
   - Verifies arrival + 30-60min ≥ next departure
   - Safety buffer for transfers

4. **Total Time Accuracy** (II.4)
   - Validates: `total_time` = sum of segment durations + layover times
   - Checks time calculation correctness

5. **Total Distance Accuracy** (II.5)
   - Validates: `total_distance` = sum of segment distances
   - Numerical accuracy check

6. **Fare Summation** (II.6)
   - Validates: `total_fare` = sum of segment fares
   - Financial accuracy

7. **Diverse Selection** (II.7)
   - Verifies results include mix of:
     - Fastest routes
     - Cheapest routes
     - Fewest transfers
   - Checks Pareto front diversity

### III. DATA INTEGRATION (RAPPID & IRCTC)
**Location:** `TestDataIntegration` class

Tests external API integrations:

1. **Live Fare Update** (III.1)
   - Verifies `live_fare` from IRCTC API in response
   - Validates real-time pricing

2. **Dual Validation Check** (III.2)
   - Tests `/api/validate-routes-dual` returns both RAPPID and IRCTC data
   - Checks for both validations in response

3. **IRCTC Status Check** (III.3)
   - Tests `/api/live-station` returns valid station data
   - Validates station availability model

4. **Class-Specific Search** (III.4)
   - Verifies availability checked for requested class (3A, SL, etc.)
   - Class-specific filtering

5. **Train Schedule Accuracy** (III.5)
   - Cross-verifies `/api/train-schedule` against IRCTC timings
   - Validates schedule data correctness

6. **Batch Validation** (III.6)
   - Tests POST `/api/validate-routes-rappid` with 10+ routes
   - Validates batch processing capability

#### Example Requests:
```bash
# Get live station data
curl "http://localhost:5000/api/live-station?station=NDLS"

# Validate routes via both APIs
curl -X POST http://localhost:5000/api/validate-routes-dual \
  -H "Content-Type: application/json" \
  -d '{"routes": [...], "date": "25-01-2026"}'

# Get train schedule
curl "http://localhost:5000/api/train-schedule?train_no=12345"
```

### IV. CACHING SYSTEM PERFORMANCE
**Location:** `TestCaching` class

Tests caching mechanisms:

1. **Memory Cache Hit** (IV.1)
   - First request ~10s (compute)
   - Second request <50ms (cache hit)
   - Tests cache effectiveness

2. **Cache Key Partitioning** (IV.2)
   - Different `max_transfers` values create different cache entries
   - Validates cache key generation

3. **Disk Persistence** (IV.3)
   - Verifies pre-computed files load correctly
   - Checks `*_pareto_routes_*.json` files

4. **Admin Clear Cache** (IV.4)
   - Tests POST `/admin/clear-cache` clears in-memory cache
   - Validates cache cleanup

5. **Cache Warming** (IV.5)
   - Tests POST `/admin/warm-cache` populates high-frequency data
   - Validates cache pre-population

#### Checking Cache Files:
```bash
# List cached route files
ls -la *_pareto_routes_*.json

# Check file structure
python -m json.tool < NDLS_to_KOTA_pareto_routes_20260125.json | head -50
```

### V. PERFORMANCE & STRESS
**Location:** `TestPerformance` class

Tests system under load:

1. **Concurrent Requests** (V.1)
   - 100 concurrent requests
   - Validates async handling
   - ThreadPoolExecutor with 10 workers

2. **Request Timeout** (V.2)
   - Verifies requests timeout gracefully
   - No crashes on timeout

3. **P95 Latency** (V.3)
   - Verifies 95% of requests respond <500ms
   - Performance baseline

4. **Memory Stability** (V.4)
   - Run 100 searches, monitor memory growth
   - Should stabilize (no memory leaks)
   - Growth <100MB

#### Running Load Tests:
```bash
# Run with custom parameters
pytest test_api_comprehensive.py::TestPerformance -v

# Monitor system resources
watch -n 1 'ps aux | grep api.py'
```

### VI. EDGE CASES
**Location:** `TestEdgeCases` class

Tests unusual and boundary scenarios:

1. **Overnight Trains** (VI.1)
   - Routes crossing midnight
   - Validates time calculation across day boundary

2. **Zero Availability** (VI.2)
   - Routes with no available seats
   - Graceful degradation

3. **Large Result Set** (VI.3)
   - Popular routes (NDLS ↔ CSMT)
   - Hundreds of possible routes
   - Tests Pareto pruning

4. **Special Characters** (VI.4)
   - Station codes with extra spaces
   - Validates input sanitization

#### Edge Case Examples:
```bash
# Test overnight route
curl "http://localhost:5000/api/routes?origin=NDLS&destination=CSMT"

# Test with extra spaces
curl "http://localhost:5000/api/routes?origin=%20NDLS%20&destination=%20KOTA%20"

# Test with max transfers
curl "http://localhost:5000/api/routes?origin=NDLS&destination=CSMT&max_transfers=3"
```

### VII. ADMIN & DATA MANAGEMENT
**Location:** `TestAdmin` class

Tests administrative endpoints:

1. **Single Train Refresh** (VII.1)
   - POST `/admin/refresh-rappid/<train_no>`
   - Updates JSON snapshot

2. **Bulk Refresh** (VII.2)
   - POST `/admin/refresh-rappid-bulk`
   - Refreshes multiple trains
   - Validates list processing

3. **RAPPID Status** (VII.3)
   - GET `/admin/status/rappid`
   - Coverage percentage
   - Missing trains list

4. **Health Check** (VII.4)
   - GET `/api/health`
   - System status
   - Component availability

#### Admin Operations:
```bash
# Refresh single train
curl -X POST "http://localhost:5000/admin/refresh-rappid/12345"

# Bulk refresh
curl -X POST "http://localhost:5000/admin/refresh-rappid-bulk" \
  -H "Content-Type: application/json" \
  -d '{"train_numbers": ["12345", "12346", "12347"]}'

# Check RAPPID coverage
curl "http://localhost:5000/admin/status/rappid"

# Health check
curl "http://localhost:5000/api/health"

# Clear cache
curl -X POST "http://localhost:5000/admin/clear-cache"

# Warm cache
curl -X POST "http://localhost:5000/admin/warm-cache"
```

### VIII. SECURITY & ROBUSTNESS
**Location:** `TestSecurity` class

Tests security measures:

1. **Input Injection** (VIII.1)
   - SQL injection attempts
   - Logic injection patterns
   - Validates sanitization

2. **Malformed JSON** (VIII.2)
   - Invalid JSON to POST endpoints
   - Should return 400 error

3. **Method Restriction** (VIII.3)
   - POST on GET-only endpoints
   - Should return 405 Method Not Allowed

4. **Rate Limiting** (VIII.4)
   - High-frequency requests
   - Validates rate limiting behavior

#### Security Testing:
```bash
# Test injection protection
curl "http://localhost:5000/api/routes?origin=NDLS%27%20OR%20%271%27%3D%271&destination=KOTA"

# Test malformed JSON
curl -X POST "http://localhost:5000/api/validate-routes-dual" \
  -H "Content-Type: application/json" \
  -d '{invalid json}'

# Test method restriction
curl -X POST "http://localhost:5000/api/routes" \
  -H "Content-Type: application/json" \
  -d '{"origin": "NDLS", "destination": "KOTA"}'
```

### IX. FRONTEND-BACKEND COMPATIBILITY
**Location:** `TestFrontendCompatibility` class

Tests response format and compatibility:

1. **Response Keys** (IX.1)
   - Verifies required keys exist:
     - `optimal_routes`
     - `all_generated_routes`
   - JSON structure validation

2. **JSON Serialization** (IX.2)
   - Valid JSON types
   - Numeric fields are numbers (not strings)
   - Proper type conversion

3. **Empty Results** (IX.3)
   - Handles empty result sets
   - Proper error messages
   - Consistent response format

#### Expected Response Structure:
```json
{
  "metadata": {...},
  "optimal_routes": [
    {
      "route_id": "unique-id",
      "segments": [
        {
          "train_no": "12345",
          "from": "NDLS",
          "to": "KOTA",
          "departure_time": "2026-01-25T10:00:00",
          "arrival_time": "2026-01-25T18:00:00",
          "duration_minutes": 480,
          "distance": 600,
          "fare": 1200,
          "class": "SL"
        }
      ],
      "total_time": 480,
      "total_distance": 600,
      "total_fare": 1200,
      "transfers": 0
    }
  ],
  "all_generated_routes": [...],
  "validation_metadata": {
    "validated_at": "2026-01-25T10:30:00",
    "travel_date": "25-01-2026",
    "routes_validated": 15,
    "validation_mode": "DUAL",
    "apis_used": ["RAPPID API", "IRCTC API"]
  }
}
```

### X. SYSTEM RESILIENCE
**Location:** `TestResilience` class

Tests error handling and recovery:

1. **API Error Graceful Handling** (X.1)
   - Simulates API errors (404, 500)
   - Validates graceful degradation
   - No unhandled exceptions

2. **End-to-End Flow** (X.2)
   - Complete workflow:
     1. Clear cache
     2. Compute routes
     3. Retrieve from cache
     4. Revalidate with live data
     5. Return results
   - Validates full pipeline

## Test Execution Examples

### Run All Tests
```bash
python test_api_comprehensive.py
```

### Run Specific Category
```bash
pytest test_api_comprehensive.py::TestCoreFeatures -v
pytest test_api_comprehensive.py::TestCaching -v
pytest test_api_comprehensive.py::TestPerformance -v
```

### Run Specific Test
```bash
pytest test_api_comprehensive.py::TestCoreFeatures::test_direct_route_search -v
```

### With Custom Output
```bash
pytest test_api_comprehensive.py -v -s --tb=short
```

## Interpreting Results

### Test Output Format
```
✓ [Test_Name] PASS - Details
✗ [Test_Name] FAIL - Error message
⊘ [Test_Name] SKIP - Reason for skipping
```

### Summary Report
```
✓ Passed:  45
✗ Failed:  3
⊘ Skipped: 5

Total: 53

Failed Tests:
  - Cache_Hit_Performance: P95 latency 520ms (target <500ms)
  - Input_Injection: Some payloads not blocked
  - End_to_End_Flow: Cache revalidation timeout
```

## Troubleshooting

### API Not Responding
```bash
# Check if server is running
curl http://127.0.0.1:5000/api/health

# Check logs
tail -f logs/api.log
```

### Tests Timing Out
- Increase `API_TIMEOUT` in test_api_comprehensive.py
- Check server performance: `top`, `htop`, or `Resource Monitor`
- Verify network connectivity

### Memory Issues
- Reduce `STRESS_TEST_ITERATIONS` in test configuration
- Check for file descriptor leaks: `lsof -p <pid>`
- Monitor with: `watch -n 1 'ps aux | grep api.py'`

### Station Code Not Found
- Verify station codes exist in Train_details.csv
- Check mapping in city_station_mapping.py
- Use valid codes: NDLS, KOTA, PGT, HWH, CSMT, etc.

## Performance Benchmarks

Expected performance metrics (on standard hardware):

| Metric | Target | Current |
|--------|--------|---------|
| Direct route search (cached) | <50ms | __ |
| Route computation | <10s | __ |
| P95 Latency | <500ms | __ |
| Concurrent requests (100x) | <5s | __ |
| Memory growth (100 searches) | <100MB | __ |
| Cache hit rate | >95% | __ |

## Continuous Integration

### GitHub Actions Example
```yaml
name: API Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - run: pip install -r requirements.txt
      - run: python api.py &
      - run: sleep 5
      - run: python test_api_comprehensive.py
```

## Coverage Analysis

To generate coverage report:
```bash
pip install pytest-cov
pytest test_api_comprehensive.py --cov=api --cov-report=html
open htmlcov/index.html
```

## Additional Testing Resources

### Manual API Testing Tools
- **Postman:** Import endpoints and test manually
- **curl:** Command-line HTTP testing
- **HTTPie:** User-friendly HTTP CLI

### Load Testing Tools
```bash
# Using Apache Bench
ab -n 1000 -c 100 "http://localhost:5000/api/health"

# Using wrk
wrk -t4 -c100 -d30s "http://localhost:5000/api/health"
```

### Monitoring & Profiling
```bash
# Python profiling
python -m cProfile -s cumtime api.py

# Memory profiling
pip install memory-profiler
python -m memory_profiler api.py
```

## Test Maintenance

### When to Update Tests
- New API endpoints added
- Response format changes
- Business logic modifications
- Performance threshold changes
- Security requirements update

### Adding New Tests
1. Create test method in appropriate class
2. Follow naming convention: `test_<description>`
3. Use `log_test()` for reporting
4. Update this guide

### Test Dependencies
- requests >= 2.28.0
- pytest >= 7.0
- psutil >= 5.9.0 (optional, for memory tests)

---

**Last Updated:** January 2026
**Test Suite Version:** 1.0
**API Version:** 3.0 (RAPPID + IRCTC Integration)
