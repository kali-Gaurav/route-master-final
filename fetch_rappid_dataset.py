#!/usr/bin/env python3
"""
Advanced RAPPID Dataset Fetcher
Fetches comprehensive train data from RAPPID API and creates a structured dataset
"""
import requests
import pandas as pd
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import concurrent.futures

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAPPIDDatasetFetcher:
    """Fetch and structure train data from RAPPID API"""
    
    def __init__(self, input_csv: str = 'dataset/Train_details.csv', output_csv: str = 'dataset/RAPPID_Complete_Dataset.csv'):
        self.input_csv = input_csv
        self.output_csv = output_csv
        self.api_base = 'https://rappid.in/apis/train.php'
        self.session = requests.Session()
        self.session.timeout = 10
        self.trains_data = []
        self.errors = []
        
    def get_unique_trains(self) -> List[str]:
        """Extract unique train numbers from existing dataset"""
        try:
            df = pd.read_csv(self.input_csv)
            trains = sorted(df['Train No'].unique().astype(str).tolist())
            logger.info(f"Found {len(trains)} unique trains in dataset")
            return trains
        except Exception as e:
            logger.error(f"Error reading dataset: {e}")
            return []
    
    def fetch_train_data(self, train_no: str) -> Optional[Dict]:
        """Fetch data for a single train from RAPPID API"""
        try:
            url = f'{self.api_base}?train_no={train_no}'
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data
                else:
                    logger.debug(f"Train {train_no}: API returned false success")
                    return None
            else:
                logger.debug(f"Train {train_no}: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.warning(f"Train {train_no}: Request timeout")
            self.errors.append({'train_no': train_no, 'error': 'Timeout'})
            return None
        except Exception as e:
            logger.warning(f"Train {train_no}: {type(e).__name__}")
            self.errors.append({'train_no': train_no, 'error': str(e)})
            return None
    
    def parse_train_response(self, train_no: str, api_response: Dict) -> List[Dict]:
        """Parse RAPPID API response into structured rows"""
        rows = []
        
        try:
            train_name = api_response.get('train_name', '')
            updated_time = api_response.get('updated_time', '')
            stations = api_response.get('data', [])
            
            for idx, station in enumerate(stations):
                row = {
                    'train_no': train_no,
                    'train_name': train_name,
                    'station_sequence': idx + 1,
                    'station_name': station.get('station_name', ''),
                    'distance_km': self._parse_distance(station.get('distance', '')),
                    'timing': station.get('timing', ''),
                    'delay': station.get('delay', ''),
                    'platform': station.get('platform', ''),
                    'halt_duration': station.get('halt', ''),
                    'is_current_station': station.get('is_current_station', False),
                    'updated_time': updated_time,
                    'fetch_timestamp': datetime.now().isoformat()
                }
                rows.append(row)
            
            return rows
        except Exception as e:
            logger.error(f"Error parsing train {train_no}: {e}")
            return []
    
    def _parse_distance(self, distance_str: str) -> Optional[float]:
        """Extract numeric distance from string like '5 km'"""
        try:
            if distance_str == '-' or not distance_str:
                return None
            # Extract first number
            num = float(distance_str.split()[0])
            return num
        except:
            return None
    
    def fetch_all_trains(self, max_workers: int = 5, start_index: int = 0):
        """Fetch data for all trains with concurrent requests"""
        trains = self.get_unique_trains()[start_index:]
        total = len(trains)
        
        logger.info(f"Starting to fetch {total} trains (max {max_workers} concurrent)")
        
        success_count = 0
        fail_count = 0
        
        # Fetch with rate limiting
        for idx, train_no in enumerate(trains, 1):
            try:
                logger.info(f"[{idx}/{total}] Fetching train {train_no}...")
                
                api_response = self.fetch_train_data(train_no)
                
                if api_response:
                    rows = self.parse_train_response(train_no, api_response)
                    self.trains_data.extend(rows)
                    success_count += 1
                    logger.info(f"  ✓ Got {len(rows)} stations")
                else:
                    fail_count += 1
                
                # Rate limiting: wait between requests
                time.sleep(0.5)
                
                # Progress checkpoint every 50 trains
                if idx % 50 == 0:
                    logger.info(f"Progress: {idx}/{total} trains fetched. Success: {success_count}, Failed: {fail_count}")
                    
            except KeyboardInterrupt:
                logger.info("Fetching interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error for train {train_no}: {e}")
                fail_count += 1
        
        logger.info(f"\nFetching complete!")
        logger.info(f"  ✓ Success: {success_count}/{total}")
        logger.info(f"  ✗ Failed: {fail_count}/{total}")
        logger.info(f"  Total rows: {len(self.trains_data)}")
    
    def save_to_csv(self):
        """Save fetched data to CSV"""
        if not self.trains_data:
            logger.error("No data to save!")
            return False
        
        try:
            df = pd.DataFrame(self.trains_data)
            
            # Reorder columns for better readability
            columns = [
                'train_no', 'train_name', 'station_sequence', 'station_name',
                'distance_km', 'timing', 'delay', 'platform', 'halt_duration',
                'is_current_station', 'updated_time', 'fetch_timestamp'
            ]
            df = df[columns]
            
            # Create dataset directory if needed
            Path('dataset').mkdir(exist_ok=True)
            
            # Save to CSV
            df.to_csv(self.output_csv, index=False)
            logger.info(f"\n✓ Dataset saved to: {self.output_csv}")
            logger.info(f"  Rows: {len(df)}")
            logger.info(f"  Columns: {len(columns)}")
            logger.info(f"  Unique trains: {df['train_no'].nunique()}")
            logger.info(f"  Size: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
            
            return True
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
            return False
    
    def save_error_log(self):
        """Save errors to log file"""
        if not self.errors:
            return
        
        try:
            error_df = pd.DataFrame(self.errors)
            error_csv = self.output_csv.replace('.csv', '_errors.csv')
            error_df.to_csv(error_csv, index=False)
            logger.info(f"Error log saved: {error_csv} ({len(self.errors)} errors)")
        except Exception as e:
            logger.error(f"Error saving error log: {e}")

def main():
    """Main execution"""
    import sys
    
    print("\n" + "="*80)
    print("RAPPID ADVANCED DATASET FETCHER")
    print("="*80)
    print("This will fetch comprehensive train data from RAPPID API")
    print("and create a structured CSV dataset\n")
    
    # Check if dataset exists
    if not Path('dataset/Train_details.csv').exists():
        print("ERROR: dataset/Train_details.csv not found!")
        print("Please ensure dataset folder has the train details file")
        return
    
    # Initialize fetcher
    fetcher = RAPPIDDatasetFetcher()
    
    # Get unique trains
    trains = fetcher.get_unique_trains()
    if not trains:
        print("No trains found in dataset!")
        return
    
    print(f"\nFound {len(trains)} unique trains")
    print(f"Sample trains: {', '.join(trains[:5])}\n")
    
    # Ask for confirmation
    response = input("Start fetching data from RAPPID API? (y/n): ").lower()
    if response != 'y':
        print("Cancelled.")
        return
    
    # Fetch data
    print("\nFetching data (this may take several minutes)...\n")
    fetcher.fetch_all_trains()
    
    # Save results
    if fetcher.trains_data:
        fetcher.save_to_csv()
        fetcher.save_error_log()
        
        print("\n" + "="*80)
        print("✓ DATASET CREATION COMPLETE!")
        print("="*80)
    else:
        print("\n✗ No data was fetched. Please check network and API availability.")

if __name__ == '__main__':
    main()
