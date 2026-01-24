#!/usr/bin/env python3
"""Direct test of route finding"""

import sys
sys.path.insert(0, '.')

from optimization_engine import OptimizedGraphBuilder
import pandas as pd
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load the data
print("Loading train data...")
df = pd.read_csv('Train_details.csv')
print(f"Loaded {len(df)} records")

# Build the graph
print("\nBuilding graph...")
builder = OptimizedGraphBuilder()
graph_data = builder.build_from_dataframe(df)

print(f"\nGraph built:")
print(f"  Stations: {len(graph_data['station_to_id'])}")
print(f"  Edges: {sum(len(v) for v in graph_data['adjacency_list'].values())}")

# Check some stations
station_to_id = graph_data['station_to_id']
id_to_station = graph_data['id_to_station']
adjacency_list = graph_data['adjacency_list']

print(f"\nChecking specific stations:")
test_stations = ['NDLS', 'KOTA', 'PGT', 'CSMT', 'HWH', 'ADI']
for st in test_stations:
    if st in station_to_id:
        st_id = station_to_id[st]
        edges = len(adjacency_list[st_id]) if st_id in adjacency_list else 0
        print(f"  {st}: ID={st_id}, Edges from this station={edges}")
    else:
        print(f"  {st}: NOT FOUND")

# Test finding direct routes
print("\n\nTesting direct route finding:")
if 'NDLS' in station_to_id and 'KOTA' in station_to_id:
    source_id = station_to_id['NDLS']
    dest_id = station_to_id['KOTA']
    
    print(f"Looking for direct routes from NDLS (ID={source_id}) to KOTA (ID={dest_id})")
    
    if source_id in adjacency_list:
        edges = adjacency_list[source_id]
        print(f"Edges from NDLS: {len(edges)}")
        
        direct_count = 0
        for edge in edges:
            if edge['to_id'] == dest_id:
                direct_count += 1
                print(f"  Found: Train {edge['train_no']}")
        
        if direct_count == 0:
            print(f"  No direct routes found")
    else:
        print(f"NDLS has no edges in the graph!")
