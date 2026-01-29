# ===============================================
# ROUTE SERVICE
# ===============================================
# Microservice handling route finding operations
# Uses the isolated RouteFinderEngine for calculations

import os
import sys
import logging
import httpx
from typing import Dict, Any, Optional
from datetime import date
from uuid import UUID

# Add shared module to path
# Add project root to path to enable shared module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import uvicorn
import redis
import json

from shared.route_finder_engine import RouteFinderEngine
from shared.config import (
    API_CONFIG, REDIS_CONFIG, ROUTE_CONFIG,
    get_cors_origins, get_service_url
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, API_CONFIG['log_level']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Railway OS Route Service",
    description="Route finding and optimization service",
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

# Global components
route_engine = RouteFinderEngine()
redis_client = None
http_client = None

# ===============================================
# DATA MODELS
# ===============================================

class RouteSearchRequest(BaseModel):
    source: str
    destination: str
    date: date
    max_transfers: Optional[int] = ROUTE_CONFIG['max_transfers']

    @validator('source', 'destination')
    def validate_station_code(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Station code cannot be empty')
        return v.strip().upper()

    @validator('max_transfers')
    def validate_max_transfers(cls, v):
        if v < 0 or v > 3:
            raise ValueError('max_transfers must be between 0 and 3')
        return v

class RouteSearchResponse(BaseModel):
    source: str
    destination: str
    date: str
    direct_routes: list
    transfer_routes: list
    total_routes: int
    search_completed: bool
    error: Optional[str]

class TenantContext(BaseModel):
    tenant_id: str
    tenant_name: str

# ===============================================
# DEPENDENCY INJECTION
# ===============================================

def get_tenant_context(tenant_id: str = Query(..., description="Tenant ID")) -> TenantContext:
    """Get tenant context from request"""
    # In a real implementation, this would validate the tenant
    # For now, we'll accept any tenant_id
    return TenantContext(
        tenant_id=tenant_id,
        tenant_name=f"Tenant {tenant_id}"
    )

# ===============================================
# CACHE MANAGEMENT
# ===============================================

def get_cache_key(tenant_id: str, source: str, destination: str, date: date, max_transfers: int) -> str:
    """Generate cache key for route search"""
    return f"route:{tenant_id}:{source}:{destination}:{date.isoformat()}:{max_transfers}"

def get_cached_result(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get cached route search result"""
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        return None
    except Exception as e:
        logger.error(f"Cache read error: {e}")
        return None

def set_cached_result(cache_key: str, result: Dict[str, Any], ttl: int = ROUTE_CONFIG['cache_ttl']):
    """Cache route search result"""
    try:
        redis_client.setex(cache_key, ttl, json.dumps(result))
    except Exception as e:
        logger.error(f"Cache write error: {e}")

# ===============================================
# DATA SERVICE CLIENT
# ===============================================

async def get_route_data_from_data_service(tenant_id: str, source: str, destination: str, search_date: date) -> Dict[str, Any]:
    """Fetch route data from data service"""
    try:
        data_service_url = get_service_url('data_service')
        url = f"{data_service_url}/v1/route-data"

        async with http_client as client:
            response = await client.get(
                url,
                params={
                    'tenant_id': tenant_id,
                    'source': source,
                    'destination': destination,
                    'date': search_date.isoformat()
                }
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error fetching route data: {e}")
        raise HTTPException(status_code=503, detail="Data service unavailable")

# ===============================================
# ROUTE SEARCH ENDPOINTS
# ===============================================

@app.post("/v1/routes/search", response_model=RouteSearchResponse)
async def search_routes(
    request: RouteSearchRequest,
    tenant: TenantContext = Depends(get_tenant_context)
):
    """Search for routes between two stations"""
    try:
        # Check cache first
        cache_key = get_cache_key(
            tenant.tenant_id,
            request.source,
            request.destination,
            request.date,
            request.max_transfers
        )

        cached_result = get_cached_result(cache_key)
        if cached_result:
            logger.info(f"Cache hit for route search: {cache_key}")
            return RouteSearchResponse(**cached_result)

        # Fetch data from data service
        route_data = await get_route_data_from_data_service(
            tenant.tenant_id,
            request.source,
            request.destination,
            request.date
        )

        # Prepare data for route engine
        stations_data = route_data['stations']
        train_schedule_data = route_data['train_schedule']

        # Convert running days to dict format
        train_running_days = {}
        for rd in route_data['train_running_days']:
            train_running_days[rd['train_no']] = {
                'mon': rd['mon'],
                'tue': rd['tue'],
                'wed': rd['wed'],
                'thu': rd['thu'],
                'fri': rd['fri'],
                'sat': rd['sat'],
                'sun': rd['sun']
            }

        # Perform route search
        result = route_engine.find_routes(
            source=request.source,
            destination=request.destination,
            date=request.date,
            train_schedule_data=train_schedule_data,
            train_running_days=train_running_days,
            stations_data=stations_data,
            max_transfers=request.max_transfers
        )

        # Cache the result
        set_cached_result(cache_key, result)

        return RouteSearchResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in route search: {e}")
        return RouteSearchResponse(
            source=request.source,
            destination=request.destination,
            date=request.date.isoformat(),
            direct_routes=[],
            transfer_routes=[],
            total_routes=0,
            search_completed=False,
            error=str(e)
        )

@app.post("/v1/routes/search-async")
async def search_routes_async(
    request: RouteSearchRequest,
    background_tasks: BackgroundTasks,
    tenant: TenantContext = Depends(get_tenant_context)
):
    """Asynchronous route search - returns job ID"""
    try:
        # Generate job ID
        job_id = str(UUID.uuid4())

        # Store job request in Redis for worker processing
        job_data = {
            'job_id': job_id,
            'tenant_id': tenant.tenant_id,
            'request': request.dict(),
            'status': 'queued',
            'created_at': str(date.today())
        }

        redis_client.setex(f"job:{job_id}", 3600, json.dumps(job_data))  # 1 hour TTL

        # Add to job queue
        redis_client.lpush('route_jobs', job_id)

        return {
            'job_id': job_id,
            'status': 'queued',
            'message': 'Route search job queued for processing'
        }

    except Exception as e:
        logger.error(f"Error queuing async route search: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue job")

@app.get("/v1/routes/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of asynchronous route search job"""
    try:
        # Check if job exists
        job_data_raw = redis_client.get(f"job:{job_id}")
        if not job_data_raw:
            raise HTTPException(status_code=404, detail="Job not found")

        job_data = json.loads(job_data_raw)

        # Check if result is available
        result_raw = redis_client.get(f"job_result:{job_id}")
        if result_raw:
            result = json.loads(result_raw)
            return {
                'job_id': job_id,
                'status': 'completed',
                'result': result
            }

        return {
            'job_id': job_id,
            'status': job_data.get('status', 'processing'),
            'message': 'Job is being processed'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ===============================================
# CACHE MANAGEMENT ENDPOINTS
# ===============================================

@app.post("/v1/cache/clear")
async def clear_route_cache(
    tenant: TenantContext = Depends(get_tenant_context),
    pattern: Optional[str] = Query(None, description="Cache key pattern to clear")
):
    """Clear route search cache"""
    try:
        if pattern:
            # Clear specific pattern (simplified implementation)
            keys_to_delete = redis_client.keys(f"route:{tenant.tenant_id}:{pattern}*")
            if keys_to_delete:
                redis_client.delete(*keys_to_delete)
                return {"message": f"Cleared {len(keys_to_delete)} cache entries"}
            else:
                return {"message": "No cache entries found matching pattern"}
        else:
            # Clear all tenant cache
            keys_to_delete = redis_client.keys(f"route:{tenant.tenant_id}:*")
            if keys_to_delete:
                redis_client.delete(*keys_to_delete)
                return {"message": f"Cleared {len(keys_to_delete)} cache entries"}
            else:
                return {"message": "No cache entries to clear"}

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

# ===============================================
# HEALTH CHECK ENDPOINT
# ===============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connection
        redis_client.ping()

        # Test data service connection
        data_service_url = get_service_url('data_service')
        async with http_client as client:
            response = await client.get(f"{data_service_url}/health")
            response.raise_for_status()

        return {
            "status": "healthy",
            "service": "route-service",
            "redis": "connected",
            "data_service": "connected"
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
    global redis_client, http_client

    try:
        logger.info("Starting Route Service...")

        # Initialize Redis client
        redis_client = redis.Redis.from_url(REDIS_CONFIG['url'], decode_responses=True)

        # Test Redis connection
        redis_client.ping()

        # Initialize HTTP client
        http_client = httpx.AsyncClient(timeout=30.0)

        logger.info("Route Service started successfully")

    except Exception as e:
        logger.error(f"Failed to start Route Service: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global http_client

    try:
        if http_client:
            await http_client.aclose()
        logger.info("Route Service shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# ===============================================
# MAIN ENTRY POINT
# ===============================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8002")),
        reload=API_CONFIG['debug_mode']
    )