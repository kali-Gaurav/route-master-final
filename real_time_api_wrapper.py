import logging
import aiohttp
from datetime import datetime
from typing import Any, Dict, Optional
from irctc_client import get_seat_availability, get_train_fare

logger = logging.getLogger(__name__)

def _normalize_payload(payload: Optional[Any]) -> Dict[str, Any]:
    if payload is None:
        return {}
    if hasattr(payload, "model_dump"):
        try:
            return payload.model_dump()
        except Exception:
            pass
    if hasattr(payload, "dict"):
        try:
            return payload.dict()
        except Exception:
            pass
    if isinstance(payload, dict):
        return payload
    return {}


def _coerce_to_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return datetime.now()

class ApiLiveFetcher:
    def __init__(self, rappid_client, aiohttp_session: aiohttp.ClientSession):
        self.rappid_client = rappid_client
        self.aiohttp_session = aiohttp_session

    async def fetch_segment_data(self, train_no: str, from_station_code: str, to_station_code: str, journey_date: datetime, travel_class: str = 'SL') -> dict:
        """Returns availability and fare data for a train segment, normalized for route planning."""
        journey_dt = _coerce_to_datetime(journey_date)
        logger.debug(
            "Fetching live data for %s from %s to %s on %s for class %s",
            train_no,
            from_station_code,
            to_station_code,
            journey_dt.strftime('%Y-%m-%d'),
            travel_class,
        )

        availability_string = "UNKNOWN"
        fare_value = 0.0
        seat_payload = {}
        fare_payload = {}

        def _extract_seat_status(payload: Dict[str, Any]) -> str:
            classes = payload.get('classes') or payload.get('seat_classes') or []
            status = payload.get('status')
            if isinstance(classes, list):
                for cls in classes:
                    code = (cls.get('code') or cls.get('class_code') or '').upper()
                    if travel_class.upper() and code == travel_class.upper():
                        return cls.get('status') or cls.get('seat_status') or 'UNKNOWN'
                    if not travel_class and cls.get('status'):
                        status = cls.get('status')
            if status:
                return status
            availability = payload.get('availability')
            if isinstance(availability, list) and availability:
                return availability[0].get('status', 'UNKNOWN')
            return 'UNKNOWN'

        def _extract_seat_count(payload: Dict[str, Any]) -> Optional[int]:
            if not payload:
                return None
            classes = payload.get('classes') or payload.get('seat_classes') or []
            for cls in classes:
                code = (cls.get('code') or cls.get('class_code') or '').upper()
                if travel_class.upper() and code == travel_class.upper():
                    seats = cls.get('seats')
                    if isinstance(seats, (int, float)):
                        return int(seats)
                    try:
                        return int(cls.get('wl_no', seats))
                    except Exception:
                        pass
            return None

        def _extract_fare_amount(payload: Dict[str, Any]) -> float:
            fares = payload.get('fares') or payload.get('fare_details') or []
            for fare_detail in fares:
                code = (fare_detail.get('class_code') or fare_detail.get('code') or '').upper()
                if travel_class.upper() and code == travel_class.upper():
                    return float(fare_detail.get('price') or fare_detail.get('total_fare') or 0.0)
            total_fare = payload.get('total_fare') or payload.get('fare') or 0.0
            try:
                return float(total_fare)
            except (TypeError, ValueError):
                return 0.0

        # Fetch seat availability
        raw_seat_payload = get_seat_availability(
            train_number=train_no,
            source_station=from_station_code,
            destination_station=to_station_code,
            date=journey_dt.strftime('%d-%m-%Y'),
        )
        seat_payload = _normalize_payload(raw_seat_payload)
        availability_string = _extract_seat_status(seat_payload)
        seat_count = _extract_seat_count(seat_payload)

        if availability_string == 'UNKNOWN':
            logger.warning(
                "IRCTC seat availability fallback UNKNOWN for %s (%s-%s)",
                train_no,
                from_station_code,
                to_station_code,
            )

        # Fetch fare information
        raw_fare_payload = get_train_fare(
            train_number=train_no,
            source_station=from_station_code,
            destination_station=to_station_code,
            date=journey_dt.strftime('%d-%m-%Y'),
        )
        fare_payload = _normalize_payload(raw_fare_payload)
        fare_value = _extract_fare_amount(fare_payload)

        if not fare_value:
            logger.warning(
                "IRCTC fare returned zero for %s (%s-%s)",
                train_no,
                from_station_code,
                to_station_code,
            )

        return {
            'availability': availability_string,
            'fare': fare_value,
            'seat_count': seat_count,
            'travel_class': travel_class,
            'seat_payload': seat_payload,
            'fare_payload': fare_payload,
        }
