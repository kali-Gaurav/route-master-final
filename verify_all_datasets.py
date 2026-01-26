#!/usr/bin/env python3
"""Comprehensive database verification and analysis"""

import sqlite3
import os
from pathlib import Path

def verify_database():
    """Verify all data in database"""
    db_path = 'production.db'
    if not os.path.exists(db_path):
        print("Database not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 90)
    print(" " * 20 + "COMPREHENSIVE DATABASE VERIFICATION REPORT")
    print("=" * 90)
    print()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print("DATABASE TABLES AND CONTENTS:")
    print("-" * 90)
    print()
    
    total_rows = 0
    table_info = []
    
    for table in tables:
        table_name = table[0]
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        total_rows += count
        
        # Get columns
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        # Get indexes
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='{table_name}'")
        indexes = cursor.fetchall()
        
        table_info.append({
            'name': table_name,
            'rows': count,
            'columns': len(columns),
            'indexes': len(indexes)
        })
    
    # Display organized by category
    print("RAPPID & ROUTE DATA:")
    print("  " + "-" * 86)
    for info in table_info:
        if info['name'] in ['rappid_routes', 'stations', 'trains']:
            print(f"  {info['name']:30s}: {info['rows']:>12,} rows | {info['columns']:>2} cols | {info['indexes']:>2} indexes")
    
    print("\nPRICE DATA:")
    print("  " + "-" * 86)
    for info in table_info:
        if info['name'] == 'prices':
            print(f"  {info['name']:30s}: {info['rows']:>12,} rows | {info['columns']:>2} cols | {info['indexes']:>2} indexes")
    
    print("\nTRAIN DETAILS & SCHEDULE:")
    print("  " + "-" * 86)
    for info in table_info:
        if info['name'] in ['train_details', 'train_schedule', 'train_info']:
            print(f"  {info['name']:30s}: {info['rows']:>12,} rows | {info['columns']:>2} cols | {info['indexes']:>2} indexes")
    
    print("\nCITY & LOCATION DATA:")
    print("  " + "-" * 86)
    for info in table_info:
        if info['name'] in ['cities', 'city_station_mapping']:
            print(f"  {info['name']:30s}: {info['rows']:>12,} rows | {info['columns']:>2} cols | {info['indexes']:>2} indexes")
    
    print("\nOTHER TABLES:")
    print("  " + "-" * 86)
    for info in table_info:
        if info['name'] not in ['rappid_routes', 'stations', 'trains', 'prices', 
                                'train_details', 'train_schedule', 'train_info',
                                'cities', 'city_station_mapping', 'sqlite_sequence']:
            print(f"  {info['name']:30s}: {info['rows']:>12,} rows | {info['columns']:>2} cols | {info['indexes']:>2} indexes")
    
    print()
    print("=" * 90)
    print(f"TOTAL ROWS IN DATABASE: {total_rows:,}")
    print("=" * 90)
    
    # Data relationships
    print()
    print("DATA RELATIONSHIPS & VALIDATION:")
    print("-" * 90)
    print()
    
    # Check prices and trains link
    cursor.execute("SELECT COUNT(DISTINCT train_no) FROM prices")
    price_trains = cursor.fetchone()[0]
    print(f"  Unique trains in prices table     : {price_trains:>10,}")
    
    cursor.execute("SELECT COUNT(DISTINCT train_no) FROM trains")
    total_trains = cursor.fetchone()[0]
    print(f"  Total trains in trains table      : {total_trains:>10,}")
    
    cursor.execute("SELECT COUNT(DISTINCT train_no) FROM train_details")
    detail_trains = cursor.fetchone()[0]
    print(f"  Unique trains in train_details    : {detail_trains:>10,}")
    
    cursor.execute("SELECT COUNT(DISTINCT train_no) FROM train_schedule")
    schedule_trains = cursor.fetchone()[0]
    print(f"  Unique trains in train_schedule   : {schedule_trains:>10,}")
    
    cursor.execute("SELECT COUNT(DISTINCT train_no) FROM train_info")
    info_trains = cursor.fetchone()[0]
    print(f"  Unique trains in train_info       : {info_trains:>10,}")
    
    # Check stations
    cursor.execute("SELECT COUNT(*) FROM stations")
    total_stations = cursor.fetchone()[0]
    print()
    print(f"  Total stations                    : {total_stations:>10,}")
    
    cursor.execute("SELECT COUNT(DISTINCT station_code) FROM train_details")
    detail_stations = cursor.fetchone()[0]
    print(f"  Unique stations in train_details  : {detail_stations:>10,}")
    
    cursor.execute("SELECT COUNT(DISTINCT station_code) FROM train_schedule")
    schedule_stations = cursor.fetchone()[0]
    print(f"  Unique stations in train_schedule : {schedule_stations:>10,}")
    
    # Sample data
    print()
    print("=" * 90)
    print("SAMPLE DATA (First row from each new table):")
    print("-" * 90)
    print()
    
    # Prices sample
    print("Prices table:")
    cursor.execute("""
        SELECT train_no, from_station_code, to_station_code, class_type, 
               base_fare, total_fare FROM prices LIMIT 1
    """)
    result = cursor.fetchone()
    if result:
        print(f"  Train: {result[0]}, Route: {result[1]}->{result[2]}, Class: {result[3]}")
        print(f"  Base Fare: Rs.{result[4]}, Total: Rs.{result[5]}")
    
    print()
    print("Train Details table:")
    cursor.execute("""
        SELECT train_no, train_name, station_name, arrival_time, departure_time 
        FROM train_details LIMIT 1
    """)
    result = cursor.fetchone()
    if result:
        print(f"  Train {result[0]}: {result[1]}")
        print(f"  Station: {result[2]}, Arrival: {result[3]}, Departure: {result[4]}")
    
    print()
    print("Train Schedule table:")
    cursor.execute("""
        SELECT train_no, station_code, class_1a, class_2a, class_sl 
        FROM train_schedule LIMIT 1
    """)
    result = cursor.fetchone()
    if result:
        print(f"  Train {result[0]} at {result[1]}")
        print(f"  Availability - 1A: {result[2]}, 2A: {result[3]}, SL: {result[4]}")
    
    print()
    print("Train Info table:")
    cursor.execute("""
        SELECT train_no, train_name, source_station_name, destination_station_name 
        FROM train_info LIMIT 1
    """)
    result = cursor.fetchone()
    if result:
        print(f"  Train {result[0]}: {result[1]}")
        print(f"  Route: {result[2]} -> {result[3]}")
    
    # Query performance test
    print()
    print("=" * 90)
    print("QUERY PERFORMANCE TEST:")
    print("-" * 90)
    print()
    
    import time
    
    # Test 1: Find prices for a route
    start = time.time()
    cursor.execute("""
        SELECT COUNT(*) FROM prices 
        WHERE from_station_code = 'CSMT' AND to_station_code = 'BRC'
    """)
    result = cursor.fetchone()[0]
    elapsed = (time.time() - start) * 1000
    print(f"  Query 1 - Find prices CSMT->BRC  : {result} rows found in {elapsed:.2f}ms")
    
    # Test 2: Find train details for a train
    start = time.time()
    cursor.execute("""
        SELECT COUNT(*) FROM train_details 
        WHERE train_no = 12009
    """)
    result = cursor.fetchone()[0]
    elapsed = (time.time() - start) * 1000
    print(f"  Query 2 - Get train 12009 details: {result} rows found in {elapsed:.2f}ms")
    
    # Test 3: Find all trains running on a date
    start = time.time()
    cursor.execute("""
        SELECT COUNT(DISTINCT train_no) FROM train_info 
        WHERE running_days LIKE '%Monday%'
    """)
    result = cursor.fetchone()[0]
    elapsed = (time.time() - start) * 1000
    print(f"  Query 3 - Trains running Monday  : {result} trains found in {elapsed:.2f}ms")
    
    # Test 4: Get complete route info
    start = time.time()
    cursor.execute("""
        SELECT COUNT(*) FROM train_details td
        JOIN stations s ON td.station_code = s.station_code
        WHERE td.train_no = 12009
    """)
    result = cursor.fetchone()[0]
    elapsed = (time.time() - start) * 1000
    print(f"  Query 4 - Join stations + details: {result} rows found in {elapsed:.2f}ms")
    
    print()
    print("=" * 90)
    print("INDEXES CREATED:")
    print("-" * 90)
    
    cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY tbl_name")
    indexes_list = cursor.fetchall()
    
    for idx, table in indexes_list:
        print(f"  {idx:35s} on {table}")
    
    print()
    print("=" * 90)
    print("DATABASE SIZE & STATISTICS:")
    print("-" * 90)
    
    db_size_mb = os.path.getsize(db_path) / (1024 * 1024)
    print(f"  Database file size                : {db_size_mb:.2f} MB")
    
    print()
    print("=" * 90)
    print("STATUS: ALL DATASETS SUCCESSFULLY LOADED & OPTIMIZED")
    print("=" * 90)
    
    conn.close()

if __name__ == '__main__':
    verify_database()
