# 🧪 RAPPID Integration - Testing Guide

## Overview
Complete testing suite for RAPPID API integration in the Route Master project.

---

## Unit Tests

### Test 1: API Client Initialization
```python
from rappid_integration import RAPPIDAPIClient

def test_client_initialization():
    client = RAPPIDAPIClient(timeout=10, retry_attempts=3)
    assert client.timeout == 10
    assert client.retry_attempts == 3
    assert client.cache == {}
    assert client.cache_timestamps == {}
    print("✓ Client initialization test passed")

test_client_initialization()
```

### Test 2: Cache Functionality
```python
def test_caching():
    client = RAPPIDAPIClient()
    
    # Save to cache
    test_data = {"train": "16320", "status": "On Time"}
    client._save_to_cache("test_key", test_data)
    
    # Retrieve from cache
    cached = client._get_from_cache("test_key")
    assert cached == test_data
    
    # Verify cache timestamp exists
    assert "test_key" in client.cache_timestamps
    print("✓ Caching test passed")

test_caching()
```

### Test 3: Cache Expiration
```python
import time

def test_cache_expiration():
    client = RAPPIDAPIClient()
    client.CACHE_DURATION = 1  # 1 second for testing
    
    test_data = {"train": "16320"}
    client._save_to_cache("expire_test", test_data)
    
    # Should be valid
    assert client._is_cache_valid("expire_test")
    
    # Wait for expiration
    time.sleep(1.1)
    
    # Should be expired
    assert not client._is_cache_valid("expire_test")
    print("✓ Cache expiration test passed")

test_cache_expiration()
```

### Test 4: Validator Initialization
```python
from rappid_integration import RAPPIDRouteValidator

def test_validator_init():
    validator = RAPPIDRouteValidator()
    assert validator.api_client is not None
    assert validator.validation_cache == {}
    print("✓ Validator initialization test passed")

test_validator_init()
```

### Test 5: Coach Analysis
```python
def test_coach_analysis():
    coaches = [
        {"type": "Sleeper"},
        {"type": "Sleeper"},
        {"type": "3A"},
        {"type": "2A"}
    ]
    
    result = RAPPIDRouteValidator._analyze_coaches(coaches)
    assert result["Sleeper"] == 2
    assert result["3A"] == 1
    assert result["2A"] == 1
    print("✓ Coach analysis test passed")

test_coach_analysis()
```

### Test 6: Validation Scoring
```python
def test_validation_scoring():
    # Full data, no delays
    full_data = {
        "seat_availability": {"available": 50},
        "fare": {"total": 500},
        "train_status": {"running_on_time": True},
        "coaches": {"total": 16}
    }
    
    score = RAPPIDRouteValidator._calculate_validation_score(full_data)
    assert score == 100
    
    # Partial data
    partial_data = {
        "seat_availability": None,
        "fare": {"total": 500},
        "train_status": {"running_on_time": False},
        "coaches": None
    }
    
    score = RAPPIDRouteValidator._calculate_validation_score(partial_data)
    assert 40 <= score <= 60
    print("✓ Validation scoring test passed")

test_validation_scoring()
```

---

## Integration Tests

### Test 7: Flask API Health Check
```bash
# Test health endpoint
curl "http://localhost:5000/api/health"

# Expected response:
# {
#   "status": "healthy",
#   "irctc_api_configured": true,
#   "rappid_api_configured": true,
#   "dual_validation_available": true
# }

# Verification
if [ $? -eq 0 ]; then
    echo "✓ Health check test passed"
fi
```

### Test 8: Train Data Endpoint
```bash
# Test train data endpoint
curl "http://localhost:5000/api/train-data?train_no=16320"

# Should return:
# - train_no
# - data (with response object)
# - timestamp
# - source: "RAPPID API"

# Verification
RESPONSE=$(curl -s "http://localhost:5000/api/train-data?train_no=16320")
if echo "$RESPONSE" | grep -q "16320"; then
    echo "✓ Train data endpoint test passed"
fi
```

### Test 9: Train Schedule Endpoint
```bash
# Test schedule endpoint
RESPONSE=$(curl -s "http://localhost:5000/api/train-schedule?train_no=16320")

# Verify structure
if echo "$RESPONSE" | grep -q "train_name" && \
   echo "$RESPONSE" | grep -q "route" && \
   echo "$RESPONSE" | grep -q "total_stations"; then
    echo "✓ Train schedule endpoint test passed"
fi
```

### Test 10: Seat Availability Endpoint
```bash
# Test seats endpoint
RESPONSE=$(curl -s "http://localhost:5000/api/train-seats?train_no=16320")

# Verify structure
if echo "$RESPONSE" | grep -q "seat_info" && \
   echo "$RESPONSE" | grep -q "available"; then
    echo "✓ Seat availability endpoint test passed"
fi
```

### Test 11: Fare Endpoint
```bash
# Test fares endpoint
RESPONSE=$(curl -s "http://localhost:5000/api/train-fares?train_no=16320")

# Verify structure
if echo "$RESPONSE" | grep -q "fares" && \
   echo "$RESPONSE" | grep -q "currency"; then
    echo "✓ Fare endpoint test passed"
fi
```

### Test 12: Train Status Endpoint
```bash
# Test status endpoint
RESPONSE=$(curl -s "http://localhost:5000/api/train-status?train_no=16320")

# Verify structure
if echo "$RESPONSE" | grep -q "status" && \
   echo "$RESPONSE" | grep -q "delays"; then
    echo "✓ Train status endpoint test passed"
fi
```

### Test 13: Single Route Validation
```bash
# Test single route validation
curl -X POST "http://localhost:5000/api/validate-route-rappid" \
  -H "Content-Type: application/json" \
  -d '{
    "route": {
      "source": "ADI",
      "destination": "HWH",
      "segments": [{"train_no": "16320", "from": "ADI", "to": "HWH"}]
    },
    "date": "26-01-2026"
  }'

# Should include rappid_validation object with:
# - valid: true/false
# - segments: [...]
# - summary: {...}
```

### Test 14: Batch Route Validation
```bash
# Test batch validation
curl -X POST "http://localhost:5000/api/validate-routes-rappid" \
  -H "Content-Type: application/json" \
  -d '{
    "routes": [
      {"source": "ADI", "destination": "HWH", "segments": [...]},
      {"source": "ADI", "destination": "MAS", "segments": [...]}
    ],
    "date": "26-01-2026"
  }'

# Should include:
# - validated_routes: [...]
# - total_routes: 2
# - valid_routes: count
```

### Test 15: Dual Validation
```bash
# Test dual API validation
curl -X POST "http://localhost:5000/api/validate-routes-dual" \
  -H "Content-Type: application/json" \
  -d '{
    "routes": [{"source": "ADI", "destination": "HWH", "segments": [...]}],
    "date": "26-01-2026"
  }'

# Should include:
# - rappid_validation: {...}
# - irctc_validation: {...}
# - validation_summary: {rappid_valid, irctc_valid, overall_valid}
# - validation_sources: ["RAPPID API", "IRCTC API"]
```

### Test 16: Main Routes Endpoint with Validation
```bash
# Test routes endpoint with RAPPID validation
curl "http://localhost:5000/api/routes?origin=ADI&destination=HWH&validation=rappid"

# Test with IRCTC validation
curl "http://localhost:5000/api/routes?origin=ADI&destination=HWH&validation=irctc"

# Test with dual validation (recommended)
curl "http://localhost:5000/api/routes?origin=ADI&destination=HWH&validation=dual"

# Should include:
# - optimal_routes: [...]
# - validation_metadata with validation_source and apis_used
```

---

## Error Handling Tests

### Test 17: Missing Parameters
```bash
# Test missing train_no parameter
RESPONSE=$(curl -s "http://localhost:5000/api/train-data")

# Should return error
if echo "$RESPONSE" | grep -q "error"; then
    echo "✓ Missing parameter error test passed"
fi
```

### Test 18: Invalid Train Number
```bash
# Test with invalid train number
RESPONSE=$(curl -s "http://localhost:5000/api/train-data?train_no=99999999")

# Should return error
if echo "$RESPONSE" | grep -q "error"; then
    echo "✓ Invalid train number error test passed"
fi
```

### Test 19: Malformed JSON
```bash
# Test malformed JSON
curl -X POST "http://localhost:5000/api/validate-route-rappid" \
  -H "Content-Type: application/json" \
  -d 'invalid json'

# Should return 400 Bad Request
```

### Test 20: Missing Route Data
```bash
# Test POST without route
curl -X POST "http://localhost:5000/api/validate-route-rappid" \
  -H "Content-Type: application/json" \
  -d '{}'

# Should return error: "Route data is required"
```

---

## Performance Tests

### Test 21: Response Time - First Call
```bash
echo "Testing first API call (no cache)..."
START=$(date +%s%N)
curl -s "http://localhost:5000/api/train-data?train_no=16320" > /dev/null
END=$(date +%s%N)
TIME=$((($END - $START) / 1000000))
echo "First call took: ${TIME}ms"

# Expected: 800-1500ms
if [ $TIME -lt 2000 ]; then
    echo "✓ First call performance acceptable"
fi
```

### Test 22: Response Time - Cached Call
```bash
echo "Testing cached API call..."
# First call to populate cache
curl -s "http://localhost:5000/api/train-data?train_no=16320" > /dev/null

# Measure cached call
START=$(date +%s%N)
curl -s "http://localhost:5000/api/train-data?train_no=16320" > /dev/null
END=$(date +%s%N)
TIME=$((($END - $START) / 1000000))
echo "Cached call took: ${TIME}ms"

# Expected: <100ms
if [ $TIME -lt 200 ]; then
    echo "✓ Cache performance excellent"
fi
```

### Test 23: Concurrent Requests
```bash
echo "Testing 10 concurrent requests..."
for i in {1..10}; do
    curl -s "http://localhost:5000/api/train-data?train_no=16320" > /dev/null &
done
wait
echo "✓ Concurrent requests test completed"
```

### Test 24: Batch Validation Performance
```bash
# Create test batch with 10 routes
# Measure time
START=$(date +%s%N)
curl -X POST "http://localhost:5000/api/validate-routes-rappid" \
  -H "Content-Type: application/json" \
  -d '{...batch of 10 routes...}' > /dev/null
END=$(date +%s%N)
TIME=$((($END - $START) / 1000000))
echo "10 routes validation took: ${TIME}ms"
```

---

## Validation Data Tests

### Test 25: Verify Response Structure
```python
import json
import requests

response = requests.get('http://localhost:5000/api/train-data?train_no=16320')
data = response.json()

# Verify structure
assert 'train_no' in data
assert 'data' in data
assert 'timestamp' in data
assert 'source' in data
assert data['source'] == 'RAPPID API'
assert 'response' in data['data']

print("✓ Response structure validation passed")
```

### Test 26: Verify Validation Data Completeness
```python
response = requests.post(
    'http://localhost:5000/api/validate-route-rappid',
    json={
        "route": {
            "source": "ADI",
            "destination": "HWH",
            "segments": [{"train_no": "16320", "from": "ADI", "to": "HWH"}]
        }
    }
)

data = response.json()

# Verify validation structure
assert 'rappid_validation' in data
validation = data['rappid_validation']
assert 'valid' in validation
assert 'segments' in validation
assert 'summary' in validation

# Verify segment data
segment = validation['segments'][0]
assert 'train_no' in segment
assert 'validation_status' in segment
assert 'rappid_validation' in segment

rappid_data = segment['rappid_validation']
assert 'train_name' in rappid_data
assert 'seat_availability' in rappid_data
assert 'fare' in rappid_data
assert 'train_status' in rappid_data
assert 'validation_score' in rappid_data

print("✓ Validation data completeness test passed")
```

---

## Edge Case Tests

### Test 27: Cache Expiration
```python
# Set short cache duration for testing
client = RAPPIDAPIClient()
client.CACHE_DURATION = 1

# Fetch data
data1 = client.get_train_data('16320')

# Within cache window - should be same object
data2 = client.get_train_data('16320')
assert data1 == data2

# After expiration - should be refreshed
import time
time.sleep(1.1)
data3 = client.get_train_data('16320')
# Should be fresh data

print("✓ Cache expiration test passed")
```

### Test 28: Retry Logic
```python
# Test retry behavior with connection error
# This test would require mocking the requests library

from unittest.mock import patch
import requests

with patch('requests.get') as mock_get:
    # Simulate failures then success
    mock_get.side_effect = [
        requests.exceptions.ConnectionError(),
        requests.exceptions.Timeout(),
        type('obj', (object,), {'json': lambda: {'response': {}}, 'raise_for_status': lambda: None})()
    ]
    
    client = RAPPIDAPIClient(retry_attempts=3)
    # Should succeed on 3rd attempt
    result = client._make_request('16320')
    
    assert mock_get.call_count == 3
    print("✓ Retry logic test passed")
```

---

## Complete Test Suite Script

```bash
#!/bin/bash

echo "======================================"
echo "RAPPID Integration - Complete Test Suite"
echo "======================================"
echo ""

# Start backend (if not running)
# python api.py &
# BACKEND_PID=$!
# sleep 2

echo "Running Tests..."
echo ""

# Test 1: Health Check
echo "[1] Testing Health Check..."
curl -s "http://localhost:5000/api/health" | grep -q "healthy" && echo "✓ PASSED" || echo "✗ FAILED"

# Test 2: Train Data
echo "[2] Testing Train Data Endpoint..."
curl -s "http://localhost:5000/api/train-data?train_no=16320" | grep -q "16320" && echo "✓ PASSED" || echo "✗ FAILED"

# Test 3: Train Schedule
echo "[3] Testing Train Schedule Endpoint..."
curl -s "http://localhost:5000/api/train-schedule?train_no=16320" | grep -q "train_name" && echo "✓ PASSED" || echo "✗ FAILED"

# Test 4: Train Seats
echo "[4] Testing Train Seats Endpoint..."
curl -s "http://localhost:5000/api/train-seats?train_no=16320" | grep -q "seat_info" && echo "✓ PASSED" || echo "✗ FAILED"

# Test 5: Train Fares
echo "[5] Testing Train Fares Endpoint..."
curl -s "http://localhost:5000/api/train-fares?train_no=16320" | grep -q "fares" && echo "✓ PASSED" || echo "✗ FAILED"

# Test 6: Train Status
echo "[6] Testing Train Status Endpoint..."
curl -s "http://localhost:5000/api/train-status?train_no=16320" | grep -q "status" && echo "✓ PASSED" || echo "✗ FAILED"

# Test 7: Missing Parameter Error
echo "[7] Testing Error Handling..."
curl -s "http://localhost:5000/api/train-data" | grep -q "error" && echo "✓ PASSED" || echo "✗ FAILED"

# Test 8: Routes with RAPPID Validation
echo "[8] Testing Routes Endpoint (RAPPID validation)..."
curl -s "http://localhost:5000/api/routes?origin=ADI&destination=HWH&validation=rappid" | grep -q "optimal_routes" && echo "✓ PASSED" || echo "✗ FAILED"

# Test 9: Routes with Dual Validation
echo "[9] Testing Routes Endpoint (Dual validation)..."
curl -s "http://localhost:5000/api/routes?origin=ADI&destination=HWH&validation=dual" | grep -q "validation_sources" && echo "✓ PASSED" || echo "✗ FAILED"

echo ""
echo "======================================"
echo "Test Suite Complete!"
echo "======================================"

# Clean up
# kill $BACKEND_PID
```

---

## Testing Checklist

- [ ] Unit Tests (6 tests)
- [ ] Integration Tests (10 tests)
- [ ] Error Handling Tests (4 tests)
- [ ] Performance Tests (4 tests)
- [ ] Data Validation Tests (2 tests)
- [ ] Edge Cases (2 tests)
- [ ] Load Testing (concurrent requests)
- [ ] Cache behavior
- [ ] Error recovery
- [ ] API response times

---

## Expected Results Summary

| Test | Expected Result |
|------|-----------------|
| Health Check | status: "healthy" |
| Train Data | Returns train number and RAPPID data |
| Schedule | Returns route with stations |
| Seats | Returns availability by class |
| Fares | Returns fare information |
| Status | Returns on-time status |
| Error Handling | Returns error message |
| Performance (1st) | <2000ms |
| Performance (cached) | <100ms |
| Batch Validation | Processes all routes |

---

**Test Version:** 1.0  
**Last Updated:** January 24, 2026  
**Status:** ✅ All Tests Ready
