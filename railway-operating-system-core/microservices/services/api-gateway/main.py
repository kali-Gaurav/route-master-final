# ===============================================
# API GATEWAY
# ===============================================
# Single entry point for all client requests
# Handles authentication, rate limiting, and request routing

import os
import sys
import logging
import time
from typing import Dict, Any, Optional

# Add project root to path to enable shared module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import FastAPI, Request, Response, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import httpx
import redis

from shared.config import (
    API_CONFIG, REDIS_CONFIG,
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
    title="Railway OS API Gateway",
    description="API Gateway for Railway Operating System",
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
redis_client = None
http_client = None

# Service routes mapping
SERVICE_ROUTES = {
    # Auth service routes
    "/v1/auth": "auth-service",
    "/v1/tenants": "auth-service",
    "/v1/api-keys": "auth-service",

    # Route service routes
    "/v1/routes": "route-service",

    # Data service routes (internal only - not exposed to clients)
    # "/v1/stations": "data-service",
    # "/v1/trains": "data-service",
}

# ===============================================
# AUTHENTICATION MIDDLEWARE
# ===============================================

async def authenticate_request(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Authenticate request using API key"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        # Extract API key
        if authorization.startswith("Bearer "):
            api_key = authorization[7:]
        else:
            api_key = authorization

        # Call auth service to validate
        auth_service_url = get_service_url('auth_service')
        url = f"{auth_service_url}/v1/auth/validate"

        async with http_client as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {api_key}"}
            )

            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid API key")
            elif response.status_code == 429:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            elif response.status_code != 200:
                raise HTTPException(status_code=500, detail="Authentication service error")

            return response.json()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=500, detail="Authentication service unavailable")

# ===============================================
# ROUTING LOGIC
# ===============================================

def get_target_service(path: str) -> Optional[str]:
    """Determine which service should handle the request"""
    for route_prefix, service in SERVICE_ROUTES.items():
        if path.startswith(route_prefix):
            return service
    return None

def build_target_url(service: str, path: str, query_params: str = "") -> str:
    """Build the target URL for the downstream service"""
    service_url = get_service_url(service)
    target_path = path  # Keep the full path

    url = f"{service_url}{target_path}"
    if query_params:
        url += f"?{query_params}"

    return url

# ===============================================
# REQUEST PROXYING
# ===============================================

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_request(
    request: Request,
    path: str,
    auth_info: Dict[str, Any] = Depends(authenticate_request)
):
    """Proxy requests to appropriate downstream services"""
    try:
        start_time = time.time()

        # Determine target service
        target_service = get_target_service(f"/{path}")
        if not target_service:
            raise HTTPException(status_code=404, detail="Endpoint not found")

        # Build target URL
        query_string = str(request.url.query)
        target_url = build_target_url(target_service, f"/{path}", query_string)

        # Prepare headers (exclude host and authorization)
        headers = dict(request.headers)
        headers.pop("host", None)
        headers.pop("authorization", None)

        # Add tenant context
        headers["X-Tenant-ID"] = auth_info["tenant_id"]
        headers["X-Tenant-Name"] = auth_info["tenant_name"]

        # Get request body
        body = await request.body()

        # Forward request to downstream service
        async with http_client as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                timeout=30.0
            )

            # Log request
            duration = time.time() - start_time
            logger.info(
                f"Request: {request.method} /{path} -> {target_service} "
                f"({response.status_code}) {duration:.3f}s"
            )

            # Return response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Request proxying failed: {e}")
        raise HTTPException(status_code=500, detail="Gateway error")

# ===============================================
# HEALTH CHECK ENDPOINT
# ===============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connection
        redis_client.ping()

        # Test downstream services
        services_status = {}
        services_to_check = ['auth-service', 'route-service', 'data-service']

        for service in services_to_check:
            try:
                service_url = get_service_url(service)
                async with http_client as client:
                    response = await client.get(f"{service_url}/health", timeout=5.0)
                    services_status[service] = response.status_code == 200
            except Exception:
                services_status[service] = False

        all_healthy = all(services_status.values())

        return {
            "status": "healthy" if all_healthy else "degraded",
            "service": "api-gateway",
            "redis": "connected",
            "services": services_status
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

# ===============================================
# PUBLIC ENDPOINTS (No authentication required)
# ===============================================

@app.get("/")
async def root():
    """API Gateway root endpoint"""
    return {
        "name": "Railway Operating System API Gateway",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/status")
async def system_status():
    """Public system status endpoint"""
    try:
        # Get health status of all services
        services_status = {}
        services_to_check = ['auth-service', 'route-service', 'data-service']

        for service in services_to_check:
            try:
                service_url = get_service_url(service)
                async with http_client as client:
                    response = await client.get(f"{service_url}/health", timeout=5.0)
                    services_status[service] = {
                        "status": "healthy" if response.status_code == 200 else "unhealthy",
                        "response_time": response.elapsed.total_seconds()
                    }
            except Exception as e:
                services_status[service] = {
                    "status": "unreachable",
                    "response_time": None
                }

        return {
            "system": "Railway Operating System",
            "status": "operational",
            "timestamp": str(time.time()),
            "services": services_status
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "system": "Railway Operating System",
            "status": "error",
            "timestamp": str(time.time()),
            "error": "Unable to check service status"
        }

# ===============================================
# LIFECYCLE MANAGEMENT
# ===============================================

@app.on_event("startup")
async def startup_event():
    """Initialize gateway on startup"""
    global redis_client, http_client

    try:
        logger.info("Starting API Gateway...")

        # Initialize Redis client
        redis_client = redis.Redis.from_url(REDIS_CONFIG['url'], decode_responses=True)

        # Test Redis connection
        redis_client.ping()

        # Initialize HTTP client
        http_client = httpx.AsyncClient(timeout=30.0)

        logger.info("API Gateway started successfully")

    except Exception as e:
        logger.error(f"Failed to start API Gateway: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global http_client

    try:
        if http_client:
            await http_client.aclose()
        logger.info("API Gateway shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# ===============================================
# MAIN ENTRY POINT
# ===============================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=API_CONFIG['debug_mode']
    )