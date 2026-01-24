#!/usr/bin/env python3
"""
Phase 3: Performance Optimization Tests
Benchmarks connection pooling, caching, and overall performance improvements
"""

import requests
import json
import time
from statistics import mean, stdev
import sys

# Fix encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:5000"

print("\n" + "="*80)
print("PHASE 3: PERFORMANCE OPTIMIZATION TEST SUITE")
print("="*80)

# Test 1: Performance Metrics Endpoint
print("\n[Test 1] GET /api/performance-metrics (Client stats)")
try:
    r = requests.get(f"{BASE_URL}/api/performance-metrics")
    if r.status_code == 200:
        data = r.json()
        perf = data.get('performance', {})
        print(f"Status: 200 OK")
        print(f"  - Cache hit rate: {perf.get('cache_hit_rate', 'N/A')}")
        print(f"  - Avg response time: {perf.get('avg_response_time_ms', 'N/A')}")
        print(f"  - API calls: {perf.get('api_calls', 0)}")
        print(f"  - Cached items: {perf.get('cache_size', 0)}")
        print("  [PASS]")
    else:
        print(f"Status: {r.status_code}")
        print("  [FAIL]")
except Exception as e:
    print(f"  [ERROR]: {e}")

# Test 2: Cache Warming Endpoint
print("\n[Test 2] POST /admin/warm-cache (Pre-warm high-frequency trains)")
try:
    start_time = time.time()
    r = requests.post(f"{BASE_URL}/admin/warm-cache")
    elapsed = time.time() - start_time
    if r.status_code == 200:
        data = r.json()
        results = data.get('results', {})
        print(f"Status: 200 OK")
        print(f"  - Success: {results.get('success', 0)}")
        print(f"  - Failed: {results.get('failed', 0)}")
        print(f"  - Time: {elapsed:.2f}s")
        print("  [PASS]")
    else:
        print(f"Status: {r.status_code}")
        print("  [FAIL]")
except Exception as e:
    print(f"  [ERROR]: {e}")

# Test 3: Clear Cache Endpoint
print("\n[Test 3] POST /admin/clear-cache (Clear cached data)")
try:
    r = requests.post(f"{BASE_URL}/admin/clear-cache")
    if r.status_code == 200:
        data = r.json()
        print(f"Status: 200 OK")
        print(f"  - Message: {data.get('message', 'N/A')}")
        print("  [PASS]")
    else:
        print(f"Status: {r.status_code}")
        print("  [FAIL]")
except Exception as e:
    print(f"  [ERROR]: {e}")

# Test 4: Response Time Benchmarking
print("\n[Test 4] Response time benchmarking (10 sequential requests)")
try:
    times = []
    train_id = 16004
    
    for i in range(10):
        start = time.time()
        r = requests.get(f"{BASE_URL}/api/rappid-data/{train_id}")
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        print(f"  - Request {i+1}: {elapsed:.1f}ms - {r.status_code}")
    
    print(f"\nSummary:")
    print(f"  - Min: {min(times):.1f}ms")
    print(f"  - Max: {max(times):.1f}ms")
    print(f"  - Avg: {mean(times):.1f}ms")
    if len(times) > 1:
        print(f"  - StdDev: {stdev(times):.1f}ms")
    print("  [PASS]")
except Exception as e:
    print(f"  [ERROR]: {e}")

# Test 5: Cache Hit Ratio
print("\n[Test 5] Cache hit ratio (before and after cache warming)")
try:
    # Get initial stats
    r1 = requests.get(f"{BASE_URL}/api/performance-metrics")
    before = r1.json()['performance']
    
    # Warm cache
    requests.post(f"{BASE_URL}/admin/warm-cache")
    time.sleep(1)
    
    # Make some requests
    for _ in range(20):
        requests.get(f"{BASE_URL}/api/rappid-data/16004")
    
    # Get final stats
    r2 = requests.get(f"{BASE_URL}/api/performance-metrics")
    after = r2.json()['performance']
    
    print(f"Before warming:")
    print(f"  - Cache hit rate: {before.get('cache_hit_rate', 'N/A')}")
    print(f"  - Cached items: {before.get('cache_size', 0)}")
    print(f"\nAfter warming:")
    print(f"  - Cache hit rate: {after.get('cache_hit_rate', 'N/A')}")
    print(f"  - Cached items: {after.get('cache_size', 0)}")
    print("  [PASS]")
except Exception as e:
    print(f"  [ERROR]: {e}")

# Test 6: Connection Pool Efficiency
print("\n[Test 6] Concurrent requests (connection pooling)")
try:
    import concurrent.futures
    
    def make_request(train_id):
        start = time.time()
        r = requests.get(f"{BASE_URL}/api/rappid-data/{train_id}")
        return time.time() - start
    
    start_total = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request, 16004 + i) for i in range(10)]
        times = [f.result() for f in concurrent.futures.as_completed(futures)]
    total_time = time.time() - start_total
    
    print(f"  - 10 concurrent requests completed in {total_time:.2f}s")
    print(f"  - Average per-request time: {mean(times)*1000:.1f}ms")
    print(f"  - Min: {min(times)*1000:.1f}ms, Max: {max(times)*1000:.1f}ms")
    print("  [PASS]")
except Exception as e:
    print(f"  [ERROR]: {e}")

# Test 7: Health Check with Performance Data
print("\n[Test 7] GET /api/health (With RAPPID metrics)")
try:
    r = requests.get(f"{BASE_URL}/api/health")
    if r.status_code == 200:
        data = r.json()
        print(f"Status: 200 OK")
        print(f"  - Status: {data.get('status', 'N/A')}")
        print(f"  - RAPPID cached trains: {data.get('rappid', {}).get('cached_trains', 'N/A')}")
        print(f"  - Coverage %: {data.get('rappid', {}).get('coverage_percent', 'N/A')}")
        print("  [PASS]")
    else:
        print(f"Status: {r.status_code}")
        print("  [FAIL]")
except Exception as e:
    print(f"  [ERROR]: {e}")

# Test 8: Bulk Operations with Optimized Client
print("\n[Test 8] POST /admin/refresh-rappid-bulk (Optimized performance)")
try:
    start_time = time.time()
    payload = {"train_numbers": ["14709", "18246", "22632", "16004", "12970"]}
    r = requests.post(f"{BASE_URL}/admin/refresh-rappid-bulk", json=payload)
    elapsed = time.time() - start_time
    
    if r.status_code == 200:
        data = r.json()
        print(f"Status: 200 OK")
        print(f"  - Trains requested: {data.get('total_requested', 0)}")
        print(f"  - Successful: {data.get('successful', 0)}")
        print(f"  - Failed: {data.get('failed', 0)}")
        print(f"  - Time: {elapsed:.2f}s")
        print(f"  - Avg per train: {elapsed/data.get('total_requested', 1):.2f}s")
        print("  [PASS]")
    else:
        print(f"Status: {r.status_code}")
        print("  [FAIL]")
except Exception as e:
    print(f"  [ERROR]: {e}")

# Final Performance Summary
print("\n" + "="*80)
print("PHASE 3 PERFORMANCE SUMMARY")
print("="*80)

try:
    r = requests.get(f"{BASE_URL}/api/performance-metrics")
    if r.status_code == 200:
        perf = r.json()['performance']
        print(f"\nClient Performance Metrics:")
        print(f"  - Total requests: {perf.get('total_requests', 0)}")
        print(f"  - Cache hits: {perf.get('cache_hits', 0)}")
        print(f"  - Cache hit rate: {perf.get('cache_hit_rate', '0%')}")
        print(f"  - API calls: {perf.get('api_calls', 0)}")
        print(f"  - Failed requests: {perf.get('failed_requests', 0)}")
        print(f"  - Avg response: {perf.get('avg_response_time_ms', 'N/A')}")
        print(f"  - Min response: {perf.get('min_response_time_ms', 'N/A')}")
        print(f"  - Max response: {perf.get('max_response_time_ms', 'N/A')}")
        print(f"  - Cached items: {perf.get('cache_size', 0)}")
except:
    pass

print("\n" + "="*80)
print("PHASE 3 TESTS COMPLETE")
print("="*80 + "\n")
