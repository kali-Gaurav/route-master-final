"""
Bulk Ingestion Script for RAPPID_Complete_Dataset.csv

Reads the 122MB RAPPID dataset in chunks to avoid memory crashes.
Normalizes data into trains, stations, and train_stations tables.
Applies upsert logic to handle duplicates and updates.

Usage:
    python scripts/bulk_load_rappid.py --sample 10000  # Test with 10k rows
    python scripts/bulk_load_rappid.py --full         # Full 197k rows
"""

import json
from datetime import datetime
from pathlib import Path
import pandas as pd
import logging
import time
from typing import Dict, List, Tuple
import argparse
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database_manager import DatabaseManager, get_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATASET_PATH = Path("dataset") / "RAPPID_Complete_Dataset.csv"
CHUNK_SIZE = 10000  # Process 10k rows per chunk


class BulkLoader:
    """Handles bulk ingestion of RAPPID dataset."""
    
    def __init__(self, db: DatabaseManager = None):
        """Initialize bulk loader.
        
        Args:
            db: DatabaseManager instance (uses singleton if None)
        """
        self.db = db or get_db()
        self.stats = {
            'total_rows': 0,
            'trains_inserted': 0,
            'trains_updated': 0,
            'stations_inserted': 0,
            'routes_inserted': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    def load_dataset(self, limit: int = None) -> Tuple[int, int, int]:
        """Load RAPPID dataset in chunks.
        
        Args:
            limit: Maximum rows to load (None = all)
        
        Returns:
            Tuple of (trains_inserted, stations_inserted, routes_inserted)
        """
        if not DATASET_PATH.exists():
            logger.error(f"✗ Dataset not found: {DATASET_PATH}")
            return 0, 0, 0
        
        self.stats['start_time'] = time.time()
        logger.info(f"Starting ingestion from {DATASET_PATH}")
        logger.info(f"Chunk size: {CHUNK_SIZE} rows")
        
        chunk_num = 0
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Read CSV in chunks
            for chunk in pd.read_csv(DATASET_PATH, chunksize=CHUNK_SIZE):
                chunk_num += 1
                
                if limit and self.stats['total_rows'] >= limit:
                    logger.info(f"Reached limit of {limit} rows")
                    break
                
                # Trim chunk if limit specified
                if limit and len(chunk) + self.stats['total_rows'] > limit:
                    chunk = chunk[:limit - self.stats['total_rows']]
                
                logger.info(f"Processing chunk {chunk_num}: {len(chunk)} rows")
                self._process_chunk(chunk, cursor, conn)
                
                self.stats['total_rows'] += len(chunk)
                logger.info(f"Progress: {self.stats['total_rows']} total rows processed")
            
            logger.info("✓ All chunks processed successfully")
        
        except Exception as e:
            logger.error(f"✗ Bulk load failed: {e}")
            self.stats['errors'] += 1
        
        finally:
            conn.close()
            self.stats['end_time'] = time.time()
            self._print_summary()
            
            return (
                self.stats['trains_inserted'],
                self.stats['stations_inserted'],
                self.stats['routes_inserted']
            )
    
    def _process_chunk(self, chunk: pd.DataFrame, cursor, conn):
        """Process a single chunk of data.
        
        Args:
            chunk: DataFrame chunk
            cursor: Database cursor
            conn: Database connection
        """
        try:
            # Extract unique stations first
            unique_stations = self._extract_unique_stations(chunk)
            self._insert_stations(unique_stations, cursor, conn)
            
            # Extract unique trains
            unique_trains = self._extract_unique_trains(chunk)
            self._insert_trains(unique_trains, cursor, conn)
            
            # Insert routes
            self._insert_routes(chunk, cursor, conn)
            
            conn.commit()
        
        except Exception as e:
            conn.rollback()
            logger.error(f"✗ Chunk processing failed: {e}")
            self.stats['errors'] += 1
    
    def _extract_unique_stations(self, chunk: pd.DataFrame) -> List[Dict]:
        """Extract unique stations from chunk."""
        stations = []
        seen = set()
        
        for _, row in chunk.iterrows():
            station_name = row.get('station_name', '').strip()
            if station_name and station_name not in seen:
                stations.append({
                    'station_code': self._derive_station_code(station_name),
                    'station_name': station_name,
                    'city': row.get('city', '').strip() or None,
                    'state': row.get('state', '').strip() or None,
                })
                seen.add(station_name)
        
        return stations
    
    def _derive_station_code(self, station_name: str) -> str:
        """Derive station code from name (first 3-4 uppercase letters)."""
        # Try to use common abbreviations
        name_upper = station_name.upper()
        
        # For multi-word names, take first letter of each word
        words = name_upper.split()
        if len(words) > 1:
            code = ''.join(w[0] for w in words[:4])
        else:
            code = name_upper[:4]
        
        return code or 'UNK'
    
    def _extract_unique_trains(self, chunk: pd.DataFrame) -> List[Dict]:
        """Extract unique trains from chunk."""
        trains = []
        seen = set()
        
        for _, row in chunk.iterrows():
            train_no = str(row.get('train_no', '')).strip()
            if train_no and train_no not in seen and train_no != 'nan':
                trains.append({
                    'train_no': train_no,
                    'train_name': row.get('train_name', 'Unknown').strip(),
                })
                seen.add(train_no)
        
        return trains
    
    def _insert_stations(self, stations: List[Dict], cursor, conn):
        """Insert stations with upsert logic."""
        for station in stations:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO stations 
                    (station_code, station_name, city, state, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    station['station_code'],
                    station['station_name'],
                    station['city'],
                    station['state']
                ))
                
                self.stats['stations_inserted'] += 1
            
            except Exception as e:
                logger.warning(f"Failed to insert station {station['station_name']}: {e}")
                self.stats['errors'] += 1
    
    def _insert_trains(self, trains: List[Dict], cursor, conn):
        """Insert trains with upsert logic."""
        for train in trains:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO trains
                    (train_no, train_name, created_at, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (train['train_no'], train['train_name']))
                
                self.stats['trains_inserted'] += 1
            
            except Exception as e:
                logger.warning(f"Failed to insert train {train['train_no']}: {e}")
                self.stats['errors'] += 1
    
    def _insert_routes(self, chunk: pd.DataFrame, cursor, conn):
        """Insert train-station routes and keep raw rows for audit."""
        chunk_timestamp = datetime.utcnow().isoformat()
        for _, row in chunk.iterrows():
            try:
                train_no = str(row.get('train_no', '')).strip()
                station_name = row.get('station_name', '').strip()
    
                if not train_no or not station_name or train_no.lower() == 'nan':
                    continue
                
                cursor.execute("SELECT id FROM trains WHERE train_no = ?", (train_no,))
                train_result = cursor.fetchone()
                if not train_result:
                    continue
                train_id = train_result[0]
                
                cursor.execute("SELECT id FROM stations WHERE station_name = ?", (station_name,))
                station_result = cursor.fetchone()
                if not station_result:
                    continue
                station_id = station_result[0]
                
                sequence = int(row.get('station_sequence', 0) or 0)
                arrival = row.get('timing', '').strip() or None
                departure = row.get('timing', '').strip() or None
                distance = row.get('distance_km')

                cursor.execute("""
                    INSERT INTO train_stations
                    (train_id, station_id, sequence, arrival_time, departure_time, distance_km, last_updated, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(train_id, sequence) DO UPDATE SET
                        arrival_time = excluded.arrival_time,
                        departure_time = excluded.departure_time,
                        distance_km = excluded.distance_km,
                        last_updated = excluded.last_updated
                """, (
                    train_id,
                    station_id,
                    sequence,
                    arrival,
                    departure,
                    distance,
                    chunk_timestamp
                ))
                
                payload = row.fillna('').to_dict()
                cursor.execute("""
                    INSERT INTO routes
                    (train_id, station_id, station_sequence, arrival_time, departure_time, distance_km, raw_payload, last_updated, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    train_id,
                    station_id,
                    sequence,
                    arrival,
                    departure,
                    distance,
                    json.dumps(payload, default=str),
                    chunk_timestamp
                ))

                self.stats['routes_inserted'] += 1
            except Exception as e:
                logger.warning(f"Failed to insert route: {e}")
                self.stats['errors'] += 1
    def _print_summary(self):
        """Print ingestion summary."""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        logger.info("\n" + "="*60)
        logger.info("INGESTION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total rows processed:    {self.stats['total_rows']:,}")
        logger.info(f"Trains inserted:         {self.stats['trains_inserted']:,}")
        logger.info(f"Stations inserted:       {self.stats['stations_inserted']:,}")
        logger.info(f"Routes inserted:         {self.stats['routes_inserted']:,}")
        logger.info(f"Errors:                  {self.stats['errors']:,}")
        logger.info(f"Duration:                {duration:.2f} seconds")
        logger.info(f"Throughput:              {self.stats['total_rows']/duration:.0f} rows/sec")
        logger.info("="*60 + "\n")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Bulk load RAPPID dataset into SQLite database"
    )
    parser.add_argument(
        '--sample',
        type=int,
        help='Load only N sample rows (for testing)'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Load entire dataset (197k+ rows)'
    )
    
    args = parser.parse_args()
    
    loader = BulkLoader()
    
    limit = args.sample if args.sample else (None if args.full else 10000)
    
    logger.info(f"Loading dataset with limit: {limit or 'FULL'}")
    loader.load_dataset(limit=limit)


if __name__ == "__main__":
    main()
