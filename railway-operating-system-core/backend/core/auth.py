# core/auth.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from ..db_connection import get_db
from ..models import User
from ..schemas.auth import TokenData
from .security import verify_token

# Custom HTTPBearer that returns 401 instead of 403 for missing credentials
class HTTPBearer403To401(HTTPBearer):
    async def __call__(self, request: Request):
        try:
            return await super().__call__(request)
        except HTTPException as e:
            if e.status_code == 403:
                raise HTTPException(status_code=401, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"})
            raise

security = HTTPBearer403To401(auto_error=True)

async def optional_security(request: Request) -> Optional[HTTPAuthorizationCredentials]:
    """Optional security - returns credentials if present, None otherwise"""
    try:
        bearer = HTTPBearer(auto_error=False)
        credentials = await bearer(request)
        return credentials
    except:
        return None

# Role hierarchy (higher number = more permissions)
ROLE_HIERARCHY = {
    "guest": 1,
    "user": 2,
    "operator": 3,
    "developer": 4,
    "admin": 5
}

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def check_role(required_role: str):
    """Dependency to check if user has required role or higher"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        user_level = ROLE_HIERARCHY.get(current_user.role, 0)
        required_level = ROLE_HIERARCHY.get(required_role, 999)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_role}, Current: {current_user.role}"
            )
        return current_user
    return role_checker

# Convenience dependencies for common roles
require_admin = check_role("admin")
require_developer = check_role("developer")
require_operator = check_role("operator")
require_user = check_role("user")

def get_tenant_user(
    tenant_id: UUID,
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Ensure user belongs to the specified tenant"""
    if current_user.tenant_id != tenant_id and current_user.role not in ["admin", "developer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: User does not belong to this tenant"
        )
    return current_user