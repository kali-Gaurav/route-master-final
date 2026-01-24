import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

import requests

from rappid_optimized import OptimizedRAPPIDClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

IRCTC_API_KEY = "e0adaea886msh3fb9b9456cad9ccp17a317jsna7fe7b2fe0b6"
IRCTC_API_HOST = "irctc1.p.rapidapi.com"
IRCTC_BASE_URL = "https://irctc1.p.rapidapi.com/api/v3"


class IRCTCClient:
    """Lightweight wrapper for the IRCTC RapidAPI endpoints we rely on."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()

    def _headers(self) -> Dict[str, str]:
        return {
            "x-rapidapi-host": IRCTC_API_HOST,
            "x-rapidapi-key": IRCTC_API_KEY,
        }

    def _request(self, endpoint: str, params: Dict[str, str]) -> Optional[Dict]:
        url = f"{IRCTC_BASE_URL}/{endpoint}"
        try:
            response = self.session.get(
                url,
                params=params,
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            logger.info("IRCTC %s success", endpoint)
            return payload
        except requests.RequestException as exc:
            logger.warning("IRCTC %s failed: %s", endpoint, exc)
        except ValueError:
            logger.warning("IRCTC %s returned invalid JSON", endpoint)
        return None

    def get_live_station_data(self, station: str, hours: int = 1) -> Optional[Dict]:
        return self._request("getLiveStation", {"station": station, "hours": str(hours)})

    def get_seat_availability(
        self,
        train_number: str,
        source: str,
        destination: str,
        date: str,
        seat_class: str = "SL",
    ) -> Optional[Dict]:
        params = {
            "trainNo": train_number,
            "source": source,
            "destination": destination,
            "date": date,
            "class": seat_class,
        }
        return self._request("getSeatAvailability", params)

    def get_train_fare(
        self,
        train_number: str,
        source: str,
        destination: str,
        date: str,
        seat_class: str = "SL",
    ) -> Optional[Dict]:
        params = {
            "trainNo": train_number,
            "source": source,
            "destination": destination,
            "date": date,
            "class": seat_class,
        }
        return self._request("getFare", params)


_irctc_client = IRCTCClient()


def get_live_station_data(station: str, hours: int = 1) -> Optional[Dict]:
    return _irctc_client.get_live_station_data(station, hours)


def get_seat_availability(
    train_number: str,
    source: str,
    destination: str,
    date: str,
    seat_class: str = "SL",
) -> Optional[Dict]:
    return _irctc_client.get_seat_availability(train_number, source, destination, date, seat_class)


def get_train_fare(
    train_number: str,
    source: str,
    destination: str,
    date: str,
    seat_class: str = "SL",
) -> Optional[Dict]:
    return _irctc_client.get_train_fare(train_number, source, destination, date, seat_class)


class LiveSegmentEnricher:
    """Enriches a segment with sleeper availability, fare, and RAPPID train data."""

    def __init__(self, seat_class: str = "SL") -> None:
        self.seat_class = seat_class
        self.rappid_client = OptimizedRAPPIDClient()
        self._cache: Dict[Tuple[str, str, str, str, str], Dict] = {}

    def enrich_segment(
        self,
        segment: Dict,
        travel_date: str,
        seat_class: Optional[str] = None,
    ) -> Dict:
        seat_class = seat_class or self.seat_class
        key = (
            segment.get("train_no", ""),
            segment.get("from", ""),
            segment.get("to", ""),
            travel_date,
            seat_class,
        )
        if key in self._cache:
            return self._cache[key]

        train_no = segment.get("train_no", "")
        source = segment.get("from", "")
        destination = segment.get("to", "")
        live_info: Dict = {}

        seat_payload = get_seat_availability(train_no, source, destination, travel_date, seat_class)
        live_info["seat_payload"] = seat_payload or {}
        live_info["seat_status"] = self._describe_seat(seat_payload)
        live_info["seat_class"] = seat_class

        fare_payload = get_train_fare(train_no, source, destination, travel_date, seat_class)
        live_info["fare_payload"] = fare_payload or {}
        live_info["fare_amount"] = self._extract_fare(fare_payload)
        live_info["fare_currency"] = self._extract_currency(fare_payload)

        train_payload = self.rappid_client.get_train_data(train_no, use_cache=True)
        live_info["rappid_payload"] = train_payload or {}
        if train_payload:
            live_info["train_status"] = self._extract_train_status(train_payload)
        else:
            live_info["train_status"] = {}

        validation_sources = ["IRCTC"]
        if train_payload:
            validation_sources.append("RAPPID")
        live_info["validation_sources"] = validation_sources
        live_info["fetched_at"] = datetime.now().isoformat()

        self._cache[key] = live_info
        return live_info

    def _describe_seat(self, payload: Optional[Dict]) -> str:
        if not payload:
            return "UNKNOWN"
        data = payload.get("data") or {}
        status = data.get("status") or data.get("SeatAvailability")
        if status:
            return status
        availability = data.get("availability")
        if isinstance(availability, list) and availability:
            return availability[0].get("status", "UNKNOWN")
        return "UNKNOWN"

    def _extract_fare(self, payload: Optional[Dict]) -> Optional[float]:
        if not payload:
            return None
        data = payload.get("data") or {}
        fare = data.get("fare") or data.get("total_fare")
        if fare is None:
            try:
                fare = float(data.get("total_fare", 0))
            except (TypeError, ValueError):
                fare = None
        return fare

    def _extract_currency(self, payload: Optional[Dict]) -> str:
        if not payload:
            return "INR"
        data = payload.get("data") or {}
        return data.get("currency", "INR")

    def _extract_train_status(self, payload: Dict) -> Dict:
        route = payload.get("data") or []
        current = next((station for station in route if station.get("is_current_station")), None)
        return {
            "current_station": current.get("station_name") if current else None,
            "delay": current.get("delay_minutes") if current else None,
            "platform": current.get("platform") if current else None,
        }
