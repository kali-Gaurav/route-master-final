# PostgreSQL Migration Quickstart

## Overview
This guide walks through migrating your Railway Operating System from SQLite (development) to PostgreSQL (production). The migration is safe, reversible, and includes verification steps.

---

## Prerequisites

1. **PostgreSQL Server Running**
   ```bash
   # Docker (easiest):
   docker run --name railway-postgres \
     -e POSTGRES_DB=railway_os \
     -e POSTGRES_USER=railway \
     -e POSTGRES_PASSWORD=secure_password \
     -p 5432:5432 \
     -d postgres:15-alpine
   
   # Or install PostgreSQL locally on Windows/Mac/Linux
   ```

2. **Python Packages Installed**
   ```bash
   pip install -r requirements.txt
   # Ensures psycopg2, sqlalchemy, etc. are available
   ```

3. **Environment Variables Set** (Optional but recommended)
   ```bash
   export DATABASE_URL="postgresql://railway:secure_password@localhost:5432/railway_os"
   # On Windows PowerShell:
   $env:DATABASE_URL="postgresql://railway:secure_password@localhost:5432/railway_os"
   ```

---

## Step 1: Dry-Run (Validate without Writing)

```bash
python rosctl.py migrate-db \
  --postgres-url "postgresql://railway:secure_password@localhost:5432/railway_os" \
  --dry-run \
  --backup
```

**Expected Output:**
```json
{
  "status": "success",
  "mode": "dry-run",
  "tables_migrated": 12,
  "rows_processed": 5042,
  "duration_sec": 2.34,
  "details": {
    "system_tenants": { "sqlite_rows": 5, "postgres_rows": 5, "verified": true },
    "system_api_keys": { "sqlite_rows": 8, "postgres_rows": 8, "verified": true },
    ...
  }
}
```

**What this does:**
- Connects to both SQLite and PostgreSQL
- Creates tables in PostgreSQL (as temp schema or with rollback)
- Copies all data from SQLite to PostgreSQL
- Verifies row counts match
- **Does NOT commit to PostgreSQL**
- Backs up SQLite to `backups/` folder

---

## Step 2: Verify Data Consistency

```bash
python rosctl.py verify-migration \
  --postgres-url "postgresql://railway:secure_password@localhost:5432/railway_os" \
  --sqlite-db railway_os.db
```

**Expected Output:**
```json
{
  "status": "verified",
  "total_tables": 12,
  "matching_tables": 12,
  "mismatches": [],
  "details": {
    "system_tenants": { "sqlite": 5, "postgres": 5, "match": true },
    "system_jobs": { "sqlite": 42, "postgres": 42, "match": true },
    ...
  }
}
```

---

## Step 3: Live Migration (Production Write)

Once dry-run and verification pass:

```bash
python rosctl.py migrate-db \
  --postgres-url "postgresql://railway:secure_password@localhost:5432/railway_os" \
  --backup
```

**What this does:**
- Backs up SQLite to `backups/railway_os_backup_<timestamp>.db`
- Creates all tables in PostgreSQL
- Copies ALL data from SQLite to PostgreSQL
- Verifies row counts
- Commits to PostgreSQL
- **SQLite remains untouched as fallback**

---

## Step 4: Switch API to PostgreSQL

Once migration is complete, point the API to PostgreSQL:

```bash
# Set environment variable
export DATABASE_URL="postgresql://railway:secure_password@localhost:5432/railway_os"
export DB_BACKEND="postgresql"

# Start API
python rosctl.py api-start --host 0.0.0.0 --port 8000
```

The API will now:
- Use PostgreSQL for all reads/writes
- Fall back to SQLite if PostgreSQL is unavailable
- Use connection pooling (20 connections, 40 overflow)

---

## Step 5: Monitor & Verify

```bash
# Check job logs to confirm API is using Postgres
python rosctl.py job-log <job_id>

# Check metrics to see request rate
curl http://localhost:8000/metrics

# Run a test route search
curl -X POST http://localhost:8000/routes \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "Delhi",
    "dest": "Mumbai",
    "date": "2024-12-25"
  }'
```

---

## Troubleshooting

### Issue: Connection refused
**Solution:** Ensure PostgreSQL is running:
```bash
docker ps | grep railway-postgres
# Or: psql -h localhost -U railway -d railway_os (test login)
```

### Issue: "psycopg2 not installed"
**Solution:** Install it:
```bash
pip install psycopg2-binary
```

### Issue: Row count mismatch
**Solution:** 
1. Check PostgreSQL for duplicate constraints: `SELECT COUNT(*) FROM table_name`
2. Rollback and retry with `--backup` flag
3. Check job logs for error details: `python rosctl.py job-log <job_id>`

### Issue: Need to rollback to SQLite
**Solution:**
```bash
# Set API back to SQLite
unset DATABASE_URL
unset DB_BACKEND
# Or explicitly:
export DB_BACKEND="sqlite"

# Restart API
python rosctl.py api-start
```

---

## Performance Notes

**After Migration:**
- PostgreSQL is **~3-5x faster** than SQLite for concurrent workloads
- Connection pooling handles 100+ simultaneous requests
- Redis caching (if enabled) further reduces latency
- Celery workers can run on separate machines

**Recommended Settings:**
```python
# db_pool.py defaults:
POOL_SIZE = 20          # Base connections
MAX_OVERFLOW = 40       # Additional connections under load
POOL_RECYCLE = 3600     # Recycle connections every hour
```

---

## Next Steps

1. **Set up Read Replicas** (optional, for scaling):
   - Create PostgreSQL read replicas
   - Point read-heavy queries to replicas
   - Update `db_pool.py` to use replica URLs

2. **Enable Celery Workers** (for async jobs):
   ```bash
   celery -A tasks worker --loglevel=info
   ```

3. **Set up Monitoring** (Prometheus/Grafana):
   - Scrape `/metrics` endpoint
   - Alert on error rate, latency, database pool exhaustion

4. **Backup Strategy**:
   ```bash
   # Daily backup of PostgreSQL
   pg_dump railway_os | gzip > backups/postgres_backup_$(date +%s).sql.gz
   ```

---

## Migration Rollback (If Needed)

To revert to SQLite:

```bash
# Stop API
# (Ctrl+C or kill process)

# Delete PostgreSQL data (optional)
# (Or just disconnect)

# Set API back to SQLite
export DB_BACKEND="sqlite"
export DATABASE_URL=""

# Restart API
python rosctl.py api-start
```

**SQLite data remains in `railway_os.db`—no data loss!**

---

## FAQ

**Q: Will there be downtime?**
A: Minimal. Dry-run first (zero writes), then live migration is typically <10 seconds for most datasets.

**Q: Can I keep both databases in sync?**
A: Not automatically, but you can run the migrator regularly for incremental syncs (deletes/updates may need custom logic).

**Q: What about multi-tenancy during migration?**
A: API keys and tenants are migrated as-is. Existing API keys remain valid after migration.

**Q: Can I migrate specific tables only?**
A: Currently, the migrator is all-or-nothing. For selective migration, edit `db_migrator.py` and adjust the `TABLES` list.

---

## Contact & Support

For issues or questions:
- Check `job-log` for detailed error messages
- Review PostgreSQL logs: `docker logs railway-postgres` (if using Docker)
- Inspect migration report JSON for data mismatches
