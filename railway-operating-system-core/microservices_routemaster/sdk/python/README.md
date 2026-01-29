# Railway Operating System Python SDK

A Python client library for the Railway Operating System microservices platform. This SDK provides a convenient interface for interacting with the Railway OS API, including route search, tenant management, and data access.

## Features

- 🚄 **Route Search**: Find routes between stations with advanced filtering
- 🏢 **Multi-tenant Support**: Built-in tenant isolation and management
- 🔑 **API Key Authentication**: Secure authentication with API keys
- ⚡ **Async Operations**: Support for asynchronous job processing
- 📊 **Data Access**: Query stations, trains, and route information
- 🏥 **Health Monitoring**: Check service health and status
- 🛡️ **Error Handling**: Comprehensive error handling and validation

## Installation

```bash
pip install railway-os-sdk
```

Or install from source:

```bash
git clone https://github.com/railway-os/sdk-python.git
cd sdk-python
pip install -e .
```

## Quick Start

```python
from railway_os_sdk import RailwayOSClient

# Initialize the client
client = RailwayOSClient(
    api_key="your-api-key-here",
    tenant_id="your-tenant-id-here",
    base_url="https://api.railwayos.com"  # or http://localhost:8000 for local
)

# Search for routes
routes = client.search_routes(
    origin="Delhi",
    destination="Mumbai",
    date="2024-01-15",
    max_transfers=2
)

print(f"Found {len(routes['routes'])} routes")

# Get station information
stations = client.get_stations(search="Delhi", limit=10)
print(f"Found {len(stations['stations'])} stations")

# Async route search
job_id = client.search_routes_async(
    origin="Chennai",
    destination="Kolkata",
    date="2024-01-15"
)

# Wait for completion
result = client.wait_for_job(job_id, timeout=60)
print(f"Async search found {len(result['routes'])} routes")
```

## API Reference

### Initialization

```python
client = RailwayOSClient(
    api_key="your-api-key",      # Required: Your API key
    tenant_id="your-tenant-id",  # Required: Your tenant ID
    base_url="http://localhost:8000"  # Optional: API gateway URL
)
```

### Route Search

#### Synchronous Search
```python
routes = client.search_routes(
    origin="Delhi",              # Origin station name/code
    destination="Mumbai",        # Destination station name/code
    date="2024-01-15",          # Travel date (YYYY-MM-DD)
    max_transfers=3,            # Maximum transfers (default: 3)
    preferences={               # Optional preferences
        "preferred_trains": ["Rajdhani", "Shatabdi"],
        "avoid_stations": ["Agra"],
        "max_duration": 24
    }
)
```

#### Asynchronous Search
```python
# Start async search
job_id = client.search_routes_async(
    origin="Delhi",
    destination="Mumbai",
    date="2024-01-15"
)

# Check status
status = client.get_job_status(job_id)

# Wait for completion
result = client.wait_for_job(job_id, timeout=300)
```

### Station Data

```python
# List stations
stations = client.get_stations(
    search="Delhi",     # Optional search query
    limit=100,          # Maximum results
    offset=0           # Pagination offset
)

# Get specific station
station = client.get_station_details("DEL")  # Station code
```

### Train Data

```python
# List trains
trains = client.get_trains(
    search="Rajdhani",  # Optional search query
    limit=50,
    offset=0
)

# Get specific train
train = client.get_train_details("12951")  # Train number
```

### Tenant Management

```python
# Get current tenant info
tenant = client.get_tenant()

# Update tenant settings
updated = client.update_tenant(updates={
    "settings": {
        "max_routes_per_request": 100,
        "cache_ttl": 7200
    }
})
```

### API Key Management

```python
# Create new API key
new_key = client.create_api_key(
    name="Mobile App Key",
    permissions=["read:routes", "read:stations"],
    expires_at="2025-12-31T23:59:59Z"
)

# List API keys
keys = client.list_api_keys()

# Revoke API key
client.revoke_api_key("key-id-here")
```

### Health Monitoring

```python
# Check all services
health = client.health_check()

# Check specific service
route_health = client.health_check("route-service")
```

## Error Handling

The SDK raises `RailwayOSException` for API errors:

```python
from railway_os_sdk import RailwayOSException

try:
    routes = client.search_routes("Delhi", "Mumbai", "2024-01-15")
except RailwayOSException as e:
    print(f"API Error: {e}")
    print(f"Details: {e.error_data}")
```

## Configuration

### Environment Variables

You can configure the client using environment variables:

```bash
export RAILWAY_OS_API_KEY="your-api-key"
export RAILWAY_OS_TENANT_ID="your-tenant-id"
export RAILWAY_OS_BASE_URL="https://api.railwayos.com"
```

Then initialize without parameters:

```python
import os
client = RailwayOSClient(
    api_key=os.getenv("RAILWAY_OS_API_KEY"),
    tenant_id=os.getenv("RAILWAY_OS_TENANT_ID"),
    base_url=os.getenv("RAILWAY_OS_BASE_URL")
)
```

## Advanced Usage

### Custom Session Configuration

```python
import requests
from railway_os_sdk import RailwayOSClient

# Create custom session with proxy
session = requests.Session()
session.proxies = {
    'http': 'http://proxy.company.com:8080',
    'https': 'http://proxy.company.com:8080'
}

client = RailwayOSClient("api-key", "tenant-id")
client.session = session  # Replace the default session
```

### Pagination Handling

```python
# Handle large result sets
all_stations = []
offset = 0
limit = 100

while True:
    result = client.get_stations(limit=limit, offset=offset)
    stations = result['stations']
    all_stations.extend(stations)

    if len(stations) < limit:
        break
    offset += limit

print(f"Total stations: {len(all_stations)}")
```

### Batch Operations

```python
# Search multiple routes
route_queries = [
    {"origin": "Delhi", "destination": "Mumbai", "date": "2024-01-15"},
    {"origin": "Chennai", "destination": "Kolkata", "date": "2024-01-16"},
    {"origin": "Bangalore", "destination": "Delhi", "date": "2024-01-17"}
]

# Start async searches
job_ids = []
for query in route_queries:
    job_id = client.search_routes_async(**query)
    job_ids.append(job_id)

# Collect results
results = []
for job_id in job_ids:
    result = client.wait_for_job(job_id)
    results.append(result)
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/railway-os/sdk-python.git
cd sdk-python
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black railway_os_sdk/

# Sort imports
isort railway_os_sdk/

# Lint code
flake8 railway_os_sdk/

# Type checking
mypy railway_os_sdk/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 **Documentation**: https://railway-os-sdk.readthedocs.io/
- 🐛 **Bug Reports**: https://github.com/railway-os/sdk-python/issues
- 💬 **Discussions**: https://github.com/railway-os/sdk-python/discussions
- 📧 **Email**: support@railwayos.com

## Changelog

### Version 1.0.0
- Initial release
- Route search functionality
- Station and train data access
- Tenant and API key management
- Async job processing
- Health monitoring
- Comprehensive error handling