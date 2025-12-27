import pandas as pd
import json
from datetime import datetime, timedelta

# Load city mapping
with open('city_mapping.json', 'r') as f:
    CITY_MAPPING = json.load(f)

def get_city_from_code(code):
    return CITY_MAPPING.get(code, "Unknown City")

def process_train_data():
    """
    Reads train data from Train_details.csv, processes it into segments,
    and calculates duration and distance for each segment.
    """
    try:
        # Load the dataset using the 'python' engine for more robust parsing
        train_details_df = pd.read_csv('Train_details.csv', dtype={'Train No': str, 'SEQ': str}, engine='python', on_bad_lines='warn')
        train_details_df.columns = train_details_df.columns.str.strip()

        # Coerce to numeric, errors will be NaT
        train_details_df['SEQ'] = pd.to_numeric(train_details_df['SEQ'], errors='coerce')
        train_details_df['Distance'] = pd.to_numeric(train_details_df['Distance'], errors='coerce')

        # Drop rows where essential data is missing
        train_details_df.dropna(subset=['Train No', 'SEQ', 'Station Code', 'Departure Time', 'Arrival time', 'Distance'], inplace=True)
        
        # Convert SEQ to integer
        train_details_df['SEQ'] = train_details_df['SEQ'].astype(int)

        processed_train_routes = []
        
        # Group by train number to process each train's route individually
        for train_no, train_group in train_details_df.groupby('Train No'):
            train_group = train_group.sort_values(by='SEQ')
            
            # Iterate through the stops of a single train
            for i in range(len(train_group) - 1):
                current_stop = train_group.iloc[i]
                next_stop = train_group.iloc[i+1]

                # Calculate duration
                try:
                    dep_dt = datetime.strptime(str(current_stop['Departure Time']), '%H:%M:%S')
                    arr_dt = datetime.strptime(str(next_stop['Arrival time']), '%H:%M:%S')
                    if arr_dt < dep_dt:
                        arr_dt += timedelta(days=1)
                    duration = arr_dt - dep_dt
                    duration_minutes = duration.total_seconds() / 60
                except (ValueError, TypeError):
                    duration_minutes = None # Handle missing or malformed times

                # Calculate distance for the segment
                distance_km = next_stop['Distance'] - current_stop['Distance']

                processed_train_routes.append({
                    'type': 'train',
                    'unique_id': f"{train_no}_{current_stop['Station Code']}_{next_stop['Station Code']}",
                    'origin': current_stop['Station Code'],
                    'origin_city': current_stop['Station Name'],
                    'destination': next_stop['Station Code'],
                    'destination_city': next_stop['Station Name'],
                    'departure_time': current_stop['Departure Time'],
                    'arrival_time': next_stop['Arrival time'],
                    'duration_minutes': duration_minutes,
                    'cost_inr': 1500,  # Placeholder cost
                    'distance_km': distance_km,
                    'train_name': current_stop['Train Name']
                })

        return processed_train_routes

    except FileNotFoundError:
        print("Error: Train_details.csv not found.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred in process_train_data: {e}")
        return []

def process_flight_data():
    """
    Reads and processes flight route data, combining information from 
    routes.csv, Clean_Dataset.csv, and airport_codes.csv.
    """
    try:
        print("--- Debugging process_flight_data ---")
        # Load datasets
        routes_df = pd.read_csv('routes.csv')
        routes_df.columns = routes_df.columns.str.strip()
        print(f"Loaded routes_df: {len(routes_df)} rows")

        clean_df = pd.read_csv('Clean_Dataset.csv')
        clean_df.columns = clean_df.columns.str.strip()
        print(f"Loaded clean_df: {len(clean_df)} rows")

        airport_codes_df = pd.read_csv('airport_codes.csv')
        airport_codes_df.columns = airport_codes_df.columns.str.strip()
        print(f"Loaded airport_codes_df: {len(airport_codes_df)} rows")

        # Create a mapping from city name to IATA code (from external airport codes file)
        city_to_iata = airport_codes_df.set_index('city')['iata_code'].to_dict()
        
        # Add manual mappings for major Indian cities to their IATA codes
        # These are commonly used codes and might not be present or consistent in the general airport_codes.csv
        manual_iata_mapping = {
            "Delhi": "DEL",
            "Mumbai": "BOM",
            "Bangalore": "BLR",
            "Chennai": "MAA",
            "Hyderabad": "HYD",
            "Kolkata": "CCU"
        }
        # Update the dictionary, manual mappings will override if duplicates exist
        city_to_iata.update(manual_iata_mapping)

        print(f"Created city_to_iata mapping with {len(city_to_iata)} entries after manual update.")

        flight_routes = []
        skipped_flights_no_iata = 0
        skipped_flights_no_route = 0

        # Process flight data from Clean_Dataset.csv
        for idx, flight in clean_df.iterrows():
            source_city = flight['source_city']
            dest_city = flight['destination_city']

            # Get IATA codes from city names, case-insensitive match for robustness
            source_iata = city_to_iata.get(source_city) or city_to_iata.get(source_city.title()) or city_to_iata.get(source_city.upper())
            dest_iata = city_to_iata.get(dest_city) or city_to_iata.get(dest_city.title()) or city_to_iata.get(dest_city.upper())

            if not source_iata:
                # print(f"Skipping flight {idx}: No IATA code for source city '{source_city}'")
                skipped_flights_no_iata += 1
                continue
            if not dest_iata:
                # print(f"Skipping flight {idx}: No IATA code for destination city '{dest_city}'")
                skipped_flights_no_iata += 1
                continue

            # Find the corresponding route in routes.csv
            route_info = routes_df[
                (routes_df['source airport'] == source_iata) & 
                (routes_df['destination apirport'] == dest_iata)
            ]

            if route_info.empty:
                # print(f"Skipping flight {idx}: No matching route in routes.csv for {source_iata} -> {dest_iata}")
                skipped_flights_no_route += 1
                continue
                
            # Use the first matching route
            route = route_info.iloc[0]

            # Convert duration from hours to minutes
            duration_minutes = flight['duration'] * 60 if pd.notna(flight['duration']) else None

            flight_routes.append({
                'type': 'flight',
                'unique_id': f"{flight['airline']}_{flight['flight']}",
                'origin': source_iata,
                'origin_city': source_city,
                'destination': dest_iata,
                'destination_city': dest_city,
                'departure_time': flight['departure_time'],
                'arrival_time': flight['arrival_time'],
                'duration_minutes': duration_minutes,
                'cost_inr': flight['price'],
                'distance_km': None,  # No distance data for flights
            })
        
        print(f"Total flights from Clean_Dataset.csv: {len(clean_df)}")
        print(f"Skipped due to missing IATA: {skipped_flights_no_iata}")
        print(f"Skipped due to no matching route in routes.csv: {skipped_flights_no_route}")
        print(f"Generated {len(flight_routes)} flight segments.")

        return flight_routes

    except FileNotFoundError as e:
        print(f"Error processing flight data: {e}. Make sure all required CSV files are in the directory.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred in process_flight_data: {e}")
        return []

def main():
    """
    Main function to process all data and save to a unified file.
    """
    print("Starting data processing...")
    
    train_data = process_train_data()
    print(f"Processed {len(train_data)} train segments.")
    
    flight_data = process_flight_data()
    print(f"Processed {len(flight_data)} flight segments.")
    
    unified_data = train_data + flight_data
    
    with open('unified_routes.json', 'w') as f:
        json.dump(unified_data, f, indent=4)
        
    print(f"Successfully created unified_routes.json with {len(unified_data)} total segments.")

if __name__ == '__main__':
    main()