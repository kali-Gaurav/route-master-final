from database_system import DatabasePool
from sqlalchemy import text
from database.config import DatabaseConfig

def alter_routes_stops_to_jsonb():
    """Change routes.stops column from JSON to JSONB."""

    config = DatabaseConfig()
    database_url = config.database_url
    session = DatabasePool.get_session(database_url)

    try:
        print("Changing routes.stops column from JSON to JSONB...")

        # First, check if the column is already JSONB
        result = session.execute(text("SELECT data_type FROM information_schema.columns WHERE table_name = 'routes' AND column_name = 'stops'"))
        current_type = result.scalar()

        if current_type == 'jsonb':
            print("Column is already JSONB, no change needed.")
            return

        # Change column type from JSON to JSONB
        session.execute(text("""
            ALTER TABLE routes ALTER COLUMN stops TYPE JSONB USING stops::jsonb;
        """))

        session.commit()
        print("✅ Successfully changed routes.stops column to JSONB")

    except Exception as e:
        session.rollback()
        print(f"❌ Error changing column type: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    alter_routes_stops_to_jsonb()