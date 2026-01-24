# API TEST ASSERTIONS & EXPECTED RESPONSES

## Core Test Assertions Reference

### Category I: Core Functional Tests

#### Test I.1: Direct Route Search
**Request:**
```bash
GET /api/routes?origin=NDLS&destination=KOTA&max_transfers=0
```

**Expected Response:**
```json
{
  "optimal_routes": [
    {
      "route_id": "route-1",
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
  "metadata": {...}
}
```

**Assertions:**
```python
# All routes should have exactly 1 segment (direct)
assert all(len(r["segments"]) == 1 for r in response["optimal_routes"])

# All routes should have 0 transfers
assert all(r.get("transfers", 0) == 0 for r in response["optimal_routes"])

# Response should have valid keys
assert "optimal_routes" in response
assert "all_generated_routes" in response
```

---

#### Test I.2: Single Transfer Search
**Request:**
```bash
GET /api/routes?origin=PGT&destination=NDLS&max_transfers=1
```

**Assertions:**
```python
# Segments should be <= 2 (0 transfers = 1 segment, 1 transfer = 2 segments)
assert all(len(r["segments"]) <= 2 for r in response["optimal_routes"])

# Routes should have 0 or 1 transfers only
transfers = [len(r["segments"]) - 1 for r in response["optimal_routes"]]
assert all(t in [0, 1] for t in transfers)
```

---

#### Test I.3: Max Transfers Constraint
**Request:**
```bash
GET /api/routes?origin=NDLS&destination=KOTA&max_transfers=1
```

**Assertions:**
```python
# Should not return routes with > 1 transfer
assert all(len(r["segments"]) <= 2 for r in response["optimal_routes"])

# Response with max_transfers=2 should have more/different routes
resp_mt1 = get("/api/routes?origin=NDLS&destination=KOTA&max_transfers=1")
resp_mt2 = get("/api/routes?origin=NDLS&destination=KOTA&max_transfers=2")

len(resp_mt1["optimal_routes"]) <= len(resp_mt2["optimal_routes"])
```

---

#### Test I.4: Invalid Station Code
**Request:**
```bash
GET /api/routes?origin=ABCD&destination=KOTA
```

**Expected Status:** 400

**Expected Response:**
```json
{
  "error": "Origin and destination are required."
}
```

**Assertions:**
```python
assert response.status_code == 400
assert "error" in response.json()
```

---

#### Test I.5: Missing Parameters
**Request:**
```bash
GET /api/routes
```

**Expected Status:** 400

**Assertions:**
```python
assert response.status_code == 400
assert "error" in response.json()
```

---

#### Test I.6: Date Formatting
**Requests:**
```bash
GET /api/routes?origin=NDLS&destination=KOTA&date=25-01-2026
GET /api/routes?origin=NDLS&destination=KOTA&date=2026-01-25
GET /api/routes?origin=NDLS&destination=KOTA&date=2026/01/25
```

**Assertions:**
```python
# All date formats should work
formats = ["25-01-2026", "2026-01-25", "2026/01/25"]
responses = [get(f"/api/routes?origin=NDLS&destination=KOTA&date={d}") for d in formats]

for resp in responses:
    assert resp.status_code == 200
    assert len(resp.json()["optimal_routes"]) > 0
```

---

### Category II: Pareto Algorithm Tests

#### Test II.1: Route ID Uniqueness
**Assertion:**
```python
response = get("/api/routes?origin=NDLS&destination=KOTA")
routes = response.json()["optimal_routes"]

# Extract all route IDs
route_ids = [r["route_id"] for r in routes if "route_id" in r]

# Check for duplicates
assert len(route_ids) == len(set(route_ids)), "Found duplicate route IDs"

# All routes should have route_id
assert all("route_id" in r for r in routes), "Some routes missing route_id"
```

---

#### Test II.2: Segment Continuity
**Assertion:**
```python
response = get("/api/routes?origin=NDLS&destination=KOTA")
routes = response.json()["optimal_routes"]

for route_idx, route in enumerate(routes):
    segments = route["segments"]
    
    # Check each consecutive pair of segments
    for seg_idx in range(len(segments) - 1):
        to_station = segments[seg_idx]["to"]
        from_station = segments[seg_idx + 1]["from"]
        
        assert to_station == from_station, \
            f"Route {route_idx} segment {seg_idx}: " \
            f"Discontinuity detected. {to_station} != {from_station}"
```

---

#### Test II.3: Layover Time Calculation
**Assertion:**
```python
from datetime import datetime, timedelta

response = get("/api/routes?origin=NDLS&destination=KOTA&max_transfers=2")
routes = response.json()["optimal_routes"]

MIN_LAYOVER_MINUTES = 30

for route_idx, route in enumerate(routes):
    segments = route["segments"]
    
    for seg_idx in range(len(segments) - 1):
        arrival = datetime.fromisoformat(segments[seg_idx]["arrival_time"])
        departure = datetime.fromisoformat(segments[seg_idx + 1]["departure_time"])
        
        layover_minutes = (departure - arrival).total_seconds() / 60
        
        assert layover_minutes >= MIN_LAYOVER_MINUTES, \
            f"Route {route_idx}: Insufficient layover time: {layover_minutes} minutes"
```

---

#### Test II.4: Total Time Accuracy
**Assertion:**
```python
from datetime import datetime

response = get("/api/routes?origin=NDLS&destination=KOTA")
routes = response.json()["optimal_routes"]

for route_idx, route in enumerate(routes):
    segments = route["segments"]
    
    # Sum all segment durations
    total_segment_duration = sum(seg["duration_minutes"] for seg in segments)
    
    # Add layovers
    total_layover = 0
    for i in range(len(segments) - 1):
        arrival = datetime.fromisoformat(segments[i]["arrival_time"])
        departure = datetime.fromisoformat(segments[i + 1]["departure_time"])
        layover = (departure - arrival).total_seconds() / 60
        total_layover += layover
    
    calculated_total = total_segment_duration + total_layover
    reported_total = route["total_time"]
    
    # Allow 5 minute tolerance for rounding
    assert abs(calculated_total - reported_total) <= 5, \
        f"Route {route_idx}: Time mismatch. Calculated: {calculated_total}, " \
        f"Reported: {reported_total}"
```

---

#### Test II.5: Total Distance Accuracy
**Assertion:**
```python
response = get("/api/routes?origin=NDLS&destination=KOTA")
routes = response.json()["optimal_routes"]

for route_idx, route in enumerate(routes):
    segments = route["segments"]
    
    # Sum segment distances
    calculated_distance = sum(seg["distance"] for seg in segments)
    reported_distance = route["total_distance"]
    
    assert abs(calculated_distance - reported_distance) <= 1, \
        f"Route {route_idx}: Distance mismatch. Calculated: {calculated_distance}, " \
        f"Reported: {reported_distance}"
```

---

#### Test II.6: Fare Summation
**Assertion:**
```python
response = get("/api/routes?origin=NDLS&destination=KOTA")
routes = response.json()["optimal_routes"]

for route_idx, route in enumerate(routes):
    segments = route["segments"]
    
    # Sum segment fares
    calculated_fare = sum(seg["fare"] for seg in segments)
    reported_fare = route["total_fare"]
    
    assert abs(calculated_fare - reported_fare) <= 1, \
        f"Route {route_idx}: Fare mismatch. Calculated: {calculated_fare}, " \
        f"Reported: {reported_fare}"
```

---

#### Test II.7: Diverse Selection
**Assertion:**
```python
response = get("/api/routes?origin=NDLS&destination=KOTA")
routes = response.json()["optimal_routes"]

assert len(routes) >= 3, "Need at least 3 routes for diversity check"

# Sort by different criteria
by_time = sorted(routes, key=lambda r: r["total_time"])
by_fare = sorted(routes, key=lambda r: r["total_fare"])
by_transfers = sorted(routes, key=lambda r: len(r["segments"]))

# Best route by time should differ from best by fare or transfers
best_time = by_time[0]["route_id"]
best_fare = by_fare[0]["route_id"]
best_transfers = by_transfers[0]["route_id"]

is_diverse = (best_time != best_fare) or (best_fare != best_transfers) or (best_time != best_transfers)
assert is_diverse, "Routes are not diverse (same route is best by all criteria)"
```

---

### Category III: Data Integration Tests

#### Test III.1: Live Fare Update
**Assertion:**
```python
response = get("/api/routes?origin=NDLS&destination=KOTA&validation=irctc")
routes = response.json()["optimal_routes"]

# Count segments with live fare
segments_with_live_fare = 0
for route in routes:
    for segment in route["segments"]:
        if "live_fare" in segment:
            segments_with_live_fare += 1
            # Live fare should be numeric
            assert isinstance(segment["live_fare"], (int, float))

assert segments_with_live_fare > 0, "No segments have live_fare data"
```

---

#### Test III.2: Dual Validation Check
**Request:**
```bash
POST /api/validate-routes-dual
Content-Type: application/json

{
  "routes": [...],
  "date": "25-01-2026"
}
```

**Expected Response:**
```json
{
  "validated_routes": [
    {
      "route_id": "...",
      "validation_summary": {
        "rappid_valid": true,
        "irctc_valid": true,
        "overall_valid": true,
        "rappid_score": 0.95,
        "validation_timestamp": "2026-01-25T10:30:00"
      },
      "rappid_validation": {...},
      "irctc_validation": {...}
    }
  ],
  "total_routes": 1,
  "valid_routes": 1,
  "validation_sources": ["RAPPID API", "IRCTC API"]
}
```

**Assertions:**
```python
response = post("/api/validate-routes-dual", {
    "routes": [sample_route],
    "date": "25-01-2026"
})

assert response.status_code == 200
routes = response.json()["validated_routes"]

for route in routes:
    # Check validation_summary exists
    assert "validation_summary" in route
    summary = route["validation_summary"]
    
    # Check all required fields
    assert "rappid_valid" in summary
    assert "irctc_valid" in summary
    assert "overall_valid" in summary
    assert "rappid_score" in summary
    
    # Overall should be AND of both
    assert summary["overall_valid"] == (summary["rappid_valid"] and summary["irctc_valid"])
```

---

#### Test III.3: IRCTC Status Check
**Request:**
```bash
GET /api/live-station?station=NDLS&hours=2
```

**Expected Response:**
```json
{
  "station_code": "NDLS",
  "station_name": "New Delhi",
  "trains": [
    {
      "train_no": "12345",
      "train_name": "...",
      "departure_time": "2026-01-25T10:00:00",
      "arrival_time": "2026-01-25T18:00:00",
      "status": "ON TIME"
    }
  ],
  "fetched_at": "2026-01-25T10:30:00"
}
```

**Assertions:**
```python
response = get("/api/live-station?station=NDLS")

assert response.status_code == 200
data = response.json()

# Check response structure
assert "station_code" in data or "trains" in data
assert data.get("station_code") == "NDLS" or data.get("error") is None
```

---

### Category IV: Caching Tests

#### Test IV.1: Memory Cache Hit
**Assertion:**
```python
import time

params = {"origin": "NDLS", "destination": "KOTA"}

# First request (populate cache)
start = time.time()
response1 = get("/api/routes", params=params)
time1 = (time.time() - start) * 1000

assert response1.status_code == 200
data1 = response1.json()
route_count_1 = len(data1["optimal_routes"])

# Second request (should hit cache)
start = time.time()
response2 = get("/api/routes", params=params)
time2 = (time.time() - start) * 1000

assert response2.status_code == 200
data2 = response2.json()
route_count_2 = len(data2["optimal_routes"])

# Same routes
assert route_count_1 == route_count_2

# Second request should be much faster
# Cached request should be < 100ms (even with some variance)
# First might be 5-30 seconds depending on data
assert time2 < 100, f"Cache hit too slow: {time2:.0f}ms"

print(f"Cache hit performance: {time1:.0f}ms → {time2:.0f}ms")
```

---

#### Test IV.2: Cache Key Partitioning
**Assertion:**
```python
response_mt1 = get("/api/routes?origin=NDLS&destination=KOTA&max_transfers=1")
response_mt2 = get("/api/routes?origin=NDLS&destination=KOTA&max_transfers=2")

routes_mt1 = response_mt1.json()["optimal_routes"]
routes_mt2 = response_mt2.json()["optimal_routes"]

# Different max_transfers should result in different cache keys
# and potentially different routes
assert len(routes_mt1) != len(routes_mt2) or routes_mt1 != routes_mt2, \
    "Cache keys not properly partitioned by max_transfers"
```

---

#### Test IV.3: Admin Clear Cache
**Assertion:**
```python
# Clear cache
response = post("/admin/clear-cache")
assert response.status_code == 200

data = response.json()
assert "success" in data.get("status", "")
assert data.get("status") == "success"
```

---

### Category V: Performance Tests

#### Test V.3: P95 Latency
**Assertion:**
```python
import statistics
import time

times = []
for _ in range(20):
    start = time.time()
    response = get("/api/routes?origin=NDLS&destination=KOTA")
    elapsed = (time.time() - start) * 1000
    times.append(elapsed)

# Calculate P95 (95th percentile)
p95 = statistics.quantiles(times, n=20)[18]  # n=20 gives 5-percentile buckets

# P95 should be < 500ms for cached requests
assert p95 < 500, f"P95 latency {p95:.0f}ms exceeds target of 500ms"

print(f"Latency metrics:")
print(f"  Min:    {min(times):.1f}ms")
print(f"  Max:    {max(times):.1f}ms")
print(f"  Avg:    {statistics.mean(times):.1f}ms")
print(f"  P95:    {p95:.1f}ms")
```

---

### Category VI: Edge Cases

#### Test VI.1: Overnight Trains
**Assertion:**
```python
response = get("/api/routes?origin=NDLS&destination=CSMT")

routes = response.json()["optimal_routes"]
assert len(routes) > 0, "No routes found for NDLS->CSMT"

for route in routes:
    segments = route["segments"]
    
    for segment in segments:
        dep = datetime.fromisoformat(segment["departure_time"])
        arr = datetime.fromisoformat(segment["arrival_time"])
        
        # Duration should be positive (handles overnight correctly)
        duration = (arr - dep).total_seconds() / 60
        assert duration > 0, "Invalid time calculation (negative duration)"
        
        # Duration should match reported
        assert abs(duration - segment["duration_minutes"]) < 1
```

---

#### Test VI.3: Large Result Set
**Assertion:**
```python
response = get("/api/routes?origin=NDLS&destination=CSMT&max_transfers=3", timeout=60)

assert response.status_code == 200
routes = response.json()["optimal_routes"]

# Should get multiple routes for popular stations
if len(routes) > 10:
    print(f"Successfully handled large result set: {len(routes)} routes")
else:
    print(f"Returned {len(routes)} routes (less than 10)")

# Response should still be valid JSON
assert "optimal_routes" in response.json()
assert "all_generated_routes" in response.json()
```

---

### Category VIII: Security Tests

#### Test VIII.1: Input Injection
**Assertion:**
```python
malicious_inputs = [
    "NDLS; DROP TABLE;",
    "NDLS' OR '1'='1",
    "NDLS\" OR \"1\"=\"1",
    "../../etc/passwd"
]

for payload in malicious_inputs:
    response = get(f"/api/routes?origin={payload}&destination=KOTA")
    
    # Should not crash and should return either 400 or 200
    assert response.status_code in (400, 200), \
        f"Unexpected status for payload {payload}: {response.status_code}"
    
    # If it returns 200, should not execute SQL/command
    if response.status_code == 200:
        data = response.json()
        assert "error" not in data or "optimal_routes" in data
```

---

#### Test VIII.3: Method Restriction
**Assertion:**
```python
# POST should not be allowed on GET endpoint
response = post("/api/routes", {"origin": "NDLS", "destination": "KOTA"})

# Should return either 405 (Method Not Allowed) or 400 (Bad Request)
assert response.status_code in (405, 400), \
    f"Expected 405 or 400, got {response.status_code}"
```

---

### Category IX: Frontend Compatibility

#### Test IX.1: Response Keys
**Assertion:**
```python
response = get("/api/routes?origin=NDLS&destination=KOTA")
data = response.json()

# Required top-level keys
required_keys = ["optimal_routes", "all_generated_routes"]
for key in required_keys:
    assert key in data, f"Missing required key: {key}"

# Check route structure
for route in data["optimal_routes"]:
    required_route_keys = ["route_id", "segments", "total_time", "total_distance", "total_fare"]
    for key in required_route_keys:
        assert key in route, f"Route missing key: {key}"

# Check segment structure
for route in data["optimal_routes"]:
    for segment in route["segments"]:
        required_segment_keys = ["train_no", "from", "to", "departure_time", 
                               "arrival_time", "fare", "class"]
        for key in required_segment_keys:
            assert key in segment, f"Segment missing key: {key}"
```

---

#### Test IX.2: JSON Serialization
**Assertion:**
```python
response = get("/api/routes?origin=NDLS&destination=KOTA")
data = response.json()

# Verify types
for route in data["optimal_routes"]:
    # Numeric fields should be numbers, not strings
    assert isinstance(route["total_time"], (int, float)), \
        f"total_time is {type(route['total_time'])}, not numeric"
    
    assert isinstance(route["total_fare"], (int, float)), \
        f"total_fare is {type(route['total_fare'])}, not numeric"
    
    assert isinstance(route["total_distance"], (int, float)), \
        f"total_distance is {type(route['total_distance'])}, not numeric"

# Verify ISO format timestamps
import re
iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
for route in data["optimal_routes"]:
    for segment in route["segments"]:
        assert re.match(iso_pattern, segment["departure_time"]), \
            f"Invalid departure_time format: {segment['departure_time']}"
        assert re.match(iso_pattern, segment["arrival_time"]), \
            f"Invalid arrival_time format: {segment['arrival_time']}"
```

---

## Running Assertion Tests

Save assertions to a Python file:

```python
# file: test_assertions.py
import requests
from datetime import datetime
import statistics
import time

BASE_URL = "http://127.0.0.1:5000"

def get(endpoint, params=None, timeout=30):
    return requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=timeout)

def post(endpoint, data=None, timeout=30):
    return requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=timeout)

# Copy any assertion tests above and run with:
# python -m pytest test_assertions.py -v
```

---

**For more details, see:**
- [API_TEST_GUIDE.md](API_TEST_GUIDE.md) - Complete testing guide
- [TEST_QUICK_REFERENCE.md](TEST_QUICK_REFERENCE.md) - Quick reference
- [test_api_comprehensive.py](test_api_comprehensive.py) - Full test suite
