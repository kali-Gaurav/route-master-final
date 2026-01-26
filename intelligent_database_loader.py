#!/usr/bin/env python3
"""
Intelligent Database Loader
Loads all datasets from folder into database with proper separation and optimization
"""

import sqlite3
import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntelligentDatabaseLoader:
    """Load all datasets intelligently into database"""
    
    def __init__(self, db_path='production.db', dataset_path='dataset'):
        self.db_path = db_path
        self.dataset_path = Path(dataset_path)
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        logger.info(f"Connected to database: {self.db_path}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def create_schemas(self):
        """Create all necessary table schemas"""
        logger.info("=" * 80)
        logger.info("CREATING DATABASE SCHEMAS")
        logger.info("=" * 80)
        
        # Table 1: Price Data (from price_data.csv)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                train_no INTEGER,
                from_station_code TEXT,
                to_station_code TEXT,
                class_type TEXT,
                base_fare REAL,
                reservation_charge REAL,
                superfast_charge REAL,
                fuel_amount REAL,
                total_concession REAL,
                concession_percentage REAL,
                adult REAL,
                child REAL,
                senior_citizen REAL,
                total_fare REAL,
                contingency_surcharge REAL,
                gst_percent REAL,
                gst_amount REAL,
                total_with_gst REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (train_no) REFERENCES trains(train_no)
            )
        ''')
        logger.info("Created table: prices")
        
        # Table 2: Train Details (from Train_details_CLEANED.csv)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS train_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                train_no INTEGER,
                train_name TEXT,
                sequence_number INTEGER,
                station_code TEXT,
                station_name TEXT,
                arrival_time TEXT,
                departure_time TEXT,
                halt_minutes INTEGER,
                distance_from_source REAL,
                route_day_indicator TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (train_no) REFERENCES trains(train_no),
                FOREIGN KEY (station_code) REFERENCES stations(station_code),
                UNIQUE(train_no, sequence_number, station_code)
            )
        ''')
        logger.info("Created table: train_details")
        
        # Table 3: Train Schedule (from train_schedule.csv)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS train_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                train_no INTEGER,
                station_code TEXT,
                class_1a INTEGER,
                class_2a INTEGER,
                class_3a INTEGER,
                class_sl INTEGER,
                class_fc INTEGER,
                class_cc INTEGER,
                coaches_available TEXT,
                total_coaches INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (train_no) REFERENCES trains(train_no),
                FOREIGN KEY (station_code) REFERENCES stations(station_code),
                UNIQUE(train_no, station_code)
            )
        ''')
        logger.info("Created table: train_schedule")
        
        # Table 4: Cities (from cities_locations.json)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city_name TEXT UNIQUE,
                latitude REAL,
                longitude REAL,
                state TEXT,
                country TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("Created table: cities")
        
        # Table 5: City-Station Mapping (from station_city_mapping.json)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS city_station_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                station_code TEXT,
                station_name TEXT,
                city_name TEXT,
                state TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (station_code) REFERENCES stations(station_code),
                FOREIGN KEY (city_name) REFERENCES cities(city_name),
                UNIQUE(station_code)
            )
        ''')
        logger.info("Created table: city_station_mapping")
        
        # Table 6: Train Info (from train_info.csv - for quick lookups)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS train_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                train_no INTEGER UNIQUE,
                train_name TEXT,
                source_station_name TEXT,
                destination_station_name TEXT,
                running_days TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (train_no) REFERENCES trains(train_no)
            )
        ''')
        logger.info("Created table: train_info")
        
        self.conn.commit()
    
    def load_price_data(self):
        """Load price data from CSV"""
        logger.info("\n" + "=" * 80)
        logger.info("LOADING PRICE DATA")
        logger.info("=" * 80)
        
        price_file = self.dataset_path / 'price_data.csv'
        if not price_file.exists():
            logger.warning(f"Price file not found: {price_file}")
            return 0
        
        try:
            # Check if data already exists
            self.cursor.execute("SELECT COUNT(*) FROM prices")
            count = self.cursor.fetchone()[0]
            if count > 0:
                logger.info(f"Price data already loaded ({count:,} rows)")
                return count
            
            logger.info(f"Reading {price_file.name}...")
            df = pd.read_csv(price_file, low_memory=False)
            
            # Rename columns to match schema
            column_mapping = {
                'train_no': 'train_no',
                'fromStnCode': 'from_station_code',
                'toStnCode': 'to_station_code',
                'classCode': 'class_type',
                'baseFare': 'base_fare',
                'reservationCharge': 'reservation_charge',
                'superfastCharge': 'superfast_charge',
                'fuelAmount': 'fuel_amount',
                'totalConcession': 'total_concession',
                'concessionPercentage': 'concession_percentage',
                'adult': 'adult',
                'child': 'child',
                'seniorCitizen': 'senior_citizen',
                'totalFare': 'total_fare',
                'contingencySurcharge': 'contingency_surcharge',
                'gstPercent': 'gst_percent',
                'gstAmount': 'gst_amount',
                'totalWithGst': 'total_with_gst'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Insert data
            df_filtered = df[[col for col in column_mapping.values() if col in df.columns]]
            df_filtered.to_sql('prices', self.conn, if_exists='append', index=False)
            
            self.conn.commit()
            loaded = len(df)
            logger.info(f"Loaded {loaded:,} price records")
            return loaded
        
        except Exception as e:
            logger.error(f"Error loading price data: {e}")
            return 0
    
    def load_train_details(self):
        """Load train details from CSV"""
        logger.info("\n" + "=" * 80)
        logger.info("LOADING TRAIN DETAILS")
        logger.info("=" * 80)
        
        detail_file = self.dataset_path / 'Train_details_CLEANED.csv'
        if not detail_file.exists():
            logger.warning(f"Train details file not found: {detail_file}")
            return 0
        
        try:
            # Check if data already exists
            self.cursor.execute("SELECT COUNT(*) FROM train_details")
            count = self.cursor.fetchone()[0]
            if count > 0:
                logger.info(f"Train details already loaded ({count:,} rows)")
                return count
            
            logger.info(f"Reading {detail_file.name}...")
            df = pd.read_csv(detail_file, low_memory=False)
            
            # Rename columns to match schema
            column_mapping = {
                'Train No': 'train_no',
                'Train Name': 'train_name',
                'SEQ': 'sequence_number',
                'Station Code': 'station_code',
                'Station Name': 'station_name',
                'Arrival time': 'arrival_time',
                'Departure time': 'departure_time',
                'Halt': 'halt_minutes',
                'Distance from source': 'distance_from_source',
                'Route day': 'route_day_indicator'
            }
            
            df = df.rename(columns=column_mapping)
            df_filtered = df[[col for col in column_mapping.values() if col in df.columns]]
            
            # Handle duplicates (keep first occurrence per train+sequence+station)
            df_filtered = df_filtered.drop_duplicates(
                subset=['train_no', 'sequence_number', 'station_code'],
                keep='first'
            )
            
            df_filtered.to_sql('train_details', self.conn, if_exists='append', index=False)
            
            self.conn.commit()
            loaded = len(df_filtered)
            logger.info(f"Loaded {loaded:,} train detail records")
            return loaded
        
        except Exception as e:
            logger.error(f"Error loading train details: {e}")
            return 0
    
    def load_train_schedule(self):
        """Load train schedule from CSV"""
        logger.info("\n" + "=" * 80)
        logger.info("LOADING TRAIN SCHEDULE")
        logger.info("=" * 80)
        
        schedule_file = self.dataset_path / 'train_schedule.csv'
        if not schedule_file.exists():
            logger.warning(f"Train schedule file not found: {schedule_file}")
            return 0
        
        try:
            # Check if data already exists
            self.cursor.execute("SELECT COUNT(*) FROM train_schedule")
            count = self.cursor.fetchone()[0]
            if count > 0:
                logger.info(f"Train schedule already loaded ({count:,} rows)")
                return count
            
            logger.info(f"Reading {schedule_file.name}...")
            df = pd.read_csv(schedule_file, low_memory=False)
            
            # Rename columns to match schema
            column_mapping = {
                'Train_No': 'train_no',
                'Station_Code': 'station_code',
                '1A': 'class_1a',
                '2A': 'class_2a',
                '3A': 'class_3a',
                'SL': 'class_sl',
                'FC': 'class_fc',
                'CC': 'class_cc'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Use only available columns
            available_cols = [col for col in column_mapping.values() if col in df.columns]
            df_filtered = df[available_cols]
            
            # Handle duplicates
            df_filtered = df_filtered.drop_duplicates(
                subset=['train_no', 'station_code'],
                keep='first'
            )
            
            df_filtered.to_sql('train_schedule', self.conn, if_exists='append', index=False)
            
            self.conn.commit()
            loaded = len(df_filtered)
            logger.info(f"Loaded {loaded:,} train schedule records")
            return loaded
        
        except Exception as e:
            logger.error(f"Error loading train schedule: {e}")
            return 0
    
    def load_cities(self):
        """Load cities from JSON"""
        logger.info("\n" + "=" * 80)
        logger.info("LOADING CITIES")
        logger.info("=" * 80)
        
        cities_file = self.dataset_path / 'cities_locations.json'
        if not cities_file.exists():
            logger.warning(f"Cities file not found: {cities_file}")
            return 0
        
        try:
            # Check if data already exists
            self.cursor.execute("SELECT COUNT(*) FROM cities")
            count = self.cursor.fetchone()[0]
            if count > 0:
                logger.info(f"Cities already loaded ({count:,} rows)")
                return count
            
            logger.info(f"Reading {cities_file.name}...")
            with open(cities_file, 'r') as f:
                cities_data = json.load(f)
            
            if isinstance(cities_data, dict):
                cities_list = cities_data.get('cities', [])
            else:
                cities_list = cities_data
            
            logger.info(f"Found {len(cities_list)} cities")
            
            for city in cities_list:
                self.cursor.execute('''
                    INSERT OR IGNORE INTO cities (city_name, latitude, longitude, state, country)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    city.get('city_name'),
                    city.get('latitude'),
                    city.get('longitude'),
                    city.get('state'),
                    city.get('country')
                ))
            
            self.conn.commit()
            logger.info(f"Loaded {len(cities_list)} cities")
            return len(cities_list)
        
        except Exception as e:
            logger.error(f"Error loading cities: {e}")
            return 0
    
    def load_city_station_mapping(self):
        """Load city-station mapping from JSON"""
        logger.info("\n" + "=" * 80)
        logger.info("LOADING CITY-STATION MAPPING")
        logger.info("=" * 80)
        
        mapping_file = self.dataset_path / 'station_city_mapping.json'
        if not mapping_file.exists():
            logger.warning(f"Mapping file not found: {mapping_file}")
            return 0
        
        try:
            # Check if data already exists
            self.cursor.execute("SELECT COUNT(*) FROM city_station_mapping")
            count = self.cursor.fetchone()[0]
            if count > 0:
                logger.info(f"City-station mapping already loaded ({count:,} rows)")
                return count
            
            logger.info(f"Reading {mapping_file.name}...")
            with open(mapping_file, 'r') as f:
                mapping_data = json.load(f)
            
            total_loaded = 0
            
            if isinstance(mapping_data, dict):
                for station_code, mapping_info in mapping_data.items():
                    if isinstance(mapping_info, dict):
                        self.cursor.execute('''
                            INSERT OR IGNORE INTO city_station_mapping 
                            (station_code, station_name, city_name, state)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            station_code,
                            mapping_info.get('station_name'),
                            mapping_info.get('city_name'),
                            mapping_info.get('state')
                        ))
                        total_loaded += 1
            
            self.conn.commit()
            logger.info(f"Loaded {total_loaded} city-station mappings")
            return total_loaded
        
        except Exception as e:
            logger.error(f"Error loading city-station mapping: {e}")
            return 0
    
    def load_train_info(self):
        """Load train info from CSV"""
        logger.info("\n" + "=" * 80)
        logger.info("LOADING TRAIN INFO")
        logger.info("=" * 80)
        
        info_file = self.dataset_path / 'train_info.csv'
        if not info_file.exists():
            logger.warning(f"Train info file not found: {info_file}")
            return 0
        
        try:
            # Check if data already exists
            self.cursor.execute("SELECT COUNT(*) FROM train_info")
            count = self.cursor.fetchone()[0]
            if count > 0:
                logger.info(f"Train info already loaded ({count:,} rows)")
                return count
            
            logger.info(f"Reading {info_file.name}...")
            df = pd.read_csv(info_file)
            
            # Use available columns
            df_filtered = df[['Train_No', 'Train_Name', 'Source_Station_Name', 'Destination_Station_Name', 'days']]
            df_filtered.columns = ['train_no', 'train_name', 'source_station_name', 'destination_station_name', 'running_days']
            
            # Remove duplicates
            df_filtered = df_filtered.drop_duplicates(subset=['train_no'], keep='first')
            
            df_filtered.to_sql('train_info', self.conn, if_exists='append', index=False)
            
            self.conn.commit()
            loaded = len(df_filtered)
            logger.info(f"Loaded {loaded:,} train info records")
            return loaded
        
        except Exception as e:
            logger.error(f"Error loading train info: {e}")
            return 0
    
    def create_indexes(self):
        """Create indexes for fast lookups"""
        logger.info("\n" + "=" * 80)
        logger.info("CREATING INDEXES FOR PERFORMANCE")
        logger.info("=" * 80)
        
        indexes = [
            # Prices indexes
            ('prices', 'train_no', 'idx_prices_train_no'),
            ('prices', 'from_station_code, to_station_code', 'idx_prices_route'),
            ('prices', 'class_type', 'idx_prices_class'),
            
            # Train details indexes
            ('train_details', 'train_no', 'idx_details_train_no'),
            ('train_details', 'station_code', 'idx_details_station'),
            ('train_details', 'train_no, sequence_number', 'idx_details_sequence'),
            
            # Train schedule indexes
            ('train_schedule', 'train_no', 'idx_schedule_train_no'),
            ('train_schedule', 'station_code', 'idx_schedule_station'),
            
            # City-station mapping index
            ('city_station_mapping', 'city_name', 'idx_city_mapping'),
            ('city_station_mapping', 'station_code', 'idx_station_mapping'),
            
            # Train info indexes
            ('train_info', 'train_no', 'idx_train_info_no'),
            ('train_info', 'source_station_name, destination_station_name', 'idx_train_info_route'),
        ]
        
        created_count = 0
        for table, columns, index_name in indexes:
            try:
                self.cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({columns})")
                logger.info(f"  Created index: {index_name}")
                created_count += 1
            except Exception as e:
                logger.warning(f"  Could not create index {index_name}: {e}")
        
        self.conn.commit()
        logger.info(f"Created {created_count} indexes")
    
    def generate_summary(self):
        """Generate summary of loaded data"""
        logger.info("\n" + "=" * 80)
        logger.info("DATABASE SUMMARY")
        logger.info("=" * 80)
        print()
        
        tables_to_check = [
            'prices', 'train_details', 'train_schedule', 'cities',
            'city_station_mapping', 'train_info'
        ]
        
        for table in tables_to_check:
            try:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = self.cursor.fetchone()[0]
                print(f"  {table:25s}: {count:>10,} rows")
            except:
                pass
        
        print()
        logger.info("=" * 80)
    
    def load_all(self):
        """Load all datasets"""
        logger.info("STARTING INTELLIGENT DATABASE LOADER")
        logger.info(f"Database: {self.db_path}")
        logger.info(f"Dataset folder: {self.dataset_path}")
        
        try:
            self.connect()
            self.create_schemas()
            
            self.load_price_data()
            self.load_train_details()
            self.load_train_schedule()
            self.load_cities()
            self.load_city_station_mapping()
            self.load_train_info()
            
            self.create_indexes()
            self.generate_summary()
            
            logger.info("\n" + "=" * 80)
            logger.info("ALL DATASETS LOADED SUCCESSFULLY!")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Error during loading: {e}")
        finally:
            self.close()

if __name__ == '__main__':
    loader = IntelligentDatabaseLoader()
    loader.load_all()
