import sqlite3
from pathlib import Path

DB = Path(__file__).parent / 'production.db'
if not DB.exists():
    print('ERROR: production.db not found at', DB)
    raise SystemExit(2)

con = sqlite3.connect(str(DB))
cur = con.cursor()

print('Database:', DB)

cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
rows = [r[0] for r in cur.fetchall()]
print('Tables:', rows)

for tbl in ('train_routes','train_running_days','trains_master'):
    if tbl in rows:
        print('\nSchema for',tbl)
        cur.execute(f"PRAGMA table_info({tbl});")
        for col in cur.fetchall():
            cid,name,ctype,notnull,dflt,pk = col
            print(f" - {name} ({ctype}) notnull={notnull} pk={pk} default={dflt}")
    else:
        print(f"\nMissing expected table: {tbl}")

con.close()
print('\nDB sanity check complete')
