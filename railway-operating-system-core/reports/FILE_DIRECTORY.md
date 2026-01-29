# Railway Operating System - File Directory

## 🎯 Core Consolidated Modules (NEW - USE THESE!)

### 1. **security_system.py** ⭐ [Complete Auth Subsystem]
- Classes: `TenantManager`, `APIKeyManager`
- Functions: `record_audit()`, `get_audit_logs()`, `audit_summary()`
- 480 lines | Merged: auth.py + tenants.py + audit.py
- **Use for:** API keys, tenants, audit trails, compliance

### 2. **database_system.py** ⭐ [Complete DB Subsystem]
- Classes: `DatabaseConnection`, `DatabasePool`, `DatabaseMigrator`
- Models: `Tenant`, `APIKey`, `SystemJob`, `JobLog`, `SystemAudit`, `TrainMaster`, etc.
- 620 lines | Merged: database.py + db_pool.py + db_migrator.py + schema.py
- **Use for:** Database operations, pooling, migration, ORM queries

### 3. **infrastructure.py** ⭐ [Complete Async & Cache Subsystem]
- Classes: `CacheManager`, `RouteCache`, `JobManager`
- Celery: `app`, `generate_routes_async()`, `batch_routes()`
- 510 lines | Merged: cache.py + tasks.py + jobs.py
- **Use for:** Caching, async jobs, job queues, Celery

### 4. **route_engine.py** ⭐ [Complete Route Subsystem]
- Class: `RouteEngine` (global instance: `route_engine`)
- Functions: `find_routes()`, `find_direct()`
- 420 lines | Merged: route_finder.py + route_display.py + quick_routes.py + profile_routes.py
- **Use for:** Route finding, display, optimization

### 5. **monitoring.py** ⭐ [Complete Monitoring Subsystem]
- Classes: `MetricsCollector`, `StructuredLogger`, `HealthCheck`
- Decorator: `@rate_limit_check`
- 450 lines | Merged: metrics.py + new integrated monitoring
- **Use for:** Metrics, logging, rate-limiting, health checks

---

## 🔧 Integration Files (UPDATE THESE!)

### **rosctl.py** - CLI Dispatcher
- Status: Needs import update to use consolidated modules
- Uses: security_system, database_system, infrastructure, route_engine, monitoring
- Commands: generate-routes, worker, job-status, backup-db, restore-db, create-tenant, issue-key, migrate-db

### **ros_api.py** - FastAPI Application
- Status: Needs import update
- Uses: security_system, database_system, infrastructure, route_engine, monitoring
- Endpoints: /routes, /jobs, /metrics

### **ros_worker.py** - Background Worker
- Status: Needs import update
- Uses: infrastructure (JobManager, Celery), database_system, route_engine, monitoring
- Function: Polls and processes jobs from queue

---

## 📦 Supporting Files (KEEP AS-IS)

### **config.py** - Configuration
- Database paths, timeout settings, colors, logging

### **requirements.txt** - Python Dependencies
- FastAPI, SQLAlchemy, psycopg2, redis, celery, etc.

### **main.py** - Entry Point
- Alternative CLI entry point

---

## 📚 Documentation Files (CREATED)

### **CONSOLIDATION_COMPLETE_REPORT.md** 📄
Comprehensive analysis of consolidation with before/after comparison

### **CONSOLIDATION_SUMMARY.md** 📄
Strategic overview of consolidation with file mapping

### **CONSOLIDATED_MODULES_GUIDE.md** 📄
Quick reference guide with usage examples

---

## 🗑️ OLD FILES (To Be Removed After Integration)

These are now consolidated into the 5 main modules. Keep for reference but don't import from:

```
auth.py                    → Use: security_system.APIKeyManager
tenants.py                 → Use: security_system.TenantManager
audit.py                   → Use: security_system.record_audit()
database.py                → Use: database_system.DatabaseConnection
db_pool.py                 → Use: database_system.DatabasePool
db_migrator.py             → Use: database_system.DatabaseMigrator
schema.py                  → Use: database_system ORM models
cache.py                   → Use: infrastructure.CacheManager
tasks.py                   → Use: infrastructure.generate_routes_async
jobs.py                    → Use: infrastructure.JobManager
route_finder.py            → Use: route_engine.RouteEngine
route_display.py           → Use: route_engine.RouteEngine.format_*
metrics.py                 → Use: monitoring.MetricsCollector
```

---

## 🧪 Test Files

### **tests.py** - Unit Tests
- 15 comprehensive tests (all passing)
- Tests for: auth, tenants, audit, rate-limiting, job-logs, metrics
- Run: `pytest tests.py -v`

### **test_migration.py** - Migration Tests
- 5 integration tests for database migration
- Tests dry-run, verification, data integrity, rollback
- Run: `python test_migration.py --postgres-url <url>`

---

## 🐳 Docker & Deployment

### **docker-compose.prod.yml**
Full production stack: PostgreSQL, Redis, Celery, FastAPI

### **Dockerfile.api**
FastAPI application container

### **Dockerfile.celery**
Celery worker container

### **Dockerfile.backend**
General backend service container

---

## 📊 Data & Scripts

### **backups/** - Database Backups
Automatic backup storage location

### **data/** - Data Files
Train, station, and schedule data

### **logs/** - Application Logs
Structured logs from operations

### **production.db** - SQLite Database
Current development database (will migrate to PostgreSQL)

---

## 🎯 Quick Import Reference

### Before (Old - DON'T USE)
```python
from auth import create_api_key
from tenants import create_tenant
from database import DatabaseConnection
from cache import get_cached_routes
from jobs import enqueue_job
from metrics import track_request
```

### After (New - USE THIS)
```python
from security_system import APIKeyManager, TenantManager
from database_system import DatabaseConnection
from infrastructure import RouteCache, JobManager
from monitoring import MetricsCollector
```

---

## 📋 File Organization Summary

```
railway-operating-system-core/
├── 🎯 CORE MODULES (5 files - USE THESE)
│   ├── security_system.py
│   ├── database_system.py
│   ├── infrastructure.py
│   ├── route_engine.py
│   └── monitoring.py
│
├── 🔧 INTEGRATION (3 files - UPDATE IMPORTS)
│   ├── rosctl.py
│   ├── ros_api.py
│   └── ros_worker.py
│
├── ⚙️ CONFIG & SUPPORT
│   ├── config.py
│   ├── main.py
│   └── requirements.txt
│
├── 🧪 TESTING (2 files)
│   ├── tests.py
│   └── test_migration.py
│
├── 📚 DOCUMENTATION (4 files)
│   ├── CONSOLIDATION_COMPLETE_REPORT.md
│   ├── CONSOLIDATION_SUMMARY.md
│   ├── CONSOLIDATED_MODULES_GUIDE.md
│   └── README.md
│
├── 🐳 DEPLOYMENT (4 files)
│   ├── docker-compose.prod.yml
│   ├── Dockerfile.api
│   ├── Dockerfile.celery
│   └── Dockerfile.backend
│
├── 📦 DATA (3 dirs)
│   ├── backups/
│   ├── data/
│   └── logs/
│
├── 📊 DATABASE
│   └── production.db
│
└── 🗑️ OLD FILES (for reference only)
    ├── auth.py [CONSOLIDATED]
    ├── tenants.py [CONSOLIDATED]
    ├── audit.py [CONSOLIDATED]
    ├── database.py [CONSOLIDATED]
    ├── db_pool.py [CONSOLIDATED]
    ├── db_migrator.py [CONSOLIDATED]
    ├── schema.py [CONSOLIDATED]
    ├── cache.py [CONSOLIDATED]
    ├── tasks.py [CONSOLIDATED]
    ├── jobs.py [CONSOLIDATED]
    ├── route_finder.py [CONSOLIDATED]
    ├── route_display.py [CONSOLIDATED]
    └── metrics.py [CONSOLIDATED]
```

---

## ✅ Next Steps

1. **Review** the consolidation (CONSOLIDATION_COMPLETE_REPORT.md)
2. **Understand** the modules (CONSOLIDATED_MODULES_GUIDE.md)
3. **Update** imports in rosctl.py, ros_api.py, ros_worker.py
4. **Test** with pytest tests.py -v
5. **Deploy** with confidence!

---

## 💡 Key Takeaway

Instead of importing from 15+ scattered files:
```python
from auth import ...
from tenants import ...
from audit import ...
from database import ...
from db_pool import ...
from cache import ...
from jobs import ...
from route_finder import ...
from metrics import ...
```

Now import from 5 organized modules:
```python
from security_system import ...
from database_system import ...
from infrastructure import ...
from route_engine import ...
from monitoring import ...
```

**Much cleaner! Much more professional! Much easier to maintain!** 🚀
