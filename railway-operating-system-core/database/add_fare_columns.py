from database_system import DatabasePool
from sqlalchemy import text
from database_system import DatabaseConfig

def add_missing_fare_columns():
    """Add missing columns to fares table."""

    config = DatabaseConfig()
    database_url = config.database_url
    session = DatabasePool.get_session(database_url)

    try:
        print("Adding missing columns to fares table...")

        # Add dynamic_pricing_enabled column
        session.execute(text("""
            ALTER TABLE fares ADD COLUMN IF NOT EXISTS dynamic_pricing_enabled BOOLEAN DEFAULT FALSE;
        """))

        # Add demand_multiplier column
        session.execute(text("""
            ALTER TABLE fares ADD COLUMN IF NOT EXISTS demand_multiplier DECIMAL(3,2) DEFAULT 1.0;
        """))

        # Add seasonal_multiplier column
        session.execute(text("""
            ALTER TABLE fares ADD COLUMN IF NOT EXISTS seasonal_multiplier DECIMAL(3,2) DEFAULT 1.0;
        """))

        # Add minimum_fare column
        session.execute(text("""
            ALTER TABLE fares ADD COLUMN IF NOT EXISTS minimum_fare DECIMAL(8,2);
        """))

        # Add maximum_fare column
        session.execute(text("""
            ALTER TABLE fares ADD COLUMN IF NOT EXISTS maximum_fare DECIMAL(8,2);
        """))

        # Add cancellation_policy column
        session.execute(text("""
            ALTER TABLE fares ADD COLUMN IF NOT EXISTS cancellation_policy JSONB;
        """))

        session.commit()
        print("✅ Successfully added missing columns to fares table")

    except Exception as e:
        session.rollback()
        print(f"❌ Error adding columns: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    add_missing_fare_columns()