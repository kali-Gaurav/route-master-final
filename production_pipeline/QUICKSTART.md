# Production Pipeline - Quick Start Guide

## 5-Minute Setup

### Prerequisites
- Python 3.9+
- pip or conda
- SQLite (included) or PostgreSQL

### Local Setup

```bash
# 1. Navigate to project
cd route-master-final

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r production_pipeline/requirements.txt

# 4. Configure environment (optional, defaults to LOCAL/SQLite)
export ENVIRONMENT=LOCAL
# or Windows: set ENVIRONMENT=LOCAL

# 5. Run the application
python -m production_pipeline.main

# 6. Test the API in another terminal
curl http://localhost:8000/api/v1/health
```

You should see:
```json
{
  "status": "healthy",
  "database": "healthy",
  "cache": "healthy",
  "timestamp": "2024-02-14T..."
}
```

---

## API Quick Reference

### Search Routes (Main Feature)
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "NDLS",
    "destination": "KOTA",
    "max_results": 10
  }'
```

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### System Metrics
```bash
curl http://localhost:8000/api/v1/metrics
```

### List All Stations
```bash
curl http://localhost:8000/api/v1/stations
```

### Search Trains
```bash
curl http://localhost:8000/api/v1/trains
```

---

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=sqlite:///./data/railway.db     # SQLite (default)
DATABASE_URL=postgresql://user:pass@host/db  # PostgreSQL

# Application
ENVIRONMENT=LOCAL      # LOCAL, STAGING, PRODUCTION
HOST=0.0.0.0
PORT=8000

# Ingestion
RATE_LIMIT_RPS=10
CACHE_TTL_SECONDS=3600
MAX_RETRIES=3

# Logging
LOGGING_LEVEL=INFO
LOGS_DIR=./logs

# Caching
CACHE_DIR=./data/cache
```

### Configuration File

All config in `production_pipeline/config.py`:

```python
from production_pipeline.config import get_config

config = get_config()

# Access settings
print(config.database.connection_string)
print(config.ingestion.rate_limit_rps)
print(config.api.port)
```

---

## Database Setup

### Initialize Database

```python
from production_pipeline.database import DatabaseManager

db = DatabaseManager("sqlite:///./data/railway.db")
db.create_all_tables()  # Creates all tables
print("Database initialized!")
```

### Load Sample Data

```python
from sqlalchemy.orm import Session
from production_pipeline.database import DatabaseManager, Train, Station, TrainStation

db = DatabaseManager("sqlite:///./data/railway.db")
session = db.get_session()

# Add a station
station = Station(code="NDLS", name="New Delhi", city="Delhi")
session.add(station)

# Add a train
train = Train(
    train_no="12345",
    train_name="Express Train",
    source_station_code="NDLS",
    destination_station_code="KOTA",
    days_running="SMTWTFS",  # All days
    journey_duration_minutes=420
)
session.add(train)

session.commit()
print("Sample data added!")
```

---

## Production Deployment

### Using Docker

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

ENV ENVIRONMENT=PRODUCTION
ENV DATABASE_URL=postgresql://postgres:password@db/railway

CMD ["python", "-m", "production_pipeline.main"]
```

**Build and Run**:
```bash
docker build -t railway-api .
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  -e ENVIRONMENT=PRODUCTION \
  railway-api
```

### Using Gunicorn (Production Server)

```bash
# Install
pip install gunicorn

# Run with 4 workers
gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  production_pipeline.main:app
```

### Using Systemd (Linux)

**Create /etc/systemd/system/railway-api.service**:
```ini
[Unit]
Description=Railway Route Master API
After=network.target

[Service]
Type=notify
User=railway
WorkingDirectory=/opt/railway
Environment="PATH=/opt/railway/venv/bin"
Environment="DATABASE_URL=postgresql://user:pass@localhost/railway_db"
ExecStart=/opt/railway/venv/bin/gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8000 \
  production_pipeline.main:app

Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start**:
```bash
sudo systemctl enable railway-api
sudo systemctl start railway-api
sudo systemctl status railway-api
```

---

## Monitoring

### Log Files

All logs are stored in JSON format in `logs/` directory:

```bash
# View recent logs
tail -100 logs/application.log | jq '.'

# Filter by error
grep '"level":"ERROR"' logs/errors.log | jq '.'

# Get performance metrics
grep 'http_request_duration' logs/application.log | jq '.metric_value'
```

### Metrics Endpoint

```bash
# Get all metrics
curl http://localhost:8000/api/v1/metrics | jq '.'
```

Response:
```json
{
  "searches_total": 145,
  "searches_success": 142,
  "searches_failed": 3,
  "avg_search_time_ms": 156.4,
  "routes_generated_total": 725,
  "errors_total": 2,
  "uptime_seconds": 3600.0
}
```

### Database Inspection

```python
from production_pipeline.database import DatabaseManager, SearchLog
from sqlalchemy import func

db = DatabaseManager("sqlite:///./data/railway.db")
session = db.get_session()

# Total searches
total = session.query(SearchLog).count()
print(f"Total searches: {total}")

# Success rate
successful = session.query(SearchLog).filter_by(success=True).count()
print(f"Success rate: {successful/total*100:.1f}%")

# Average latency
from sqlalchemy import func
avg_latency = session.query(func.avg(SearchLog.search_duration_ms)).scalar()
print(f"Average search latency: {avg_latency:.0f}ms")
```

---

## Troubleshooting

### API Won't Start

**Error: "Address already in use"**
- Another service on port 8000
- `lsof -i :8000` (Linux/Mac) to find process
- `netstat -ano | findstr :8000` (Windows)
- Kill process or change PORT env var

**Error: "No module named 'production_pipeline'"**
- Wrong working directory
- `cd route-master-final` first
- Or adjust PYTHONPATH

### Database Errors

**Error: "database is locked" (SQLite)**
- Close other connections to database
- Delete `data/railway.db-journal` if exists
- Switch to PostgreSQL for production

**Error: "Connection refused" (PostgreSQL)**
- Verify PostgreSQL is running
- Check DATABASE_URL is correct
- `psql postgresql://user:pass@host/db` to test

### Slow Performance

```bash
# Check metrics
curl http://localhost:8000/api/v1/metrics | jq '.avg_search_time_ms'

# Check logs for slow queries
grep 'Slow' logs/application.log

# Check database size
SELECT pg_size_pretty(pg_database_size('railway_db'));

# Rebuild indexes
REINDEX DATABASE railway_db;
```

### High Memory Usage

```python
# Check cache size
from production_pipeline.ingestion import CacheManager
cache = CacheManager("./data/cache")
print(f"Cache entries: {len(cache.memory_cache)}")

# Clear old cache
cache.clear_expired()
```

---

## Common Tasks

### Add New Train
```python
from production_pipeline.database import DatabaseManager, Train
from datetime import datetime

db = DatabaseManager("sqlite:///./data/railway.db")
session = db.get_session()

train = Train(
    train_no="12345",
    train_name="Shatabdi Express",
    source_station_code="NDLS",
    destination_station_code="KOTA",
    days_running="SMTWTFS",
    journey_duration_minutes=420,
    last_verified_at=datetime.utcnow()
)
session.add(train)
session.commit()
print(f"Added: {train}")
```

### List All Routes
```python
from production_pipeline.database import DatabaseManager, Train

db = DatabaseManager("sqlite:///./data/railway.db")
session = db.get_session()

trains = session.query(Train).limit(10).all()
for train in trains:
    print(f"{train.train_no}: {train.source_station_code} -> {train.destination_station_code}")
```

### Check Search Statistics
```python
from production_pipeline.database import DatabaseManager, SearchLog
from sqlalchemy import func, desc
from datetime import datetime, timedelta

db = DatabaseManager("sqlite:///./data/railway.db")
session = db.get_session()

# Top search routes
top_searches = session.query(
    SearchLog.origin,
    SearchLog.destination,
    func.count(SearchLog.id).label('count')
).group_by(SearchLog.origin, SearchLog.destination).order_by(desc('count')).limit(10).all()

for origin, destination, count in top_searches:
    print(f"{origin} -> {destination}: {count} searches")
```

---

## Performance Tips

1. **Use PostgreSQL in Production**
   - SQLite is slower for concurrent requests
   - PostgreSQL supports connection pooling better

2. **Enable Query Caching**
   - Caches route search results for 3600s
   - Reduces duplicate API calls

3. **Batch Data Loading**
   - Load 100 records at a time
   - Reduces memory footprint

4. **Monitor Metrics Regularly**
   - Check `/api/v1/metrics` endpoint
   - Look for slow searches (>5s)
   - Monitor error rate

5. **Optimize Database**
   - Indexes already defined on key columns
   - Rebuild indexes periodically
   - Archive old logs

---

## Support

For issues or questions:

1. Check logs: `tail -f logs/application.log | jq '.'`
2. Review metrics: `curl http://localhost:8000/api/v1/metrics`
3. Test database: `python -c "from production_pipeline.database import *; print('DB OK')"`
4. Review ARCHITECTURE.md for detailed documentation

---

## Next: Production Checklist

- [ ] Switch to PostgreSQL
- [ ] Configure automated backups
- [ ] Set up monitoring (Prometheus)
- [ ] Configure log aggregation (ELK)
- [ ] Load real train/station data
- [ ] Performance test under load
- [ ] Set up automated deployments
- [ ] Configure SSL/TLS
- [ ] Set up rate limiting for clients
- [ ] Document API for users
