# Analytics Service Integration Guide

## Overview

The Analytics Service provides comprehensive data analytics, business intelligence, and reporting capabilities for the Railway Operating System. This guide explains how to integrate and use the Analytics Service with other microservices.

## Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway                              │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
    ┌─────────┐    ┌────────────┐    ┌───────────────┐
    │ Auth    │    │Route       │    │Analytics      │
    │Service  │    │Service     │    │Service        │
    └────┬────┘    └──┬────────┬┘    └───┬───────────┘
         │            │        │          │
         └─────┬──────┴─┬──────┴──────────┘
               │        │
        ┌──────▼────┬───▼──────┐
        │  PostgreSQL          │
        │  (Multi-tenant)      │
        │  Schema-per-tenant   │
        └──────┬────┬────────┬─┘
               │    │        │
        ┌──────▼─┐ ┌┴──────┐ │
        │Analytics│Cache   │ │
        │Tables   │(Redis) │ │
        └─────────┘└───────┘ │
                      ▲       │
                      │       ▼
                  ┌───┴──────────┐
                  │  ETL Pipeline│
                  │ Aggregation  │
                  └──────────────┘
```

## Multi-Tenant Architecture

The Analytics Service uses **schema-per-tenant** isolation:

```
railway_os (Database)
├── public (shared tables)
│   └── tenants, api_keys, audit_logs
├── tenant_<uuid_1> (Tenant 1)
│   ├── analytics_metrics
│   ├── api_metrics
│   ├── route_search_metrics
│   └── user_engagement
├── tenant_<uuid_2> (Tenant 2)
│   ├── analytics_metrics
│   ├── api_metrics
│   ├── route_search_metrics
│   └── user_engagement
└── tenant_<uuid_n> (Tenant N)
    └── ...
```

## Integration Points

### 1. API Gateway Integration

The Analytics Service is accessed through the API Gateway:

```
Client → API Gateway:8000 → Analytics Service:8084
```

**Gateway Configuration:**
```python
# routes/analytics.py
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
import httpx

router = APIRouter(prefix="/v1/analytics")

@router.post("/query")
async def query_analytics(query: dict, tenant_id: str):
    """Proxy analytics query to analytics service"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://analytics-service:8084/v1/analytics/query",
            json=query,
            params={"tenant_id": tenant_id},
            timeout=30.0
        )
    return response.json()
```

### 2. Data Service Integration

The Analytics Service consumes data from the Data Service:

```python
# In analytics_engine.py
async def sync_with_data_service(self, tenant_id: UUID):
    """Sync data from Data Service for analytics"""
    async with httpx.AsyncClient() as client:
        # Get route data
        routes_response = await client.get(
            "http://data-service:8003/v1/routes",
            params={"tenant_id": str(tenant_id)},
            timeout=30.0
        )
        
        # Get station data
        stations_response = await client.get(
            "http://data-service:8003/v1/stations",
            params={"tenant_id": str(tenant_id)},
            timeout=30.0
        )
        
        return {
            "routes": routes_response.json(),
            "stations": stations_response.json()
        }
```

### 3. Route Service Integration

Get route search metrics from Route Service:

```python
# In analytics_engine.py
async def get_route_search_data(self, tenant_id: UUID, start_date: date, end_date: date):
    """Get route search analytics from Route Service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://route-service:8002/v1/analytics/searches",
            params={
                "tenant_id": str(tenant_id),
                "start_date": str(start_date),
                "end_date": str(end_date)
            },
            timeout=30.0
        )
        
        return response.json()
```

### 4. Monitoring Integration

Health checks and monitoring:

```python
# In monitoring.py
from services.analytics_service.main import app

async def check_analytics_health():
    """Check analytics service health"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "http://analytics-service:8084/health",
                timeout=5.0
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Analytics service health check failed: {e}")
            return False
```

## API Endpoint Integration Examples

### Example 1: Fetch Route Analytics in Web Dashboard

```python
# Frontend integration (JavaScript/React)
async function fetchRouteAnalytics(tenantId, dateRange = '30d') {
    const response = await fetch(`/api/v1/dashboard/routes?tenant_id=${tenantId}&date_range=${dateRange}`)
    const data = await response.json()
    
    return {
        topRoutes: data.route_popularity.slice(0, 10),
        stationConnectivity: data.station_connectivity,
        transferPatterns: data.transfer_analysis,
        peakHours: data.peak_hours
    }
}
```

### Example 2: Generate and Email Report

```python
# Backend integration (Python)
import httpx
from datetime import date

async def generate_route_report(tenant_id: str, email_recipients: list):
    """Generate route performance report and email it"""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://analytics-service:8084/v1/reports/generate",
            json={
                "tenant_id": tenant_id,
                "report_type": "route_performance",
                "format": "pdf",
                "parameters": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31"
                },
                "email_recipients": email_recipients
            },
            timeout=60.0
        )
        
    return response.json()
```

### Example 3: Real-Time Performance Metrics Dashboard

```python
# WebSocket integration for real-time updates
from fastapi import WebSocket

async def analytics_websocket(websocket: WebSocket, tenant_id: str):
    await websocket.accept()
    
    try:
        while True:
            # Get latest metrics every 5 seconds
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://analytics-service:8084/v1/analytics/metrics",
                    params={
                        "tenant_id": tenant_id,
                        "metric_names": ["total_searches", "avg_response_time", "cache_hit_rate"]
                    }
                )
            
            metrics = response.json()
            await websocket.send_json({
                "type": "metrics_update",
                "data": metrics,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            await asyncio.sleep(5)
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    
    finally:
        await websocket.close()
```

### Example 4: Data Export with Background Processing

```python
# Background task for data export
from celery import shared_task

@shared_task
def export_analytics_data(tenant_id: str, export_type: str, format: str):
    """Export analytics data asynchronously"""
    
    async def _export():
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://analytics-service:8084/v1/analytics/export/{export_type}",
                params={
                    "tenant_id": tenant_id,
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31"
                },
                timeout=120.0
            )
            
            # Save to file storage
            with open(f"/exports/{tenant_id}_{export_type}.{format}", 'wb') as f:
                f.write(response.content)
            
            return f"/exports/{tenant_id}_{export_type}.{format}"
    
    return asyncio.run(_export())
```

## Database Schema Integration

### Analytics Tables in Multi-Tenant Schema

```sql
-- For each tenant schema (tenant_<uuid>)
CREATE TABLE analytics_metrics (
    metric_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    computed_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_metrics_tenant (tenant_id),
    INDEX idx_metrics_name (metric_name)
);

CREATE TABLE api_metrics (
    metric_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    endpoint VARCHAR(500) NOT NULL,
    response_time_ms FLOAT NOT NULL,
    status_code INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_api_metrics_tenant (tenant_id),
    INDEX idx_api_metrics_endpoint (endpoint)
);

CREATE TABLE route_search_metrics (
    metric_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    search_id UUID NOT NULL,
    search_duration_ms FLOAT NOT NULL,
    results_found INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_route_search_tenant (tenant_id)
);
```

## Configuration Management

### Service Configuration

```python
# shared/config.py
ANALYTICS_CONFIG = {
    'service_name': 'analytics-service',
    'version': '1.0.0',
    'port': 8084,
    'host': '0.0.0.0',
    'debug_mode': False,
    'log_level': 'INFO',
    'cache_ttl': 300,  # 5 minutes
    'aggregation_schedule': '0 0 * * *',  # Daily at midnight
    'max_query_duration': 60,  # seconds
}
```

### Environment Variables

```bash
# Analytics Service Configuration
ANALYTICS_SERVICE_URL=http://analytics-service:8084
ANALYTICS_DB_SCHEMA_PREFIX=tenant_
ANALYTICS_CACHE_TTL=300
ANALYTICS_AGGREGATION_ENABLED=true
ANALYTICS_EXPORT_MAX_SIZE=104857600  # 100MB
ANALYTICS_ALERT_ENABLED=true
```

## Error Handling

### Service Error Response Format

```python
# Consistent error response across services
{
    "error": {
        "code": "ANALYTICS_ERROR_CODE",
        "message": "Human-readable error message",
        "status": 500,
        "timestamp": "2024-01-31T10:00:00Z",
        "request_id": "uuid",
        "details": {
            "tenant_id": "uuid",
            "service": "analytics-service",
            "operation": "get_dashboard_data"
        }
    }
}
```

### Error Recovery

```python
# Retry logic for service integration
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_analytics_service(endpoint: str, **kwargs):
    """Call analytics service with automatic retry"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://analytics-service:8084{endpoint}",
            **kwargs
        )
        response.raise_for_status()
        return response.json()
```

## Caching Strategy

### Redis Cache Integration

```python
# Cache analytics queries
from redis import Redis
import json
import hashlib

redis_client = Redis.from_url("redis://redis:6379/0")

async def get_cached_analytics(query: dict) -> Optional[dict]:
    """Get cached analytics query result"""
    cache_key = f"analytics:{hashlib.md5(json.dumps(query).encode()).hexdigest()}"
    
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    return None

async def cache_analytics_result(query: dict, result: dict, ttl: int = 300):
    """Cache analytics query result"""
    cache_key = f"analytics:{hashlib.md5(json.dumps(query).encode()).hexdigest()}"
    redis_client.setex(cache_key, ttl, json.dumps(result))
```

## Monitoring & Observability

### Logging Integration

```python
# Structured logging for analytics service
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger('analytics-service')
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

# Usage
logger.info("Analytics query executed", extra={
    "tenant_id": tenant_id,
    "query_type": "route_analytics",
    "duration_ms": 125,
    "result_count": 50
})
```

### Metrics Collection

```python
# Prometheus metrics for analytics service
from prometheus_client import Counter, Histogram, Gauge

analytics_queries = Counter(
    'analytics_queries_total',
    'Total analytics queries',
    ['query_type', 'status']
)

query_duration = Histogram(
    'analytics_query_duration_seconds',
    'Analytics query duration',
    ['query_type']
)

cache_hit_rate = Gauge(
    'analytics_cache_hit_rate',
    'Analytics cache hit rate',
    ['cache_type']
)
```

## Performance Optimization

### Query Optimization Tips

1. **Always specify date ranges** to limit data scanned
2. **Use indexed columns** in WHERE clauses
3. **Leverage pre-aggregated metrics** instead of raw data
4. **Enable query caching** for frequently accessed metrics
5. **Use batch operations** for multiple queries

### Database Optimization

```sql
-- Index frequently queried columns
CREATE INDEX idx_api_metrics_tenant_endpoint 
ON api_metrics(tenant_id, endpoint);

CREATE INDEX idx_route_search_metrics_tenant_created 
ON route_search_metrics(tenant_id, created_at DESC);

-- Partitioning large tables by date
ALTER TABLE api_metrics PARTITION BY RANGE (YEAR(created_at))
(
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025)
);
```

## Testing Integration

### Unit Tests

```python
# tests/test_analytics_integration.py
import pytest
from unittest.mock import Mock, patch
import httpx

@pytest.mark.asyncio
async def test_analytics_query_integration():
    """Test analytics query through API Gateway"""
    
    # Mock the Analytics Service response
    mock_response = {
        "data": [{"route": "A-B", "searches": 100}],
        "total_count": 1,
        "metadata": {}
    }
    
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.json.return_value = mock_response
        
        # Call through gateway
        result = await query_analytics(
            query={"metrics": ["route_popularity"]},
            tenant_id="test-tenant"
        )
        
        assert result["total_count"] == 1
        assert mock_post.called
```

### Integration Tests

```python
# tests/test_analytics_e2e.py
@pytest.mark.asyncio
async def test_full_analytics_workflow():
    """Test complete analytics workflow"""
    
    # 1. Create test data
    tenant_id = await create_test_tenant()
    
    # 2. Insert metrics
    await insert_test_metrics(tenant_id)
    
    # 3. Generate report
    report = await client.post(
        "/v1/reports/generate",
        json={
            "tenant_id": str(tenant_id),
            "report_type": "route_performance",
            "format": "json"
        }
    )
    
    # 4. Verify report
    assert report.status_code == 200
    assert "data" in report.json()
```

## Deployment Checklist

- [ ] Analytics service Docker image built and pushed
- [ ] Docker Compose configuration updated with analytics service
- [ ] PostgreSQL analytics tables created
- [ ] Redis connection configured
- [ ] API Gateway routes configured
- [ ] Environment variables set
- [ ] Health checks passing
- [ ] Logs being collected
- [ ] Metrics being exported
- [ ] Documentation updated

## Troubleshooting

### Service Not Responding

```bash
# Check service health
curl http://analytics-service:8084/health

# Check logs
docker logs analytics-service

# Verify database connection
psql postgresql://user:password@postgres:5432/railway_os
```

### Slow Queries

```sql
-- Identify slow queries
SELECT query, mean_exec_time 
FROM pg_stat_statements 
WHERE mean_exec_time > 1000 
ORDER BY mean_exec_time DESC;

-- Check query plan
EXPLAIN ANALYZE 
SELECT * FROM tenant_<uuid>.analytics_metrics 
WHERE metric_name = 'total_searches';
```

### Memory Issues

```python
# Monitor memory usage
import psutil

process = psutil.Process()
print(process.memory_info())  # RSS, VMS

# Optimize caching
cache_size = get_redis_memory_usage()
if cache_size > 500_000_000:  # 500MB
    clear_old_cache_entries()
```

## Next Steps

1. Deploy analytics service to development environment
2. Run integration tests
3. Configure production monitoring
4. Create analytics dashboards in frontend
5. Set up automated reports
6. Monitor performance in production

## References

- [Analytics Service README](./README.md)
- [API Documentation](./API.md)
- [Database Schema](./SCHEMA.md)
- [Deployment Guide](./DEPLOYMENT.md)