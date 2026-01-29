# core/security.py
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from ..config import settings
from .token_blacklist import TokenBlacklist
from .jwt_secret_manager import jwt_secret_manager

# Use argon2 for better security (more compatible than bcrypt)
# Falls back to plaintext for development if argon2 unavailable
try:
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
except Exception:
    # Fallback for development/testing if argon2 not available
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password with argon2/pbkdf2"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token with rotated secrets"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)

    # Add secret ID for token validation
    active_secret = jwt_secret_manager.get_active_secret()
    if not active_secret:
        raise ValueError("No active JWT secret available")

    to_encode.update({
        "exp": expire,
        "type": "access",
        "secret_id": jwt_secret_manager.get_secret_ids()[-1]  # Current active secret ID
    })

    encoded_jwt = jwt.encode(to_encode, active_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT refresh token with rotated secrets"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_refresh_expiration_hours)

    # Add secret ID for token validation
    active_secret = jwt_secret_manager.get_active_secret()
    if not active_secret:
        raise ValueError("No active JWT secret available")

    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "secret_id": jwt_secret_manager.get_secret_ids()[-1]  # Current active secret ID
    })

    encoded_jwt = jwt.encode(to_encode, active_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token with secret rotation support"""
    try:
        # Check if token is blacklisted first
        if TokenBlacklist.is_blacklisted(token):
            return None

        # Decode without verification to get header and payload
        header = jwt.get_unverified_header(token)
        payload = jwt.decode(token, options={"verify_signature": False})

        # Get secret ID from payload
        secret_id = payload.get("secret_id")
        if secret_id:
            # Try to get the specific secret used for this token
            secret = jwt_secret_manager.get_secret_by_id(secret_id)
            if not secret:
                return None  # Secret no longer available or expired
        else:
            # Fallback to active secret for backward compatibility
            secret = jwt_secret_manager.get_active_secret()
            if not secret:
                return None

        # Verify the token with the appropriate secret
        try:
            payload = jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
            return payload
        except JWTError:
            # If verification fails with the specific secret, try active secret
            if secret_id:
                active_secret = jwt_secret_manager.get_active_secret()
                if active_secret and active_secret != secret:
                    try:
                        payload = jwt.decode(token, active_secret, algorithms=[settings.jwt_algorithm])
                        return payload
                    except JWTError:
                        pass
            return None

    except JWTError as e:
        # Token is malformed or expired
        return None
    except Exception as e:
        # Other errors
        return None
