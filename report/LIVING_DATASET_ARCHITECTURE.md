# Living Railway Dataset Architecture

## 🎯 System Overview

This is a **living dataset system** that continuously maintains accurate railway train information by:
- **Never trusting static data** - continuously validates against live APIs
- **Maintaining ground truth** - raw API responses stored as immutable JSON
- **Smart refreshing** - updates only when needed based on intelligent policies
- **Production-ready** - includes error handling, monitoring, and disaster recovery

```
Internet (RAPPID / IRCTC)
         ↓
Fetcher Engine (rappid_fetcher.py)
         ↓
Raw Live Store (data/raw_rappid/*.json)  ← Immutable ground truth
         ↓
Status Tracker (database.py)  ← Train status, freshness scores
         ↓
Structured Cache (data/rappid_structured/)  ← Working dataset
         ↓
Active-Only Routing (optimization_engine.py)  ← Only use ACTIVE trains
```

## 📋 Core Components

### 1. **Configuration Management** (`config.py`)
- Centralized settings for all modules
- Environment variable support for deployment
- Validation on startup
- Includes:
  - API endpoints and timeouts
  - Database connection strings
  - Refresh intervals and thresholds
  - Rate limiting and caching settings
  - Alerting configuration

### 2. **Database Schema** (`database.py`)
Tables for managing the living dataset:

**trains** - Train master data
```
train_no, train_name, status (ACTIVE/INACTIVE/UNKNOWN),
last_fetched, data_quality_score, raw_data_hash
```

**stations** - Station master data
```
station_code, station_name, location, zone
```

**train_stations** - Route details
```
train_id, station_id, sequence, arrival_time, departure_time,
platform_number, is_verified
```

**fetch_logs** - Audit trail
```
train_id, fetch_type, timestamp, status, response_time_ms,
records_fetched, error_message
```

**data_quality_metrics** - Historical metrics
```
timestamp, total_trains, active_trains, overall_freshness_score
```

### 3. **Logging & Observability** (`logger.py`)
- Structured JSON logging
- Audit trail for all operations
- File rotation and retention
- Contextual information tracking
- Performance metrics logging

### 4. **Raw Fetch Layer** (`rappid_fetcher.py`)
Core fetching with resilience:

Features:
- **Rate Limiting** - Token bucket algorithm (2 req/sec, 10 burst)
- **Circuit Breaker** - Stops calling failed APIs temporarily
- **Retry Logic** - Exponential backoff (2x multiplier)
- **Session Pooling** - Connection reuse for efficiency

Methods:
```python
fetcher = RAPPIDFetcher()
success, data, error = fetcher.fetch_train_details("16320")
fetcher.save_raw_response("16320", data)
results = fetcher.fetch_batch(["16320", "12951"])
```

### 5. **Refresh Policy** (`refresh_policy.py`)
Smart refresh decisions:

```
Train Status → Decision
UNKNOWN        → Fetch now (first time)
               → Recheck weekly after that
INACTIVE       → Skip by default
               → Recheck every 90 days
ACTIVE & <7d   → Use cache (100% fresh)
ACTIVE & 7-30d → Cache valid, refresh if available
ACTIVE & >30d  → Force refresh (expired)
```

**Priority Levels:**
- CRITICAL (4) - Force refresh immediately
- HIGH (3) - Include in next refresh batch
- MEDIUM (2) - Include if available capacity
- LOW (1) - Refresh if time permits
- SKIP (0) - No refresh needed

### 6. **Data Validation** (`validator.py`)
Pre-flight validation before using data:
- ✓ Duplicate detection
- ✓ Required field validation
- ✓ Date/time format checking
- ✓ Station sequence validation
- ✓ Platform consistency
- ✓ Timing logic validation

Output: `data/validation_report.json`

## 🔄 Data Flow

### Discovery Phase
1. **Initial Load** → Migrate existing Train_details.csv to database
2. **Mark Status** → All trains start as UNKNOWN
3. **Log Baseline** → Record initial state in fetch_logs

### Continuous Update
```
Weekly Refresh Job (scheduler.py)
         ↓
Refresh Policy Engine
         ↓
Prioritize by refresh decision
         ↓
Fetch CRITICAL → HIGH → MEDIUM → LOW trains
         ↓
Store raw JSON (immutable)
         ↓
Mark train status (ACTIVE/INACTIVE)
         ↓
Update structured cache
         ↓
Log all operations
         ↓
Update quality metrics
```

### Query Time
```
User Query
    ↓
Filter: status == ACTIVE only
    ↓
Check freshness score
    ↓
Use cached structured data
    ↓
Return results
```

## 📊 Configuration Examples

### .env file
```
# Database
DB_TYPE=sqlite
CACHE_VALID_DAYS=7
REFRESH_AFTER_DAYS=30

# API
RAPPID_API_BASE=https://rappid.zoppi.co.in
RAPPID_API_TIMEOUT=30

# Rate Limiting
RATE_LIMIT_RPS=2.0
CIRCUIT_BREAKER_THRESHOLD=5

# Caching
CACHE_MAX_SIZE_MB=500
CACHE_COMPRESSION=true

# Alerts
ENABLE_EMAIL_ALERTS=true
ALERT_EMAIL_RECIPIENTS=admin@railway.com
ALERT_INACTIVE_THRESHOLD=0.2
```

## 🚀 Usage Examples

### 1. Fetch Train Details
```python
from rappid_fetcher import fetcher

# Fetch single train
success, data, error = fetcher.fetch_train_details("16320")

# Fetch batch
results = fetcher.fetch_batch(["16320", "12951", "22691"])
```

### 2. Check Refresh Decision
```python
from refresh_policy import refresh_engine
from database import TrainStatus
from datetime import datetime, timedelta

decision = refresh_engine.decide_refresh(
    train_no="16320",
    current_status=TrainStatus.ACTIVE,
    last_fetched=datetime.utcnow() - timedelta(days=5),
    is_frequently_searched=True
)

print(decision.should_refresh)  # False (within cache valid period)
print(decision.reason)  # "Cache valid (5d < 7d)"
```

### 3. Validate Data
```python
from validator import validator

# Validate trains
report = validator.validate_trains(trains_list)
print(f"Valid: {report.is_valid}")
print(f"Errors: {report.error_count}")
validator.save_report(report)
```

### 4. Access Database
```python
from database import db, Train, TrainStatus

session = db.get_session()

# Get active trains
active_trains = session.query(Train).filter(
    Train.status == TrainStatus.ACTIVE
).all()

# Get recently updated
from datetime import timedelta, datetime
recent = session.query(Train).filter(
    Train.last_updated > datetime.utcnow() - timedelta(days=7)
).all()
```

## 📈 Monitoring & Health Checks

### Key Metrics
- **Active Trains** - Count of trains marked ACTIVE
- **Data Freshness** - % of trains <7 days old
- **API Success Rate** - Successful fetches / total attempts
- **Cache Hit Rate** - Queries served from cache
- **Avg Response Time** - API response latency

### Alerts
Automatic alerts when:
- >20% of trains become inactive
- API failure rate exceeds 10%
- Data freshness score < 60%
- Database backup fails
- Validation errors exceed threshold

### Health Endpoint
```
GET /health
{
    "status": "healthy",
    "active_trains": 3847,
    "inactive_trains": 247,
    "unknown_trains": 12,
    "data_freshness_percent": 85,
    "last_refresh": "2026-01-25T02:00:00Z",
    "cache_hit_rate": 0.94
}
```

## 🔒 Error Handling & Recovery

### Rate Limiting
- Token bucket: 2 req/sec, 10 burst
- Exponential backoff: 1s, 2s, 4s, 8s, 16s
- Circuit breaker: Stops after 5 consecutive failures

### Data Validation
- Pre-fetch validation on raw JSON
- Post-fetch validation on structured data
- Validation report saved to `data/validation_report.json`
- Failed validation blocks dataset usage

### Backup & Recovery
```python
from database import db

# Automatic daily backups
db.create_backup()  # Creates data/backups/train_master_20260125_123456.db

# Recovery (manual)
# 1. Stop application
# 2. Replace train_master.db with backup
# 3. Restart application
```

## 📋 Operational Procedures

### Weekly Maintenance
Every Sunday 02:00 UTC:
1. Run refresh policy on all trains
2. Fetch CRITICAL and HIGH priority trains
3. Validate all data
4. Update quality metrics
5. Generate weekly report
6. Check alerts

### Monthly Operations
- Archive old data (>30 days) to `data/archives/`
- Review validation errors
- Update train status classifications
- Database optimization/vacuum

### Quarterly Reviews
- Analyze trends in data freshness
- Review API performance
- Update refresh thresholds if needed
- Archive quarterly snapshots

## 🔧 Troubleshooting

### Problem: "Circuit breaker OPEN"
- API is temporarily down
- Wait 60 seconds (configurable in CIRCUIT_BREAKER_TIMEOUT)
- System will automatically retry

### Problem: "Rate limit timeout"
- Too many concurrent requests
- Check RATE_LIMIT_RPS setting
- Increase if API allows

### Problem: "Validation report shows many errors"
- Data quality issue detected
- Review VALIDATION_REPORT.md
- May indicate API format change
- Contact API provider if format changed

### Problem: "Data freshness score < 60%"
- Many trains haven't been updated recently
- Check if refresh job is running
- Verify API connectivity
- Check circuit breaker status

## 📚 Further Reading

- [RAPPID API Docs](https://rappid.zoppi.co.in/api/docs)
- [Database Schema](./database.py)
- [Configuration Reference](./config.py)
- [Monitoring Dashboard](./dashboard_api.py)
- [Test Suite](./test_pipeline.py)

## 🎓 Key Design Principles

1. **Never Trust Static Data** - Always validate against live sources
2. **Immutable Ground Truth** - Raw API responses are permanent records
3. **Smart Caching** - Cache valid based on age and importance
4. **Audit Everything** - Complete audit trail of all operations
5. **Fail Gracefully** - Use cache and degradation when APIs fail
6. **Monitor Continuously** - Track metrics and alert on issues
7. **Scale Gradually** - Start with SQLite, migrate to PostgreSQL as needed

## 🚀 Deployment Checklist

- [ ] Create `.env` with all required variables
- [ ] Initialize database with `python database.py`
- [ ] Migrate existing data with `python migration.py`
- [ ] Run validation with `python validator.py`
- [ ] Start scheduler with `python scheduler.py`
- [ ] Enable monitoring dashboard
- [ ] Setup alerting webhooks
- [ ] Configure backup location
- [ ] Test recovery process
- [ ] Document any custom settings

---

**Last Updated:** January 25, 2026
**System Version:** 3.0 (Living Dataset)
**Status:** Production Ready
