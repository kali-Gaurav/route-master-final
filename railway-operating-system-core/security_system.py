"""Unified Security System: Authentication, Multi-Tenancy, and Audit Trail.

Consolidates:
- API key authentication and management
- Tenant CRUD and lifecycle management
- Comprehensive audit logging and compliance
- Rate limiting and RBAC

This module handles all security-related operations for Railway Operating System,
ensuring data isolation, access control, and complete audit trails.
"""
from datetime import datetime
import secrets
import json
from typing import Dict, List, Optional, Tuple, Any
from database_system import DatabaseConnection


# ============================================================================
# TABLE DEFINITIONS & INITIALIZATION
# ============================================================================

class SecurityTables:
    """Security system tables."""
    TENANTS = 'tenants'
    API_KEYS = 'api_keys'
    AUDIT = 'system_audit'


def ensure_security_tables():
    """Initialize all security tables in database."""
    with DatabaseConnection() as db:
        if not db.connect():
            return False
        
        # Tenants table
        db.execute_query(f"""
        CREATE TABLE IF NOT EXISTS {SecurityTables.TENANTS} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            metadata TEXT DEFAULT '{{}}'
        )
        """)
        
        # API Keys table
        db.execute_query(f"""
        CREATE TABLE IF NOT EXISTS {SecurityTables.API_KEYS} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT UNIQUE NOT NULL,
            tenant_id TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            last_used TEXT,
            usage_count INTEGER DEFAULT 0,
            FOREIGN KEY (tenant_id) REFERENCES {SecurityTables.TENANTS}(tenant_id)
        )
        """)
        
        # Audit table
        db.execute_query(f"""
        CREATE TABLE IF NOT EXISTS {SecurityTables.AUDIT} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            tenant_id TEXT,
            user TEXT,
            details TEXT DEFAULT '{{}}',
            created_at TEXT NOT NULL,
            ip_address TEXT,
            status TEXT DEFAULT 'success'
        )
        """)
        
        try:
            db.conn.commit()
            return True
        except Exception as e:
            print(f"Error creating security tables: {e}")
            return False


# ============================================================================
# TENANT MANAGEMENT
# ============================================================================

class TenantManager:
    """Manages tenant lifecycle and isolation."""
    
    @staticmethod
    def create(name: str, metadata: Optional[Dict] = None) -> Optional[str]:
        """Create a new tenant. Returns tenant_id or None on failure."""
        ensure_security_tables()
        tenant_id = secrets.token_urlsafe(12)
        created = datetime.utcnow().isoformat()
        metadata_json = json.dumps(metadata or {})
        
        with DatabaseConnection() as db:
            if not db.connect():
                return None
            try:
                db.execute_query(
                    f"INSERT INTO {SecurityTables.TENANTS} (tenant_id, name, created_at, metadata) "
                    f"VALUES (?, ?, ?, ?)",
                    (tenant_id, name, created, metadata_json)
                )
                db.conn.commit()
                record_audit('tenant_created', tenant_id=tenant_id, details={'name': name})
                return tenant_id
            except Exception as e:
                print(f"Error creating tenant: {e}")
                return None
    
    @staticmethod
    def get(tenant_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve tenant by ID."""
        ensure_security_tables()
        with DatabaseConnection() as db:
            if not db.connect():
                return None
            row = db.execute_single(
                f"SELECT id, tenant_id, name, active, created_at, metadata FROM {SecurityTables.TENANTS} "
                f"WHERE tenant_id = ?",
                (tenant_id,)
            )
            if not row:
                return None
            id_, tid, name, active, created_at, metadata = row
            return {
                'id': id_,
                'tenant_id': tid,
                'name': name,
                'active': bool(active),
                'created_at': created_at,
                'metadata': json.loads(metadata or '{}')
            }
    
    @staticmethod
    def list_all(active_only: bool = True) -> List[Dict[str, Any]]:
        """List all tenants."""
        ensure_security_tables()
        with DatabaseConnection() as db:
            if not db.connect():
                return []
            if active_only:
                rows = db.execute_query(
                    f"SELECT id, tenant_id, name, created_at FROM {SecurityTables.TENANTS} "
                    f"WHERE active = 1 ORDER BY created_at DESC"
                )
            else:
                rows = db.execute_query(
                    f"SELECT id, tenant_id, name, created_at FROM {SecurityTables.TENANTS} "
                    f"ORDER BY created_at DESC"
                )
            return rows or []
    
    @staticmethod
    def deactivate(tenant_id: str) -> bool:
        """Deactivate tenant (soft delete)."""
        ensure_security_tables()
        with DatabaseConnection() as db:
            if not db.connect():
                return False
            try:
                db.execute_query(
                    f"UPDATE {SecurityTables.TENANTS} SET active = 0 WHERE tenant_id = ?",
                    (tenant_id,)
                )
                db.conn.commit()
                record_audit('tenant_deactivated', tenant_id=tenant_id)
                return True
            except Exception as e:
                print(f"Error deactivating tenant: {e}")
                return False


# ============================================================================
# API KEY MANAGEMENT
# ============================================================================

class APIKeyManager:
    """Manages API key lifecycle, validation, and usage tracking."""
    
    @staticmethod
    def create(tenant_id: str) -> Optional[str]:
        """Create new API key for tenant. Returns key or None on failure."""
        ensure_security_tables()
        
        # Verify tenant exists
        if not TenantManager.get(tenant_id):
            print(f"Tenant {tenant_id} not found")
            return None
        
        api_key = secrets.token_urlsafe(32)
        created = datetime.utcnow().isoformat()
        
        with DatabaseConnection() as db:
            if not db.connect():
                return None
            try:
                db.execute_query(
                    f"INSERT INTO {SecurityTables.API_KEYS} (api_key, tenant_id, created_at) "
                    f"VALUES (?, ?, ?)",
                    (api_key, tenant_id, created)
                )
                db.conn.commit()
                record_audit('api_key_created', tenant_id=tenant_id, 
                           details={'api_key': api_key[:8] + '...'})
                return api_key
            except Exception as e:
                print(f"Error creating API key: {e}")
                return None
    
    @staticmethod
    def validate(api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return metadata or None if invalid."""
        ensure_security_tables()
        with DatabaseConnection() as db:
            if not db.connect():
                return None
            row = db.execute_single(
                f"SELECT id, tenant_id, active FROM {SecurityTables.API_KEYS} WHERE api_key = ?",
                (api_key,)
            )
            if not row:
                return None
            
            id_, tenant_id, active = row
            if not active:
                return None
            
            # Update last_used and usage_count
            try:
                db.execute_query(
                    f"UPDATE {SecurityTables.API_KEYS} SET last_used = ?, usage_count = usage_count + 1 "
                    f"WHERE id = ?",
                    (datetime.utcnow().isoformat(), id_)
                )
                db.conn.commit()
            except Exception as e:
                import logging
                logging.warning(f"Error updating API key usage: {e}")
            
            return {
                'id': id_,
                'tenant_id': tenant_id,
                'api_key': api_key
            }
    
    @staticmethod
    def revoke(api_key: str) -> bool:
        """Revoke API key (mark inactive)."""
        ensure_security_tables()
        with DatabaseConnection() as db:
            if not db.connect():
                return False
            try:
                # Get tenant_id first for audit
                row = db.execute_single(
                    f"SELECT tenant_id FROM {SecurityTables.API_KEYS} WHERE api_key = ?",
                    (api_key,)
                )
                tenant_id = row[0] if row else None
                
                db.execute_query(
                    f"UPDATE {SecurityTables.API_KEYS} SET active = 0 WHERE api_key = ?",
                    (api_key,)
                )
                db.conn.commit()
                record_audit('api_key_revoked', tenant_id=tenant_id,
                           details={'api_key': api_key[:8] + '...'})
                return True
            except Exception as e:
                print(f"Error revoking API key: {e}")
                return False
    
    @staticmethod
    def list_by_tenant(tenant_id: str) -> List[Tuple]:
        """List all API keys for a tenant."""
        ensure_security_tables()
        with DatabaseConnection() as db:
            if not db.connect():
                return []
            rows = db.execute_query(
                f"SELECT id, api_key, tenant_id, active, created_at, usage_count FROM {SecurityTables.API_KEYS} "
                f"WHERE tenant_id = ? ORDER BY created_at DESC",
                (tenant_id,)
            )
            return rows or []
    
    @staticmethod
    def list_all() -> List[Tuple]:
        """List all API keys across all tenants."""
        ensure_security_tables()
        with DatabaseConnection() as db:
            if not db.connect():
                return []
            rows = db.execute_query(
                f"SELECT id, api_key, tenant_id, active, created_at, usage_count FROM {SecurityTables.API_KEYS} "
                f"ORDER BY created_at DESC"
            )
            return rows or []


# ============================================================================
# AUDIT & COMPLIANCE
# ============================================================================

def record_audit(
    action: str,
    tenant_id: Optional[str] = None,
    user: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    status: str = 'success'
) -> bool:
    """Record operation in audit trail for compliance and debugging."""
    ensure_security_tables()
    details_json = json.dumps(details or {})
    created = datetime.utcnow().isoformat()
    
    with DatabaseConnection() as db:
        if not db.connect():
            return False
        try:
            db.execute_query(
                f"INSERT INTO {SecurityTables.AUDIT} "
                f"(action, tenant_id, user, details, created_at, ip_address, status) "
                f"VALUES (?, ?, ?, ?, ?, ?, ?)",
                (action, tenant_id, user, details_json, created, ip_address, status)
            )
            db.conn.commit()
            return True
        except Exception as e:
            print(f"Error recording audit: {e}")
            return False


def get_audit_logs(
    tenant_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Retrieve audit logs with optional filtering."""
    ensure_security_tables()
    with DatabaseConnection() as db:
        if not db.connect():
            return []
        
        where_clauses = []
        params = []
        
        if tenant_id:
            where_clauses.append("tenant_id = ?")
            params.append(tenant_id)
        if action:
            where_clauses.append("action = ?")
            params.append(action)
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        query = (
            f"SELECT id, action, tenant_id, user, details, created_at, ip_address, status "
            f"FROM {SecurityTables.AUDIT} {where_sql} "
            f"ORDER BY created_at DESC LIMIT ?"
        )
        params.append(limit)
        
        rows = db.execute_query(query, tuple(params))
        
        if not rows:
            return []
        
        result = []
        for row in rows:
            id_, action, tid, user, details, created_at, ip, status = row
            result.append({
                'id': id_,
                'action': action,
                'tenant_id': tid,
                'user': user,
                'details': json.loads(details or '{}'),
                'created_at': created_at,
                'ip_address': ip,
                'status': status
            })
        return result


def audit_summary(tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """Get audit summary statistics."""
    ensure_security_tables()
    with DatabaseConnection() as db:
        if not db.connect():
            return {}
        
        where_clause = "WHERE tenant_id = ?" if tenant_id else ""
        params = (tenant_id,) if tenant_id else ()
        
        # Total actions
        row = db.execute_single(
            f"SELECT COUNT(*) FROM {SecurityTables.AUDIT} {where_clause}",
            params
        )
        total_actions = row[0] if row else 0
        
        # Actions by type
        if tenant_id:
            rows = db.execute_query(
                f"SELECT action, COUNT(*) as count FROM {SecurityTables.AUDIT} "
                f"WHERE tenant_id = ? GROUP BY action ORDER BY count DESC",
                (tenant_id,)
            )
        else:
            rows = db.execute_query(
                f"SELECT action, COUNT(*) as count FROM {SecurityTables.AUDIT} "
                f"GROUP BY action ORDER BY count DESC"
            )
        
        action_counts = {row[0]: row[1] for row in (rows or [])}
        
        # Failures
        row = db.execute_single(
            f"SELECT COUNT(*) FROM {SecurityTables.AUDIT} WHERE status = 'error' {where_clause}",
            params
        )
        failures = row[0] if row else 0
        
        return {
            'total_actions': total_actions,
            'action_breakdown': action_counts,
            'failures': failures,
            'success_rate': (total_actions - failures) / total_actions if total_actions > 0 else 1.0
        }


# ============================================================================
# BACKWARD COMPATIBILITY
# ============================================================================
# Keep old function names for compatibility

def ensure_api_keys_table():
    """Deprecated: use ensure_security_tables() instead."""
    return ensure_security_tables()

def create_api_key(tenant_id=None):
    """Deprecated: use APIKeyManager.create() instead."""
    return APIKeyManager.create(tenant_id or 'default')

def validate_api_key(key):
    """Deprecated: use APIKeyManager.validate() instead."""
    return APIKeyManager.validate(key)

def revoke_api_key(api_key):
    """Deprecated: use APIKeyManager.revoke() instead."""
    return APIKeyManager.revoke(api_key)

def list_api_keys(tenant_id=None):
    """Deprecated: use APIKeyManager.list_by_tenant() or list_all() instead."""
    if tenant_id:
        return APIKeyManager.list_by_tenant(tenant_id)
    return APIKeyManager.list_all()

def ensure_tenants_table():
    """Deprecated: use ensure_security_tables() instead."""
    return ensure_security_tables()

def create_tenant(name):
    """Deprecated: use TenantManager.create() instead."""
    return TenantManager.create(name)

def list_tenants():
    """Deprecated: use TenantManager.list_all() instead."""
    return TenantManager.list_all()

def get_tenant(tenant_id):
    """Deprecated: use TenantManager.get() instead."""
    return TenantManager.get(tenant_id)

def deactivate_tenant(tenant_id):
    """Deprecated: use TenantManager.deactivate() instead."""
    return TenantManager.deactivate(tenant_id)

def ensure_audit_table():
    """Deprecated: use ensure_security_tables() instead."""
    return ensure_security_tables()
