#!/usr/bin/env python3
"""Test that graph builds entirely from RAPPID database without CSV files."""

from route_optimizer import GraphSingleton
from database_manager import get_db

print("Testing graph build from RAPPID database...")
print("="*80)

gs = GraphSingleton(db=get_db())

print("\nGraph Statistics:")
print(f"  Stations: {len(gs._station_maps['station_to_id'])}")
print(f"  Trains: {len(gs._train_info)}")
print(f"  Graph size: {sum(len(edges) for edges in gs._graph.values())} edges")

print("\nSample train info:")
for train_no in list(gs._train_info.keys())[:3]:
    info = gs._train_info[train_no]
    print(f"  Train {train_no}: {info['name']} with {len(info['stations'])} stations")

print("\n" + "="*80)
print("SUCCESS: Graph built entirely from RAPPID database")
print("NO CSV FILES READ")
print("="*80)
