# Consolidated Modules Quick Reference

## 🎯 Core 5 Modules (After Consolidation)

### 1. **security_system.py** - Authentication & Multi-Tenancy
Complete security subsystem combining auth, tenants, and audit.

```python
from security_system import (
    TenantManager,        # Tenant CRUD
    APIKeyManager,        # API key management
    record_audit,         # Audit logging
    get_audit_logs,       # Query audit trail
    audit_summary         # Compliance stats
)

# Create tenant
tenant_id = TenantManager.create('IRCTC Partner')
api_key = APIKeyManager.create(tenant_id)

# Audit trail
record_audit('route_search', tenant_id=tenant_id, 
             details={'source': 'NDLS', 'dest': 'HWH'})
```

---

### 2. **database_system.py** - Database & Connections
Complete database infrastructure with pooling, migration, and ORM.

```python
from database_system import (
    DatabaseConnection,   # Legacy SQLite connection
    DatabasePool,        # PostgreSQL connection pooling
    DatabaseMigrator,    # Safe migration
    Tenant,              # ORM models
    APIKey,
    SystemJob,
    TrainMaster,
    # ... other models
)

# Get pooled session (PostgreSQL)
session = DatabasePool.get_session(DATABASE_URL)
tenants = session.query(Tenant).all()

# Migrate SQLite → PostgreSQL
result = DatabaseMigrator.migrate(
    postgres_url='postgresql://...',
    dry_run=False,
    backup_first=True
)
```

---

### 3. **infrastructure.py** - Caching & Async Jobs
Complete async and caching infrastructure.

```python
from infrastructure import (
    CacheManager,         # Redis + in-memory cache
    RouteCache,          # Route result caching
    JobManager,          # Job queue management
    generate_routes_async, # Celery tasks
    batch_routes,
    app as celery_app    # Celery application
)

# Cache management
RouteCache.set('NDLS', 'HWH', '2026-01-28', routes)
cached = RouteCache.get('NDLS', 'HWH', '2026-01-28')

# Job queue
job_id = JobManager.enqueue('generate-routes', 
    payload={'source': 'NDLS', 'dest': 'HWH'})
job = JobManager.get(job_id)
JobManager.update_status(job_id, 'completed', result={...})

# Async tasks
result = generate_routes_async.delay('NDLS', 'HWH', '2026-01-28')
```

---

### 4. **route_engine.py** - Route Finding & Display
Complete route search and optimization engine.

```python
from route_engine import (
    RouteEngine,          # Main engine
    route_engine,         # Global instance
    find_routes,          # Convenience function
    find_direct           # Direct routes only
)

# Quick search
result = route_engine.quick_search('NDLS', 'HWH', '2026-01-28')

# Detailed search
routes = route_engine.find_routes_with_transfers(
    'NDLS', 'HWH',
    max_transfers=3,
    max_results=100
)

# Display
table = RouteEngine.format_routes_table(routes['direct'])
stats = route_engine.get_route_statistics(routes)
```

---

### 5. **monitoring.py** - Metrics & Observability
Complete monitoring, logging, and health checking.

```python
from monitoring import (
    MetricsCollector,     # Metrics collection
    StructuredLogger,     # Structured logging
    HealthCheck,          # System health
    rate_limit_check,     # Rate limit decorator
    track_request,        # Quick functions
    is_rate_limited,
    get_metrics,
    get_health
)

# Metrics
MetricsCollector.track_request(api_key)
MetricsCollector.track_latency(api_key, 125.5)
if MetricsCollector.is_rate_limited(api_key):
    return error_response("Rate limited")

# Logging
logger = StructuredLogger('my_module')
logger.log_request(api_key, '/routes', 'POST', source='NDLS')
logger.log_error(api_key, 'Connection timeout', error='...')

# Health
health = HealthCheck.get_system_health()
print(health['database'])  # {'database': True, 'type': 'postgres'}
print(health['cache'])     # {'cache': True, 'type': 'redis'}

# Prometheus metrics
metrics_text = MetricsCollector.get_prometheus_metrics()
```

---

## 🔄 Common Usage Patterns

### Authentication Flow
```python
from security_system import APIKeyManager

def require_api_key(api_key):
    result = APIKeyManager.validate(api_key)
    if not result:
        raise AuthError("Invalid API key")
    return result['tenant_id']
```

### Route Search with Caching
```python
from route_engine import route_engine
from infrastructure import RouteCache

def search_routes(source, dest, date):
    # Try cache first
    cached = RouteCache.get(source, dest, date)
    if cached:
        return cached
    
    # Compute and cache
    routes = route_engine.find_routes_with_transfers(source, dest)
    RouteCache.set(source, dest, date, routes)
    return routes
```

### Background Job Processing
```python
from infrastructure import JobManager, generate_routes_async

def generate_routes_background(source, dest, date):
    # Queue job
    job_id = JobManager.enqueue('generate-routes',
        payload={'source': source, 'dest': dest, 'date': date})
    
    # Or use Celery async
    task = generate_routes_async.delay(source, dest, date)
    
    return job_id
```

### Database Query
```python
from database_system import DatabasePool, Tenant

# Get session from pool
session = DatabasePool.get_session(DATABASE_URL)
try:
    tenants = session.query(Tenant).all()
finally:
    session.close()
```

### Rate Limiting
```python
from monitoring import MetricsCollector, rate_limit_check

@rate_limit_check
def api_call(api_key, **kwargs):
    # Function body
    pass

# Or manual
MetricsCollector.track_request(api_key)
if MetricsCollector.is_rate_limited(api_key):
    raise RateLimitError()
```

---

## 📊 Module Responsibilities

| Module | Owns |
|--------|------|
| **security_system.py** | Authentication, tenants, audit, compliance |
| **database_system.py** | Connections, pooling, migration, ORM, schema |
| **infrastructure.py** | Caching, async tasks, job queues, Celery |
| **route_engine.py** | Route finding, display, optimization, analytics |
| **monitoring.py** | Metrics, logging, rate-limiting, health checks |

---

## ⚡ Performance Tips

### Cache Management
```python
# Set custom TTL
RouteCache.set(source, dest, date, routes, ttl=7200)

# Clear cache on update
RouteCache.clear()  # Clear all route cache
CacheManager.clear(namespace='routes')  # Namespace clear
```

### Connection Pooling
```python
# Get pool status
status = DatabasePool.get_pool_status(DATABASE_URL)
print(f"Active: {status['checked_out']}/20 connections")

# Pool auto-manages connections
# No manual connection opening/closing needed
```

### Async Tasks
```python
# Enqueue with long timeout
task = generate_routes_async.apply_async(
    args=('NDLS', 'HWH'),
    expires=3600,  # 1 hour timeout
    retry=3        # Retry 3 times
)

# Check result
result = task.get()
```

---

## 🐛 Debugging

### Check Metrics
```python
from monitoring import MetricsCollector

metrics = MetricsCollector.get_all_metrics()
print(metrics['per_key']['your_api_key'])
# Shows: requests, errors, latency, rate_limit status
```

### View Audit Trail
```python
from security_system import get_audit_logs

logs = get_audit_logs(tenant_id='xxx', limit=100)
for log in logs:
    print(f"{log['created_at']} | {log['action']} | {log['details']}")
```

### Health Check
```python
from monitoring import HealthCheck

health = HealthCheck.get_system_health()
if not health['database']['database']:
    print("Database is down!")
```

### Check Rate Limit
```python
from monitoring import MetricsCollector

is_limited, current, limit = MetricsCollector.is_rate_limited(api_key)
if is_limited:
    print(f"Rate limited: {current}/{limit} requests/min")
```

---

## 🚀 Integration Checklist

- [ ] Import from consolidated modules (not old split files)
- [ ] Update CLI (rosctl.py) imports
- [ ] Update API (ros_api.py) imports
- [ ] Update workers (ros_worker.py) imports
- [ ] Run tests to verify compatibility
- [ ] Update any custom scripts
- [ ] Deploy to production

---

## 📚 Reference

**Old scattered approach:**
```python
from auth import validate_api_key
from tenants import create_tenant
from audit import record_audit
from database import DatabaseConnection
from cache import get_cached_routes
from jobs import enqueue_job
from route_finder import RouteFinder
from metrics import track_request
# Too many imports!
```

**New consolidated approach:**
```python
from security_system import APIKeyManager, TenantManager, record_audit
from database_system import DatabaseConnection, DatabaseMigrator
from infrastructure import RouteCache, JobManager
from route_engine import route_engine
from monitoring import MetricsCollector
# Clear, organized, professional!
```

---

**Ready to use! Clean, consolidated, professional architecture! 🎉**
