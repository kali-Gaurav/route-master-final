# Production Pipeline - Developer Guide

## Overview for Developers

This guide explains how to extend, modify, and develop the production pipeline system.

---

## Architecture at a Glance

```
HTTP Request
    ↓
FastAPI (api.py)
    ↓
RoutingEngine (routing_engine.py)
    ↓
Database (database.py)
    ↓
Raw/Clean Data Layers
    ↓
Background Jobs (jobs.py) ← Ingestion (ingestion.py)
    ↓
Observability (observability.py)
```

---

## Code Organization

### Entry Point: `main.py`
```python
class ProductionPipeline:
    def __init__(self):          # Initialize all components
    async def start(self):       # Start system
    async def shutdown(self):    # Cleanup
    async def run_server(self):  # Run FastAPI server
```

**When to modify**: If you need to add new initialization steps or components

### Configuration: `config.py`
```python
@dataclass
class SystemConfig:
    database: DatabaseConfig
    ingestion: IngestionConfig
    api: APIConfig
    logging: LoggingConfig
    metrics: MetricsConfig
```

**When to modify**: Adding new configuration options or changing defaults

### Database: `database.py`
```python
Base              # SQLAlchemy declarative base
Train             # Train model
Station           # Station model
TrainStation      # Junction table
RawPayload        # Raw API responses
CleanDataset      # Processed data
RoutesCache       # Cached results
SearchLog         # User searches
PerformanceLog    # Metrics
ErrorLog          # Errors
```

**When to modify**: Changing schema, adding new tables, modifying relationships

### Data Ingestion: `ingestion.py`
```python
AsyncHTTPClient
    ├── start()              # Initialize session
    ├── close()              # Cleanup
    ├── fetch()              # Fetch single URL
    └── fetch_batch()        # Fetch multiple URLs

RAPPIDFetcher
    ├── fetch_trains()       # Get train data
    ├── fetch_stations()     # Get station data
    └── fetch_train_details()# Get train details
```

**When to modify**: Adding new data sources, changing API endpoints, adjusting rate limits

### Data Pipeline: `data_pipeline.py`
```python
DataValidator
    ├── validate_station_code()
    ├── validate_train_number()
    ├── validate_train_data()
    └── validate_station_data()

DataNormalizer
    ├── normalize_station_code()
    ├── normalize_name()
    └── normalize_time()

CleanDataPipeline
    ├── process_train()
    └── process_station()
```

**When to modify**: Changing validation rules, adding new normalization logic, adding validation

### Routing Engine: `routing_engine.py`
```python
RouteGraph
    ├── _build_graph()           # Load from DB
    └── get_connected_trains()   # Query connections

RoutingEngine
    ├── find_direct_routes()     # Direct paths
    ├── find_routes()            # All routes
    ├── rank_routes()            # Sort by preference
    ├── filter_routes()          # Limit results
    └── search()                 # Complete search
```

**When to modify**: Adding new routing algorithms, changing ranking logic, optimizing performance

### API Layer: `api.py`
```python
create_app()        # Create FastAPI application
    ├── /api/v1/search       # Main feature
    ├── /api/v1/health       # Health check
    ├── /api/v1/metrics      # Metrics
    ├── /api/v1/stations     # Station list
    └── /api/v1/trains       # Train list
```

**When to modify**: Adding endpoints, changing response format, adding validation

### Background Jobs: `jobs.py`
```python
JobExecutor
    ├── job_daily_data_refresh()
    ├── job_retry_failed_ingestions()
    ├── job_clean_expired_cache()
    ├── job_aggregate_metrics()
    ├── job_cleanup_old_logs()
    └── job_health_check()

JobScheduler
    ├── schedule_jobs()       # Setup schedule
    ├── start()               # Start scheduler
    ├── shutdown()            # Stop scheduler
    └── get_jobs_status()     # Job information
```

**When to modify**: Adding new jobs, changing schedules, modifying job logic

### Observability: `observability.py`
```python
JSONFormatter       # Structured logging
MetricsCollector    # Record & analyze metrics
PerformanceMonitor  # Track latencies
ErrorTracker        # Error frequency
setup_logging()     # Initialize logging
```

**When to modify**: Adding new metrics, changing log format, adding alerting

---

## Common Development Tasks

### 1. Add a New API Endpoint

**File**: `api.py`

```python
@app.get("/api/v1/new-endpoint", tags=["MyFeature"])
async def new_endpoint(query_param: str):
    """Get something new"""
    session = db_manager.get_session()
    try:
        # Do something
        return {"result": "data"}
    finally:
        session.close()
```

**Steps**:
1. Define Pydantic schema (optional)
2. Add endpoint function
3. Add error handling
4. Test with curl
5. Update API documentation

### 2. Add a New Database Table

**File**: `database.py`

```python
class MyTable(Base):
    __tablename__ = "my_table"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_name", "name"),
    )
```

**Steps**:
1. Define model class inheriting from Base
2. Add columns with appropriate types
3. Add indexes for frequently queried columns
4. Add foreign keys if needed
5. Run `db_manager.create_all_tables()` to create table

### 3. Add a New Validation Rule

**File**: `data_pipeline.py`

```python
def validate_custom_field(self, value: str) -> Tuple[bool, Optional[str]]:
    """Validate custom field
    
    Args:
        value: Value to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value or not isinstance(value, str):
        return False, "Value is required"
    
    if len(value) < 3:
        return False, "Value too short"
    
    return True, None
```

**Steps**:
1. Add validation method to DataValidator
2. Call in appropriate validate_*_data() method
3. Log validation failures
4. Test with sample data

### 4. Add a New Background Job

**File**: `jobs.py`

```python
def job_my_new_task(self, session: Session) -> bool:
    """My new task description
    
    Args:
        session: Database session
        
    Returns:
        Success status
    """
    logger.info("Starting my_new_task")
    
    try:
        # Do work
        logger.info("Completed my_new_task")
        return True
    
    except Exception as e:
        logger.error(f"my_new_task failed: {e}")
        return False
```

Then in `JobScheduler.schedule_jobs()`:
```python
self.scheduler.add_job(
    self._wrap_job("my_new_task", self.executor.job_my_new_task),
    trigger=CronTrigger(hour=12, minute=0),  # Run at noon daily
    id="my_new_task",
    name="My New Task",
    replace_existing=True
)
```

**Steps**:
1. Implement job method in JobExecutor
2. Add schedule in JobScheduler.schedule_jobs()
3. Test manually first
4. Monitor logs to verify execution

### 5. Add a New Metric

**File**: `observability.py`

```python
def log_my_metric(self, value: float, source: str):
    """Log my custom metric"""
    self.metrics_collector.record(
        "my_metric_name",
        value,
        tags={"source": source}
    )
```

Then use it:
```python
perf_monitor = get_performance_monitor()
perf_monitor.log_my_metric(42.5, "api")
```

**Steps**:
1. Add logging method to PerformanceMonitor
2. Use `metrics_collector.record()`
3. Check metrics via `/api/v1/metrics` endpoint
4. Review in logs/application.log

---

## Testing

### Unit Testing

```python
# test_routing_engine.py
def test_find_direct_routes():
    session = db.get_session()
    engine = RoutingEngine(session)
    routes = engine.find_direct_routes("NDLS", "KOTA")
    assert len(routes) > 0
    assert routes[0].origin == "NDLS"
    assert routes[0].destination == "KOTA"
```

### Integration Testing

```python
# test_api_endpoints.py
def test_search_endpoint():
    response = client.post(
        "/api/v1/search",
        json={
            "origin": "NDLS",
            "destination": "KOTA",
            "max_results": 10
        }
    )
    assert response.status_code == 200
    assert response.json()["success"] == True
```

### Performance Testing

```bash
# Load test with 100 concurrent requests
ab -n 1000 -c 100 http://localhost:8000/api/v1/health
```

---

## Debugging

### Enable Debug Logging

```python
from production_pipeline.config import get_config
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Now you get DEBUG level logs
```

### Database Inspection

```python
from production_pipeline.database import DatabaseManager, Train, TrainStation

db = DatabaseManager("sqlite:///./data/railway.db")
session = db.get_session()

# Check a train
train = session.query(Train).filter_by(train_no="12345").first()
print(f"Train: {train.train_name}")

# Get its route
for stop in train.train_stations:
    print(f"  → {stop.station.name}")

session.close()
```

### Check Cached Data

```python
from production_pipeline.ingestion import CacheManager

cache = CacheManager("./data/cache")
cached_data = cache.get("RAPPID", "trains")
print(f"Cached: {cached_data}")
```

### Analyze Metrics

```python
from production_pipeline.observability import get_metrics_collector

collector = get_metrics_collector()
stats = collector.get_all_metrics()
for metric_name, stats_data in stats.items():
    print(f"{metric_name}: avg={stats_data['avg']:.2f}")
```

---

## Performance Optimization

### Database Query Optimization

1. **Add Indexes**: See database.py for examples
2. **Use Filtering**: Filter in SQL, not Python
3. **Limit Results**: Always use LIMIT
4. **Avoid N+1**: Use eager loading

### API Response Optimization

1. **Cache Results**: Cache cache cache (config.ingestion.cache_ttl_seconds)
2. **Batch Operations**: Fetch multiple records together
3. **Limit Response Size**: Use pagination
4. **Async Operations**: Use async endpoints

### Memory Optimization

1. **Clear Cache**: Call cache.clear_expired()
2. **Batch Processing**: Process in chunks
3. **Close Sessions**: Always close db sessions
4. **Monitor Memory**: Check logs for memory issues

---

## Deployment Checklist

Before deploying to production:

- [ ] All tests passing
- [ ] Database migrations applied
- [ ] Environment variables set
- [ ] SSL/TLS configured
- [ ] Monitoring set up
- [ ] Backups configured
- [ ] Rate limits adjusted
- [ ] Cache TTL optimized
- [ ] Error alerting enabled
- [ ] Documentation updated

---

## Code Style

### Python Style Guide
- Follow PEP 8
- Use type hints
- Write docstrings
- Keep functions small
- Use descriptive names

### Docstring Format
```python
def my_function(param1: str, param2: int) -> bool:
    """Short description
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When something is invalid
    """
    pass
```

---

## Resources

### Frameworks & Libraries
- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://sqlalchemy.org/
- **APScheduler**: https://apscheduler.readthedocs.io/
- **Pydantic**: https://pydantic-docs.helpmanual.io/

### Python Async
- **AsyncIO**: https://docs.python.org/3/library/asyncio.html
- **aiohttp**: https://docs.aiohttp.org/

### Databases
- **PostgreSQL**: https://www.postgresql.org/docs/
- **SQLite**: https://www.sqlite.org/docs.html

---

## Getting Help

1. **Read Code Comments**: Each module has docstrings
2. **Check Tests**: Test examples show usage
3. **Review Logs**: Check logs/application.log for errors
4. **Ask Questions**: Review architecture.md
5. **Debug**: Use Python debugger or pdb

---

## Contributing Guidelines

1. **Fork/Branch**: Create feature branch
2. **Write Tests**: Add unit tests for new code
3. **Follow Style**: Match existing code style
4. **Document**: Add docstrings and comments
5. **Test**: Run all tests before PR
6. **Update Docs**: Update relevant markdown files

---

## Next: Advanced Topics

### Horizontal Scaling
- Deploy multiple API instances
- Use Redis for distributed cache
- Use Celery for async jobs
- Load balance with Nginx

### High Availability
- Database replication
- API instance redundancy
- Automated failover
- Health checks

### Advanced Monitoring
- Prometheus metrics export
- Grafana dashboards
- ELK stack logging
- Alert rules

---

## Questions?

1. Check docstrings in code
2. Review ARCHITECTURE.md
3. Look at test examples
4. Check logs for errors
5. Read relevant documentation

**Happy developing!** 🚀
