"""
Clean Train_details.csv and replace the original
Removes corrupted rows and fixes identified issues
"""

import pandas as pd
import shutil
from datetime import datetime

print("=" * 70)
print("TRAIN DATASET CLEANUP & REPLACEMENT")
print("=" * 70)

# Step 1: Backup original
print("\n[1] Creating backup of original dataset...")
backup_name = f'Train_details_BACKUP_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
shutil.copy('Train_details.csv', backup_name)
print(f"✓ Backup created: {backup_name}")

# Step 2: Load dataset
print("\n[2] Loading dataset...")
df = pd.read_csv('Train_details.csv', low_memory=False)
print(f"✓ Loaded {len(df):,} rows")

# Step 3: Remove corrupted rows (the 5 problematic records)
print("\n[3] Removing 5 corrupted rows...")
problematic_rows = [2309, 2321, 135827, 135885, 140469]
df_cleaned = df.drop(index=problematic_rows, errors='ignore')
removed_count = len(df) - len(df_cleaned)
print(f"✓ Removed {removed_count} corrupted records")
print(f"✓ Records remaining: {len(df_cleaned):,}")

# Step 4: Fix single-character station codes
print("\n[4] Processing single-character station codes...")
single_char_mask = df_cleaned['Station Code'].str.len() == 1
single_char_count = single_char_mask.sum()

if single_char_count > 0:
    # Create reference from valid codes
    valid_codes_df = df_cleaned[df_cleaned['Station Code'].str.len() > 1][
        ['Station Name', 'Station Code']
    ].drop_duplicates().set_index('Station Name')
    
    def find_correct_code(station_name):
        try:
            return valid_codes_df.loc[station_name, 'Station Code']
        except:
            return None
    
    # Create a mapping of single-char codes to correct ones
    single_char_records = df_cleaned[single_char_mask].copy()
    corrections_made = 0
    
    for idx in single_char_records.index:
        station_name = single_char_records.loc[idx, 'Station Name']
        corrected = find_correct_code(station_name)
        if corrected:
            df_cleaned.loc[idx, 'Station Code'] = corrected
            corrections_made += 1
    
    print(f"✓ Fixed {corrections_made} single-character codes")
    print(f"⚠ {single_char_count - corrections_made} single-char codes could not be auto-mapped (will need manual review)")

# Step 5: Fill empty source/destination names
print("\n[5] Filling empty source/destination station names...")

# Create lookup dictionary
station_name_map = df_cleaned[['Station Code', 'Station Name']].drop_duplicates()
station_name_map = dict(zip(station_name_map['Station Code'], station_name_map['Station Name']))

# Fill source names
empty_source = df_cleaned['Source Station Name'].isna() | (df_cleaned['Source Station Name'].str.strip() == '')
empty_source_count = empty_source.sum()
if empty_source_count > 0:
    df_cleaned.loc[empty_source, 'Source Station Name'] = \
        df_cleaned.loc[empty_source, 'Source Station'].map(station_name_map)
    print(f"✓ Filled {empty_source_count} empty source station names")

# Fill destination names
empty_dest = df_cleaned['Destination Station Name'].isna() | (df_cleaned['Destination Station Name'].str.strip() == '')
empty_dest_count = empty_dest.sum()
if empty_dest_count > 0:
    df_cleaned.loc[empty_dest, 'Destination Station Name'] = \
        df_cleaned.loc[empty_dest, 'Destination Station'].map(station_name_map)
    print(f"✓ Filled {empty_dest_count} empty destination station names")

# Step 6: Save cleaned dataset
print("\n[6] Saving cleaned dataset as Train_details.csv...")
df_cleaned.to_csv('Train_details.csv', index=False)
print(f"✓ Saved {len(df_cleaned):,} records to Train_details.csv")

# Step 7: Verification
print("\n[7] Post-cleanup Verification...")
df_verify = pd.read_csv('Train_details.csv', low_memory=False)
print(f"✓ File size: {len(df_verify):,} records")
print(f"✓ Columns: {len(df_verify.columns)}")
print(f"✓ Data completeness: {(df_verify.notna().sum().sum() / (len(df_verify) * len(df_verify.columns)) * 100):.2f}%")

# Summary
print("\n" + "=" * 70)
print("CLEANUP SUMMARY")
print("=" * 70)
print(f"Original records:        {len(df):,}")
print(f"Cleaned records:         {len(df_cleaned):,}")
print(f"Records removed:         {removed_count}")
print(f"Station codes fixed:     {corrections_made}")
print(f"Names populated:         {empty_source_count + empty_dest_count}")
print(f"Backup location:         {backup_name}")
print("=" * 70)
print("✓ DATASET CLEANUP COMPLETE!")
print("✓ Original dataset replaced with cleaned version")
print(f"✓ Backup saved as: {backup_name}")
print("=" * 70)
