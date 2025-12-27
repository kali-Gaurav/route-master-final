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
    routes.csv, Clean_Dataset.csv, and airport_codes.csv efficiently.
    """
    try:
        print("--- Optimizing process_flight_data ---")
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

        # Create a mapping from city name to IATA code
        city_to_iata_base = airport_codes_df.set_index('city')['iata_code'].to_dict()
        
        # Add manual mappings for major Indian cities to their IATA codes
        manual_iata_mapping = {
            "Delhi": "DEL",
            "Mumbai": "BOM",
            "Bangalore": "BLR",
            "Chennai": "MAA",
            "Hyderabad": "HYD",
            "Kolkata": "CCU"
        }
        city_to_iata_base.update(manual_iata_mapping)

        print(f"Created city_to_iata mapping with {len(city_to_iata_base)} entries.")

        # Function to get IATA code, handling case variations
        def get_iata_code(city_name):
            if pd.isna(city_name):
                return None
            return city_to_iata_base.get(city_name) or \
                   city_to_iata_base.get(city_name.title()) or \
                   city_to_iata_base.get(city_name.upper())

        # Apply IATA mapping to clean_df
        clean_df['source_iata'] = clean_df['source_city'].apply(get_iata_code)
        clean_df['destination_iata'] = clean_df['destination_city'].apply(get_iata_code)

        # Drop rows where IATA codes couldn't be determined
        initial_flights_count = len(clean_df)
        clean_df.dropna(subset=['source_iata', 'destination_iata'], inplace=True)
        skipped_flights_no_iata = initial_flights_count - len(clean_df)
        print(f"Skipped {skipped_flights_no_iata} flights due to missing IATA codes.")

        # Merge clean_df with routes_df
        # Ensure column names for merging are consistent
        routes_df.rename(columns={'source airport': 'source_iata', 'destination apirport': 'destination_iata'}, inplace=True)
        
        # Perform an inner merge to find matching flight routes efficiently
        merged_flights_df = pd.merge(
            clean_df,
            routes_df,
            on=['source_iata', 'destination_iata'],
            how='inner',
            suffixes=('_clean', '_routes') # This suffix applies only to columns existing in both DFs
        )

        print(f"Found {len(merged_flights_df)} matching flights after merging with routes.csv.")
        print(f"Columns of merged_flights_df: {merged_flights_df.columns.tolist()}") # Debug print for columns

        FLIGHT_SPEED_KMH = 800 # Average cruising speed of a commercial airliner

        flight_routes = []
        # Iterate through the merged DataFrame to create the final flight_routes list
        for _, row in merged_flights_df.iterrows():
            duration_minutes = row['duration'] * 60 if pd.notna(row['duration']) else None
            
            estimated_distance_km = None
            if duration_minutes is not None:
                estimated_distance_km = (duration_minutes / 60) * FLIGHT_SPEED_KMH

            flight_routes.append({
                'type': 'flight',
                'unique_id': f"{row['airline_clean']}_{row['flight']}", 
                'origin': row['source_iata'],
                'origin_city': row['source_city'],
                'destination': row['destination_iata'],
                'destination_city': row['destination_city'],
                'departure_time': row['departure_time'],
                'arrival_time': row['arrival_time'],
                'duration_minutes': duration_minutes,
                'cost_inr': row['price'],
                'distance_km': estimated_distance_km,  
                'airline': row['airline_clean']
            })
        
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