"""
Generate comprehensive station-city mapping from Train_details.csv
Uses cities_locations.json and fuzzy matching to map all stations to cities
"""

import pandas as pd
import json
from difflib import get_close_matches
import re

def load_cities_data():
    """Load cities and their stations from cities_locations.json"""
    with open('cities_locations.json', 'r') as f:
        data = json.load(f)
    
    city_station_map = {}
    station_city_map = {}
    
    for location in data['locations']:
        city = location['city']
        state = location['state']
        
        for hub in location['hubs']:
            station_code = hub['code']
            station_name = hub['name']
            
            station_city_map[station_code] = {
                'city': city,
                'state': state,
                'station_name': station_name,
                'station_code': station_code
            }
            
            if city not in city_station_map:
                city_station_map[city] = []
            
            city_station_map[city].append({
                'code': station_code,
                'name': station_name
            })
    
    return city_station_map, station_city_map

def normalize_name(name):
    """Normalize station/city name for matching"""
    if pd.isna(name):
        return ""
    name = str(name).upper()
    # Remove common suffixes
    name = re.sub(r'\s+(JN\.?|JUNCTION|RAILWAY STATION|STATION|TERMINUS|TERM|JCT)', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def fuzzy_match_city(station_name, cities_list, threshold=0.6):
    """Try to find matching city using fuzzy matching"""
    normalized_station = normalize_name(station_name)
    
    # Direct match
    for city in cities_list:
        if normalize_name(city) in normalized_station or normalized_station in normalize_name(city):
            return city
    
    # Fuzzy match
    matches = get_close_matches(normalized_station, 
                                [normalize_name(c) for c in cities_list],
                                n=1, cutoff=threshold)
    
    if matches:
        # Find original city name
        for city in cities_list:
            if normalize_name(city) == matches[0]:
                return city
    
    return None

def generate_station_city_mapping():
    """Generate comprehensive station-city mapping"""
    
    print("Loading data...")
    
    # Load cities data
    city_station_map, station_city_map = load_cities_data()
    all_cities = list(city_station_map.keys())
    
    # Load train details to get all unique stations
    df = pd.read_csv('Train_details.csv')
    
    # Get unique stations
    unique_stations = df[['Station Code', 'Station Name']].drop_duplicates()
    
    print(f"Found {len(unique_stations)} unique stations in dataset")
    print(f"Found {len(station_city_map)} stations already mapped in cities_locations.json")
    
    # Create comprehensive mapping
    all_stations = []
    matched = 0
    unmatched = 0
    
    for _, row in unique_stations.iterrows():
        station_code = row['Station Code']
        station_name = row['Station Name']
        
        # Check if already mapped
        if station_code in station_city_map:
            entry = station_city_map[station_code].copy()
            entry['matched'] = 'exact'
            all_stations.append(entry)
            matched += 1
        else:
            # Try fuzzy matching
            matched_city = fuzzy_match_city(station_name, all_cities)
            
            if matched_city:
                # Find state for this city
                state = None
                for city_data in city_station_map:
                    if city_data == matched_city:
                        # Get state from cities_locations
                        for location in json.load(open('cities_locations.json'))['locations']:
                            if location['city'] == matched_city:
                                state = location['state']
                                break
                        break
                
                all_stations.append({
                    'station_code': station_code,
                    'station_name': station_name,
                    'city': matched_city,
                    'state': state or 'Unknown',
                    'matched': 'fuzzy'
                })
                matched += 1
            else:
                # Extract potential city name from station name
                potential_city = station_name.split()[0] if station_name else "Unknown"
                
                all_stations.append({
                    'station_code': station_code,
                    'station_name': station_name,
                    'city': potential_city,
                    'state': 'Unknown',
                    'matched': 'extracted'
                })
                unmatched += 1
    
    print(f"\nMapping Results:")
    print(f"  ✓ Exact matches: {sum(1 for s in all_stations if s.get('matched') == 'exact')}")
    print(f"  ✓ Fuzzy matches: {sum(1 for s in all_stations if s.get('matched') == 'fuzzy')}")
    print(f"  ⚠ Extracted names: {sum(1 for s in all_stations if s.get('matched') == 'extracted')}")
    print(f"  Total stations: {len(all_stations)}")
    
    # Create city to stations index
    city_to_stations = {}
    for station in all_stations:
        city = station['city']
        if city not in city_to_stations:
            city_to_stations[city] = []
        
        city_to_stations[city].append({
            'code': station['station_code'],
            'name': station['station_name'],
            'state': station.get('state', 'Unknown')
        })
    
    # Sort stations by city
    all_stations_sorted = sorted(all_stations, key=lambda x: (x['city'], x['station_name']))
    
    # Create output JSON
    output = {
        'metadata': {
            'total_stations': len(all_stations),
            'total_cities': len(city_to_stations),
            'exact_matches': sum(1 for s in all_stations if s.get('matched') == 'exact'),
            'fuzzy_matches': sum(1 for s in all_stations if s.get('matched') == 'fuzzy'),
            'extracted_matches': sum(1 for s in all_stations if s.get('matched') == 'extracted'),
            'generated_from': 'Train_details.csv and cities_locations.json'
        },
        'stations': all_stations_sorted,
        'city_index': city_to_stations
    }
    
    # Save to file
    with open('station_city_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved to station_city_mapping.json")
    print(f"  Total cities indexed: {len(city_to_stations)}")
    
    # Save a simplified version for frontend
    frontend_data = {
        'stations': [
            {
                'code': s['station_code'],
                'name': s['station_name'],
                'city': s['city'],
                'state': s.get('state', 'Unknown')
            }
            for s in all_stations_sorted
        ],
        'cities': sorted(city_to_stations.keys())
    }
    
    with open('station_search_data.json', 'w', encoding='utf-8') as f:
        json.dump(frontend_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved frontend data to station_search_data.json")
    
    return output

if __name__ == "__main__":
    mapping = generate_station_city_mapping()
    
    # Print sample
    print("\n=== Sample Stations ===")
    for i, station in enumerate(mapping['stations'][:10]):
        print(f"{i+1}. {station['station_code']} - {station['station_name']} ({station['city']}, {station.get('state', 'N/A')})")
