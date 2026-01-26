#!/usr/bin/env python3
"""Check current database contents and dataset folder structure"""

import sqlite3
import os
from pathlib import Path

def check_database():
    """Check what's currently in the database"""
    db_path = 'production.db'
    if not os.path.exists(db_path):
        print("Database file not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print("=" * 80)
    print("CURRENT DATABASE TABLES")
    print("=" * 80)
    print()
    
    if tables:
        for table in tables:
            table_name = table[0]
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            # Get columns
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"Table: {table_name}")
            print(f"  Rows: {count:,}")
            print(f"  Columns: {len(columns)}")
            for col in columns:
                print(f"    - {col[1]}: {col[2]}")
            print()
    else:
        print("No tables found in database")
    
    conn.close()

def check_dataset_folder():
    """Check what files are in the dataset folder"""
    dataset_path = Path('dataset')
    if not dataset_path.exists():
        print("Dataset folder not found!")
        return
    
    print("=" * 80)
    print("DATASET FOLDER CONTENTS")
    print("=" * 80)
    print()
    
    csv_files = list(dataset_path.glob('*.csv'))
    xlsx_files = list(dataset_path.glob('*.xlsx'))
    json_files = list(dataset_path.glob('*.json'))
    
    all_files = csv_files + xlsx_files + json_files
    
    if not all_files:
        print("No data files found in dataset folder")
        return
    
    print(f"Found {len(all_files)} data files:\n")
    
    for file in sorted(all_files):
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"  [{file.suffix.upper()[1:]}] {file.name} ({size_mb:.2f} MB)")
        
        # For CSV files, show info about rows and columns
        if file.suffix.lower() == '.csv':
            try:
                import pandas as pd
                df = pd.read_csv(file)
                print(f"       Rows: {len(df):,}, Columns: {len(df.columns)}")
                print(f"       Columns: {', '.join(df.columns[:5])}" + ("..." if len(df.columns) > 5 else ""))
            except Exception as e:
                print(f"       Error reading file: {e}")
        print()

if __name__ == '__main__':
    check_database()
    print()
    check_dataset_folder()
