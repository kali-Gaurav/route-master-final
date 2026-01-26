# Data Cleanup & Correction Guide

## Overview
This guide provides step-by-step instructions to clean and correct the Train_details.csv dataset based on validation results.

---

## Issue #1: Critical - 5 Corrupted Rows (MUST FIX)

### Affected Records:
- Row 2309: Train K, Station 214
- Row 2321: Train K, Station 33
- Row 135827: Train K, Station 142
- Row 135885: Train K, Station 214
- Row 140469: Train K, Station 142

### Problem:
Complete data corruption with columns shifted - station names appearing in time fields, etc.

### Solution Options:

#### Option A: Delete the Rows (Simplest)
```python
import pandas as pd

df = pd.read_csv('Train_details.csv')
problematic_rows = [2309, 2321, 135827, 135885, 140469]
df_cleaned = df.drop(index=problematic_rows)
df_cleaned.to_csv('Train_details_cleaned.csv', index=False)
print(f"Removed {len(problematic_rows)} corrupted rows")
print(f"New total: {len(df_cleaned)} records")
```

#### Option B: Fetch from Source System (Preferred)
1. Identify which trains these belong to (Train K appears to be corrupted label)
2. Query your source system (IRCTC API, database backup) for these train-station combinations
3. Rebuild the 5 rows with correct data
4. Update the CSV

#### Option C: Use Backup Data
1. Check if you have backup versions of Train_details.csv from before corruption
2. Extract these 5 records from clean backup
3. Replace the corrupted ones

### Verification Script:
```python
import pandas as pd

df = pd.read_csv('Train_details.csv')

# Check if rows are gone or fixed
problematic_rows = [2309, 2321, 135827, 135885, 140469]
remaining = df.loc[df.index.isin(problematic_rows)]

if len(remaining) == 0:
    print("✓ All problematic rows removed")
else:
    print(f"⚠ {len(remaining)} rows still present")
    print(remaining[['Train No', 'Station Code', 'Arrival time']])
```

---

## Issue #2: High Priority - 471 Single-Character Station Codes

### Affected Records:
- 471 rows with station codes like: R, G, J, S, Y, D, H, etc.

### Problem:
Ambiguous codes that may be abbreviations, errors, or legacy codes

### Investigation Steps:

#### Step 1: Identify All Single-Character Codes
```python
import pandas as pd

df = pd.read_csv('Train_details.csv')
single_char = df[df['Station Code'].str.len() == 1]

print(f"Found {len(single_char)} single-character codes")
print(f"Unique codes: {single_char['Station Code'].unique()}")
print(f"\nBreakdown:")
print(single_char['Station Code'].value_counts())
```

#### Step 2: Review Sample Records
```python
# Show first 10 records with single-character codes
print(single_char.head(10)[['Train No', 'Station Code', 'Station Name', 'Distance']])

# Show for each single-char code
for code in single_char['Station Code'].unique():
    subset = single_char[single_char['Station Code'] == code]
    print(f"\n{code}: {len(subset)} records")
    print(f"  Sample station names: {subset['Station Name'].unique()[:3]}")
```

#### Step 3: Determine Correct Codes
```python
# Create mapping from station names to correct codes
# Example mapping based on investigation:
code_mapping = {
    'R': 'Need to determine - check associated station names',
    'G': 'GANDHINAGAR (maybe GNDG?)',
    'J': 'JAIPUR (maybe JP?)',
    # ... etc
}

# Get unique station names for each single-char code
for code in single_char['Station Code'].unique():
    names = single_char[single_char['Station Code'] == code]['Station Name'].unique()
    print(f"\n'{code}' maps to stations: {names}")
```

### Correction Steps:

#### Option A: Use Station Name to Look Up Correct Code
```python
import pandas as pd

df = pd.read_csv('Train_details.csv')

# Load reference of correct station codes
# (create from valid codes in your dataset)
valid_codes = df[df['Station Code'].str.len() > 1][['Station Name', 'Station Code']].drop_duplicates()

# Function to find correct code for a station
def find_correct_code(station_name, valid_codes_df):
    match = valid_codes_df[valid_codes_df['Station Name'] == station_name]
    if len(match) > 0:
        return match.iloc[0]['Station Code']
    return None

# Apply correction
df['Station Code'] = df.apply(
    lambda row: find_correct_code(row['Station Name'], valid_codes) 
    if len(row['Station Code']) == 1 
    else row['Station Code'],
    axis=1
)

df.to_csv('Train_details_cleaned.csv', index=False)
```

#### Option B: Manual Mapping File
Create a `station_code_corrections.csv`:
```csv
wrong_code,correct_code,reason,verified
R,<correct>,Checked station names,Yes/No
G,<correct>,Found in master data,Yes/No
J,<correct>,Used in route X,Yes/No
```

Then apply:
```python
import pandas as pd

df = pd.read_csv('Train_details.csv')
corrections = pd.read_csv('station_code_corrections.csv')

# Create mapping
correction_map = dict(zip(corrections['wrong_code'], corrections['correct_code']))

# Apply
df['Station Code'] = df['Station Code'].replace(correction_map)
df.to_csv('Train_details_cleaned.csv', index=False)
```

### Validation After Correction:
```python
import pandas as pd

df = pd.read_csv('Train_details_cleaned.csv')

# Check no single-char codes remain
single_char = df[df['Station Code'].str.len() == 1]
if len(single_char) == 0:
    print("✓ All single-character codes fixed")
else:
    print(f"⚠ {len(single_char)} single-char codes still remain")

# Verify all codes are 2-5 characters
valid_length = df['Station Code'].str.len().between(2, 5).all()
if valid_length:
    print("✓ All codes are proper length (2-5 chars)")
else:
    print("✗ Some codes still have invalid length")
```

---

## Issue #3: Medium Priority - 10 Records with Empty Source/Destination Names

### Affected Records:
- 10 rows missing Source Station Name and/or Destination Station Name

### Problem:
Incomplete records that will be less useful for display and reporting

### Solution:

#### Step 1: Identify Records
```python
import pandas as pd

df = pd.read_csv('Train_details.csv')

# Find records with empty source names
empty_source = df[df['Source Station Name'].str.strip() == '']
print(f"Empty Source Names: {len(empty_source)} records")
print(empty_source[['Train No', 'Source Station', 'Source Station Name']])

# Find records with empty destination names  
empty_dest = df[df['Destination Station Name'].str.strip() == '']
print(f"\nEmpty Destination Names: {len(empty_dest)} records")
print(empty_dest[['Train No', 'Destination Station', 'Destination Station Name']])
```

#### Step 2: Lookup Correct Names
```python
import pandas as pd

df = pd.read_csv('Train_details.csv')

# Create lookup table from valid records
station_names = df[df['Station Name'].notna()][['Station Code', 'Station Name']].drop_duplicates()

# Function to look up name
def get_station_name(station_code, lookup_df):
    match = lookup_df[lookup_df['Station Code'] == station_code]
    if len(match) > 0:
        return match.iloc[0]['Station Name']
    return None

# Fill Source Station Names
empty_source_mask = df['Source Station Name'].str.strip() == ''
df.loc[empty_source_mask, 'Source Station Name'] = \
    df.loc[empty_source_mask, 'Source Station'].apply(
        lambda x: get_station_name(x, station_names) or x
    )

# Fill Destination Station Names
empty_dest_mask = df['Destination Station Name'].str.strip() == ''
df.loc[empty_dest_mask, 'Destination Station Name'] = \
    df.loc[empty_dest_mask, 'Destination Station'].apply(
        lambda x: get_station_name(x, station_names) or x
    )

df.to_csv('Train_details_cleaned.csv', index=False)

print(f"Filled {empty_source_mask.sum()} source names")
print(f"Filled {empty_dest_mask.sum()} destination names")
```

### Validation:
```python
import pandas as pd

df = pd.read_csv('Train_details_cleaned.csv')

# Check no empty names remain
empty_source = (df['Source Station Name'].str.strip() == '').sum()
empty_dest = (df['Destination Station Name'].str.strip() == '').sum()

if empty_source == 0 and empty_dest == 0:
    print("✓ All station names populated")
else:
    print(f"⚠ Still {empty_source} empty source names, {empty_dest} empty dest names")
```

---

## Complete Cleanup Script

```python
"""
Complete cleanup script for Train_details.csv
Applies all corrections in one pass
"""

import pandas as pd

def clean_train_dataset(input_file='Train_details.csv', output_file='Train_details_cleaned.csv'):
    """
    Perform all data cleanup operations
    """
    
    df = pd.read_csv(input_file, low_memory=False)
    print(f"Starting with {len(df):,} records")
    
    # STEP 1: Remove corrupted rows
    print("\n[1] Removing 5 corrupted rows...")
    problematic_rows = [2309, 2321, 135827, 135885, 140469]
    df = df.drop(index=problematic_rows)
    print(f"✓ Removed {len(problematic_rows)} rows -> {len(df):,} remaining")
    
    # STEP 2: Fix single-character station codes
    print("\n[2] Fixing single-character station codes...")
    single_char_mask = df['Station Code'].str.len() == 1
    single_char_count = single_char_mask.sum()
    
    # Create reference from valid codes
    valid_codes = df[df['Station Code'].str.len() > 1][
        ['Station Name', 'Station Code']
    ].drop_duplicates()
    
    def find_correct_code(station_name):
        matches = valid_codes[valid_codes['Station Name'] == station_name]
        if len(matches) > 0:
            return matches.iloc[0]['Station Code']
        return None
    
    df.loc[single_char_mask, 'Station Code'] = df.loc[single_char_mask].apply(
        lambda row: find_correct_code(row['Station Name']) or row['Station Code'],
        axis=1
    )
    print(f"✓ Processed {single_char_count} single-character codes")
    
    # STEP 3: Fill empty station names
    print("\n[3] Filling empty source/destination station names...")
    
    # Create lookup
    station_names = df[df['Station Name'].notna()][
        ['Station Code', 'Station Name']
    ].drop_duplicates().set_index('Station Code')['Station Name'].to_dict()
    
    def get_station_name(code):
        return station_names.get(code, code)
    
    # Fill source names
    empty_source = df['Source Station Name'].str.strip() == ''
    df.loc[empty_source, 'Source Station Name'] = df.loc[empty_source, 'Source Station'].apply(get_station_name)
    
    # Fill destination names
    empty_dest = df['Destination Station Name'].str.strip() == ''
    df.loc[empty_dest, 'Destination Station Name'] = df.loc[empty_dest, 'Destination Station'].apply(get_station_name)
    
    print(f"✓ Filled {empty_source.sum()} source names and {empty_dest.sum()} destination names")
    
    # Save cleaned dataset
    df.to_csv(output_file, index=False)
    print(f"\n✓ Cleaned dataset saved to: {output_file}")
    print(f"Final record count: {len(df):,}")
    
    return df

if __name__ == '__main__':
    df_clean = clean_train_dataset()
    print("\n✓ Data cleanup complete!")
```

---

## Post-Cleanup Validation

After applying any corrections, re-run the validation:

```bash
python validate_train_dataset.py
```

Expected results after cleanup:
- ✅ 0 corrupted rows (instead of 5)
- ✅ 0 single-character station codes (instead of 471)
- ✅ 0 empty station names (instead of 10)
- ✅ 186,124 valid records (or 186,119 if you delete the 5 bad rows)

---

## Best Practices Going Forward

1. **Add Input Validation:**
   - Validate on insert/import
   - Reject non-compliant records
   - Log validation failures

2. **Implement Data Governance:**
   - Establish data quality standards
   - Regular validation checks
   - Audit trails for changes

3. **Version Control:**
   - Keep backup of original CSV
   - Track changes with timestamps
   - Maintain version history

4. **Automation:**
   - Run validation on schedule
   - Alert on new issues
   - Auto-fix where possible

5. **Documentation:**
   - Document all corrections
   - Keep mapping files updated
   - Record source of truth for each field

---

## Additional Resources

- **Validation Report:** `DATASET_VALIDATION_REPORT.md`
- **Validation Script:** `validate_train_dataset.py`
- **Invalid Records List:** `invalid_records.csv`
- **Validation Details:** `validation_report.json`

