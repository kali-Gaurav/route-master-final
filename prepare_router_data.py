import pandas as pd
import pickle
from route_optimizer import ParetoTrainRouter
import numpy as np

def prepare_router_data():
    """
    This script prepares the ParetoTrainRouter object and saves it to a file.
    This avoids the expensive graph building process on every API request.
    """
    print("Loading train data...")
    try:
        df = pd.read_csv('Train_details.csv', low_memory=False)
        df = df[df['Train No'].astype(str).str.len() == 5].copy()
        # The 'Seat Availability' is randomly generated in the original code,
        # so we do it here as well during the pre-computation.
        df['Seat Availability'] = np.random.choice([0, 1], size=len(df), p=[0.2, 0.8])
    except FileNotFoundError:
        print("Error: 'Train_details.csv' not found.")
        return

    print("Building the router object... (This may take a while)")
    router = ParetoTrainRouter(df)
    print("Router object created successfully.")

    print("Saving router object to 'router_data.pkl'...")
    with open('router_data.pkl', 'wb') as f:
        pickle.dump(router, f)
    print("Router data saved successfully.")

if __name__ == "__main__":
    prepare_router_data()
