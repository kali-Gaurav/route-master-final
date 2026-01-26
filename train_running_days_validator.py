"""
Train Running Days Validator
Handles validation of trains running on specific dates and manages day-crossing transfers
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict
import sqlite3
from pathlib import Path

class TrainRunningDaysValidator:
    """
    Validates train availability based on running days and handles multi-day transfers.
    
    Key Features:
    - Maps day-of-week to train availability
    - Validates if a train runs on a specific date
    - Handles transfers that cross midnight (day boundary)
    - Manages connection times between trains across days
    """
    
    # Map day names to weekday numbers (Monday=0, Sunday=6)
    DAY_NAME_TO_NUMBER = {
        'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
        'Friday': 4, 'Saturday': 5, 'Sunday': 6
    }
    
    WEEKDAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    def __init__(self, db_path: str = 'production.db'):
        """
        Initialize the validator with database connection
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Create train_running_days table if it doesn't exist"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS train_running_days (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                train_no INTEGER UNIQUE NOT NULL,
                train_name TEXT,
                days TEXT NOT NULL,
                monday INTEGER DEFAULT 0,
                tuesday INTEGER DEFAULT 0,
                wednesday INTEGER DEFAULT 0,
                thursday INTEGER DEFAULT 0,
                friday INTEGER DEFAULT 0,
                saturday INTEGER DEFAULT 0,
                sunday INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def load_running_days_from_csv(self, csv_path: str):
        """
        Load train running days from train_info.csv
        
        Args:
            csv_path: Path to train_info.csv file
            
        Returns:
            Number of trains processed
        """
        try:
            df = pd.read_csv(csv_path)
            
            # Expected columns: Train_No, Train_Name, days
            if 'Train_No' not in df.columns or 'days' not in df.columns:
                raise ValueError("CSV must have 'Train_No' and 'days' columns")
            
            processed = 0
            for _, row in df.iterrows():
                train_no = int(row['Train_No'])
                train_name = row.get('Train_Name', '')
                days = str(row['days']).strip()
                
                # Parse the days string
                running_days = self._parse_days_string(days)
                
                # Insert or update in database
                self._insert_train_running_days(train_no, train_name, days, running_days)
                processed += 1
            
            print(f"✅ Loaded running days for {processed} trains from {csv_path}")
            return processed
            
        except Exception as e:
            print(f"❌ Error loading running days: {str(e)}")
            return 0
    
    def _parse_days_string(self, days_str: str) -> Dict[str, int]:
        """
        Parse days string like "Monday,Wednesday,Friday" or single day "Saturday"
        Returns dictionary with day flags
        
        Args:
            days_str: Days string from CSV
            
        Returns:
            Dictionary with day flags (0 or 1 for each day)
        """
        running_days = {day: 0 for day in self.WEEKDAY_NAMES}
        
        if not days_str or days_str.lower() == 'nan':
            return running_days
        
        # Split by comma if multiple days
        days_list = [d.strip() for d in days_str.split(',')]
        
        for day in days_list:
            day_clean = day.strip().title()
            if day_clean in self.DAY_NAME_TO_NUMBER:
                day_key = day_clean.lower()
                running_days[day_key] = 1
        
        return running_days
    
    def _insert_train_running_days(self, train_no: int, train_name: str, days_str: str, 
                                   running_days: Dict[str, int]):
        """Insert or update train running days in database"""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO train_running_days 
                (train_no, train_name, days, monday, tuesday, wednesday, thursday, friday, saturday, sunday)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                train_no, train_name, days_str,
                running_days.get('monday', 0),
                running_days.get('tuesday', 0),
                running_days.get('wednesday', 0),
                running_days.get('thursday', 0),
                running_days.get('friday', 0),
                running_days.get('saturday', 0),
                running_days.get('sunday', 0)
            ))
            self.conn.commit()
        except Exception as e:
            print(f"Error inserting train {train_no}: {str(e)}")
    
    def is_train_running_on_date(self, train_no: int, travel_date: datetime) -> bool:
        """
        Check if a train is running on a specific date
        
        Args:
            train_no: Train number
            travel_date: Date to check (datetime object)
            
        Returns:
            True if train runs on that day, False otherwise
        """
        try:
            weekday = travel_date.weekday()  # 0=Monday, 6=Sunday
            day_name = self.WEEKDAY_NAMES[weekday].lower()
            
            self.cursor.execute(f'''
                SELECT {day_name} FROM train_running_days WHERE train_no = ?
            ''', (train_no,))
            
            result = self.cursor.fetchone()
            if result:
                return bool(result[0])
            return False
        except Exception as e:
            print(f"Error checking train {train_no} on date {travel_date}: {str(e)}")
            return False
    
    def get_trains_running_on_date(self, travel_date: datetime, 
                                   source_station: str = None, 
                                   destination_station: str = None) -> List[int]:
        """
        Get all trains running on a specific date (optionally filtered by route)
        
        Args:
            travel_date: Date to check
            source_station: Optional source station code
            destination_station: Optional destination station code
            
        Returns:
            List of train numbers running on that date
        """
        try:
            weekday = travel_date.weekday()
            day_name = self.WEEKDAY_NAMES[weekday].lower()
            
            query = f'SELECT train_no FROM train_running_days WHERE {day_name} = 1'
            
            self.cursor.execute(query)
            trains = [row[0] for row in self.cursor.fetchall()]
            
            return trains
        except Exception as e:
            print(f"Error getting trains for {travel_date}: {str(e)}")
            return []
    
    def can_transfer_between_trains(self, 
                                   source_arrival_time: str,
                                   dest_departure_time: str,
                                   min_transfer_time_minutes: int = 15,
                                   arrival_date: datetime = None) -> Tuple[bool, Optional[str]]:
        """
        Check if transfer between two trains is possible
        Handles case where transfer crosses midnight (next day)
        
        Args:
            source_arrival_time: Arrival time at intermediate station (HH:MM format)
            dest_departure_time: Departure time from intermediate station (HH:MM format)
            min_transfer_time_minutes: Minimum connection time required (default 15 min)
            arrival_date: Date of arrival at intermediate station
            
        Returns:
            Tuple of (can_transfer: bool, next_day_required: Optional[bool])
            - can_transfer: True if transfer is possible
            - next_day_required: True if departure is next day, False if same day, None if impossible
        """
        try:
            # Parse times
            arr_hour, arr_min = map(int, source_arrival_time.split(':'))
            dep_hour, dep_min = map(int, dest_departure_time.split(':'))
            
            arrival_minutes = arr_hour * 60 + arr_min
            departure_minutes = dep_hour * 60 + dep_min
            
            # Case 1: Both on same day
            if departure_minutes >= arrival_minutes:
                connection_time = departure_minutes - arrival_minutes
                if connection_time >= min_transfer_time_minutes:
                    return (True, False)
                else:
                    return (False, None)
            
            # Case 2: Departure is next day (crossing midnight)
            # e.g., arrival at 23:00, departure at 02:00 next day
            else:
                # Time from arrival to midnight
                time_to_midnight = (24 * 60) - arrival_minutes
                # Time from midnight to departure
                time_after_midnight = departure_minutes
                total_time = time_to_midnight + time_after_midnight
                
                if total_time >= min_transfer_time_minutes:
                    return (True, True)  # Valid transfer, next day
                else:
                    return (False, None)
        
        except Exception as e:
            print(f"Error checking transfer: {str(e)}")
            return (False, None)
    
    def validate_route_trains(self, route_trains: List[Tuple[int, str, str]], 
                             travel_date: datetime) -> Dict[str, any]:
        """
        Validate a complete route's trains and transfers
        
        Args:
            route_trains: List of (train_no, arrival_time, departure_time) tuples
            travel_date: Journey start date
            
        Returns:
            Validation report with details about train availability and transfers
        """
        report = {
            'is_valid': True,
            'travel_date': travel_date.strftime('%Y-%m-%d'),
            'total_segments': len(route_trains),
            'valid_trains': [],
            'invalid_trains': [],
            'valid_transfers': [],
            'invalid_transfers': [],
            'notes': []
        }
        
        current_date = travel_date
        
        for idx, (train_no, arrival_time, departure_time) in enumerate(route_trains):
            # Check if train runs on current date
            if not self.is_train_running_on_date(train_no, current_date):
                report['is_valid'] = False
                report['invalid_trains'].append({
                    'segment': idx + 1,
                    'train_no': train_no,
                    'date': current_date.strftime('%Y-%m-%d'),
                    'reason': 'Train not running on this day'
                })
                continue
            
            report['valid_trains'].append({
                'segment': idx + 1,
                'train_no': train_no,
                'date': current_date.strftime('%Y-%m-%d')
            })
            
            # Check transfer if not last segment
            if idx < len(route_trains) - 1:
                can_transfer, next_day = self.can_transfer_between_trains(
                    arrival_time, 
                    departure_time,
                    min_transfer_time_minutes=15,
                    arrival_date=current_date
                )
                
                if can_transfer:
                    # Update date if transfer crosses midnight
                    if next_day:
                        current_date = current_date + timedelta(days=1)
                        report['notes'].append(
                            f"Transfer at segment {idx+1} crosses midnight. Next train on {current_date.strftime('%Y-%m-%d')}"
                        )
                    
                    report['valid_transfers'].append({
                        'transfer_at': f"Segment {idx+1} to {idx+2}",
                        'arrival_time': arrival_time,
                        'departure_time': departure_time,
                        'next_day': next_day or False
                    })
                else:
                    report['is_valid'] = False
                    report['invalid_transfers'].append({
                        'transfer_at': f"Segment {idx+1} to {idx+2}",
                        'arrival_time': arrival_time,
                        'departure_time': departure_time,
                        'reason': 'Insufficient transfer time'
                    })
        
        return report
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# Example usage
if __name__ == '__main__':
    # Initialize validator
    validator = TrainRunningDaysValidator('production.db')
    
    # Load running days from CSV
    validator.load_running_days_from_csv('dataset/train_info.csv')
    
    # Test: Check if train 10103 runs on a specific date
    test_date = datetime(2026, 1, 26)  # Monday
    is_running = validator.is_train_running_on_date(10103, test_date)
    print(f"Train 10103 running on {test_date.strftime('%A, %Y-%m-%d')}: {is_running}")
    
    # Get all trains running on a date
    trains = validator.get_trains_running_on_date(test_date)
    print(f"Total trains running on {test_date.strftime('%Y-%m-%d')}: {len(trains)}")
    
    # Test transfer
    can_transfer, next_day = validator.can_transfer_between_trains('23:00', '02:00')
    print(f"Can transfer from 23:00 to 02:00: {can_transfer}, Next day: {next_day}")
    
    validator.close()
