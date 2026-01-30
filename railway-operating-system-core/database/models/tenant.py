# models/tenant.py
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Text, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from base import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    api_key = Column(String(255), unique=True, nullable=False)
    schema_name = Column(String(100), unique=True)
    database_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_tenants_name', 'name'),
        Index('idx_tenants_api_key', 'api_key'),
        Index('idx_tenants_schema', 'schema_name'),
        Index('idx_tenants_active', 'is_active'),
        Index('idx_tenants_deleted', 'is_deleted'),
    )

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete='RESTRICT'), nullable=False)
    key_hash = Column(String(255), nullable=False)
    name = Column(String(100))
    permissions = Column(JSON, default=dict)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant")

    __table_args__ = (
        CheckConstraint("expires_at > created_at", name='check_api_key_expiry'),
        Index('idx_api_keys_tenant', 'tenant_id'),
        Index('idx_api_keys_active', 'is_active'),
        Index('idx_api_keys_deleted', 'is_deleted'),
        Index('idx_api_keys_expires', 'expires_at'),
    )