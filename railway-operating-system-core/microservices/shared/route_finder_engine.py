# ===============================================
# RAILWAY ROUTE FINDER LIBRARY
# ===============================================
# Isolated, self-contained route finding engine
# Independent of database connections and external dependencies

from functools import lru_cache
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)

class RouteFinderEngine:
    """Isolated route finding engine with defined inputs and outputs"""

    def __init__(self):
        # Simple in-memory caches for performance
        self._direct_cache = {}
        self._runs_cache = {}

    @staticmethod
    def calculate_time_diff(departure: str, arrival: str, day_diff: int = 0) -> Tuple[int, str]:
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
        except Exception as e:
            logger.error(f"Error calculating time diff: {e}")
            return 0, "N/A"

    @staticmethod
    def calculate_transfer_waiting(
        arr_time_str: str,
        dep_time_str: str
    ) -> Tuple[int, int, str, str, bool]:
        """Calculate waiting time between trains considering day transitions"""
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

    def train_runs_on_date(
        self,
        train_no: int,
        target_date: datetime.date,
        running_days_data: Dict[int, Dict[str, bool]]
    ) -> bool:
        """Check if train runs on specific date using provided running days data"""
        try:
            cache_key = (train_no, target_date.isoformat())
            if cache_key in self._runs_cache:
                return self._runs_cache[cache_key]

            weekday = target_date.weekday()  # 0=Mon,6=Sun
            day_cols = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
            day_col = day_cols[weekday]

            if train_no not in running_days_data:
                self._runs_cache[cache_key] = False
                return False

            result_bool = running_days_data[train_no].get(day_col, False)
            self._runs_cache[cache_key] = result_bool
            return result_bool
        except Exception as e:
            logger.error(f"Error checking if train {train_no} runs on {target_date}: {e}")
            return False

    def find_direct_routes(
        self,
        source: str,
        destination: str,
        date: datetime.date,
        train_schedule_data: List[Dict[str, Any]],
        train_running_days: Dict[int, Dict[str, bool]]
    ) -> List[Dict[str, Any]]:
        """Find direct routes between source and destination"""
        routes = []

        try:
            # Get all trains that stop at source
            source_trains = [
                train for train in train_schedule_data
                if train['station_code'] == source
            ]

            # Get all trains that stop at destination
            dest_trains = [
                train for train in train_schedule_data
                if train['station_code'] == destination
            ]

            # Group by train_no
            source_by_train = defaultdict(list)
            dest_by_train = defaultdict(list)

            for train in source_trains:
                source_by_train[train['train_no']].append(train)
            for train in dest_trains:
                dest_by_train[train['train_no']].append(train)

            # Find common trains
            common_trains = set(source_by_train.keys()) & set(dest_by_train.keys())

            for train_no in common_trains:
                if not self.train_runs_on_date(train_no, date, train_running_days):
                    continue

                source_stops = source_by_train[train_no]
                dest_stops = dest_by_train[train_no]

                # Find the earliest departure from source and latest arrival at destination
                source_stop = min(source_stops, key=lambda x: x['departure_time'] or '23:59:59')
                dest_stop = max(dest_stops, key=lambda x: x['arrival_time'] or '00:00:00')

                # Ensure the destination stop comes after source stop in journey
                if dest_stop['day_of_journey'] < source_stop['day_of_journey']:
                    continue
                elif dest_stop['day_of_journey'] == source_stop['day_of_journey']:
                    if dest_stop['arrival_time'] <= source_stop['departure_time']:
                        continue

                # Calculate travel time
                day_diff = dest_stop['day_of_journey'] - source_stop['day_of_journey']
                travel_minutes, travel_time_str = self.calculate_time_diff(
                    source_stop['departure_time'],
                    dest_stop['arrival_time'],
                    day_diff
                )

                route = {
                    'train_no': train_no,
                    'train_name': f"Train {train_no}",  # Would be populated from trains_master
                    'source_station': source,
                    'destination_station': destination,
                    'departure_time': source_stop['departure_time'],
                    'arrival_time': dest_stop['arrival_time'],
                    'day_of_journey': source_stop['day_of_journey'],
                    'travel_time': travel_time_str,
                    'travel_minutes': travel_minutes,
                    'transfers': 0,
                    'route_type': 'direct'
                }
                routes.append(route)

        except Exception as e:
            logger.error(f"Error finding direct routes: {e}")

        return routes

    def find_single_transfer_routes(
        self,
        source: str,
        destination: str,
        date: datetime.date,
        train_schedule_data: List[Dict[str, Any]],
        train_running_days: Dict[int, Dict[str, bool]],
        stations_data: List[Dict[str, Any]],
        max_transfers: int = 1
    ) -> List[Dict[str, Any]]:
        """Find routes with one transfer between source and destination"""
        routes = []

        try:
            # Get junction stations
            junction_stations = {s['station_code'] for s in stations_data if s.get('is_junction', False)}

            # Get all trains that stop at source
            source_trains = [
                train for train in train_schedule_data
                if train['station_code'] == source
            ]

            # Get all trains that stop at destination
            dest_trains = [
                train for train in train_schedule_data
                if train['station_code'] == destination
            ]

            # Group by train_no
            source_by_train = defaultdict(list)
            dest_by_train = defaultdict(list)

            for train in source_trains:
                source_by_train[train['train_no']].append(train)
            for train in dest_trains:
                dest_by_train[train['train_no']].append(train)

            # For each first-leg train from source
            for first_train_no, first_stops in source_by_train.items():
                if not self.train_runs_on_date(first_train_no, date, train_running_days):
                    continue

                first_departure = min(first_stops, key=lambda x: x['departure_time'] or '23:59:59')

                # Find potential transfer stations for this train
                transfer_stations = set()
                for stop in first_stops:
                    if stop['station_code'] in junction_stations and stop['station_code'] != source:
                        transfer_stations.add(stop['station_code'])

                # For each potential transfer station
                for transfer_station in transfer_stations:
                    # Find arrival time at transfer station
                    transfer_arrival_stops = [
                        stop for stop in first_stops
                        if stop['station_code'] == transfer_station
                    ]
                    if not transfer_arrival_stops:
                        continue

                    transfer_arrival = max(transfer_arrival_stops, key=lambda x: x['arrival_time'] or '00:00:00')

                    # Find second-leg trains from transfer station to destination
                    for second_train_no, second_stops in dest_by_train.items():
                        if not self.train_runs_on_date(second_train_no, date, train_running_days):
                            continue

                        # Don't use same train for both legs
                        if second_train_no == first_train_no:
                            continue

                        # Find departure from transfer station
                        transfer_departure_stops = [
                            stop for stop in second_stops
                            if stop['station_code'] == transfer_station
                        ]
                        if not transfer_departure_stops:
                            continue

                        transfer_departure = min(
                            transfer_departure_stops,
                            key=lambda x: x['departure_time'] or '23:59:59'
                        )

                        # Find arrival at destination
                        dest_arrival_stops = [
                            stop for stop in second_stops
                            if stop['station_code'] == destination
                        ]
                        if not dest_arrival_stops:
                            continue

                        dest_arrival = max(
                            dest_arrival_stops,
                            key=lambda x: x['arrival_time'] or '00:00:00'
                        )

                        # Calculate transfer waiting time
                        waiting_minutes, day_offset, waiting_str, transfer_info, valid = \
                            self.calculate_transfer_waiting(
                                transfer_arrival['arrival_time'],
                                transfer_departure['departure_time']
                            )

                        if not valid:
                            continue

                        # Calculate total travel time
                        first_leg_minutes, _ = self.calculate_time_diff(
                            first_departure['departure_time'],
                            transfer_arrival['arrival_time'],
                            transfer_arrival['day_of_journey'] - first_departure['day_of_journey']
                        )

                        second_leg_minutes, _ = self.calculate_time_diff(
                            transfer_departure['departure_time'],
                            dest_arrival['arrival_time'],
                            dest_arrival['day_of_journey'] - transfer_departure['day_of_journey'] + day_offset
                        )

                        total_minutes = first_leg_minutes + waiting_minutes + second_leg_minutes
                        total_time_str = f"{total_minutes // 60}h {total_minutes % 60}m"

                        route = {
                            'first_train_no': first_train_no,
                            'second_train_no': second_train_no,
                            'first_train_name': f"Train {first_train_no}",
                            'second_train_name': f"Train {second_train_no}",
                            'source_station': source,
                            'transfer_station': transfer_station,
                            'destination_station': destination,
                            'departure_time': first_departure['departure_time'],
                            'arrival_time': dest_arrival['arrival_time'],
                            'transfer_waiting': waiting_str,
                            'transfer_info': transfer_info,
                            'total_travel_time': total_time_str,
                            'total_travel_minutes': total_minutes,
                            'transfers': 1,
                            'route_type': 'single_transfer'
                        }
                        routes.append(route)

        except Exception as e:
            logger.error(f"Error finding single transfer routes: {e}")

        return routes

    def find_routes(
        self,
        source: str,
        destination: str,
        date: datetime.date,
        train_schedule_data: List[Dict[str, Any]],
        train_running_days: Dict[int, Dict[str, bool]],
        stations_data: List[Dict[str, Any]],
        max_transfers: int = 1
    ) -> Dict[str, Any]:
        """Main route finding method with defined inputs and outputs"""

        result = {
            'source': source,
            'destination': destination,
            'date': date.isoformat(),
            'direct_routes': [],
            'transfer_routes': [],
            'total_routes': 0,
            'search_completed': False,
            'error': None
        }

        try:
            # Find direct routes
            direct_routes = self.find_direct_routes(
                source, destination, date,
                train_schedule_data, train_running_days
            )
            result['direct_routes'] = direct_routes

            # Find transfer routes if requested
            if max_transfers >= 1:
                transfer_routes = self.find_single_transfer_routes(
                    source, destination, date,
                    train_schedule_data, train_running_days,
                    stations_data, max_transfers
                )
                result['transfer_routes'] = transfer_routes

            result['total_routes'] = len(direct_routes) + len(transfer_routes)
            result['search_completed'] = True

        except Exception as e:
            logger.error(f"Error in route finding: {e}")
            result['error'] = str(e)

        return result