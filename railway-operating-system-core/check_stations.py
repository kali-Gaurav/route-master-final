import sys
sys.path.insert(0, '.')
from database.connection import db_manager

with db_manager.session_scope() as session:
    from database.models.station import Station
    stations = session.query(Station.code, Station.name).limit(20).all()
    print('Sample stations in database:')
    for code, name in stations:
        print(f'  {code}: {name}')
    
    # Check if our test stations exist
    test_codes = ['NDLS', 'BCT', 'HWH', 'MAS', 'PUNE', 'LKO']
    existing = session.query(Station.code).filter(Station.code.in_(test_codes)).all()
    existing_codes = [s[0] for s in existing]
    print(f'\nTest station codes: {test_codes}')
    print(f'Existing in DB: {existing_codes}')
    missing = [code for code in test_codes if code not in existing_codes]
    if missing:
        print(f'Missing stations: {missing}')
    else:
        print('All test stations exist in database')