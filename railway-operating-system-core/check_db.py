import sqlite3

conn = sqlite3.connect('data/production.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]
print("Tables in production.db:", tables)

# Check a sample table
if tables:
    cursor.execute(f"SELECT COUNT(*) FROM {tables[0]}")
    count = cursor.fetchone()[0]
    print(f"Rows in {tables[0]}: {count}")

conn.close()