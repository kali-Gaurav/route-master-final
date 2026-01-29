# api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from ...db_connection import get_db
from ...models import User
from ...schemas.auth import UserCreate, UserUpdate, User as UserSchema, Token, LoginRequest, PasswordChange
from ...services.user_service import UserService
from ...core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, verify_token
from ...core.auth import get_current_active_user
from ...core.token_blacklist import TokenBlacklist
from ...core.email_service import get_email_service
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
import os

logger = logging.getLogger(__name__)

# Create limiter, but it's disabled in test mode
limiter = Limiter(key_func=get_remote_address)

# Helper to conditionally apply rate limiting based on environment
def rate_limit(rate_spec: str):
    """Apply rate limiting unless in test mode"""
    if os.getenv("TESTING") == "1":
        # In test mode, return a no-op decorator
        def no_op_decorator(func):
            return func
        return no_op_decorator
    else:
        # In production, apply the actual rate limit
        return limiter.limit(rate_spec)

router = APIRouter()

@router.post("/login", response_model=Token)
@rate_limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """User login endpoint with rate limiting"""
    try:
        user_service = UserService(db)
        user = user_service.authenticate_user(form_data.username, form_data.password)

        if not user:
            logger.warning(f"Failed login attempt for user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(hours=settings.jwt_expiration_hours)
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role, "tenant_id": str(user.tenant_id) if user.tenant_id else None},
            expires_delta=access_token_expires
        )
        
        # Create refresh token
        refresh_token_expires = timedelta(hours=settings.jwt_refresh_expiration_hours)
        refresh_token = create_refresh_token(
            data={"sub": user.email},
            expires_delta=refresh_token_expires
        )

        logger.info(f"User logged in: {user.email}")
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
    request: Request = None
):
    """Logout user by blacklisting token"""
    try:
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            TokenBlacklist.revoke_token(token)
            logger.info(f"User logged out: {current_user.email}")
        
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_active_user)
):
    """Refresh access token (issue new access and refresh token)"""
    try:
        access_token_expires = timedelta(hours=settings.jwt_expiration_hours)
        access_token = create_access_token(
            data={"sub": current_user.email, "role": current_user.role, "tenant_id": str(current_user.tenant_id) if current_user.tenant_id else None},
            expires_delta=access_token_expires
        )
        
        # Always issue new refresh token for better security
        refresh_token_expires = timedelta(hours=settings.jwt_refresh_expiration_hours)
        refresh_token = create_refresh_token(
            data={"sub": current_user.email},
            expires_delta=refresh_token_expires
        )

        logger.info(f"Token refreshed for user: {current_user.email}")
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

@router.get("/me", response_model=UserSchema)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user

@router.post("/register", response_model=dict)
@rate_limit("3/minute")
async def register_user(
    request: Request,
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """Register new user with email verification"""
    try:
        user_service = UserService(db)

        # Check if user already exists
        db_user = user_service.get_user_by_email(user.email)
        if db_user:
            logger.warning(f"Registration attempt with existing email: {user.email}")
            raise HTTPException(status_code=400, detail="Email already registered")

        # Check if username already exists
        if user_service.get_user_by_username(user.username):
            raise HTTPException(status_code=400, detail="Username already taken")

        # Validate password policy
        user_info = {
            'username': user.username,
            'email': user.email,
            'first_name': getattr(user, 'first_name', None),
            'last_name': getattr(user, 'last_name', None)
        }
        password_validation = password_validator.validate_password(user.password, user_info)

        if not password_validation['valid']:
            logger.warning(f"Password policy violation for user {user.email}: {password_validation['violations']}")
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Password does not meet security requirements",
                    "violations": password_validation['violations'],
                    "requirements": password_validator.get_policy_requirements()
                }
            )

        # Create user (inactive by default)
        created_user = user_service.create_user(user, is_active=False)

        # Send verification email
        email_service = get_email_service()
        verification_url = f"{settings.api_base_url}/auth/verify-email"
        success = email_service.send_verification_email(user.email, verification_url)

        if not success:
            # If email fails, still create user but log the issue
            logger.error(f"Failed to send verification email to {user.email}")
            # For now, we'll activate the account if email fails
            # In production, you might want to handle this differently
            user_service.activate_user(created_user.id)

        logger.info(f"New user registered (pending verification): {created_user.email}")
        return {
            "message": "Registration successful. Please check your email for verification instructions.",
            "email": user.email,
            "requires_verification": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify user email with token"""
    try:
        email_service = get_email_service()

        # Verify token and get email
        email = email_service.verify_email_token(token)
        if not email:
            raise HTTPException(status_code=400, detail="Invalid or expired verification token")

        user_service = UserService(db)
        user = user_service.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.is_active:
            return {"message": "Email already verified"}

        # Activate user
        success = user_service.activate_user(user.id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to activate account")

        # Send welcome email
        email_service.send_welcome_email(email, user.first_name or user.username)

        logger.info(f"Email verified for user: {email}")
        return {"message": "Email verified successfully. Your account is now active."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(status_code=500, detail="Email verification failed")

@router.put("/me", response_model=UserSchema)
async def update_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user"""
    try:
        user_service = UserService(db)
        updated = user_service.update_user(current_user.id, user_update)
        if not updated:
            raise HTTPException(status_code=404, detail="User not found")
        logger.info(f"User profile updated: {current_user.email}")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {e}")
        raise HTTPException(status_code=500, detail="Update failed")

@router.put("/password")
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change current user's password"""
    try:
        user_service = UserService(db)

        # Verify current password
        if not user_service.authenticate_user(current_user.email, password_change.current_password):
            logger.warning(f"Invalid current password for password change: {current_user.email}")
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Validate new password policy
        user_info = {
            'username': current_user.username,
            'email': current_user.email,
            'first_name': getattr(current_user, 'first_name', None),
            'last_name': getattr(current_user, 'last_name', None)
        }
        password_validation = password_validator.validate_password(password_change.new_password, user_info)

        if not password_validation['valid']:
            logger.warning(f"Password policy violation for password change: {current_user.email}: {password_validation['violations']}")
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "New password does not meet security requirements",
                    "violations": password_validation['violations'],
                    "requirements": password_validator.get_policy_requirements()
                }
            )

        # Update password
        success = user_service.set_password(current_user.id, password_change.new_password)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update password")

        logger.info(f"Password changed for user: {current_user.email}")
        return {"message": "Password changed successfully. Your current session will remain active, but you may need to login again on other devices."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(status_code=500, detail="Password change failed")

@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify user email with token"""
    try:
        email_service = get_email_service()
        email = email_service.verify_email_token(token)

        if not email:
            raise HTTPException(status_code=400, detail="Invalid or expired verification token")

        user_service = UserService(db)
        user = user_service.get_user_by_email(email)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.is_active:
            return {"message": "Email already verified"}

        # Activate user
        success = user_service.activate_user(user.id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to activate account")

        # Send welcome email
        email_service.send_welcome_email(email, user.first_name or user.username)

        logger.info(f"Email verified for user: {email}")
        return {"message": "Email verified successfully. Your account is now active."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(status_code=500, detail="Email verification failed")

@router.get("/password-policy")
async def get_password_policy():
    """Get current password policy requirements"""
    return {
        "policy": password_validator.get_policy_requirements(),
        "description": "Password must meet all the specified requirements for account security."
    }