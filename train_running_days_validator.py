"""
Intelligent Train Running Days Validator with RAPPID Dataset Matching

This module intelligently matches trains between RAPPID_Complete_Dataset.csv
(actual routes used) and train_info.csv (running days information).

Key Features:
1. Only loads running days for trains that exist in RAPPID dataset
2. Cross-references train numbers between datasets
3. Efficiently stores and retrieves from database
4. Uses singleton pattern to avoid repeated database queries
5. Implements batch loading and caching for performance
6. Database-first approach - fetches running days from DB, not CSV
"""

import sys
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
import logging
import pandas as pd
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

logger = logging.getLogger(__name__)


class TrainRunningDaysValidator:
    """
    Intelligent validator that:
    1. Extracts valid train numbers from RAPPID dataset
    2. Matches with train_info.csv running days
    3. Stores in database for efficient querying
    4. Implements singleton pattern for memory efficiency
    """
    
    _instance = None
    _cache = {}
    _lock = None
    
    WEEKDAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    def __new__(cls, db_path: str = 'production.db'):
        """Singleton pattern - create only one instance"""
        if cls._instance is None:
            import threading
            cls._lock = threading.Lock()
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
            cls._instance._db_path = db_path
            cls._instance._conn = None
            cls._instance._cursor = None
            cls._instance._train_days_cache = {}  # In-memory cache for fast lookups
        return cls._instance
    
    def __init__(self, db_path: str = 'production.db'):
        """Initialize validator (only runs once due to singleton)"""
        if self._initialized:
            return
        
        with self._lock:
            if self._initialized:
                return
            
            self._db_path = db_path
            self._connect_db()
            self._initialized = True
            logger.info(f"✅ TrainRunningDaysValidator initialized (Singleton pattern)")
    
    def _connect_db(self):
        """Connect to SQLite database"""
        try:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._cursor = self._conn.cursor()
            logger.debug(f"Connected to database: {self._db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def _get_valid_rappid_trains(self) -> Set[int]:
        """
        Extract list of train numbers that exist in RAPPID dataset
        
        Returns:
            Set of valid train numbers from RAPPID_Complete_Dataset.csv
        """
        rappid_path = Path('dataset/RAPPID_Complete_Dataset.csv')
        
        if not rappid_path.exists():
            logger.warning(f"⚠️  RAPPID dataset not found at {rappid_path}")
            return set()
        
        try:
            logger.info("📂 Reading RAPPID_Complete_Dataset.csv to get valid train numbers...")
            df = pd.read_csv(rappid_path, usecols=['train_no'], dtype={'train_no': int})
            valid_trains = set(df['train_no'].unique())
            logger.info(f"✅ Found {len(valid_trains)} unique trains in RAPPID dataset")
            return valid_trains
        except Exception as e:
            logger.error(f"Error reading RAPPID dataset: {e}")
            return set()
    
    def _parse_days_string(self, days_str: str) -> Dict[str, bool]:
        """
        Parse days string like 'Monday,Wednesday,Friday' into boolean flags
        Handles common typos and variations (e.g., 'Mondayd', 'monday', 'MON')
        
        Args:
            days_str: Comma or space separated day names
        
        Returns:
            Dict mapping day names to boolean
        """
        days_dict = {day: False for day in self.WEEKDAY_NAMES}
        
        if not days_str or pd.isna(days_str):
            return days_dict
        
        # Handle various separators: comma, space, etc.
        days = [d.strip() for d in str(days_str).replace(',', ' ').split()]
        
        # Day name patterns (handle typos, abbreviations, case variations)
        day_patterns = {
            'monday': ['monday', 'mon'],
            'tuesday': ['tuesday', 'tue', 'tues'],
            'wednesday': ['wednesday', 'wed'],
            'thursday': ['thursday', 'thu', 'thurs'],
            'friday': ['friday', 'fri'],
            'saturday': ['saturday', 'sat'],
            'sunday': ['sunday', 'sun']
        }
        
        for day in days:
            day_clean = day.lower().rstrip('d').strip()  # Remove trailing 'd' (typo), lowercase
            
            # Try exact match first
            day_title = day_clean.title()
            if day_title in days_dict:
                days_dict[day_title] = True
                continue
            
            # Try pattern matching
            matched = False
            for weekday, patterns in day_patterns.items():
                if day_clean in patterns:
                    days_dict[weekday.title()] = True
                    matched = True
                    break
            
            # Fuzzy match: find closest match
            if not matched:
                for weekday in self.WEEKDAY_NAMES:
                    if day_clean.startswith(weekday[:3].lower()):  # Match first 3 chars
                        days_dict[weekday] = True
                        break
        
        return days_dict
    
    def setup_database_schema(self) -> bool:
        """
        Create database table for train running days if it doesn't exist
        
        Returns:
            True if successful
        """
        try:
            self._cursor.execute('''
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
                    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for fast lookups
            self._cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_train_running_days_train_no 
                ON train_running_days(train_no)
            ''')
            
            self._conn.commit()
            logger.info("✅ Database schema ready")
            return True
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            return False
    
    def load_running_days_for_rappid_trains(self) -> int:
        """
        Intelligently load running days for ONLY trains that exist in RAPPID dataset
        
        This is the key method that implements the intelligent matching:
        1. Read RAPPID dataset to get valid train numbers
        2. Read train_info.csv
        3. Filter train_info to only valid trains
        4. Store in database
        
        Returns:
            Number of trains loaded
        """
        logger.info("\n" + "=" * 80)
        logger.info("INTELLIGENT TRAIN RUNNING DAYS LOADING")
        logger.info("=" * 80)
        
        # Step 1: Get valid train numbers from RAPPID
        valid_trains = self._get_valid_rappid_trains()
        if not valid_trains:
            logger.error("❌ No valid trains found in RAPPID dataset")
            return 0
        
        # Step 2: Read train_info.csv
        train_info_path = Path('dataset/train_info.csv')
        if not train_info_path.exists():
            logger.error(f"❌ train_info.csv not found at {train_info_path}")
            return 0
        
        try:
            logger.info(f"📂 Reading train_info.csv...")
            df_info = pd.read_csv(train_info_path)
            
            logger.info(f"   Total trains in train_info.csv: {len(df_info)}")
            
            # Step 3: Filter to ONLY trains in RAPPID (intelligent matching!)
            # Convert train_no to int for comparison - handle both 'Train_No' and 'train_no'
            train_no_col = 'Train_No' if 'Train_No' in df_info.columns else 'train_no'
            days_col = 'days'
            
            df_filtered = df_info.copy()
            df_filtered['train_no_int'] = df_filtered[train_no_col].astype(int)
            df_filtered = df_filtered[df_filtered['train_no_int'].isin(valid_trains)]
            logger.info(f"   Trains matching RAPPID dataset: {len(df_filtered)}")
            
            # Step 4: Prepare data for database insertion
            self._cursor.execute('DELETE FROM train_running_days')  # Clear old data
            
            loaded_count = 0
            for idx, row in df_filtered.iterrows():
                try:
                    train_no = int(row['train_no_int'])
                    train_name = str(row.get('Train_Name', row.get('train_name', 'Unknown')))
                    days_str = str(row.get('days', ''))
                    
                    # Parse days string into boolean flags
                    days_dict = self._parse_days_string(days_str)
                    
                    # Insert into database
                    self._cursor.execute('''
                        INSERT INTO train_running_days 
                        (train_no, train_name, monday, tuesday, wednesday, thursday, friday, saturday, sunday, days_string)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        train_no,
                        train_name,
                        int(days_dict['Monday']),
                        int(days_dict['Tuesday']),
                        int(days_dict['Wednesday']),
                        int(days_dict['Thursday']),
                        int(days_dict['Friday']),
                        int(days_dict['Saturday']),
                        int(days_dict['Sunday']),
                        days_str
                    ))
                    
                    # Cache in memory for fast access
                    self._train_days_cache[train_no] = days_dict
                    loaded_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to insert train {row.get('train_no_int', row.get('Train_No'))}: {e}")
                    continue
            
            self._conn.commit()
            
            logger.info("=" * 80)
            logger.info(f"✅ Successfully loaded {loaded_count} trains into database")
            logger.info(f"   Coverage: {loaded_count}/{len(valid_trains)} RAPPID trains "
                       f"({100*loaded_count/len(valid_trains):.1f}%)")
            logger.info("=" * 80)
            
            return loaded_count
            
        except Exception as e:
            logger.error(f"❌ Error loading running days: {e}", exc_info=True)
            return 0
    
    def is_train_running_on_date(self, train_no: int, travel_date: datetime) -> bool:
        """
        Check if train runs on given date (fetches from database)
        
        Args:
            train_no: Train number
            travel_date: Date to check
        
        Returns:
            True if train runs on that day of week
        """
        weekday = travel_date.weekday()  # 0=Monday, 6=Sunday
        day_name = self.WEEKDAY_NAMES[weekday].lower()
        
        try:
            # Try cache first (in-memory, fastest)
            if train_no in self._train_days_cache:
                return self._train_days_cache[train_no][self.WEEKDAY_NAMES[weekday]]
            
            # Query database (second fastest)
            self._cursor.execute(
                f'SELECT {day_name} FROM train_running_days WHERE train_no = ?',
                (train_no,)
            )
            result = self._cursor.fetchone()
            
            if result:
                # Cache it
                self._train_days_cache[train_no] = {
                    'Monday': False,    # Will be updated properly on next full cache
                    'Tuesday': False,
                    'Wednesday': False,
                    'Thursday': False,
                    'Friday': False,
                    'Saturday': False,
                    'Sunday': False
                }
                return bool(result[0])
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking train {train_no}: {e}")
            return False
    
    def get_trains_running_on_date(self, travel_date: datetime) -> List[int]:
        """
        Get all trains running on a specific date (fetched from database)
        
        Args:
            travel_date: Date to check
        
        Returns:
            List of train numbers running on that date
        """
        weekday = travel_date.weekday()
        day_name = self.WEEKDAY_NAMES[weekday].lower()
        
        try:
            self._cursor.execute(
                f'SELECT train_no FROM train_running_days WHERE {day_name} = 1 ORDER BY train_no'
            )
            results = self._cursor.fetchall()
            return [row[0] for row in results]
        except Exception as e:
            logger.error(f"Error fetching trains for {travel_date.strftime('%A')}: {e}")
            return []
    
    def can_transfer_between_trains(self, 
                                   source_arrival_time: str, 
                                   dest_departure_time: str,
                                   current_date: datetime,
                                   next_date: datetime,
                                   min_transfer_time_minutes: int = 15) -> Tuple[bool, Optional[bool]]:
        """
        Check if transfer is possible, handling day crossing
        
        Args:
            source_arrival_time: HH:MM format
            dest_departure_time: HH:MM format
            current_date: Current travel date
            next_date: Next day date
            min_transfer_time_minutes: Minimum transfer time
        
        Returns:
            (can_transfer, crosses_midnight)
        """
        try:
            arrival_mins = int(source_arrival_time.split(':')[0]) * 60 + int(source_arrival_time.split(':')[1])
            depart_mins = int(dest_departure_time.split(':')[0]) * 60 + int(dest_departure_time.split(':')[1])
            
            # Same day transfer
            if depart_mins >= arrival_mins:
                connection_time = depart_mins - arrival_mins
                return (connection_time >= min_transfer_time_minutes, False)
            # Midnight crossing
            else:
                time_to_midnight = (24 * 60) - arrival_mins
                time_after_midnight = depart_mins
                total_time = time_to_midnight + time_after_midnight
                return (total_time >= min_transfer_time_minutes, True)
        except:
            return (False, None)
    
    def validate_route_trains(self, route_trains: List[Tuple[int, str, str]], 
                             travel_date: datetime) -> Dict:
        """
        Validate all trains in a route for the travel date
        
        Args:
            route_trains: List of (train_no, arrival_time, departure_time)
            travel_date: Travel date
        
        Returns:
            Validation report
        """
        report = {
            'is_valid': True,
            'valid_trains': [],
            'valid_transfers': [],
            'invalid_trains': [],
            'invalid_transfers': [],
            'notes': []
        }
        
        current_date = travel_date
        
        for i, (train_no, arrival, departure) in enumerate(route_trains):
            # Check if train runs on current date
            if not self.is_train_running_on_date(train_no, current_date):
                report['is_valid'] = False
                report['invalid_trains'].append({
                    'segment': i + 1,
                    'train_no': train_no,
                    'date': current_date.strftime('%Y-%m-%d (%A)'),
                    'reason': 'Train does not run on this day'
                })
                continue
            
            report['valid_trains'].append({
                'segment': i + 1,
                'train_no': train_no,
                'date': current_date.strftime('%Y-%m-%d (%A)')
            })
            
            # Check transfer to next segment
            if i < len(route_trains) - 1:
                next_train_no, next_arrival, next_departure = route_trains[i + 1]
                
                next_date = current_date
                can_transfer, crosses_midnight = self.can_transfer_between_trains(
                    arrival, next_departure, current_date, current_date + timedelta(days=1)
                )
                
                # Update current_date for next iteration if crossing midnight
                if crosses_midnight:
                    next_date = current_date + timedelta(days=1)
                    current_date = next_date
                
                # Check if next train runs on the day it departs
                if not self.is_train_running_on_date(next_train_no, next_date):
                    report['is_valid'] = False
                    report['invalid_transfers'].append({
                        'from_train': train_no,
                        'to_train': next_train_no,
                        'issue': f'Next train does not run on {next_date.strftime("%A")}'
                    })
                    continue
                
                if not can_transfer:
                    report['is_valid'] = False
                    report['invalid_transfers'].append({
                        'from_train': train_no,
                        'to_train': next_train_no,
                        'issue': 'Insufficient transfer time'
                    })
                else:
                    report['valid_transfers'].append({
                        'from_train': train_no,
                        'to_train': next_train_no,
                        'crosses_midnight': crosses_midnight
                    })
        
        return report
    
    def get_database_stats(self) -> Dict:
        """Get statistics about loaded data"""
        try:
            self._cursor.execute('SELECT COUNT(*) FROM train_running_days')
            total = self._cursor.fetchone()[0]
            
            stats = {
                'total_trains': total,
                'cache_size': len(self._train_days_cache),
                'db_path': self._db_path
            }
            return stats
        except:
            return {}
    
    def __del__(self):
        """Close database connection"""
        try:
            if self._conn:
                self._conn.close()
        except:
            pass


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize validator (singleton)
    validator = TrainRunningDaysValidator('production.db')
    
    # Setup database
    if validator.setup_database_schema():
        # Load running days for RAPPID trains only
        loaded = validator.load_running_days_for_rappid_trains()
        
        if loaded > 0:
            # Show stats
            stats = validator.get_database_stats()
            print(f"\nDatabase Statistics:")
            print(f"   Total trains loaded: {stats['total_trains']}")
            print(f"   Memory cache size: {stats['cache_size']}")
            
            # Test a few trains
            print(f"\nReady for intelligent train validation!")
            
            # Example test
            monday = datetime(2026, 1, 26)
            available = validator.get_trains_running_on_date(monday)
            print(f"\nTrains available on Monday: {len(available)} trains")
