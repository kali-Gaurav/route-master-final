from database_manager import get_db
db = get_db()
stats = db.get_stats()
print('\n=== Database Statistics ===')
for k, v in stats.items():
    print(f'{k}: {v:,}')
