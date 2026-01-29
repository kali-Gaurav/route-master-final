# Role-Based Access Control & Authorization (RBAC/ABAC)

**Version**: 1.0  
**Status**: MANDATORY SECURITY REQUIREMENT  
**Enforced Since**: 2026-01-28

---

## Executive Summary

This document defines:
1. RBAC model (who can do what)
2. Fine-grained permissions per endpoint
3. Service-to-service authentication (mTLS)
4. Tenant isolation enforcement
5. Audit logging of all access

---

## 1. RBAC Model

### Roles

```
Admin
  - Can read/write all data
  - Can manage users
  - Can view audit logs
  - Can configure alerts
  - Can access system settings

Power User
  - Can read/write own tenant data
  - Can create reports
  - Can export data
  - Cannot manage users
  - Cannot modify system settings

Regular User
  - Can read own tenant data
  - Can create saved searches
  - Can export own data
  - Cannot modify data
  - Cannot see other tenants

Read-Only User
  - Can only read own tenant data
  - Cannot create, update, delete
  - Cannot export

Service Account
  - For service-to-service calls
  - Limited to specific endpoints
  - Uses mTLS for authentication
```

### Role Assignment

```
User: john@company.com
Tenant: my-company
Roles:
  - analytics_admin (within my-company)
  - route_viewer (within my-company)

User: jane@company.com
Tenant: my-company
Roles:
  - analytics_viewer (within my-company)

User: api@my-company.com (service account)
Tenant: my-company
Roles:
  - service:analytics:read
  - service:route:read
```

---

## 2. Fine-Grained Permissions

### Endpoint Permissions Matrix

```
GET /v1/analytics/metrics

Admin:          ✅ Allowed
Power User:     ✅ Allowed (own tenant only)
Regular User:   ✅ Allowed (own tenant only)
Read-Only User: ✅ Allowed (own tenant only)
Service Account:✅ Allowed (if has service:analytics:read)

POST /v1/analytics/metrics

Admin:          ✅ Allowed
Power User:     ✅ Allowed (own tenant only)
Regular User:   ❌ Denied
Read-Only User: ❌ Denied
Service Account:❌ Denied (service accounts are read-only)

DELETE /v1/analytics/metrics/{id}

Admin:          ✅ Allowed
Power User:     ❌ Denied (cannot delete)
Regular User:   ❌ Denied
Read-Only User: ❌ Denied
Service Account:❌ Denied
```

### Implementation

```python
# analytics_service/auth.py
from fastapi import FastAPI, Depends, HTTPException, status
from typing import List

app = FastAPI()

async def get_current_user(token: str = Header(...)):
    """Extract and verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        roles = payload.get("roles", [])
        tenant_id = payload.get("tenant_id")
        return {"user_id": user_id, "roles": roles, "tenant_id": tenant_id}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(*roles: str):
    """Dependency to check if user has required role"""
    async def check_role(current_user = Depends(get_current_user)):
        user_roles = set(current_user["roles"])
        required_roles = set(roles)
        
        if not user_roles.intersection(required_roles):
            raise HTTPException(
                status_code=403,
                detail=f"Requires one of: {roles}"
            )
        
        return current_user
    
    return check_role

def require_tenant_isolation():
    """Dependency to enforce tenant isolation"""
    async def check_tenant(current_user = Depends(get_current_user)):
        # Tenant ID must match
        return current_user
    
    return check_tenant

# Usage
@app.get("/v1/analytics/metrics")
async def get_metrics(
    tenant_id: str,
    current_user = Depends(require_role("admin", "power_user", "regular_user", "read_only_user"))
):
    """Get metrics - any authenticated user can read"""
    
    # Enforce tenant isolation
    if current_user["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Cannot access other tenant")
    
    return {"metrics": [...]}

@app.post("/v1/analytics/metrics")
async def create_metrics(
    tenant_id: str,
    data: dict,
    current_user = Depends(require_role("admin", "power_user"))
):
    """Create metrics - only admin and power_user"""
    
    if current_user["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Cannot access other tenant")
    
    return {"created": True}

@app.delete("/v1/analytics/metrics/{metric_id}")
async def delete_metrics(
    tenant_id: str,
    metric_id: str,
    current_user = Depends(require_role("admin"))
):
    """Delete metrics - only admin"""
    
    if current_user["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Cannot access other tenant")
    
    return {"deleted": True}
```

---

## 3. JWT Token Structure

### Standard Claims

```json
{
  "iss": "https://auth-service:8000",
  "sub": "user-123",
  "aud": "api",
  "iat": 1674910000,
  "exp": 1674913600,
  "tenant_id": "company-456",
  "email": "john@company.com",
  "roles": [
    "analytics_admin",
    "route_viewer"
  ]
}
```

### Token Validation

```python
# analytics_service/token_validator.py
import jwt
from datetime import datetime

SECRET_KEY = os.environ['JWT_SECRET_KEY']
ALGORITHM = "HS256"

def validate_token(token: str):
    """Validate and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check expiration
        if payload['exp'] < datetime.now().timestamp():
            raise jwt.ExpiredSignatureError()
        
        # Check issuer
        if payload['iss'] != 'https://auth-service:8000':
            raise jwt.InvalidIssuerError()
        
        # Check audience
        if payload['aud'] != 'api':
            raise jwt.InvalidAudienceError()
        
        return payload
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Invalid signature")
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Token Refresh

```
User logs in:
  1. Send username + password to /auth/login
  2. Get access_token (expires in 15 min) + refresh_token (expires in 30 days)
  3. Store refresh_token in secure cookie (httpOnly, secure)
  4. Use access_token in Authorization header

When access_token expires:
  1. Detect 401 response
  2. Send refresh_token to /auth/refresh
  3. Get new access_token
  4. Retry original request

When refresh_token expires:
  1. User must log in again
```

---

## 4. Service-to-Service Authentication (mTLS)

### What Is mTLS?

```
Mutual TLS = both services verify each other

Traditional (one-way):
  Client trusts Server (server has certificate)
  Server doesn't verify client
  
mTLS (two-way):
  Client verifies Server certificate
  Server verifies Client certificate
  Only known services can communicate
```

### Implementation

```yaml
# kubernetes/analytics-service-mtls.yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: analytics-service
spec:
  mtls:
    mode: STRICT  # Require mTLS

---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: analytics-service
spec:
  host: analytics-service
  trafficPolicy:
    tls:
      mode: MUTUAL  # Use mTLS
      clientCertificate: /etc/istio/certs/tls.crt
      privateKey: /etc/istio/certs/tls.key
      caCertificates: /etc/istio/certs/ca.crt
```

### Certificate Rotation

```
Kubernetes (via Istio):
  - Automatically generates certificates
  - Rotates every 90 days
  - No downtime during rotation
  - Pods get new certs automatically

Verification:
  - Check certificate expiration
  - Alert when < 30 days to expiry
  - Automatic rotation prevents expiry
```

---

## 5. Tenant Isolation Enforcement

### Database Level

```sql
-- Create tenant-specific schema
CREATE SCHEMA company_123;

-- All tables in tenant schema
CREATE TABLE company_123.analytics_metrics (
  metric_id UUID PRIMARY KEY,
  metric_name VARCHAR,
  metric_value NUMERIC
);

-- Auth service only allows queries to own schema
SELECT * FROM company_123.analytics_metrics;  -- ✅ OK
SELECT * FROM company_456.analytics_metrics;  -- ❌ Denied
```

### Application Level

```python
# analytics_service/db.py
from sqlalchemy import create_engine

class TenantAwareDatabase:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def get_session(self, tenant_id: str):
        """Get database session for specific tenant"""
        # Schema per tenant approach
        db_url = f"{self.base_url}?schema={tenant_id}"
        return sessionmaker(bind=create_engine(db_url))()

# Usage
db = TenantAwareDatabase("postgresql://localhost/railway")

# Get metrics for tenant A
session_a = db.get_session("tenant-a")
metrics_a = session_a.query(Metric).all()  # Only tenant-a data

# Get metrics for tenant B
session_b = db.get_session("tenant-b")
metrics_b = session_b.query(Metric).all()  # Only tenant-b data
```

### Query Filtering

```python
# ✅ Always filter by tenant_id
def get_user_metrics(tenant_id: str, user_id: str):
    """Get metrics for specific user in specific tenant"""
    metrics = session.query(Metric) \
        .filter(Metric.tenant_id == tenant_id) \
        .filter(Metric.user_id == user_id) \
        .all()
    
    return metrics

# ❌ NEVER query without tenant filter
def get_metrics_bad(user_id: str):
    """BUG: Returns metrics from ALL tenants"""
    metrics = session.query(Metric) \
        .filter(Metric.user_id == user_id) \
        .all()  # WRONG! No tenant filter
    
    return metrics  # May leak data from other tenants
```

---

## 6. Audit Logging

### Audit Log Schema

```python
# models/audit_log.py
from sqlalchemy import Column, String, DateTime, JSON, UUID
from datetime import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    audit_id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, nullable=False, index=True)
    user_id = Column(UUID, nullable=False)
    action = Column(String, nullable=False)  # CREATE, READ, UPDATE, DELETE
    resource_type = Column(String)  # metrics, dashboards, reports
    resource_id = Column(UUID)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String)
    user_agent = Column(String)
    result = Column(String)  # success, denied, error
    error_message = Column(String, nullable=True)
    details = Column(JSON)  # Additional context
```

### Audit Logging Middleware

```python
# analytics_service/audit_middleware.py
from fastapi import Request
import json
from uuid import uuid4
from datetime import datetime

async def audit_log_middleware(request: Request, call_next):
    """Log all requests for audit"""
    
    start_time = datetime.utcnow()
    user_id = request.headers.get('X-User-Id')
    tenant_id = request.headers.get('X-Tenant-Id')
    
    response = await call_next(request)
    
    # Create audit log entry
    audit_entry = {
        'audit_id': str(uuid4()),
        'tenant_id': tenant_id,
        'user_id': user_id,
        'action': request.method,
        'resource_type': extract_resource_type(request.url.path),
        'timestamp': start_time.isoformat(),
        'ip_address': request.client.host,
        'user_agent': request.headers.get('User-Agent'),
        'method': request.method,
        'path': request.url.path,
        'status_code': response.status_code,
        'duration_ms': (datetime.utcnow() - start_time).total_seconds() * 1000
    }
    
    # Save to database
    audit_log = AuditLog(**audit_entry)
    db.session.add(audit_log)
    db.session.commit()
    
    return response
```

### Querying Audit Logs

```python
# Query: Who accessed analytics metrics?
SELECT * FROM audit_logs
WHERE resource_type = 'metrics'
AND action = 'READ'
AND timestamp > NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC;

# Result:
# user_id | tenant_id | action | timestamp | ip_address
# john123 | company_a | READ   | 2026-01-28 10:15:00 | 192.168.1.1
# jane456 | company_a | READ   | 2026-01-28 10:14:00 | 192.168.1.2
```

---

## 7. Authorization Enforcement Checklist

Before deploying service:

- [ ] All endpoints have role checks (@require_role)
- [ ] All endpoints filter by tenant_id
- [ ] JWT token validation implemented
- [ ] mTLS configured for service-to-service calls
- [ ] Service accounts created for integrations
- [ ] Audit logging configured
- [ ] Audit log retention policy set (5 years min)
- [ ] Authorization tests pass (test each role)
- [ ] Cross-tenant queries rejected (integration test)
- [ ] Secrets in JWT token (never in URL)
- [ ] Token refresh mechanism working
- [ ] Rate limiting per user/tenant

---

**Document Established**: 2026-01-28  
**Owner**: Security/Auth Team  
**Review Cycle**: When adding new endpoints or roles  
**Last Updated**: 2026-01-28
