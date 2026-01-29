# Phase 1 PostgreSQL Deployment Checklist

## 🎯 Objective
Transition Railway Operating System from SQLite (development) to PostgreSQL (production) with zero downtime, connection pooling, async workers, and comprehensive monitoring.

---

## ✅ Pre-Migration Checklist

### Infrastructure Setup
- [ ] PostgreSQL server running (Docker or native)
  - [ ] Connection tested: `psql -h localhost -U railway -d railway_os`
  - [ ] Database exists: `railway_os`
  - [ ] User permissions verified: can create tables, insert/update/delete data

- [ ] Redis server running (for Celery + caching)
  - [ ] Connection tested: `redis-cli ping` returns `PONG`
  - [ ] Memory available: at least 512MB free

- [ ] Python environment ready
  - [ ] Python 3.8+ installed: `python --version`
  - [ ] Virtual environment activated
  - [ ] Dependencies installed: `pip install -r requirements.txt`
  - [ ] psycopg2-binary available: `python -c "import psycopg2"`
  - [ ] Celery available: `python -c "import celery"`

### Data Preparation
- [ ] SQLite database backed up
  - [ ] Backup command: `python rosctl.py backup-db --compress`
  - [ ] Backup verified: file exists in `backups/` folder
  - [ ] Size recorded for reference

- [ ] Data quality checked
  - [ ] No orphaned records (foreign key consistency)
  - [ ] No duplicate API keys or tenants
  - [ ] All job records have valid status

### Documentation & Comms
- [ ] MIGRATION_QUICKSTART.md reviewed by ops team
- [ ] Rollback plan documented and tested
- [ ] Downtime window communicated (if any)
- [ ] Alert rules configured for monitoring

---

## 🔄 Migration Execution

### Phase 1.1: Dry-Run (Validation Only)
- [ ] Run dry-run migration:
  ```bash
  python rosctl.py migrate-db \
    --postgres-url "postgresql://railway:password@localhost:5432/railway_os" \
    --dry-run \
    --backup
  ```
  
- [ ] Review output JSON:
  - [ ] `status == "success"`
  - [ ] `tables_migrated` == expected count (12)
  - [ ] All table verifications pass

- [ ] No PostgreSQL writes made (verify: `SELECT COUNT(*) FROM system_tenants` returns 0)

- [ ] SQLite remains unchanged (verify: `sqlite3 railway_os.db "SELECT COUNT(*) FROM system_tenants"`)

### Phase 1.2: Verification (Data Consistency Check)
- [ ] Run verification:
  ```bash
  python rosctl.py verify-migration \
    --postgres-url "postgresql://railway:password@localhost:5432/railway_os"
  ```

- [ ] Review output:
  - [ ] `status == "verified"`
  - [ ] `total_tables == matching_tables`
  - [ ] No mismatches reported
  - [ ] Row counts match across all tables

### Phase 1.3: Live Migration (Production Write)
- [ ] Set maintenance mode (if applicable)
  - [ ] Stop accepting new requests (or queue them)
  - [ ] Wait for in-flight requests to complete

- [ ] Run live migration:
  ```bash
  python rosctl.py migrate-db \
    --postgres-url "postgresql://railway:password@localhost:5432/railway_os" \
    --backup
  ```

- [ ] Monitor migration process:
  - [ ] Check database logs for errors
  - [ ] Monitor disk space usage
  - [ ] Note migration duration

- [ ] Verify success:
  - [ ] Job log shows `status == "success"`
  - [ ] PostgreSQL contains all expected data
  - [ ] SQLite backup created in `backups/` folder

### Phase 1.4: API Switchover
- [ ] Set environment variables:
  ```bash
  export DATABASE_URL="postgresql://railway:password@localhost:5432/railway_os"
  export DB_BACKEND="postgresql"
  export REDIS_URL="redis://localhost:6379/0"
  ```

- [ ] Restart API service:
  ```bash
  python rosctl.py api-start --host 0.0.0.0 --port 8000
  ```

- [ ] Monitor for errors in logs (first 5 minutes)
  - [ ] No "connection refused" errors
  - [ ] No "table not found" errors
  - [ ] API responding to requests

### Phase 1.5: Functional Testing
- [ ] Test core functionality:
  - [ ] Route search works: `curl -X POST http://localhost:8000/routes ...`
  - [ ] API key auth works: all endpoints require valid key
  - [ ] Rate limiting enforced: >100 RPS blocked appropriately

- [ ] Test multi-tenancy:
  - [ ] Multiple tenants can issue their own API keys
  - [ ] Tenant A cannot see Tenant B's data
  - [ ] Audit logs capture all operations

- [ ] Test job system:
  - [ ] Jobs enqueue correctly: `python rosctl.py generate-routes ... --background`
  - [ ] Job logs available: `python rosctl.py job-log <job_id>`
  - [ ] Worker processes jobs: `python rosctl.py worker`

- [ ] Test caching (if Redis enabled):
  - [ ] First route search is slower (~200ms)
  - [ ] Second identical search is faster (~50ms)
  - [ ] Cache clears on data updates

---

## ⚙️ Post-Migration Configuration

### Connection Pooling
- [ ] Verify pool settings in `db_pool.py`:
  - [ ] `POOL_SIZE = 20` (base connections)
  - [ ] `MAX_OVERFLOW = 40` (surge capacity)
  - [ ] `POOL_RECYCLE = 3600` (recycle interval)

- [ ] Monitor pool exhaustion:
  - [ ] Check metrics: `/metrics` endpoint
  - [ ] Alert if `db_connections_active > 50`
  - [ ] Alert if `db_pool_overflow > 30`

### Celery Workers
- [ ] Start Celery worker:
  ```bash
  celery -A tasks worker --loglevel=info
  ```

- [ ] Configure for auto-restart:
  - [ ] systemd service (Linux)
  - [ ] supervisord config (multi-process)
  - [ ] Docker container (recommended)

- [ ] Monitor worker:
  - [ ] `celery -A tasks inspect stats` shows active workers
  - [ ] `celery -A tasks inspect active` shows running tasks

### Redis Caching
- [ ] Enable in `cache.py`:
  ```python
  # Ensure REDIS_URL environment variable is set
  REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
  ```

- [ ] Monitor cache:
  - [ ] `redis-cli INFO stats` shows cache hits/misses
  - [ ] `redis-cli DBSIZE` shows number of keys

- [ ] Configure cache eviction policy (if needed):
  ```bash
  redis-cli CONFIG SET maxmemory-policy allkeys-lru
  ```

---

## 📊 Monitoring & Observability

### Prometheus Metrics
- [ ] Metrics endpoint configured: `/metrics`
- [ ] Scrape frequency: every 30 seconds
- [ ] Key metrics to monitor:
  - [ ] `http_requests_total` (request count)
  - [ ] `http_request_duration_seconds` (latency)
  - [ ] `http_errors_total` (error rate)
  - [ ] `db_pool_active` (active connections)
  - [ ] `cache_hits_total` / `cache_misses_total` (hit rate)

### Logging
- [ ] Structured logging enabled in `database.py`
- [ ] Log levels:
  - [ ] DEBUG: connection pool events
  - [ ] INFO: migration steps, worker tasks
  - [ ] WARNING: slow queries, pool exhaustion
  - [ ] ERROR: connection failures, migration errors

- [ ] Log aggregation configured (optional):
  - [ ] ELK stack, Splunk, or CloudWatch
  - [ ] Search logs by: `tenant_id`, `api_key`, `job_id`

### Alerting
- [ ] Alert rules configured:
  - [ ] PostgreSQL down: immediate page
  - [ ] Connection pool >80% used: warning
  - [ ] Query latency >500ms: investigate
  - [ ] Error rate >1%: warning
  - [ ] Redis down: fallback to in-memory cache (graceful degradation)

---

## 🔄 Rollback Plan

### If Migration Fails
1. Stop API: `kill <api_process_id>`
2. Set env vars back to SQLite:
   ```bash
   unset DATABASE_URL
   export DB_BACKEND="sqlite"
   ```
3. Restart API: `python rosctl.py api-start`
4. Investigate issue in PostgreSQL
5. Retry migration after fix

### If Postgres Goes Down
1. No action needed! API automatically falls back to SQLite
2. Users experience slight performance degradation but no data loss
3. Monitor `db_fallback_count` metric
4. Restart PostgreSQL service
5. API resumes using Postgres once available

---

## 📋 Post-Migration Verification

### Day 1 (Immediate)
- [ ] All tenants can access their data
- [ ] API keys still valid
- [ ] No increase in error rates
- [ ] No missing audit logs

### Day 3 (Stability Check)
- [ ] No latency degradation
- [ ] No connection pool exhaustion
- [ ] Scheduled backups running successfully
- [ ] Metrics being scraped correctly

### Week 1 (Performance Baseline)
- [ ] Compare latency: PostgreSQL vs SQLite backup
- [ ] Document throughput improvement
- [ ] Identify slow queries (>100ms)
- [ ] Tune indexes if needed

### Month 1 (Production Hardening)
- [ ] Enable read replicas (if scaling needed)
- [ ] Configure automated backups (daily/weekly)
- [ ] Test disaster recovery procedures
- [ ] Document lessons learned

---

## 🚀 Next Phase: Docker & Scaling

### Docker Deployment
- [ ] Build images:
  ```bash
  docker build -t railway-api:v1 -f Dockerfile.api .
  docker build -t railway-celery:v1 -f Dockerfile.celery .
  ```

- [ ] Run full stack:
  ```bash
  docker-compose -f docker-compose.prod.yml up -d
  ```

- [ ] Verify services:
  ```bash
  docker-compose ps
  docker logs railway-api
  ```

### Horizontal Scaling
- [ ] Add additional Celery workers (as Docker services)
- [ ] Set up load balancer for API (nginx/HAProxy)
- [ ] Configure PostgreSQL read replicas for analytics queries
- [ ] Monitor resource usage; scale as needed

### Vendor Integration
- [ ] Create vendor onboarding guide
- [ ] Provide API documentation (OpenAPI/Swagger)
- [ ] Set rate limits per tenant
- [ ] Configure SLA monitoring

---

## ✅ Sign-Off

- [ ] Checklist completed by: `___________________` (Name)
- [ ] Date: `___________________`
- [ ] Approved by: `___________________` (Manager/Lead)
- [ ] Notes/Issues:
  ```
  
  
  
  ```

---

## 📚 Reference Documents

- [MIGRATION_QUICKSTART.md](MIGRATION_QUICKSTART.md) - Step-by-step migration guide
- [MIGRATIONS_SETUP.md](MIGRATIONS_SETUP.md) - Alembic schema management
- [db_migrator.py](db_migrator.py) - Migration implementation
- [db_pool.py](db_pool.py) - Connection pooling configuration
- [tasks.py](tasks.py) - Celery task definitions
- [cache.py](cache.py) - Redis caching layer

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| PostgreSQL connection refused | Check service is running; verify credentials |
| Row count mismatch | Run dry-run first; check for constraint violations |
| API slow after migration | Check pool size; monitor slow queries; add indexes |
| Cache not working | Verify Redis is running; check REDIS_URL env var |
| Celery tasks not running | Start worker: `celery -A tasks worker --loglevel=info` |
| Disk space full | Check PostgreSQL data directory; run `VACUUM` if needed |

