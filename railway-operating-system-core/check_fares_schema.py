from database_system import DatabasePool
from sqlalchemy import text

# Get database URL from config
from database.config import DatabaseConfig
config = DatabaseConfig()
database_url = config.database_url

session = DatabasePool.get_session(database_url)
result = session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'fares' ORDER BY ordinal_position"))
print('Fares table columns:')
for row in result:
    print(f'  {row[0]}')
session.close()