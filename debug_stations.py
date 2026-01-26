import requests
import json

r = requests.get('http://localhost:5000/api/stations?limit=10')
stations = r.json()

print(f'Type: {type(stations)}')
print(f'Length: {len(stations)}')
print(f'First item: {stations[0] if stations else "empty"}')
print(f'Raw JSON:\n{json.dumps(stations[:3], indent=2)}')
