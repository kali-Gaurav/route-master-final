# Observability Stack & Monitoring

**Version**: 1.0  
**Status**: MANDATORY PRODUCTION REQUIREMENT  
**Enforced Since**: 2026-01-28

---

## Executive Summary

This document defines:
1. What metrics MUST be exported (Prometheus)
2. How requests are traced end-to-end (OpenTelemetry)
3. How logs are structured and centralized
4. How dashboards and alerts are configured
5. SLO/SLI definitions per service

---

## 1. Metrics Export (Prometheus)

### Required Metrics by Service

```
All services MUST export:
  ✅ request_duration_seconds (histogram)
  ✅ request_errors_total (counter)
  ✅ active_requests (gauge)
  ✅ database_connection_pool_size (gauge)
  ✅ cache_hit_rate (gauge)
  ✅ circuit_breaker_state (gauge: 0=closed, 1=open)
```

### Implementation

```python
# analytics_service/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time

# Request duration histogram (buckets in seconds)
request_duration = Histogram(
    'request_duration_seconds',
    'HTTP request latency',
    labelnames=['method', 'endpoint', 'status'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# Request error counter
request_errors = Counter(
    'request_errors_total',
    'Total HTTP request errors',
    labelnames=['method', 'endpoint', 'status']
)

# Active requests gauge
active_requests = Gauge(
    'active_requests',
    'Currently active requests',
    labelnames=['method', 'endpoint']
)

# Database connection pool
db_pool_size = Gauge(
    'database_connection_pool_size',
    'Current database connection pool size'
)

# Cache hit rate
cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate percentage'
)

# Circuit breaker state
circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open)',
    labelnames=['service']
)
```

### Middleware to Export Metrics

```python
# analytics_service/middleware.py
from fastapi import FastAPI
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import time

app = FastAPI()

@app.middleware("http")
async def add_metrics(request, call_next):
    """Track metrics for every request"""
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    
    # Increment active requests
    active_requests.labels(method=method, endpoint=endpoint).inc()
    
    try:
        response = await call_next(request)
        status = response.status_code
        
        # Record request duration
        duration = time.time() - start_time
        request_duration.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).observe(duration)
        
        return response
    
    except Exception as e:
        status = 500
        request_errors.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        raise
    
    finally:
        # Decrement active requests
        active_requests.labels(method=method, endpoint=endpoint).dec()

# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

### Prometheus Scrape Config

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'analytics-service'
    static_configs:
      - targets: ['analytics-service:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'route-service'
    static_configs:
      - targets: ['route-service:8000']
    metrics_path: '/metrics'

  - job_name: 'auth-service'
    static_configs:
      - targets: ['auth-service:8000']
    metrics_path: '/metrics'

  - job_name: 'postgresql'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

---

## 2. Distributed Tracing (OpenTelemetry)

### What Is It?

```
Single API request flows through multiple services:

User request
  ↓
API Gateway (trace_id=abc123)
  ↓
Analytics Service (span_id=xyz789)
  ↓
Database Query (span_id=def456)
  ↓
Redis Cache (span_id=ghi789)
  ↓
Response

OpenTelemetry records:
- Full trace path (abc123)
- Each hop (xyz789, def456, ghi789)
- Duration of each hop
- Errors in any hop
- Custom attributes (tenant_id, user_id, etc.)
```

### Implementation

```python
# analytics_service/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

# Configure Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name='jaeger',
    agent_port=6831,
)

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Auto-instrument frameworks
FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=db_engine)
RedisInstrumentor().instrument(client=redis_client)

# Manual tracing for custom operations
tracer = trace.get_tracer(__name__)

def process_analytics_query(query):
    with tracer.start_as_current_span("process_analytics_query") as span:
        span.set_attribute("query", query)
        span.set_attribute("tenant_id", get_current_tenant_id())
        
        # Do work
        result = expensive_calculation(query)
        
        span.set_attribute("result_size", len(result))
        return result
```

### Trace Context Propagation

```
When service A calls service B, propagate trace context:

Service A (outgoing request):
  - Get current trace_id and span_id
  - Add to HTTP headers: traceparent=trace_id;span_id
  
HTTP request with headers:
  traceparent: 00-abc123def456-ghi789jkl012-01
  
Service B (incoming request):
  - Read traceparent header
  - Extract trace_id and parent_span_id
  - Continue same trace (span_id is new)
  
Result: Single trace across multiple services
```

---

## 3. Structured Logging with JSON

### Why Structured Logging?

```
❌ Unstructured (hard to parse):
  2026-01-28 10:00:00 ERROR Failed to fetch route 123

✅ Structured (machine-readable):
  {
    "timestamp": "2026-01-28T10:00:00Z",
    "level": "ERROR",
    "message": "Failed to fetch route",
    "route_id": "123",
    "service": "analytics",
    "trace_id": "abc123",
    "error": "connection_timeout"
  }
```

### Implementation

```python
# analytics_service/logging.py
import json
import logging
import sys
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": "analytics-service",
            "logger": record.name,
        }
        
        # Add trace context if available
        if hasattr(record, 'trace_id'):
            log_entry['trace_id'] = record.trace_id
        if hasattr(record, 'span_id'):
            log_entry['span_id'] = record.span_id
        
        # Add custom fields
        if hasattr(record, 'tenant_id'):
            log_entry['tenant_id'] = record.tenant_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

# Configure logger
handler = logging.StreamHandler(sys.stdout)
formatter = JSONFormatter()
handler.setFormatter(formatter)

logger = logging.getLogger('analytics')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Usage
logger.info("Query executed", extra={
    'tenant_id': '123',
    'query': 'SELECT COUNT(*)',
    'duration_ms': 145
})
```

---

## 4. Centralized Log Aggregation (ELK Stack)

### Architecture

```
Services (write logs to stdout)
         ↓
    Filebeat (collect)
         ↓
    Kafka (buffer)
         ↓
  Elasticsearch (store, index)
         ↓
    Kibana (visualize)
```

### Docker Compose Setup

```yaml
# docker-compose.prod.yml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.5.0
    user: root
    volumes:
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
    command: filebeat -e -strict.perms=false
    depends_on:
      - elasticsearch

volumes:
  elasticsearch-data:
```

### Filebeat Configuration

```yaml
# filebeat.yml
filebeat.inputs:
  - type: container
    enabled: true
    paths:
      - '/var/lib/docker/containers/*/*.log'
    
    # Parse JSON logs automatically
    json.keys_under_root: true
    json.add_error_key: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "logs-%{+yyyy.MM.dd}"

processors:
  - add_docker_metadata: ~
  - add_kubernetes_metadata: ~
```

### Kibana Dashboard

```
Dashboard: Analytics Service Performance

Visualizations:
  - Error rate (last 24h): pie chart
  - Response latency: histogram
  - Requests by endpoint: bar chart
  - Circuit breaker states: table
  - Database connection pool: gauge
  - Cache hit rate: gauge
```

---

## 5. Alerts & SLOs

### Service Level Objectives (SLOs)

```
Analytics Service SLO:
  - Availability: 99.9% (43 minutes downtime/month)
  - Latency: p99 < 1000ms (99% of requests faster than 1s)
  - Error rate: < 0.1% (99.9% of requests succeed)

Route Service SLO:
  - Availability: 99.95% (22 minutes downtime/month)
  - Latency: p99 < 500ms (user-facing, must be fast)
  - Error rate: < 0.05% (99.95% of requests succeed)

Auth Service SLO:
  - Availability: 99.99% (4 minutes downtime/month)
  - Latency: p99 < 200ms (security critical)
  - Error rate: < 0.001% (99.999% of requests succeed)
```

### Alert Rules

```yaml
# prometheus/alerts.yml
groups:
  - name: analytics-service
    interval: 30s
    rules:
      # Alert when error rate exceeds threshold
      - alert: AnalyticsHighErrorRate
        expr: |
          rate(request_errors_total{job="analytics-service"}[5m])
          / 
          rate(request_duration_seconds_count{job="analytics-service"}[5m])
          > 0.001
        for: 5m
        annotations:
          summary: "Analytics service error rate > 0.1%"
          runbook: "https://wiki/runbooks/analytics-high-error-rate"
      
      # Alert when latency is high
      - alert: AnalyticsHighLatency
        expr: |
          histogram_quantile(0.99, 
            rate(request_duration_seconds_bucket{job="analytics-service"}[5m])
          ) > 1
        for: 5m
        annotations:
          summary: "Analytics service p99 latency > 1s"
          action: "Check database performance, check for slow queries"
      
      # Alert when circuit breaker is open
      - alert: CircuitBreakerOpen
        expr: circuit_breaker_state{service="analytics-service"} == 1
        for: 1m
        annotations:
          summary: "Analytics circuit breaker is OPEN"
          action: "Investigate what analytics-service is calling"
      
      # Alert when database connection pool is saturated
      - alert: DatabaseConnectionPoolSaturated
        expr: |
          database_connection_pool_usage{service="analytics-service"}
          > 0.8
        for: 2m
        annotations:
          summary: "Database connection pool > 80% capacity"
          action: "Increase pool size or reduce concurrent connections"
```

---

## 6. Dashboard Requirements

### System Health Dashboard

```
Top row (overview):
  - Overall system availability (%)
  - Total errors (last hour)
  - Average latency (p99)
  - Active users (gauge)

Per-service panels:
  Analytics Service:
    - Status (green=healthy, red=error)
    - Error rate trend
    - Latency trend
    - Request volume
  
  Route Service:
    - Status
    - Error rate trend
    - Latency trend
    - Request volume
  
  Auth Service:
    - Status
    - Error rate trend
    - Latency trend
    - Request volume

Infrastructure panels:
  - Database connection pool usage
  - Redis memory usage
  - Disk space available
  - Network bandwidth
```

---

## 7. Observability Checklist

Before deploying service:

- [ ] All endpoints export metrics to /metrics
- [ ] Prometheus scrape config updated
- [ ] OpenTelemetry initialized (auto-instrumentation)
- [ ] Logs formatted as JSON
- [ ] Trace context propagation implemented
- [ ] Alert rules defined in prometheus/alerts.yml
- [ ] Runbooks created for each alert
- [ ] SLOs defined (availability, latency, error rate)
- [ ] Dashboard created in Kibana/Grafana
- [ ] Integration test includes metrics assertion
- [ ] Load test includes latency/error rate tracking
- [ ] On-call rotation has access to dashboards

---

**Document Established**: 2026-01-28  
**Owner**: Monitoring/SRE Team  
**Review Cycle**: When adding new service or changing SLOs  
**Last Updated**: 2026-01-28
