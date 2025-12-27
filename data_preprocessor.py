import pandas as pd
import json
from datetime import datetime, timedelta

def process_train_data():
    """
    Reads and merges train information and schedule data.
    """
    try:
        train_info_df = pd.read_csv('train_info.csv')
        train_schedule_df = pd.read_csv('train_schedule.csv')

        # Clean up column names
        train_info_df.columns = train_info_df.columns.str.strip()
        train_schedule_df.columns = train_schedule_df.columns.str.strip()

        # Merge the dataframes
        merged_df = pd.merge(train_schedule_df, train_info_df, on='Train_No', how='left')

        # unified format
        train_routes = []
        for _, row in merged_df.iterrows():
            train_routes.append({
                'type': 'train',
                'unique_id': f"{row['Train_No']}_{row['Route_Number']}",
                'origin': row['Station_Code'],
                'destination': None, # To be filled in later
                'departure_time': row['Departure_Time'],
                'arrival_time': row['Arrival_time'],
                'duration_minutes': None, # To be calculated
                'cost_inr': row['3A'],  # Assuming 3A class for now
                'distance_km': row['Distance'],
                'train_name': row['Train_Name']
            })
        
        # Post-process to link destinations and calculate duration
        processed_train_routes = []
        for i in range(len(train_routes) - 1):
            current = train_routes[i]
            next_stop = train_routes[i+1]

            # Check if the next stop is part of the same train journey
            if current['unique_id'] == next_stop['unique_id']:
                current['destination'] = next_stop['origin']
                
                # A simple duration calculation (this should be improved with proper datetime parsing)
                # This is a placeholder and might not be accurate across midnight
                try:
                    # Convert to datetime objects for accurate duration calculation
                    # Assume both are on the same arbitrary date initially
                    dep_dt = datetime.strptime(current['departure_time'], '%H:%M:%S')
                    arr_dt = datetime.strptime(next_stop['arrival_time'], '%H:%M:%S')

                    # If arrival is before departure, it means it's on the next day
                    if arr_dt < dep_dt:
                        arr_dt += timedelta(days=1)
                    
                    duration = arr_dt - dep_dt
                    current['duration_minutes'] = duration.total_seconds() / 60
                except (ValueError, TypeError):
                    current['duration_minutes'] = 0

                # distance calculation
                current['distance_km'] = next_stop['distance_km'] - current['distance_km']
                
                processed_train_routes.append(current)


        return processed_train_routes

    except FileNotFoundError as e:
        print(f"Error processing train data: {e}")
        return []

def process_flight_data():
    """
    Reads and processes flight route data.
    """
    try:
        flight_routes_df = pd.read_csv('routes.csv')
        flight_routes_df.columns = flight_routes_df.columns.str.strip()
        
        # Placeholder for price data processing
        # price_df = pd.read_csv('price_data.csv', chunksize=10000)
        # clean_df = pd.read_csv('Clean_Dataset.csv', chunksize=10000)
        # Since we cannot read these files, we will generate dummy data for now.

        flight_routes = []
        for _, row in flight_routes_df.iterrows():
            flight_routes.append({
                'type': 'flight',
                'unique_id': f"{row['airline']}_{row['source airport id']}_{row['destination airport id']}",
                'origin': row['source airport'],
                'destination': row['destination apirport'],
                'departure_time': None, # To be filled from other sources
                'arrival_time': None, # To be filled from other sources
                'duration_minutes': 120,  # Placeholder
                'cost_inr': 5000,  # Placeholder
                'distance_km': None,
            })

        return flight_routes

    except FileNotFoundError as e:
        print(f"Error processing flight data: {e}")
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
