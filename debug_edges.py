#!/usr/bin/env python3
"""
Debug: Examine actual graph edges for DADAR
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from route_optimizer import GraphSingleton
from database_manager import get_db

def main():
    print("\n" + "="*80)
    print("GRAPH EDGES EXAMINATION - DADAR station")
    print("="*80 + "\n")
    
    db = get_db()
    graph = GraphSingleton(db)
    
    # Get DADAR
    dadar_code = "DADAR"
    dadar_id = graph.station_maps['station_to_id'].get(dadar_code)
    
    print(f"Station: {dadar_code} (ID: {dadar_id})")
    print(f"\nEdges from DADAR ({len(graph.graph[dadar_id])} total):")
    
    edges = graph.graph[dadar_id][:10]  # First 10
    for edge in edges:
        to_id = edge['to_id']
        to_station = graph.station_maps['id_to_station'][to_id]
        train_no = edge['train_no']
        print(f"   Train {train_no:6} → {to_station}")
    
    # Check if THANE is reachable
    thane_code = "THANE"
    thane_id = graph.station_maps['station_to_id'].get(thane_code)
    
    print(f"\nSearching for THANE (ID: {thane_id}) in DADAR's edges...")
    found = False
    for edge in graph.graph[dadar_id]:
        if edge['to_id'] == thane_id:
            print(f"✅ Found! Train {edge['train_no']} connects DADAR → THANE")
            found = True
            break
    
    if not found:
        print(f"❌ THANE not directly connected from DADAR")
        
        # Check reverse
        print(f"\nLet's check if THANE has edges to other stations...")
        print(f"Edges from THANE ({len(graph.graph[thane_id])} total):")
        
        thane_edges = graph.graph[thane_id][:10]
        for edge in thane_edges:
            to_id = edge['to_id']
            to_station = graph.station_maps['id_to_station'][to_id]
            train_no = edge['train_no']
            print(f"   Train {train_no:6} → {to_station}")


if __name__ == '__main__':
    main()
