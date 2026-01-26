# Production Pipeline - Architecture & Implementation Guide

## Overview

This is a **production-grade, self-healing data pipeline** for a railway route discovery platform. It processes raw API data, validates/normalizes it, stores it reliably, and serves optimized route search queries through a FastAPI backend.

**Design Philosophy:**
- **Robustness**: Self-healing with retries, fallbacks, and error recovery
- **Scalability**: Async operations, connection pooling, caching
- **Observability**: Structured logging, metrics collection, error tracking
- **Maintainability**: Clean separation of concerns, isolated testable components
- **Reproducibility**: Environment-based configuration, deterministic operations

---

## 6-Layer Architecture

### Layer 1: Data Ingestion
**Purpose**: Fetch data from external sources with rate limiting and caching.

**Components**:
- `AsyncHTTPClient`: HTTP client with automatic retries, rate limiting, caching
- `RateLimitWindow`: Enforces 10 RPS limit (configurable)
- `CacheManager`: TTL-based caching (3600s default)
- `RAPPIDFetcher`: Specialized fetcher for RAPPID API
- `IngestionOrchestrator`: Coordinates ingestion from multiple sources

**Key Features**:
- Exponential backoff retry (2.0x factor, 3 max retries)
- Rate limiting prevents API overload
- Cache with disk backing for persistence
- Batch fetching with concurrency control
- Immutable raw payload storage

**Example Usage**:
```python
async with AsyncHTTPClient(cache_manager) as client:
    data = await client.fetch(
        "https://api.example.com/trains",
        use_cache=True,
        cache_key="RAPPID:trains"
    )
```

### Layer 2: Raw Data Storage
**Purpose**: Immutable append-only storage of raw API responses.

**Table**: `raw_payloads`
- `raw_data`: Full JSON from API
- `http_status`: Response status code
- `is_valid`: Data validity flag
- `checksum`: SHA256 of payload (prevents duplicates)
- `received_at`: Timestamp for auditing

**Characteristics**:
- Append-only (no updates)
- Indexes on source, entity_type, received_at
- Enables replay and audit trail
- Checksum prevents duplicate ingestion

### Layer 3: Clean Operational Database
**Purpose**: Validated, deduplicated, normalized data ready for business logic.

**Tables**:
- `trains`: Train master data
- `stations`: Station master data
- `train_stations`: Train's route through stations
- `clean_dataset`: Denormalized data for fast queries

**Data Pipeline**:
1. **Validation**: `DataValidator` checks schema, types, ranges
2. **Deduplication**: `DeduplicationEngine` prevents duplicate records
3. **Normalization**: `DataNormalizer` standardizes formats
4. **Storage**: `CleanDataPipeline` persists processed data

**Example Pipeline**:
```python
pipeline = CleanDataPipeline(session)
success, train = pipeline.process_train(raw_data, raw_payload_id)
if success:
    session.commit()
```

### Layer 4: Business Logic (Routing Engine)
**Purpose**: Compute optimal routes between stations.

**Components**:
- `RouteGraph`: Graph representation of railway network
- `RoutingEngine`: Route discovery using Dijkstra's algorithm
- `Route`, `RouteSegment`: Data structures for results

**Algorithm**:
1. Build directed graph from train routes
2. Find direct routes first (fast path)
3. Implement BFS for multi-hop routes (TODO)
4. Rank routes by duration, transfers, confidence
5. Filter to top 10 results

**Example Usage**:
```python
routing_engine = RoutingEngine(session)
routes = routing_engine.search("NDLS", "KOTA", max_results=10)
for route in routes:
    print(f"{route.num_trains} trains, {route.total_duration_minutes} min")
```

### Layer 5: API Layer
**Purpose**: REST API for client applications.

**Endpoints**:
- `POST /api/v1/search`: Search routes (main feature)
- `GET /api/v1/health`: Health check
- `GET /api/v1/metrics`: System metrics
- `GET /api/v1/stations`: List stations
- `GET /api/v1/trains`: List trains

**Features**:
- Request validation with Pydantic
- Comprehensive error handling
- Response timing for metrics
- CORS support for web clients
- Structured error responses

**Search Request**:
```json
{
    "origin": "NDLS",
    "destination": "KOTA",
    "travel_date": "2024-02-15",
    "max_results": 10
}
```

**Search Response**:
```json
{
    "success": true,
    "routes": [
        {
            "segments": [...],
            "num_trains": 1,
            "total_duration_minutes": 420,
            "departure": "14:30",
            "arrival": "07:30",
            "confidence_score": 1.0
        }
    ],
    "total_routes": 5,
    "search_duration_ms": 145,
    "timestamp": "2024-02-14T10:30:00"
}
```

### Layer 6: Observability
**Purpose**: Logging, metrics, error tracking for monitoring and debugging.

**Components**:
- `JSONFormatter`: Structured JSON logging
- `MetricsCollector`: In-memory metrics with statistics
- `PerformanceMonitor`: Request and database latency tracking
- `ErrorTracker`: Error frequency and categorization
- `PerformanceMonitor.get_report()`: Generate performance summaries

**Logs**:
- **application.log**: All logs in JSON format
- **errors.log**: Errors and warnings in JSON format
- Log rotation: 100MB per file, 10 backups

**Metrics Tracked**:
- HTTP request latency (by endpoint, status)
- Database operation latency (by operation, table)
- Search latency (by route pair)
- Ingestion metrics (by source)
- Cache hits/misses
- System health checks

**Example**:
```python
perf_monitor = get_performance_monitor()
perf_monitor.log_request("/api/v1/search", "POST", 145.2, 200, True)
perf_monitor.log_database_operation("SELECT", 12.5, True, "trains")
```

---

## Database Schema

### Core Tables

**trains**
```sql
train_no (PK) VARCHAR(10)
train_name VARCHAR(255)
source_station_code VARCHAR(10)
destination_station_code VARCHAR(10)
days_running VARCHAR(7)  -- SMTWTFS format
journey_duration_minutes INTEGER
status ENUM(ACTIVE, INACTIVE, SUSPENDED)
created_at TIMESTAMP
updated_at TIMESTAMP
last_verified_at TIMESTAMP
```

**stations**
```sql
code (PK) VARCHAR(10)
name VARCHAR(255)
city VARCHAR(100)
state VARCHAR(100)
latitude FLOAT
longitude FLOAT
zone VARCHAR(50)
division VARCHAR(100)
created_at TIMESTAMP
updated_at TIMESTAMP
```

**train_stations** (Many-to-Many junction)
```sql
train_id (FK) INTEGER
station_id (FK) INTEGER
sequence INTEGER  -- Order in route
arrival_time VARCHAR(5)  -- HH:MM
departure_time VARCHAR(5)  -- HH:MM
halt_minutes INTEGER
distance_from_source_km FLOAT
is_originating BOOLEAN
is_terminating BOOLEAN
```

**Relationships**:
- Train -> TrainStation (1:N)
- Station -> TrainStation (1:N)
- Clean graph representation for efficient routing

### Supporting Tables

**raw_payloads**: Immutable raw API responses (audit trail)
**clean_dataset**: Denormalized view for fast queries
**routes_cache**: Cached search results with TTL
**search_logs**: User search history (analytics)
**performance_logs**: System metrics over time
**error_logs**: Error tracking with resolution tracking

---

## Configuration System

**config.py** provides environment-based configuration:

```python
config = get_config()

# Database
config.database.connection_string  # SQLite or PostgreSQL
config.database.pool_size          # Connection pooling

# Ingestion
config.ingestion.rate_limit_rps    # 10 requests/second
config.ingestion.cache_ttl_seconds # 3600
config.ingestion.max_retries       # 3
config.ingestion.retry_backoff_factor  # 2.0

# API
config.api.host                    # 0.0.0.0
config.api.port                    # 8000
config.api.rate_limit_requests_per_minute  # 300

# Logging
config.logging.logs_dir            # ./logs
config.logging.max_bytes           # 100MB
config.logging.backup_count        # 10

# Metrics
config.metrics.retention_days      # 30
config.metrics.collection_interval # 60s
```

---

## Background Jobs

**JobScheduler** runs automated maintenance tasks:

1. **Daily Data Refresh** (2 AM): Fetch fresh data from all sources
2. **Retry Failed Ingestions** (Every 30 min): Retry failed payload processing
3. **Clean Expired Cache** (Every 6 hours): Remove stale cached routes
4. **Aggregate Metrics** (Hourly): Summarize performance data
5. **Cleanup Old Logs** (3 AM): Delete logs older than retention period
6. **Health Check** (Every 5 min): Monitor system health

All jobs are logged with start/end times and error tracking.

---

## Running the Pipeline

### Local Development

```bash
# 1. Install dependencies
pip install -r production_pipeline/requirements.txt

# 2. Configure environment
export ENVIRONMENT=LOCAL
export DATABASE_URL=sqlite:///./data/railway.db

# 3. Run application
python -m production_pipeline.main
# API available at http://localhost:8000

# 4. Health check
curl http://localhost:8000/api/v1/health

# 5. Search routes
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"origin": "NDLS", "destination": "KOTA"}'
```

### Production Deployment

**Environment Variables**:
```bash
ENVIRONMENT=PRODUCTION
DATABASE_URL=postgresql://user:password@localhost/railway_db
LOGGING_LEVEL=INFO
CACHE_DIR=/var/cache/railway
LOGS_DIR=/var/log/railway
```

**Docker Compose**:
```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: railway_db
      POSTGRES_PASSWORD: secure_password

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:secure_password@postgres/railway_db
      ENVIRONMENT: PRODUCTION
    depends_on:
      - postgres

  redis:  # Optional, for distributed caching
    image: redis:7
```

**Running with Gunicorn** (production server):
```bash
gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  production_pipeline.main:app
```

---

## Scaling Strategies

### Horizontal Scaling
1. **Database**: Switch to PostgreSQL with read replicas
2. **API Servers**: Load balance multiple API instances
3. **Caching**: Use Redis for distributed cache
4. **Jobs**: Use job queue (Celery) for async task processing

### Optimization Tips
1. **Database Indexes**: Already defined on frequently queried columns
2. **Connection Pooling**: Configured (20 base, 40 max overflow)
3. **Batch Processing**: Process ingestion in batches (100 records)
4. **Caching**: 3600s TTL reduces API calls by ~80%
5. **Async Operations**: Non-blocking I/O for concurrency

---

## Monitoring & Debugging

### View Logs
```bash
# Recent logs
tail -f logs/application.log | jq .

# Errors only
tail -f logs/errors.log | jq .

# Search specific error
grep "SearchError" logs/errors.log | jq .
```

### Check Metrics
```bash
curl http://localhost:8000/api/v1/metrics
```

### Database Queries
```python
# Connect to database
from production_pipeline.database import DatabaseManager
db = DatabaseManager("sqlite:///./data/railway.db")
session = db.get_session()

# Check train count
from production_pipeline.database import Train
count = session.query(Train).count()
print(f"Total trains: {count}")

# Check recent searches
from production_pipeline.database import SearchLog
recent = session.query(SearchLog).order_by(SearchLog.created_at.desc()).limit(5)
for log in recent:
    print(f"{log.origin} -> {log.destination}: {log.routes_returned} routes")
```

---

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=production_pipeline tests/

# Run specific layer tests
pytest tests/test_layer1_ingestion.py -v
pytest tests/test_layer2_database.py -v
pytest tests/test_layer3_routing.py -v
pytest tests/test_layer4_api.py -v
```

---

## Troubleshooting

### Issue: API Slow (>5s latency)
- Check `/api/v1/metrics` for bottlenecks
- Review `logs/errors.log` for database errors
- Verify connection pooling settings
- Check database indexes

### Issue: High Memory Usage
- Check `cache_manager.metrics` - may need to clear in-memory cache
- Monitor job scheduler - may be accumulating tasks
- Review `performance_logs` table - may be too large

### Issue: Failed Ingestions
- Check `error_logs` table for detailed error types
- Retry job runs every 30 minutes automatically
- Check API rate limiting - may need to increase `rate_limit_rps`

### Issue: Missing Routes
- Verify trains exist: `SELECT COUNT(*) FROM trains`
- Verify stations exist: `SELECT COUNT(*) FROM stations`
- Check `train_stations` for route connections
- Review routing engine logs in `application.log`

---

## API Usage Examples

### Example 1: Search for Routes
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "NDLS",
    "destination": "KOTA",
    "travel_date": "2024-02-15",
    "max_results": 10
  }' | jq .
```

### Example 2: Get Health Status
```bash
curl http://localhost:8000/api/v1/health | jq .
```

### Example 3: Get System Metrics
```bash
curl http://localhost:8000/api/v1/metrics | jq .
```

### Example 4: List Stations
```bash
curl 'http://localhost:8000/api/v1/stations?city=Delhi' | jq .
```

---

## Performance Targets

- **Search Latency**: <200ms for common routes
- **API Throughput**: 100+ requests/second
- **Data Freshness**: <24 hours old
- **System Uptime**: 99.9%
- **Error Rate**: <0.1%

---

## Next Steps

1. **Data Loading**: Populate with real train/station data
2. **Integration Testing**: Test with production data volume
3. **Performance Tuning**: Monitor metrics and optimize bottlenecks
4. **Monitoring Setup**: Configure Prometheus/Grafana
5. **Scaling**: Deploy multiple API instances as needed
