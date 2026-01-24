"""
RAPPID Train API Integration Module
Provides real-time validation of train routes using RAPPID API
https://rappid.in/apis/train.php?train_no=XXXX

Features:
- Real-time train schedule data
- Live seat availability
- Fare information
- Train status and delays
- Platform information
- Coach composition
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from functools import lru_cache
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAPPIDAPIClient:
    """RAPPID Train API Client for real-time train data"""
    
    BASE_URL = "https://rappid.in/apis/train.php"
    CACHE_DURATION = 300  # 5 minutes
    
    def __init__(self, timeout: int = 10, retry_attempts: int = 3):
        """
        Initialize RAPPID API Client
        
        Args:
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
        """
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.cache = {}
        self.cache_timestamps = {}
        
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid"""
        if key not in self.cache_timestamps:
            return False
        return (datetime.now() - self.cache_timestamps[key]).total_seconds() < self.CACHE_DURATION
    
    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """Get data from cache if valid"""
        if self._is_cache_valid(key):
            logger.info(f"✓ Cache hit for {key}")
            return self.cache[key]
        return None
    
    def _save_to_cache(self, key: str, data: Dict) -> None:
        """Save data to cache"""
        self.cache[key] = data
        self.cache_timestamps[key] = datetime.now()
    
    def _make_request(self, train_no: str) -> Optional[Dict]:
        """
        Make request to RAPPID API with retry logic
        
        Args:
            train_no: Train number to fetch data for
            
        Returns:
            API response as dictionary or None if failed
        """
        params = {'train_no': train_no}
        
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"Fetching data for train {train_no} (attempt {attempt + 1}/{self.retry_attempts})")
                response = requests.get(
                    self.BASE_URL,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"✓ Successfully fetched data for train {train_no}")
                return data
                
            except requests.exceptions.Timeout:
                logger.warning(f"⏱️ Timeout for train {train_no} (attempt {attempt + 1})")
            except requests.exceptions.ConnectionError:
                logger.warning(f"🔌 Connection error for train {train_no} (attempt {attempt + 1})")
            except requests.exceptions.HTTPError as e:
                logger.warning(f"HTTP error for train {train_no}: {e}")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response for train {train_no}")
                return None
            except Exception as e:
                logger.error(f"Error fetching train {train_no}: {e}")
            
            if attempt < self.retry_attempts - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def get_train_data(self, train_no: str, use_cache: bool = True) -> Optional[Dict]:
        """
        Get comprehensive train data from RAPPID API
        
        Args:
            train_no: Train number
            use_cache: Whether to use cached data if available
            
        Returns:
            Dictionary with train information or None
        """
        cache_key = f"train_{train_no}"
        
        # Check cache first
        if use_cache:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
        
        # Fetch from API
        data = self._make_request(train_no)
        
        if data:
            self._save_to_cache(cache_key, data)
            return data
        
        return None
    
    def get_train_schedule(self, train_no: str) -> Optional[Dict]:
        """Get detailed train schedule"""
        try:
            data = self.get_train_data(train_no)
            if not data:
                logger.warning(f"No data received for train {train_no}")
                return None
            
            # RAPPID API returns: {success, train_name, message, updated_time, data}
            return {
                'train_no': train_no,
                'train_name': data.get('train_name', 'N/A'),
                'source_station': 'N/A',
                'destination_station': 'N/A',
                'route': data.get('data', []),
                'total_stations': len(data.get('data', [])),
                'journey_days': [],
                'last_updated': data.get('updated_time', 'N/A'),
                'success': data.get('success', False)
            }
        except Exception as e:
            logger.error(f"Error getting schedule for train {train_no}: {e}", exc_info=True)
        return None
    
    def get_seat_availability(self, train_no: str) -> Optional[Dict]:
        """Get seat availability information"""
        try:
            data = self.get_train_data(train_no)
            if not data:
                return None
            
            return {
                'train_no': train_no,
                'seat_info': {},
                'availability_data': {},
                'message': 'Seat data not available from RAPPID API',
                'last_updated': data.get('updated_time', 'N/A'),
                'note': 'Use /api/train-data for complete train information'
            }
        except Exception as e:
            logger.error(f"Error getting seat availability for train {train_no}: {e}")
        return None
    
    def get_fare_information(self, train_no: str) -> Optional[Dict]:
        """Get fare details for the train"""
        try:
            data = self.get_train_data(train_no)
            if not data:
                return None
            
            return {
                'train_no': train_no,
                'fares': {},
                'fare_information': {},
                'currency': 'INR',
                'message': 'Fare data not available from RAPPID API',
                'last_updated': data.get('updated_time', 'N/A'),
                'note': 'Use /api/train-data for complete train information'
            }
        except Exception as e:
            logger.error(f"Error getting fare for train {train_no}: {e}")
        return None
    
    def get_train_status(self, train_no: str) -> Optional[Dict]:
        """Get current train status and delays"""
        try:
            data = self.get_train_data(train_no)
            if not data:
                return None
            
            # Extract status info from route data
            route_data = data.get('data', [])
            
            # Find current station
            current_station = None
            for station in route_data:
                if station.get('is_current_station'):
                    current_station = station
                    break
            
            return {
                'train_no': train_no,
                'status': 'Running',
                'train_name': data.get('train_name', 'N/A'),
                'running_status': current_station or {},
                'delays': {},
                'current_station': current_station.get('station_name') if current_station else 'N/A',
                'platform_info': current_station.get('platform', 'N/A') if current_station else {},
                'last_updated': data.get('updated_time', 'N/A')
            }
        except Exception as e:
            logger.error(f"Error getting status for train {train_no}: {e}")
        return None


class RAPPIDRouteValidator:
    """Validates and enriches routes using RAPPID API data"""
    
    def __init__(self, api_client: Optional[RAPPIDAPIClient] = None):
        """
        Initialize route validator
        
        Args:
            api_client: RAPPIDAPIClient instance (creates new if not provided)
        """
        self.api_client = api_client or RAPPIDAPIClient()
        self.validation_cache = {}
    
    def validate_segment(self, segment: Dict) -> Dict:
        """
        Validate a single route segment using RAPPID API
        
        Args:
            segment: Route segment with train info {train_no, from, to, ...}
            
        Returns:
            Enriched segment with validation data
        """
        train_no = segment.get('train_no', '')
        if not train_no:
            return {**segment, 'validation_status': 'INVALID', 'error': 'Missing train number'}
        
        # Check validation cache
        cache_key = f"segment_{train_no}_{segment.get('from')}_{segment.get('to')}"
        if cache_key in self.validation_cache:
            return self.validation_cache[cache_key]
        
        # Fetch data from RAPPID API
        logger.info(f"🚆 Validating segment: {train_no} ({segment.get('from')} → {segment.get('to')})")
        
        train_data = self.api_client.get_train_data(train_no, use_cache=True)
        
        validated_segment = segment.copy()
        validated_segment['rappid_validation'] = {}
        
        if not train_data:
            validated_segment['validation_status'] = 'DATA_UNAVAILABLE'
            validated_segment['error'] = f'Could not fetch RAPPID data for train {train_no}'
            self.validation_cache[cache_key] = validated_segment
            return validated_segment
        
        try:
            response = train_data.get('response', {})
            
            # Validate train existence and basic info
            validated_segment['validation_status'] = 'VALID'
            validated_segment['rappid_validation']['train_name'] = response.get('train_name', '')
            validated_segment['rappid_validation']['source'] = response.get('source_station_code', '')
            validated_segment['rappid_validation']['destination'] = response.get('destination_station_code', '')
            
            # Get schedule information
            route = response.get('route', [])
            validated_segment['rappid_validation']['route_stations'] = len(route)
            validated_segment['rappid_validation']['full_route'] = route
            
            # Extract from and to station indices
            from_station = segment.get('from')
            to_station = segment.get('to')
            
            segment_route = self._extract_segment_route(route, from_station, to_station)
            if segment_route:
                validated_segment['rappid_validation']['segment_route'] = segment_route
                validated_segment['rappid_validation']['segment_distance'] = segment_route.get('distance', 0)
                validated_segment['rappid_validation']['segment_duration'] = segment_route.get('duration', '')
            else:
                validated_segment['validation_status'] = 'PARTIAL'
                validated_segment['rappid_validation']['warning'] = f'Could not extract segment {from_station}-{to_station}'
            
            # Get seat availability
            seat_availability = response.get('seat_info', {})
            if seat_availability:
                validated_segment['rappid_validation']['seat_availability'] = {
                    'available': seat_availability.get('available', 0),
                    'classes': seat_availability.get('classes', {}),
                    'last_updated': datetime.now().isoformat()
                }
            
            # Get fare information
            fares = response.get('fares', {})
            if fares:
                validated_segment['rappid_validation']['fare'] = {
                    'base_fare': fares.get('base_fare', 0),
                    'total_fare': fares.get('total_fare', 0),
                    'classes': fares.get('classes', {}),
                    'currency': 'INR'
                }
            
            # Get train status
            status = response.get('status', 'Unknown')
            validated_segment['rappid_validation']['train_status'] = {
                'current_status': status,
                'running_on_time': status == 'On Time',
                'delays': response.get('delays', {}),
                'platform': response.get('platform_info', {})
            }
            
            # Get coach composition
            coaches = response.get('coaches', [])
            if coaches:
                validated_segment['rappid_validation']['coaches'] = {
                    'total_coaches': len(coaches),
                    'coach_types': self._analyze_coaches(coaches),
                    'coach_details': coaches[:5]  # First 5 coaches
                }
            
            # Get journey days
            journey_days = response.get('journey_days', [])
            validated_segment['rappid_validation']['journey_days'] = journey_days
            
            # Overall validation score
            validation_score = self._calculate_validation_score(validated_segment['rappid_validation'])
            validated_segment['rappid_validation']['validation_score'] = validation_score
            
        except Exception as e:
            logger.error(f"Error validating segment {train_no}: {e}")
            validated_segment['validation_status'] = 'ERROR'
            validated_segment['error'] = str(e)
        
        self.validation_cache[cache_key] = validated_segment
        return validated_segment
    
    def validate_route(self, route: Dict, travel_date: Optional[str] = None) -> Dict:
        """
        Validate entire route using RAPPID API
        
        Args:
            route: Route dictionary with segments
            travel_date: Travel date in DD-MM-YYYY format
            
        Returns:
            Enriched route with validation data
        """
        validated_route = route.copy()
        validated_route['rappid_validation'] = {
            'segments': [],
            'summary': {},
            'valid': True,
            'errors': [],
            'warnings': [],
            'travel_date': travel_date or datetime.now().strftime('%d-%m-%Y'),
            'validation_timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"🔄 Validating route: {route.get('source')} → {route.get('destination')}")
        
        # Validate each segment
        segments = route.get('segments', [])
        for idx, segment in enumerate(segments, 1):
            logger.info(f"  Validating segment {idx}/{len(segments)}")
            validated_segment = self.validate_segment(segment)
            validated_route['rappid_validation']['segments'].append(validated_segment)
            
            # Check for errors
            if validated_segment.get('validation_status') == 'ERROR':
                validated_route['rappid_validation']['errors'].append(
                    f"Segment {idx} ({segment.get('train_no')}): {validated_segment.get('error')}"
                )
                validated_route['rappid_validation']['valid'] = False
            elif validated_segment.get('validation_status') == 'PARTIAL':
                validated_route['rappid_validation']['warnings'].append(
                    f"Segment {idx} ({segment.get('train_no')}): {validated_segment.get('rappid_validation', {}).get('warning')}"
                )
        
        # Calculate route summary
        self._calculate_route_summary(validated_route)
        
        return validated_route
    
    def validate_routes_batch(self, routes: List[Dict], travel_date: Optional[str] = None) -> Dict:
        """
        Validate multiple routes efficiently
        
        Args:
            routes: List of routes to validate
            travel_date: Travel date in DD-MM-YYYY format
            
        Returns:
            Dictionary with validated routes and summary
        """
        logger.info(f"🚀 Validating batch of {len(routes)} routes")
        
        validated_routes = []
        for idx, route in enumerate(routes, 1):
            logger.info(f"Processing route {idx}/{len(routes)}")
            validated_route = self.validate_route(route, travel_date)
            validated_routes.append(validated_route)
        
        return {
            'validated_routes': validated_routes,
            'total_routes': len(validated_routes),
            'valid_routes': sum(1 for r in validated_routes if r['rappid_validation']['valid']),
            'batch_timestamp': datetime.now().isoformat(),
            'travel_date': travel_date or datetime.now().strftime('%d-%m-%Y')
        }
    
    @staticmethod
    def _extract_segment_route(full_route: List[Dict], from_station: str, to_station: str) -> Optional[Dict]:
        """Extract specific segment from full route"""
        try:
            from_idx = None
            to_idx = None
            
            for idx, station in enumerate(full_route):
                station_code = station.get('station_code', '')
                if station_code == from_station:
                    from_idx = idx
                elif station_code == to_station:
                    to_idx = idx
            
            if from_idx is not None and to_idx is not None and from_idx < to_idx:
                segment = full_route[from_idx:to_idx + 1]
                
                # Calculate distance and duration
                distance = 0
                duration_minutes = 0
                
                for i in range(len(segment) - 1):
                    current = segment[i]
                    next_station = segment[i + 1]
                    distance += next_station.get('distance_from_source', 0) - current.get('distance_from_source', 0)
                
                # Calculate duration
                arrival_time = segment[-1].get('arrival_time', '')
                departure_time = segment[0].get('departure_time', '')
                
                return {
                    'stations': [s.get('station_code', '') for s in segment],
                    'distance': distance,
                    'duration': f"{len(segment) - 1} stops",
                    'arrival_time': arrival_time,
                    'departure_time': departure_time,
                    'station_count': len(segment)
                }
        except Exception as e:
            logger.error(f"Error extracting segment route: {e}")
        
        return None
    
    @staticmethod
    def _analyze_coaches(coaches: List[Dict]) -> Dict:
        """Analyze coach composition"""
        coach_types = {}
        for coach in coaches:
            coach_type = coach.get('type', 'Unknown')
            coach_types[coach_type] = coach_types.get(coach_type, 0) + 1
        return coach_types
    
    @staticmethod
    def _calculate_validation_score(validation_data: Dict) -> float:
        """Calculate validation score (0-100)"""
        score = 100.0
        
        # Deduct points for missing data
        if not validation_data.get('seat_availability'):
            score -= 10
        if not validation_data.get('fare'):
            score -= 10
        if validation_data.get('train_status', {}).get('delays'):
            score -= 20
        if not validation_data.get('coaches'):
            score -= 5
        
        return max(0, min(100, score))
    
    @staticmethod
    def _calculate_route_summary(route: Dict) -> None:
        """Calculate summary statistics for the route"""
        validation = route['rappid_validation']
        segments = validation['segments']
        
        if not segments:
            validation['summary'] = {'total_segments': 0}
            return
        
        total_distance = 0
        total_fare = 0
        seat_count = 0
        available_seats = 0
        all_on_time = True
        
        for segment in segments:
            rappid_data = segment.get('rappid_validation', {})
            
            if rappid_data.get('segment_distance'):
                total_distance += rappid_data['segment_distance']
            
            if rappid_data.get('fare', {}).get('total_fare'):
                total_fare += rappid_data['fare']['total_fare']
            
            seats = rappid_data.get('seat_availability', {})
            if seats.get('available'):
                available_seats += seats['available']
            
            if not rappid_data.get('train_status', {}).get('running_on_time'):
                all_on_time = False
        
        validation['summary'] = {
            'total_segments': len(segments),
            'total_distance': total_distance,
            'total_fare': total_fare,
            'total_available_seats': available_seats,
            'all_trains_on_time': all_on_time,
            'average_validation_score': sum(
                s.get('rappid_validation', {}).get('validation_score', 50) for s in segments
            ) / len(segments) if segments else 0
        }


# Convenience functions for easy integration

def validate_single_train(train_no: str) -> Dict:
    """Quick validation of a single train"""
    client = RAPPIDAPIClient()
    data = client.get_train_data(train_no)
    
    if not data:
        return {'error': f'Could not fetch data for train {train_no}'}
    
    return {
        'train_no': train_no,
        'schedule': client.get_train_schedule(train_no),
        'seat_availability': client.get_seat_availability(train_no),
        'fares': client.get_fare_information(train_no),
        'status': client.get_train_status(train_no),
        'raw_data': data
    }


def validate_routes_quick(routes: List[Dict], travel_date: Optional[str] = None) -> Dict:
    """Quick validation of multiple routes"""
    validator = RAPPIDRouteValidator()
    return validator.validate_routes_batch(routes, travel_date)
