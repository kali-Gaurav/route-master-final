# api/dependencies.py
from fastapi import Request
from typing import Optional
from uuid import UUID

def get_tenant_from_api_key(request: Request) -> Optional[UUID]:
    """Extract tenant ID from API key in header"""
    api_key = request.headers.get("X-API-Key")
    if api_key:
        # Here you would validate the API key and return tenant_id
        # For now, return None - implement proper validation
        pass
    return None

def get_tenant_from_subdomain(request: Request) -> Optional[UUID]:
    """Extract tenant ID from subdomain"""
    host = request.headers.get("host", "")
    if "." in host:
        subdomain = host.split(".")[0]
        # Here you would map subdomain to tenant_id
        # For now, return None - implement proper mapping
        pass
    return None