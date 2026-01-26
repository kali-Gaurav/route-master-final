import sqlite3
from pathlib import Path
import json
conn = sqlite3.connect(Path(__file__).parent / 'data' / 'production.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('tables:', json.dumps([row[0] for row in c.fetchall()]))
for tbl in ['trains', 'stations', 'train_stations', 'search_logs', 'performance_logs', 'data_quality']:
    try:
        c.execute(f"SELECT COUNT(*) FROM {tbl}")
        print(tbl, c.fetchone()[0])
    except sqlite3.OperationalError:
        print(f'missing {tbl}')
print('train_stations schema:')
try:
    c.execute('PRAGMA table_info(train_stations)')
    print(json.dumps(c.fetchall()))
except sqlite3.OperationalError:
    print('train_stations table absent')
print('train_stations indexes:')
try:
    c.execute('PRAGMA index_list(train_stations)')
    print(json.dumps(c.fetchall()))
except sqlite3.OperationalError:
    print('train_stations table absent')
conn.close()
