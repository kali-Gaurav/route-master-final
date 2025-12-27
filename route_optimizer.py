import pandas as pd
import numpy as np
from collections import defaultdict
import heapq
from datetime import datetime, timedelta
import json
from collections import deque

class ParetoRouteOptimizer:
    """
    Advanced train routing with Pareto-Optimal multi-objective optimization
    Combines O(E log V) Dijkstra with Pareto frontier analysis
    """
    
    def __init__(self, df, travel_date):
        self.df = df
        self.travel_date = travel_date # Store the travel date
        self.location_to_id = {}
        self.id_to_location = {}
        self.graph = defaultdict(list)
        self.segment_info = {}
        self._build_sparse_graph()
    
    def _build_sparse_graph(self):
        """Build sparse graph from the unified dataset."""
        print("Building optimized sparse graph for multimodal routes...")
        
        # Get all unique locations (stations and airports)
        all_locations = pd.concat([self.df['origin'], self.df['destination']]).unique()
        for idx, location in enumerate(all_locations):
            if location is None: continue
            self.location_to_id[location] = idx
            self.id_to_location[idx] = location
        
        edge_count = 0
        
        for _, segment in self.df.iterrows():
            if segment['origin'] not in self.location_to_id or segment['destination'] not in self.location_to_id:
                continue

            from_id = self.location_to_id[segment['origin']]
            to_id = self.location_to_id[segment['destination']]
            
            # Store segment info
            segment_id = segment['unique_id']
            if segment_id not in self.segment_info:
                 self.segment_info[segment_id] = {
                    'type': segment['type'],
                    'name': segment.get('train_name', 'N/A') if segment['type'] == 'train' else segment.get('airline', 'N/A')
                 }


            edge = {
                'to_id': to_id,
                'segment_id': segment_id,
                'departure': segment['departure_time'],
                'arrival': segment['arrival_time'],
                'distance': segment['distance_km'],
                'duration': segment['duration_minutes'] / 60 if segment['duration_minutes'] else 0, # in hours
                'cost': segment['cost_inr'],
                'seat_available': segment['Seat Availability']
            }
            
            self.graph[from_id].append(edge)
            edge_count += 1
        
        print(f"✓ Graph built: {len(self.location_to_id)} locations, {edge_count} edges")
    

    
    def generate_all_routes(self, source, destination, max_transfers=3):
        """
        Generate comprehensive route set using multi-strategy search
        Returns: List of all feasible routes (200-300 routes)
        """
        source_id = self.location_to_id[source]
        dest_id = self.location_to_id[destination]
        
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
        """Find all direct routes"""
        routes = []
        
        for edge in self.graph[source_id]:
            if edge['to_id'] == dest_id:
                path = [{
                    'segment_id': edge['segment_id'],
                    'from': self.id_to_location[source_id],
                    'to': self.id_to_location[dest_id],
                    'departure': edge['departure'],
                    'arrival': edge['arrival'],
                    'distance': edge['distance'],
                    'duration': edge['duration'],
                    'cost': edge['cost'],
                    'wait_before': 0,
                    'seat_available': edge['seat_available']
                }]
                routes.append(path)
        
        return routes
    
    def _find_single_transfer_routes(self, source_id, dest_id, max_routes=100):
        """Find routes with exactly 1 transfer"""
        routes = []
        visited_junctions = set()
        
        # Find intermediate locations (junctions)
        for edge1 in self.graph[source_id]:
            junction_id = edge1['to_id']
            
            if junction_id in visited_junctions or junction_id == dest_id:
                continue
            visited_junctions.add(junction_id)
            
            # Find connections from junction to destination
            for edge2 in self.graph[junction_id]:
                if edge2['to_id'] == dest_id:
                    # Check if different segments
                    if edge1['segment_id'] != edge2['segment_id']:
                        wait_time = self._calculate_wait_time(edge1['arrival'], edge2['departure'])
                        
                        # TODO: Add more sophisticated transfer penalty, e.g., based on location type (airport vs station)
                        
                        # Realistic transfer time: 30 min to 8 hours
                        if 0.5 <= wait_time <= 8:
                            path = [
                                {
                                    'segment_id': edge1['segment_id'],
                                    'from': self.id_to_location[source_id],
                                    'to': self.id_to_location[junction_id],
                                    'departure': edge1['departure'],
                                    'arrival': edge1['arrival'],
                                    'distance': edge1['distance'],
                                    'duration': edge1['duration'],
                                    'cost': edge1['cost'],
                                    'wait_before': 0,
                                    'seat_available': edge1['seat_available']
                                },
                                {
                                    'segment_id': edge2['segment_id'],
                                    'from': self.id_to_location[junction_id],
                                    'to': self.id_to_location[dest_id],
                                    'departure': edge2['departure'],
                                    'arrival': edge2['arrival'],
                                    'distance': edge2['distance'],
                                    'duration': edge2['duration'],
                                    'cost': edge2['cost'],
                                    'wait_before': wait_time,
                                    'seat_available': edge2['seat_available']
                                }
                            ]
                            routes.append(path)
                            
                            if len(routes) >= max_routes:
                                return routes
        
        return routes
    
    def _find_multi_transfer_routes(self, source_id, dest_id, max_transfers, max_routes=100):
        """Find routes with 2-3 transfers using BFS"""
        routes = []
        queue = deque()
        queue.append((source_id, [], 0, 0))
        visited = set()
        
        while queue and len(routes) < max_routes:
            current_id, path, transfers, total_dist = queue.popleft()
            
            if current_id == dest_id and path:
                routes.append(path[:])
                continue
            
            if transfers >= max_transfers or total_dist > 5000: # Increased distance for flights
                continue
            
            state = (current_id, transfers)
            if state in visited:
                continue
            visited.add(state)
            
            for edge in self.graph[current_id]:
                next_id = edge['to_id']
                
                wait_time = 0
                is_transfer = False
                
                if path:
                    last_segment_id = path[-1]['segment_id']
                    if last_segment_id != edge['segment_id']:
                        is_transfer = True
                        wait_time = self._calculate_wait_time(path[-1]['arrival'], edge['departure'])
                        if wait_time < 0.5 or wait_time > 8:
                            continue
                
                new_segment = {
                    'segment_id': edge['segment_id'],
                    'from': self.id_to_location[current_id],
                    'to': self.id_to_location[next_id],
                    'departure': edge['departure'],
                    'arrival': edge['arrival'],
                    'distance': edge['distance'],
                    'duration': edge['duration'],
                    'cost': edge['cost'],
                    'wait_before': wait_time,
                    'seat_available': edge['seat_available']
                }
                
                new_path = path + [new_segment]
                new_transfers = transfers + (1 if is_transfer else 0)
                new_dist = total_dist + (edge['distance'] if edge['distance'] is not None else 0)
                
                queue.append((next_id, new_path, new_transfers, new_dist))
        
        return routes
    
    def calculate_route_objectives(self, path):
        """
        Calculate 5 optimization objectives for a route
        Returns: (time, cost, transfers, seat_prob, safety_score)
        """
        # Objective 1: Total journey time (minimize)
        total_time = sum(seg['duration'] + seg['wait_before'] for seg in path)
        
        # Objective 2: Total cost (minimize)
        total_cost = sum(seg['cost'] for seg in path if seg['cost'] is not None)
        
        # Objective 3: Number of transfers (minimize)
        transfers = len(path) - 1
        
        # Objective 4: Seat availability probability (maximize)
        # Average seat availability across all segments
        seat_prob = np.mean([seg['seat_available'] for seg in path]) * 100
        
        # Objective 5: Safety score (maximize)
        # Based on: fewer transfers = safer
        base_safety = 100
        transfer_penalty = transfers * 10  # -10 points per transfer
        safety_score = max(base_safety - transfer_penalty, 40)
        
        total_distance = sum(seg['distance'] for seg in path if seg['distance'] is not None)

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
        return tuple(segment['segment_id'] for segment in route)
    
    def _get_route_type(self, route):
        has_train = False
        has_flight = False
        for segment in route:
            segment_info = self.segment_info[segment['segment_id']]
            if segment_info['type'] == 'train':
                has_train = True
            elif segment_info['type'] == 'flight':
                has_flight = True
        
        if has_train and has_flight:
            return "Train-Flight"
        elif has_train:
            return "Train Only"
        elif has_flight:
            return "Flight Only"
        else:
            return "Unknown" # Should not happen
    
    def _deduplicate_routes(self, routes):
        """Removes duplicate routes based on their fingerprint."""
        unique_routes = {}
        for route in routes:
            fingerprint = self._get_route_fingerprint(route)
            unique_routes[fingerprint] = route
        return list(unique_routes.values())

    def select_optimal_routes(self, pareto_front):
        """
        Selects a diverse set of up to 20 optimal routes from the Pareto front,
        prioritizing specific categories and ensuring a good balance of objectives.
        """
        print(f"\n🏆 Phase 3: Selecting diverse optimal routes (max {self.MAX_FINAL_ROUTES})...")
        
        if not pareto_front:
            return [], []
        
        # Add route_type to each pareto_front entry
        for route_data in pareto_front:
            route_data['route_type'] = self._get_route_type(route_data['route'])

        # --- Configuration ---
        self.MAX_FINAL_ROUTES = 20
        # Categories and their target counts for diversity
        category_targets = {
            'FASTEST ⚡': 1,
            'CHEAPEST 💰': 1,
            'MOST DIRECT 🚂': 1,
            'SAFEST 🛡️': 1,
            'BEST MULTIMODAL ✈️+🚂': 1,
            'BALANCED ⚖️': 2, # More balanced options
            'Train Only': 2,
            'Flight Only': 2,
            'Train-Flight': 2,
        }
        # --------------------
        
        final_selections = {} # Maps fingerprint to (route_data, category, priority)
        selected_fingerprints = set()
        current_priority = 100 # Higher number means higher priority

        # Helper to add a route if not already selected
        def add_route(route_data, category_tag, priority_val):
            fingerprint = self._get_route_fingerprint(route_data['route'])
            if fingerprint not in selected_fingerprints:
                final_selections[fingerprint] = {'route_data': route_data, 'category': category_tag, 'priority': priority_val}
                selected_fingerprints.add(fingerprint)
                return True
            return False

        # --- Step 1: Guarantee "Must-Have" Routes ---
        print("  → Adding absolute best routes in primary categories...")
        sorted_by_time = sorted(pareto_front, key=lambda x: x['objectives']['time'])
        sorted_by_cost = sorted(pareto_front, key=lambda x: x['objectives']['cost'])
        sorted_by_transfers = sorted(pareto_front, key=lambda x: x['objectives']['transfers'])
        sorted_by_safety = sorted(pareto_front, key=lambda x: x['objectives']['safety_score'], reverse=True)
        multimodal_routes = [r for r in pareto_front if r['route_type'] == 'Train-Flight']
        sorted_by_multimodal = sorted(multimodal_routes, key=lambda x: x['objectives']['time'])
        
        if sorted_by_time: add_route(sorted_by_time[0], 'FASTEST ⚡', current_priority); current_priority -= 1
        if sorted_by_cost: add_route(sorted_by_cost[0], 'CHEAPEST 💰', current_priority); current_priority -= 1
        if sorted_by_transfers: add_route(sorted_by_transfers[0], 'MOST DIRECT 🚂', current_priority); current_priority -= 1
        if sorted_by_safety: add_route(sorted_by_safety[0], 'SAFEST 🛡️', current_priority); current_priority -= 1
        if sorted_by_multimodal: add_route(sorted_by_multimodal[0], 'BEST MULTIMODAL ✈️+🚂', current_priority); current_priority -= 1

        # --- Step 2: Fill remaining slots with diverse Pareto-optimal routes ---
        print("  → Filling remaining slots with diverse options...")
        
        # Calculate balanced scores for all Pareto routes if not already done
        if pareto_front and 'balanced_score' not in pareto_front[0]:
            times = [r['objectives']['time'] for r in pareto_front]
            costs = [r['objectives']['cost'] for r in pareto_front]
            transfers_list = [r['objectives']['transfers'] for r in pareto_front]
            seats = [r['objectives']['seat_prob'] for r in pareto_front]
            safety = [r['objectives']['safety_score'] for r in pareto_front]
            
            min_time, max_time = (min(times), max(times)) if times else (0, 0)
            min_cost, max_cost = (min(costs), max(costs)) if costs else (0, 0)
            min_transfers, max_transfers_val = (min(transfers_list), max(transfers_list)) if transfers_list else (0, 0)
            min_seats, max_seats = (min(seats), max(seats)) if seats else (0, 0)
            min_safety, max_safety = (min(safety), max(safety)) if safety else (0, 0)

            time_range = max_time - min_time + 0.001
            cost_range = max_cost - min_cost + 0.001
            transfers_range = max_transfers_val - min_transfers + 0.001
            seats_range = max_seats - min_seats + 0.001
            safety_range = max_safety - min_safety + 0.001
            
            for route_data in pareto_front:
                obj = route_data['objectives']
                route_data['balanced_score'] = (
                    ((max_time - obj['time']) / time_range) * 0.25 +
                    ((max_cost - obj['cost']) / cost_range) * 0.25 +
                    ((max_transfers_val - obj['transfers']) / transfers_range) * 0.20 +
                    ((obj['seat_prob'] - min_seats) / seats_range) * 0.15 +
                    ((obj['safety_score'] - min_safety) / safety_range) * 0.15
                )
        sorted_balanced = sorted(pareto_front, key=lambda x: x['balanced_score'], reverse=True)

        # Iteratively add routes from sorted lists to achieve diversity and fill slots
        # We use a round-robin-like approach to pick from different sorted views
        all_sorted_views = {
            'time': iter(sorted_by_time),
            'cost': iter(sorted(pareto_front, key=lambda x: x['objectives']['cost'])),
            'transfers': iter(sorted(pareto_front, key=lambda x: x['objectives']['transfers'])),
            'balanced': iter(sorted_balanced),
            'multimodal': iter(sorted_by_multimodal)
        }
        
        while len(final_selections) < self.MAX_FINAL_ROUTES and pareto_front:
            routes_added_in_cycle = 0
            for view_name, route_iterator in all_sorted_views.items():
                if len(final_selections) >= self.MAX_FINAL_ROUTES:
                        break
                try:
                    route_data = next(route_iterator)
                    category_tag = route_data['route_type'] # Default category for diversity
                    
                    # Try to add with a more specific tag if it fits the primary categories and isn't taken
                    if view_name == 'time' and add_route(route_data, 'FAST ⚡', current_priority):
                        current_priority -= 1
                        routes_added_in_cycle += 1
                    elif view_name == 'cost' and add_route(route_data, 'CHEAP 💰', current_priority):
                        current_priority -= 1
                        routes_added_in_cycle += 1
                    elif view_name == 'balanced' and add_route(route_data, 'BALANCED ⚖️', current_priority):
                        current_priority -= 1
                        routes_added_in_cycle += 1
                    elif view_name == 'multimodal' and route_data['route_type'] == 'Train-Flight' and add_route(route_data, 'MULTIMODAL ✈️+🚂', current_priority):
                        current_priority -= 1
                        routes_added_in_cycle += 1
                    elif add_route(route_data, 'OPTIMAL ALTERNATIVE 🎯', current_priority): # Catch-all for other diverse options
                        current_priority -= 1
                        routes_added_in_cycle += 1
                except StopIteration:
                    continue # This iterator is exhausted

            if routes_added_in_cycle == 0 and len(final_selections) < self.MAX_FINAL_ROUTES:
                # If no new routes were added in a full cycle, and we still need more,
                # just pick from the remaining pareto_front by overall balanced score
                remaining_pareto = [r for r in sorted_balanced if self._get_route_fingerprint(r['route']) not in selected_fingerprints]
                for route_data in remaining_pareto:
                    if len(final_selections) >= self.MAX_FINAL_ROUTES:
                        break
                    if add_route(route_data, 'OPTIMAL ALTERNATIVE 🎯', current_priority):
                        current_priority -= 1


        # Convert dictionary back to lists, sorted by priority first, then by time
        final_selected_routes = []
        final_categories = []
        
        sorted_final_selections = sorted(final_selections.values(), key=lambda x: (x['priority'], x['route_data']['objectives']['time']), reverse=True)

        for selection_data in sorted_final_selections:
            final_selected_routes.append(selection_data['route_data'])
            final_categories.append(selection_data['category'])

        print(f"✓ Selected {len(final_selected_routes)} optimal routes for comparison")
        return final_selected_routes, final_categories    
    
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
    
    def _calculate_wait_time(self, arrival_time_str, departure_time_str):
        """Calculate waiting time in hours using the travel_date."""
        try:
            # Parse time strings to time objects
            arrival_time = datetime.strptime(arrival_time_str, '%H:%M:%S').time()
            departure_time = datetime.strptime(departure_time_str, '%H:%M:%S').time()

            # Construct datetime objects using the stored travel_date
            # The arrival of the first segment is on the travel_date
            # The departure of the second segment could be on the same day or next day relative to the arrival
            arrival_dt = datetime.combine(self.travel_date, arrival_time)
            departure_dt = datetime.combine(self.travel_date, departure_time)

            # If the departure of the next segment is earlier than the arrival of the current segment
            # it implies the departure is on the next day.
            if departure_dt < arrival_dt:
                departure_dt += timedelta(days=1)
            
            wait_time = (departure_dt - arrival_dt).total_seconds() / 3600
            return max(0, wait_time) # Ensure wait time is not negative

        except ValueError:
            # This should ideally not happen if time strings are consistent
            return 1.0 # Default wait time if parsing fails
    
    def format_duration(self, minutes):
        """Format duration as HH:MM"""
        h = int(minutes // 60)
        m = int(minutes % 60)
        return f"{h}h {m}m"

def get_routes_data(source, destination, max_transfers, travel_date_str):
    # Load data
    try:
        with open('unified_routes.json', 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        # df = df[df['Train No'].astype(str).str.len() == 5].copy()
        df['Seat Availability'] = np.random.choice([0, 1], size=len(df), p=[0.2, 0.8])
    except FileNotFoundError:
        return {"error": "Could not find 'unified_routes.json'."}, None
    except Exception as e:
        return {"error": str(e)}, None

    # Parse travel_date_str
    try:
        travel_date = datetime.strptime(travel_date_str, '%Y-%m-%d').date() if travel_date_str else datetime.now().date()
    except ValueError:
        return {"error": "Invalid travel date format. Expected YYYY-MM-DD."}, None

    # Initialize router
    router = ParetoRouteOptimizer(df, travel_date)

    if source not in router.location_to_id:
        return {"error": f"Station '{source}' not found."}, router
    if destination not in router.location_to_id:
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
    source = input("Enter origin station/airport code (e.g., JP, DEL): ").strip().upper()
    destination = input("Enter destination station/airport code (e.g., KOTA, BLR): ").strip().upper()
    
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
    print(f"{ 'Route':<8} {'Category':<20} {'Time':<10} {'Cost':<8} {'Transfer':<9} {'Seats':<8} {'Safety':<7}")
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
            segment_info = router.segment_info[segment['segment_id']]
            
            csv_rows.append({
                'Route ID': f"ROUTE_{idx:02d}",
                'Segment': seg_num,
                'Type': segment_info['type'],
                'Segment ID': segment['segment_id'],
                'Name': segment_info['name'],
                'From': segment['from'],
                'To': segment['to'],
                'Departure': segment['departure'],
                'Arrival': segment['arrival'],
                'Distance (km)': round(segment['distance'], 2) if segment['distance'] is not None else 0,
                'Duration': router.format_duration(segment['duration'] * 60),
                'Wait Before': router.format_duration(segment['wait_before'] * 60),
                'Cost': segment['cost']
            })

    # Save CSV
    df_out = pd.DataFrame(csv_rows)
    df_out.to_csv(csv_file, index=False)
    print(f"✓ All routes saved successfully.")


def save_results(router, optimal_routes, categories, csv_file, json_file, all_routes, pareto_front, source, destination):
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
            segment_info = router.segment_info[segment['segment_id']]
            
            csv_rows.append({
                'Route ID': f"OPT_ROUTE_{idx:02d}",
                'Category': category,
                'Segment': seg_num,
                'Type': segment_info['type'],
                'Segment ID': segment['segment_id'],
                'Name': segment_info['name'],
                'From': segment['from'],
                'To': segment['to'],
                'Departure': segment['departure'],
                'Arrival': segment['arrival'],
                'Distance (km)': round(segment['distance'], 2) if segment['distance'] is not None else 0,
                'Duration': router.format_duration(segment['duration'] * 60),
                'Wait Before': router.format_duration(segment['wait_before'] * 60),
                'Cost': segment['cost'],
                'Seat Available': segment['seat_available'],
                'Total Time (min)': round(obj['time'], 2),
                'Total Cost (₹)': round(obj['cost'], 2),
                'Total Transfers': obj['transfers'],
                'Seat Probability (%)': round(obj['seat_prob'], 2),
                'Safety Score': round(obj['safety_score'], 2)
            })

            route_json['segments'].append({
                'type': segment_info['type'],
                'segment_id': segment['segment_id'],
                'name': segment_info['name'],
                'from': segment['from'],
                'to': segment['to'],
                'departure': segment['departure'],
                'arrival': segment['arrival'],
                'distance': round(segment['distance'], 2) if segment['distance'] is not None else 0,
                'duration_min': round(segment['duration'] * 60, 2),
                'wait_min': round(segment['wait_before'] * 60, 2),
                'cost': segment['cost']
            })

        json_data['optimal_routes'].append(route_json) # Append to optimal_routes
    
    # Process all generated routes for JSON output
    # Categorize and sort all generated routes
    categorized_all_routes = []
    for route in all_routes:
        obj = router.calculate_route_objectives(route)
        route_type = router._get_route_type(route) # Get the route type

        route_json = {
            'route_id': f"ALL_ROUTE_{idx:03d}", # Prefix for all routes
            'category': route_type, # Use the determined route type as category
            'objectives': obj,
            'segments': []
        }
        
        for seg_num, segment in enumerate(route, 1):
            segment_info = router.segment_info[segment['segment_id']]
            route_json['segments'].append({
                'type': segment_info['type'],
                'segment_id': segment['segment_id'],
                'name': segment_info['name'],
                'from': segment['from'],
                'to': segment['to'],
                'departure': segment['departure'],
                'arrival': segment['arrival'],
                'distance': round(segment['distance'], 2) if segment['distance'] is not None else 0,
                'duration_min': round(segment['duration'] * 60, 2),
                'wait_min': round(segment['wait_before'] * 60, 2),
                'cost': segment['cost']
            })
        categorized_all_routes.append(route_json)
    
    # Sort all generated routes by time
    categorized_all_routes.sort(key=lambda x: x['objectives']['time'])
    json_data['all_generated_routes'] = categorized_all_routes

    # Sort optimal routes by time and take top 20
    optimal_routes.sort(key=lambda x: x['objectives']['time'])
    json_data['optimal_routes'] = [] # Clear existing optimal_routes to re-populate with sorted and limited
    for idx, route_data in enumerate(optimal_routes[:20], 1): # Take top 20
        route = route_data['route']
        obj = route_data['objectives']

        route_json = {
            'route_id': f"OPT_ROUTE_{idx:02d}", # Prefix for optimal routes
            'category': route_data['category'], # Keep the Pareto category
            'objectives': obj,
            'segments': []
        }

        for seg_num, segment in enumerate(route, 1):
            segment_info = router.segment_info[segment['segment_id']]
            
            # This part is for the CSV output, which will be generated from optimal_routes
            csv_rows.append({
                'Route ID': f"OPT_ROUTE_{idx:02d}",
                'Category': route_data['category'],
                'Segment': seg_num,
                'Type': segment_info['type'],
                'Segment ID': segment['segment_id'],
                'Name': segment_info['name'],
                'From': segment['from'],
                'To': segment['to'],
                'Departure': segment['departure'],
                'Arrival': segment['arrival'],
                'Distance (km)': round(segment['distance'], 2) if segment['distance'] is not None else 0,
                'Duration': router.format_duration(segment['duration'] * 60),
                'Wait Before': router.format_duration(segment['wait_before'] * 60),
                'Cost': segment['cost'],
                'Seat Available': segment['seat_available'],
                'Total Time (min)': round(obj['time'], 2),
                'Total Cost (₹)': round(obj['cost'], 2),
                'Total Transfers': obj['transfers'],
                'Seat Probability (%)': round(obj['seat_prob'], 2),
                'Safety Score': round(obj['safety_score'], 2)
            })

            route_json['segments'].append({
                'type': segment_info['type'],
                'segment_id': segment['segment_id'],
                'name': segment_info['name'],
                'from': segment['from'],
                'to': segment['to'],
                'departure': segment['departure'],
                'arrival': segment['arrival'],
                'distance': round(segment['distance'], 2) if segment['distance'] is not None else 0,
                'duration_min': round(segment['duration'] * 60, 2),
                'wait_min': round(segment['wait_before'] * 60, 2),
                'cost': segment['cost']
            })
        json_data['optimal_routes'].append(route_json) # Append to optimal_routes

if __name__ == '__main__':
    main()