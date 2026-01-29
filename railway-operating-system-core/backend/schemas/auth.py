# schemas/auth.py
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, Union
from uuid import UUID
from datetime import datetime
import re

class UserBase(BaseModel):
    email: EmailStr
    role: str  # admin, developer, operator, user, guest

class UserCreate(UserBase):
    password: str
    username: str
    first_name: str
    last_name: str
    tenant_id: Optional[Union[int, str]] = None
    
    @field_validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, hyphens, and dots')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: Union[int, UUID]
    tenant_id: Optional[Union[int, UUID]] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    tenant_id: Optional[Union[int, UUID]] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class PasswordChange(BaseModel):
    current_password: str
    new_password: str