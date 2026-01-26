from database_manager import get_db

db = get_db()
conn = db.get_connection()
c = conn.cursor()
c.execute("SELECT station_code, station_name FROM stations LIMIT 10")
print("First 10 stations:")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]}")

c.execute("SELECT station_code, station_name FROM stations WHERE station_code IN ('CSMT', 'KHED')")
result = c.fetchall()
print(f"\nCSMT and KHED check: {result}")

c.execute("SELECT COUNT(*) FROM stations")
total = c.fetchone()[0]
print(f"Total stations: {total}")

conn.close()
