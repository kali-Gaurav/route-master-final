# services/rls_policy_manager.py - Row-Level Security Policy Management
"""
Implement Row-Level Security (RLS) for multi-tenant data isolation.
Ensures that users can only access data belonging to their tenant.
"""

import sys
from pathlib import Path
from sqlalchemy import text
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from connection import DatabaseConnectionManager, DatabaseConfig
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RLSPolicyManager:
    """Manage Row-Level Security policies for database tables."""

    def __init__(self):
        self.db_manager = DatabaseConnectionManager(DatabaseConfig())

    def enable_rls_on_table(self, table_name: str, tenant_column: str = 'tenant_id') -> bool:
        """Enable RLS on a specific table."""
        try:
            with self.db_manager.session_scope() as session:
                # Enable RLS
                session.execute(text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY"))
                
                # Create policy for users to see only their tenant's data
                policy_name = f"{table_name}_tenant_isolation"
                
                # Drop existing policy if it exists
                session.execute(text(f"""
                    DROP POLICY IF EXISTS {policy_name} ON {table_name}
                """))
                
                # Create new policy
                session.execute(text(f"""
                    CREATE POLICY {policy_name} ON {table_name}
                    USING ({tenant_column} = current_setting('app.current_tenant_id')::uuid)
                    WITH CHECK ({tenant_column} = current_setting('app.current_tenant_id')::uuid)
                """))
                
                session.commit()
                logger.info(f"✓ RLS enabled on {table_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to enable RLS on {table_name}: {e}")
            return False

    def setup_all_rls_policies(self) -> bool:
        """Setup RLS on all tenant-related tables."""
        tables_with_rls = [
            ('stations', 'tenant_id'),
            ('trains', 'tenant_id'),
            ('routes', 'tenant_id'),
            ('schedules', 'route_id'),  # Via route -> tenant
            ('fares', 'route_id'),      # Via route -> tenant
            ('users', 'tenant_id'),
            ('audit_logs', 'tenant_id'),
            ('jobs', 'tenant_id'),
        ]
        
        success_count = 0
        
        for table, column in tables_with_rls:
            if self.enable_rls_on_table(table, column):
                success_count += 1
        
        logger.info(f"✓ RLS setup: {success_count}/{len(tables_with_rls)} tables configured")
        return success_count == len(tables_with_rls)

    def set_tenant_context(self, session, tenant_id: str) -> None:
        """Set the current tenant context for RLS."""
        session.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))

    def create_rls_admin_role(self) -> bool:
        """Create admin role that bypasses RLS."""
        try:
            with self.db_manager.session_scope() as session:
                session.execute(text("""
                    CREATE ROLE rls_admin WITH LOGIN PASSWORD 'secure_admin_password';
                    GRANT CONNECT ON DATABASE railway_os TO rls_admin;
                    ALTER ROLE rls_admin SET rls.bypass = ON;
                """))
                
                session.commit()
                logger.info("✓ RLS admin role created")
                return True

        except Exception as e:
            logger.error(f"Failed to create admin role: {e}")
            return False

    def create_tenant_role(self, tenant_id: str, tenant_name: str) -> bool:
        """Create a database role for a specific tenant."""
        try:
            with self.db_manager.session_scope() as session:
                role_name = f"tenant_{tenant_name.lower().replace(' ', '_')}"
                
                session.execute(text(f"""
                    CREATE ROLE {role_name} WITH LOGIN PASSWORD 'tenant_password_{tenant_id}';
                    GRANT CONNECT ON DATABASE railway_os TO {role_name};
                    GRANT SELECT, INSERT, UPDATE, DELETE ON stations TO {role_name};
                    GRANT SELECT, INSERT, UPDATE, DELETE ON trains TO {role_name};
                    GRANT SELECT, INSERT, UPDATE, DELETE ON routes TO {role_name};
                """))
                
                session.commit()
                logger.info(f"✓ Tenant role created: {role_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to create tenant role: {e}")
            return False

    def verify_rls_enforcement(self) -> bool:
        """Verify that RLS is properly enforced."""
        try:
            with self.db_manager.session_scope() as session:
                # Check if RLS is enabled on critical tables
                result = session.execute(text("""
                    SELECT schemaname, tablename, rowsecurity
                    FROM pg_tables
                    WHERE tablename IN ('stations', 'trains', 'routes', 'users')
                """))
                
                tables_checked = result.fetchall()
                
                for schema, table, rls_enabled in tables_checked:
                    status = "✓" if rls_enabled else "✗"
                    logger.info(f"{status} {table}: RLS {'enabled' if rls_enabled else 'disabled'}")
                
                return True

        except Exception as e:
            logger.error(f"RLS verification failed: {e}")
            return False


# SQL script to apply RLS policies
RLS_SETUP_SQL = """
-- Enable RLS on all tenant-aware tables
ALTER TABLE stations ENABLE ROW LEVEL SECURITY;
ALTER TABLE trains ENABLE ROW LEVEL SECURITY;
ALTER TABLE routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

-- Create tenant isolation policies
CREATE POLICY stations_tenant_isolation ON stations
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY trains_tenant_isolation ON trains
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY routes_tenant_isolation ON routes
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY users_tenant_isolation ON users
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY audit_logs_tenant_isolation ON audit_logs
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY jobs_tenant_isolation ON jobs
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Create admin role that bypasses RLS
CREATE ROLE rls_admin WITH LOGIN PASSWORD 'change_me_secure';
ALTER ROLE rls_admin SET row_security = OFF;
"""
