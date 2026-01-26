import sqlite3
import json
from pathlib import Path
conn = sqlite3.connect(Path(__file__).parent / 'data' / 'production.db')
c = conn.cursor()
for tbl in ['trains', 'stations', 'routes']:
    c.execute(f"SELECT COUNT(*) FROM {tbl}")
    print(tbl, c.fetchone()[0])
c.execute('PRAGMA table_info(routes)')
print('routes schema:')
print(json.dumps(c.fetchall()))
c.execute('PRAGMA index_list(routes)')
print('routes indexes:')
print(c.fetchall())
conn.close()
