# Data Ownership & Contracts Matrix

**Version**: 1.0  
**Status**: MANDATORY GOVERNANCE  
**Enforced Since**: 2026-01-28

---

## Executive Summary

This matrix defines:
1. WHO owns each table
2. WHO can write to each table
3. WHO can read from each table
4. WHAT lifecycle each table follows

---

## 1. Data Ownership Matrix

### Analytics System

| Table | Owner | Write | Read | SLA | Retention |
|-------|-------|-------|------|-----|-----------|
| analytics_metrics | Analytics Team | Analytics Service | Analytics, Gateway | 99.9% | Hot: 30d, Warm: 6mo, Cold: 1y |
| analytics_reports | Analytics Team | Analytics Service | Analytics, Users | 99.9% | 1 year |
| analytics_dashboards | Analytics Team | Analytics Service | Analytics, Users | 99.9% | Indefinite |
| analytics_queries | Analytics Team | Analytics Service | Analytics | 99% | 7 days (cache) |
| api_metrics | Gateway Team | API Gateway | Analytics, Monitoring, Gateway | 99% | Hot: 7d, Warm: 90d |
| route_search_metrics | Route Team | Route Service | Analytics, Route Service | 99% | Hot: 7d, Warm: 6mo |
| cache_metrics | DevOps Team | Services | Analytics, Monitoring | 95% | Hot: 24h |
| user_engagement | Data Team | Data Service | Analytics, Data Service | 99% | Hot: 30d, Warm: 1y |
| user_locations | Data Team | Data Service | Analytics (filtered) | 99% | Hot: 7d, then purge (GDPR) |
| business_metrics | Data Team | Data Service | Analytics, Billing | 99.9% | 2 years |
| alert_configurations | Analytics Team | Analytics Service | Analytics | 99% | Indefinite |
| alert_history | Analytics Team | Analytics Service | Analytics, Monitoring | 99% | 2 years |

### Route System

| Table | Owner | Write | Read | SLA | Retention |
|-------|-------|-------|------|-----|-----------|
| routes | Route Team | Route Service (admin) | All Services | 99.9% | Indefinite (versioned) |
| route_segments | Route Team | Route Service (admin) | Route Service, Analytics | 99.9% | Indefinite |
| stations | Route Team | Route Service (admin) | All Services | 99.9% | Indefinite |
| route_versions | Route Team | Route Service | Route Service, Analytics | 99% | 2 years |
| station_rankings | Route Team | Route Service (ETL) | Analytics, Route Service | 99% | Daily updates |

### Core System

| Table | Owner | Write | Read | SLA | Retention |
|-------|-------|-------|------|-----|-----------|
| tenants | Auth Team | Auth Service | All Services | 99.95% | Indefinite |
| api_keys | Auth Team | Auth Service | Gateway, Auth Service | 99.95% | Key lifetime |
| audit_logs | Monitoring Team | All Services | Monitoring, Auth, Compliance | 99.9% | 5 years (compliance) |
| users | Auth Team | Auth Service | Auth, Data Service (filtered) | 99% | Indefinite |

---

## 2. Write Access Rules

### Who Can Write?

```
analytics_metrics
  ✅ Analytics Service (primary)
  ❌ Any other service
  ❌ Manual SQL (never)

api_metrics
  ✅ API Gateway (automatic)
  ✅ Services (via gateway)
  ❌ Manual SQL

user_engagement
  ✅ Data Service (primary)
  ✅ Services (events)
  ❌ Analytics Service (read-only)

audit_logs
  ✅ All Services (append-only)
  ❌ Deletion (only after retention)
```

---

## 3. Read Access Rules

### Principle: Least Privilege

```
📊 Analytics Service reads:
  ✅ All tables (read-only)
  ✅ Cross-tenant aggregations
  ✅ Historical data (warm storage)
  ❌ Personally identifiable info (except user engagement metrics)

🔐 Auth Service reads:
  ✅ tenants, api_keys, users
  ✅ audit_logs (filtered to own tenant)
  ❌ Business metrics
  ❌ User behavior (privacy)

🗺️ Route Service reads:
  ✅ routes, stations, route_segments
  ✅ route_search_metrics (own searches)
  ✅ user_engagement (anonymized)
  ❌ Business metrics (not its concern)

🗂️ Data Service reads:
  ✅ All tables (for aggregation)
  ✅ user_engagement
  ✅ Reads are filtered by tenant_id
  ❌ Cannot modify other services' data
```

---

## 4. Data Lifecycle Policies

### Hot Data (Recent - Days 0-7)
**Storage**: PostgreSQL (SSD)  
**Access**: Real-time queries OK  
**Purpose**: Operational dashboards, alerts  
**Retention**: Full fidelity

```
Example:
  analytics_metrics: 7 days
  api_metrics: 7 days
  cache_metrics: 24 hours (high volume, low value)
  audit_logs: indefinite (compliance)
```

### Warm Data (Historical - Days 7-180)
**Storage**: TimescaleDB or ClickHouse (compressed)  
**Access**: Batch queries OK (not real-time)  
**Purpose**: Historical analysis, reports  
**Retention**: Aggregated fidelity (hourly summaries)

```
Example:
  analytics_metrics: aggregate to hourly
  route_search_metrics: compress by factor 10
  api_metrics: delete low-priority endpoints
```

### Cold Data (Archive - 6+ months)
**Storage**: S3 (Parquet files, encrypted)  
**Access**: Retrieval jobs (24hr latency OK)  
**Purpose**: Compliance, deep historical analysis  
**Retention**: Aggregated (daily summaries)

```
Example:
  audit_logs: Archive to S3 after 1 year
  business_metrics: Keep forever
  user_locations: Purge (GDPR)
```

---

## 5. Data Contracts by Service

### Analytics Service Writes These

```python
# analytics_metrics (primary write)
{
  "metric_id": "uuid",
  "tenant_id": "uuid",  # Required for isolation
  "metric_name": "total_searches",
  "metric_value": 1250,
  "computed_at": "2026-01-28T10:00:00Z"
}

# Contract:
# - NEVER update (append-only)
# - MUST include tenant_id
# - MUST be idempotent (safe to retry)
```

### API Gateway Writes These

```python
# api_metrics (high volume)
{
  "metric_id": "uuid",
  "tenant_id": "uuid",
  "endpoint": "/v1/analytics/query",
  "response_time_ms": 125,
  "status_code": 200,
  "created_at": "2026-01-28T10:00:00Z"
}

# Contract:
# - Fire and forget (async write)
# - Acceptable to lose (not critical)
# - Batch writes for performance
```

### Data Service Writes These

```python
# user_engagement (events)
{
  "metric_id": "uuid",
  "tenant_id": "uuid",
  "user_id": "uuid",
  "action": "route_search",
  "created_at": "2026-01-28T10:00:00Z"
}

# Contract:
# - Append-only events
# - MUST have tenant isolation
# - Queries must filter by tenant_id
```

---

## 6. Cross-Service Data Queries

### When Analytics Service Needs Data from Route Service

```python
# ❌ WRONG: Direct database query
SELECT * FROM routes WHERE tenant_id = ?  # Violates ownership

# ✅ RIGHT: Via API endpoint
GET /v1/routes?tenant_id={}&limit=100
# Calls Route Service, which enforces access control

# ✅ ALSO OK: Via shared read-only table
# If routes table is in public schema (shared)
# But still must filter by tenant_id
```

### When Auth Service Needs User Data

```python
# ✅ Auth service owns: tenants, api_keys, users
SELECT * FROM users WHERE tenant_id = ?  # OK (owns it)

# ✅ Auth service can READ: api_metrics
SELECT * FROM api_metrics WHERE tenant_id = ? AND created_at > NOW() - '7 days'::interval
# For audit/logging purposes

# ❌ Auth service CANNOT write: api_metrics
# Only API Gateway can write those
```

---

## 7. Data Quality Guarantees

### By Table Owner

```
Analytics Team (analytics_metrics)
  - Uniqueness: metric_id is globally unique
  - No nulls: metric_name, metric_value required
  - Freshness: Updated hourly
  - Accuracy: Verified by data quality checks

Gateway Team (api_metrics)
  - Uniqueness: metric_id is globally unique
  - Sampling OK: High volume, can sample 10%
  - Freshness: Real-time (sub-1s)
  - Accuracy: Best effort (may lose under load)

Route Team (routes)
  - Uniqueness: route_id is globally unique
  - No nulls: All required fields filled
  - Freshness: Updated on manual admin action
  - Accuracy: 100% (validated on insert)
```

---

## 8. Data Migration Rules

### When Schema Changes

```
1. Create new table with versioned name
   routes → routes_v2

2. Populate from old table
   INSERT INTO routes_v2 SELECT ... FROM routes

3. Deploy new code to read from routes_v2
   Dual-write period (write to both)

4. Verify data consistency
   SELECT COUNT(*) FROM routes_v2 - routes
   (Should be 0)

5. Promote new table
   ALTER TABLE routes_v2 RENAME TO routes

6. Drop old table
   DROP TABLE routes_old (after 30-day grace period)
```

---

## 9. Data Deletion & GDPR Compliance

### Tables with PII (Personally Identifiable Information)

```
user_locations
  - Stores: IP, location, device
  - Retention: 30 days max
  - Deletion: Automatic after 30 days
  - Right to be forgotten: Immediate purge by user ID

users
  - Stores: Name, email, phone
  - Retention: As long as account exists
  - Deletion: Account deletion → cascade delete
  - Right to be forgotten: 30-day grace period, then purge
```

### Deletion Procedure

```sql
-- Delete user data (GDPR request)
BEGIN;
  DELETE FROM user_locations WHERE user_id = 'uuid';
  DELETE FROM user_engagement WHERE user_id = 'uuid';
  DELETE FROM users WHERE user_id = 'uuid';
  INSERT INTO audit_logs VALUES ('GDPR deletion', user_id);
COMMIT;
```

---

## 10. Enforcement Mechanisms

### In Code Review

- [ ] New table introduced? Check DATA_OWNERSHIP_MATRIX
- [ ] Cross-service data access? Must go through API
- [ ] Write to table not owned? Reject PR
- [ ] Missing tenant_id filter? Reject PR
- [ ] PII stored without expiry? Reject PR

### In Deployment

- [ ] Database permissions enforced by PostgreSQL RBAC
- [ ] Service accounts have minimal privileges
- [ ] Audit logs track all writes by service
- [ ] Violations trigger alerts

---

**Matrix Established**: 2026-01-28  
**Review Cycle**: Quarterly or when adding tables  
**Owner**: Database Team + Architecture  
**Last Updated**: 2026-01-28
