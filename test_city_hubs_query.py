from database_manager import DatabaseManager

if __name__ == "__main__":
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT city, state, hub_code, hub_name FROM city_hubs WHERE city = ?", ("Kolkata",))
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    print(f"Total: {len(rows)} stations for Kolkata")
