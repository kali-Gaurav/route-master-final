import os
import requests
import logging
import sys
import json
import time
import random # For jitter in rate limit backoff
from copy import deepcopy
from datetime import datetime
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from pybreaker import CircuitBreaker, CircuitBreakerError, CircuitBreakerListener
from pydantic import BaseModel, Field, ValidationError

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Custom Exception Classes for IRCTC API ---
class IrctcApiError(Exception):
    """Base exception for IRCTC API errors."""
    pass

class IrctcUnauthorizedError(IrctcApiError):
    """Raised when IRCTC API returns 401 Unauthorized."""
    pass

class IrctcRateLimitExceededError(IrctcApiError):
    """Raised when IRCTC API returns 429 Too Many Requests."""
    pass

class IrctcNotFoundError(IrctcApiError):
    """Raised when IRCTC API returns 404 Not Found."""
    pass

class IrctcServerError(IrctcApiError):
    """Raised when IRCTC API returns 5xx Server Error."""
    pass

class IrctcConnectionError(IrctcApiError):
    """Raised for network connection issues to IRCTC API."""
    pass

class IrctcTimeoutError(IrctcApiError):
    """Raised when IRCTC API request times out."""
    pass

class IrctcInvalidResponseError(IrctcApiError):
    """Raised when IRCTC API returns an unexpected or malformed response."""
    pass
# --- End Custom Exception Classes ---


# --- Pydantic Models for IRCTC API Responses ---
# These models are based on common API patterns and might need adjustment
# based on the actual IRCTC RapidAPI documentation.

class LiveStationTrain(BaseModel):
    train_no: str = Field(..., alias="trainNo")
    train_name: str = Field(..., alias="trainName")
    current_status: str = Field(..., alias="currentStatus")
    # Add other fields as per API response

class LiveStationData(BaseModel):
    station_code: str = Field(..., alias="stationCode")
    timestamp: datetime
    trains: List[LiveStationTrain] = Field(default_factory=list)
    # Add other fields as per API response


class SeatAvailabilityClass(BaseModel):
    code: str
    status: str
    seats: Optional[int] = None
    wl_no: Optional[int] = None

class SeatAvailabilityData(BaseModel):
    train_no: str = Field(..., alias="trainNo")
    source_station: str = Field(..., alias="source")
    destination_station: str = Field(..., alias="destination")
    journey_date: str = Field(..., alias="date")
    classes: List[SeatAvailabilityClass] = Field(default_factory=list)
    # Add other fields as per API response


class TrainFareDetail(BaseModel):
    class_code: str = Field(..., alias="classCode")
    price: float
    # Add other fields as per API response

class TrainFareData(BaseModel):
    train_no: str = Field(..., alias="trainNo")
    source_station: str = Field(..., alias="source")
    destination_station: str = Field(..., alias="destination")
    journey_date: str = Field(..., alias="date")
    fares: List[TrainFareDetail] = Field(default_factory=list)
    total_fare: Optional[float] = None
    # Add other fields as per API response

# Generic wrapper for API responses that often have a 'data' key
class ApiResponse(BaseModel):
    data: Any
    # Add other common fields like 'status', 'message' if present
# --- End Pydantic Models ---


# Load environment variables from .env file
load_dotenv()

# IRCTC RapidAPI Configuration - loaded from environment
_IRCTC_API_KEY = os.getenv("IRCTC_API_KEY")
if not _IRCTC_API_KEY:
    logger.critical("IRCTC_API_KEY not found in environment variables. Please set it in .env or your deployment environment.")
    sys.exit(1) # Exit if API key is not found

IRCTC_API_KEY = _IRCTC_API_KEY
IRCTC_API_HOST = os.getenv("IRCTC_API_HOST", "irctc1.p.rapidapi.com") # Make host configurable too
IRCTC_BASE_URL = os.getenv("IRCTC_BASE_URL", "https://irctc1.p.rapidapi.com/api/v3") # Make base URL configurable too
IRCTC_API_TIMEOUT_SECONDS = int(os.getenv("IRCTC_API_TIMEOUT_SECONDS", 10)) # Make timeout configurable too
MAX_IRCTC_RATE_LIMIT_RETRIES = int(os.getenv("MAX_IRCTC_RATE_LIMIT_RETRIES", 3)) # Max retries for 429 errors


# --- Circuit Breaker Setup ---
class IrctcCircuitListener(CircuitBreakerListener):
    """Listener for IRCTC circuit breaker state changes."""
    def state_change(self, breaker, old_state, new_state):
        logger.warning(f"CIRCUIT BREAKER: IRCTC API circuit changed from {old_state.name} to {new_state.name}")
    
    def failure(self, breaker, exc):
        logger.info(f"CIRCUIT BREAKER: IRCTC API call failed with {type(exc).__name__}. Current failures: {breaker.fail_counter}")

    def success(self, breaker):
        logger.info(f"CIRCUIT BREAKER: IRCTC API call successful. Resetting failure counter.")

irctc_breaker = CircuitBreaker(
    fail_max=5,                # Max failures before opening the circuit
    reset_timeout=60,          # Time (seconds) to wait before attempting to close the circuit
    exclude=[IrctcNotFoundError, IrctcUnauthorizedError], # Don't open circuit for these expected errors
    listeners=[IrctcCircuitListener()]
)
# --- End Circuit Breaker Setup ---

# --- Configuration Constants ---
USER_AGENT = "RouteMaster/1.0 (+https://example.com/routemaster-info)" # Replace with actual app info


def get_irctc_headers():
    """Return headers for IRCTC API requests"""
    headers = {
        'x-rapidapi-host': IRCTC_API_HOST,
        'x-rapidapi-key': IRCTC_API_KEY
    }
    headers['User-Agent'] = USER_AGENT # Add User-Agent
    return headers

def _handle_irctc_response(response: requests.Response, context_msg: str, model: Optional[BaseModel] = None):
    """
    Helper to handle common IRCTC API responses, raise custom exceptions, and validate with Pydantic.
    Logs full request and response details at DEBUG level.
    """
    # Log request details
    if logger.isEnabledFor(logging.DEBUG):
        masked_headers = {k: v if k.lower() != 'x-rapidapi-key' else '***MASKED***' for k, v in response.request.headers.items()}
        logger.debug(f"IRCTC Request: {response.request.method} {response.request.url}")
        logger.debug(f"IRCTC Request Headers: {masked_headers}")
        if response.request.body:
            logger.debug(f"IRCTC Request Body: {response.request.body}")

    # Log response details
    logger.debug(f"IRCTC Response Status: {response.status_code}")
    logger.debug(f"IRCTC Response Headers: {response.headers}")
    logger.debug(f"IRCTC Response Text: {response.text}")

    try:
        response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 401:
            raise IrctcUnauthorizedError(f"{context_msg}: Unauthorized - Check API key. {e}")
        elif status_code == 404:
            raise IrctcNotFoundError(f"{context_msg}: Resource not found. {e}")
        elif status_code == 429:
            raise IrctcRateLimitExceededError(f"{context_msg}: Rate limit exceeded. {e}")
        elif 400 <= status_code < 500:
            raise IrctcApiError(f"{context_msg}: Client error {status_code}. {e}")
        elif 500 <= status_code < 600:
            raise IrctcServerError(f"{context_msg}: Server error {status_code}. {e}")
        else:
            raise IrctcApiError(f"{context_msg}: Unexpected HTTP error {status_code}. {e}")
    except requests.exceptions.Timeout as e:
        raise IrctcTimeoutError(f"{context_msg}: Request timed out. {e}")
    except requests.exceptions.ConnectionError as e:
        raise IrctcConnectionError(f"{context_msg}: Network connection error. {e}")
    except requests.exceptions.RequestException as e:
        raise IrctcApiError(f"{context_msg}: An unexpected request error occurred. {e}")
    
    try:
        json_data = response.json()
        if model:
            # Assume the API response has a 'data' field that holds the actual model data
            # Adjust this if the API returns the model directly at the root
            validated_data = model.model_validate(json_data.get('data', json_data))
            return validated_data
        return json_data
    except json.JSONDecodeError as e:
        raise IrctcInvalidResponseError(f"{context_msg}: Invalid JSON response from API. {e}. Response: {response.text[:200]}")
    except ValidationError as e:
        raise IrctcInvalidResponseError(f"{context_msg}: Pydantic validation failed for API response. {e}. Response: {response.text[:200]}")

@irctc_breaker
def _irctc_api_call(method: str, url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None, context_msg: str = "IRCTC API call", model: Optional[BaseModel] = None, max_retries: int = MAX_IRCTC_RATE_LIMIT_RETRIES):
    """
    Generalized helper to make IRCTC API calls with rate limit handling, retries, and Pydantic validation.
    """
    for attempt in range(max_retries + 1):
        try:
            response = requests.request(
                method,
                url,
                params=params,
                headers=headers,
                timeout=IRCTC_API_TIMEOUT_SECONDS
            )
            return _handle_irctc_response(response, context_msg, model)
        except IrctcRateLimitExceededError as e:
            if attempt < max_retries:
                retry_after_header = response.headers.get("Retry-After")
                try:
                    # Retry-After can be a date or a number of seconds
                    wait_time = int(retry_after_header) if retry_after_header and retry_after_header.isdigit() else 0
                    if wait_time == 0: # Fallback to exponential backoff with jitter if header not numeric or missing
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                except (TypeError, ValueError):
                    wait_time = (2 ** attempt) + random.uniform(0, 1) # Fallback if Retry-After is a date string

                logger.warning(f"Rate limit hit for {context_msg}. Retrying in {wait_time:.2f} seconds (attempt {attempt + 1}/{max_retries}).")
                time.sleep(wait_time)
            else:
                logger.error(f"Max retries ({max_retries}) exceeded for rate limit on {context_msg}.")
                raise # Re-raise if max retries exceeded
        except IrctcApiError:
            raise # Re-raise other API errors directly
        except CircuitBreakerError:
            raise # Re-raise CircuitBreakerError
        except Exception as e:
            logger.error(f"❌ Unexpected error in _irctc_api_call for {context_msg}: {e}", exc_info=True)
            raise IrctcApiError(f"Unexpected error during API call for {context_msg}: {e}")
    
    return None # Should ideally not be reached, exceptions should be raised


def _normalize_irctc_response(payload: Any) -> Dict[str, Any]:
    if payload is None:
        return {}
    for attr in ("model_dump", "dict"):
        if hasattr(payload, attr):
            try:
                data = getattr(payload, attr)()
                if isinstance(data, dict):
                    return data
            except Exception:
                continue
    if isinstance(payload, dict):
        return payload
    return {}


def _extract_irctc_seat_summary(payload: Dict[str, Any], travel_class: str) -> Dict[str, Any]:
    summary = {
        'status': payload.get('status') or payload.get('SeatAvailability') or 'UNKNOWN',
        'seats': None,
        'class': travel_class,
        'raw_payload': payload,
    }
    class_target = travel_class.upper() if travel_class else ''
    classes = payload.get('classes') or payload.get('seat_classes') or []
    if isinstance(classes, dict):
        classes = [classes]
    for cls in classes:
        code = (cls.get('code') or cls.get('class_code') or '').upper()
        if class_target and code != class_target:
            continue
        summary['status'] = cls.get('status') or cls.get('seat_status') or summary['status']
        seats = cls.get('seats') or cls.get('wl_no')
        if isinstance(seats, (int, float)):
            summary['seats'] = int(seats)
        else:
            try:
                summary['seats'] = int(seats)
            except Exception:
                summary['seats'] = summary['seats']
        break
    availability_list = payload.get('availability')
    if availability_list and isinstance(availability_list, list) and availability_list:
        first = availability_list[0]
        summary['status'] = first.get('status') or summary['status']
    return summary


def _extract_irctc_fare_summary(payload: Dict[str, Any], travel_class: str) -> Dict[str, Any]:
    summary = {
        'amount': 0.0,
        'currency': payload.get('currency', 'INR'),
        'raw_payload': payload,
    }
    class_target = travel_class.upper() if travel_class else ''
    fares = payload.get('fares') or payload.get('fare_details') or []
    if isinstance(fares, dict):
        fares = [fares]
    for fare in fares:
        code = (fare.get('class_code') or fare.get('code') or '').upper()
        if class_target and code != class_target:
            continue
        amount = fare.get('price') or fare.get('total_fare') or fare.get('fare')
        try:
            summary['amount'] = float(amount)
        except (TypeError, ValueError):
            summary['amount'] = 0.0
        summary['currency'] = fare.get('currency', summary['currency'])
        return summary
    total = payload.get('total_fare') or payload.get('fare') or 0.0
    try:
        summary['amount'] = float(total)
    except (TypeError, ValueError):
        summary['amount'] = 0.0
    return summary


def validate_route_with_irctc(route: Dict[str, Any], travel_date: Optional[str] = None, travel_class: str = 'SL') -> Dict[str, Any]:
    travel_date = travel_date or datetime.now().strftime('%d-%m-%Y')
    validated_route = deepcopy(route)
    validation_payload = {
        'travel_date': travel_date,
        'validation_timestamp': datetime.utcnow().isoformat(),
        'validation_sources': ['IRCTC API'],
        'segments': [],
        'valid': True,
        'errors': [],
        'warnings': [],
    }

    for idx, segment in enumerate(validated_route.get('segments', []), start=1):
        train_no = str(segment.get('train_no') or segment.get('trainNumber') or '').strip()
        from_station = segment.get('from')
        to_station = segment.get('to')

        if not train_no or not from_station or not to_station:
            validation_payload['valid'] = False
            validation_payload['errors'].append(f"Segment {idx}: missing identifiers")
            continue

        seat_payload = _normalize_irctc_response(
            get_seat_availability(train_no, from_station, to_station, travel_date)
        )
        fare_payload = _normalize_irctc_response(
            get_train_fare(train_no, from_station, to_station, travel_date)
        )

        seat_summary = _extract_irctc_seat_summary(seat_payload, travel_class)
        fare_summary = _extract_irctc_fare_summary(fare_payload, travel_class)

        status = seat_summary.get('status', 'UNKNOWN').upper()
        if 'AVAILABLE' not in status:
            validation_payload['valid'] = False
            validation_payload['warnings'].append(
                f"Segment {idx} ({train_no}): seats not listed as AVAILABLE"
            )

        segment_validation = {
            'train_no': train_no,
            'from': from_station,
            'to': to_station,
            'seat_status': seat_summary.get('status'),
            'seat_details': seat_summary,
            'fare_details': fare_summary,
            'validation_status': 'VALID' if 'AVAILABLE' in status else 'CHECK',
        }
        validation_payload['segments'].append(segment_validation)

    validation_payload['overall_valid'] = validation_payload['valid'] and not validation_payload['errors']
    validated_route['irctc_validation'] = validation_payload
    return validated_route

@irctc_breaker
def get_live_station_data(station_code, hours=1) -> Optional[LiveStationData]:
    """
    Fetch live station data from IRCTC API
    Returns: LiveStationData model or None
    """
    context_msg = f"live station data for {station_code}"
    try:
        url = f"{IRCTC_BASE_URL}/getLiveStation"
        params = {
            'hours': hours,
            'stationCode': station_code
        }
        headers = get_irctc_headers()
        
        data = _irctc_api_call(
            method="GET",
            url=url,
            params=params,
            headers=headers,
            context_msg=context_msg,
            model=LiveStationData
        )
        logger.info(f"✓ Live station data retrieved for {station_code}")
        return data
    except IrctcApiError as e:
        logger.warning(f"⚠️ {e}")
        return None
    except CircuitBreakerError:
        logger.warning(f"⚠️ CIRCUIT BREAKER OPEN: IRCTC API calls for {context_msg} are temporarily disabled.")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error in get_live_station_data for {station_code}: {e}", exc_info=True)
        return None

@irctc_breaker
def get_seat_availability(train_number, source_station, destination_station, date) -> Optional[SeatAvailabilityData]:
    """
    Fetch seat availability from IRCTC API
    Returns: SeatAvailabilityData model or None
    """
    context_msg = f"seat availability for {train_number} from {source_station} to {destination_station} on {date}"
    try:
        url = f"{IRCTC_BASE_URL}/getSeatAvailability"
        params = {
            'trainNo': train_number,
            'source': source_station,
            'destination': destination_station,
            'date': date
        }
        headers = get_irctc_headers()
        
        data = _irctc_api_call(
            method="GET",
            url=url,
            params=params,
            headers=headers,
            context_msg=context_msg,
            model=SeatAvailabilityData
        )
        logger.info(f"✓ Seat availability retrieved for train {train_number} from {source_station} to {destination_station} on {date}")
        return data
    except IrctcApiError as e:
        logger.warning(f"⚠️ {e}")
        return None
    except CircuitBreakerError:
        logger.warning(f"⚠️ CIRCUIT BREAKER OPEN: IRCTC API calls for {context_msg} are temporarily disabled.")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error in get_seat_availability for {train_number}: {e}", exc_info=True)
        return None

@irctc_breaker
def get_train_fare(train_number, source_station, destination_station, date) -> Optional[TrainFareData]:
    """
    Fetch train fare from IRCTC API
    Returns: TrainFareData model or None
    """
    context_msg = f"train fare for {train_number} from {source_station} to {destination_station} on {date}"
    try:
        url = f"{IRCTC_BASE_URL}/getFare"
        params = {
            'trainNo': train_number,
            'source': source_station,
            'destination': destination_station,
            'date': date
        }
        headers = get_irctc_headers()
        
        data = _irctc_api_call(
            method="GET",
            url=url,
            params=params,
            headers=headers,
            context_msg=context_msg,
            model=TrainFareData
        )
        logger.info(f"✓ Fare retrieved for train {train_number} from {source_station} to {destination_station} on {date}")
        return data
    except IrctcApiError as e:
        logger.warning(f"⚠️ {e}")
        return None
    except CircuitBreakerError:
        logger.warning(f"⚠️ CIRCUIT BREAKER OPEN: IRCTC API calls for {context_msg} are temporarily disabled.")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error in get_train_fare for {train_number}: {e}", exc_info=True)
        return None