# models/system.py
from sqlalchemy import Column, String, Integer, Boolean, DateTime, DECIMAL, ForeignKey, JSON, Text, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from connection import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete='RESTRICT'))
    type = Column(String(50), nullable=False)
    status = Column(String(20), default='pending')
    priority = Column(Integer, default=1)
    payload = Column(JSON)
    result = Column(JSON)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False, index=True)

    tenant = relationship("Tenant")

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'running', 'completed', 'failed', 'cancelled')", name='check_job_status'),
        CheckConstraint("priority > 0", name='check_job_priority_positive'),
        Index('idx_jobs_tenant_status', 'tenant_id', 'status'),
        Index('idx_jobs_type', 'type'),
        Index('idx_jobs_created', 'created_at'),
        Index('idx_jobs_deleted', 'is_deleted'),
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete='RESTRICT'))
    user_id = Column(UUID(as_uuid=True))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(UUID(as_uuid=True))
    old_values = Column(JSON)
    new_values = Column(JSON)
    ip_address = Column(INET)
    user_agent = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False, index=True)

    tenant = relationship("Tenant")

    __table_args__ = (
        Index('idx_audit_logs_tenant', 'tenant_id'),
        Index('idx_audit_logs_user', 'user_id'),
        Index('idx_audit_logs_action', 'action'),
        Index('idx_audit_logs_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_logs_timestamp', 'timestamp'),
        Index('idx_audit_logs_deleted', 'is_deleted'),
    )

class SystemMetric(Base):
    __tablename__ = "system_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(DECIMAL(15,4))
    labels = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False, index=True)

    __table_args__ = (
        CheckConstraint("metric_value >= 0", name='check_metric_value_non_negative'),
        Index('idx_system_metrics_name', 'metric_name'),
        Index('idx_system_metrics_timestamp', 'timestamp'),
        Index('idx_system_metrics_deleted', 'is_deleted'),
    )