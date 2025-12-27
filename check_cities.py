
import json

cities_from_clean_dataset = ["Bangalore", "Chennai", "Delhi", "Hyderabad", "Kolkata", "Mumbai"]

with open('city_mapping.json', 'r') as f:
    city_mapping_data = json.load(f)

city_mapping_list = city_mapping_data.get('cities', [])

found_cities = []
not_found_cities = []

for city in cities_from_clean_dataset:
    if city.upper() in city_mapping_list: # city_mapping is in uppercase
        found_cities.append(city)
    else:
        not_found_cities.append(city)

print(f"Cities found in city_mapping.json: {found_cities}")
print(f"Cities NOT found in city_mapping.json: {not_found_cities}")
