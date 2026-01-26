import json
from database_manager import DatabaseManager
from pathlib import Path

# Path to the cities_locations.json file
CITIES_JSON = Path("route-master-final/dataset/cities_locations.json")

def import_city_hubs():
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()

    with open(CITIES_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for loc in data["locations"]:
        city = loc["city"].strip()
        state = loc.get("state", "").strip()
        for hub in loc.get("hubs", []):
            hub_code = hub.get("code", "").strip()
            hub_name = hub.get("name", "").strip()
            hub_type = hub.get("type", "").strip()
            hub_full_name = hub.get("fullName", "").strip()
            cursor.execute(
                """
                INSERT INTO city_hubs (city, state, hub_code, hub_name, hub_type, hub_full_name)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (city, state, hub_code, hub_name, hub_type, hub_full_name)
            )
            count += 1
    conn.commit()
    print(f"Imported {count} city-hub records into city_hubs table.")

if __name__ == "__main__":
    import_city_hubs()
