#!/usr/bin/env python3
"""
Debug: Check graph structure and station connections
"""

import sys
from pathlib import Path
import sqlite3
import time

sys.path.insert(0, str(Path(__file__).parent))

from route_optimizer import GraphSingleton
from database_manager import get_db

def main():
    print("\n" + "="*80)
    print("GRAPH STRUCTURE DEBUG")
    print("="*80 + "\n")
    
    # Initialize graph
    print("Loading graph...")
    db = get_db()
    graph_singleton = GraphSingleton(db)
    
    print(f"✅ Graph loaded")
    print(f"   Stations: {len(graph_singleton.station_maps['id_to_station'])}")
    print(f"   Edges: {sum(len(edges) for edges in graph_singleton.graph.values())}\n")
    
    # Check specific stations
    test_stations = ['HOWRAHJN', 'JAYNAGAR', 'SHRIGANGAN']
    
    for station_code in test_stations:
        station_id = graph_singleton.station_maps['station_to_id'].get(station_code)
        
        if station_id is None:
            print(f"❌ {station_code}: NOT in station_maps")
            
            # Try to find it in database
            conn = sqlite3.connect('production.db')
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT station_name FROM rappid_routes WHERE UPPER(REPLACE(station_name, ' ', ''))[:10] LIKE ?", 
                          (f"%{station_code}%",))
            results = cursor.fetchall()
            conn.close()
            
            if results:
                print(f"   Found in database:")
                for (name,) in results[:5]:
                    code = name.upper().replace(" ", "")[:10]
                    print(f"      - {code} ({name})")
            print()
        else:
            edges = graph_singleton.graph.get(station_id, [])
            print(f"✅ {station_code}: ID={station_id}, {len(edges)} connections")
            
            if edges:
                print(f"   First 5 connections:")
                for edge in edges[:5]:
                    to_station = graph_singleton.station_maps['id_to_station'][edge['to_id']]
                    train = edge['train_no']
                    print(f"      - Train {train} to {to_station}")
            print()
    
    # Check database for test route
    print("\n" + "="*80)
    print("DATABASE QUERY: Trains with HOWRAHJN → JAYNAGAR")
    print("="*80 + "\n")
    
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    # Find trains that have both stations in sequence
    cursor.execute("""
        WITH howrah_trains AS (
            SELECT train_no, station_sequence
            FROM rappid_routes
            WHERE UPPER(REPLACE(station_name, ' ', '')) LIKE 'HOWRAHJN%'
        ),
        jaynagar_trains AS (
            SELECT train_no, station_sequence
            FROM rappid_routes  
            WHERE UPPER(REPLACE(station_name, ' ', '')) LIKE 'JAYNAGAR%'
        )
        SELECT DISTINCT h.train_no, h.station_sequence as howrah_seq, j.station_sequence as jaynagar_seq
        FROM howrah_trains h
        JOIN jaynagar_trains j ON h.train_no = j.train_no
        WHERE j.station_sequence > h.station_sequence
        LIMIT 10
    """)
    
    results = cursor.fetchall()
    print(f"Found {len(results)} trains with HOWRAHJN before JAYNAGAR:")
    for train_no, howrah_seq, jaynagar_seq in results[:5]:
        print(f"   Train {train_no}: HOWRAHJN (seq {howrah_seq}) → JAYNAGAR (seq {jaynagar_seq})")
    
    # Check raw station names
    print("\n" + "="*80)
    print("DATABASE: Check raw station names")
    print("="*80 + "\n")
    
    cursor.execute("SELECT DISTINCT station_name FROM rappid_routes WHERE station_name LIKE '%Howrah%' LIMIT 5")
    print("Howrah stations:")
    for (name,) in cursor.fetchall():
        code = name.upper().replace(" ", "")[:10]
        print(f"   {code:10} = {name}")
    
    cursor.execute("SELECT DISTINCT station_name FROM rappid_routes WHERE station_name LIKE '%Jaynagar%' LIMIT 5")
    print("\nJaynagar stations:")
    for (name,) in cursor.fetchall():
        code = name.upper().replace(" ", "")[:10]
        print(f"   {code:10} = {name}")
    
    conn.close()

if __name__ == '__main__':
    main()
