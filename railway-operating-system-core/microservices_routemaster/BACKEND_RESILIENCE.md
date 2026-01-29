# Backend Resilience & Circuit Breaker Patterns

**Version**: 1.0  
**Status**: MANDATORY IMPLEMENTATION GUIDE  
**Enforced Since**: 2026-01-28

---

## Executive Summary

This document defines:
1. How backend services fail gracefully
2. Circuit breaker patterns for all service-to-service calls
3. Retry strategies that don't cascade failures
4. Timeout configurations per service
5. Graceful degradation for Analytics queries

---

## 1. Circuit Breaker Pattern (Mandatory)

### When to Use

**Every HTTP call between services MUST use circuit breaker pattern:**

```
Analytics Service → Route Service (API call)
    ↓
Circuit Breaker (detect failure)
    ↓
    If healthy: call through
    If failing: return cached/default response
    If open: fail fast (no retry)
```

### Implementation

```python
# Using pybreaker library (Python)
from pybreaker import CircuitBreaker

# Create circuit breaker for Route Service
route_service_breaker = CircuitBreaker(
    fail_max=5,              # Open after 5 failures
    reset_timeout=60,        # Try again after 60 seconds
    listeners=[AlertListener()],  # Alert when state changes
    listeners=[MetricsListener()]  # Send to Prometheus
)

@route_service_breaker
def call_route_service(route_id):
    return requests.get(f"http://route-service:8000/routes/{route_id}")

# Usage
try:
    result = call_route_service(route_id)
except CircuitBreakerListener:
    # Circuit is OPEN
    result = get_cached_route(route_id)  # Fallback
    alert_ops("Route Service is down")
```

### Circuit Breaker States

```
┌─────────────────────────────────────────────────────────────┐
│ CLOSED (Normal)                                             │
│ - Requests go through                                        │
│ - Failures count                                            │
│ - Count < 5: Stay closed                                    │
│ - Count >= 5: Transition to OPEN                           │
└─────────────────────────────────────────────────────────────┘
           ↓ (5 failures)
┌─────────────────────────────────────────────────────────────┐
│ OPEN (Failing)                                              │
│ - Requests fail FAST (no retry)                             │
│ - Return cached/default response                            │
│ - Wait 60 seconds                                           │
│ - Transition to HALF_OPEN                                   │
└─────────────────────────────────────────────────────────────┘
           ↓ (timeout expires)
┌─────────────────────────────────────────────────────────────┐
│ HALF_OPEN (Testing)                                         │
│ - Try ONE request to test if service is back               │
│ - If succeeds: Transition to CLOSED                        │
│ - If fails: Transition back to OPEN (wait 60s again)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Retry Strategies

### When NOT to Retry

```
❌ Client errors (4xx)
   - 400 Bad Request: Bad input, won't change on retry
   - 401 Unauthorized: Token invalid, won't change
   - 403 Forbidden: Permission denied, won't change
   - 404 Not Found: Resource gone, won't reappear

❌ Server errors caused by bad request
   - 422 Unprocessable Entity: Bad data
   - 500 Internal Server Error (if non-idempotent)
```

### When TO Retry

```
✅ Transient failures (5xx)
   - 502 Bad Gateway: Service restarting
   - 503 Service Unavailable: Temporary overload
   - 504 Gateway Timeout: Slow response

✅ Network failures
   - Connection timeout
   - Connection refused
   - Read timeout

✅ But ONLY if idempotent
   - GET requests (always safe)
   - PUT requests (only if generating own IDs)
   - POST requests (NEVER - creates duplicates)
```

### Retry Policy by Service

```python
# Analytics Service calling Route Service
class RouteServiceRetry:
    max_retries = 3
    backoff_factor = 2  # 1s, 2s, 4s
    timeout = 5
    
    # Retry on: 502, 503, 504, timeout, connection errors
    # Don't retry: 400, 401, 403, 404, 422

# Analytics Service calling Database
class DatabaseRetry:
    max_retries = 5  # Higher for database
    backoff_factor = 1.5  # 1.5s, 2.25s, 3.375s...
    timeout = 30
    
    # Retry on: Deadlock, connection pool exhausted
    # Don't retry: Syntax error, constraint violation
```

### Example: Exponential Backoff

```
Attempt 1: Fail immediately
           Wait 1 second
Attempt 2: Fail immediately
           Wait 2 seconds
Attempt 3: Fail immediately
           Wait 4 seconds
Attempt 4: Fail immediately
           
Result: Failure after ~7 seconds total
```

---

## 3. Timeout Configurations

### By Service Type

```
API Gateway → Downstream Services
  Timeout: 5 seconds
  Reason: User-facing, must be fast

Service → Database (local)
  Timeout: 30 seconds
  Reason: Complex queries OK

Analytics Service → Route Service
  Timeout: 10 seconds
  Reason: Cross-service, must complete

Analytics Service → External API
  Timeout: 60 seconds
  Reason: External API may be slow
```

### Implementation

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Create session with timeout + retries
session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=1.5,
    status_forcelist=[502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

# Use with timeout
response = session.get(
    'http://route-service:8000/routes',
    timeout=5  # 5 second timeout
)
```

---

## 4. Graceful Degradation

### For Analytics Service

When Route Service is down:

```python
def get_route_search_metrics(route_id):
    try:
        # Try to get fresh data
        return call_route_service_with_cb(route_id)
    except CircuitBreakerOpen:
        # Circuit is open, service is down
        # Return cached data instead
        cached = redis.get(f"route:{route_id}")
        if cached:
            logger.warning(f"Using cached route data for {route_id}")
            return cached
        
        # No cache, return degraded response
        logger.error(f"Route Service down, no cache. Returning empty.")
        return {
            "route_id": route_id,
            "status": "unavailable",
            "message": "Route service temporarily unavailable. Data may be stale.",
            "cached_at": None
        }
```

### For Real-time Queries

When Analytics Database is slow:

```python
def query_analytics(query_str, user_id):
    try:
        # Try fresh query (timeout = 5s)
        return database.execute(query_str, timeout=5)
    except Timeout:
        # Query too slow, return cached results
        cached = cache.get(f"query:{query_str}:{user_id}")
        if cached and is_recent(cached, minutes=30):
            logger.warning("Query slow, returning cached results")
            return cached
        
        # Return degraded response
        return {
            "status": "incomplete",
            "message": "Query took too long. Returning partial results.",
            "data": partial_results
        }
```

---

## 5. Bulkhead Pattern (Isolation)

### Problem

One failing service brings down all requests:

```
Request to Route Service
  → Connection pool saturated
  → No connections left for other requests
  → Everything fails
```

### Solution: Separate Connection Pools

```python
# Each service gets its own connection pool
class ServiceClients:
    # Route Service: 20 connection max
    route_client = HTTPClient(
        pool_size=20,
        max_retries=3,
        timeout=10
    )
    
    # Analytics Database: 10 connections max
    analytics_db = DatabaseClient(
        pool_size=10,
        max_retries=5,
        timeout=30
    )
    
    # External API: 5 connections max (external = slower)
    external_api = HTTPClient(
        pool_size=5,
        max_retries=2,
        timeout=60
    )

# Now if Route Service is slow:
# - Uses up to 20 connections
# - Other services still have their own 10 + 5
# - Failure is isolated
```

---

## 6. Monitoring & Alerts

### Metrics to Track

```
Circuit Breaker State (per service)
  - gauge: circuit_breaker_state{service=route_service, state=closed}
  - When OPEN: Alert immediately

Request Latency (per service)
  - histogram: request_latency_ms{service=route_service}
  - Alert if p99 > 5000ms

Error Rate (per service)
  - counter: request_errors_total{service=route_service, status=503}
  - Alert if > 5% of requests fail

Retry Count (per service)
  - counter: request_retries_total{service=route_service}
  - Alert if retries > 10% of requests
```

### Alert Rules

```yaml
# Alert when Route Service circuit breaker opens
- alert: CircuitBreakerOpen
  expr: circuit_breaker_state{service="route_service", state="open"} == 1
  for: 1m
  annotations:
    summary: "Route Service circuit breaker is OPEN"
    action: "Check Route Service health immediately"

# Alert when p99 latency is high
- alert: ServiceLatencyHigh
  expr: request_latency_p99{service="route_service"} > 5000
  for: 5m
  annotations:
    summary: "Route Service p99 latency > 5s"
    action: "Check Route Service performance/load"

# Alert when error rate is high
- alert: ServiceErrorRateHigh
  expr: rate(request_errors_total{service="route_service"}[5m]) > 0.05
  for: 2m
  annotations:
    summary: "Route Service error rate > 5%"
    action: "Check Route Service logs"
```

---

## 7. Recovery Procedures

### When Service is Down

```
1. DETECT (Circuit breaker opens automatically)
   - Requests start returning cached data
   - Alert triggered to ops

2. ISOLATE (Already isolated by circuit breaker)
   - Other services not affected
   - Requests queue up (not cascading)

3. RESTORE (Ops fixes the service)
   - Service restarts
   - Circuit breaker stays OPEN for 60 seconds

4. HALF-OPEN (Circuit breaker tests service)
   - Next request after 60s tests if service is back
   - If succeeds: Circuit closes, normal operation resumes
   - If fails: Circuit opens again, wait another 60s

5. CLOSE (Service is back)
   - Circuit breaker closes
   - Fresh data fetched from service
   - Metrics reset
```

### Manual Recovery

```
If circuit breaker is stuck OPEN:

# Reset circuit breaker (force close)
circuit_breaker.reset()

# Check service health
GET /health HTTP/1.1
Host: route-service:8000

# Once healthy, restart affected services
docker-compose restart analytics-service
```

---

## 8. Governance Checklist

Before deploying new service:

- [ ] Every external call uses circuit breaker
- [ ] Timeout configured appropriately
- [ ] Retry policy defined (idempotent only)
- [ ] Fallback/cache strategy defined
- [ ] Graceful degradation implemented
- [ ] Metrics exported to Prometheus
- [ ] Alerts defined for circuit breaker state
- [ ] Manual recovery procedure documented
- [ ] Load tested with failures
- [ ] Architecture review completed

---

**Document Established**: 2026-01-28  
**Owner**: Backend Team + SRE  
**Review Cycle**: When adding new service-to-service calls  
**Last Updated**: 2026-01-28
