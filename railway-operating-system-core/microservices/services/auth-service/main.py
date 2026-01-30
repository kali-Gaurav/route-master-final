# ===============================================
# AUTH SERVICE
# ===============================================
# Microservice handling authentication and tenant management
# Manages API keys, tenant validation, and access control

import os
import sys
import logging
import hashlib
import secrets
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID

# Add project root to path to enable shared module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import FastAPI, HTTPException, Depends, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
import uvicorn
import redis

from shared.models import DatabaseManager, Tenant, APIKey
from shared.config import (
    API_CONFIG, DATABASE_CONFIG, REDIS_CONFIG, AUTH_CONFIG,
    get_cors_origins
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, API_CONFIG['log_level']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Railway OS Auth Service",
    description="Authentication and tenant management service",
    version="1.0.0",
    debug=API_CONFIG['debug_mode']
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security scheme
security = HTTPBearer()

# Global components
db_manager = None
redis_client = None

# ===============================================
# DATA MODELS
# ===============================================

class TenantCreateRequest(BaseModel):
    tenant_name: str
    tenant_domain: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    subscription_plan: Optional[str] = "basic"

    @validator('tenant_name')
    def validate_tenant_name(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Tenant name must be at least 3 characters')
        return v.strip()

class TenantResponse(BaseModel):
    tenant_id: str
    tenant_name: str
    tenant_domain: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    subscription_plan: str
    is_active: bool
    created_at: str
    updated_at: str

class APIKeyCreateRequest(BaseModel):
    api_key_name: str
    rate_limit_per_minute: Optional[int] = AUTH_CONFIG['default_rate_limit_per_minute']
    rate_limit_per_hour: Optional[int] = AUTH_CONFIG['default_rate_limit_per_hour']

    @validator('api_key_name')
    def validate_api_key_name(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('API key name must be at least 3 characters')
        return v.strip()

class APIKeyResponse(BaseModel):
    api_key_id: str
    tenant_id: str
    api_key_name: str
    is_active: bool
    rate_limit_per_minute: int
    rate_limit_per_hour: int
    created_at: str
    last_used_at: Optional[str]
    expires_at: Optional[str]

class AuthValidationResponse(BaseModel):
    tenant_id: str
    tenant_name: str
    is_active: bool
    rate_limit_per_minute: int
    rate_limit_per_hour: int
    api_key_name: str

# ===============================================
# UTILITY FUNCTIONS
# ===============================================

def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)

def get_rate_limit_key(tenant_id: str, identifier: str) -> str:
    """Generate Redis key for rate limiting"""
    return f"ratelimit:{tenant_id}:{identifier}"

def check_rate_limit(tenant_id: str, rate_limit_per_minute: int, rate_limit_per_hour: int) -> bool:
    """Check if request is within rate limits"""
    try:
        current_minute = datetime.utcnow().strftime("%Y-%m-%d-%H-%M")
        current_hour = datetime.utcnow().strftime("%Y-%m-%d-%H")

        # Check per-minute limit
        minute_key = get_rate_limit_key(tenant_id, f"minute:{current_minute}")
        minute_count = redis_client.get(minute_key)
        if minute_count and int(minute_count) >= rate_limit_per_minute:
            return False

        # Check per-hour limit
        hour_key = get_rate_limit_key(tenant_id, f"hour:{current_hour}")
        hour_count = redis_client.get(hour_key)
        if hour_count and int(hour_count) >= rate_limit_per_hour:
            return False

        # Increment counters
        redis_client.incr(minute_key)
        redis_client.incr(hour_key)

        # Set expiration for keys
        redis_client.expire(minute_key, 60)  # 1 minute
        redis_client.expire(hour_key, 3600)  # 1 hour

        return True
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        return True  # Allow request on error

# ===============================================
# AUTHENTICATION ENDPOINTS
# ===============================================

@app.post("/v1/auth/validate", response_model=AuthValidationResponse)
async def validate_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Validate API key and return tenant information"""
    try:
        # Extract API key from Authorization header
        auth_header = credentials.credentials
        if not auth_header:
            raise HTTPException(status_code=401, detail="Missing API key")

        # Hash the API key for lookup
        api_key_hash = hash_api_key(auth_header)

        # Validate API key
        tenant_info = db_manager.validate_api_key(api_key_hash)
        if not tenant_info:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Check rate limits
        if not check_rate_limit(
            tenant_info['tenant_id'],
            tenant_info['rate_limit_per_minute'],
            tenant_info['rate_limit_per_hour']
        ):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        # Update last used timestamp
        session = db_manager.get_session()
        session.execute("""
            UPDATE system.api_keys
            SET last_used_at = CURRENT_TIMESTAMP
            WHERE api_key_hash = %s
        """, (api_key_hash,))
        session.commit()
        session.close()

        return AuthValidationResponse(
            tenant_id=tenant_info['tenant_id'],
            tenant_name=tenant_info['tenant_name'],
            is_active=tenant_info['is_active'],
            rate_limit_per_minute=tenant_info['rate_limit_per_minute'],
            rate_limit_per_hour=tenant_info['rate_limit_per_hour'],
            api_key_name="API Key"  # Would be populated from actual key record
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key validation failed: {e}")
        raise HTTPException(status_code=500, detail="Authentication service error")

# ===============================================
# TENANT MANAGEMENT ENDPOINTS
# ===============================================

@app.post("/v1/tenants", response_model=TenantResponse)
async def create_tenant(request: TenantCreateRequest):
    """Create a new tenant (admin only - would require authentication)"""
    try:
        session = db_manager.get_session()

        # Check if tenant name already exists
        existing = session.execute("""
            SELECT tenant_id FROM system.tenants
            WHERE tenant_name = %s
        """, (request.tenant_name,)).fetchone()

        if existing:
            raise HTTPException(status_code=409, detail="Tenant name already exists")

        # Create tenant in database
        tenant_id = str(UUID.uuid4())
        session.execute("""
            INSERT INTO system.tenants (
                tenant_id, tenant_name, tenant_domain, contact_email,
                contact_phone, subscription_plan, is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, true)
        """, (
            tenant_id,
            request.tenant_name,
            request.tenant_domain,
            request.contact_email,
            request.contact_phone,
            request.subscription_plan
        ))

        # Create tenant schema
        if not db_manager.create_tenant_schema(tenant_id, request.tenant_name):
            raise HTTPException(status_code=500, detail="Failed to create tenant schema")

        session.commit()

        # Get created tenant
        result = session.execute("""
            SELECT tenant_id, tenant_name, tenant_domain, contact_email,
                   contact_phone, subscription_plan, is_active, created_at, updated_at
            FROM system.tenants WHERE tenant_id = %s
        """, (tenant_id,)).fetchone()

        session.close()

        return TenantResponse(
            tenant_id=result[0],
            tenant_name=result[1],
            tenant_domain=result[2],
            contact_email=result[3],
            contact_phone=result[4],
            subscription_plan=result[5],
            is_active=result[6],
            created_at=str(result[7]),
            updated_at=str(result[8])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create tenant: {e}")
        raise HTTPException(status_code=500, detail="Failed to create tenant")

@app.get("/v1/tenants", response_model=list[TenantResponse])
async def list_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """List tenants (admin only)"""
    try:
        session = db_manager.get_session()

        results = session.execute("""
            SELECT tenant_id, tenant_name, tenant_domain, contact_email,
                   contact_phone, subscription_plan, is_active, created_at, updated_at
            FROM system.tenants
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (limit, skip)).fetchall()

        session.close()

        return [
            TenantResponse(
                tenant_id=row[0],
                tenant_name=row[1],
                tenant_domain=row[2],
                contact_email=row[3],
                contact_phone=row[4],
                subscription_plan=row[5],
                is_active=row[6],
                created_at=str(row[7]),
                updated_at=str(row[8])
            )
            for row in results
        ]

    except Exception as e:
        logger.error(f"Failed to list tenants: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tenants")

@app.get("/v1/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str):
    """Get tenant by ID"""
    try:
        session = db_manager.get_session()

        result = session.execute("""
            SELECT tenant_id, tenant_name, tenant_domain, contact_email,
                   contact_phone, subscription_plan, is_active, created_at, updated_at
            FROM system.tenants WHERE tenant_id = %s
        """, (tenant_id,)).fetchone()

        session.close()

        if not result:
            raise HTTPException(status_code=404, detail="Tenant not found")

        return TenantResponse(
            tenant_id=result[0],
            tenant_name=result[1],
            tenant_domain=result[2],
            contact_email=result[3],
            contact_phone=result[4],
            subscription_plan=result[5],
            is_active=result[6],
            created_at=str(result[7]),
            updated_at=str(result[8])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tenant: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tenant")

# ===============================================
# API KEY MANAGEMENT ENDPOINTS
# ===============================================

@app.post("/v1/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    request: APIKeyCreateRequest,
    tenant_id: str = Query(..., description="Tenant ID")
):
    """Create a new API key for a tenant"""
    try:
        session = db_manager.get_session()

        # Verify tenant exists
        tenant = session.execute("""
            SELECT tenant_name FROM system.tenants
            WHERE tenant_id = %s AND is_active = true
        """, (tenant_id,)).fetchone()

        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found or inactive")

        # Generate API key
        api_key = generate_api_key()
        api_key_hash = hash_api_key(api_key)

        # Create API key record
        api_key_id = str(UUID.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=AUTH_CONFIG['token_expiry_days'])

        session.execute("""
            INSERT INTO system.api_keys (
                api_key_id, tenant_id, api_key_hash, api_key_name,
                rate_limit_per_minute, rate_limit_per_hour, expires_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            api_key_id,
            tenant_id,
            api_key_hash,
            request.api_key_name,
            request.rate_limit_per_minute,
            request.rate_limit_per_hour,
            expires_at
        ))

        session.commit()

        # Get created API key
        result = session.execute("""
            SELECT api_key_id, tenant_id, api_key_name, is_active,
                   rate_limit_per_minute, rate_limit_per_hour, created_at,
                   last_used_at, expires_at
            FROM system.api_keys WHERE api_key_id = %s
        """, (api_key_id,)).fetchone()

        session.close()

        return APIKeyResponse(
            api_key_id=result[0],
            tenant_id=result[1],
            api_key_name=result[2],
            is_active=result[3],
            rate_limit_per_minute=result[4],
            rate_limit_per_hour=result[5],
            created_at=str(result[6]),
            last_used_at=str(result[7]) if result[7] else None,
            expires_at=str(result[8]) if result[8] else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to create API key")

@app.get("/v1/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    tenant_id: str = Query(..., description="Tenant ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """List API keys for a tenant"""
    try:
        session = db_manager.get_session()

        results = session.execute("""
            SELECT api_key_id, tenant_id, api_key_name, is_active,
                   rate_limit_per_minute, rate_limit_per_hour, created_at,
                   last_used_at, expires_at
            FROM system.api_keys
            WHERE tenant_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (tenant_id, limit, skip)).fetchall()

        session.close()

        return [
            APIKeyResponse(
                api_key_id=row[0],
                tenant_id=row[1],
                api_key_name=row[2],
                is_active=row[3],
                rate_limit_per_minute=row[4],
                rate_limit_per_hour=row[5],
                created_at=str(row[6]),
                last_used_at=str(row[7]) if row[7] else None,
                expires_at=str(row[8]) if row[8] else None
            )
            for row in results
        ]

    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to list API keys")

# ===============================================
# HEALTH CHECK ENDPOINT
# ===============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        session = db_manager.get_session()
        session.execute("SELECT 1").fetchone()
        session.close()

        # Test Redis connection
        redis_client.ping()

        return {
            "status": "healthy",
            "service": "auth-service",
            "database": "connected",
            "redis": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

# ===============================================
# LIFECYCLE MANAGEMENT
# ===============================================

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    global db_manager, redis_client

    try:
        logger.info("Starting Auth Service...")

        # Initialize database connection
        db_manager = DatabaseManager(DATABASE_CONFIG['url'])
        if not db_manager.connect():
            raise Exception("Failed to connect to database")

        # Initialize Redis client
        redis_client = redis.Redis.from_url(REDIS_CONFIG['url'], decode_responses=True)

        # Test Redis connection
        redis_client.ping()

        logger.info("Auth Service started successfully")

    except Exception as e:
        logger.error(f"Failed to start Auth Service: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global db_manager

    try:
        if db_manager:
            db_manager.disconnect()
        logger.info("Auth Service shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# ===============================================
# MAIN ENTRY POINT
# ===============================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8001")),
        reload=API_CONFIG['debug_mode']
    )