# models/user.py
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete='RESTRICT'))
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # admin, developer, operator, user, guest
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant")

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'developer', 'operator', 'user', 'guest')", name='check_user_role'),
        Index('idx_users_email', 'email'),
        Index('idx_users_role', 'role'),
        Index('idx_users_active', 'is_active'),
        Index('idx_users_deleted', 'is_deleted'),
        Index('idx_users_tenant_active', 'tenant_id', 'is_active'),
    )