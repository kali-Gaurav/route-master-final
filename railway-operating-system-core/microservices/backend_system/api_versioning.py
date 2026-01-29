"""
API Gateway and Versioning System
Implements API versioning (/v1, /v2), rate limiting, and backward compatibility
"""

from fastapi import FastAPI, APIRouter, Header, HTTPException, status, Request, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class APIVersion(str, Enum):
    """Supported API versions"""
    V1 = "v1"
    V2 = "v2"


class VersionedAPIRouter(APIRouter):
    """Router that handles API versioning"""
    
    def __init__(self, version: APIVersion, *args, **kwargs):
        self.version = version
        super().__init__(*args, prefix=f"/api/{version}", tags=[f"{version.upper()}"], **kwargs)


class APIVersioningPolicy:
    """
    API versioning and backward compatibility management
    
    Rules:
    - v1: NEVER changed (backward compatible forever)
    - v2: New features, breaking changes OK if needed
    - Deprecation: 90 days warning → 180 days total lifecycle
    """
    
    # Deprecation schedule (days from release)
    DEPRECATION_WARNING_DAYS = 90
    DEPRECATION_SUNSET_DAYS = 180
    
    # Version lifecycle tracking
    VERSION_TIMELINE = {
        'v1': {
            'release_date': '2025-06-01',
            'status': 'stable',
            'sunset_date': None,  # Never sunset v1
            'policy': 'backward_compatible_forever'
        },
        'v2': {
            'release_date': '2026-01-01',
            'status': 'stable',
            'deprecation_warning_date': None,
            'sunset_date': None,
            'policy': 'breaking_changes_allowed'
        },
        'v3': {
            'release_date': '2026-02-01',  # Coming soon
            'status': 'beta',
            'policy': 'experimental'
        }
    }
    
    # Endpoint backward compatibility matrix
    COMPATIBILITY_MATRIX = {
        '/analytics/metrics': {
            'v1': {
                'deprecated': False,
                'response_fields': ['metric_id', 'metric_name', 'metric_value', 'created_at'],
                'breaking_changes': None
            },
            'v2': {
                'deprecated': False,
                'response_fields': ['metric_id', 'metric_name', 'metric_value', 'created_at', 'tenant_id'],
                'breaking_changes': 'Added tenant_id field (backward compatible)'
            }
        },
        '/analytics/query': {
            'v1': {
                'deprecated': False,
                'request_fields': ['query', 'limit', 'offset'],
                'response_fields': ['results', 'total_count']
            },
            'v2': {
                'deprecated': False,
                'request_fields': ['query', 'limit', 'offset', 'filter', 'sort'],
                'response_fields': ['results', 'total_count', 'has_more']
            }
        }
    }
    
    @classmethod
    def get_version_status(cls, version: str) -> dict:
        """Get version lifecycle status"""
        timeline = cls.VERSION_TIMELINE.get(version, {})
        
        return {
            'version': version,
            'release_date': timeline.get('release_date'),
            'status': timeline.get('status'),
            'policy': timeline.get('policy'),
            'sunset_date': timeline.get('sunset_date'),
            'is_stable': timeline.get('status') == 'stable',
            'is_deprecated': timeline.get('status') == 'deprecated'
        }
    
    @classmethod
    def validate_compatibility(cls, version: str, endpoint: str) -> dict:
        """Validate endpoint compatibility with version"""
        
        if endpoint not in cls.COMPATIBILITY_MATRIX:
            return {'compatible': True, 'warnings': []}
        
        compatibility = cls.COMPATIBILITY_MATRIX[endpoint].get(version, {})
        
        return {
            'compatible': True,
            'version': version,
            'endpoint': endpoint,
            'deprecated': compatibility.get('deprecated', False),
            'breaking_changes': compatibility.get('breaking_changes'),
            'response_fields': compatibility.get('response_fields', []),
            'request_fields': compatibility.get('request_fields', [])
        }


class RateLimiter:
    """Rate limiting by tenant and user"""
    
    # Rate limiting tiers
    RATE_LIMITS = {
        'free': {
            'requests_per_minute': 60,
            'requests_per_hour': 1000,
            'burst_size': 10
        },
        'pro': {
            'requests_per_minute': 300,
            'requests_per_hour': 10000,
            'burst_size': 50
        },
        'enterprise': {
            'requests_per_minute': 1000,
            'requests_per_hour': 100000,
            'burst_size': 200
        }
    }
    
    def __init__(self):
        self.request_history = {}  # In production: use Redis
    
    def check_rate_limit(self, tenant_id: str, user_id: str, tier: str = 'free') -> dict:
        """
        Check if request should be allowed
        
        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            tier: Rate limit tier
        
        Returns:
            Dict with rate limit status and headers
        """
        limit_config = self.RATE_LIMITS.get(tier, self.RATE_LIMITS['free'])
        key = f"{tenant_id}:{user_id}"
        
        # Get request count (in production: from Redis)
        now = datetime.utcnow()
        current_count = self._get_request_count(key, now)
        
        allowed = current_count < limit_config['requests_per_minute']
        
        return {
            'allowed': allowed,
            'limit': limit_config['requests_per_minute'],
            'remaining': max(0, limit_config['requests_per_minute'] - current_count),
            'reset_at': (now + timedelta(minutes=1)).isoformat(),
            'tier': tier
        }
    
    def _get_request_count(self, key: str, now: datetime) -> int:
        """Get request count for key in current minute"""
        # In production: use Redis with EXPIRE
        # For now: simple in-memory tracking
        if key not in self.request_history:
            self.request_history[key] = []
        
        # Remove old entries
        cutoff = now - timedelta(minutes=1)
        self.request_history[key] = [t for t in self.request_history[key] if t > cutoff]
        
        # Add current request
        self.request_history[key].append(now)
        
        return len(self.request_history[key])


class ErrorResponseStandardization:
    """Standardized error response format across all API versions"""
    
    # Standard error codes
    ERROR_CODES = {
        'INVALID_REQUEST': {
            'status': 400,
            'description': 'Invalid request parameters'
        },
        'UNAUTHORIZED': {
            'status': 401,
            'description': 'Authentication required or failed'
        },
        'FORBIDDEN': {
            'status': 403,
            'description': 'Access denied'
        },
        'NOT_FOUND': {
            'status': 404,
            'description': 'Resource not found'
        },
        'CONFLICT': {
            'status': 409,
            'description': 'Resource conflict'
        },
        'RATE_LIMITED': {
            'status': 429,
            'description': 'Too many requests'
        },
        'INTERNAL_ERROR': {
            'status': 500,
            'description': 'Internal server error'
        },
        'SERVICE_UNAVAILABLE': {
            'status': 503,
            'description': 'Service temporarily unavailable'
        }
    }
    
    @staticmethod
    def format_error(error_code: str, message: str, details: Dict = None) -> dict:
        """
        Format error response
        
        Returns:
            Standardized error dict
        """
        error_info = ErrorResponseStandardization.ERROR_CODES.get(
            error_code,
            ErrorResponseStandardization.ERROR_CODES['INTERNAL_ERROR']
        )
        
        return {
            'error': {
                'code': error_code,
                'message': message,
                'status': error_info['status'],
                'timestamp': datetime.utcnow().isoformat(),
                'details': details or {},
                'request_id': None  # Will be set by middleware
            }
        }


class APIGateway:
    """API Gateway with versioning, rate limiting, and standardization"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.versioning_policy = APIVersioningPolicy()
        self.rate_limiter = RateLimiter()
        self.error_formatter = ErrorResponseStandardization()
        
        # Setup middleware
        self._setup_middleware()
    
    def _setup_middleware(self):
        """Setup API gateway middleware"""
        
        @self.app.middleware("http")
        async def api_gateway_middleware(request: Request, call_next):
            """Main API gateway middleware"""
            
            # Extract version from path
            path_parts = request.url.path.split('/')
            version = path_parts[2] if len(path_parts) > 2 else 'v1'
            
            # Check version is supported
            try:
                APIVersion(version)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content=self.error_formatter.format_error(
                        'INVALID_REQUEST',
                        f'API version {version} not supported'
                    )
                )
            
            # Add request headers for downstream services
            request.state.api_version = version
            request.state.request_id = request.headers.get('X-Request-ID', str(datetime.utcnow().timestamp()))
            
            # Check rate limiting
            tenant_id = request.headers.get('X-Tenant-ID', 'anonymous')
            user_id = request.headers.get('X-User-ID', 'anonymous')
            tier = request.headers.get('X-Rate-Limit-Tier', 'free')
            
            rate_limit = self.rate_limiter.check_rate_limit(tenant_id, user_id, tier)
            
            if not rate_limit['allowed']:
                return JSONResponse(
                    status_code=429,
                    content=self.error_formatter.format_error(
                        'RATE_LIMITED',
                        'Too many requests'
                    ),
                    headers={
                        'X-RateLimit-Limit': str(rate_limit['limit']),
                        'X-RateLimit-Remaining': str(rate_limit['remaining']),
                        'X-RateLimit-Reset': rate_limit['reset_at']
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers['X-RateLimit-Limit'] = str(rate_limit['limit'])
            response.headers['X-RateLimit-Remaining'] = str(rate_limit['remaining'])
            response.headers['X-RateLimit-Reset'] = rate_limit['reset_at']
            response.headers['X-Request-ID'] = request.state.request_id
            
            return response
    
    def add_version_routes(self, v1_router: APIRouter, v2_router: APIRouter = None):
        """Register versioned routes"""
        self.app.include_router(v1_router)
        if v2_router:
            self.app.include_router(v2_router)
    
    def get_version_info(self) -> dict:
        """Get API version information"""
        return {
            'supported_versions': [v.value for v in APIVersion],
            'versions': {
                version.value: self.versioning_policy.get_version_status(version.value)
                for version in APIVersion
            },
            'rate_limits': RateLimiter.RATE_LIMITS
        }
