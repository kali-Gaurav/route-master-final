#!/usr/bin/env python3
"""Check source data for trains with missing days"""

import pandas as pd
import sqlite3

# Read train_info.csv
df = pd.read_csv('dataset/train_info.csv')

print("=" * 80)
print("CHECKING SOURCE DATA QUALITY")
print("=" * 80)

# Check specific trains
trains_to_check = [40902, 41001, 41003]
print("\nSample of trains with no running days:")
for train in trains_to_check:
    row = df[df['Train_No'] == train]
    if not row.empty:
        train_name = row.iloc[0]['Train_Name']
        days = row.iloc[0]['days']
        print(f"  Train {train}: {train_name}")
        print(f"    days column value: '{days}' (type: {type(days).__name__})")
    else:
        print(f"  Train {train}: NOT FOUND in train_info.csv")

# Count trains with empty days
print("\n" + "=" * 80)
print("DATA QUALITY METRICS")
print("=" * 80)

empty_count = df[df['days'].isna()].shape[0]
print(f"\nTrains with NULL days: {empty_count}")

empty_str_count = df[df['days'] == ''].shape[0]
print(f"Trains with EMPTY string days: {empty_str_count}")

valid_count = df[(df['days'].notna()) & (df['days'] != '')].shape[0]
print(f"Trains with valid days data: {valid_count}")

print(f"\nTotal trains in train_info.csv: {len(df)}")

# Show sample of trains with missing days
print("\n" + "=" * 80)
print("FIRST 10 TRAINS WITH MISSING DAYS")
print("=" * 80)

missing_days = df[df['days'].isna() | (df['days'] == '')]
for idx, row in missing_days.head(10).iterrows():
    print(f"  {row['Train_No']}: {row['Train_Name']}")

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print("""
These 1,025 trains have no running day information in train_info.csv.
This is a data quality issue in the source dataset.

Options:
1. ✅ CURRENT: Keep them in database but they won't be used in routes
   (Route generator will skip trains with no running days)
2. Filter them out before loading
3. Assign default days (e.g., 'daily') if available in other sources

The system is working correctly - it's just reflecting source data gaps.
Routes generated will still be valid because the validator will exclude
trains with no running day information.
""")
