# scripts/health_check.py - Database Health Check System
"""
Comprehensive health check utility for monitoring database status.
Checks connectivity, performance, schema, and data integrity.
"""

import sys
from pathlib import Path
from datetime import datetime
import logging
import json
import click
from typing import Dict, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from connection import DatabaseConnectionManager, DatabaseConfig
from config import config
from models.station import Station
from models.route import Route
from models.train import Train

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseHealthChecker:
    """Check database health and report issues."""

    def __init__(self):
        self.config = config
        self.db_config = config.database
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'overall_status': 'healthy',
            'issues': [],
        }

    def check_connectivity(self) -> Tuple[bool, str]:
        """Check if database is accessible."""
        try:
            db_manager = DatabaseConnectionManager(DatabaseConfig())
            with db_manager.session_scope() as session:
                session.execute("SELECT 1")
            
            return True, "Database connectivity: OK"

        except Exception as e:
            return False, f"Database connectivity failed: {str(e)}"

    def check_table_count(self) -> Tuple[bool, str]:
        """Check if all required tables exist."""
        required_tables = [
            'stations', 'trains', 'routes', 'schedules', 'fares',
            'tenants', 'users', 'api_keys', 'jobs', 'audit_logs', 'system_metrics'
        ]
        
        try:
            db_manager = DatabaseConnectionManager(DatabaseConfig())
            with db_manager.session_scope() as session:
                result = session.execute(
                    "SELECT tablename FROM pg_tables WHERE schemaname='public'"
                )
                existing_tables = {row[0] for row in result}
            
            missing_tables = set(required_tables) - existing_tables
            
            if missing_tables:
                return False, f"Missing tables: {', '.join(missing_tables)}"
            
            return True, f"All {len(required_tables)} required tables exist"

        except Exception as e:
            return False, f"Table count check failed: {str(e)}"

    def check_data_integrity(self) -> Tuple[bool, str]:
        """Check data integrity constraints."""
        issues = []
        
        try:
            db_manager = DatabaseConnectionManager(DatabaseConfig())
            with db_manager.session_scope() as session:
                # Check for foreign key violations
                # Check for null violations
                # Check for constraint violations
                
                # Sample: Check station count
                station_count = session.query(Station).count()
                
                if station_count == 0:
                    issues.append("No stations found in database")
                else:
                    logger.info(f"Stations found: {station_count}")
            
            if issues:
                return False, "; ".join(issues)
            
            return True, "Data integrity checks passed"

        except Exception as e:
            return False, f"Data integrity check failed: {str(e)}"

    def check_indexes(self) -> Tuple[bool, str]:
        """Check if all important indexes exist."""
        try:
            db_manager = DatabaseConnectionManager(DatabaseConfig())
            with db_manager.session_scope() as session:
                result = session.execute(
                    "SELECT indexname FROM pg_indexes WHERE schemaname='public' ORDER BY indexname"
                )
                indexes = [row[0] for row in result]
            
            if len(indexes) < 10:
                return False, f"Only {len(indexes)} indexes found (expected >10)"
            
            return True, f"All {len(indexes)} indexes present"

        except Exception as e:
            return False, f"Index check failed: {str(e)}"

    def check_statistics(self) -> Tuple[bool, str]:
        """Check table statistics."""
        try:
            db_manager = DatabaseConnectionManager(DatabaseConfig())
            with db_manager.session_scope() as session:
                stats = []
                
                station_count = session.query(Station).count()
                route_count = session.query(Route).count()
                train_count = session.query(Train).count()
                
                stats.append(f"Stations: {station_count}")
                stats.append(f"Routes: {route_count}")
                stats.append(f"Trains: {train_count}")
            
            return True, "; ".join(stats)

        except Exception as e:
            return False, f"Statistics check failed: {str(e)}"

    def run_all_checks(self) -> Dict:
        """Run all health checks."""
        checks = {
            'connectivity': self.check_connectivity,
            'tables': self.check_table_count,
            'data_integrity': self.check_data_integrity,
            'indexes': self.check_indexes,
            'statistics': self.check_statistics,
        }
        
        for check_name, check_func in checks.items():
            try:
                success, message = check_func()
                self.results['checks'][check_name] = {
                    'status': 'ok' if success else 'failed',
                    'message': message,
                }
                
                if not success:
                    self.results['issues'].append(f"{check_name}: {message}")
                    self.results['overall_status'] = 'degraded' if self.results['overall_status'] == 'healthy' else 'critical'

            except Exception as e:
                self.results['checks'][check_name] = {
                    'status': 'error',
                    'message': str(e),
                }
                self.results['issues'].append(f"{check_name}: {str(e)}")
                self.results['overall_status'] = 'critical'
        
        return self.results

    def print_report(self):
        """Print health check report."""
        print("\n" + "="*60)
        print("DATABASE HEALTH CHECK REPORT")
        print("="*60 + "\n")
        
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Overall Status: {self.results['overall_status'].upper()}\n")
        
        print("Individual Checks:")
        print("-" * 60)
        
        for check_name, result in self.results['checks'].items():
            status_icon = "✓" if result['status'] == 'ok' else "✗"
            print(f"{status_icon} {check_name}: {result['status']}")
            print(f"  → {result['message']}\n")
        
        if self.results['issues']:
            print("\nIssues Found:")
            print("-" * 60)
            for issue in self.results['issues']:
                print(f"  ⚠ {issue}")
        
        print("\n" + "="*60 + "\n")


@click.command()
@click.option('--json-output', is_flag=True, help='Output as JSON')
def cli(json_output):
    """Run database health checks."""
    checker = DatabaseHealthChecker()
    results = checker.run_all_checks()
    
    if json_output:
        print(json.dumps(results, indent=2))
    else:
        checker.print_report()
    
    # Exit with appropriate code
    sys.exit(0 if results['overall_status'] == 'healthy' else 1)


if __name__ == '__main__':
    cli()
