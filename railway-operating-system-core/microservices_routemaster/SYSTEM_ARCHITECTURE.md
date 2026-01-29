# Railway Operating System - System Architecture Constitution

**Document Version**: 1.0  
**Last Updated**: 2026-01-28  
**Status**: ACTIVE GOVERNANCE  
**Classification**: Internal - Architecture

---

## Executive Summary

This document defines the foundational architecture of the Railway Operating System as a production-grade platform. It establishes service boundaries, ownership contracts, failure modes, and scaling principles.

**This is the "constitution" that all 4 systems must follow.**

---

## 1. Platform Vision & Philosophy

### Design Principle
```
Build 4 independent, production-grade systems first.
Only integrate when each system achieves maturity.
Integration happens via strict contracts, never tight coupling.
```

### Architecture Layers
```
┌─────────────────────────────────────────────────┐
│         FRONTEND SYSTEM (Independent)           │
│    (Dashboard, BI, Charts, State Management)    │
└───────────────┬─────────────────────────────────┘
                │ (REST/GraphQL Contracts)
┌───────────────▼─────────────────────────────────┐
│       BACKEND SYSTEM (Independent)              │
│  (Microservices, APIs, Business Logic)          │
└───────────────┬─────────────────────────────────┘
                │ (SQL/Connection Contracts)
┌───────────────▼─────────────────────────────────┐
│       DATABASE SYSTEM (Independent)             │
│  (PostgreSQL, Schema, Migrations, Storage)      │
└─────────────────────────────────────────────────┘

PLUS: Deployment System (CI/CD, Infra, Secrets)
```

---

## 2. System Boundaries & Ownership

### 2.1 Database System
**Owner**: Database Team  
**Responsibility**: Data integrity, schema governance, migrations, backups  
**Independence**: Can be tested standalone with test fixtures

| Aspect | Rule |
|--------|------|
| Schema Changes | Alembic migrations only, never direct SQL |
| Multi-tenancy | Schema-per-tenant isolation, no cross-tenant queries |
| Migrations | Versioned, bidirectional (up/down) |
| Backups | Daily, automated, tested monthly |
| Retention | Hot (7d) → Warm (6mo) → Cold (archive) |
| Contracts | Owns 13 analytics tables, route tables, metrics |

**Database Owned Tables**:
```
Analytics System:
  ├── analytics_metrics (Owner: Analytics Service)
  ├── api_metrics (Owner: API Gateway)
  ├── route_search_metrics (Owner: Route Service)
  ├── user_engagement (Owner: Data Service)
  ├── alert_configurations (Owner: Analytics Service)
  └── ... (8 more)

Route System:
  ├── routes (Owner: Route Service)
  ├── route_segments (Owner: Route Service)
  └── stations (Owner: Route Service)

Core System:
  ├── tenants (Owner: Auth Service)
  ├── api_keys (Owner: Auth Service)
  └── audit_logs (Owner: Monitoring)
```

### 2.2 Backend System
**Owner**: Backend/Platform Team  
**Responsibility**: API contracts, business logic, service orchestration  
**Independence**: Can run against test database, no frontend dependency

| Service | Port | Owner | Read Tables | Write Tables |
|---------|------|-------|-------------|--------------|
| API Gateway | 8000 | Gateway Team | all | api_metrics, audit_logs |
| Auth Service | 8001 | Auth Team | tenants, api_keys | tenants, api_keys, audit_logs |
| Route Service | 8002 | Route Team | routes, stations | route_search_metrics |
| Data Service | 8003 | Data Team | all | user_engagement, business_metrics |
| Analytics Service | 8084 | Analytics Team | all (read-only) | analytics_* |
| Worker Service | 8004 | Async Team | all | all (background) |

**Backend Non-Negotiables**:
- All services must implement `/health` endpoint
- All services must expose Prometheus metrics
- All services must implement circuit breakers
- All services must have request timeouts
- All services must log correlation IDs

### 2.3 Frontend System
**Owner**: Frontend/Product Team  
**Responsibility**: UI/UX, state management, client-side logic  
**Independence**: Can run against mock API server

**Frontend Contracts**:
- Must communicate only via published REST/GraphQL APIs
- Must use API versioning (v1, v2, etc.)
- Must handle all HTTP error codes gracefully
- Must implement optimistic updates + rollback
- Must support offline-first architecture (where applicable)

### 2.4 Deployment System
**Owner**: DevOps/SRE Team  
**Responsibility**: Infrastructure, CI/CD, secrets, monitoring  
**Independence**: Infrastructure-as-Code, reproducible in any environment

---

## 3. API Contracts & Versioning

### 3.1 API Versioning Strategy

**Rule**: Never break a published API version

```
URL Pattern: /v{major}/resource

Example:
  GET /v1/analytics/query       → Stable, no breaking changes
  GET /v2/analytics/query       → New features, backward compatible v1
  DELETE /v1/analytics/query    → Only via deprecation policy
```

### 3.2 Deprecation Policy

| Phase | Timeline | Action |
|-------|----------|--------|
| Active | Indefinite | Full support |
| Deprecation Notice | Day 1 | Announce in docs, add deprecation header |
| Deprecation Warning | 90 days | 410 Gone or 308 Permanent Redirect |
| Sunset | 180 days | Remove endpoint entirely |

**Header Example**:
```http
Deprecation: true
Sunset: Wed, 31 Jul 2026 23:59:59 GMT
Link: </v2/analytics/query>; rel="successor-version"
```

### 3.3 Response Contract

**All endpoints must follow this contract**:

```json
{
  "status": "success|error|partial",
  "data": {},
  "errors": [],
  "metadata": {
    "version": "1.0",
    "timestamp": "2026-01-28T10:00:00Z",
    "correlation_id": "uuid",
    "request_id": "uuid"
  },
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 1000,
    "has_more": true
  }
}
```

**Error Response Contract**:

```json
{
  "status": "error",
  "errors": [
    {
      "code": "INVALID_TENANT_ID",
      "message": "Tenant ID is required",
      "field": "tenant_id",
      "status_code": 400
    }
  ],
  "metadata": {
    "timestamp": "2026-01-28T10:00:00Z",
    "correlation_id": "uuid"
  }
}
```

---

## 4. Data Ownership & Flow

### 4.1 Data Ownership Matrix

| Entity | Owner | Write | Read | Governance |
|--------|-------|-------|------|-----------|
| Tenants | Auth Service | Auth Team | All Services | Immutable once created |
| Routes | Route Service | Route Team | All Services | Versioned by route_version_id |
| Metrics | Analytics Service | Analytics Service | Analytics, Gateway | Immutable, append-only |
| API Metrics | API Gateway | Gateway Team | Analytics, Monitoring | TTL-based retention |
| User Data | Data Service | Data Team | Analytics (filtered) | GDPR compliant |

### 4.2 Data Flow Contracts

**Principle**: Data flows ONE direction unless explicit bidirectional agreement

```
Client Request
    ↓
API Gateway (logs to api_metrics)
    ↓
Service (logs to service_metrics)
    ↓
Database (stores in tenant schema)
    ↓
Response back to Client
    ↓
Analytics Service (reads metrics for dashboards)
    ↓
User sees insights
```

**Why unidirectional?**
- Prevents circular dependencies
- Makes failure modes obvious
- Enables independent testing

### 4.3 Data Lifecycle

**Each table has a lifecycle policy**:

```
HOT (Recent)
├── Duration: 0-7 days
├── Storage: PostgreSQL (SSD)
├── Access: Real-time queries OK
└── Backup: Continuous replication

WARM (Historical)
├── Duration: 7 days - 6 months
├── Storage: TimescaleDB or ClickHouse
├── Access: Batch queries OK
└── Backup: Weekly snapshots

COLD (Archive)
├── Duration: 6+ months
├── Storage: S3 (Parquet files)
├── Access: Retrieval job needed (24hr latency OK)
└── Backup: Versioned S3 buckets
```

---

## 5. Service Communication Contracts

### 5.1 Synchronous (Request/Response)

**When**: API Gateway → Service → Database

**Contract**:
```python
# Service MUST respond within timeout
TIMEOUT = 30_seconds

# Service MUST implement retry logic
MAX_RETRIES = 3
BACKOFF = exponential(1s, max=10s)

# Service MUST have circuit breaker
FAILURE_THRESHOLD = 5
RECOVERY_TIMEOUT = 60_seconds
```

### 5.2 Asynchronous (Event/Message Queue)

**When**: Long-running operations (reports, exports, ETL)

**Contract**:
```python
# Use RabbitMQ for queuing
QUEUE_NAME = f"{service_name}.{event_type}"

# Message structure MUST include:
{
  "event_id": "uuid",
  "event_type": "report.generated",
  "tenant_id": "uuid",
  "timestamp": "2026-01-28T10:00:00Z",
  "correlation_id": "uuid",
  "payload": {}
}

# Dead Letter Queue for failures
DLQ_RETENTION = 30_days
```

### 5.3 Database Connection Contract

**When**: Service → PostgreSQL

**Contract**:
```python
# Connection pooling
POOL_SIZE = 10
MAX_OVERFLOW = 5
POOL_TIMEOUT = 10_seconds

# Query timeout
QUERY_TIMEOUT = 60_seconds

# Transaction isolation
ISOLATION_LEVEL = READ_COMMITTED

# Schema access
USE_TENANT_SCHEMA = f"tenant_{tenant_id.hex}"
```

---

## 6. Failure Modes & Recovery

### 6.1 System Failure Matrix

| Failure | Service Impact | User Impact | Recovery |
|---------|----------------|-------------|----------|
| Database Down | All services fail | Cannot query/update | Auto-failover to replica |
| Redis Down | Cache misses increase | Slower response (100ms→1s) | Query DB directly |
| Service Down | API returns 503 | User sees error | Auto-restart, gradual recovery |
| Network Partition | Timeout errors | Cannot reach service | Circuit breaker opens |
| ETL Failure | Metrics delayed | Dashboards stale (up to 24h) | Manual retry, alert sent |
| Secrets Missing | Service won't start | System down | Manual ops intervention |

### 6.2 Recovery Strategies

**For Database Failure**:
```
1. Detect: Health check fails 2x
2. Failover: Promote read replica (automatic)
3. Alert: PagerDuty alert to DBA
4. Recovery: Restore from backup if needed
5. Validation: Run data integrity checks
```

**For Service Failure**:
```
1. Detect: Liveness probe fails 3x
2. Restart: Kubernetes auto-restart
3. Alert: Alert monitoring dashboard
4. Escalation: If restarting 5+ times, page on-call
5. Investigation: Pull logs and traces
```

**For Circuit Breaker (Cascading Failure)**:
```
1. Detect: Service not responding
2. Open: Stop sending requests
3. Wait: Half-open after 60 seconds
4. Test: Send probe request
5. Close: Resume normal traffic if probe succeeds
```

---

## 7. Scaling Rules

### 7.1 Horizontal Scaling

**Rule**: Each service can scale independently

```yaml
analytics-service:
  min_replicas: 2
  max_replicas: 10
  scale_on_cpu: 70%
  scale_on_memory: 80%
  scale_on_requests: 1000/sec per replica

route-service:
  min_replicas: 3
  max_replicas: 20
  scale_on_p99_latency: 500ms
  scale_on_requests: 5000/sec per replica
```

### 7.2 Database Scaling

**Rule**: Scale database BEFORE application

```
PostgreSQL Scaling:
├── Phase 1 (Small): Single instance + read replicas
├── Phase 2 (Medium): Master-slave replication + partitioning
├── Phase 3 (Large): Sharding by tenant_id
└── Phase 4 (Enterprise): Distributed database (CockroachDB)
```

### 7.3 Cache Scaling

**Rule**: Redis cache scales horizontally

```
Redis Cluster:
├── 6 nodes minimum (3 master, 3 replica)
├── 16GB per node
├── Keyspace notification events
└── Pub/Sub for invalidation
```

---

## 8. Tenancy Model

### 8.1 Schema-Per-Tenant Isolation

**Architecture**:
```sql
PostgreSQL Database: railway_os
├── public schema (shared)
│   ├── tenants (multi-tenant registry)
│   ├── api_keys (credentials)
│   └── audit_logs (all activity)
│
├── tenant_550e8400e29b41d4a716446655440000 (Tenant A)
│   ├── routes
│   ├── stations
│   ├── analytics_metrics
│   └── user_engagement
│
├── tenant_550e8400e29b41d4a716446655440001 (Tenant B)
│   └── (isolated copy of all tables)
│
└── tenant_xxxxxxxx... (More tenants)
```

**Contract**:
- Every query MUST include `tenant_id`
- Never allow cross-tenant queries
- Backups are per-tenant
- Each tenant can have custom retention policy

### 8.2 Tenant Isolation Verification

```python
# REQUIRED: All queries must verify tenant access
@require_tenant_access
async def get_metrics(tenant_id: UUID):
    """Raises error if tenant_id not in request"""
    pass

# Forbidden patterns:
SELECT * FROM analytics_metrics  # ❌ No tenant filter
SELECT * FROM public.tenants WHERE id != current_tenant  # ❌ Data leak
```

---

## 9. Observability Contracts

### 9.1 Logging Contract

**Every service must log**:

```json
{
  "timestamp": "2026-01-28T10:00:00Z",
  "level": "INFO|WARN|ERROR|DEBUG",
  "service": "analytics-service",
  "correlation_id": "uuid",
  "request_id": "uuid",
  "tenant_id": "uuid",
  "user_id": "uuid",
  "message": "User event description",
  "duration_ms": 125,
  "error": null
}
```

### 9.2 Metrics Contract

**Every service must expose**:

```python
# Prometheus metrics
service_requests_total{service, endpoint, status}
service_request_duration_seconds{service, endpoint}
service_cache_hits_total{service, cache_type}
service_cache_misses_total{service, cache_type}
service_database_connections{service, status}
service_circuit_breaker_state{service, dependency}
```

### 9.3 Tracing Contract

**Every request must have**:

```
Correlation ID (UUID): Unique per user workflow
Request ID (UUID): Unique per API request
Trace ID (UUID): Distributed tracing ID
Parent Span ID: For nested calls
```

**Example**:
```
User creates search
  ↓ Correlation ID: abc-123-def
  API Gateway receives request
    ↓ Request ID: xyz-789
    Route Service processes
      ↓ Trace ID: parent-span-1
      Data Service called
        ↓ Trace ID: parent-span-2 (parent: parent-span-1)
        Database query
          ↓ Trace ID: parent-span-3 (parent: parent-span-2)
```

---

## 10. Security & Access Control

### 10.1 Authentication Contract

**Every service must verify**:

```python
# 1. API Key exists and is valid
api_key = extract_from_auth_header()
tenant_id = validate_api_key(api_key)

# 2. Request includes tenant_id
if not request.tenant_id:
    raise UnauthorizedException()

# 3. Tenant matches API key
if request.tenant_id != api_key.tenant_id:
    raise ForbiddenException()
```

### 10.2 Authorization Contract

**Every endpoint has roles**:

```python
@require_role("admin", "analyst")
@require_tenant_access
async def get_sensitive_metrics(tenant_id: UUID):
    """Only admin or analyst can access"""
    pass

# Roles:
ROLES = {
    "admin": ["read", "write", "delete", "manage_users"],
    "analyst": ["read", "export"],
    "viewer": ["read"],
    "system": ["all"],
}
```

### 10.3 Data Access Contract

**Principle**: Row-level security (RLS) in database

```sql
-- Every table should have RLS policy
ALTER TABLE analytics_metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON analytics_metrics
  USING (tenant_id = current_setting('app.tenant_id')::uuid);

-- Every query sets tenant context
SET app.tenant_id = '550e8400-e29b-41d4-a716-446655440000';
```

---

## 11. Governance Checklist

### Before Deploying Any Service

- [ ] Service has `/health` endpoint
- [ ] Service implements circuit breakers
- [ ] Service logs correlation IDs
- [ ] Service exposes Prometheus metrics
- [ ] Service has request timeouts
- [ ] Service validates tenant_id on all queries
- [ ] Service has database connection pooling
- [ ] Service implements retry logic
- [ ] Service has API versioning plan
- [ ] Service documents all error codes

### Before Data Goes to Production

- [ ] Schema has been versioned with Alembic
- [ ] Migrations are bidirectional (up/down)
- [ ] Data ownership matrix updated
- [ ] Backup strategy documented
- [ ] Retention policy defined
- [ ] Disaster recovery tested
- [ ] Data contracts reviewed by Database Team

### Before Deploying to Production

- [ ] All 4 systems mature and tested independently
- [ ] Integration tests pass
- [ ] Load tests show acceptable performance
- [ ] Chaos tests pass (failure scenarios)
- [ ] Monitoring and alerting configured
- [ ] Runbooks written for on-call team
- [ ] Rollback plan tested
- [ ] Team trained on operations

---

## 12. Evolution & Future States

### Current State (Now)
```
4 Independent Systems Being Built
├── Database System (schema, migrations)
├── Backend System (microservices)
├── Frontend System (UI, dashboards)
└── Deployment System (CI/CD, infra)
```

### Intermediate State (Q2 2026)
```
Services Integrated
├── Backend ↔ Database (working)
├── Frontend ↔ Backend (working)
└── Deployment (partial - staging)
```

### Mature State (Q4 2026)
```
Full Production Platform
├── All 4 systems working
├── Self-healing infrastructure
├── Automated scaling
├── Multi-region support
└── Sub-100ms p99 latency
```

---

## 13. Document References

This constitution links to:

| Document | Purpose |
|----------|---------|
| API_GOVERNANCE.md | API versioning, deprecation policies |
| DATA_OWNERSHIP_MATRIX.md | Table ownership, write/read rights |
| BACKEND_RESILIENCE.md | Circuit breakers, retry logic |
| DEPLOYMENT_ARCHITECTURE.md | Environments, blue-green deploy |
| SYSTEM_TESTING_STRATEGY.md | Contract, load, chaos tests |
| OBSERVABILITY_STACK.md | Tracing, metrics, logs |
| RBAC_AUTHZ.md | Roles, permissions, scopes |
| SECRETS_MANAGEMENT.md | Vault, rotation, per-env |
| CI_CD_PIPELINE.md | Build, test, deploy gates |

---

## 14. Review & Amendment

**This document is reviewed**:
- Quarterly by Architecture Team
- After each major incident
- When adding new service
- When scaling beyond current limits

**To amend**: Requires agreement from:
- Database Team Lead
- Backend Team Lead
- DevOps Lead
- Product Lead

---

**Constitution Established**: 2026-01-28  
**Next Review**: 2026-04-28  
**Owner**: Platform Architecture Team