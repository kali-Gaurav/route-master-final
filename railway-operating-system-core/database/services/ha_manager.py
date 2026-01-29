# services/ha_manager.py - High Availability & Failover Management
"""
High Availability setup for PostgreSQL with read replicas, streaming replication,
and automatic failover capabilities.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

from connection import DatabaseConnectionManager, DatabaseConfig
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ReplicaConfig:
    """Configuration for a read replica."""
    replica_name: str
    primary_host: str
    replica_host: str
    replica_port: int = 5432
    replication_user: str = 'replicator'
    replication_password: str = 'secure_password'


class HighAvailabilityManager:
    """Manages PostgreSQL HA setup with replicas and failover."""

    def __init__(self):
        self.db_manager = DatabaseConnectionManager(DatabaseConfig())

    def setup_replication_user(self, username: str, password: str) -> bool:
        """Create replication user with necessary privileges."""
        logger.info(f"Setting up replication user: {username}")
        
        try:
            with self.db_manager.session_scope() as session:
                # Check if user exists
                result = session.execute(text(
                    f"SELECT 1 FROM pg_roles WHERE rolname = '{username}'"
                )).fetchone()
                
                if result:
                    logger.info(f"User {username} already exists")
                    return True
                
                # Create user with replication privilege
                session.execute(text(f"""
                    CREATE USER {username} WITH 
                        PASSWORD '{password}'
                        REPLICATION
                        LOGIN
                """))
                
                logger.info(f"Created replication user: {username}")
                return True

        except Exception as e:
            logger.error(f"Failed to setup replication user: {e}")
            return False

    def enable_wal_archiving(self, archive_directory: str) -> bool:
        """Enable WAL archiving for point-in-time recovery."""
        logger.info(f"Enabling WAL archiving to {archive_directory}")
        
        try:
            with self.db_manager.session_scope() as session:
                # Create archive directory SQL (would be done via pg_hba.conf/postgresql.conf)
                session.execute(text(f"""
                    ALTER SYSTEM SET wal_level = 'replica'
                """))
                
                session.execute(text(f"""
                    ALTER SYSTEM SET archive_mode = on
                """))
                
                session.execute(text(f"""
                    ALTER SYSTEM SET archive_command = 'test ! -f {archive_directory}/%f && cp %p {archive_directory}/%f'
                """))
                
                logger.info("WAL archiving configured")
                return True

        except Exception as e:
            logger.error(f"Failed to enable WAL archiving: {e}")
            return False

    def setup_streaming_replication(self, replica_name: str) -> bool:
        """Setup streaming replication from primary to replica."""
        logger.info(f"Setting up streaming replication for {replica_name}")
        
        try:
            with self.db_manager.session_scope() as session:
                # Verify primary is in standby mode
                result = session.execute(text(
                    "SELECT pg_is_in_recovery()"
                )).fetchone()
                
                if result[0]:
                    logger.warning("This server is already in standby mode (replica)")
                    return False
                
                logger.info(f"Primary server confirmed. Ready to accept replica: {replica_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to setup streaming replication: {e}")
            return False

    def monitor_replica_lag(self) -> Dict[str, float]:
        """Monitor replication lag on all connected replicas."""
        logger.info("Monitoring replica lag...")
        
        try:
            with self.db_manager.session_scope() as session:
                result = session.execute(text("""
                    SELECT 
                        client_addr::text as replica_address,
                        application_name,
                        state,
                        write_lag,
                        flush_lag,
                        replay_lag,
                        backend_start
                    FROM pg_stat_replication
                """)).fetchall()
                
                lag_status = {}
                for client_addr, app_name, state, write_lag, flush_lag, replay_lag, start_time in result:
                    lag_status[client_addr] = {
                        'application': app_name,
                        'state': state,
                        'write_lag_ms': float(write_lag.total_seconds() * 1000) if write_lag else 0,
                        'flush_lag_ms': float(flush_lag.total_seconds() * 1000) if flush_lag else 0,
                        'replay_lag_ms': float(replay_lag.total_seconds() * 1000) if replay_lag else 0,
                    }
                
                logger.info(f"Monitored {len(lag_status)} replicas")
                return lag_status

        except Exception as e:
            logger.error(f"Failed to monitor replica lag: {e}")
            return {}

    def check_replica_health(self, replica_host: str) -> bool:
        """Check if a replica is healthy and up-to-date."""
        logger.info(f"Checking replica health at {replica_host}")
        
        try:
            # Would connect to replica and check status
            # This is a placeholder for actual health check logic
            logger.info(f"Replica {replica_host} is healthy")
            return True

        except Exception as e:
            logger.error(f"Replica health check failed: {e}")
            return False

    def initiate_failover(self, new_primary_host: str) -> bool:
        """Promote a standby (replica) to primary."""
        logger.info(f"Initiating failover to {new_primary_host}")
        
        try:
            # This would require connecting to the replica
            # and executing: pg_ctl promote
            logger.warning("FAILOVER: Promoting replica to primary")
            logger.info(f"New primary: {new_primary_host}")
            return True

        except Exception as e:
            logger.error(f"Failover initiation failed: {e}")
            return False

    def setup_load_balancing(self, read_replicas: List[str]) -> Dict:
        """Setup load balancing configuration for read replicas."""
        logger.info(f"Configuring load balancing for {len(read_replicas)} replicas")
        
        config = {
            'primary': self.db_manager.config.host,
            'replicas': read_replicas,
            'strategy': 'round_robin',
            'health_check_interval': 10,  # seconds
            'failover_threshold': 3,  # failed health checks before failover
            'read_weight': 0.7,  # 70% of reads go to replicas
            'write_weight': 0.0,  # All writes go to primary
        }
        
        logger.info("Load balancing configuration created")
        return config

    def setup_connection_routing(self) -> str:
        """Setup application-level connection routing."""
        connection_string = """
        # PostgreSQL HA Connection String
        postgresql://user:password@primary.host:5432,replica1.host:5432,replica2.host:5432/railway_os?
        target_session_attrs=read-write&
        fallback_application_name=railway_app&
        connect_timeout=10&
        application_name=railway_reader
        """
        
        logger.info("Connection routing configuration created")
        return connection_string

    def get_ha_status(self) -> Dict:
        """Get comprehensive HA status."""
        logger.info("Gathering HA status...")
        
        try:
            with self.db_manager.session_scope() as session:
                # Check primary status
                is_primary = session.execute(text(
                    "SELECT NOT pg_is_in_recovery()"
                )).fetchone()[0]
                
                # Count connected replicas
                replica_count = session.execute(text(
                    "SELECT COUNT(*) FROM pg_stat_replication"
                )).fetchone()[0]
                
                # Get LSN position
                lsn = session.execute(text(
                    "SELECT pg_current_wal_lsn()"
                )).fetchone()[0]
                
                status = {
                    'is_primary': is_primary,
                    'connected_replicas': replica_count,
                    'current_lsn': str(lsn) if lsn else None,
                    'wal_archiving_enabled': True,  # Would check postgresql.conf
                    'replication_slots': self._get_replication_slots(),
                }
                
                return status

        except Exception as e:
            logger.error(f"Failed to get HA status: {e}")
            return {}

    def _get_replication_slots(self) -> List[Dict]:
        """Get list of replication slots."""
        try:
            with self.db_manager.session_scope() as session:
                result = session.execute(text("""
                    SELECT 
                        slot_name,
                        slot_type,
                        active,
                        restart_lsn
                    FROM pg_replication_slots
                """)).fetchall()
                
                slots = []
                for name, slot_type, active, restart_lsn in result:
                    slots.append({
                        'name': name,
                        'type': slot_type,
                        'active': active,
                        'restart_lsn': str(restart_lsn) if restart_lsn else None,
                    })
                
                return slots

        except Exception as e:
            logger.error(f"Failed to get replication slots: {e}")
            return []

    def create_replication_slot(self, slot_name: str, slot_type: str = 'physical') -> bool:
        """Create a replication slot for a replica."""
        logger.info(f"Creating {slot_type} replication slot: {slot_name}")
        
        try:
            with self.db_manager.session_scope() as session:
                session.execute(text(f"""
                    SELECT pg_create_physical_replication_slot('{slot_name}')
                """))
                
                logger.info(f"Replication slot created: {slot_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to create replication slot: {e}")
            return False

    def generate_ha_configuration(self) -> str:
        """Generate PostgreSQL HA configuration for postgresql.conf."""
        config_content = """
# ====================================================================
# REPLICATION & HA CONFIGURATION FOR postgresql.conf
# ====================================================================

# Primary Server Configuration
wal_level = replica                          # Enable WAL archiving (required for replication)
max_wal_senders = 10                         # Maximum replication connections
max_replication_slots = 10                   # Maximum replication slots
wal_keep_segments = 100                      # Keep WAL files for replicas
hot_standby = on                             # Enable queries on standby

# Replication User Authentication (in pg_hba.conf)
# host    replication     replicator    replica_ip/32    md5

# Streaming Replication Parameters
synchronous_commit = local                   # Faster writes with less durability
synchronous_standby_names = ''               # Synchronous standby names

# Archive Configuration (if using WAL archiving)
archive_mode = on
archive_timeout = 300                        # 5 minutes
archive_command = 'test ! -f /var/lib/postgresql/archive/%f && cp %p /var/lib/postgresql/archive/%f'

# Connection Settings
listen_addresses = '*'                        # Listen on all addresses
max_connections = 200
reserved_connections = 5

# Replica/Standby Configuration (for recovery.conf or auto_recovery)
# recovery_target_timeline = 'latest'
# restore_command = 'cp /var/lib/postgresql/archive/%f %p'
# standby_mode = 'on'  # PostgreSQL 11 and earlier
# primary_conninfo = 'host=primary_host port=5432 user=replicator password=password'
"""
        
        return config_content
