# Living Railway Dataset System - Quick Start Guide

## 🚀 System Overview

A production-ready **living dataset system** that continuously maintains accurate railway train information through:
- **Smart fetching** - Only update when needed
- **Intelligent validation** - Comprehensive data quality checks
- **Automatic backups** - Daily database backups
- **Health monitoring** - Real-time alerts on issues
- **Complete audit trail** - Full logging of all operations

---

## ⚡ Quick Start (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
python -c "from database import db; print('✓ Database initialized')"
python -c "from migration import run_migration; run_migration()"
```

### 3. Test Basic Operations
```bash
# Test fetching
python -c "from rappid_fetcher import fetcher; success, data, error = fetcher.fetch_train_details('16320'); print(f'Fetch successful: {success}')"

# Test validation
python -c "from validator import validator; report = validator.validate_trains([{'train_no': '16320', 'train_name': 'Test', 'status': 'ACTIVE'}]); print(f'Valid: {report.is_valid}')"

# Test quality scoring
python -c "from quality_scorer import scorer; from datetime import datetime, timedelta; score = scorer.score_train({'train_no': '16320', 'train_name': 'Test', 'status': 'ACTIVE', 'last_updated': datetime.utcnow() - timedelta(days=2)}); print(f'Score: {score.overall_score}, Grade: {score.data_quality_grade}')"
```

### 4. Start Scheduler (Optional)
```bash
pip install apscheduler  # Required for scheduler
python scheduler.py      # Starts background scheduler
```

---

## 🔄 RAPPID Bulk Loading Pipeline

The system now uses a **database-driven** architecture that ingests all RAPPID train data into SQLite for fast, production-scale operations.

### Full Bulk Load (All 200k+ Records)

```bash
# Full ingestion of all RAPPID data
python scripts/bulk_load_rappid.py --full
```

**Expected Results:**
- **197,469 records** processed from RAPPID CSV
- **9,880 unique trains** inserted with metadata
- **3,874 unique stations** mapped and indexed
- **92,226 train-station relationships** created
- **Processing time:** ~60 seconds (3,300 rows/sec)
- **RAM usage:** 100-150 MB peak (chunked 10k rows/batch)

### Sample Load (1000 Records)

For testing or CI/CD pipelines:

```bash
python scripts/bulk_load_rappid.py --sample
```

### Data Refresh & Last_Updated Tracking

The pipeline tracks when records are last updated to support incremental refresh:

```python
# In database_manager.py
cursor.execute("""
    INSERT INTO train_stations (train_id, station_id, station_sequence, arrival, departure, last_updated)
    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(train_id, station_id) DO UPDATE SET
        last_updated = CURRENT_TIMESTAMP
""")
```

**Check last updated records:**

```python
from database_manager import get_db

db = get_db()
cursor = db.conn.cursor()
cursor.execute("""
    SELECT train_id, station_id, last_updated 
    FROM train_stations 
    ORDER BY last_updated DESC 
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"Train {row[0]} at Station {row[1]}: {row[2]}")
```

### Cache Invalidation

After bulk loading, the graph cache is automatically rebuilt on the next API request via the `GraphSingleton` pattern:

```python
from route_optimizer import ParetoTrainRouter

# Automatic cache rebuild on first request
router = ParetoTrainRouter()  # Lazy-loads and caches graph

# Force rebuild if needed
router._graph_singleton = None  
router = ParetoTrainRouter()  # Rebuilds from database
```

**Cache statistics:**
- **Build time:** <1s for full graph (9,880 trains, 92,226 edges)
- **Memory:** ~50-70 MB cached in RAM
- **Query time:** O(1) per API request (no rebuild)

---

## 📁 File Structure

```
├── config.py                      # Configuration management
├── database.py                    # Database schema & ORM
├── logger.py                      # Logging system
├── rappid_fetcher.py             # API fetcher with resilience
├── refresh_policy.py             # Smart refresh decisions
├── validator.py                  # Data validation
├── incremental_updater.py        # Incremental updates
├── quality_scorer.py             # Quality scoring
├── migration.py                  # CSV to database migration
├── backup_manager.py             # Backup & recovery
├── alerting_system.py            # Alerts & notifications
├── scheduler.py                  # Automated scheduling
├── test_pipeline.py              # Test suite
├── LIVING_DATASET_ARCHITECTURE.md # Full architecture
├── IMPLEMENTATION_SUMMARY.md     # What's implemented
├── data/
│   ├── raw_rappid/               # Raw API responses
│   ├── rappid_structured/        # Structured data
│   ├── fetch_logs/               # Fetch logs
│   ├── archives/                 # Historical data
│   └── backups/                  # Database backups
└── logs/
    ├── railway_dataset.log
    ├── rappid_fetcher.log
    └── *.log                      # All operation logs
```

---

## 💻 Core Operations

### Fetch Train Data
```python
from rappid_fetcher import fetcher

# Single train
success, data, error = fetcher.fetch_train_details("16320")

# Multiple trains
results = fetcher.fetch_batch(["16320", "12951", "22691"])
```

### Check Refresh Decision
```python
from refresh_policy import refresh_engine
from database import TrainStatus
from datetime import datetime, timedelta

decision = refresh_engine.decide_refresh(
    train_no="16320",
    current_status=TrainStatus.ACTIVE,
    last_fetched=datetime.utcnow() - timedelta(days=5)
)
print(f"Refresh needed: {decision.should_refresh}")
```

### Validate Data
```python
from validator import validator

report = validator.validate_trains(trains_list)
print(f"Errors: {report.error_count}, Warnings: {report.warning_count}")
validator.save_report(report)
```

### Score Data Quality
```python
from quality_scorer import scorer

score = scorer.score_train(train_dict)
print(f"Score: {score.overall_score:.1f}/100, Grade: {score.data_quality_grade}")
```

### Create Backup
```python
from backup_manager import backup_manager

backup_path = backup_manager.create_backup()
print(f"Backup created: {backup_path}")
```

### Check System Health
```python
from alerting_system import alertingSystem

alert = alertingSystem.check_inactive_trains_threshold(total=3847, inactive=769)
if alert:
    alertingSystem.send_alert(alert)
```

---

## 🔧 Configuration

Create a `.env` file (copy from `.env.example`):

```env
# Database
DB_TYPE=sqlite

# RAPPID API
RAPPID_API_BASE=https://rappid.zoppi.co.in
RAPPID_API_TIMEOUT=30

# Refresh Policy
CACHE_VALID_DAYS=7
REFRESH_AFTER_DAYS=30

# Rate Limiting
RATE_LIMIT_RPS=2.0
RATE_LIMIT_BURST=10

# Logging
LOG_LEVEL=INFO

# Alerts
ENABLE_EMAIL_ALERTS=false
ENABLE_WEBHOOK_ALERTS=false
```

---

## 📊 Key Features

✓ **Rate Limiting** - 2 req/sec with token bucket algorithm  
✓ **Circuit Breaker** - Auto-stops API calls after 5 failures  
✓ **Retry Logic** - Exponential backoff (1s, 2s, 4s, 8s, 16s)  
✓ **Smart Refresh** - Only update when data is stale  
✓ **Data Validation** - Comprehensive pre-flight checks  
✓ **Quality Scoring** - Freshness + completeness + validation  
✓ **Incremental Updates** - 80-90% faster than full refresh  
✓ **Backup & Recovery** - Daily automated backups  
✓ **Alerting** - Email & webhook notifications  
✓ **Complete Logging** - JSON structured logs with audit trail  

---

## 📈 Monitoring

### Get System Health
```python
from scheduler import pipeline_scheduler

status = pipeline_scheduler.get_status()
print(f"Scheduler running: {status['is_running']}")
print(f"Last refresh: {status['last_refresh']}")
print(f"Refresh stats: {status['stats']}")
```

### View Alerts
```python
from alerting_system import alertingSystem

alerts = alertingSystem.get_alert_history(limit=20)
for alert in alerts:
    print(f"{alert['severity']}: {alert['title']}")
```

### List Backups
```python
from backup_manager import backup_manager

backups = backup_manager.list_backups()
for backup in backups:
    print(f"{backup['filename']}: {backup['size_mb']:.1f} MB")
```

---

## 🧪 Testing

Run test suite:
```bash
python -m pytest test_pipeline.py -v
# Or
python test_pipeline.py
```

Test categories:
- Rate limiting
- Circuit breaker
- Refresh decisions
- Data validation
- Quality scoring
- Alerting
- Integration tests

---

## 🚨 Troubleshooting

### Problem: "Circuit breaker OPEN"
**Solution:** API is temporarily down. System will retry in 60 seconds.

### Problem: "Rate limit timeout"
**Solution:** Reduce RATE_LIMIT_RPS in config or wait for throttle to pass.

### Problem: "Validation report shows many errors"
**Solution:** Review data quality. May indicate API format change.

### Problem: "Database backup failed"
**Solution:** Check disk space and permissions on backup directory.

---

## 📞 Getting Help

1. **Architecture Details** → Read [LIVING_DATASET_ARCHITECTURE.md](LIVING_DATASET_ARCHITECTURE.md)
2. **Implementation Status** → Check [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
3. **Logs** → Check `logs/` directory for detailed error messages
4. **Code Comments** → Detailed docstrings in all modules

---

## 🔄 Typical Workflow

```
Day 1: Initial Setup
  ↓
  python migration.py
  (Migrate CSV → Database)
  
Day 2-6: Manual Validation
  ↓
  from rappid_fetcher import fetcher
  success, data, _ = fetcher.fetch_train_details("16320")
  (Validate a few trains manually)
  
Day 7: Start Automated Refresh
  ↓
  python scheduler.py
  (Runs weekly refresh cycle)
  (Monitors health daily)
  (Creates backups daily)
  
Ongoing: Monitor & Maintain
  ↓
  Check alerts
  Review logs
  Verify backups
  Analyze data quality
```

---

## 📋 Data Flow

```
RAPPID API
    ↓
[rate limiter] ← [circuit breaker]
    ↓
[rappid_fetcher] → Save raw JSON
    ↓
[refresh_policy] → Decide if refresh needed
    ↓
[incremental_updater] → Transform to structured
    ↓
[validator] → Validate data integrity
    ↓
[quality_scorer] → Score freshness + completeness
    ↓
[Database] → Update status & metrics
    ↓
[alerting_system] → Check thresholds
    ↓
[Users] ← Query only ACTIVE trains
```

---

## ✨ Key Differentiators

**This is NOT a traditional dataset import:**
- ❌ Not one-time CSV import
- ❌ Not static data file
- ❌ Not trust everything from API

**This IS a living system:**
- ✓ Continuously validates against live APIs
- ✓ Stores raw responses as immutable truth
- ✓ Smart caching based on data freshness
- ✓ Automatic error recovery
- ✓ Complete audit trail
- ✓ Health monitoring & alerts

---

## 🎯 Success Metrics

After 1 month of operation, you should see:
- ✓ 90%+ trains marked ACTIVE (validated)
- ✓ 85%+ data freshness (< 14 days old)
- ✓ <5% validation errors
- ✓ 94%+ cache hit rate
- ✓ Zero data loss (verified backups)
- ✓ Complete audit trail of all operations

---

## 📚 Documentation

- **[LIVING_DATASET_ARCHITECTURE.md](LIVING_DATASET_ARCHITECTURE.md)** - System architecture & design
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - What's been implemented
- **[config.py](config.py)** - Configuration reference
- **[database.py](database.py)** - Database schema
- **[Module docstrings](.) ** - Detailed API documentation

---

**Status: Production Ready** ✅  
**Last Updated:** January 25, 2026  
**Version:** 3.0 - Living Dataset System  

**Questions?** Review the architecture guide or check the logs for detailed information.
