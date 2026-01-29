# ===============================================
# DATABASE CONNECTION AND QUERY HELPERS
# ===============================================
# Handles all database operations with proper error handling

import sqlite3
import os
import sys
from datetime import datetime, timedelta
from config import DB_PATH, DB_TIMEOUT, COLORS, LOG_FILE

class DatabaseConnection:
    """Manages SQLite database connection with error handling"""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(self.db_path, timeout=DB_TIMEOUT)
            self.conn.row_factory = None
            self.cursor = self.conn.cursor()
            return True
        except sqlite3.Error as e:
            print(f"{COLORS['RED']}❌ Database Connection Error: {str(e)}{COLORS['RESET']}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def execute_query(self, query, params=None):
        """Execute SELECT query safely"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"{COLORS['RED']}❌ Query Error: {str(e)}{COLORS['RESET']}")
            return []
    
    def execute_single(self, query, params=None):
        """Execute query and fetch single row"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"{COLORS['RED']}❌ Query Error: {str(e)}{COLORS['RESET']}")
            return None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

# ===============================================
# DATABASE QUERY FUNCTIONS
# ===============================================

def get_all_stations():
    """Get all stations from database"""
    with DatabaseConnection() as db:
        if not db.connect():
            return []
        
        query = """
            SELECT station_code, station_name, city, state, is_junction
            FROM stations_master
            ORDER BY station_name
        """
        return db.execute_query(query)

def search_station(search_term):
    """Search for station by code or name"""
    search_term = search_term.upper().strip()
    
    with DatabaseConnection() as db:
        if not db.connect():
            return []
        
        query = """
            SELECT station_code, station_name, city, state, is_junction
            FROM stations_master
            WHERE station_code LIKE ? OR station_name LIKE ?
            ORDER BY station_name
            LIMIT 50
        """
        search_pattern = '%' + search_term + '%'
        return db.execute_query(query, (search_pattern, search_pattern))

def get_station_info(station_code):
    """Get detailed information about a station"""
    station_code = station_code.upper().strip()
    
    with DatabaseConnection() as db:
        if not db.connect():
            return None
        
        query = """
            SELECT station_code, station_name, city, state, is_junction, 
                   latitude, longitude
            FROM stations_master
            WHERE station_code = ?
        """
        return db.execute_single(query, (station_code,))

def get_all_trains():
    """Get all trains"""
    with DatabaseConnection() as db:
        if not db.connect():
            return []
        
        query = """
            SELECT train_no, train_name, train_type, source_station, destination_station
            FROM trains_master
            ORDER BY train_no
        """
        return db.execute_query(query)

def search_train(search_term):
    """Search trains by number or name"""
    search_pattern = '%' + search_term.upper() + '%'
    
    with DatabaseConnection() as db:
        if not db.connect():
            return []
        
        query = """
            SELECT train_no, train_name, train_type, source_station, destination_station
            FROM trains_master
            WHERE train_no LIKE ? OR train_name LIKE ?
            ORDER BY train_no
            LIMIT 50
        """
        return db.execute_query(query, (search_pattern, search_pattern))

def get_train_info(train_no):
    """Get detailed train information"""
    with DatabaseConnection() as db:
        if not db.connect():
            return None
        
        query = """
            SELECT train_no, train_name, train_type, source_station, destination_station
            FROM trains_master
            WHERE train_no = ?
        """
        return db.execute_single(query, (train_no,))

def get_train_route(train_no):
    """Get all stops for a train"""
    with DatabaseConnection() as db:
        if not db.connect():
            return []
        
        query = """
            SELECT sequence, station_code, distance_from_source
            FROM train_routes
            WHERE train_no = ?
            ORDER BY sequence
        """
        return db.execute_query(query, (train_no,))

def get_trains_between_stations(source, destination):
    """Get direct trains between two stations"""
    source = source.upper().strip()
    destination = destination.upper().strip()
    
    with DatabaseConnection() as db:
        if not db.connect():
            return []
        
        query = """
            SELECT DISTINCT t.train_no, t.train_name, t.train_type,
                   r1.sequence as source_seq, r2.sequence as dest_seq
            FROM trains_master t
            JOIN train_routes r1 ON t.train_no = r1.train_no AND r1.station_code = ?
            JOIN train_routes r2 ON t.train_no = r2.train_no AND r2.station_code = ?
            WHERE r1.sequence < r2.sequence
            ORDER BY r1.sequence, r2.sequence
        """
        return db.execute_query(query, (source, destination))

def get_schedule(train_no, station_code):
    """Get schedule for a train at a specific station"""
    train_no = int(train_no)
    station_code = station_code.upper().strip()
    
    with DatabaseConnection() as db:
        if not db.connect():
            return []
        
        query = """
            SELECT ts.arrival_time, ts.departure_time, ts.day_offset, ts.stop_duration
            FROM train_schedule ts
            WHERE ts.train_no = ? AND ts.station_code = ?
        """
        return db.execute_query(query, (train_no, station_code))

def get_fares(train_no, source, destination):
    """Get all fare classes between two stations"""
    train_no = int(train_no)
    source = source.upper().strip()
    destination = destination.upper().strip()
    
    with DatabaseConnection() as db:
        if not db.connect():
            return []
        
        query = """
            SELECT class_code, total_fare, available_seats
            FROM train_fares
            WHERE train_no = ? AND source_station = ? AND destination_station = ?
            ORDER BY total_fare
        """
        return db.execute_query(query, (train_no, source, destination))

def is_train_running(train_no, day_code):
    """Check if train runs on specific day"""
    train_no = int(train_no)
    day_code = day_code.upper().strip()
    
    with DatabaseConnection() as db:
        if not db.connect():
            return False
        
        query = """
            SELECT {0}
            FROM train_running_days
            WHERE train_no = ?
        """.format(day_code)
        
        result = db.execute_single(query, (train_no,))
        return result[0] == 1 if result else False

def is_train_active(train_no):
    """Check if train is currently active/operational"""
    train_no = int(train_no)
    
    with DatabaseConnection() as db:
        if not db.connect():
            return True  # Assume active if cannot verify
        
        # Try to get train info - if it exists, it's active
        query = """
            SELECT train_no FROM trains_master WHERE train_no = ?
        """
        result = db.execute_single(query, (train_no,))
        return result is not None

def get_database_stats():
    """Get overall database statistics"""
    with DatabaseConnection() as db:
        if not db.connect():
            return {}
        
        stats = {}
        
        # Count stations
        result = db.execute_single("SELECT COUNT(*) FROM stations_master")
        stats['total_stations'] = result[0] if result else 0
        
        # Count trains
        result = db.execute_single("SELECT COUNT(*) FROM trains_master")
        stats['total_trains'] = result[0] if result else 0
        
        # Count routes
        result = db.execute_single("SELECT COUNT(*) FROM train_routes")
        stats['total_routes'] = result[0] if result else 0
        
        # Count schedules
        result = db.execute_single("SELECT COUNT(*) FROM train_schedule")
        stats['total_schedules'] = result[0] if result else 0
        
        # Count fares
        result = db.execute_single("SELECT COUNT(*) FROM train_fares")
        stats['total_fares'] = result[0] if result else 0
        
        # Count active trains (all trains in database are considered active)
        result = db.execute_single("SELECT COUNT(*) FROM trains_master")
        stats['active_trains'] = result[0] if result else 0
        
        # Get major train types
        query = "SELECT train_type, COUNT(*) as count FROM trains_master GROUP BY train_type ORDER BY count DESC"
        train_types = db.execute_query(query)
        stats['train_types'] = {row[0]: row[1] for row in train_types if row}
        
        return stats

def verify_database():
    """Verify database integrity and connectivity"""
    checks = {
        'database_exists': os.path.exists(DB_PATH),
        'database_readable': os.access(DB_PATH, os.R_OK),
        'connection_works': False,
        'tables_exist': False,
        'data_present': False
    }
    
    try:
        with DatabaseConnection() as db:
            if db.connect():
                checks['connection_works'] = True
                
                # Check if tables exist
                query = "SELECT name FROM sqlite_master WHERE type='table'"
                tables = db.execute_query(query)
                checks['tables_exist'] = len(tables) > 0
                
                # Check if data present
                result = db.execute_single("SELECT COUNT(*) FROM stations_master")
                checks['data_present'] = result[0] > 0 if result else False
    except:
        pass
    
    return checks

if __name__ == '__main__':
    print("Testing Database Connection...")
    print("=" * 50)
    
    checks = verify_database()
    for check, status in checks.items():
        symbol = '✅' if status else '❌'
        print(f"{symbol} {check}: {status}")
    
    print("\n" + "=" * 50)
    stats = get_database_stats()
    print("Database Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
