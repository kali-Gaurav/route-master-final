"""Check database schema"""
from database_manager import DatabaseManager

db = DatabaseManager()
with db.get_connection() as conn:
    cursor = conn.cursor()
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("Tables in database:")
    for table in tables:
        print(f"  • {table[0]}")
    
    if tables:
        print("\nTrain table schema:")
        cursor.execute("PRAGMA table_info(trains)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  • {col[1]} ({col[2]})")
        
        # Get sample data
        print("\nSample train data:")
        cursor.execute("SELECT * FROM trains LIMIT 1")
        sample = cursor.fetchone()
        if sample:
            print(f"  Data: {sample}")
