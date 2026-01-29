from database_system import DatabasePool
from sqlalchemy import text
from database_system import DatabaseConfig

config = DatabaseConfig()
database_url = config.database_url
session = DatabasePool.get_session(database_url)
result = session.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'routes' AND column_name = 'stops'"))
for row in result:
    print(f'routes.stops column type: {row[1]}')
session.close()