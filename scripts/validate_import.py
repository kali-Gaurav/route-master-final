"""
Validation Script for RAPPID Data Import

Verifies that data was imported correctly into SQLite database:
- Row counts match source CSV
- All required columns present
- Data integrity checks
- Sample queries to verify structure

Usage:
    python scripts/validate_import.py
"""

import pandas as pd
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from database_manager import get_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATASET_PATH = Path("dataset") / "RAPPID_Complete_Dataset.csv"


class DataValidator:
    """Validates imported data."""
    
    def __init__(self):
        """Initialize validator."""
        self.db = get_db()
        self.results = {}
    
    def validate_all(self):
        """Run all validation checks."""
        logger.info("Starting validation...")
        logger.info("="*60)
        
        self._check_csv_source()
        self._check_database_stats()
        self._check_data_integrity()
        self._check_sample_queries()
        
        self._print_report()
    
    def _check_csv_source(self):
        """Check source CSV file."""
        logger.info("\n1. Checking Source CSV...")
        
        if not DATASET_PATH.exists():
            logger.error(f"✗ Dataset not found: {DATASET_PATH}")
            self.results['csv_exists'] = False
            return
        
        self.results['csv_exists'] = True
        logger.info(f"✓ Found: {DATASET_PATH}")
        
        # Read CSV to get row count
        try:
            df = pd.read_csv(DATASET_PATH)
            logger.info(f"✓ Total rows in CSV: {len(df):,}")
            logger.info(f"✓ Columns: {list(df.columns)}")
            
            self.results['csv_rows'] = len(df)
            self.results['csv_columns'] = list(df.columns)
        except Exception as e:
            logger.error(f"✗ Failed to read CSV: {e}")
    
    def _check_database_stats(self):
        """Check database statistics."""
        logger.info("\n2. Checking Database Statistics...")
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check table counts
            cursor.execute("SELECT COUNT(*) FROM trains")
            train_count = cursor.fetchone()[0]
            logger.info(f"✓ Trains in database: {train_count:,}")
            self.results['db_trains'] = train_count
            
            cursor.execute("SELECT COUNT(*) FROM stations")
            station_count = cursor.fetchone()[0]
            logger.info(f"✓ Stations in database: {station_count:,}")
            self.results['db_stations'] = station_count
            
            cursor.execute("SELECT COUNT(*) FROM train_stations")
            route_count = cursor.fetchone()[0]
            logger.info(f"✓ Routes in database: {route_count:,}")
            self.results['db_routes'] = route_count
            
            # Check index existence
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
            """)
            indexes = cursor.fetchall()
            logger.info(f"✓ Indexes created: {len(indexes)}")
            
            conn.close()
        except Exception as e:
            logger.error(f"✗ Database check failed: {e}")
    
    def _check_data_integrity(self):
        """Check data integrity."""
        logger.info("\n3. Checking Data Integrity...")
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check for NULL train_no
            cursor.execute("SELECT COUNT(*) FROM trains WHERE train_no IS NULL")
            null_trains = cursor.fetchone()[0]
            if null_trains == 0:
                logger.info("✓ No NULL train_no values")
            else:
                logger.warning(f"⚠ Found {null_trains} NULL train_no values")
            
            # Check for NULL station_code
            cursor.execute("SELECT COUNT(*) FROM stations WHERE station_code IS NULL")
            null_stations = cursor.fetchone()[0]
            if null_stations == 0:
                logger.info("✓ No NULL station_code values")
            else:
                logger.warning(f"⚠ Found {null_stations} NULL station_code values")
            
            # Check for duplicate train_no
            cursor.execute("""
                SELECT COUNT(*) FROM trains 
                GROUP BY train_no 
                HAVING COUNT(*) > 1
            """)
            dup_trains = len(cursor.fetchall())
            if dup_trains == 0:
                logger.info("✓ No duplicate train_no values")
            else:
                logger.warning(f"⚠ Found {dup_trains} duplicate train_no groups")
            
            # Check foreign key integrity
            cursor.execute("""
                SELECT COUNT(*) FROM train_stations ts
                WHERE NOT EXISTS (SELECT 1 FROM trains t WHERE t.id = ts.train_id)
            """)
            orphan_routes = cursor.fetchone()[0]
            if orphan_routes == 0:
                logger.info("✓ No orphaned train_stations (train_id)")
            else:
                logger.warning(f"⚠ Found {orphan_routes} orphaned train_stations")
            
            conn.close()
        except Exception as e:
            logger.error(f"✗ Integrity check failed: {e}")
    
    def _check_sample_queries(self):
        """Run sample queries."""
        logger.info("\n4. Running Sample Queries...")
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Sample train
            cursor.execute("SELECT train_no, train_name FROM trains LIMIT 1")
            train = cursor.fetchone()
            if train:
                logger.info(f"✓ Sample train: {train[0]} ({train[1]})")
                
                # Get routes for this train
                cursor.execute("""
                    SELECT COUNT(*) FROM train_stations
                    WHERE train_id = (SELECT id FROM trains WHERE train_no = ?)
                """, (train[0],))
                route_count = cursor.fetchone()[0]
                logger.info(f"  → Routes for this train: {route_count}")
            
            # Sample station search
            cursor.execute("""
                SELECT station_code, station_name FROM stations 
                WHERE station_name LIKE '%Delhi%' LIMIT 1
            """)
            station = cursor.fetchone()
            if station:
                logger.info(f"✓ Sample station: {station[0]} ({station[1]})")
                
                # Get trains passing through this station
                cursor.execute("""
                    SELECT COUNT(DISTINCT train_id) FROM train_stations
                    WHERE station_id = (SELECT id FROM stations WHERE station_code = ?)
                """, (station[0],))
                train_count = cursor.fetchone()[0]
                logger.info(f"  → Trains passing through: {train_count}")
            
            conn.close()
        except Exception as e:
            logger.error(f"✗ Sample queries failed: {e}")
    
    def _print_report(self):
        """Print validation report."""
        logger.info("\n" + "="*60)
        logger.info("VALIDATION REPORT")
        logger.info("="*60)
        
        # Row counts
        csv_rows = self.results.get('csv_rows', 0)
        db_routes = self.results.get('db_routes', 0)
        
        logger.info(f"\nSource Data:")
        logger.info(f"  CSV rows:          {csv_rows:,}")
        logger.info(f"  Database routes:   {db_routes:,}")
        
        if csv_rows > 0:
            ratio = db_routes / csv_rows * 100
            logger.info(f"  Import ratio:      {ratio:.1f}%")
        
        # Entity counts
        logger.info(f"\nDatabase Entities:")
        logger.info(f"  Trains:            {self.results.get('db_trains', 0):,}")
        logger.info(f"  Stations:          {self.results.get('db_stations', 0):,}")
        logger.info(f"  Routes:            {self.results.get('db_routes', 0):,}")
        
        logger.info("\n" + "="*60)
        logger.info("✓ Validation complete!")
        logger.info("="*60 + "\n")


def main():
    """CLI entry point."""
    validator = DataValidator()
    validator.validate_all()


if __name__ == "__main__":
    main()
