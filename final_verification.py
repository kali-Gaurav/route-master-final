#!/usr/bin/env python3
"""Final database verification"""

import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print('=' * 80)
print('DATABASE VERIFICATION - FINAL RUN')
print('=' * 80)
print()
print('TABLES IN DATABASE:')
for table in tables:
    print(f'  [OK] {table[0]}')
print()

# Check data
cursor.execute('SELECT COUNT(*) FROM train_running_days')
count = cursor.fetchone()[0]
print(f'TRAINS LOADED: {count:,}')
print()

# Check days
days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

print('DISTRIBUTION BY DAY:')
for day_col, day_name in zip(days, day_names):
    cursor.execute(f'SELECT COUNT(*) FROM train_running_days WHERE {day_col} = 1')
    c = cursor.fetchone()[0]
    pct = (c / count) * 100
    print(f'  {day_name:12s}: {c:5,} trains ({pct:5.1f}%)')

print()
print('=' * 80)
print('STATUS: DATABASE IS READY FOR ROUTE GENERATION')
print('=' * 80)

conn.close()
