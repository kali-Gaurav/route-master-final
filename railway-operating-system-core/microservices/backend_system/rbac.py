"""
Role-Based Access Control (RBAC) Implementation
Fine-grained authorization for API endpoints
"""

from fastapi import Depends, HTTPException, status
from typing import List, Optional, Callable
import logging
import jwt
from datetime import datetime

logger = logging.getLogger(__name__)


class Role:
    """User roles and permissions"""
    
    ADMIN = "admin"
    POWER_USER = "power_user"
    ANALYST = "analyst"
    VIEWER = "viewer"
    SYSTEM = "system"
    
    # Role permissions mapping
    PERMISSIONS = {
        ADMIN: [
            'analytics:read',
            'analytics:write',
            'analytics:delete',
            'analytics:export',
            'system:admin',
            'users:manage',
            'audit:read'
        ],
        POWER_USER: [
            'analytics:read',
            'analytics:write',
            'analytics:export',
            'reports:create',
            'audit:read'
        ],
        ANALYST: [
            'analytics:read',
            'reports:create',
        ],
        VIEWER: [
            'analytics:read',
        ],
        SYSTEM: [
            'service:internal',
            'system:metrics',
        ]
    }


class TokenPayload:
    """JWT token payload structure"""
    
    def __init__(self,
                 user_id: str,
                 tenant_id: str,
                 roles: List[str],
                 email: str,
                 exp: int,
                 iat: int):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.roles = roles
        self.email = email
        self.exp = exp
        self.iat = iat
    
    def is_valid(self) -> bool:
        """Check if token is not expired"""
        return datetime.utcnow().timestamp() < self.exp


class AuthorizationManager:
    """Manage authorization and access control"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def decode_token(self, token: str) -> Optional[TokenPayload]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            token_data = TokenPayload(
                user_id=payload.get('sub'),
                tenant_id=payload.get('tenant_id'),
                roles=payload.get('roles', []),
                email=payload.get('email'),
                exp=payload.get('exp'),
                iat=payload.get('iat')
            )
            
            if not token_data.is_valid():
                logger.warning(f"Expired token for user {token_data.user_id}")
                return None
            
            return token_data
        
        except jwt.DecodeError as e:
            logger.error(f"Token decode error: {e}")
            return None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None
    
    def has_permission(self, token: TokenPayload, required_permission: str) -> bool:
        """Check if user has required permission"""
        for role in token.roles:
            permissions = Role.PERMISSIONS.get(role, [])
            if required_permission in permissions:
                return True
        
        return False
    
    def has_role(self, token: TokenPayload, required_role: str) -> bool:
        """Check if user has required role"""
        return required_role in token.roles
    
    def has_tenant_access(self, token: TokenPayload, tenant_id: str) -> bool:
        """Check if user has access to tenant"""
        return token.tenant_id == tenant_id


class RBACDependencies:
    """FastAPI dependency injections for RBAC"""
    
    def __init__(self, auth_manager: AuthorizationManager):
        self.auth_manager = auth_manager
    
    async def get_current_user(self, authorization: str = None) -> TokenPayload:
        """Get current user from token"""
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header"
            )
        
        # Parse Bearer token
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid auth scheme")
        except (ValueError, IndexError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header"
            )
        
        # Decode token
        payload = self.auth_manager.decode_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        return payload
    
    def require_permission(self, *permissions: str):
        """Dependency for checking permissions"""
        async def check_permission(current_user = Depends(self.get_current_user)):
            for permission in permissions:
                if self.auth_manager.has_permission(current_user, permission):
                    return current_user
            
            logger.warning(
                f"User {current_user.user_id} denied access - missing permission: {permissions}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permissions}"
            )
        
        return check_permission
    
    def require_role(self, *roles: str):
        """Dependency for checking roles"""
        async def check_role(current_user = Depends(self.get_current_user)):
            for role in roles:
                if self.auth_manager.has_role(current_user, role):
                    return current_user
            
            logger.warning(
                f"User {current_user.user_id} denied access - missing role: {roles}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role: required one of {roles}"
            )
        
        return check_role
    
    def require_tenant_access(self, tenant_param: str = 'tenant_id'):
        """Dependency for tenant isolation"""
        async def check_tenant(
            current_user = Depends(self.get_current_user),
            tenant_id: str = None
        ):
            if not tenant_id:
                # Get from query params or path params
                tenant_id = current_user.tenant_id
            
            if not self.auth_manager.has_tenant_access(current_user, tenant_id):
                logger.warning(
                    f"User {current_user.user_id} denied access to tenant {tenant_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this tenant"
                )
            
            return current_user
        
        return check_tenant


class AuditLogger:
    """Log access and authorization decisions"""
    
    def __init__(self):
        self.logger = logging.getLogger('audit')
    
    def log_access(self,
                   user_id: str,
                   action: str,
                   resource: str,
                   result: str,
                   details: dict = None):
        """Log access attempt"""
        self.logger.info(
            f"user_id={user_id} action={action} resource={resource} result={result}",
            extra={
                'user_id': user_id,
                'action': action,
                'resource': resource,
                'result': result,
                'timestamp': datetime.utcnow().isoformat(),
                'details': details or {}
            }
        )


class ServiceAccountAuthenticator:
    """Service-to-service authentication (mTLS style)"""
    
    def __init__(self):
        self.service_accounts = {}
    
    def register_service(self, service_name: str, service_token: str, permissions: List[str]):
        """Register service account"""
        self.service_accounts[service_name] = {
            'token': service_token,
            'permissions': permissions
        }
    
    def authenticate_service(self, service_name: str, token: str) -> bool:
        """Authenticate service"""
        account = self.service_accounts.get(service_name)
        if not account:
            logger.warning(f"Unknown service: {service_name}")
            return False
        
        if account['token'] != token:
            logger.warning(f"Invalid token for service: {service_name}")
            return False
        
        return True
