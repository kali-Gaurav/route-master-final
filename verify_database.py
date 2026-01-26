#!/usr/bin/env python3
"""Verify database is ready for route generation"""

import sqlite3
import sys

def verify_database():
    """Check if database has all required tables and data"""
    try:
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()
        
        print("=" * 80)
        print("DATABASE VERIFICATION FOR ROUTE GENERATION")
        print("=" * 80)
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print("\n✓ TABLES IN DATABASE:")
        for table in tables:
            print(f"    {table[0]}")
        
        if not tables:
            print("    ❌ NO TABLES FOUND!")
            return False
        
        # Check train_running_days table
        print("\n✓ train_running_days TABLE SCHEMA:")
        cursor.execute("PRAGMA table_info(train_running_days)")
        columns = cursor.fetchall()
        
        if not columns:
            print("    ❌ Table does not exist!")
            return False
            
        for col in columns:
            col_name, col_type = col[1], col[2]
            print(f"    - {col_name}: {col_type}")
        
        # Check row count
        cursor.execute("SELECT COUNT(*) FROM train_running_days")
        count = cursor.fetchone()[0]
        print(f"\n✓ DATA LOADED:")
        print(f"    Total trains: {count:,}")
        
        if count == 0:
            print("    ❌ NO DATA LOADED!")
            return False
        
        if count != 9880:
            print(f"    ⚠️  WARNING: Expected 9,880 trains, found {count:,}")
        else:
            print(f"    ✅ Perfect match with RAPPID dataset (9,880 trains)")
        
        # Check indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='train_running_days'")
        indexes = cursor.fetchall()
        
        print(f"\n✓ INDEXES ON train_running_days:")
        if indexes:
            for idx in indexes:
                print(f"    - {idx[0]}")
        else:
            print("    ⚠️  No indexes found")
        
        # Sample data verification
        print(f"\n✓ SAMPLE DATA (first 3 trains):")
        cursor.execute("SELECT train_no, train_name, monday, tuesday, wednesday, thursday, friday, saturday, sunday FROM train_running_days LIMIT 3")
        samples = cursor.fetchall()
        
        for row in samples:
            train_no, train_name, mon, tue, wed, thu, fri, sat, sun = row
            days = []
            if mon: days.append("Mon")
            if tue: days.append("Tue")
            if wed: days.append("Wed")
            if thu: days.append("Thu")
            if fri: days.append("Fri")
            if sat: days.append("Sat")
            if sun: days.append("Sun")
            print(f"    Train {train_no} ({train_name}): {', '.join(days) if days else 'None'}")
        
        # Verify required columns exist
        print(f"\n✓ REQUIRED COLUMNS CHECK:")
        required_cols = ['train_no', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        col_names = [col[1] for col in columns]
        
        all_present = True
        for col in required_cols:
            if col in col_names:
                print(f"    ✅ {col}")
            else:
                print(f"    ❌ {col} - MISSING!")
                all_present = False
        
        # Verify data integrity
        print(f"\n✓ DATA INTEGRITY CHECK:")
        
        # Check for any trains with no days
        cursor.execute("""
            SELECT COUNT(*) FROM train_running_days 
            WHERE (monday + tuesday + wednesday + thursday + friday + saturday + sunday) = 0
        """)
        no_days = cursor.fetchone()[0]
        
        if no_days > 0:
            print(f"    ⚠️  {no_days} trains have no running days (potential issue)")
        else:
            print(f"    ✅ All 9,880 trains have at least one running day")
        
        # Check distribution
        print(f"\n✓ TRAINS BY DAY OF WEEK:")
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day_col, day_name in zip(days, day_names):
            cursor.execute(f"SELECT COUNT(*) FROM train_running_days WHERE {day_col} = 1")
            count = cursor.fetchone()[0]
            pct = (count / 9880) * 100
            print(f"    {day_name:10s}: {count:5,} trains ({pct:5.1f}%)")
        
        conn.close()
        
        print("\n" + "=" * 80)
        print("✅ DATABASE IS READY FOR ROUTE GENERATION")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = verify_database()
    sys.exit(0 if success else 1)
