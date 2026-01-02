import pandas as pd
import numpy as np
from collections import defaultdict
import heapq
from datetime import datetime, timedelta
import json
from collections import deque

class ParetoTrainRouter:
    """
    Advanced train routing with Pareto-Optimal multi-objective optimization
    Combines O(E log V) Dijkstra with Pareto frontier analysis
    """
    
    def __init__(self, df):
        self.df = df
        self.station_to_id = {}
        self.id_to_station = {}
        self.graph = defaultdict(list)
        self.train_info = {}
        self._build_graph()
    
    def _build_graph(self):
        """Build graph with edges between all pairs of stations on the same train"""
        print("Building optimized graph...")
        
        unique_stations = self.df['Station Code'].unique()
        for idx, station in enumerate(unique_stations):
            self.station_to_id[station] = idx
            self.id_to_station[idx] = station
        
        grouped = self.df.groupby('Train No')
        edge_count = 0
        
        for train_no, train_df in grouped:
            train_df = train_df.sort_values('SEQ').reset_index(drop=True)
            stations_data = train_df.to_dict('records')
            
            self.train_info[train_no] = {
                'name': train_df.iloc[0]['Train Name'],
                'source': train_df.iloc[0]['Source Station'],
                'destination': train_df.iloc[0]['Destination Station'],
                'stations': []
            }
            
            # Store station info for the train
            for row in stations_data:
                self.train_info[train_no]['stations'].append({
                    'station': row['Station Code'],
                    'seq': int(row['SEQ']),
                    'arrival': row['Arrival time'],
                    'departure': row['Departure Time'],
                    'distance': float(row['Distance'])
                })
            
            # Add edges between all pairs (i, j) where j > i
            for i in range(len(stations_data)):
                curr_row = stations_data[i]
                from_id = self.station_to_id[curr_row['Station Code']]
                
                for j in range(i + 1, len(stations_data)):
                    next_row = stations_data[j]
                    to_id = self.station_to_id[next_row['Station Code']]
                    
                    distance = abs(float(next_row['Distance']) - float(curr_row['Distance']))
                    # Use actual time for duration
                    duration = self._calculate_wait_time(curr_row['Departure Time'], next_row['Arrival time'])
                    
                    edge = {
                        'to_id': to_id,
                        'train_no': train_no,
                        'departure': curr_row['Departure Time'],
                        'arrival': next_row['Arrival time'],
                        'distance': distance,
                        'duration': duration,
                        'from_seq': int(curr_row['SEQ']),
                        'to_seq': int(next_row['SEQ']),
                        'seat_available': curr_row['Seat Availability']
                    }
                    
                    self.graph[from_id].append(edge)
                    edge_count += 1
        
        print(f"✓ Graph built: {len(self.station_to_id)} stations, {edge_count} edges")
    
    def find_direct_trains(self, source, destination):
        """Find all direct trains"""
        direct_trains = []
        
        for train_no, info in self.train_info.items():
            stations = [s['station'] for s in info['stations']]
            if source in stations and destination in stations:
                src_idx = stations.index(source)
                dst_idx = stations.index(destination)
                if dst_idx > src_idx:
                    direct_trains.append(train_no)
        
        return direct_trains
    
    def generate_all_routes(self, source, destination, max_transfers=3):
        """
        Generate comprehensive route set using multi-strategy search
        Returns: List of all feasible routes (200-300 routes)
        """
        source_id = self.station_to_id[source]
        dest_id = self.station_to_id[destination]
        
        all_routes = []
        
        print("\n🔍 Phase 1: Generating comprehensive route set...")
        
        # Strategy 1: Direct routes (0 transfers)
        print("  → Finding direct routes...")
        direct_routes = self._find_direct_routes(source_id, dest_id)
        all_routes.extend(direct_routes)
        print(f"    Found {len(direct_routes)} direct routes")
        
        # Strategy 2: Single-transfer routes (1 transfer)
        if max_transfers >= 1:
            print("  → Finding single-transfer routes...")
            single_transfer = self._find_single_transfer_routes(source_id, dest_id)
            all_routes.extend(single_transfer)
            print(f"    Found {len(single_transfer)} single-transfer routes")
        
        # Strategy 3: Multi-transfer routes (2-3 transfers)
        if max_transfers >= 2:
            print("  → Finding multi-transfer routes...")
            multi_transfer = self._find_multi_transfer_routes(source_id, dest_id, max_transfers)
            all_routes.extend(multi_transfer)
            print(f"    Found {len(multi_transfer)} multi-transfer routes")
        
        print(f"\n✓ Total routes generated: {len(all_routes)}")
        return self._deduplicate_routes(all_routes)
    
    def _find_direct_routes(self, source_id, dest_id):
        """Find all direct train routes"""
        routes = []
        
        for edge in self.graph[source_id]:
            if edge['to_id'] == dest_id:
                path = [{
                    'train_no': edge['train_no'],
                    'from': self.id_to_station[source_id],
                    'to': self.id_to_station[dest_id],
                    'departure': edge['departure'],
                    'arrival': edge['arrival'],
                    'distance': edge['distance'],
                    'duration': edge['duration'],
                    'wait_before': 0,
                    'seat_available': edge['seat_available']
                }]
                routes.append(path)
        
        return routes
    
    def _find_single_transfer_routes(self, source_id, dest_id, max_routes=100):
        """Find routes with exactly 1 transfer via major junctions"""
        routes = []
        visited_junctions = set()
        
        # Find intermediate stations (junctions)
        for edge1 in self.graph[source_id]:
            junction_id = edge1['to_id']
            
            if junction_id in visited_junctions or junction_id == dest_id:
                continue
            visited_junctions.add(junction_id)
            
            # Find connections from junction to destination
            for edge2 in self.graph[junction_id]:
                if edge2['to_id'] == dest_id:
                    # Check if different trains
                    if edge1['train_no'] != edge2['train_no']:
                        wait_time = self._calculate_wait_time(edge1['arrival'], edge2['departure'])
                        
                        # Realistic transfer time: 30 min to 8 hours
                        if 0.5 <= wait_time <= 8:
                            path = [
                                {
                                    'train_no': edge1['train_no'],
                                    'from': self.id_to_station[source_id],
                                    'to': self.id_to_station[junction_id],
                                    'departure': edge1['departure'],
                                    'arrival': edge1['arrival'],
                                    'distance': edge1['distance'],
                                    'duration': edge1['duration'],
                                    'wait_before': 0,
                                    'seat_available': edge1['seat_available']
                                },
                                {
                                    'train_no': edge2['train_no'],
                                    'from': self.id_to_station[junction_id],
                                    'to': self.id_to_station[dest_id],
                                    'departure': edge2['departure'],
                                    'arrival': edge2['arrival'],
                                    'distance': edge2['distance'],
                                    'duration': edge2['duration'],
                                    'wait_before': wait_time,
                                    'seat_available': edge2['seat_available']
                                }
                            ]
                            routes.append(path)
                            
                            if len(routes) >= max_routes:
                                return routes
        
        return routes
    
    def _find_multi_transfer_routes(self, source_id, dest_id, max_transfers, max_routes=100):
        """Find routes with 2-3 transfers using BFS on trains"""
        routes = []
        # queue stores: (current_station_id, current_path, num_transfers, total_distance)
        queue = deque([(source_id, [], 0, 0)])
        visited = {} # station_id -> min_transfers
        
        while queue and len(routes) < max_routes:
            curr_id, path, transfers, total_dist = queue.popleft()
            
            if curr_id == dest_id:
                routes.append(path)
                continue
                
            if transfers > max_transfers:
                continue
                
            # Optimization: if we reached this station with more transfers than before, skip
            if curr_id in visited and visited[curr_id] < transfers:
                continue
            visited[curr_id] = transfers
            
            # Limit branching factor for performance
            edges = self.graph[curr_id]
            if len(edges) > 500:
                # Prioritize edges that go towards destination or are major trains
                # For now, just take a sample to avoid explosion
                edges = edges[:500]

            for edge in edges:
                # Check for transfer
                is_transfer = False
                wait_time = 0
                if path:
                    is_transfer = True 
                    wait_time = self._calculate_wait_time(path[-1]['arrival'], edge['departure'])
                    # Realistic transfer time: 30 min to 12 hours
                    if wait_time < 0.5 or wait_time > 12:
                        continue
                
                new_transfers = transfers + (1 if path else 0)
                if new_transfers > max_transfers:
                    continue
                    
                new_segment = {
                    'train_no': edge['train_no'],
                    'from': self.id_to_station[curr_id],
                    'to': self.id_to_station[edge['to_id']],
                    'departure': edge['departure'],
                    'arrival': edge['arrival'],
                    'distance': edge['distance'],
                    'duration': edge['duration'],
                    'wait_before': wait_time,
                    'seat_available': edge['seat_available']
                }
                
                queue.append((edge['to_id'], path + [new_segment], new_transfers, total_dist + edge['distance']))
        
        return routes
    
    def calculate_route_objectives(self, path):
        """
        Calculate 5 optimization objectives for a route
        Returns: (time, cost, transfers, seat_prob, safety_score)
        """
        # Objective 1: Total journey time (minimize)
        total_time = sum(seg['duration'] + seg['wait_before'] for seg in path)
        
        # Objective 2: Total cost (minimize) - ₹1 per km
        total_distance = sum(seg['distance'] for seg in path)
        total_cost = total_distance * 1.0
        
        # Objective 3: Number of transfers (minimize)
        transfers = len(path) - 1
        
        # Objective 4: Seat availability probability (maximize)
        # Set to 100% as requested
        seat_prob = 100.0
        
        # Objective 5: Safety score (maximize)
        # Set to 100% as requested
        safety_score = 100.0
        
        return {
            'time': total_time * 60,  # Convert to minutes
            'cost': total_cost,
            'transfers': transfers,
            'seat_prob': seat_prob,
            'safety_score': safety_score,
            'distance': total_distance
        }
    
    def pareto_optimize(self, routes):
        """
        Apply Pareto optimization to find non-dominated routes
        Returns: Pareto-optimal routes (typically 20-40% of total)
        """
        print("\n🎯 Phase 2: Pareto optimization analysis...")
        
        # Calculate objectives for all routes
        route_objectives = []
        for route in routes:
            obj = self.calculate_route_objectives(route)
            route_objectives.append({
                'route': route,
                'objectives': obj
            })
        
        # Find Pareto front
        pareto_front = []
        
        for i, route_i in enumerate(route_objectives):
            is_dominated = False
            obj_i = route_i['objectives']
            
            for j, route_j in enumerate(route_objectives):
                if i == j:
                    continue
                
                obj_j = route_j['objectives']
                
                # Check if route_j dominates route_i
                if self._dominates(obj_j, obj_i):
                    is_dominated = True
                    break
            
            if not is_dominated:
                pareto_front.append(route_i)
        
        print(f"✓ Pareto front size: {len(pareto_front)} / {len(routes)} routes")
        return pareto_front
    
    def _dominates(self, obj_a, obj_b):
        """
        Check if objective set A dominates B
        A dominates B if A is better or equal in all objectives and strictly better in at least one
        
        Minimize: time, cost, transfers
        Maximize: seat_prob, safety_score
        """
        # A must be better or equal in all objectives
        better_or_equal = (
            obj_a['time'] <= obj_b['time'] and
            obj_a['cost'] <= obj_b['cost'] and
            obj_a['transfers'] <= obj_b['transfers'] and
            obj_a['seat_prob'] >= obj_b['seat_prob'] and
            obj_a['safety_score'] >= obj_b['safety_score']
        )
        
        # A must be strictly better in at least one objective
        strictly_better = (
            obj_a['time'] < obj_b['time'] or
            obj_a['cost'] < obj_b['cost'] or
            obj_a['transfers'] < obj_b['transfers'] or
            obj_a['seat_prob'] > obj_b['seat_prob'] or
            obj_a['safety_score'] > obj_b['safety_score']
        )
        
        return better_or_equal and strictly_better
    
    def _get_route_fingerprint(self, route):
        """Generate a unique, hashable fingerprint for a route."""
        return tuple(segment['train_no'] for segment in route)
    
    def _deduplicate_routes(self, routes):
        """Removes duplicate routes based on their fingerprint."""
        unique_routes = {}
        for route in routes:
            fingerprint = self._get_route_fingerprint(route)
            unique_routes[fingerprint] = route
        return list(unique_routes.values())

    def select_optimal_routes(self, pareto_front):
        """
        Select 7 diverse optimal routes from Pareto front.
        """
        print(f"\n🏆 Phase 3: Selecting 7 diverse optimal routes...")
        
        if len(pareto_front) == 0:
            return [], []
        
        # Maps fingerprint to (route_data, category)
        final_selections = {} 

        # Sort by different objectives
        sorted_by_time = sorted(pareto_front, key=lambda x: x['objectives']['time'])
        sorted_by_cost = sorted(pareto_front, key=lambda x: x['objectives']['cost'])
        sorted_by_dist = sorted(pareto_front, key=lambda x: x['objectives']['distance'])
        
        # Helper to add route
        def add_route(route_data, category):
            if len(final_selections) >= 7:
                return False
            fingerprint = self._get_route_fingerprint(route_data['route'])
            if fingerprint not in final_selections:
                final_selections[fingerprint] = (route_data, category)
                return True
            return False

        # 1. Absolute Fastest
        add_route(sorted_by_time[0], 'FASTEST ⚡')
        
        # 2. Absolute Cheapest
        add_route(sorted_by_cost[0], 'CHEAPEST 💰')
        
        # 3. Shortest Distance
        add_route(sorted_by_dist[0], 'SHORTEST 📏')

        # 4. Balanced (using a simple score)
        times = [r['objectives']['time'] for r in pareto_front]
        costs = [r['objectives']['cost'] for r in pareto_front]
        min_t, max_t = min(times), max(times) + 1
        min_c, max_c = min(costs), max(costs) + 1
        
        for r in pareto_front:
            # Normalized score (lower is better)
            r['score'] = ((r['objectives']['time'] - min_t) / (max_t - min_t)) + \
                         ((r['objectives']['cost'] - min_c) / (max_c - min_c))
        
        sorted_balanced = sorted(pareto_front, key=lambda x: x['score'])
        
        # Add balanced routes until we hit 7
        for r in sorted_balanced:
            add_route(r, 'BALANCED ⚖️')
            if len(final_selections) >= 7:
                break

        # Convert back to lists
        optimal_routes = []
        categories = []
        for r_data, cat in final_selections.values():
            optimal_routes.append(r_data)
            categories.append(cat)
            
        return optimal_routes, categories

    def _calculate_duration(self, distance):
        """Calculate realistic travel duration"""
        if distance > 1800:
            return distance / 58
        elif distance > 1000:
            return distance / 60
        elif distance > 500:
            return distance / 55
        elif distance > 300:
            return distance / 50
        elif distance > 150:
            return distance / 45
        else:
            return distance / 38
    
    def _calculate_wait_time(self, arrival_time, departure_time):
        """Calculate waiting time in hours"""
        try:
            fmt = '%H:%M:%S'
            t1 = datetime.strptime(arrival_time, fmt)
            t2 = datetime.strptime(departure_time, fmt)
            if t2 < t1:
                t2 += timedelta(days=1)
            return (t2 - t1).total_seconds() / 3600
        except:
            return 1.0
    
    def format_duration(self, minutes):
        """Format duration as HH:MM"""
        h = int(minutes // 60)
        m = int(minutes % 60)
        return f"{h}h {m}m"

def get_routes_data(source, destination, max_transfers):
    # Load data
    try:
        df = pd.read_csv('Train_details.csv', low_memory=False)
        df = df[df['Train No'].astype(str).str.len() == 5].copy()
        df['Seat Availability'] = np.random.choice([0, 1], size=len(df), p=[0.2, 0.8])
    except FileNotFoundError:
        return {"error": "Could not find 'Train_details.csv'."}, None
    except Exception as e:
        return {"error": str(e)}, None

    # Initialize router
    router = ParetoTrainRouter(df)

    if source not in router.station_to_id:
        return {"error": f"Station '{source}' not found."}, router
    if destination not in router.station_to_id:
        return {"error": f"Station '{destination}' not found."}, router
    if source == destination:
        return {"error": "Origin and destination must be different."}, router

    # PIPELINE: Generate → Optimize → Select
    all_routes = router.generate_all_routes(source, destination, max_transfers)

    if not all_routes:
        return {"error": "No routes found!"}, router

    # Save all routes to a CSV file
    save_all_routes(router, all_routes, source, destination)

    pareto_front = router.pareto_optimize(all_routes)
    optimal_routes, categories = router.select_optimal_routes(pareto_front)

    # Save and get JSON data
    json_data = save_results(router, optimal_routes, categories,
                             f"{source}_to_{destination}_pareto_routes.csv",
                             f"{source}_to_{destination}_pareto_routes.json",
                             all_routes, pareto_front, source, destination)
    
    return json_data, router

def main():
    print("\n" + "="*80)
    print(" PARETO-OPTIMAL TRAIN ROUTE OPTIMIZER")
    print(" Multi-Objective Optimization: Time | Cost | Transfers | Comfort | Safety")
    print("="*80)

    # Get user input
    source = input("Enter origin station code (e.g., PGT, CSMT): ").strip().upper()
    destination = input("Enter destination station code (e.g., KOTA, NGP): ").strip().upper()
    
    while True:
        try:
            max_transfers = int(input("Maximum transfers allowed (0-3): "))
            if 0 <= max_transfers <= 3:
                break
            print("Please enter 0-3")
        except ValueError:
            print("Invalid input")

    print("\n" + "="*80)
    print("STARTING PARETO OPTIMIZATION PIPELINE")
    print("="*80)
    
    results, router = get_routes_data(source, destination, max_transfers)

    if "error" in results:
        print(f"Error: {results['error']}")
        return

    # For console output, we can re-create some of the original display logic
    # This is a simplified version of the original output.
    print("\n" + "="*80)
    print("ALL OPTIMAL ROUTES - COMPARE & CHOOSE YOUR PREFERENCE")
    print("="*80)

    print("\n📊 QUICK COMPARISON TABLE")
    print("-" * 80)
    print(f"{'Route':<8} {'Category':<20} {'Time':<10} {'Cost':<8} {'Transfer':<9} {'Seats':<8} {'Safety':<7}")
    print("-" * 80)

    if router:
        for route_data in results['optimal_routes']:
            obj = route_data['objectives']
            time_str = router.format_duration(obj['time'])
            print(f"{route_data['route_id']:<8} {route_data['category']:<20} {time_str:<10} ₹{obj['cost']:<7.0f} "
                  f"{obj['transfers']:<9} {obj['seat_prob']:<7.1f}% {obj['safety_score']:<6.0f}/100")

    print("-" * 80)
    print("\n💾 Results also saved to JSON and CSV files.")


def save_all_routes(router, all_routes, source, destination):
    """Save all generated routes to a CSV file."""
    csv_file = f"{source}_to_{destination}_all_routes.csv"
    print(f"\n💾 Saving all {len(all_routes)} generated routes to {csv_file}...")

    # Prepare CSV data
    csv_rows = []
    for idx, route in enumerate(all_routes, 1):
        for seg_num, segment in enumerate(route, 1):
            train_name = router.train_info[segment['train_no']]['name']
            
            csv_rows.append({
                'Route ID': f"ROUTE_{idx:02d}",
                'Segment': seg_num,
                'Train Number': segment['train_no'],
                'Train Name': train_name,
                'From': segment['from'],
                'To': segment['to'],
                'Departure': segment['departure'],
                'Arrival': segment['arrival'],
                'Distance (km)': round(segment['distance'], 2),
                'Duration': router.format_duration(segment['duration'] * 60),
                'Wait Before': router.format_duration(segment['wait_before'] * 60)
            })

    # Save CSV
    df_out = pd.DataFrame(csv_rows)
    df_out.to_csv(csv_file, index=False)
    print(f"✓ All routes saved successfully.")


def save_results(router, optimal_routes, categories, csv_file, json_file,
                 all_routes, pareto_front, source, destination):
    """Save optimization results to CSV and JSON, and return JSON data"""

    # Prepare CSV data
    csv_rows = []
    json_data = {
        'metadata': {
            'source': source,
            'destination': destination,
            'total_routes_generated': len(all_routes),
            'pareto_front_size': len(pareto_front),
            'optimal_routes_count': len(optimal_routes)
        },
        'optimal_routes': [], # Renamed 'routes' to 'optimal_routes' for clarity
        'all_generated_routes': [] # New key for all routes
    }

    for idx, (route_data, category) in enumerate(zip(optimal_routes, categories), 1):
        route = route_data['route']
        obj = route_data['objectives']

        route_json = {
            'route_id': f"OPT_ROUTE_{idx:02d}", # Prefix for optimal routes
            'category': category,
            'objectives': obj,
            'segments': []
        }

        for seg_num, segment in enumerate(route, 1):
            train_name = router.train_info[segment['train_no']]['name']

            csv_rows.append({
                'Route ID': f"OPT_ROUTE_{idx:02d}",
                'Category': category,
                'Segment': seg_num,
                'Train Number': segment['train_no'],
                'Train Name': train_name,
                'From': segment['from'],
                'To': segment['to'],
                'Departure': segment['departure'],
                'Arrival': segment['arrival'],
                'Distance (km)': round(segment['distance'], 2),
                'Duration': router.format_duration(segment['duration'] * 60),
                'Wait Before': router.format_duration(segment['wait_before'] * 60),
                'Seat Available': segment['seat_available'],
                'Total Time (min)': round(obj['time'], 2),
                'Total Cost (₹)': round(obj['cost'], 2),
                'Total Transfers': obj['transfers'],
                'Seat Probability (%)': round(obj['seat_prob'], 2),
                'Safety Score': round(obj['safety_score'], 2)
            })

            route_json['segments'].append({
                'train_no': segment['train_no'],
                'train_name': train_name,
                'from': segment['from'],
                'to': segment['to'],
                'departure': segment['departure'],
                'arrival': segment['arrival'],
                'distance': round(segment['distance'], 2),
                'duration_min': round(segment['duration'] * 60, 2),
                'wait_min': round(segment['wait_before'] * 60, 2)
            })

        json_data['optimal_routes'].append(route_json) # Append to optimal_routes
    
    # Process all generated routes for JSON output
    for idx, route in enumerate(all_routes, 1):
        obj = router.calculate_route_objectives(route)
        
        num_transfers = len(route) - 1
        if num_transfers == 0:
            category = "Direct 🚀"
        elif num_transfers == 1:
            category = "1 Transfer ↔️"
        else:
            category = "Multi-Transfer 🌐"

        route_json = {
            'route_id': f"ALL_ROUTE_{idx:03d}", # Prefix for all routes
            'category': category,
            'objectives': obj,
            'segments': []
        }
        
        for seg_num, segment in enumerate(route, 1):
            train_name = router.train_info[segment['train_no']]['name']
            route_json['segments'].append({
                'train_no': segment['train_no'],
                'train_name': train_name,
                'from': segment['from'],
                'to': segment['to'],
                'departure': segment['departure'],
                'arrival': segment['arrival'],
                'distance': round(segment['distance'], 2),
                'duration_min': round(segment['duration'] * 60, 2),
                'wait_min': round(segment['wait_before'] * 60, 2)
            })
        json_data['all_generated_routes'].append(route_json)


    # Save CSV
    df_out = pd.DataFrame(csv_rows)
    df_out.to_csv(csv_file, index=False)

    # Save JSON file
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=2)

    return json_data
