"""
Database Schema Optimization with Indexes
Creates comprehensive database indexes for performance
"""

import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Optimizes database with proper indexes"""
    
    def __init__(self, db_path: str = "production.db"):
        self.db_path = db_path
        self.logger = logger
    
    def create_indexes(self):
        """Create all performance indexes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Train table indexes
            indexes = [
                # Train indexes
                "CREATE INDEX IF NOT EXISTS idx_train_train_no ON Train_Master(train_no)",
                "CREATE INDEX IF NOT EXISTS idx_train_name ON Train_Master(train_name)",
                "CREATE INDEX IF NOT EXISTS idx_train_from_to ON Train_Master(from_station, to_station)",
                
                # Station indexes
                "CREATE INDEX IF NOT EXISTS idx_station_name ON Station_Master(station_name)",
                "CREATE INDEX IF NOT EXISTS idx_station_code ON Station_Master(station_code)",
                "CREATE INDEX IF NOT EXISTS idx_station_city ON Station_Master(city)",
                
                # Train segments indexes
                "CREATE INDEX IF NOT EXISTS idx_segment_train ON Train_Segments(train_no)",
                "CREATE INDEX IF NOT EXISTS idx_segment_station ON Train_Segments(station_code)",
                "CREATE INDEX IF NOT EXISTS idx_segment_sequence ON Train_Segments(station_sequence)",
                "CREATE INDEX IF NOT EXISTS idx_segment_from_to ON Train_Segments(from_station, to_station)",
                
                # Routes indexes
                "CREATE INDEX IF NOT EXISTS idx_route_origin ON routes(origin)",
                "CREATE INDEX IF NOT EXISTS idx_route_destination ON routes(destination)",
                "CREATE INDEX IF NOT EXISTS idx_route_date ON routes(travel_date)",
                "CREATE INDEX IF NOT EXISTS idx_route_transfers ON routes(num_transfers)",
                "CREATE INDEX IF NOT EXISTS idx_route_cost ON routes(total_cost)",
                
                # Composite indexes for common queries
                "CREATE INDEX IF NOT EXISTS idx_route_origin_dest_date ON routes(origin, destination, travel_date)",
                "CREATE INDEX IF NOT EXISTS idx_segment_train_seq ON Train_Segments(train_no, station_sequence)",
            ]
            
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except sqlite3.OperationalError as e:
                    if "already exists" not in str(e):
                        self.logger.warning(f"Index creation failed: {str(e)}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Database indexes created successfully for {self.db_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create indexes: {str(e)}")
            return False
    
    def analyze_database(self):
        """Run ANALYZE to update statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("ANALYZE")
            
            conn.commit()
            conn.close()
            
            self.logger.info("Database analysis completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to analyze database: {str(e)}")
            return False
    
    def get_index_info(self):
        """Get information about all indexes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = cursor.fetchall()
            
            conn.close()
            
            return [idx[0] for idx in indexes]
            
        except Exception as e:
            self.logger.error(f"Failed to get index info: {str(e)}")
            return []

def initialize_database_optimization(db_path: str = "production.db"):
    """Initialize database optimization"""
    optimizer = DatabaseOptimizer(db_path)
    optimizer.create_indexes()
    optimizer.analyze_database()
    return optimizer

if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "production.db"
    initialize_database_optimization(db_path)
