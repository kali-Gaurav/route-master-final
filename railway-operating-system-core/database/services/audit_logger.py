# services/audit_logger.py - Comprehensive Audit Logging System
"""
Comprehensive audit logging for compliance, forensics, and security monitoring.
Tracks all data modifications, user actions, and system events.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from connection import DatabaseConnectionManager, DatabaseConfig
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuditLogger:
    """Comprehensive audit logging and compliance tracking."""

    def __init__(self):
        self.db_manager = DatabaseConnectionManager(DatabaseConfig())

    def log_user_action(self, user_id: str, action: str, resource_type: str, 
                       resource_id: str, details: Dict, status: str = 'SUCCESS',
                       tenant_id: Optional[str] = None) -> bool:
        """Log a user action for audit trail."""
        logger.info(f"Logging action: {action} on {resource_type}:{resource_id} by {user_id}")
        
        try:
            with self.db_manager.session_scope() as session:
                session.execute(text(f"""
                    INSERT INTO audit_logs (
                        action, resource_type, resource_id, user_id, 
                        details, status, created_at, tenant_id
                    ) VALUES (
                        '{action}', '{resource_type}', '{resource_id}',
                        '{user_id}', :details, '{status}',
                        CURRENT_TIMESTAMP, '{tenant_id}'
                    )
                """), {'details': json.dumps(details)})
                
                return True

        except Exception as e:
            logger.error(f"Failed to log user action: {e}")
            return False

    def log_data_modification(self, table_name: str, record_id: str, operation: str,
                             old_values: Dict, new_values: Dict, 
                             user_id: Optional[str] = None,
                             tenant_id: Optional[str] = None) -> bool:
        """Log a data modification (INSERT, UPDATE, DELETE)."""
        logger.info(f"Logging {operation} on {table_name}:{record_id}")
        
        try:
            with self.db_manager.session_scope() as session:
                session.execute(text(f"""
                    INSERT INTO audit_logs (
                        action, table_name, record_id, 
                        old_values, new_values, user_id,
                        created_at, tenant_id
                    ) VALUES (
                        '{operation}', '{table_name}', '{record_id}',
                        :old_values, :new_values, '{user_id}',
                        CURRENT_TIMESTAMP, '{tenant_id}'
                    )
                """), {
                    'old_values': json.dumps(old_values),
                    'new_values': json.dumps(new_values)
                })
                
                return True

        except Exception as e:
            logger.error(f"Failed to log data modification: {e}")
            return False

    def log_security_event(self, event_type: str, severity: str, 
                          description: str, ip_address: Optional[str] = None,
                          user_id: Optional[str] = None,
                          tenant_id: Optional[str] = None) -> bool:
        """Log security-related events (login, failed auth, permission denial, etc.)."""
        logger.warning(f"[{severity}] Security event: {event_type} - {description}")
        
        try:
            with self.db_manager.session_scope() as session:
                session.execute(text(f"""
                    INSERT INTO audit_logs (
                        action, event_type, severity,
                        description, ip_address, user_id,
                        created_at, tenant_id
                    ) VALUES (
                        'SECURITY_EVENT', '{event_type}', '{severity}',
                        '{description}', '{ip_address}', '{user_id}',
                        CURRENT_TIMESTAMP, '{tenant_id}'
                    )
                """))
                
                return True

        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
            return False

    def log_api_call(self, endpoint: str, method: str, status_code: int,
                    response_time_ms: float, user_id: Optional[str] = None,
                    request_params: Optional[Dict] = None,
                    tenant_id: Optional[str] = None) -> bool:
        """Log API calls for usage monitoring."""
        logger.info(f"Logging API call: {method} {endpoint} -> {status_code}")
        
        try:
            with self.db_manager.session_scope() as session:
                session.execute(text(f"""
                    INSERT INTO audit_logs (
                        action, endpoint, method, status_code,
                        response_time_ms, user_id, request_params,
                        created_at, tenant_id
                    ) VALUES (
                        'API_CALL', '{endpoint}', '{method}', {status_code},
                        {response_time_ms}, '{user_id}', :request_params,
                        CURRENT_TIMESTAMP, '{tenant_id}'
                    )
                """), {'request_params': json.dumps(request_params or {})})
                
                return True

        except Exception as e:
            logger.error(f"Failed to log API call: {e}")
            return False

    def get_audit_trail(self, resource_type: str, resource_id: str,
                       days: int = 90) -> List[Dict]:
        """Retrieve audit trail for a specific resource."""
        logger.info(f"Retrieving audit trail for {resource_type}:{resource_id}")
        
        try:
            with self.db_manager.session_scope() as session:
                result = session.execute(text(f"""
                    SELECT 
                        id, action, resource_type, resource_id,
                        old_values, new_values, user_id,
                        created_at, status
                    FROM audit_logs
                    WHERE resource_type = '{resource_type}' 
                    AND resource_id = '{resource_id}'
                    AND created_at > CURRENT_TIMESTAMP - INTERVAL '{days} days'
                    ORDER BY created_at DESC
                """)).fetchall()
                
                trail = []
                for row in result:
                    trail.append({
                        'id': row[0],
                        'action': row[1],
                        'resource_type': row[2],
                        'resource_id': row[3],
                        'old_values': json.loads(row[4]) if row[4] else None,
                        'new_values': json.loads(row[5]) if row[5] else None,
                        'user_id': row[6],
                        'timestamp': row[7].isoformat() if row[7] else None,
                        'status': row[8],
                    })
                
                logger.info(f"Retrieved {len(trail)} audit entries")
                return trail

        except Exception as e:
            logger.error(f"Failed to retrieve audit trail: {e}")
            return []

    def get_user_actions(self, user_id: str, days: int = 30) -> List[Dict]:
        """Get all actions performed by a specific user."""
        logger.info(f"Retrieving actions by user {user_id}")
        
        try:
            with self.db_manager.session_scope() as session:
                result = session.execute(text(f"""
                    SELECT 
                        action, resource_type, resource_id,
                        status, created_at, details
                    FROM audit_logs
                    WHERE user_id = '{user_id}'
                    AND created_at > CURRENT_TIMESTAMP - INTERVAL '{days} days'
                    ORDER BY created_at DESC
                """)).fetchall()
                
                actions = []
                for row in result:
                    actions.append({
                        'action': row[0],
                        'resource_type': row[1],
                        'resource_id': row[2],
                        'status': row[3],
                        'timestamp': row[4].isoformat(),
                        'details': json.loads(row[5]) if row[5] else None,
                    })
                
                return actions

        except Exception as e:
            logger.error(f"Failed to retrieve user actions: {e}")
            return []

    def detect_suspicious_activity(self, threshold_failed_logins: int = 5) -> List[Dict]:
        """Detect suspicious user activities."""
        logger.info("Analyzing for suspicious activities...")
        
        try:
            with self.db_manager.session_scope() as session:
                # Find users with multiple failed login attempts
                result = session.execute(text(f"""
                    SELECT 
                        user_id, 
                        COUNT(*) as failed_count,
                        MAX(created_at) as last_attempt
                    FROM audit_logs
                    WHERE action = 'LOGIN_FAILED'
                    AND created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
                    GROUP BY user_id
                    HAVING COUNT(*) >= {threshold_failed_logins}
                """)).fetchall()
                
                suspicious = []
                for user_id, count, last_attempt in result:
                    suspicious.append({
                        'user_id': user_id,
                        'issue': 'Multiple failed login attempts',
                        'count': count,
                        'last_attempt': last_attempt.isoformat(),
                        'severity': 'HIGH',
                    })
                
                logger.warning(f"Found {len(suspicious)} suspicious activities")
                return suspicious

        except Exception as e:
            logger.error(f"Failed to detect suspicious activity: {e}")
            return []

    def generate_compliance_report(self, start_date: datetime, 
                                  end_date: datetime) -> Dict:
        """Generate compliance report for audit trail."""
        logger.info(f"Generating compliance report for {start_date} to {end_date}")
        
        try:
            with self.db_manager.session_scope() as session:
                # Total audit events
                total_events = session.execute(text(f"""
                    SELECT COUNT(*) FROM audit_logs
                    WHERE created_at BETWEEN '{start_date}' AND '{end_date}'
                """)).fetchone()[0]
                
                # Events by action type
                by_action = session.execute(text(f"""
                    SELECT action, COUNT(*) FROM audit_logs
                    WHERE created_at BETWEEN '{start_date}' AND '{end_date}'
                    GROUP BY action
                """)).fetchall()
                
                # Security events
                security_events = session.execute(text(f"""
                    SELECT severity, COUNT(*) FROM audit_logs
                    WHERE event_type IS NOT NULL
                    AND created_at BETWEEN '{start_date}' AND '{end_date}'
                    GROUP BY severity
                """)).fetchall()
                
                # Data modifications
                data_mods = session.execute(text(f"""
                    SELECT action, COUNT(*) FROM audit_logs
                    WHERE action IN ('INSERT', 'UPDATE', 'DELETE')
                    AND created_at BETWEEN '{start_date}' AND '{end_date}'
                    GROUP BY action
                """)).fetchall()
                
                report = {
                    'period': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat(),
                    },
                    'total_events': total_events,
                    'by_action': {action: count for action, count in by_action},
                    'security_events': {severity: count for severity, count in security_events},
                    'data_modifications': {action: count for action, count in data_mods},
                    'generated_at': datetime.now().isoformat(),
                }
                
                logger.info("Compliance report generated")
                return report

        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {}

    def purge_old_audit_logs(self, days: int = 365) -> int:
        """Remove audit logs older than specified days (for performance)."""
        logger.warning(f"Purging audit logs older than {days} days")
        
        try:
            with self.db_manager.session_scope() as session:
                result = session.execute(text(f"""
                    DELETE FROM audit_logs
                    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '{days} days'
                """))
                
                deleted_count = result.rowcount
                logger.info(f"Deleted {deleted_count} old audit log entries")
                return deleted_count

        except Exception as e:
            logger.error(f"Failed to purge audit logs: {e}")
            return 0

    def create_audit_indexes(self) -> bool:
        """Create indexes for efficient audit log queries."""
        logger.info("Creating audit log indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action)",
            "CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_logs(tenant_id)",
        ]
        
        try:
            with self.db_manager.session_scope() as session:
                for index_sql in indexes:
                    session.execute(text(index_sql))
                
                logger.info("Audit indexes created successfully")
                return True

        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            return False

    def setup_audit_table_if_not_exists(self) -> bool:
        """Ensure audit_logs table exists with proper schema."""
        logger.info("Verifying audit_logs table...")
        
        try:
            with self.db_manager.session_scope() as session:
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id BIGSERIAL PRIMARY KEY,
                        action VARCHAR(50) NOT NULL,
                        resource_type VARCHAR(100),
                        resource_id VARCHAR(100),
                        table_name VARCHAR(100),
                        record_id VARCHAR(100),
                        old_values JSONB,
                        new_values JSONB,
                        user_id UUID,
                        ip_address INET,
                        event_type VARCHAR(50),
                        severity VARCHAR(20),
                        description TEXT,
                        details JSONB,
                        status VARCHAR(20) DEFAULT 'LOGGED',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        tenant_id UUID,
                        
                        INDEX idx_audit_user_id (user_id),
                        INDEX idx_audit_created_at (created_at),
                        INDEX idx_audit_resource (resource_type, resource_id),
                        INDEX idx_audit_action (action),
                        INDEX idx_audit_tenant (tenant_id)
                    )
                """))
                
                logger.info("Audit logs table verified/created")
                return True

        except Exception as e:
            logger.error(f"Failed to setup audit table: {e}")
            return False

    def get_audit_statistics(self) -> Dict:
        """Get statistical summary of audit logs."""
        logger.info("Gathering audit statistics...")
        
        try:
            with self.db_manager.session_scope() as session:
                stats = {}
                
                # Total records
                stats['total_records'] = session.execute(
                    text("SELECT COUNT(*) FROM audit_logs")
                ).fetchone()[0]
                
                # Date range
                date_range = session.execute(text("""
                    SELECT MIN(created_at), MAX(created_at) FROM audit_logs
                """)).fetchone()
                stats['date_range'] = {
                    'start': date_range[0].isoformat() if date_range[0] else None,
                    'end': date_range[1].isoformat() if date_range[1] else None,
                }
                
                # Most active users
                stats['top_users'] = session.execute(text("""
                    SELECT user_id, COUNT(*) as count
                    FROM audit_logs
                    WHERE user_id IS NOT NULL
                    GROUP BY user_id
                    ORDER BY count DESC
                    LIMIT 5
                """)).fetchall()
                
                # Most modified tables
                stats['most_modified_tables'] = session.execute(text("""
                    SELECT table_name, COUNT(*) as count
                    FROM audit_logs
                    WHERE table_name IS NOT NULL
                    GROUP BY table_name
                    ORDER BY count DESC
                    LIMIT 5
                """)).fetchall()
                
                return stats

        except Exception as e:
            logger.error(f"Failed to get audit statistics: {e}")
            return {}
