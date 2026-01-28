# ===============================================
# ROUTE FINDING ENGINE
# ===============================================
# Complete route search with single and multi-transfer support

import sqlite3
from functools import lru_cache
from collections import defaultdict
from datetime import datetime, timedelta
from config import DB_PATH, DB_TIMEOUT, MAX_TRANSFERS
from database import DatabaseConnection

class RouteFinder:
    """Main route searching engine"""
    
    def __init__(self):
        self.db_path = DB_PATH
        # Simple per-instance caches to reduce repeated DB queries during combinatorial searches
        # Cache for direct route lookups keyed by (source, destination)
        self._direct_cache = {}
        # Cache for train_runs_on results keyed by (train_no, iso_date)
        self._runs_cache = {}
    
    @staticmethod
    def calculate_time_diff(departure, arrival, day_diff=0):
        """Calculate travel time between departure and arrival"""
        try:
            dep = datetime.strptime(departure, '%H:%M:%S')
            arr = datetime.strptime(arrival, '%H:%M:%S')
            
            # If arrival is earlier than departure, it's next day
            if day_diff == 0 and arr < dep:
                day_diff = 1
            
            # Calculate total minutes
            dep_minutes = dep.hour * 60 + dep.minute
            arr_minutes = arr.hour * 60 + arr.minute
            
            if day_diff > 0:
                arr_minutes += (24 * 60 * day_diff)
            
            total_minutes = arr_minutes - dep_minutes
            hours = total_minutes // 60
            minutes = total_minutes % 60
            
            return total_minutes, f"{hours}h {minutes}m"
        except:
            return 0, "N/A"
    
    @staticmethod
    def calculate_transfer_waiting(arr_time_str, dep_time_str):
        """Calculate waiting time between trains considering day transitions
        Returns: (waiting_minutes, day_offset, waiting_str, transfer_info)
        where day_offset is 0 for same day, 1 for next day departures"""
        arr_time = datetime.strptime(arr_time_str, '%H:%M:%S')
        dep_time = datetime.strptime(dep_time_str, '%H:%M:%S')
        
        # Minimum transfer time (baggage handling, etc.)
        MIN_TRANSFER_TIME = 30  # minutes
        
        # Convert to minutes since midnight
        arr_minutes = arr_time.hour * 60 + arr_time.minute
        dep_minutes = dep_time.hour * 60 + dep_time.minute
        
        day_offset = 0

        # Case 1: Departure is later same day
        if dep_minutes > arr_minutes:
            waiting_minutes = dep_minutes - arr_minutes
            waiting_str = f"{waiting_minutes // 60}h {waiting_minutes % 60}m"
            transfer_info = f"Same day transfer: {arr_time_str} → {dep_time_str}"

        # Case 2: Departure is earlier (must be next day)
        else:
            waiting_minutes = (24 * 60 - arr_minutes) + dep_minutes
            waiting_str = f"{waiting_minutes // 60}h {waiting_minutes % 60}m"
            day_offset = 1
            transfer_info = f"Next day transfer: {arr_time_str} (Day 1) → {dep_time_str}+1d (Day 2)"
        
        # Ensure minimum transfer time is respected
        valid = True
        if waiting_minutes < MIN_TRANSFER_TIME:
            # This is an invalid transfer - too little time
            valid = False
            transfer_info = f"Invalid: only {waiting_minutes}m between trains (min {MIN_TRANSFER_TIME}m)"

        return waiting_minutes, day_offset, waiting_str, transfer_info, valid

    def train_runs_on(self, train_no, base_date=None, day_offset=0):
        """Check `train_running_days` for whether `train_no` runs on base_date + day_offset.
        `base_date` is a datetime.date. If None, uses today."""
        try:
            if base_date is None:
                base_date = datetime.today().date()
            target_date = base_date + timedelta(days=day_offset)
            weekday = target_date.weekday()  # 0=Mon,6=Sun
            day_cols = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
            day_col = day_cols[weekday]

            # Check cache first
            cache_key = (int(train_no), target_date.isoformat())
            if cache_key in self._runs_cache:
                return self._runs_cache[cache_key]

            with DatabaseConnection(self.db_path) as db:
                if not db.connect():
                    return False
                query = f"SELECT {day_col} FROM train_running_days WHERE train_no = ?"
                res = db.execute_single(query, (train_no,))
                if not res:
                    self._runs_cache[cache_key] = False
                    return False
                result_bool = bool(res[0])
                self._runs_cache[cache_key] = result_bool
                return result_bool
        except:
            return False

    def get_running_days_for_trains(self, train_day_map, base_date=None):
        """Batch-check running-day flags for many (train_no, day_offset) pairs.

        Accepts: an iterable of (train_no, day_offset) pairs. Returns a dict mapping
        (train_no, iso_date) -> bool indicating whether the train runs on that date.
        This allows callers to pre-compute all required train/date checks and fetch
        them in grouped DB queries.
        """
        pairs = list(train_day_map)
        if base_date is None:
            base_date = datetime.today().date()

        # Group trains by target_date (ISO) -> list of train_nos
        date_to_trains = defaultdict(list)
        pair_keys = []
        for train_no, day_offset in pairs:
            iso = (base_date + timedelta(days=day_offset)).isoformat()
            date_to_trains[iso].append(int(train_no))
            pair_keys.append((int(train_no), iso))

        results = {}
        with DatabaseConnection(self.db_path) as db:
            if not db.connect():
                for k in pair_keys:
                    results[k] = False
                return results

            for iso_date, train_list in date_to_trains.items():
                try:
                    target_date = datetime.fromisoformat(iso_date).date()
                except Exception:
                    target_date = base_date
                weekday = target_date.weekday()  # 0=Mon
                day_cols = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
                day_col = day_cols[weekday]

                placeholders = ','.join(['?'] * len(train_list))
                query = f"SELECT train_no, {day_col} FROM train_running_days WHERE train_no IN ({placeholders})"
                rows = db.execute_query(query, tuple(train_list))
                present = {int(r[0]): bool(r[1]) for r in rows} if rows else {}

                for t in train_list:
                    key = (int(t), iso_date)
                    results[key] = present.get(int(t), False)
                    # update cache
                    self._runs_cache[key] = results[key]

        return results


# Module-level LRU-cached helper for direct route queries
@lru_cache(maxsize=1024)
def _find_direct_routes_cached(db_path, source, destination):
    """Cached helper that mirrors `RouteFinder.find_direct_routes` query logic.

    Returns a list of dicts similar to `find_direct_routes`.
    """
    rf = RouteFinder()
    # Avoid recursion into cached method by calling the DB query path directly
    with DatabaseConnection(db_path) as db:
        if not db.connect():
            return []

        query = """
            SELECT DISTINCT
                t.train_no,
                t.train_name,
                t.train_type,
                r1.seq_no as source_seq,
                r2.seq_no as dest_seq,
                r1.departure_time,
                r2.arrival_time,
                r2.distance_from_source - r1.distance_from_source as distance,
                CASE WHEN r2.arrival_time < r1.departure_time THEN 1 ELSE 0 END as day_diff
            FROM trains_master t
            JOIN train_routes r1 ON t.train_no = r1.train_no AND r1.station_code = ?
            JOIN train_routes r2 ON t.train_no = r2.train_no AND r2.station_code = ?
            WHERE r1.seq_no < r2.seq_no
            ORDER BY r1.departure_time
        """

        routes = db.execute_query(query, (source, destination))
        result = []
        for route in routes:
            train_no, name, ttype, src_seq, dst_seq, dep, arr, dist, day_diff = route
            time_minutes, time_str = rf.calculate_time_diff(dep, arr, day_diff or 0)
            result.append({
                'train_no': train_no,
                'train_name': name,
                'train_type': ttype,
                'source_seq': src_seq,
                'dest_seq': dst_seq,
                'departure': dep,
                'arrival': arr,
                'distance': dist or 0,
                'time_minutes': time_minutes,
                'time_str': time_str,
                'day_diff': day_diff or 0
            })

        return result
    
    @staticmethod
    def format_distance(km):
        """Format distance in km"""
        if km is None or km == 0:
            return "N/A"
        return f"{km} km"
    
    def get_leg_details(self, train_no, source, destination):
        """Get distance and time details for a leg"""
        with DatabaseConnection(self.db_path) as db:
            if not db.connect():
                return {"distance": 0, "time_minutes": 0, "time_str": "N/A"}
            
            query = """
                SELECT 
                    r1.departure_time,
                    r2.arrival_time,
                    r2.distance_from_source - r1.distance_from_source as leg_distance,
                    CASE WHEN r2.arrival_time < r1.departure_time THEN 1 ELSE 0 END as day_diff
                FROM train_routes r1
                JOIN train_routes r2 ON r1.train_no = r2.train_no 
                    AND r1.station_code = ? 
                    AND r2.station_code = ?
                    AND r1.seq_no < r2.seq_no
                WHERE r1.train_no = ?
                LIMIT 1
            """
            
            result = db.execute_single(query, (source, destination, train_no))
            
            if result:
                departure, arrival, distance, day_diff = result
                time_minutes, time_str = self.calculate_time_diff(departure, arrival, day_diff or 0)
                
                return {
                    "distance": distance or 0,
                    "time_minutes": time_minutes,
                    "time_str": time_str,
                    "departure": departure,
                    "arrival": arrival
                }
            
            return {"distance": 0, "time_minutes": 0, "time_str": "N/A"}
        
    def find_direct_routes(self, source, destination):
        """Find direct trains between two stations"""
        source = source.upper().strip()
        destination = destination.upper().strip()
        # Prefer the module-level LRU-cached helper to maximize cache hits
        try:
            cached = _find_direct_routes_cached(self.db_path, source, destination)
            # keep an instance cache copy as well
            import copy
            self._direct_cache[(source, destination)] = copy.deepcopy(cached)
            return copy.deepcopy(cached)
        except Exception:
            # Fall back to DB path if cache helper fails
            cache_key = (source, destination)
            if cache_key in self._direct_cache:
                import copy as _copy
                return _copy.deepcopy(self._direct_cache[cache_key])

            with DatabaseConnection(self.db_path) as db:
                if not db.connect():
                    return []

                query = """
                    SELECT DISTINCT
                        t.train_no,
                        t.train_name,
                        t.train_type,
                        r1.seq_no as source_seq,
                        r2.seq_no as dest_seq,
                        r1.departure_time,
                        r2.arrival_time,
                        r2.distance_from_source - r1.distance_from_source as distance,
                        CASE WHEN r2.arrival_time < r1.departure_time THEN 1 ELSE 0 END as day_diff
                    FROM trains_master t
                    JOIN train_routes r1 ON t.train_no = r1.train_no AND r1.station_code = ?
                    JOIN train_routes r2 ON t.train_no = r2.train_no AND r2.station_code = ?
                    WHERE r1.seq_no < r2.seq_no
                    ORDER BY r1.departure_time
                """

                routes = db.execute_query(query, (source, destination))

                # Add time calculation to each route
                result = []
                for route in routes:
                    train_no, name, ttype, src_seq, dst_seq, dep, arr, dist, day_diff = route
                    time_minutes, time_str = self.calculate_time_diff(dep, arr, day_diff or 0)
                    result.append({
                        'train_no': train_no,
                        'train_name': name,
                        'train_type': ttype,
                        'source_seq': src_seq,
                        'dest_seq': dst_seq,
                        'departure': dep,
                        'arrival': arr,
                        'distance': dist or 0,
                        'time_minutes': time_minutes,
                        'time_str': time_str,
                        'day_diff': day_diff or 0
                    })
                # store in cache
                try:
                    import copy as _copy
                    self._direct_cache[cache_key] = _copy.deepcopy(result)
                except Exception:
                    self._direct_cache[cache_key] = result

                return result
    
    def find_one_transfer_routes(self, source, destination, start_date=None, max_results=100, verbose=False):
        """Find routes with exactly one transfer"""
        source = source.upper().strip()
        destination = destination.upper().strip()
        
        with DatabaseConnection(self.db_path) as db:
            if not db.connect():
                return []
            
            # Find all stations reachable from source and that can reach destination
            query = """
                SELECT DISTINCT j.station_code
                FROM stations_master j
                WHERE EXISTS (
                    SELECT 1 FROM train_routes tr1
                    WHERE tr1.station_code = j.station_code
                    AND EXISTS (
                        SELECT 1 FROM train_routes tr1b
                        WHERE tr1b.train_no = tr1.train_no
                        AND tr1b.station_code = ?
                        AND tr1b.seq_no < tr1.seq_no
                    )
                )
                AND EXISTS (
                    SELECT 1 FROM train_routes tr2
                    WHERE tr2.station_code = j.station_code
                    AND EXISTS (
                        SELECT 1 FROM train_routes tr2b
                        WHERE tr2b.train_no = tr2.train_no
                        AND tr2b.station_code = ?
                        AND tr2b.seq_no > tr2.seq_no
                    )
                )
                AND j.station_code NOT IN (?, ?)
                LIMIT 200
            """
            
            junctions = db.execute_query(query, (source, destination, source, destination))
            
            routes = []
            skips = []
            for junction in junctions:
                junction_code = junction[0]

                # Get trains from source to junction
                leg1_trains = self.find_direct_routes(source, junction_code)

                # Get trains from junction to destination
                leg2_trains = self.find_direct_routes(junction_code, destination)

                # Precompute combination info so we can batch-check running days
                combo_info = {}
                running_checks = []
                base_date_obj = start_date or datetime.today().date()

                for train1 in leg1_trains[:10]:
                    for train2 in leg2_trains[:10]:
                        wait_result = self.calculate_transfer_waiting(train1['arrival'], train2['departure'])
                        waiting_minutes, wait_day_offset, waiting_str, transfer_info, wait_valid = wait_result
                        leg1_arrival_day = train1.get('day_diff', 0)
                        dep2_day_offset = leg1_arrival_day + (wait_day_offset or 0)

                        key = (int(train1['train_no']), int(train2['train_no']))
                        combo_info[key] = {
                            'train1': train1,
                            'train2': train2,
                            'waiting_minutes': waiting_minutes,
                            'wait_day_offset': wait_day_offset,
                            'waiting_str': waiting_str,
                            'transfer_info': transfer_info,
                            'wait_valid': wait_valid,
                            'dep2_day_offset': dep2_day_offset
                        }

                        if wait_valid:
                            running_checks.append((int(train2['train_no']), dep2_day_offset))

                # Batch-check running days for all candidate connecting trains
                running_map = {}
                if running_checks:
                    running_map = self.get_running_days_for_trains(running_checks, base_date=base_date_obj)

                # Materialize routes or skips
                for k, info in combo_info.items():
                    train1 = info['train1']
                    train2 = info['train2']
                    waiting_minutes = info['waiting_minutes']
                    waiting_str = info['waiting_str']
                    transfer_info = info['transfer_info']
                    wait_valid = info['wait_valid']
                    dep2_day_offset = info['dep2_day_offset']

                    if not wait_valid:
                        if verbose:
                            try:
                                target_date = (base_date_obj + timedelta(days=dep2_day_offset)).isoformat()
                            except:
                                target_date = str(base_date_obj)
                            skips.append({
                                'type': 'one_transfer',
                                'junction': junction_code,
                                'train1_no': train1['train_no'],
                                'train1_name': train1.get('train_name'),
                                'train2_no': train2['train_no'],
                                'train2_name': train2.get('train_name'),
                                'train2_departure': train2.get('departure'),
                                'wait_minutes': waiting_minutes,
                                'min_transfer_minutes': 30,
                                'target_date': target_date,
                                'reason': transfer_info
                            })
                        continue

                    iso = (base_date_obj + timedelta(days=dep2_day_offset)).isoformat()
                    runs_key = (int(train2['train_no']), iso)
                    runs_ok = running_map.get(runs_key, False)

                    if not runs_ok:
                        if verbose:
                            skips.append({
                                'type': 'one_transfer',
                                'junction': junction_code,
                                'train1_no': train1['train_no'],
                                'train1_name': train1.get('train_name'),
                                'train2_no': train2['train_no'],
                                'train2_name': train2.get('train_name'),
                                'train2_departure': train2.get('departure'),
                                'target_date': iso,
                                'reason': f"Train {train2['train_no']} does not run on {iso}"
                            })
                        continue

                    total_time_minutes = train1['time_minutes'] + train2['time_minutes'] + waiting_minutes
                    total_distance = train1['distance'] + train2['distance']
                    total_time_str = f"{total_time_minutes // 60}h {total_time_minutes % 60}m"

                    routes.append({
                        'type': 'one_transfer',
                        'leg1': {
                            'train_no': train1['train_no'],
                            'train_name': train1['train_name'],
                            'train_type': train1['train_type'],
                            'departure': train1['departure'],
                            'arrival': train1['arrival'],
                            'distance': train1['distance'],
                            'time_minutes': train1['time_minutes'],
                            'time_str': train1['time_str'],
                            'day': 1
                        },
                        'leg2': {
                            'train_no': train2['train_no'],
                            'train_name': train2['train_name'],
                            'train_type': train2['train_type'],
                            'departure': train2['departure'],
                            'arrival': train2['arrival'],
                            'distance': train2['distance'],
                            'time_minutes': train2['time_minutes'],
                            'time_str': train2['time_str'],
                            'day': 1 + dep2_day_offset
                        },
                        'junction': junction_code,
                        'waiting_time_minutes': waiting_minutes,
                        'waiting_time_str': waiting_str,
                        'transfer_info': transfer_info,
                        'total_distance': total_distance,
                        'total_time_minutes': total_time_minutes,
                        'total_time_str': total_time_str
                    })
            
            if verbose:
                return {'routes': routes[:max_results], 'skips': skips}
            return routes[:max_results]
    
    def find_two_transfer_routes(self, source, destination, start_date=None, max_results=50, verbose=False):
        """Find routes with exactly two transfers (3 legs)"""
        source = source.upper().strip()
        destination = destination.upper().strip()
        
        with DatabaseConnection(self.db_path) as db:
            if not db.connect():
                return []
            
            # Find possible first junctions
            query = """
                SELECT DISTINCT j.station_code
                FROM stations_master j
                WHERE EXISTS (
                    SELECT 1 FROM train_routes tr1
                    WHERE tr1.station_code = j.station_code
                    AND EXISTS (
                        SELECT 1 FROM train_routes tr1b
                        WHERE tr1b.train_no = tr1.train_no
                        AND tr1b.station_code = ?
                        AND tr1b.seq_no < tr1.seq_no
                    )
                )
                AND j.station_code NOT IN (?, ?)
                LIMIT 100
            """
            
            first_junctions = db.execute_query(query, (source, source, destination))
            routes = []
            skips = []
            
            for j1 in first_junctions[:15]:
                j1_code = j1[0]
                
                # Find second junctions from first junction
                second_junctions = db.execute_query(query, (j1_code, source, destination))
                
                for j2 in second_junctions[:10]:
                    j2_code = j2[0]
                    if j2_code == j1_code:
                        continue
                    
                    # Get trains for each leg
                    leg1 = self.find_direct_routes(source, j1_code)
                    leg2 = self.find_direct_routes(j1_code, j2_code)
                    leg3 = self.find_direct_routes(j2_code, destination)
                    
                    # Combine with limits but precompute combos to batch running-day checks
                    combos = []
                    running_checks = []
                    base_date_obj = start_date or datetime.today().date()

                    for t1 in leg1[:5]:
                        for t2 in leg2[:5]:
                            # wait between leg1 arrival and leg2 departure
                            wait1_result = self.calculate_transfer_waiting(t1['arrival'], t2['departure'])
                            wait1_min, wait1_day_offset, wait1_str, wait1_info, wait1_valid = wait1_result

                            leg1_arrival_day = t1.get('day_diff', 0)
                            t2_dep_day_offset = leg1_arrival_day + (wait1_day_offset or 0)

                            if not wait1_valid:
                                if verbose:
                                    try:
                                        target_date = (base_date_obj + timedelta(days=t2_dep_day_offset)).isoformat()
                                    except:
                                        target_date = str(base_date_obj)
                                    skips.append({
                                        'type': 'two_transfer',
                                        'junctions': (j1_code, j2_code),
                                        'train_nums': [t1['train_no'], t2['train_no']],
                                        'train_names': [t1.get('train_name'), t2.get('train_name')],
                                        'failed_leg': 2,
                                        'failed_train_no': t2['train_no'],
                                        'failed_train_name': t2.get('train_name'),
                                        'failed_departure': t2.get('departure'),
                                        'wait_minutes': wait1_min,
                                        'min_transfer_minutes': 30,
                                        'target_date': target_date,
                                        'reason': wait1_info
                                    })
                                continue

                            for t3 in leg3[:5]:
                                wait2_result = self.calculate_transfer_waiting(t2['arrival'], t3['departure'])
                                wait2_min, wait2_day_offset, wait2_str, wait2_info, wait2_valid = wait2_result

                                t2_arrival_day = t2_dep_day_offset + t2.get('day_diff', 0)
                                t3_dep_day_offset = t2_arrival_day + (wait2_day_offset or 0)

                                if not wait2_valid:
                                    if verbose:
                                        try:
                                            target_date = (base_date_obj + timedelta(days=t3_dep_day_offset)).isoformat()
                                        except:
                                            target_date = str(base_date_obj)
                                        skips.append({
                                            'type': 'two_transfer',
                                            'junctions': (j1_code, j2_code),
                                            'train_nums': [t1['train_no'], t2['train_no'], t3['train_no']],
                                            'train_names': [t1.get('train_name'), t2.get('train_name'), t3.get('train_name')],
                                            'failed_leg': 3,
                                            'failed_train_no': t3['train_no'],
                                            'failed_train_name': t3.get('train_name'),
                                            'failed_departure': t3.get('departure'),
                                            'wait_minutes': wait2_min,
                                            'min_transfer_minutes': 30,
                                            'target_date': target_date,
                                            'reason': wait2_info
                                        })
                                    continue

                                # Valid combination - store for later
                                combos.append({
                                    't1': t1,
                                    't2': t2,
                                    't3': t3,
                                    'wait1_min': wait1_min,
                                    'wait2_min': wait2_min,
                                    'wait1_str': wait1_str,
                                    'wait2_str': wait2_str,
                                    't2_dep_day_offset': t2_dep_day_offset,
                                    't3_dep_day_offset': t3_dep_day_offset
                                })

                                running_checks.append((int(t2['train_no']), t2_dep_day_offset))
                                running_checks.append((int(t3['train_no']), t3_dep_day_offset))

                    # Batch-check running days
                    running_map = {}
                    if running_checks:
                        # deduplicate
                        unique_checks = list({(int(t), d) for t, d in running_checks})
                        running_map = self.get_running_days_for_trains(unique_checks, base_date=base_date_obj)

                    # Finalize combos into routes or skips
                    for combo in combos:
                        t1 = combo['t1']
                        t2 = combo['t2']
                        t3 = combo['t3']
                        t2_iso = (base_date_obj + timedelta(days=combo['t2_dep_day_offset'])).isoformat()
                        t3_iso = (base_date_obj + timedelta(days=combo['t3_dep_day_offset'])).isoformat()

                        if not running_map.get((int(t2['train_no']), t2_iso), False):
                            if verbose:
                                skips.append({
                                    'type': 'two_transfer',
                                    'junctions': (j1_code, j2_code),
                                    'train_nums': [t1['train_no'], t2['train_no']],
                                    'train_names': [t1.get('train_name'), t2.get('train_name')],
                                    'failed_leg': 2,
                                    'failed_train_no': t2['train_no'],
                                    'failed_train_name': t2.get('train_name'),
                                    'failed_departure': t2.get('departure'),
                                    'target_date': t2_iso,
                                    'reason': f"Train {t2['train_no']} does not run on {t2_iso}"
                                })
                            continue

                        if not running_map.get((int(t3['train_no']), t3_iso), False):
                            if verbose:
                                skips.append({
                                    'type': 'two_transfer',
                                    'junctions': (j1_code, j2_code),
                                    'train_nums': [t1['train_no'], t2['train_no'], t3['train_no']],
                                    'train_names': [t1.get('train_name'), t2.get('train_name'), t3.get('train_name')],
                                    'failed_leg': 3,
                                    'failed_train_no': t3['train_no'],
                                    'failed_train_name': t3.get('train_name'),
                                    'failed_departure': t3.get('departure'),
                                    'target_date': t3_iso,
                                    'reason': f"Train {t3['train_no']} does not run on {t3_iso}"
                                })
                            continue

                        # Compute display day numbers
                        t2_day_display = 1 + combo['t2_dep_day_offset']
                        t3_day_display = 1 + combo['t3_dep_day_offset']

                        total_time_minutes = t1['time_minutes'] + t2['time_minutes'] + t3['time_minutes'] + combo['wait1_min'] + combo['wait2_min']
                        total_distance = t1['distance'] + t2['distance'] + t3['distance']
                        total_time_str = f"{total_time_minutes // 60}h {total_time_minutes % 60}m"

                        routes.append({
                            'type': 'two_transfer',
                            'legs': [
                                {'train_no': t1['train_no'], 'train_name': t1['train_name'], 'train_type': t1['train_type'],
                                 'departure': t1['departure'], 'arrival': t1['arrival'], 'from': source, 'to': j1_code,
                                 'distance': t1['distance'], 'time_str': t1['time_str'], 'day': 1},
                                {'train_no': t2['train_no'], 'train_name': t2['train_name'], 'train_type': t2['train_type'],
                                 'departure': t2['departure'], 'arrival': t2['arrival'], 'from': j1_code, 'to': j2_code,
                                 'distance': t2['distance'], 'time_str': t2['time_str'], 'day': t2_day_display},
                                {'train_no': t3['train_no'], 'train_name': t3['train_name'], 'train_type': t3['train_type'],
                                 'departure': t3['departure'], 'arrival': t3['arrival'], 'from': j2_code, 'to': destination,
                                 'distance': t3['distance'], 'time_str': t3['time_str'], 'day': t3_day_display}
                            ],
                            'total_distance': total_distance,
                            'waiting_times': [combo['wait1_str'], combo['wait2_str']],
                            'total_waiting_minutes': combo['wait1_min'] + combo['wait2_min'],
                            'total_time_minutes': total_time_minutes,
                            'total_time_str': total_time_str
                        })
            
            if verbose:
                return {'routes': routes[:max_results], 'skips': skips}
            return routes[:max_results]
    
    def find_three_transfer_routes(self, source, destination, start_date=None, max_results=30, verbose=False):
        """Find routes with exactly three transfers (4 legs)"""
        source = source.upper().strip()
        destination = destination.upper().strip()
        
        with DatabaseConnection(self.db_path) as db:
            if not db.connect():
                return []
            
            # Find possible first junctions
            query = """
                SELECT DISTINCT j.station_code
                FROM stations_master j
                WHERE EXISTS (
                    SELECT 1 FROM train_routes tr1
                    WHERE tr1.station_code = j.station_code
                    AND EXISTS (
                        SELECT 1 FROM train_routes tr1b
                        WHERE tr1b.train_no = tr1.train_no
                        AND tr1b.station_code = ?
                        AND tr1b.seq_no < tr1.seq_no
                    )
                )
                AND j.station_code NOT IN (?, ?)
                LIMIT 100
            """
            
            first_junctions = db.execute_query(query, (source, source, destination))
            routes = []
            skips = []
            
            for j1 in first_junctions[:10]:
                j1_code = j1[0]
                
                # Find second junctions
                second_junctions = db.execute_query(query, (j1_code, source, destination))
                
                for j2 in second_junctions[:8]:
                    j2_code = j2[0]
                    if j2_code == j1_code:
                        continue
                    
                    # Find third junctions
                    third_junctions = db.execute_query(query, (j2_code, j1_code, destination))
                    
                    for j3 in third_junctions[:5]:
                        j3_code = j3[0]
                        if j3_code in (j1_code, j2_code):
                            continue
                        
                        # Get all legs
                        leg1 = self.find_direct_routes(source, j1_code)
                        leg2 = self.find_direct_routes(j1_code, j2_code)
                        leg3 = self.find_direct_routes(j2_code, j3_code)
                        leg4 = self.find_direct_routes(j3_code, destination)
                        
                        # Combine with strict limits but precompute combos for batch checks
                        combos = []
                        running_checks = []
                        base_date_obj = start_date or datetime.today().date()

                        for t1 in leg1[:3]:
                            for t2 in leg2[:3]:
                                wait1_result = self.calculate_transfer_waiting(t1['arrival'], t2['departure'])
                                wait1, wait1_day_offset, wait1_str, wait1_info, wait1_valid = wait1_result

                                leg1_arrival_day = t1.get('day_diff', 0)
                                t2_dep_day_offset = leg1_arrival_day + (wait1_day_offset or 0)

                                if not wait1_valid:
                                    if verbose:
                                        try:
                                            target_date = (base_date_obj + timedelta(days=t2_dep_day_offset)).isoformat()
                                        except:
                                            target_date = str(base_date_obj)
                                        skips.append({
                                            'type': 'three_transfer',
                                            'junctions': (j1_code, j2_code, j3_code),
                                            'train_nums': [t1['train_no'], t2['train_no']],
                                            'train_names': [t1.get('train_name'), t2.get('train_name')],
                                            'failed_leg': 2,
                                            'failed_train_no': t2['train_no'],
                                            'failed_train_name': t2.get('train_name'),
                                            'failed_departure': t2.get('departure'),
                                            'wait_minutes': wait1,
                                            'min_transfer_minutes': 30,
                                            'target_date': target_date,
                                            'reason': wait1_info
                                        })
                                    continue

                                for t3 in leg3[:3]:
                                    wait2_result = self.calculate_transfer_waiting(t2['arrival'], t3['departure'])
                                    wait2, wait2_day_offset, wait2_str, wait2_info, wait2_valid = wait2_result

                                    t2_arrival_day = t2_dep_day_offset + t2.get('day_diff', 0)
                                    t3_dep_day_offset = t2_arrival_day + (wait2_day_offset or 0)

                                    if not wait2_valid:
                                        if verbose:
                                            try:
                                                target_date = (base_date_obj + timedelta(days=t3_dep_day_offset)).isoformat()
                                            except:
                                                target_date = str(base_date_obj)
                                            skips.append({
                                                'type': 'three_transfer',
                                                'junctions': (j1_code, j2_code, j3_code),
                                                'train_nums': [t1['train_no'], t2['train_no'], t3['train_no']],
                                                'train_names': [t1.get('train_name'), t2.get('train_name'), t3.get('train_name')],
                                                'failed_leg': 3,
                                                'failed_train_no': t3['train_no'],
                                                'failed_train_name': t3.get('train_name'),
                                                'failed_departure': t3.get('departure'),
                                                'wait_minutes': wait2,
                                                'min_transfer_minutes': 30,
                                                'target_date': target_date,
                                                'reason': wait2_info
                                            })
                                        continue

                                    for t4 in leg4[:3]:
                                        wait3_result = self.calculate_transfer_waiting(t3['arrival'], t4['departure'])
                                        wait3, wait3_day_offset, wait3_str, wait3_info, wait3_valid = wait3_result

                                        t3_arrival_day = t3_dep_day_offset + t3.get('day_diff', 0)
                                        t4_dep_day_offset = t3_arrival_day + (wait3_day_offset or 0)

                                        if not wait3_valid:
                                            if verbose:
                                                try:
                                                    target_date = (base_date_obj + timedelta(days=t4_dep_day_offset)).isoformat()
                                                except:
                                                    target_date = str(base_date_obj)
                                                skips.append({
                                                    'type': 'three_transfer',
                                                    'junctions': (j1_code, j2_code, j3_code),
                                                    'train_nums': [t1['train_no'], t2['train_no'], t3['train_no'], t4['train_no']],
                                                    'train_names': [t1.get('train_name'), t2.get('train_name'), t3.get('train_name'), t4.get('train_name')],
                                                    'failed_leg': 4,
                                                    'failed_train_no': t4['train_no'],
                                                    'failed_train_name': t4.get('train_name'),
                                                    'failed_departure': t4.get('departure'),
                                                    'wait_minutes': wait3,
                                                    'min_transfer_minutes': 30,
                                                    'target_date': target_date,
                                                    'reason': wait3_info
                                                })
                                            continue

                                        # Valid 4-leg combination - store
                                        combos.append({
                                            't1': t1,
                                            't2': t2,
                                            't3': t3,
                                            't4': t4,
                                            'wait1': wait1,
                                            'wait2': wait2,
                                            'wait3': wait3,
                                            'wait1_str': wait1_str,
                                            'wait2_str': wait2_str,
                                            'wait3_str': wait3_str,
                                            't2_dep_day_offset': t2_dep_day_offset,
                                            't3_dep_day_offset': t3_dep_day_offset,
                                            't4_dep_day_offset': t4_dep_day_offset
                                        })

                                        running_checks.append((int(t2['train_no']), t2_dep_day_offset))
                                        running_checks.append((int(t3['train_no']), t3_dep_day_offset))
                                        running_checks.append((int(t4['train_no']), t4_dep_day_offset))

                        # Batch-check running days for all candidate trains
                        running_map = {}
                        if running_checks:
                            unique_checks = list({(int(t), d) for t, d in running_checks})
                            running_map = self.get_running_days_for_trains(unique_checks, base_date=base_date_obj)

                        # Finalize combos into routes or skips
                        for combo in combos:
                            t1 = combo['t1']
                            t2 = combo['t2']
                            t3 = combo['t3']
                            t4 = combo['t4']

                            t2_iso = (base_date_obj + timedelta(days=combo['t2_dep_day_offset'])).isoformat()
                            t3_iso = (base_date_obj + timedelta(days=combo['t3_dep_day_offset'])).isoformat()
                            t4_iso = (base_date_obj + timedelta(days=combo['t4_dep_day_offset'])).isoformat()

                            if not running_map.get((int(t2['train_no']), t2_iso), False):
                                if verbose:
                                    skips.append({
                                        'type': 'three_transfer',
                                        'junctions': (j1_code, j2_code, j3_code),
                                        'train_nums': [t1['train_no'], t2['train_no']],
                                        'train_names': [t1.get('train_name'), t2.get('train_name')],
                                        'failed_leg': 2,
                                        'failed_train_no': t2['train_no'],
                                        'failed_train_name': t2.get('train_name'),
                                        'failed_departure': t2.get('departure'),
                                        'target_date': t2_iso,
                                        'reason': f"Train {t2['train_no']} does not run on {t2_iso}"
                                    })
                                continue

                            if not running_map.get((int(t3['train_no']), t3_iso), False):
                                if verbose:
                                    skips.append({
                                        'type': 'three_transfer',
                                        'junctions': (j1_code, j2_code, j3_code),
                                        'train_nums': [t1['train_no'], t2['train_no'], t3['train_no']],
                                        'train_names': [t1.get('train_name'), t2.get('train_name'), t3.get('train_name')],
                                        'failed_leg': 3,
                                        'failed_train_no': t3['train_no'],
                                        'failed_train_name': t3.get('train_name'),
                                        'failed_departure': t3.get('departure'),
                                        'target_date': t3_iso,
                                        'reason': f"Train {t3['train_no']} does not run on {t3_iso}"
                                    })
                                continue

                            if not running_map.get((int(t4['train_no']), t4_iso), False):
                                if verbose:
                                    skips.append({
                                        'type': 'three_transfer',
                                        'junctions': (j1_code, j2_code, j3_code),
                                        'train_nums': [t1['train_no'], t2['train_no'], t3['train_no'], t4['train_no']],
                                        'train_names': [t1.get('train_name'), t2.get('train_name'), t3.get('train_name'), t4.get('train_name')],
                                        'failed_leg': 4,
                                        'failed_train_no': t4['train_no'],
                                        'failed_train_name': t4.get('train_name'),
                                        'failed_departure': t4.get('departure'),
                                        'target_date': t4_iso,
                                        'reason': f"Train {t4['train_no']} does not run on {t4_iso}"
                                    })
                                continue

                            # Human-friendly day numbers
                            t2_day = 1 + combo['t2_dep_day_offset']
                            t3_day = 1 + combo['t3_dep_day_offset']
                            t4_day = 1 + combo['t4_dep_day_offset']

                            total_time_minutes = t1['time_minutes'] + t2['time_minutes'] + t3['time_minutes'] + t4['time_minutes'] + combo['wait1'] + combo['wait2'] + combo['wait3']
                            total_distance = t1['distance'] + t2['distance'] + t3['distance'] + t4['distance']
                            total_time_str = f"{total_time_minutes // 60}h {total_time_minutes % 60}m"

                            routes.append({
                                'type': 'three_transfer',
                                'legs': [
                                    {'train_no': t1['train_no'], 'train_name': t1['train_name'], 'train_type': t1['train_type'],
                                     'departure': t1['departure'], 'arrival': t1['arrival'], 'from': source, 'to': j1_code,
                                     'distance': t1['distance'], 'time_str': t1['time_str'], 'day': 1},
                                    {'train_no': t2['train_no'], 'train_name': t2['train_name'], 'train_type': t2['train_type'],
                                     'departure': t2['departure'], 'arrival': t2['arrival'], 'from': j1_code, 'to': j2_code,
                                     'distance': t2['distance'], 'time_str': t2['time_str'], 'day': t2_day},
                                    {'train_no': t3['train_no'], 'train_name': t3['train_name'], 'train_type': t3['train_type'],
                                     'departure': t3['departure'], 'arrival': t3['arrival'], 'from': j2_code, 'to': j3_code,
                                     'distance': t3['distance'], 'time_str': t3['time_str'], 'day': t3_day},
                                    {'train_no': t4['train_no'], 'train_name': t4['train_name'], 'train_type': t4['train_type'],
                                     'departure': t4['departure'], 'arrival': t4['arrival'], 'from': j3_code, 'to': destination,
                                     'distance': t4['distance'], 'time_str': t4['time_str'], 'day': t4_day}
                                ],
                                'total_distance': total_distance,
                                'waiting_times': [combo['wait1_str'], combo['wait2_str'], combo['wait3_str']],
                                'total_waiting_minutes': combo['wait1'] + combo['wait2'] + combo['wait3'],
                                'total_time_minutes': total_time_minutes,
                                'total_time_str': total_time_str
                            })
            
            if verbose:
                return {'routes': routes[:max_results], 'skips': skips}
            return routes[:max_results]
    
    def find_all_routes(self, source, destination, start_date=None, max_transfers=MAX_TRANSFERS, max_results=100, verbose=False, sort_by=None):
        """Find all possible routes (direct + all transfers)"""
        source = source.upper().strip()
        destination = destination.upper().strip()
        
        all_routes = {
            'direct': [],
            'one_transfer': [],
            'two_transfer': [],
            'three_transfer': []
        }
        
        # Direct routes
        direct = self.find_direct_routes(source, destination)
        all_routes['direct'] = direct[:max_results] if direct else []
        
        # One transfer routes
        if max_transfers >= 1:
            one_transfer = self.find_one_transfer_routes(source, destination, start_date, max_results, verbose=verbose)
            if isinstance(one_transfer, dict):
                all_routes['one_transfer'] = one_transfer.get('routes', [])
                if verbose:
                    all_routes.setdefault('skips', []).extend(one_transfer.get('skips', []))
            else:
                all_routes['one_transfer'] = one_transfer[:max_results] if one_transfer else []
        
        # Two transfer routes
        if max_transfers >= 2:
            two_transfer = self.find_two_transfer_routes(source, destination, start_date, max_results, verbose=verbose)
            if isinstance(two_transfer, dict):
                all_routes['two_transfer'] = two_transfer.get('routes', [])
                if verbose:
                    all_routes.setdefault('skips', []).extend(two_transfer.get('skips', []))
            else:
                all_routes['two_transfer'] = two_transfer[:max_results] if two_transfer else []
        
        # Three transfer routes
        if max_transfers >= 3:
            three_transfer = self.find_three_transfer_routes(source, destination, start_date, max_results, verbose=verbose)
            if isinstance(three_transfer, dict):
                all_routes['three_transfer'] = three_transfer.get('routes', [])
                if verbose:
                    all_routes.setdefault('skips', []).extend(three_transfer.get('skips', []))
            else:
                all_routes['three_transfer'] = three_transfer[:max_results] if three_transfer else []

        # Optionally sort results before returning. Supported: 'duration'
        if sort_by == 'duration':
            # Direct routes sort by `time_minutes`
            all_routes['direct'] = sorted(all_routes.get('direct', []), key=lambda r: r.get('time_minutes', float('inf')))
            # One/two/three transfer routes have `total_time_minutes`
            for key in ('one_transfer', 'two_transfer', 'three_transfer'):
                all_routes[key] = sorted(all_routes.get(key, []), key=lambda r: r.get('total_time_minutes', float('inf')))

        # `skips` has been collected during generation when verbose=True
        return all_routes
    
    def get_route_details(self, train_no, source, destination):
        """Get detailed information for a specific route"""
        train_no = int(train_no)
        source = source.upper().strip()
        destination = destination.upper().strip()
        
        details = {}
        
        with DatabaseConnection(self.db_path) as db:
            if not db.connect():
                return details
            
            # Get train info
            query = "SELECT train_no, train_name, train_type FROM trains_master WHERE train_no = ?"
            train = db.execute_single(query, (train_no,))
            
            if train:
                details['train'] = {
                    'number': train[0],
                    'name': train[1],
                    'type': train[2]
                }
            
            # Get schedule info
            query = """
                SELECT station_code, arrival_time, departure_time, 
                       distance_from_source, seq_no
                FROM train_routes
                WHERE train_no = ?
                ORDER BY seq_no
            """
            schedule = db.execute_query(query, (train_no,))
            details['journey'] = schedule if schedule else []
            
            # Get fares between source and destination
            query = """
                SELECT class_code, total_fare, available_seats
                FROM train_fares
                WHERE train_no = ? AND source_station = ? AND destination_station = ?
            """
            fares = db.execute_query(query, (train_no, source, destination))
            details['fares'] = {row[0]: {'price': row[1], 'seats': row[2]} for row in fares} if fares else {}
            
            # Check running days
            query = "SELECT MON, TUE, WED, THU, FRI, SAT, SUN FROM train_running_days WHERE train_no = ?"
            running = db.execute_single(query, (train_no,))
            details['running_days'] = {
                'MON': running[0],
                'TUE': running[1],
                'WED': running[2],
                'THU': running[3],
                'FRI': running[4],
                'SAT': running[5],
                'SUN': running[6]
            } if running else {}
        
        return details

def search_routes_interactive(source, destination):
    """User-friendly route search function"""
    finder = RouteFinder()
    
    print(f"\n🔍 Searching routes from {source.upper()} to {destination.upper()}...")
    
    routes = finder.find_all_routes(source, destination)

    total_routes = len(routes.get('direct', [])) + len(routes.get('one_transfer', [])) + len(routes.get('two_transfer', [])) + len(routes.get('three_transfer', []))

    if total_routes == 0:
        print(f"❌ No routes found between {source.upper()} and {destination.upper()}")
        return None

    print(f"\n✅ Found {total_routes} total routes:")
    print(f"   ✓ Direct: {len(routes.get('direct', []))} routes")
    print(f"   ✓ 1 Transfer: {len(routes.get('one_transfer', []))} routes")
    
    return routes

if __name__ == '__main__':
    print("Route Finder Test")
    print("=" * 50)
    
    finder = RouteFinder()
    
    # Test direct routes
    print("\nSearching NDLS -> HWH (Direct Routes)...")
    direct = finder.find_direct_routes('NDLS', 'HWH')
    print(f"Found {len(direct)} direct routes")
    if direct:
        print("Sample routes:")
        for route in direct[:3]:
            print(f"  Train {route[0]}: {route[1]} ({route[2]})")
            print(f"    Depart: {route[5]}, Arrive: {route[6]}")
