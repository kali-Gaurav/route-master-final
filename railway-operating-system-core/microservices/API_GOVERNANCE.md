# API Governance Framework

**Version**: 1.0  
**Status**: MANDATORY FOR ALL SERVICES  
**Enforced Since**: 2026-01-28

---

## 1. API Versioning Strategy

### 1.1 URL Versioning Pattern

```
/v{MAJOR}/resource

Examples:
  ✅ GET /v1/analytics/query
  ✅ POST /v2/routes/search
  ❌ GET /analytics/v1/query  (wrong position)
  ❌ GET /analytics?version=1 (no query param versioning)
```

### 1.2 Version Lifecycle

| Stage | Timeline | Status | Example |
|-------|----------|--------|---------|
| Development | Pre-release | Not published | /v3/routes/search (in development branch only) |
| Active | 12+ months | Production ready | /v1/analytics/query (current stable) |
| Deprecation | 3 months | Warning headers | /v1/routes (deprecated, use /v2) |
| Sunset | 6 months | Removed entirely | (/v0 gone) |

### 1.3 Breaking Change Definition

**What IS a breaking change?**
```python
# ❌ Removing a field
{
  "id": "uuid",
  "name": "string",
  "email": "string"  # Removed in v2 → BREAKING
}

# ❌ Changing field type
{
  "duration": 125  # int
  # Changed to string in v2 → BREAKING
}

# ❌ Changing error codes
409 Conflict → 422 Unprocessable Entity  # BREAKING

# ❌ Changing endpoint path
/v1/metrics → /v1/analytics/metrics  # BREAKING

# ❌ Changing HTTP method
GET /v1/reports → POST /v1/reports  # BREAKING
```

**What is NOT a breaking change?**
```python
# ✅ Adding optional field
{
  "id": "uuid",
  "name": "string",
  "email": "string",
  "phone": "string?"  # Optional → OK
}

# ✅ Reordering fields
{
  "name": "string",
  "id": "uuid"  # Different order → OK (JSON is unordered)
}

# ✅ Making endpoint stricter
POST /v1/metrics body:
  BEFORE: email is optional
  AFTER: email is required  # Can enforce if handled gracefully
```

---

## 2. Versioning Rules

### 2.1 Major Version (Breaking Changes ONLY)

**Create new major version when:**

```python
# Rule 1: Removing required field
v1: GET /analytics
    Response: { id, name, email }

v2: GET /analytics
    Response: { id, name }  # email removed → /v2/
```

**Minimum supported versions**: Keep 2 active

```
Active versions:
  /v1/analytics  ← Keep supporting
  /v2/analytics  ← Current stable
  /v3/analytics  ← In deprecation (3-month warning)
  /v4/analytics  ← Not supported
```

### 2.2 Minor Version (Non-Breaking Enhancements)

**Minor versions happen within major version**

```python
# Example: v1.1 vs v1.2 internally
# But URL stays: /v1/analytics

v1.1:
  GET /v1/analytics?format=json

v1.2 (compatible):
  GET /v1/analytics?format=json&include_trends=true
  # New optional parameter OK

# URL remains /v1
```

### 2.3 No Patch Versions in URLs

```python
# ❌ WRONG: /v1.2.3/analytics
# ✅ RIGHT: /v1/analytics (bugfixes transparent)
```

---

## 3. Deprecation Process

### 3.1 Deprecation Headers

**When endpoint becomes deprecated:**

```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Wed, 31 Jul 2026 23:59:59 GMT
Link: </v2/analytics/query>; rel="successor-version"
X-API-Warn: "v1 deprecated, migrate to v2"

{
  "data": {...},
  "metadata": {
    "deprecation_notice": "Endpoint /v1/analytics will be removed on 2026-07-31"
  }
}
```

### 3.2 Deprecation Timeline

```
Day 1: Announcement
  └─ Email all API consumers
  └─ Add deprecation headers
  └─ Update documentation
  └─ Post on status page

Day 30-90: Warnings
  └─ Return 410 Gone with redirect
  └─ Log all requests to deprecated endpoint
  └─ Alert: X% traffic still using v1

Day 91-180: Migration Support
  └─ Support both v1 and v2
  └─ Send weekly reminders
  └─ Offer migration help

Day 180+: Sunset
  └─ Remove v1 endpoint
  └─ Return 404 Not Found
  └─ Archive logs
```

### 3.3 Deprecation Header Example

**For API Gateway:**

```python
@router.get("/v1/analytics/query")
async def query_analytics_v1():
    """DEPRECATED: Use /v2/analytics/query instead"""
    return {
        "status": "success",
        "data": {...},
        "_deprecated": {
            "sunset_date": "2026-07-31",
            "migrate_to": "/v2/analytics/query",
            "reason": "v1 has performance issues, v2 is 10x faster"
        }
    }
```

---

## 4. API Response Contract

### 4.1 Success Response

**ALL services must return this structure:**

```json
{
  "status": "success",
  "data": {
    "items": [],
    "count": 0
  },
  "metadata": {
    "version": "1.0",
    "timestamp": "2026-01-28T10:00:00Z",
    "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
    "request_id": "550e8400-e29b-41d4-a716-446655440001"
  },
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 1000,
    "has_more": true,
    "next_page": 2,
    "prev_page": null
  }
}
```

### 4.2 Error Response

**ALL services must return this structure:**

```json
{
  "status": "error",
  "errors": [
    {
      "code": "INVALID_TENANT_ID",
      "message": "Tenant ID must be a valid UUID",
      "field": "tenant_id",
      "status_code": 400,
      "details": {
        "provided": "invalid-uuid",
        "expected": "uuid format"
      }
    }
  ],
  "metadata": {
    "timestamp": "2026-01-28T10:00:00Z",
    "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
    "trace_id": "550e8400-e29b-41d4-a716-446655440002"
  }
}
```

### 4.3 Standard HTTP Status Codes

| Code | Use Case | Example |
|------|----------|---------|
| 200 | Success | GET /v1/analytics ✅ |
| 201 | Created | POST /v1/reports → new report |
| 202 | Accepted | POST /v1/export → long-running job |
| 204 | No content | DELETE /v1/cache → cleared |
| 400 | Bad request | Missing required field |
| 401 | Unauthorized | Invalid API key |
| 403 | Forbidden | Tenant access denied |
| 404 | Not found | /v1/endpoint-deleted (v1 sunset) |
| 409 | Conflict | Duplicate resource |
| 410 | Gone (Deprecated) | /v1/old-endpoint (sunset reached) |
| 422 | Validation error | Invalid data format |
| 429 | Rate limited | Too many requests |
| 500 | Server error | Database crash |
| 503 | Service unavailable | Circuit breaker open |
| 504 | Timeout | Query exceeded 60s |

---

## 5. Error Code Standardization

### 5.1 Error Code Format

```
[SERVICE]_[DOMAIN]_[ERROR]

Examples:
  ANALYTICS_QUERY_INVALID_DATE_RANGE
  AUTH_TENANT_NOT_FOUND
  GATEWAY_RATE_LIMIT_EXCEEDED
  ROUTES_ALGORITHM_TIMEOUT
```

### 5.2 Global Error Codes

| Code | HTTP | Meaning | Retry? |
|------|------|---------|--------|
| INTERNAL_SERVER_ERROR | 500 | Unexpected error | Yes (exponential backoff) |
| SERVICE_UNAVAILABLE | 503 | Service down/maintenance | Yes (wait longer) |
| GATEWAY_TIMEOUT | 504 | Query too slow | No (or longer timeout) |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests | Yes (after delay) |
| INVALID_REQUEST | 400 | Bad request | No |
| UNAUTHORIZED | 401 | No auth | No |
| FORBIDDEN | 403 | No permission | No |
| NOT_FOUND | 404 | Resource deleted | No |

### 5.3 Service-Specific Error Codes

**Analytics Service**:
```
ANALYTICS_QUERY_INVALID_DATE_RANGE
ANALYTICS_METRIC_NOT_FOUND
ANALYTICS_TENANT_NO_DATA
ANALYTICS_EXPORT_TOO_LARGE
ANALYTICS_CACHE_MISS
ANALYTICS_AGGREGATION_FAILED
```

**Route Service**:
```
ROUTES_SEARCH_NO_RESULTS
ROUTES_ALGORITHM_TIMEOUT
ROUTES_INVALID_STATIONS
ROUTES_TRANSFER_LIMIT_EXCEEDED
```

**Auth Service**:
```
AUTH_INVALID_API_KEY
AUTH_TENANT_SUSPENDED
AUTH_RATE_LIMIT_PER_TENANT
AUTH_INVALID_CREDENTIALS
```

---

## 6. Rate Limiting Strategy

### 6.1 Rate Limit Headers

**Response must include**:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704067260
X-RateLimit-RetryAfter: 5
```

### 6.2 Rate Limit Tiers

| Tier | Requests/Min | Concurrent | Burst | Audience |
|------|--------------|-----------|-------|----------|
| Public | 10 | 1 | No | Unauthenticated |
| Standard | 100 | 5 | 150/min | Free tier |
| Premium | 500 | 20 | 750/min | Paid tier |
| Enterprise | 2000 | 100 | Unlimited | Custom |

### 6.3 Rate Limiting Response

```json
{
  "status": "error",
  "errors": [
    {
      "code": "RATE_LIMIT_EXCEEDED",
      "message": "You have exceeded 100 requests per minute",
      "status_code": 429,
      "details": {
        "limit": 100,
        "current": 102,
        "reset_at": "2026-01-28T10:01:00Z"
      }
    }
  ]
}
```

---

## 7. Backward Compatibility Rules

### 7.1 Golden Rules

```python
# Rule 1: Always accept unknown fields
@dataclass
class Query:
    metric: str
    start_date: date
    # unknown_future_field: ??? (ignore gracefully)

# Rule 2: Always provide defaults
@dataclass
class Response:
    id: str
    name: str = ""  # Don't require if new
    created_at: datetime = datetime.now()

# Rule 3: Never reorder required fields
v1: (id, name, email)
v2: (id, name, email, phone)  # ✅ Append only
v2: (id, email, name, phone)  # ❌ Reordered (breaks client parsing)

# Rule 4: Never change enum values
v1: status = "pending" | "active" | "complete"
v2: status = "queued" | "processing" | "done"  # ❌ BREAKING

v2: status = "pending" | "active" | "complete" | "archived"  # ✅ OK
```

### 7.2 Compatibility Matrix

| Change | Major | Minor | Patch | Breaking? |
|--------|-------|-------|-------|-----------|
| Add optional field | No | No | Yes | No |
| Remove field | Yes | No | No | Yes |
| Change field type | Yes | No | No | Yes |
| Rename endpoint | Yes | No | No | Yes |
| Add HTTP method | No | No | Yes | No |
| Change HTTP method | Yes | No | No | Yes |
| Expand enum values | No | No | Yes | No |
| Remove enum values | Yes | No | No | Yes |

---

## 8. API Documentation Requirements

### 8.1 Every Endpoint Must Document

```python
@router.get("/v1/analytics/query")
async def query_analytics(
    tenant_id: UUID,
    start_date: date,
    metrics: List[str]
):
    """
    Execute custom analytics query
    
    API Version: 1.0
    Status: Active (until 2027-01-28)
    
    Parameters:
      tenant_id (UUID): Required. Tenant to query
      start_date (date): Optional. Start date YYYY-MM-DD
      metrics (List[str]): Required. Metrics to retrieve
    
    Response:
      {
        "status": "success",
        "data": {...},
        "metadata": {...}
      }
    
    Errors:
      400: INVALID_TENANT_ID - Tenant ID invalid
      401: UNAUTHORIZED - No API key
      404: NOT_FOUND - Metrics not found
      429: RATE_LIMIT_EXCEEDED - Rate limit
      503: SERVICE_UNAVAILABLE - Database down
      504: GATEWAY_TIMEOUT - Query too slow
    
    Examples:
      curl -X GET http://localhost:8084/v1/analytics/query \\
        -H "Authorization: Bearer KEY" \\
        -H "X-Tenant-ID: 550e8400-e29b-41d4-a716-446655440000" \\
        -d '{"metrics": ["total_searches"]}'
    
    Deprecation: None (v1 stable)
    Related: /v1/analytics/metrics, /v1/dashboard
    """
```

### 8.2 OpenAPI Schema (Swagger)

**Every service must export OpenAPI 3.0 spec:**

```bash
GET /openapi.json
GET /docs  (Swagger UI)
GET /redoc  (ReDoc)
```

---

## 9. API Governance Enforcement

### 9.1 Code Review Checklist

Before ANY API endpoint merges:

- [ ] Versioning follows `/v{major}` pattern
- [ ] Response follows contract structure
- [ ] Error codes are documented
- [ ] HTTP status codes are correct
- [ ] Breaking changes approved by Architecture
- [ ] Deprecation headers added if needed
- [ ] Rate limiting configured
- [ ] Backward compatibility verified
- [ ] OpenAPI schema updated
- [ ] Docs include all error codes

### 9.2 Pre-Production Validation

```bash
# Check API contract compliance
./scripts/validate-api-contract.sh

# Check for breaking changes
./scripts/check-breaking-changes.sh

# Generate OpenAPI docs
./scripts/generate-openapi.sh

# Validate against schema
./scripts/validate-against-schema.sh
```

---

## 10. Service-Specific API Policies

### 10.1 Analytics Service API

```
Base: /v1/analytics

Endpoints:
  POST /v1/analytics/query (custom queries)
  GET /v1/dashboard/{type} (dashboards)
  POST /v1/reports/generate (reporting)
  GET /v1/analytics/metrics (metrics)
  GET /v1/analytics/export/{type} (exports)
  GET /health (status)

Rate Limit: 100 req/min (Premium: 500)
Timeout: 60 seconds
Caching: 5 minutes
Deprecation Policy: 180 days notice
```

### 10.2 Route Service API

```
Base: /v1/routes

Endpoints:
  GET /v1/routes/search (route search)
  GET /v1/routes/{id} (route details)
  POST /v1/routes/optimize (route optimization)
  GET /v1/stations (station list)
  GET /health (status)

Rate Limit: 500 req/min
Timeout: 30 seconds
Caching: 2 minutes
Deprecation Policy: 180 days notice
```

### 10.3 Auth Service API

```
Base: /v1/auth

Endpoints:
  POST /v1/auth/login (login)
  POST /v1/auth/validate (validation)
  POST /v1/auth/refresh (refresh token)
  POST /v1/auth/logout (logout)
  GET /health (status)

Rate Limit: 10 req/min (public)
Timeout: 10 seconds
Caching: None
Deprecation Policy: 180 days notice
```

---

## 11. Governance Meeting & Review

**API Governance Board meets**: Monthly

**Attendees**:
- Backend Team Lead
- Frontend Team Lead
- DevOps Lead
- Product Manager

**Agenda**:
- Review new API endpoints for compliance
- Discuss breaking changes
- Approve major versions
- Review deprecations
- Update this policy

---

**API Governance Enforced Since**: 2026-01-28  
**Review Cycle**: Quarterly  
**Contact**: Platform Architecture Team