# scripts/seed_database.py - Initial Data Seeding
"""
Database seeding utility to load initial data.
Supports CSV imports and programmatic data creation.
"""

import sys
from pathlib import Path
import csv
import logging
import click
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from connection import DatabaseConnectionManager, DatabaseConfig
from models.station import Station
from models.train import Train
from models.tenant import Tenant
from models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseSeeder:
    """Seed database with initial data."""

    def __init__(self):
        self.db_manager = DatabaseConnectionManager(DatabaseConfig())

    def seed_sample_data(self) -> bool:
        """Seed with sample railway data."""
        try:
            with self.db_manager.session_scope() as session:
                # Create default tenant
                tenant = Tenant(
                    name="Indian Railways",
                    api_key="default-api-key-change-me"
                )
                session.add(tenant)
                session.commit()
                
                tenant_id = tenant.id
                logger.info(f"Created tenant: {tenant.name}")
                
                # Create admin user
                admin_user = User(
                    tenant_id=tenant_id,
                    email="admin@railway.example.com",
                    hashed_password="hashed_password_here",
                    role="admin"
                )
                session.add(admin_user)
                session.commit()
                logger.info("Created admin user")
                
                # Add sample stations
                stations_data = [
                    {"code": "NDLS", "name": "New Delhi", "latitude": 28.6415, "longitude": 77.2200, "zone": "NR"},
                    {"code": "BCT", "name": "Mumbai Central", "latitude": 18.9690, "longitude": 72.8194, "zone": "WR"},
                    {"code": "HWH", "name": "Howrah Junction", "latitude": 22.5832, "longitude": 88.3378, "zone": "ER"},
                    {"code": "CSMT", "name": "CST Mumbai", "latitude": 18.9631, "longitude": 72.8358, "zone": "WR"},
                    {"code": "CNB", "name": "Kanpur Central", "latitude": 26.4499, "longitude": 80.3319, "zone": "NR"},
                    {"code": "LKO", "name": "Lucknow Central", "latitude": 26.8444, "longitude": 80.9178, "zone": "NR"},
                ]
                
                for station_data in stations_data:
                    station = Station(**station_data, tenant_id=tenant_id, is_active=True)
                    session.add(station)
                
                session.commit()
                logger.info(f"Created {len(stations_data)} sample stations")
                
                # Add sample trains
                trains_data = [
                    {"number": "12001", "name": "Rajdhani Express", "type": "rajdhani", "operator": "NR"},
                    {"number": "12005", "name": "Bhagirath Express", "type": "rajdhani", "operator": "NR"},
                    {"number": "22877", "name": "Sealdah Rajdhani", "type": "rajdhani", "operator": "ER"},
                    {"number": "15002", "name": "Mandalay Express", "type": "express", "operator": "NR"},
                ]
                
                for train_data in trains_data:
                    train = Train(**train_data, tenant_id=tenant_id, is_active=True)
                    session.add(train)
                
                session.commit()
                logger.info(f"Created {len(trains_data)} sample trains")
                
                return True

        except Exception as e:
            logger.error(f"Seeding failed: {e}")
            return False

    def load_csv_stations(self, csv_file: str) -> bool:
        """Load stations from CSV file."""
        try:
            with self.db_manager.session_scope() as session:
                # Get default tenant
                tenant = session.query(Tenant).first()
                if not tenant:
                    logger.error("No tenant found. Create one first.")
                    return False
                
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    count = 0
                    
                    for row in reader:
                        station = Station(
                            code=row['code'],
                            name=row['name'],
                            latitude=float(row['latitude']),
                            longitude=float(row['longitude']),
                            zone=row.get('zone', 'NR'),
                            state=row.get('state', ''),
                            tenant_id=tenant.id,
                            is_active=True
                        )
                        session.add(station)
                        count += 1
                    
                    session.commit()
                    logger.info(f"Loaded {count} stations from {csv_file}")
                    return True

        except Exception as e:
            logger.error(f"CSV loading failed: {e}")
            return False

    def load_csv_trains(self, csv_file: str) -> bool:
        """Load trains from CSV file."""
        try:
            with self.db_manager.session_scope() as session:
                # Get default tenant
                tenant = session.query(Tenant).first()
                if not tenant:
                    logger.error("No tenant found. Create one first.")
                    return False
                
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    count = 0
                    
                    for row in reader:
                        train = Train(
                            number=row['number'],
                            name=row['name'],
                            type=row.get('type', 'express'),
                            operator=row.get('operator', 'IR'),
                            total_coaches=int(row.get('coaches', 18)),
                            max_speed_kmph=int(row.get('max_speed', 120)),
                            tenant_id=tenant.id,
                            is_active=True
                        )
                        session.add(train)
                        count += 1
                    
                    session.commit()
                    logger.info(f"Loaded {count} trains from {csv_file}")
                    return True

        except Exception as e:
            logger.error(f"CSV loading failed: {e}")
            return False


@click.command()
@click.option('--sample', is_flag=True, help='Seed with sample data')
@click.option('--stations-csv', help='Path to stations CSV file')
@click.option('--trains-csv', help='Path to trains CSV file')
def cli(sample, stations_csv, trains_csv):
    """Seed database with initial data."""
    seeder = DatabaseSeeder()
    
    if sample:
        if seeder.seed_sample_data():
            click.secho("✓ Sample data seeded successfully", fg='green')
        else:
            click.secho("✗ Sample data seeding failed", fg='red')
            sys.exit(1)
    
    if stations_csv:
        if seeder.load_csv_stations(stations_csv):
            click.secho(f"✓ Stations loaded from {stations_csv}", fg='green')
        else:
            click.secho("✗ Station loading failed", fg='red')
            sys.exit(1)
    
    if trains_csv:
        if seeder.load_csv_trains(trains_csv):
            click.secho(f"✓ Trains loaded from {trains_csv}", fg='green')
        else:
            click.secho("✗ Train loading failed", fg='red')
            sys.exit(1)


if __name__ == '__main__':
    cli()
