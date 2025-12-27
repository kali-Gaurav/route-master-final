
import pandas as pd
import json

def create_city_mapping():
    """
    Reads city and station data from various CSV files, combines them,
    finds the unique values, and saves them to a JSON file.
    """
    try:
        # Read the datasets
        train_details_df = pd.read_csv('Train_details.csv')
        clean_dataset_df = pd.read_csv('Clean_Dataset.csv')
        routes_df = pd.read_csv('routes.csv')

        # Extract cities and stations, handling potential errors
        train_stations = set(train_details_df['Station Name'].dropna())
        train_sources = set(train_details_df['Source Station Name'].dropna())
        train_dests = set(train_details_df['Destination Station Name'].dropna())

        flight_sources = set(clean_dataset_df['source_city'].dropna())
        flight_dests = set(clean_dataset_df['destination_city'].dropna())
        
        # Note: The column names in routes.csv have leading spaces
        route_sources = set(routes_df[' source airport'].dropna())
        route_dests = set(routes_df[' destination apirport'].dropna())

        # Combine all unique locations
        all_locations = train_stations.union(train_sources, train_dests, 
                                             flight_sources, flight_dests,
                                             route_sources, route_dests)

        # Convert to a sorted list for consistency
        sorted_locations = sorted(list(all_locations))

        # Create the final mapping structure
        city_mapping = {'cities': sorted_locations}

        # Write to JSON file
        with open('city_mapping.json', 'w') as f:
            json.dump(city_mapping, f, indent=4)

        print(f"Successfully created city_mapping.json with {len(sorted_locations)} unique locations.")

    except FileNotFoundError as e:
        print(f"Error: {e}. Make sure all required CSV files are in the directory.")
    except KeyError as e:
        print(f"Error: A column was not found in one of the CSV files: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    create_city_mapping()
