# System Testing Strategy & Contracts

**Version**: 1.0  
**Status**: MANDATORY TESTING POLICY  
**Enforced Since**: 2026-01-28

---

## Executive Summary

This document defines:
1. What tests MUST pass before production
2. Testing pyramid (what fraction of each type)
3. Contract testing (API boundaries)
4. Performance & load testing thresholds
5. Chaos engineering approach

---

## 1. Testing Pyramid

### The Layers

```
                   🧪
                 End-to-End  (5%)
               Fast feedback
                 
              ✅ ✅ ✅
            Integration Tests (20%)
           Service interactions
            
        ✅ ✅ ✅ ✅ ✅
      Unit Tests (75%)
   Fast, isolated, focused
```

### By Numbers

| Test Type | % of Tests | Runtime | Maintainability |
|-----------|-----------|---------|-----------------|
| Unit | 75% | Fast (< 1s) | Easy |
| Integration | 20% | Medium (1-5s) | Medium |
| End-to-End | 5% | Slow (5-30s) | Hard |
| **Total** | **100%** | | |

### Why This Pyramid?

```
❌ WRONG (Test Ice Cream Cone):
  - Lots of E2E tests (slow, flaky)
  - Few unit tests
  - Feedback loop: 30 minutes
  - Hard to debug failures

✅ RIGHT (Test Pyramid):
  - Lots of unit tests (fast, reliable)
  - Some integration tests
  - Few E2E tests
  - Feedback loop: 2 minutes
  - Easy to debug failures
```

---

## 2. Unit Tests

### What to Test

```python
# ✅ Test single functions in isolation
def test_calculate_route_distance():
    # Arrange
    route = Route(start=(0,0), end=(3,4))
    
    # Act
    distance = calculate_route_distance(route)
    
    # Assert
    assert distance == 5  # 3-4-5 triangle
```

### Coverage Requirements

```
Minimum: 80% code coverage
Target: 90% code coverage
Exception: External library calls (3rd party code)

Coverage by service:
  - analytics_service: 90%+
  - route_service: 85%+
  - auth_service: 95%+ (security critical)
  - gateway: 80%+ (mostly routing)
```

### How to Run

```bash
# Run tests with coverage report
pytest tests/unit/ --cov=src/ --cov-report=html

# Check coverage before commit
coverage report -m
```

### Test Structure

```python
# tests/unit/analytics_service/test_metrics.py
import pytest
from analytics_service.metrics import calculate_metrics

class TestMetricsCalculation:
    """Calculate metrics from raw data"""
    
    def test_empty_data(self):
        """Metrics from empty data is zero"""
        result = calculate_metrics([])
        assert result == {'total': 0, 'average': 0}
    
    def test_single_value(self):
        """Metrics from single value"""
        result = calculate_metrics([100])
        assert result == {'total': 100, 'average': 100}
    
    def test_multiple_values(self):
        """Metrics from multiple values"""
        result = calculate_metrics([10, 20, 30])
        assert result == {'total': 60, 'average': 20}
    
    def test_negative_values(self):
        """Negative values handled correctly"""
        result = calculate_metrics([-10, 10])
        assert result == {'total': 0, 'average': 0}
```

---

## 3. Integration Tests

### What to Test

```python
# ✅ Test services working together
def test_analytics_queries_database():
    # Arrange
    db = setup_test_database()
    analytics = AnalyticsService(db)
    
    # Act
    metrics = analytics.get_metrics(tenant_id='test-tenant')
    
    # Assert
    assert len(metrics) > 0
    assert all(m.tenant_id == 'test-tenant' for m in metrics)
    
    # Cleanup
    db.teardown()
```

### Test Coverage

```
Integration tests MUST cover:
  ✅ Service → Database reads
  ✅ Service → Database writes
  ✅ Service → Redis caching
  ✅ Service → Message queue (RabbitMQ)
  ✅ Service → File storage (S3)
  ✅ Error handling (timeout, connection failure)
  ✅ Data validation (bad input)

Integration tests MUST NOT:
  ❌ Make real HTTP calls (mock instead)
  ❌ Use real external APIs (mock instead)
  ❌ Depend on other services being up
```

### Fixtures (Test Data)

```python
# tests/conftest.py - Shared fixtures
import pytest

@pytest.fixture
def test_database():
    """In-memory database for testing"""
    db = Database(":memory:")
    db.create_schema()
    yield db
    db.close()

@pytest.fixture
def test_tenant():
    """Test tenant with sample data"""
    return {
        'tenant_id': 'test-tenant-123',
        'name': 'Test Company',
        'created_at': datetime.now()
    }

@pytest.fixture
def sample_metrics():
    """Sample metric data"""
    return [
        {'name': 'searches', 'value': 100, 'created_at': datetime.now()},
        {'name': 'errors', 'value': 5, 'created_at': datetime.now()},
    ]
```

### Mocking External Services

```python
# ✅ Mock external services (don't make real calls)
from unittest.mock import patch, MagicMock

def test_analytics_calls_route_service():
    # Mock the Route Service
    with patch('analytics.clients.route_service') as mock_route:
        mock_route.get_route.return_value = {
            'route_id': '123',
            'distance': 50
        }
        
        # Call analytics
        analytics = AnalyticsService()
        result = analytics.analyze_route('123')
        
        # Verify mock was called
        mock_route.get_route.assert_called_once_with('123')
        assert result['distance'] == 50
```

---

## 4. Contract Tests

### What Are They?

```
✅ Contract tests verify the "boundary" between services
   
   Analytics Service says:
   "I expect Route Service to respond with {route_id, distance}"
   
   Route Service says:
   "I will always respond with {route_id, distance}"
   
   Contract test:
   "If both follow the contract, they work together"
```

### Example: Analytics ↔ Route Service Contract

```python
# tests/contracts/test_route_service_contract.py
class TestRouteServiceContract:
    """Verify Route Service API contract"""
    
    def test_get_route_response_schema(self):
        """Route Service returns correct schema"""
        response = {
            'route_id': 'uuid',
            'start': {'lat': 0, 'lng': 0},
            'end': {'lat': 1, 'lng': 1},
            'distance': 100,
            'stops': [
                {'station_id': '123', 'name': 'Central'}
            ],
            'created_at': '2026-01-28T10:00:00Z'
        }
        
        # Validate schema
        assert 'route_id' in response
        assert isinstance(response['distance'], (int, float))
        assert isinstance(response['stops'], list)
    
    def test_get_route_error_response(self):
        """Route Service error response schema"""
        response = {
            'error': 'NOT_FOUND',
            'message': 'Route 123 not found',
            'timestamp': '2026-01-28T10:00:00Z'
        }
        
        assert 'error' in response
        assert 'message' in response
```

### Consumer-Driven Contracts

```
1. Analytics Service says:
   "I need routes with {route_id, distance}"
   
2. Route Service implements:
   def get_route(route_id):
       return {
           'route_id': route_id,
           'distance': 50,
           'metadata': {...}  # ← Extra fields OK
       }
   
3. Test verifies:
   - Route Service always returns route_id
   - Route Service always returns distance
   - Extra fields are OK (backward compatible)

4. If Route Service removes distance:
   - Contract test FAILS
   - Code review catches it
   - Prevents breaking change
```

---

## 5. Performance & Load Testing

### Baseline Thresholds

```
API Endpoints:
  - p50 latency: < 200ms
  - p95 latency: < 500ms
  - p99 latency: < 1000ms
  - Error rate: < 0.1%

Database Queries:
  - Simple queries (< 100 rows): < 50ms
  - Complex queries (< 10k rows): < 500ms
  - Aggregations: < 2 seconds
  - Cache hit rate: > 95%

Overall:
  - Throughput: > 1000 requests/second
  - Connection pool usage: < 80%
```

### Load Test Procedure

```bash
# 1. Baseline test (single user)
locust -f load_test.py --host=http://analytics-service:8000 -u 1

# 2. Ramp up test (gradually add users)
locust -f load_test.py --host=http://analytics-service:8000 -u 100 --spawn-rate 10 -t 10m

# 3. Spike test (sudden load increase)
locust -f load_test.py --host=http://analytics-service:8000 -u 100 -t 2m
# Then increase: -u 1000

# 4. Stress test (find breaking point)
locust -f load_test.py --host=http://analytics-service:8000 --spawn-rate 50 -t 30m
# Keep increasing until service fails

# 5. Soak test (run for hours at normal load)
locust -f load_test.py --host=http://analytics-service:8000 -u 100 -t 4h
```

### Load Test Script

```python
# load_test.py
from locust import HttpUser, task, between

class AnalyticsUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    @task(1)
    def get_metrics(self):
        """Simulate user getting metrics (weight: 1)"""
        self.client.get("/v1/analytics/metrics?tenant_id=test")
    
    @task(2)
    def get_dashboard(self):
        """Simulate user getting dashboard (weight: 2)"""
        self.client.get("/v1/analytics/dashboard?tenant_id=test")
    
    @task(1)
    def export_report(self):
        """Simulate user exporting report (weight: 1)"""
        self.client.post(
            "/v1/analytics/export",
            json={"format": "csv", "tenant_id": "test"}
        )
```

### Results Analysis

```
After 10 minutes at 100 users:

✅ Good results:
  - p99 latency: 500ms (< 1000ms threshold)
  - Error rate: 0.05% (< 0.1% threshold)
  - Throughput: 1500 req/sec (> 1000 req/sec threshold)
  → Service is production ready

❌ Bad results:
  - p99 latency: 5000ms (> 1000ms threshold)
  - Error rate: 5% (> 0.1% threshold)
  - Throughput: 200 req/sec (< 1000 req/sec threshold)
  → Service needs optimization
    - Increase connection pool?
    - Optimize queries?
    - Add caching?
    - Horizontal scaling?
```

---

## 6. Chaos Engineering

### What Is It?

```
Chaos Engineering = intentionally break things to find weaknesses

Example:
  1. Start service
  2. Kill a database connection
  3. Verify service still works (circuit breaker activates)
  4. Verify users see cached data (graceful degradation)
```

### Failure Scenarios to Test

```
✅ Database failures:
  - Kill database connection
  - Make database timeout
  - Make database return errors
  - Fill connection pool

✅ Cache failures:
  - Kill Redis instance
  - Make Redis timeout
  - Fill cache memory

✅ Network failures:
  - Introduce latency (100ms → 500ms)
  - Introduce packet loss (1% → 10%)
  - Introduce jitter (random latency)

✅ Service failures:
  - Kill service pod (Kubernetes will restart)
  - Kill multiple pods (scaled service keeps working)
  - Kill all pods in a zone (failover to other zone)
```

### Running Chaos Tests

```bash
# Install chaos toolkit
pip install chaostoolkit chaostoolkit-kubernetes

# Define chaos experiment
cat > chaos_experiments/database_failure.yaml << EOF
version: 1.0.0
title: Database Failure Recovery
description: Service continues during database outage
steady-state-hypothesis:
  title: Service is healthy
  probes:
    - type: http
      url: http://analytics-service:8000/health
      expected_status: 200

method:
  - type: action
    name: Kill database pod
    provider:
      type: process
      path: kubectl
      arguments: delete pod -n production -l app=postgres

  - type: probe
    name: Service still responds
    provider:
      type: http
      url: http://analytics-service:8000/v1/analytics/metrics
      expected_status: 200

rollback:
  - type: action
    name: Restore database
    provider:
      type: process
      path: kubectl
      arguments: apply -f database.yaml
EOF

# Run chaos experiment
chaos run chaos_experiments/database_failure.yaml
```

---

## 7. Test Execution & CI/CD

### Automated Test Pipeline

```
Developer pushes code
         ↓
Git Hook (pre-commit)
  - Format check
  - Lint check
         ↓
GitHub Actions (on push)
  - Unit tests (2 min)
  - Code coverage (1 min)
  - Type checking (1 min)
         ↓
  If any fail → Stop here, notify developer
         ↓
GitHub Actions (on PR)
  - Integration tests (5 min)
  - Contract tests (3 min)
  - Security scanning (2 min)
         ↓
  If any fail → Stop here, request changes
         ↓
Code Review (human)
  - Architecture check
  - Data ownership check
  - API governance check
         ↓
  If approved → Merge to main
         ↓
GitHub Actions (on merge)
  - Full test suite (15 min)
  - Build Docker image (5 min)
  - Push to staging (2 min)
         ↓
Staging Deployment
  - Smoke tests (3 min)
  - Performance tests (10 min)
  - Chaos tests (5 min)
         ↓
Production Deployment
  - Blue-green deployment (5 min)
  - Health checks (2 min)
  - Smoke tests (3 min)
```

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src/
      
      - name: Check coverage
        run: coverage report --fail-under=80

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Run integration tests
        run: pytest tests/integration/ -v
```

---

## 8. Test Data Management

### Test Database Seeding

```python
# tests/fixtures/seed_data.py
def seed_test_database(db):
    """Create realistic test data"""
    
    # Create tenants
    tenants = [
        db.create_tenant(name='Test Tenant 1'),
        db.create_tenant(name='Test Tenant 2'),
    ]
    
    # Create users
    for tenant in tenants:
        db.create_user(tenant_id=tenant.id, email=f'user@{tenant.name}.com')
    
    # Create sample metrics
    for tenant in tenants:
        db.create_metrics(
            tenant_id=tenant.id,
            metric_name='searches',
            metric_value=1000
        )
    
    return tenants
```

### Test Cleanup

```python
# Auto-cleanup after each test
@pytest.fixture
def fresh_database(test_db):
    """Fresh database for each test"""
    yield test_db
    test_db.teardown()  # Cleanup after test
    test_db.close()
```

---

## 9. Test Governance Checklist

Before merging code:

- [ ] All unit tests pass (80%+ coverage)
- [ ] All integration tests pass
- [ ] All contract tests pass
- [ ] Performance baselines met
- [ ] No security issues (bandit)
- [ ] Type checking passes (mypy)
- [ ] Code formatted (black)
- [ ] Linting passes (flake8)
- [ ] Documentation updated
- [ ] Code review approved
- [ ] Staging tests pass
- [ ] Load test passed
- [ ] Chaos test passed

---

**Document Established**: 2026-01-28  
**Owner**: QA Team + Engineering  
**Review Cycle**: Quarterly or when changing test thresholds  
**Last Updated**: 2026-01-28
