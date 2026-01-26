#!/usr/bin/env python3
"""
RAPPID Database Schema Builder & Loader

This script creates the complete schema for the RAPPID Complete Dataset
and populates it directly into production.db.

SINGLE SOURCE OF TRUTH: RAPPID_Complete_Dataset.csv → production.db
No CSV will be read at runtime. All graph building is database-driven.
"""

import sqlite3
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("RAPPID_Loader")

class RAPPIDDatabaseLoader:
    """Loads RAPPID Complete Dataset into production database."""
    
    def __init__(self, db_path: str = "data/production.db"):
        from pathlib import Path
        Path("data").mkdir(exist_ok=True)
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Connect to database."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        logger.info(f"Connected to {self.db_path}")
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def create_schema(self):
        """Create the complete RAPPID schema."""
        logger.info("Creating RAPPID database schema...")
        
        # DROP existing tables (clean slate)
        tables_to_drop = [
            'train_running_days',  # From previous schema
            'rappid_routes',
            'stations',
            'trains'
        ]
        
        for table in tables_to_drop:
            try:
                self.cursor.execute(f"DROP TABLE IF EXISTS {table}")
            except Exception as e:
                logger.warning(f"Could not drop {table}: {e}")
        
        # CREATE stations table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_code TEXT UNIQUE NOT NULL,
                station_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("✓ Created stations table")
        
        # CREATE trains table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS trains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                train_no INTEGER UNIQUE NOT NULL,
                train_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("✓ Created trains table")
        
        # CREATE rappid_routes table (THE SINGLE SOURCE OF TRUTH)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS rappid_routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                train_no INTEGER NOT NULL,
                train_name TEXT NOT NULL,
                station_sequence INTEGER NOT NULL,
                station_name TEXT NOT NULL,
                distance_km REAL,
                timing TEXT,
                delay TEXT,
                platform TEXT,
                halt_duration TEXT,
                is_current_station BOOLEAN DEFAULT 0,
                updated_time TEXT,
                fetch_timestamp TEXT,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY(train_no) REFERENCES trains(train_no),
                UNIQUE(train_no, station_sequence)
            )
        ''')
        logger.info("✓ Created rappid_routes table (SINGLE SOURCE OF TRUTH)")
        
        # CREATE train_running_days table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS train_running_days (
                train_no INTEGER PRIMARY KEY,
                train_name TEXT,
                monday INTEGER DEFAULT 0,
                tuesday INTEGER DEFAULT 0,
                wednesday INTEGER DEFAULT 0,
                thursday INTEGER DEFAULT 0,
                friday INTEGER DEFAULT 0,
                saturday INTEGER DEFAULT 0,
                sunday INTEGER DEFAULT 0,
                days_string TEXT,
                loaded_at TIMESTAMP
            )
        ''')
        logger.info("✓ Created train_running_days table")
        
        # CREATE indexes for fast lookups
        logger.info("Creating indexes...")
        
        indexes = [
            ("CREATE INDEX IF NOT EXISTS idx_rappid_train_no ON rappid_routes(train_no)", 
             "train_no index"),
            ("CREATE INDEX IF NOT EXISTS idx_rappid_station_name ON rappid_routes(station_name)", 
             "station_name index"),
            ("CREATE INDEX IF NOT EXISTS idx_rappid_sequence ON rappid_routes(train_no, station_sequence)", 
             "sequence index"),
            ("CREATE INDEX IF NOT EXISTS idx_stations_code ON stations(station_code)", 
             "stations code index"),
            ("CREATE INDEX IF NOT EXISTS idx_trains_no ON trains(train_no)", 
             "trains no index"),
        ]
        
        for sql, desc in indexes:
            try:
                self.cursor.execute(sql)
                logger.info(f"  ✓ {desc}")
            except Exception as e:
                logger.warning(f"  ✗ {desc}: {e}")
        
        self.conn.commit()
        logger.info("Schema created successfully!")
    
    def load_rappid_dataset(self, csv_path: str = "dataset/RAPPID_Complete_Dataset.csv"):
        """Load RAPPID Complete Dataset from CSV."""
        logger.info(f"Loading RAPPID dataset from {csv_path}...")
        
        # Read CSV
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows from RAPPID dataset")
        
        # Extract unique stations
        logger.info("Extracting unique stations...")
        unique_stations = df['station_name'].unique()
        logger.info(f"Found {len(unique_stations)} unique stations")
        
        # Insert stations
        for i, station_name in enumerate(unique_stations):
            # Convert station name to code (uppercase, remove spaces for code)
            station_code = station_name.upper().replace(" ", "")[:10]
            try:
                self.cursor.execute(
                    "INSERT INTO stations (station_code, station_name) VALUES (?, ?)",
                    (station_code, station_name)
                )
            except sqlite3.IntegrityError:
                pass  # Station already exists
        
        self.conn.commit()
        logger.info(f"✓ Inserted stations")
        
        # Extract unique trains
        logger.info("Extracting unique trains...")
        unique_trains = df[['train_no', 'train_name']].drop_duplicates()
        logger.info(f"Found {len(unique_trains)} unique trains")
        
        # Insert trains
        for _, row in unique_trains.iterrows():
            try:
                self.cursor.execute(
                    "INSERT INTO trains (train_no, train_name) VALUES (?, ?)",
                    (int(row['train_no']), str(row['train_name']))
                )
            except sqlite3.IntegrityError:
                pass  # Train already exists
        
        self.conn.commit()
        logger.info(f"✓ Inserted trains")
        
        # Insert RAPPID routes (THE SINGLE SOURCE OF TRUTH)
        logger.info("Loading RAPPID routes into database...")
        
        batch_size = 10000
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            
            rows = []
            for _, row in batch.iterrows():
                rows.append((
                    int(row['train_no']),
                    str(row['train_name']),
                    int(row['station_sequence']),
                    str(row['station_name']),
                    float(row['distance_km']) if pd.notna(row['distance_km']) else None,
                    str(row['timing']) if pd.notna(row['timing']) else None,
                    str(row['delay']) if pd.notna(row['delay']) else None,
                    str(row['platform']) if pd.notna(row['platform']) else None,
                    str(row['halt_duration']) if pd.notna(row['halt_duration']) else None,
                    1 if row['is_current_station'] else 0,
                    str(row['updated_time']) if pd.notna(row['updated_time']) else None,
                    str(row['fetch_timestamp']) if pd.notna(row['fetch_timestamp']) else None,
                ))
            
            try:
                self.cursor.executemany('''
                    INSERT OR REPLACE INTO rappid_routes (
                        train_no, train_name, station_sequence, station_name,
                        distance_km, timing, delay, platform, halt_duration,
                        is_current_station, updated_time, fetch_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', rows)
                
                progress = min(i + batch_size, len(df))
                logger.info(f"  Loaded {progress}/{len(df)} routes")
            except Exception as e:
                logger.error(f"Error loading batch: {e}")
        
        self.conn.commit()
        logger.info(f"✓ Loaded all RAPPID routes")
    
    def verify_database(self):
        """Verify database integrity."""
        logger.info("Verifying database...")
        
        # Check tables exist
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in self.cursor.fetchall()]
        logger.info(f"Tables: {tables}")
        
        # Check row counts
        self.cursor.execute("SELECT COUNT(*) FROM stations")
        station_count = self.cursor.fetchone()[0]
        logger.info(f"✓ Stations: {station_count}")
        
        self.cursor.execute("SELECT COUNT(*) FROM trains")
        train_count = self.cursor.fetchone()[0]
        logger.info(f"✓ Trains: {train_count}")
        
        self.cursor.execute("SELECT COUNT(*) FROM rappid_routes")
        route_count = self.cursor.fetchone()[0]
        logger.info(f"✓ RAPPID Routes: {route_count}")
        
        # Check unique trains in rappid_routes
        self.cursor.execute("SELECT COUNT(DISTINCT train_no) FROM rappid_routes")
        unique_trains = self.cursor.fetchone()[0]
        logger.info(f"✓ Unique trains in RAPPID: {unique_trains}")
        
        # Sample data
        logger.info("\nSample RAPPID route:")
        self.cursor.execute('''
            SELECT train_no, train_name, station_sequence, station_name, distance_km
            FROM rappid_routes
            LIMIT 3
        ''')
        
        for row in self.cursor.fetchall():
            logger.info(f"  Train {row[0]}: {row[1]} → {row[3]} (seq {row[2]}, {row[4]} km)")
        
        logger.info("\n" + "="*80)
        logger.info("DATABASE VERIFICATION COMPLETE")
        logger.info("="*80)
        logger.info(f"Stations: {station_count}")
        logger.info(f"Trains: {train_count}")
        logger.info(f"Routes: {route_count}")
        logger.info(f"Unique trains in RAPPID: {unique_trains}")
        logger.info("\nSINGLE SOURCE OF TRUTH: RAPPID Complete Dataset in database")
        logger.info("CSV files are NO LONGER read at runtime")
        logger.info("="*80)
    
    def run(self):
        """Execute the complete loading process."""
        try:
            self.connect()
            self.create_schema()
            self.load_rappid_dataset()
            self.verify_database()
            logger.info("\n✅ RAPPID database setup complete!")
            return True
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return False
        finally:
            self.close()

if __name__ == '__main__':
    loader = RAPPIDDatabaseLoader()
    success = loader.run()
    exit(0 if success else 1)
