# scripts/advanced_monitoring.py - Advanced Database Monitoring & Alerting
"""
Comprehensive monitoring system for database performance, security, and health.
Includes slow query detection, connection monitoring, alerting, and dashboards.
"""

import sys
from pathlib import Path
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import click

sys.path.insert(0, str(Path(__file__).parent.parent))

from connection import DatabaseConnectionManager, DatabaseConfig
from config import config
from models.system import SystemMetric

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedMonitor:
    """Advanced database monitoring with alerts and metrics."""

    def __init__(self):
        self.db_manager = DatabaseConnectionManager(DatabaseConfig())
        self.config = config

    def detect_slow_queries(self, threshold_ms: float = 1000) -> List[Dict]:
        """Detect slow-running queries."""
        logger.info(f"Detecting queries slower than {threshold_ms}ms...")
        
        try:
            with self.db_manager.session_scope() as session:
                result = session.execute(f"""
                    SELECT 
                        query,
                        mean_exec_time as avg_ms,
                        calls,
                        total_exec_time as total_ms
                    FROM pg_stat_statements
                    WHERE mean_exec_time > {threshold_ms}
                    ORDER BY mean_exec_time DESC
                    LIMIT 20
                """)
                
                slow_queries = []
                for query, avg_ms, calls, total_ms in result:
                    slow_queries.append({
                        'query': query[:100],  # First 100 chars
                        'avg_execution_ms': round(avg_ms, 2),
                        'call_count': calls,
                        'total_execution_ms': round(total_ms, 2),
                    })
                
                logger.info(f"Found {len(slow_queries)} slow queries")
                return slow_queries

        except Exception as e:
            logger.error(f"Slow query detection failed: {e}")
            return []

    def monitor_connection_pool(self) -> Dict:
        """Monitor database connection pool status."""
        try:
            with self.db_manager.session_scope() as session:
                result = session.execute("""
                    SELECT 
                        datname,
                        count(*) as total_connections,
                        sum(CASE WHEN state = 'active' THEN 1 ELSE 0 END) as active,
                        sum(CASE WHEN state = 'idle' THEN 1 ELSE 0 END) as idle,
                        sum(CASE WHEN state = 'idle in transaction' THEN 1 ELSE 0 END) as idle_in_tx
                    FROM pg_stat_activity
                    GROUP BY datname
                """)
                
                pool_status = {}
                for db, total, active, idle, idle_in_tx in result:
                    pool_status[db] = {
                        'total_connections': total,
                        'active_connections': active or 0,
                        'idle_connections': idle or 0,
                        'idle_in_transaction': idle_in_tx or 0,
                        'utilization_percent': round((active or 0) / self.config.database.pool_size * 100, 2),
                    }
                
                logger.info("Connection pool status retrieved")
                return pool_status

        except Exception as e:
            logger.error(f"Connection monitoring failed: {e}")
            return {}

    def detect_locks_and_deadlocks(self) -> Dict:
        """Detect locks and potential deadlocks."""
        try:
            with self.db_manager.session_scope() as session:
                # Detect blocking locks
                blocking = session.execute("""
                    SELECT 
                        blocked_locks.pid AS blocked_pid,
                        blocked_locks.usename AS blocked_user,
                        blocking_locks.pid AS blocking_pid,
                        blocking_locks.usename AS blocking_user,
                        blocked_locks.query AS blocked_statement,
                        blocking_locks.query AS blocking_statement
                    FROM pg_stat_activity blocked_locks
                    JOIN pg_stat_activity blocking_locks ON blocking_locks.locktype IS NOT NULL
                    AND blocking_locks.pid = ANY(pg_blocking_pids(blocked_locks.pid))
                """).fetchall()
                
                locks = [
                    {
                        'blocked_pid': row[0],
                        'blocked_user': row[1],
                        'blocking_pid': row[2],
                        'blocking_user': row[3],
                    }
                    for row in blocking
                ]
                
                logger.info(f"Detected {len(locks)} blocking locks")
                return {'blocking_locks': locks}

        except Exception as e:
            logger.error(f"Lock detection failed: {e}")
            return {}

    def monitor_table_sizes(self) -> List[Dict]:
        """Monitor table sizes and growth."""
        try:
            with self.db_manager.session_scope() as session:
                result = session.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """)
                
                table_sizes = []
                for schema, table, size_str, size_bytes in result:
                    table_sizes.append({
                        'table': table,
                        'size_readable': size_str,
                        'size_bytes': size_bytes,
                    })
                
                logger.info(f"Analyzed {len(table_sizes)} tables")
                return table_sizes

        except Exception as e:
            logger.error(f"Table size monitoring failed: {e}")
            return []

    def monitor_disk_usage(self) -> Dict:
        """Monitor database disk usage."""
        try:
            with self.db_manager.session_scope() as session:
                result = session.execute("""
                    SELECT 
                        datname,
                        pg_size_pretty(pg_database_size(datname)) as size,
                        pg_database_size(datname) as size_bytes
                    FROM pg_database
                    WHERE datname NOT IN ('template0', 'template1', 'postgres')
                """)
                
                disk_usage = {}
                for db, size_str, size_bytes in result:
                    disk_usage[db] = {
                        'size_readable': size_str,
                        'size_bytes': size_bytes,
                    }
                
                return disk_usage

        except Exception as e:
            logger.error(f"Disk usage monitoring failed: {e}")
            return {}

    def check_index_efficiency(self) -> List[Dict]:
        """Check for unused or inefficient indexes."""
        try:
            with self.db_manager.session_scope() as session:
                # Find unused indexes
                unused = session.execute("""
                    SELECT 
                        schemaname,
                        indexname,
                        idx_scan
                    FROM pg_stat_user_indexes
                    WHERE idx_scan = 0 AND indexrelname NOT LIKE 'pg_toast%'
                    ORDER BY idx_blks_read DESC, idx_blks_hit DESC
                """)
                
                unused_indexes = []
                for schema, index, scans in unused:
                    unused_indexes.append({
                        'index': index,
                        'scans': scans,
                        'status': 'Unused - consider dropping',
                    })
                
                logger.info(f"Found {len(unused_indexes)} potentially unused indexes")
                return unused_indexes

        except Exception as e:
            logger.error(f"Index efficiency check failed: {e}")
            return []

    def collect_metrics(self) -> Dict:
        """Collect comprehensive monitoring metrics."""
        timestamp = datetime.now()
        
        metrics = {
            'timestamp': timestamp.isoformat(),
            'slow_queries': self.detect_slow_queries(self.config.monitoring.slow_query_threshold_ms),
            'connection_pool': self.monitor_connection_pool(),
            'locks': self.detect_locks_and_deadlocks(),
            'table_sizes': self.monitor_table_sizes(),
            'disk_usage': self.monitor_disk_usage(),
            'index_efficiency': self.check_index_efficiency(),
        }
        
        return metrics

    def generate_alert(self, alert_type: str, severity: str, message: str, metric_value: float = None):
        """Generate an alert for critical conditions."""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'severity': severity,  # info, warning, critical
            'message': message,
            'metric_value': metric_value,
        }
        
        logger.log(
            logging.CRITICAL if severity == 'critical' else logging.WARNING,
            f"[{alert_type.upper()}] {message}"
        )
        
        return alert

    def check_thresholds(self, metrics: Dict) -> List[Dict]:
        """Check metrics against configured thresholds."""
        alerts = []
        
        # Check connection pool utilization
        for db, pool_info in metrics['connection_pool'].items():
            util = pool_info['utilization_percent']
            if util > self.config.monitoring.alert_threshold_cpu:  # Reuse as threshold
                alerts.append(self.generate_alert(
                    'CONNECTION_POOL',
                    'warning',
                    f"Connection pool utilization at {util}%",
                    util
                ))
        
        # Check slow queries
        if len(metrics['slow_queries']) > 5:
            alerts.append(self.generate_alert(
                'SLOW_QUERIES',
                'warning',
                f"Found {len(metrics['slow_queries'])} slow-running queries",
                len(metrics['slow_queries'])
            ))
        
        # Check blocking locks
        if metrics['locks']['blocking_locks']:
            alerts.append(self.generate_alert(
                'BLOCKING_LOCKS',
                'critical',
                f"Detected {len(metrics['locks']['blocking_locks'])} blocking locks",
                len(metrics['locks']['blocking_locks'])
            ))
        
        return alerts


@click.command()
@click.option('--detailed', is_flag=True, help='Show detailed metrics')
@click.option('--export-json', help='Export metrics to JSON file')
def cli(detailed, export_json):
    """Run advanced database monitoring."""
    monitor = AdvancedMonitor()
    
    click.secho("\n" + "="*70, fg='cyan')
    click.secho("ADVANCED DATABASE MONITORING REPORT", fg='cyan', bold=True)
    click.secho("="*70 + "\n", fg='cyan')
    
    metrics = monitor.collect_metrics()
    alerts = monitor.check_thresholds(metrics)
    
    # Display results
    click.secho(f"Timestamp: {metrics['timestamp']}", fg='white')
    click.secho(f"Alerts: {len(alerts)}\n", fg='yellow' if alerts else 'green')
    
    if alerts:
        click.secho("⚠ ACTIVE ALERTS:", fg='yellow', bold=True)
        for alert in alerts:
            click.secho(f"  [{alert['severity'].upper()}] {alert['message']}", fg='red')
        click.secho()
    
    # Connection pool
    click.secho("Connection Pool Status:", fg='cyan', bold=True)
    for db, info in metrics['connection_pool'].items():
        click.secho(f"  {db}: {info['active_connections']}/{info['total_connections']} active ({info['utilization_percent']}%)")
    click.secho()
    
    # Slow queries
    if metrics['slow_queries']:
        click.secho(f"Top Slow Queries (>{monitor.config.monitoring.slow_query_threshold_ms}ms):", fg='cyan', bold=True)
        for i, query in enumerate(metrics['slow_queries'][:5], 1):
            click.secho(f"  {i}. {query['avg_execution_ms']}ms (called {query['call_count']} times)")
        click.secho()
    
    # Table sizes
    if metrics['table_sizes']:
        click.secho("Largest Tables:", fg='cyan', bold=True)
        for table in metrics['table_sizes'][:5]:
            click.secho(f"  {table['table']}: {table['size_readable']}")
        click.secho()
    
    if detailed:
        click.secho("Full Metrics JSON:", fg='cyan', bold=True)
        click.echo(json.dumps(metrics, indent=2))
    
    if export_json:
        with open(export_json, 'w') as f:
            json.dump(metrics, f, indent=2)
        click.secho(f"\n✓ Metrics exported to {export_json}", fg='green')
    
    click.secho("="*70 + "\n", fg='cyan')


if __name__ == '__main__':
    cli()
