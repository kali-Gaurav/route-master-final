# models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db_connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)  # Email verification flag
    role = Column(String, default="user", index=True)  # guest, user, operator, developer, admin
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)  # Soft delete support
    version = Column(Integer, default=1, nullable=False)  # Optimistic locking

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    jobs = relationship("Job", back_populates="user")
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_user_tenant_active', 'tenant_id', 'is_active'),
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_role', 'role'),
        Index('idx_user_created_deleted', 'created_at', 'deleted_at'),
        Index('idx_user_tenant_deleted', 'tenant_id', 'deleted_at'),
    )

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    domain = Column(String, unique=True, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)  # Soft delete support

    # Relationships
    users = relationship("User", back_populates="tenant")
