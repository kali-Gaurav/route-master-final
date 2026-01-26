#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.cursor()

# Get trains with multiple stations (good for testing)
cursor.execute("""
    SELECT train_no, GROUP_CONCAT(station_name, '|') as stations
    FROM rappid_routes
    GROUP BY train_no
    HAVING COUNT(*) >= 3
    ORDER BY COUNT(*) DESC
    LIMIT 5
""")

trains = cursor.fetchall()

print("Sample trains with their stations:")
for train_no, stations_str in trains:
    station_list = stations_str.split('|')
    print(f"\nTrain {train_no}: {len(station_list)} stations")
    print(f"  Path: {' → '.join(station_list[:min(5, len(station_list))])}")
    if len(station_list) > 5:
        print(f"        ... → {station_list[-1]}")

# Get some good station pairs to test
print("\n\nGood station pairs for testing (from same train):")
cursor.execute("""
    WITH train_stations AS (
        SELECT train_no, GROUP_CONCAT(station_name, '|') as stations
        FROM rappid_routes
        GROUP BY train_no
        HAVING COUNT(*) >= 3
        LIMIT 10
    )
    SELECT train_no, stations FROM train_stations
""")

pairs = []
for train_no, stations_str in cursor.fetchall():
    station_list = stations_str.split('|')
    if len(station_list) >= 2:
        pairs.append((station_list[0], station_list[-1]))
        if len(station_list) >= 4:
            pairs.append((station_list[0], station_list[len(station_list)//2]))

for i, (start, end) in enumerate(pairs[:8], 1):
    print(f"{i}. {start} → {end}")

conn.close()
