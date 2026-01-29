# Backend Optimization & Fix Implementation Plan

## Phase 1: Critical Fixes (Days 1-2)

### 1. Fix ID Type Consistency
**Status:** Ready to implement
**Impact:** High - Affects all models

```python
# models/user.py - BEFORE
id = Column(Integer, primary_key=True, index=True)

# models/user.py - AFTER
from uuid import uuid4
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
```

### 2. Add Database Connection Pooling
**File:** `db_connection.py`
```python
# BEFORE
_engine = create_engine(db_url, pool_pre_ping=True, echo=False)

# AFTER
_engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=0,
    pool_recycle=3600,
    connect_args={"connect_timeout": 10}
)
```

### 3. Fix Hardcoded Secrets
**File:** `config.py`
```python
# BEFORE
jwt_secret: str = "your-super-secret-jwt-key-change-this-in-production"

# AFTER
jwt_secret: str = Field(..., description="Must be set via environment")

def __init__(self, **kwargs):
    if not os.getenv("JWT_SECRET"):
        raise ValueError("JWT_SECRET environment variable must be set!")
    super().__init__(**kwargs)
```

### 4. Add Password Complexity Validation
**File:** `schemas/auth.py`
```python
from pydantic import field_validator
import re

class UserCreate(UserBase):
    password: str
    
    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain number')
        if not re.search(r'[!@#$%^&*]', v):
            raise ValueError('Password must contain special character')
        return v
```

### 5. Add Job Model Missing Fields
**File:** `models/job.py`
```python
from uuid import uuid4

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    type = Column(String, nullable=False)
    status = Column(String, default="pending")
    priority = Column(Integer, default=1)
    payload = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="jobs")
    user = relationship("User", back_populates="jobs")
```

---

## Phase 2: Security Hardening (Days 3-4)

### 6. Implement Token Blacklist & Logout
**File:** `core/security.py` (NEW)
```python
from backend.core.cache import cache
import uuid

class TokenBlacklist:
    @staticmethod
    def revoke_token(token: str, ttl: int = 86400):
        """Add token to blacklist with TTL"""
        token_key = f"blacklist:{hash(token)}"
        cache.set(token_key, {"revoked_at": datetime.utcnow()}, ttl)
    
    @staticmethod
    def is_blacklisted(token: str) -> bool:
        """Check if token is blacklisted"""
        token_key = f"blacklist:{hash(token)}"
        return cache.exists(token_key)

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token"""
    # Check blacklist first
    if TokenBlacklist.is_blacklisted(token):
        return None
    
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None
```

### 7. Add Logout Endpoint
**File:** `api/v1/auth.py`
```python
@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout user by blacklisting token"""
    # Get token from request headers
    # TokenBlacklist.revoke_token(token)
    return {"message": "Logged out successfully"}
```

### 8. Add Rate Limiting to Auth Endpoints
**File:** `api/v1/auth.py`
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("5/minute")
@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # ... existing code

@limiter.limit("3/minute")
@router.post("/register", response_model=User)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # ... existing code
```

### 9. Add Email Verification Workflow
**File:** `services/user_service.py`
```python
def send_verification_email(self, user: User) -> bool:
    """Send verification email"""
    token = create_access_token({"sub": user.email, "type": "email_verification"}, expires_delta=timedelta(hours=24))
    # Send email with verification link
    return True

def verify_email(self, email: str, token: str) -> bool:
    """Verify email address"""
    payload = verify_token(token)
    if payload.get("type") != "email_verification" or payload.get("sub") != email:
        return False
    
    user = self.get_user_by_email(email)
    user.email_verified = True
    self.db.commit()
    return True
```

### 10. Add CSRF Protection
**File:** `main.py`
```python
from fastapi_csrf_protect import CsrfProtect

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfConfig()

@app.post("/token")
async def get_token(request: Request):
    await csrf_protect.validate_csrf(request)
    return {"access_token": "..."}
```

---

## Phase 3: Performance Optimization (Days 5-6)

### 11. Add Query Optimization with JoinedLoad
**File:** `services/route_service.py`
```python
from sqlalchemy.orm import joinedload

def get_routes(self, skip: int = 0, limit: int = 100) -> List[Route]:
    """Get all routes with optimized queries"""
    return self.db.query(Route).options(
        joinedload(Route.origin_station),
        joinedload(Route.destination_station),
        joinedload(Route.train)
    ).offset(skip).limit(limit).all()

def search_routes(self, search: RouteSearch) -> List[Route]:
    """Search routes with optimized queries"""
    query = self.db.query(Route).options(
        joinedload(Route.origin_station),
        joinedload(Route.destination_station)
    )
    # ... filter logic
    return query.offset(search.offset).limit(search.limit).all()
```

### 12. Implement Caching for Route Search
**File:** `services/route_service.py`
```python
from backend.core.cache import cache
import json

def search_routes(self, search: RouteSearch) -> List[Route]:
    """Search routes with caching"""
    # Create cache key from search params
    cache_key = f"routes:search:{json.dumps(search.dict(), sort_keys=True)}"
    
    # Check cache first
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Query database
    query = self.db.query(Route).options(
        joinedload(Route.origin_station),
        joinedload(Route.destination_station)
    )
    
    if search.origin_station:
        # ... filter logic
    
    results = query.offset(search.offset).limit(search.limit).all()
    
    # Cache results for 1 hour
    cache.set(cache_key, results, ttl_seconds=3600)
    
    return results
```

### 13. Add Database Indexes
**File:** `models/route.py`
```python
from sqlalchemy import Index

class Route(Base):
    __tablename__ = "routes"
    
    # ... existing columns
    
    __table_args__ = (
        Index('idx_origin_dest', 'origin_station_id', 'dest_station_id'),
        Index('idx_route_active', 'is_active', 'created_at'),
    )

class Station(Base):
    __tablename__ = "stations"
    
    # ... existing columns
    
    __table_args__ = (
        Index('idx_station_code_active', 'code', 'is_active'),
    )

class Job(Base):
    __tablename__ = "jobs"
    
    # ... existing columns
    
    __table_args__ = (
        Index('idx_job_tenant_status', 'tenant_id', 'status'),
        Index('idx_job_user_tenant', 'user_id', 'tenant_id'),
    )
```

### 14. Adjust Pagination Limits
**File:** `api/v1/routes.py`
```python
@router.get("/", response_model=List[RouteSchema])
async def get_routes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),  # Changed from 100, le=1000
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
```

### 15. Implement Async Database Operations
**File:** `db_connection.py` (NEW - Create `async_db.py`)
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Create async engine
async_engine = create_async_engine(
    settings.database_url.replace("postgresql", "postgresql+asyncpg"),
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
```

---

## Phase 4: Error Handling & Logging (Days 7-8)

### 16. Global Exception Handler
**File:** `main.py`
```python
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")
    logger.error(f"Unhandled exception [{correlation_id}]: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Validation error handler"""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

### 17. Request/Response Logging Middleware
**File:** `main.py`
```python
import time
import structlog

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and responses"""
    start_time = time.time()
    correlation_id = request.headers.get("X-Correlation-ID", f"req-{uuid4()}")
    
    logger = structlog.get_logger()
    
    logger.info(
        "request_start",
        method=request.method,
        path=request.url.path,
        correlation_id=correlation_id
    )
    
    response = await call_next(request)
    duration = time.time() - start_time
    
    logger.info(
        "request_complete",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration * 1000,
        correlation_id=correlation_id
    )
    
    return response
```

### 18. Correlation ID Propagation
**File:** `core/context.py` (NEW)
```python
from contextvars import ContextVar

correlation_id: ContextVar[str] = ContextVar('correlation_id', default='')

def get_correlation_id() -> str:
    return correlation_id.get()

def set_correlation_id(cid: str) -> None:
    correlation_id.set(cid)
```

### 19. Enable Prometheus Metrics
**File:** `main.py` (Uncomment and configure)
```python
from prometheus_client import CollectorRegistry, Counter, Histogram, make_asgi_app

registry = CollectorRegistry()

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    registry=registry
)

@app.middleware("http")
async def add_prometheus_metrics(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(time.time() - start_time)
    
    return response

# Mount metrics endpoint
metrics_app = make_asgi_app(registry=registry)
app.mount("/metrics", metrics_app)
```

### 20. Enhanced Health Check
**File:** `main.py`
```python
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check"""
    try:
        # Check database
        result = db.execute("SELECT 1")
        db.commit()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "services": {
                "api": "operational",
                "database": "operational"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "disconnected",
                "error": str(e)
            }
        )
```

---

## Phase 5: Data Model Improvements (Days 9-10)

### 21. Soft Delete Implementation
**File:** `models/base.py` (NEW)
```python
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func
from datetime import datetime

class BaseModel(Base):
    __abstract__ = True
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    def soft_delete(self):
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        self.deleted_at = None

# Update all models to extend BaseModel
# Queries should filter: .filter(Model.deleted_at.is_(None))
```

### 22. Add Audit Trail
**File:** `models/audit.py` (NEW)
```python
from sqlalchemy import Column, String, Integer, JSON, DateTime
from sqlalchemy.sql import func

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String, nullable=False)  # CREATE, UPDATE, DELETE
    table_name = Column(String, nullable=False)
    record_id = Column(UUID(as_uuid=True), nullable=False)
    before_data = Column(JSON, nullable=True)
    after_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
```

### 23. Add Optimistic Locking
**File:** `models/base.py`
```python
class VersionedModel(BaseModel):
    __abstract__ = True
    
    version = Column(Integer, default=1)

# Use in services:
def update_route(self, route_id: UUID, route_update: RouteUpdate, expected_version: int):
    db_route = self.db.query(Route).filter(
        Route.id == route_id, 
        Route.version == expected_version
    ).first()
    
    if not db_route:
        raise OptimisticLockError("Route was modified by another user")
    
    # Update logic...
    db_route.version += 1
    self.db.commit()
```

---

## Phase 6: Testing & Quality (Days 11-12)

### 24. Fix Route Model Foreign Keys
**File:** `models/route.py`
```python
from uuid import uuid4

class Route(Base):
    __tablename__ = "routes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    train_id = Column(UUID(as_uuid=True), ForeignKey("trains.id"), nullable=False)
    origin_station_id = Column(UUID(as_uuid=True), ForeignKey("stations.id"), nullable=False)
    dest_station_id = Column(UUID(as_uuid=True), ForeignKey("stations.id"), nullable=False)
    distance_km = Column(Float, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    train = relationship("Train", back_populates="routes")
    origin_station = relationship("Station", foreign_keys=[origin_station_id])
    destination_station = relationship("Station", foreign_keys=[dest_station_id])
```

### 25. Fix Duplicate Dependency
**File:** `requirements.txt`
```
# REMOVE one instance of: httpx==0.25.2
```

### 26. Add Security Scanning
**File:** `.github/workflows/security.yml` (NEW)
```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  bandit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Bandit
        run: pip install bandit && bandit -r backend/
  
  safety:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Safety
        run: pip install safety && safety check
```

### 27. Implement Test Database Isolation
**File:** `tests/conftest.py`
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db_connection import Base

@pytest.fixture(scope="function")
def test_db():
    """Create a new test database for each test"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    """Create test client with isolated database"""
    from backend.main import app
    from fastapi.testclient import TestClient
    
    def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
```

---

## Implementation Checklist

```
PHASE 1: CRITICAL FIXES
- [ ] Fix all ID types to UUID
- [ ] Add database connection pooling
- [ ] Remove hardcoded JWT secret
- [ ] Add password complexity validation
- [ ] Fix Job model schema mismatch

PHASE 2: SECURITY
- [ ] Implement token blacklist
- [ ] Add logout endpoint
- [ ] Rate limit auth endpoints
- [ ] Add email verification
- [ ] Add CSRF protection

PHASE 3: PERFORMANCE
- [ ] Add query optimization (joinedload)
- [ ] Implement caching for searches
- [ ] Add database indexes
- [ ] Adjust pagination limits
- [ ] Implement async operations

PHASE 4: LOGGING & MONITORING
- [ ] Global exception handler
- [ ] Request/response logging
- [ ] Correlation ID propagation
- [ ] Enable Prometheus metrics
- [ ] Enhanced health checks

PHASE 5: DATA MODELS
- [ ] Soft delete implementation
- [ ] Audit trail logging
- [ ] Optimistic locking
- [ ] Fix Route foreign keys
- [ ] Fix duplicate dependencies

PHASE 6: QUALITY
- [ ] Security scanning setup
- [ ] Test database isolation
- [ ] Load testing suite
- [ ] Integration tests
- [ ] Documentation updates
```

