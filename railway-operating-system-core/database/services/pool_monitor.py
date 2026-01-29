# services/pool_monitor.py - Connection Pool Monitoring & Optimization
"""
Real-time connection pool monitoring, bottleneck detection, and performance optimization.
Tracks connection utilization, identifies leaks, and provides alerting.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

from connection import DatabaseConnectionManager, DatabaseConfig
from sqlalchemy import text
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PoolMetric:
    """Single connection pool metric snapshot."""
    timestamp: datetime
    total_connections: int
    active_connections: int
    idle_connections: int
    waiting_requests: int
    utilization_percent: float
    response_time_ms: float


class PoolMonitor:
    """Monitor and optimize database connection pool."""

    def __init__(self):
        self.db_manager = DatabaseConnectionManager(DatabaseConfig())
        self.metrics_history: List[PoolMetric] = []
        self.alert_thresholds = {
            'utilization_critical': 90,  # %
            'utilization_warning': 75,   # %
            'connection_wait_time': 1000,  # ms
            'idle_timeout': 300,  # seconds
        }

    def get_pool_status(self) -> Dict:
        """Get current connection pool status."""
        logger.info("Fetching connection pool status...")
        
        try:
            with self.db_manager.session_scope() as session:
                result = session.execute(text("""
                    SELECT 
                        datname,
                        count(*) as total_connections,
                        sum(CASE WHEN state = 'active' THEN 1 ELSE 0 END) as active,
                        sum(CASE WHEN state = 'idle' THEN 1 ELSE 0 END) as idle,
                        sum(CASE WHEN state = 'idle in transaction' THEN 1 ELSE 0 END) as idle_in_tx,
                        sum(CASE WHEN wait_event IS NOT NULL THEN 1 ELSE 0 END) as waiting
                    FROM pg_stat_activity
                    WHERE datname IS NOT NULL
                    GROUP BY datname
                """)).fetchall()
                
                status = {}
                for db, total, active, idle, idle_in_tx, waiting in result:
                    active_count = active or 0
                    utilization = round((active_count / self.db_manager.config.pool_size) * 100, 2)
                    
                    status[db] = {
                        'total': total,
                        'active': active_count,
                        'idle': idle or 0,
                        'idle_in_transaction': idle_in_tx or 0,
                        'waiting': waiting or 0,
                        'utilization_percent': utilization,
                        'pool_size': self.db_manager.config.pool_size,
                        'max_overflow': self.db_manager.config.max_overflow,
                    }
                
                return status

        except Exception as e:
            logger.error(f"Failed to get pool status: {e}")
            return {}

    def detect_connection_leaks(self) -> List[Dict]:
        """Detect potential connection leaks."""
        logger.info("Analyzing for connection leaks...")
        
        try:
            with self.db_manager.session_scope() as session:
                # Find idle connections lasting too long
                result = session.execute(text(f"""
                    SELECT 
                        pid, usename, datname, state,
                        EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - state_change)) as idle_time,
                        query, state_change
                    FROM pg_stat_activity
                    WHERE state = 'idle'
                    AND state_change < CURRENT_TIMESTAMP - INTERVAL '{self.alert_thresholds["idle_timeout"]} seconds'
                    ORDER BY state_change
                """)).fetchall()
                
                leaks = []
                for pid, user, db, state, idle_time, query, change_time in result:
                    leaks.append({
                        'pid': pid,
                        'user': user,
                        'database': db,
                        'idle_time_seconds': int(idle_time),
                        'last_query': query[:100] if query else None,
                        'state_changed_at': change_time.isoformat(),
                        'risk_level': 'HIGH' if idle_time > self.alert_thresholds['idle_timeout'] * 2 else 'MEDIUM',
                    })
                
                logger.warning(f"Found {len(leaks)} potential connection leaks")
                return leaks

        except Exception as e:
            logger.error(f"Failed to detect connection leaks: {e}")
            return []

    def identify_bottlenecks(self) -> Dict:
        """Identify performance bottlenecks in connection handling."""
        logger.info("Identifying connection bottlenecks...")
        
        bottlenecks = {
            'high_lock_contention': [],
            'slow_queries': [],
            'transaction_aborts': [],
            'connection_timeouts': [],
        }
        
        try:
            with self.db_manager.session_scope() as session:
                # High lock contention
                lock_result = session.execute(text("""
                    SELECT 
                        relation::regclass as table_name,
                        mode, count(*) as count
                    FROM pg_locks
                    WHERE NOT granted
                    GROUP BY relation, mode
                    HAVING count(*) > 1
                    ORDER BY count DESC
                """)).fetchall()
                
                for table, mode, count in lock_result:
                    bottlenecks['high_lock_contention'].append({
                        'table': str(table),
                        'lock_mode': mode,
                        'waiting_count': count,
                    })
                
                # Slow running transactions
                slow_result = session.execute(text("""
                    SELECT 
                        pid, usename,
                        EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - xact_start)) as duration_sec,
                        query
                    FROM pg_stat_activity
                    WHERE xact_start IS NOT NULL
                    AND CURRENT_TIMESTAMP - xact_start > INTERVAL '1 minute'
                    ORDER BY xact_start
                """)).fetchall()
                
                for pid, user, duration, query in slow_result:
                    bottlenecks['slow_queries'].append({
                        'pid': pid,
                        'user': user,
                        'duration_seconds': int(duration),
                        'query': query[:100] if query else None,
                    })
                
                return bottlenecks

        except Exception as e:
            logger.error(f"Failed to identify bottlenecks: {e}")
            return bottlenecks

    def get_connection_age_distribution(self) -> Dict:
        """Analyze age distribution of connections."""
        logger.info("Analyzing connection age distribution...")
        
        try:
            with self.db_manager.session_scope() as session:
                result = session.execute(text("""
                    SELECT 
                        CASE 
                            WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - backend_start)) < 60 
                                THEN '< 1 minute'
                            WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - backend_start)) < 300 
                                THEN '1-5 minutes'
                            WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - backend_start)) < 3600 
                                THEN '5 min - 1 hour'
                            ELSE '> 1 hour'
                        END as age_range,
                        COUNT(*) as count,
                        SUM(CASE WHEN state = 'active' THEN 1 ELSE 0 END) as active
                    FROM pg_stat_activity
                    WHERE datname IS NOT NULL
                    GROUP BY age_range
                    ORDER BY count DESC
                """)).fetchall()
                
                distribution = {}
                for age_range, count, active in result:
                    distribution[age_range] = {
                        'total': count,
                        'active': active or 0,
                        'idle': count - (active or 0),
                    }
                
                return distribution

        except Exception as e:
            logger.error(f"Failed to analyze connection age: {e}")
            return {}

    def get_user_connection_stats(self) -> List[Dict]:
        """Get connection statistics by user."""
        logger.info("Gathering per-user connection statistics...")
        
        try:
            with self.db_manager.session_scope() as session:
                result = session.execute(text("""
                    SELECT 
                        usename,
                        COUNT(*) as total_connections,
                        SUM(CASE WHEN state = 'active' THEN 1 ELSE 0 END) as active,
                        SUM(CASE WHEN state = 'idle' THEN 1 ELSE 0 END) as idle,
                        MAX(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - backend_start)))::int as oldest_connection_sec
                    FROM pg_stat_activity
                    WHERE datname IS NOT NULL
                    GROUP BY usename
                    ORDER BY total_connections DESC
                """)).fetchall()
                
                stats = []
                for user, total, active, idle, oldest in result:
                    stats.append({
                        'username': user,
                        'total_connections': total,
                        'active': active or 0,
                        'idle': idle or 0,
                        'oldest_connection_seconds': oldest or 0,
                    })
                
                return stats

        except Exception as e:
            logger.error(f"Failed to get user connection stats: {e}")
            return []

    def measure_response_time(self) -> float:
        """Measure average query response time."""
        logger.info("Measuring response time...")
        
        try:
            start = time.time()
            
            with self.db_manager.session_scope() as session:
                session.execute(text("SELECT 1"))
            
            elapsed_ms = (time.time() - start) * 1000
            logger.info(f"Response time: {elapsed_ms:.2f}ms")
            return elapsed_ms

        except Exception as e:
            logger.error(f"Failed to measure response time: {e}")
            return 0.0

    def collect_metric_snapshot(self) -> Optional[PoolMetric]:
        """Collect a single metric snapshot."""
        pool_status = self.get_pool_status()
        response_time = self.measure_response_time()
        
        if not pool_status:
            return None
        
        # Aggregate across all databases
        total = sum(s['total'] for s in pool_status.values())
        active = sum(s['active'] for s in pool_status.values())
        idle = sum(s['idle'] for s in pool_status.values())
        waiting = sum(s['waiting'] for s in pool_status.values())
        
        utilization = round((active / (self.db_manager.config.pool_size or 1)) * 100, 2)
        
        metric = PoolMetric(
            timestamp=datetime.now(),
            total_connections=total,
            active_connections=active,
            idle_connections=idle,
            waiting_requests=waiting,
            utilization_percent=utilization,
            response_time_ms=response_time,
        )
        
        self.metrics_history.append(metric)
        return metric

    def check_alert_conditions(self, metric: PoolMetric) -> List[Dict]:
        """Check if metric triggers any alerts."""
        alerts = []
        
        if metric.utilization_percent >= self.alert_thresholds['utilization_critical']:
            alerts.append({
                'severity': 'CRITICAL',
                'type': 'POOL_SATURATION',
                'message': f"Connection pool at {metric.utilization_percent}% utilization",
                'value': metric.utilization_percent,
            })
        elif metric.utilization_percent >= self.alert_thresholds['utilization_warning']:
            alerts.append({
                'severity': 'WARNING',
                'type': 'HIGH_UTILIZATION',
                'message': f"Connection pool at {metric.utilization_percent}% utilization",
                'value': metric.utilization_percent,
            })
        
        if metric.response_time_ms > self.alert_thresholds['connection_wait_time']:
            alerts.append({
                'severity': 'WARNING',
                'type': 'SLOW_RESPONSE',
                'message': f"Response time: {metric.response_time_ms:.2f}ms",
                'value': metric.response_time_ms,
            })
        
        if metric.waiting_requests > 0:
            alerts.append({
                'severity': 'WARNING',
                'type': 'WAITING_REQUESTS',
                'message': f"{metric.waiting_requests} requests waiting for connections",
                'value': metric.waiting_requests,
            })
        
        return alerts

    def get_performance_trends(self, hours: int = 1) -> Dict:
        """Analyze performance trends over time."""
        logger.info(f"Analyzing trends over past {hours} hours...")
        
        if not self.metrics_history:
            return {}
        
        # Filter recent metrics
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        if not recent:
            return {}
        
        utilizations = [m.utilization_percent for m in recent]
        response_times = [m.response_time_ms for m in recent]
        
        return {
            'samples': len(recent),
            'utilization': {
                'min': min(utilizations),
                'max': max(utilizations),
                'avg': sum(utilizations) / len(utilizations),
            },
            'response_time_ms': {
                'min': min(response_times),
                'max': max(response_times),
                'avg': sum(response_times) / len(response_times),
            },
        }

    def generate_optimization_recommendations(self) -> List[str]:
        """Generate recommendations for pool optimization."""
        logger.info("Generating optimization recommendations...")
        
        recommendations = []
        
        # Get current status
        pool_status = self.get_pool_status()
        if not pool_status:
            return recommendations
        
        # Check utilization
        max_util = max((s['utilization_percent'] for s in pool_status.values()), default=0)
        if max_util > 80:
            recommendations.append(
                f"Consider increasing pool_size from {self.db_manager.config.pool_size} "
                f"(current utilization: {max_util:.1f}%)"
            )
        
        # Check for leaks
        leaks = self.detect_connection_leaks()
        if leaks:
            recommendations.append(
                f"Found {len(leaks)} potentially leaked connections. "
                f"Review application error handling and connection cleanup."
            )
        
        # Check bottlenecks
        bottlenecks = self.identify_bottlenecks()
        if bottlenecks['high_lock_contention']:
            recommendations.append(
                "High lock contention detected. "
                "Review transaction isolation levels and query patterns."
            )
        
        if bottlenecks['slow_queries']:
            recommendations.append(
                f"Found {len(bottlenecks['slow_queries'])} slow transactions. "
                f"Analyze and optimize long-running queries."
            )
        
        return recommendations

    def create_pool_monitoring_dashboard(self) -> str:
        """Generate monitoring dashboard content."""
        dashboard = """
# Connection Pool Monitoring Dashboard

## Key Metrics
- **Total Connections**: Count of all connections to database
- **Active Connections**: Connections currently executing queries
- **Idle Connections**: Idle but available connections
- **Utilization**: (Active / Pool Size) * 100%
- **Response Time**: Time to execute test query

## Status Indicators
- 🟢 Green (0-75%): Normal operation
- 🟡 Yellow (75-90%): High utilization, monitor closely
- 🔴 Red (>90%): Critical, connection pool saturated

## Common Issues & Solutions

### High Utilization (>85%)
- Increase `pool_size` configuration
- Optimize slow queries reducing query duration
- Review application for connection leak patterns
- Consider connection pooling at application layer (pgBouncer)

### Connection Leaks
- Connections remain idle for extended periods (>5 min)
- Indicates improper connection cleanup in application
- Review try/finally blocks around database operations
- Implement connection timeout mechanisms

### Slow Response Times
- Individual queries taking >1000ms
- Check query execution plans
- Add missing indexes
- Review table scan operations

### Lock Contention
- Waiting connections due to row/table locks
- Review transaction isolation levels
- Reduce transaction duration
- Batch operations efficiently

### Connection Pool Exhaustion
- All connections in use, new requests queuing
- Application demands exceed pool size
- Increase pool_size or implement request queuing
- Profile application connection usage patterns
"""
        
        return dashboard
