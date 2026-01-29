# models/job.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db_connection import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    type = Column(String, nullable=False)  # e.g., 'route_analysis', 'report_generation'
    status = Column(String, default="pending", index=True)  # pending, running, completed, failed, cancelled
    priority = Column(Integer, default=1, index=True)  # 1-10, higher = more important
    payload = Column(JSON, nullable=True)  # Input data for the job
    result = Column(JSON, nullable=True)  # Output data from the job
    error_message = Column(Text, nullable=True)
    progress = Column(Integer, default=0)  # 0-100 percent completion
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # For soft deletes
    version = Column(Integer, default=1, nullable=False)  # Optimistic locking

    # Relationships
    user = relationship("User", back_populates="jobs")
    tenant = relationship("Tenant")
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_job_tenant_status', 'tenant_id', 'status'),
        Index('idx_job_user_created', 'user_id', 'created_at'),
        Index('idx_job_status_priority', 'status', 'priority'),
        Index('idx_job_type_status', 'type', 'status'),
        Index('idx_job_created_deleted', 'created_at', 'deleted_at'),
        Index('idx_job_tenant_deleted', 'tenant_id', 'deleted_at'),
        Index('idx_job_status_deleted', 'status', 'deleted_at'),
    )
