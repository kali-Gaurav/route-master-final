"""
User Preferences and History Management
Stores user preferences, saved routes, and search history.
"""

import sqlite3
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class UserPreferencesManager:
    """Manages user preferences and history"""
    
    def __init__(self, db_path: str = "production.db"):
        self.db_path = db_path
        self.logger = logger
        self._init_tables()
    
    def _init_tables(self):
        """Initialize user-related tables in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                name TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # User preferences table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                preference_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                preference_key TEXT,
                preference_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """)
            
            # Saved routes table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_routes (
                saved_route_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                origin TEXT,
                destination TEXT,
                route_data TEXT,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """)
            
            # Search history table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                origin TEXT,
                destination TEXT,
                travel_date TEXT,
                filters TEXT,
                results_count INTEGER,
                response_time_ms INTEGER,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """)
            
            # User preferences index
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_preferences 
            ON user_preferences(user_id)
            """)
            
            # Search history index
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_search_history 
            ON search_history(user_id, searched_at)
            """)
            
            conn.commit()
            conn.close()
            
            self.logger.info("User tables initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize user tables: {str(e)}")
    
    def create_user(self, user_id: str, email: str, name: str, phone: str = "") -> bool:
        """Create new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO users (user_id, email, name, phone)
            VALUES (?, ?, ?, ?)
            """, (user_id, email, name, phone))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"User created: {user_id}")
            return True
            
        except sqlite3.IntegrityError:
            self.logger.warning(f"User already exists: {user_id}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to create user: {str(e)}")
            return False
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get all user preferences"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT preference_key, preference_value 
            FROM user_preferences 
            WHERE user_id = ?
            """, (user_id,))
            
            preferences = {}
            for key, value in cursor.fetchall():
                try:
                    preferences[key] = json.loads(value)
                except:
                    preferences[key] = value
            
            conn.close()
            return preferences
            
        except Exception as e:
            self.logger.error(f"Failed to get user preferences: {str(e)}")
            return {}
    
    def set_preference(self, user_id: str, key: str, value: Any) -> bool:
        """Set user preference"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Store as JSON if complex type
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            else:
                value = str(value)
            
            cursor.execute("""
            INSERT OR REPLACE INTO user_preferences (user_id, preference_key, preference_value)
            VALUES (?, ?, ?)
            """, (user_id, key, value))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Preference set for user {user_id}: {key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set preference: {str(e)}")
            return False
    
    def save_route(self, user_id: str, origin: str, destination: str, route_data: dict) -> bool:
        """Save a route"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO saved_routes (user_id, origin, destination, route_data)
            VALUES (?, ?, ?, ?)
            """, (user_id, origin, destination, json.dumps(route_data)))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Route saved for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save route: {str(e)}")
            return False
    
    def get_saved_routes(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all saved routes for user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT saved_route_id, origin, destination, route_data, saved_at
            FROM saved_routes
            WHERE user_id = ?
            ORDER BY saved_at DESC
            """, (user_id,))
            
            routes = []
            for row in cursor.fetchall():
                routes.append({
                    'id': row[0],
                    'origin': row[1],
                    'destination': row[2],
                    'route': json.loads(row[3]),
                    'saved_at': row[4]
                })
            
            conn.close()
            return routes
            
        except Exception as e:
            self.logger.error(f"Failed to get saved routes: {str(e)}")
            return []
    
    def log_search(self, user_id: str, origin: str, destination: str, 
                  travel_date: str, filters: dict, results_count: int, 
                  response_time_ms: int) -> bool:
        """Log search to history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO search_history 
            (user_id, origin, destination, travel_date, filters, results_count, response_time_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, origin, destination, travel_date, json.dumps(filters), 
                  results_count, response_time_ms))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log search: {str(e)}")
            return False
    
    def get_search_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user search history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT history_id, origin, destination, travel_date, filters, 
                   results_count, response_time_ms, searched_at
            FROM search_history
            WHERE user_id = ?
            ORDER BY searched_at DESC
            LIMIT ?
            """, (user_id, limit))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'id': row[0],
                    'origin': row[1],
                    'destination': row[2],
                    'travel_date': row[3],
                    'filters': json.loads(row[4]) if row[4] else {},
                    'results_count': row[5],
                    'response_time_ms': row[6],
                    'searched_at': row[7]
                })
            
            conn.close()
            return history
            
        except Exception as e:
            self.logger.error(f"Failed to get search history: {str(e)}")
            return []
    
    def get_frequent_routes(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get user's most searched routes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT origin, destination, COUNT(*) as search_count
            FROM search_history
            WHERE user_id = ?
            GROUP BY origin, destination
            ORDER BY search_count DESC
            LIMIT ?
            """, (user_id, limit))
            
            routes = []
            for row in cursor.fetchall():
                routes.append({
                    'origin': row[0],
                    'destination': row[1],
                    'search_count': row[2]
                })
            
            conn.close()
            return routes
            
        except Exception as e:
            self.logger.error(f"Failed to get frequent routes: {str(e)}")
            return []

# Global instance
_preferences_manager: Optional[UserPreferencesManager] = None

def get_preferences_manager(db_path: str = "production.db") -> UserPreferencesManager:
    """Get or create preferences manager"""
    global _preferences_manager
    if _preferences_manager is None:
        _preferences_manager = UserPreferencesManager(db_path)
    return _preferences_manager

__all__ = ['UserPreferencesManager', 'get_preferences_manager']
