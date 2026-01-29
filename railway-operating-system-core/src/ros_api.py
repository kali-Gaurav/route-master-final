from fastapi import FastAPI, Query, Header, HTTPException, Depends, Response
from typing import Optional
from pydantic import BaseModel
import time

# Import from consolidated modules
from security_system import APIKeyManager
from database_system import DatabasePool, DatabaseConfig
from infrastructure import JobManager, RouteCache
from route_engine import RouteEngine, route_engine
from monitoring import MetricsCollector, rate_limit_check
from route_service import create_route_service_router

app = FastAPI(
    title='Railway OS API',
    description='Production-grade route finding and scheduling API',
    version='1.0.0'
)

# Initialize core services
db_config = DatabaseConfig()
metrics = MetricsCollector()
job_manager = JobManager(db_config)
route_cache = RouteCache()

# Get API key manager (needs to use proper database connection)
try:
    # For now, we'll initialize without APIKeyManager
    api_key_manager = None
except Exception as e:
    print(f"Warning: Could not initialize API key manager: {e}")
    api_key_manager = None

# Mount route service endpoints
router = create_route_service_router(api_key_manager)
app.include_router(router)


# ============================================================================
# AUTH MIDDLEWARE
# ============================================================================

async def get_tenant_from_api_key(authorization: Optional[str] = Header(None)):
    """Extract tenant_id from API key in Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    try:
        # Support both "Bearer token" and "X-API-Key: token" formats
        if authorization.startswith("Bearer "):
            api_key = authorization[7:]
        else:
            api_key = authorization
        
        key_record = api_key_manager.validate_api_key(api_key)
        if not key_record:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        return key_record
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


# ============================================================================
# JOBS API ENDPOINTS (Task 22)
# ============================================================================

class JobRequest(BaseModel):
    operation: str
    origin: str
    destination: str
    date_start: Optional[str] = None
    date_end: Optional[str] = None


@app.post('/v1/jobs')
async def enqueue_job_endpoint(
    request: JobRequest,
    key_record: dict = Depends(get_tenant_from_api_key)
):
    """Enqueue an async job"""
    tenant_id = key_record["tenant_id"]
    
    try:
        job_id = job_manager.enqueue(
            tenant_id=tenant_id,
            operation=request.operation,
            payload={
                "origin": request.origin,
                "destination": request.destination,
                "date_start": request.date_start,
                "date_end": request.date_end,
            }
        )
        
        metrics.track_request("api.enqueue_job", tenant_id, True)
        return {
            "job_id": job_id,
            "status": "queued",
            "created_at": time.time()
        }
    
    except Exception as e:
        metrics.track_error("api.enqueue_job", tenant_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/v1/jobs/{job_id}')
async def get_job_status(
    job_id: str,
    key_record: dict = Depends(get_tenant_from_api_key)
):
    """Get job status"""
    tenant_id = key_record["tenant_id"]
    
    try:
        job = job_manager.get(job_id, tenant_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "job_id": job["id"],
            "tenant_id": job["tenant_id"],
            "status": job["status"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "result": job.get("result"),
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/v1/jobs/{job_id}/logs')
async def get_job_logs(
    job_id: str,
    key_record: dict = Depends(get_tenant_from_api_key)
):
    """Get job execution logs"""
    tenant_id = key_record["tenant_id"]
    
    try:
        logs = job_manager.get_logs(job_id, tenant_id)
        if logs is None:
            raise HTTPException(status_code=404, detail="Job logs not found")
        
        return {
            "job_id": job_id,
            "logs": logs
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# METRICS ENDPOINTS (Task 28)
# ============================================================================

@app.get('/v1/metrics')
async def get_metrics(
    key_record: dict = Depends(get_tenant_from_api_key)
):
    """Get API metrics for tenant"""
    tenant_id = key_record["tenant_id"]
    
    metrics_data = metrics.get_metrics()
    
    return {
        "tenant_id": tenant_id,
        "total_requests": metrics_data.get("total_requests", 0),
        "total_errors": metrics_data.get("total_errors", 0),
        "avg_latency_ms": metrics_data.get("avg_latency_ms", 0),
        "p95_latency_ms": metrics_data.get("p95_latency_ms", 0),
        "p99_latency_ms": metrics_data.get("p99_latency_ms", 0),
        "cache_hit_rate": metrics_data.get("cache_hit_rate", 0),
        "current_rate_limit": metrics_data.get("rate_limit_rps", 100),
        "rate_limited_requests": metrics_data.get("rate_limited_count", 0),
    }


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get('/health')
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }


@app.get('/ready')
async def readiness_check():
    """Readiness check (all dependencies online)"""
    try:
        # Check database connectivity
        db_pool.get_connection()
        
        # Check route engine initialized
        stats = route_engine.get_route_statistics()
        
        return {
            "ready": True,
            "database": "connected",
            "route_engine": "initialized",
            "dataset_version": stats.get("version", "unknown")
        }
    
    except Exception as e:
        return {
            "ready": False,
            "error": str(e)
        }, 503


# ============================================================================
# LEGACY ROUTE ENDPOINT (Task 14 - API key validation)
# ============================================================================

class LegacyRouteRequest(BaseModel):
    source: str
    dest: str
    date: Optional[str] = None
    max_transfers: Optional[int] = 3


@app.post('/routes')
async def find_routes_legacy(
    req: LegacyRouteRequest,
    key_record: dict = Depends(get_tenant_from_api_key)
):
    """Legacy route endpoint (for backward compatibility)"""
    tenant_id = key_record["tenant_id"]
    
    try:
        routes = route_engine.find_routes(
            origin=req.source,
            destination=req.dest,
            date=req.date,
            max_transfers=req.max_transfers
        )
        
        metrics.track_request("api.find_routes_legacy", tenant_id, False)
        
        return {
            "source": req.source,
            "destination": req.dest,
            "routes": routes,
            "count": len(routes)
        }
    
    except Exception as e:
        metrics.track_error("api.find_routes_legacy", tenant_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# API ROOT
# ============================================================================

@app.get('/')
async def root():
    """API root with documentation links"""
    return {
        "name": "Railway Operating System API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "routes": {
                "search": "POST /v1/routes/search",
                "direct": "POST /v1/routes/direct",
                "batch": "POST /v1/routes/batch",
                "stats": "GET /v1/routes/stats",
            },
            "jobs": {
                "enqueue": "POST /v1/jobs",
                "status": "GET /v1/jobs/{job_id}",
                "logs": "GET /v1/jobs/{job_id}/logs",
            },
            "monitoring": {
                "metrics": "GET /v1/metrics",
                "health": "GET /health",
                "ready": "GET /ready",
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
