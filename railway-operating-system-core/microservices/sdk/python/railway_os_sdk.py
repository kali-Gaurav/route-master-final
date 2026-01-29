# Railway Operating System - Python SDK
# A Python client library for the Railway Operating System microservices platform

import requests
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
import time
import logging

logger = logging.getLogger(__name__)

class RailwayOSClient:
    """
    Python SDK for Railway Operating System microservices platform.

    Provides a convenient interface for interacting with the Railway OS API,
    including route search, tenant management, and data access.
    """

    def __init__(self, api_key: str, tenant_id: str, base_url: str = "http://localhost:8000"):
        """
        Initialize the Railway OS client.

        Args:
            api_key: Your API key for authentication
            tenant_id: Your tenant ID
            base_url: Base URL of the API gateway (default: http://localhost:8000)
        """
        self.api_key = api_key
        self.tenant_id = tenant_id
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'X-Tenant-ID': tenant_id,
            'Content-Type': 'application/json'
        })

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                     params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make an HTTP request to the API."""
        url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, params=params)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, params=params)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            error_data = e.response.json() if e.response.content else {}
            raise RailwayOSException(f"API request failed: {e}", error_data)
        except requests.exceptions.RequestException as e:
            raise RailwayOSException(f"Request failed: {e}")

    def health_check(self, service: Optional[str] = None) -> Dict[str, Any]:
        """
        Check the health of services.

        Args:
            service: Specific service to check (optional)

        Returns:
            Health status information
        """
        endpoint = f"/health/{service}" if service else "/health"
        return self._make_request('GET', endpoint)

    # ============================================================================
    # TENANT MANAGEMENT
    # ============================================================================

    def create_tenant(self, name: str, domain: str, contact_email: str,
                     settings: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create a new tenant.

        Args:
            name: Tenant name
            domain: Tenant domain
            contact_email: Contact email
            settings: Optional tenant settings

        Returns:
            Created tenant information
        """
        data = {
            'name': name,
            'domain': domain,
            'contact_email': contact_email,
            'settings': settings or {}
        }
        return self._make_request('POST', '/api/v1/tenants', data)

    def get_tenant(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get tenant information.

        Args:
            tenant_id: Tenant ID (defaults to current tenant)

        Returns:
            Tenant information
        """
        tenant = tenant_id or self.tenant_id
        return self._make_request('GET', f'/api/v1/tenants/{tenant}')

    def update_tenant(self, tenant_id: Optional[str] = None,
                     updates: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Update tenant information.

        Args:
            tenant_id: Tenant ID (defaults to current tenant)
            updates: Fields to update

        Returns:
            Updated tenant information
        """
        tenant = tenant_id or self.tenant_id
        return self._make_request('PUT', f'/api/v1/tenants/{tenant}', updates)

    # ============================================================================
    # API KEY MANAGEMENT
    # ============================================================================

    def create_api_key(self, name: str, permissions: List[str],
                       expires_at: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new API key.

        Args:
            name: Key name
            permissions: List of permissions
            expires_at: Expiration date (ISO format)

        Returns:
            Created API key information
        """
        data = {
            'name': name,
            'permissions': permissions,
            'expires_at': expires_at
        }
        return self._make_request('POST', f'/api/v1/tenants/{self.tenant_id}/api-keys', data)

    def list_api_keys(self) -> List[Dict[str, Any]]:
        """
        List all API keys for the tenant.

        Returns:
            List of API keys
        """
        response = self._make_request('GET', f'/api/v1/tenants/{self.tenant_id}/api-keys')
        return response.get('api_keys', [])

    def revoke_api_key(self, key_id: str) -> Dict[str, Any]:
        """
        Revoke an API key.

        Args:
            key_id: API key ID to revoke

        Returns:
            Revocation confirmation
        """
        return self._make_request('DELETE', f'/api/v1/tenants/{self.tenant_id}/api-keys/{key_id}')

    # ============================================================================
    # ROUTE SEARCH
    # ============================================================================

    def search_routes(self, origin: str, destination: str, date: Union[str, date],
                     max_transfers: int = 3, preferences: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Search for routes between two stations.

        Args:
            origin: Origin station name or code
            destination: Destination station name or code
            date: Travel date (YYYY-MM-DD)
            max_transfers: Maximum number of transfers
            preferences: Optional search preferences

        Returns:
            Route search results
        """
        if isinstance(date, date):
            date = date.isoformat()

        data = {
            'origin': origin,
            'destination': destination,
            'date': date,
            'max_transfers': max_transfers,
            'preferences': preferences or {}
        }

        return self._make_request('POST', '/api/v1/routes/search', data)

    def search_routes_async(self, origin: str, destination: str, date: Union[str, date],
                           max_transfers: int = 3, preferences: Optional[Dict] = None) -> str:
        """
        Search for routes asynchronously.

        Args:
            origin: Origin station name or code
            destination: Destination station name or code
            date: Travel date (YYYY-MM-DD)
            max_transfers: Maximum number of transfers
            preferences: Optional search preferences

        Returns:
            Job ID for tracking the async search
        """
        if isinstance(date, date):
            date = date.isoformat()

        data = {
            'origin': origin,
            'destination': destination,
            'date': date,
            'max_transfers': max_transfers,
            'preferences': preferences or {}
        }

        response = self._make_request('POST', '/api/v1/routes/search-async', data)
        return response['job_id']

    def get_route_details(self, route_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific route.

        Args:
            route_id: Route ID

        Returns:
            Route details
        """
        return self._make_request('GET', f'/api/v1/routes/{route_id}')

    # ============================================================================
    # STATION DATA
    # ============================================================================

    def get_stations(self, search: Optional[str] = None, limit: int = 100,
                    offset: int = 0) -> Dict[str, Any]:
        """
        Get list of stations.

        Args:
            search: Search query for station names
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of stations
        """
        params = {'limit': limit, 'offset': offset}
        if search:
            params['search'] = search

        return self._make_request('GET', '/api/v1/stations', params=params)

    def get_station_details(self, station_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a station.

        Args:
            station_id: Station ID

        Returns:
            Station details
        """
        return self._make_request('GET', f'/api/v1/stations/{station_id}')

    # ============================================================================
    # TRAIN DATA
    # ============================================================================

    def get_trains(self, search: Optional[str] = None, limit: int = 100,
                  offset: int = 0) -> Dict[str, Any]:
        """
        Get list of trains.

        Args:
            search: Search query for train numbers or names
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of trains
        """
        params = {'limit': limit, 'offset': offset}
        if search:
            params['search'] = search

        return self._make_request('GET', '/api/v1/trains', params=params)

    def get_train_details(self, train_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a train.

        Args:
            train_id: Train ID

        Returns:
            Train details
        """
        return self._make_request('GET', f'/api/v1/trains/{train_id}')

    # ============================================================================
    # ASYNC JOB MANAGEMENT
    # ============================================================================

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of an async job.

        Args:
            job_id: Job ID

        Returns:
            Job status information
        """
        return self._make_request('GET', f'/api/v1/jobs/{job_id}/status')

    def get_job_result(self, job_id: str) -> Dict[str, Any]:
        """
        Get the result of a completed async job.

        Args:
            job_id: Job ID

        Returns:
            Job result data
        """
        return self._make_request('GET', f'/api/v1/jobs/{job_id}/result')

    def wait_for_job(self, job_id: str, timeout: int = 300,
                    poll_interval: float = 1.0) -> Dict[str, Any]:
        """
        Wait for an async job to complete.

        Args:
            job_id: Job ID
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks

        Returns:
            Job result data

        Raises:
            TimeoutError: If job doesn't complete within timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.get_job_status(job_id)
            job_status = status.get('status')

            if job_status == 'completed':
                return self.get_job_result(job_id)
            elif job_status == 'failed':
                raise RailwayOSException(f"Job failed: {status.get('error', 'Unknown error')}")

            time.sleep(poll_interval)

        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def get_api_info(self) -> Dict[str, Any]:
        """
        Get API information and available endpoints.

        Returns:
            API information
        """
        return self._make_request('GET', '/api/v1/info')

    def get_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for the tenant.

        Returns:
            Usage statistics
        """
        return self._make_request('GET', f'/api/v1/tenants/{self.tenant_id}/stats')


class RailwayOSException(Exception):
    """Exception raised for Railway OS API errors."""

    def __init__(self, message: str, error_data: Optional[Dict] = None):
        super().__init__(message)
        self.error_data = error_data or {}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_client(api_key: str, tenant_id: str, base_url: str = "http://localhost:8000") -> RailwayOSClient:
    """
    Create a Railway OS client instance.

    Args:
        api_key: Your API key
        tenant_id: Your tenant ID
        base_url: API gateway base URL

    Returns:
        Configured RailwayOSClient instance
    """
    return RailwayOSClient(api_key, tenant_id, base_url)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_usage():
    """
    Example usage of the Railway OS Python SDK.
    """

    # Initialize client
    client = RailwayOSClient(
        api_key="your-api-key-here",
        tenant_id="your-tenant-id-here",
        base_url="http://localhost:8000"
    )

    try:
        # Check system health
        health = client.health_check()
        print(f"System health: {health}")

        # Search for routes
        routes = client.search_routes(
            origin="Delhi",
            destination="Mumbai",
            date="2024-01-15",
            max_transfers=2
        )
        print(f"Found {len(routes.get('routes', []))} routes")

        # Get station information
        stations = client.get_stations(search="Delhi", limit=10)
        print(f"Found {len(stations.get('stations', []))} stations matching 'Delhi'")

        # Async route search
        job_id = client.search_routes_async(
            origin="Chennai",
            destination="Kolkata",
            date="2024-01-15"
        )
        print(f"Started async search with job ID: {job_id}")

        # Wait for completion
        result = client.wait_for_job(job_id, timeout=60)
        print(f"Async search completed with {len(result.get('routes', []))} routes")

    except RailwayOSException as e:
        print(f"API Error: {e}")
        if e.error_data:
            print(f"Error details: {e.error_data}")


if __name__ == "__main__":
    example_usage()