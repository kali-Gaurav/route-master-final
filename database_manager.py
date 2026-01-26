"""
Unified Database Manager for FINALTrip

Centralizes all SQL operations and schema management for:
- Trains (11,112+ unique trains from RAPPID)
- Stations (origin/destination lookups)
- Train-Station routes (197,469+ station records)
- Real-time delays and seat availability

Uses SQLite for development; PostgreSQL-ready for production.
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

DB_DIR = Path("data")
DB_PATH = DB_DIR / "production.db"


class DatabaseManager:
    """Centralized SQLite database manager with connection pooling support."""
    
    def __init__(self, db_path: Path = DB_PATH, pool_size: int = 5):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
            pool_size: Connection pool size (for future async implementation)
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self._ensure_db_dir()
        self._init_schema()
        logger.info(f"✓ DatabaseManager initialized: {self.db_path}")
    
    def _ensure_db_dir(self):
        """Ensure database directory exists."""
        DB_DIR.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a new database connection with optimizations."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        conn.execute("PRAGMA synchronous=NORMAL")  # Balance speed/safety
        conn.execute("PRAGMA cache_size=10000")  # 10MB cache
        conn.execute("PRAGMA foreign_keys=ON")  # Enforce FK constraints
        return conn
    
    def _init_schema(self):
        """Create database schema if not exists."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # City-Hubs mapping for fast city-to-station lookup
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS city_hubs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT NOT NULL,
                    state TEXT,
                    hub_code TEXT NOT NULL,
                    hub_name TEXT NOT NULL,
                    hub_type TEXT,
                    hub_full_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # Trains table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    train_no TEXT UNIQUE NOT NULL,
                    train_name TEXT NOT NULL,
                    station_sequence INTEGER,
                    station_name TEXT,
                    distance_km REAL,
                    timing TEXT,
                    delay TEXT DEFAULT 'On Time',
                    platform TEXT,
                    halt_duration TEXT,
                    is_current_station INTEGER DEFAULT 0,
                    updated_time TEXT,
                    fetch_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Stations table (deduplicated from trains)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_code TEXT UNIQUE NOT NULL,
                    station_name TEXT UNIQUE NOT NULL,
                    city TEXT,
                    state TEXT,
                    latitude REAL,
                    longitude REAL,
                    zone TEXT,
                    is_major_station INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Train-Station routes (normalized)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS train_stations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    train_id INTEGER NOT NULL,
                    station_id INTEGER NOT NULL,
                    sequence INTEGER NOT NULL,
                    arrival_time TEXT,
                    departure_time TEXT,
                    halt_minutes INTEGER DEFAULT 0,
                    distance_km REAL,
                    is_source INTEGER DEFAULT 0,
                    is_destination INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (train_id) REFERENCES trains(id),
                    FOREIGN KEY (station_id) REFERENCES stations(id),
                    UNIQUE(train_id, sequence)
                );
            """)

            # Raw dataset replication for auditing and counts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS routes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    train_id INTEGER,
                    station_id INTEGER,
                    station_sequence INTEGER,
                    arrival_time TEXT,
                    departure_time TEXT,
                    distance_km REAL,
                    raw_payload TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (train_id) REFERENCES trains(id),
                    FOREIGN KEY (station_id) REFERENCES stations(id)
                );
            """)
            
            # Search logs for analytics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    origin TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    travel_date TEXT,
                    results_count INTEGER,
                    response_time_ms REAL,
                    cached INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Performance metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    duration_ms REAL,
                    records_processed INTEGER,
                    success INTEGER DEFAULT 1,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Data quality tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_quality (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            conn.commit()
            logger.info("✓ Database schema initialized")
        
        except Exception as e:
            logger.error(f"✗ Schema initialization failed: {e}")
            raise
        
        finally:
            conn.close()

    def get_station_by_code(self, code: str) -> Optional[Dict]:
        """Return matching station record by code."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, station_code, station_name, city, state FROM stations WHERE station_code = ?",
                (code.upper(),)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'code': row[1],
                    'name': row[2],
                    'city': row[3],
                    'state': row[4]
                }
            return None
        finally:
            conn.close()
    
    def create_indexes(self):
        """Create all performance indexes for RAPPID schema."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Only create indexes on tables that exist in RAPPID schema
            tables = []
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"Creating indexes for existing tables: {tables}")
            
            # RAPPID table indexes
            if 'rappid_routes' in tables:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_rappid_train_no ON rappid_routes(train_no);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_rappid_station ON rappid_routes(station_name);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_rappid_sequence ON rappid_routes(train_no, station_sequence);")
                logger.info("  ✓ RAPPID indexes created")
            
            # Trains table indexes
            if 'trains' in tables:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_train_no ON trains(train_no);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_train_name ON trains(train_name);")
                logger.info("  ✓ Trains indexes created")
            
            # Stations table indexes
            if 'stations' in tables:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_station_code ON stations(station_code);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_station_name ON stations(station_name);")
                logger.info("  ✓ Stations indexes created")
            
            # Train running days indexes
            if 'train_running_days' in tables:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_running_days_train ON train_running_days(train_no);")
                logger.info("  ✓ Running days indexes created")
            
            conn.commit()
            logger.info("✓ All RAPPID indexes created successfully")
        
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
            logger.error(f"✗ Index creation failed: {e}")
            raise
        
        finally:
            conn.close()
    
    def upsert_train(self, train_no: str, train_name: str, data: Dict) -> int:
        """Upsert a train record.
        
        Args:
            train_no: Train number (unique identifier)
            train_name: Train name
            data: Additional fields (delay, updated_time, etc.)
        
        Returns:
            Train ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if exists
            cursor.execute("SELECT id FROM trains WHERE train_no = ?", (train_no,))
            result = cursor.fetchone()
            
            if result:
                # Update
                train_id = result[0]
                cursor.execute("""
                    UPDATE trains
                    SET train_name = ?, updated_at = CURRENT_TIMESTAMP, ?
                    WHERE train_no = ?
                """, (train_name, datetime.now().isoformat(), train_no))
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO trains (train_no, train_name, created_at, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (train_no, train_name))
                train_id = cursor.lastrowid
            
            conn.commit()
            return train_id
        
        except Exception as e:
            logger.error(f"✗ Upsert train failed: {e}")
            raise
        
        finally:
            conn.close()
    
    def bulk_insert_trains(self, records: List[Dict], batch_size: int = 1000):
        """Bulk insert train records with transaction batching.
        
        Args:
            records: List of train record dictionaries
            batch_size: Records per batch transaction
        
        Returns:
            Tuple of (inserted_count, updated_count, failed_count)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        inserted = 0
        updated = 0
        failed = 0
        
        try:
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                
                for record in batch:
                    try:
                        train_no = record.get('train_no')
                        train_name = record.get('train_name', 'Unknown')
                        
                        cursor.execute("SELECT id FROM trains WHERE train_no = ?", (train_no,))
                        if cursor.fetchone():
                            updated += 1
                        else:
                            cursor.execute("""
                                INSERT INTO trains (train_no, train_name, created_at, updated_at)
                                VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            """, (train_no, train_name))
                            inserted += 1
                    
                    except Exception as e:
                        failed += 1
                        logger.warning(f"Failed to insert train {record.get('train_no')}: {e}")
                
                conn.commit()
                logger.info(f"✓ Processed batch: {i//batch_size + 1} ({inserted} inserted, {updated} updated, {failed} failed)")
            
            logger.info(f"✓ Bulk insert complete: {inserted} inserted, {updated} updated, {failed} failed")
            return inserted, updated, failed
        
        except Exception as e:
            logger.error(f"✗ Bulk insert failed: {e}")
            raise
        
        finally:
            conn.close()
    
    def get_train_by_no(self, train_no: str) -> Optional[Dict]:
        """Get train by train_no."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, train_no, train_name, updated_at
                FROM trains
                WHERE train_no = ?
            """, (train_no,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'train_no': row[1],
                    'train_name': row[2],
                    'updated_at': row[3]
                }
            return None
        
        finally:
            conn.close()
    
    def search_stations(self, query: str, limit: int = 20) -> List[Dict]:
        """Search stations by name or code."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, station_code, station_name, city
                FROM stations
                WHERE station_name LIKE ? OR station_code LIKE ?
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            
            return [
                {'id': row[0], 'code': row[1], 'name': row[2], 'city': row[3]}
                for row in cursor.fetchall()
            ]
        
        finally:
            conn.close()
    
    def get_route_between(self, origin: str, destination: str) -> List[Dict]:
        """Get all train routes between two stations."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT DISTINCT t.id, t.train_no, t.train_name, t.delay
                FROM trains t
                WHERE t.id IN (
                    SELECT train_id FROM train_stations
                    WHERE station_name = ? OR station_code = ?
                )
                AND t.id IN (
                    SELECT train_id FROM train_stations
                    WHERE station_name = ? OR station_code = ?
                )
            """, (origin, origin, destination, destination))
            
            return [
                {'id': row[0], 'train_no': row[1], 'train_name': row[2], 'delay': row[3]}
                for row in cursor.fetchall()
            ]
        
        finally:
            conn.close()
    
    def log_search(self, origin: str, destination: str, travel_date: str, 
                   results_count: int, response_time_ms: float, cached: bool = False):
        """Log a search operation."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO search_logs (origin, destination, travel_date, results_count, response_time_ms, cached)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (origin, destination, travel_date, results_count, response_time_ms, int(cached)))
            conn.commit()
        
        except Exception as e:
            logger.error(f"✗ Log search failed: {e}")
        
        finally:
            conn.close()
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            stats = {}
            
            cursor.execute("SELECT COUNT(*) FROM trains;")
            stats['total_trains'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM stations;")
            stats['total_stations'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM train_stations;")
            stats['total_routes'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM routes;")
            stats['route_records'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM search_logs;")
            stats['total_searches'] = cursor.fetchone()[0]
            
            return stats
        
        finally:
            conn.close()


# Singleton instance
_db_manager: Optional[DatabaseManager] = None


def get_db() -> DatabaseManager:
    """Get or create singleton database manager."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.create_indexes()
    return _db_manager


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db = get_db()
    print("✓ Database manager initialized successfully")
    print(f"Database path: {db.db_path}")
    print(f"Stats: {db.get_stats()}")
