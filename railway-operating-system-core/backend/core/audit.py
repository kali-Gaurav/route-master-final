# core/audit.py
"""Audit Trail System for User Actions"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID
import json
import logging
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
import redis

from ..config import settings

logger = logging.getLogger(__name__)
Base = declarative_base()

class AuditLog(Base):
    """Audit log table for tracking user actions"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)  # UUID as string
    tenant_id = Column(String(36), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(36), nullable=True, index=True)
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE
    endpoint = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    status_code = Column(Integer, nullable=True)
    request_data = Column(JSONB, nullable=True)  # Store sanitized request data
    response_data = Column(JSONB, nullable=True)  # Store sanitized response data
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    correlation_id = Column(String(36), nullable=True, index=True)

    # Indexes for performance
    __table_args__ = (
        Index('idx_audit_user_action', 'user_id', 'action'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_timestamp_user', 'timestamp', 'user_id'),
        Index('idx_audit_correlation', 'correlation_id'),
    )

class AuditEvent:
    """Represents an auditable event"""

    def __init__(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        method: str,
        endpoint: str,
        correlation_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
        duration_ms: Optional[int] = None
    ):
        self.user_id = user_id
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.tenant_id = tenant_id
        self.method = method
        self.endpoint = endpoint
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.status_code = status_code
        self.request_data = self._sanitize_data(request_data) if request_data else None
        self.duration_ms = duration_ms
        self.correlation_id = correlation_id
        self.timestamp = datetime.utcnow()

    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from audit data"""
        if not isinstance(data, dict):
            return data

        sanitized = {}
        sensitive_fields = {
            'password', 'token', 'secret', 'key', 'authorization',
            'credit_card', 'ssn', 'social_security', 'api_key'
        }

        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'timestamp': self.timestamp,
            'user_id': self.user_id,
            'tenant_id': self.tenant_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'method': self.method,
            'endpoint': self.endpoint,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'status_code': self.status_code,
            'request_data': self.request_data,
            'duration_ms': self.duration_ms,
            'correlation_id': self.correlation_id
        }

class AuditService:
    """Service for managing audit logs"""

    def __init__(self, db: Session, redis_client: Optional[redis.Redis] = None):
        self.db = db
        self.redis = redis_client

    async def log_event(self, event: AuditEvent) -> None:
        """Log an audit event"""
        try:
            # Create audit log entry
            audit_log = AuditLog(
                timestamp=event.timestamp,
                user_id=event.user_id,
                tenant_id=event.tenant_id,
                action=event.action,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                method=event.method,
                endpoint=event.endpoint,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                status_code=event.status_code,
                request_data=event.request_data,
                duration_ms=event.duration_ms,
                correlation_id=event.correlation_id
            )

            self.db.add(audit_log)
            self.db.commit()

            # Also store in Redis for recent activity (TTL 24 hours)
            if self.redis:
                try:
                    key = f"audit:recent:{event.user_id}"
                    self.redis.lpush(key, json.dumps(event.to_dict()))
                    self.redis.ltrim(key, 0, 99)  # Keep last 100 events
                    self.redis.expire(key, 86400)  # 24 hours
                except Exception as e:
                    logger.warning(f"Failed to store audit event in Redis: {e}")

            logger.info(
                f"AUDIT: {event.action} by user {event.user_id} on {event.resource_type}",
                extra={
                    'user_id': event.user_id,
                    'action': event.action,
                    'resource_type': event.resource_type,
                    'correlation_id': event.correlation_id
                }
            )

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            # Don't raise exception to avoid breaking the main flow

    async def log_event_async(self, event: AuditEvent) -> None:
        """Alias for log_event to match middleware interface"""
        await self.log_event(event)

    async def get_user_activity(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get audit logs for a specific user"""
        try:
            query = self.db.query(AuditLog).filter(AuditLog.user_id == user_id)

            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)

            audit_logs = (
                query.order_by(AuditLog.timestamp.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            return [self._audit_log_to_dict(log) for log in audit_logs]

        except Exception as e:
            logger.error(f"Failed to get user activity: {e}")
            return []

    async def get_recent_activity(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activity from Redis cache"""
        if not self.redis:
            return await self.get_user_activity(user_id, limit=limit)

        try:
            key = f"audit:recent:{user_id}"
            events = self.redis.lrange(key, 0, limit - 1)

            if events:
                return [json.loads(event) for event in events]
            else:
                # Fall back to database
                return await self.get_user_activity(user_id, limit=limit)

        except Exception as e:
            logger.warning(f"Failed to get recent activity from Redis: {e}")
            return await self.get_user_activity(user_id, limit=limit)

    async def search_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Search audit logs with filters"""
        try:
            query = self.db.query(AuditLog)

            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            if action:
                query = query.filter(AuditLog.action == action)
            if resource_type:
                query = query.filter(AuditLog.resource_type == resource_type)
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)

            audit_logs = (
                query.order_by(AuditLog.timestamp.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            return [self._audit_log_to_dict(log) for log in audit_logs]

        except Exception as e:
            logger.error(f"Failed to search audit logs: {e}")
            return []

    def _audit_log_to_dict(self, audit_log: AuditLog) -> Dict[str, Any]:
        """Convert AuditLog object to dictionary"""
        return {
            'id': audit_log.id,
            'timestamp': audit_log.timestamp.isoformat(),
            'user_id': audit_log.user_id,
            'tenant_id': audit_log.tenant_id,
            'action': audit_log.action,
            'resource_type': audit_log.resource_type,
            'resource_id': audit_log.resource_id,
            'method': audit_log.method,
            'endpoint': audit_log.endpoint,
            'ip_address': audit_log.ip_address,
            'user_agent': audit_log.user_agent,
            'status_code': audit_log.status_code,
            'request_data': audit_log.request_data,
            'duration_ms': audit_log.duration_ms,
            'correlation_id': audit_log.correlation_id
        }

# Global audit service instance
audit_service = None

def get_audit_service(db: Session) -> AuditService:
    """Get audit service instance"""
    global audit_service
    if audit_service is None:
        # Try to get Redis client
        redis_client = None
        try:
            import redis
            redis_client = redis.from_url(settings.redis_url)
        except:
            pass

        audit_service = AuditService(db, redis_client)
    return audit_service