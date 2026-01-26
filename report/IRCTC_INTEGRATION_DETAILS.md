# IRCTC API Integration Guide

## Overview

This document describes how the IRCTC RapidAPI has been integrated into the Route Master application for real-time validation of train routes.

## API Key Configuration

**API Key**: `e0adaea886msh3fb9b9456cad9ccp17a317jsna7fe7b2fe0b6`
**Host**: `irctc1.p.rapidapi.com`
**Base URL**: `https://irctc1.p.rapidapi.com/api/v3`

The API key is configured in [api.py](api.py#L17-L19) and should be moved to environment variables in production.

## IRCTC Endpoints Used

### 1. `getLiveStation`
Gets real-time information about trains at a specific station.

**Usage**: Retrieve live trains currently at or passing through a station
**Configuration in code**: [get_live_station_data()](api.py#L26-L47)

```python
GET /api/live-station?station=PGT&hours=1
```

### 2. `getSeatAvailability`
Checks real-time seat availability for a specific train journey.

**Usage**: Validate if seats are available on each train segment
**Configuration in code**: [get_seat_availability()](api.py#L49-L71)

```python
GET /api/seat-availability?train=12345&source=PGT&destination=KOTA&date=25-01-2026
```

### 3. `getFare`
Gets current fare information for a train journey.

**Usage**: Show updated pricing for routes
**Configuration in code**: [get_train_fare()](api.py#L73-L95)

```python
GET /api/fare?train=12345&source=PGT&destination=KOTA&date=25-01-2026
```

### 4. Live Train Location (if available)
Can be used to show real-time train locations on a map.

## Integration Flow

### Request Processing Pipeline

```
User Request
    ↓
[/api/routes endpoint]
    ↓
Route Generation (route_optimizer.py)
    ↓
↓→ Generate all feasible routes (200-300)
↓→ Pareto optimization
↓→ Select top 10 routes
    ↓
[IRCTC Validation Loop - Top 10 Routes]
    ↓
For Each Route:
  ├─→ get_seat_availability() → Check seats
  ├─→ get_train_fare() → Get current fares
  ├─→ Validate timing & locations
  └─→ Mark route as valid/invalid
    ↓
Response to Frontend
    ↓
Display Validated Routes with:
  • Real-time seat availability
  • Current fares
  • Live train information
```

### Key Function: `validate_route_with_irctc()`

Location: [api.py#L123-L176](api.py#L123-L176)

This function:
1. Takes a route and travel date
2. For each train segment in the route:
   - Calls `get_seat_availability()` to check available seats
   - Calls `get_train_fare()` to get current pricing
   - Stores results in IRCTC validation metadata
3. Returns enriched route with validation data
4. Marks route as valid/invalid based on errors

```python
validated_route = validate_route_with_irctc(route, travel_date)
# Returns route with:
# {
#   ...route_data,
#   'irctc_validation': {
#     'segments': [
#       {
#         'train_no': '12345',
#         'seats': {...},
#         'fare': {...}
#       },
#       ...
#     ],
#     'valid': True/False,
#     'errors': [...]
#   }
# }
```

## Backend API Endpoints

### 1. Main Routes Endpoint (with IRCTC Validation)
```
GET /api/routes?origin=PGT&destination=KOTA&max_transfers=3&date=25-01-2026
```

**Response**:
```json
{
  "metadata": {
    "source": "PGT",
    "destination": "KOTA",
    "total_routes_generated": 245,
    "pareto_front_size": 52,
    "optimal_routes_count": 10
  },
  "optimal_routes": [
    {
      "route_id": "OPT_ROUTE_01",
      "category": "FASTEST ⚡",
      "objectives": {
        "time": 480,
        "cost": 2500,
        "transfers": 1,
        "seat_prob": 100.0,
        "safety_score": 100.0,
        "distance": 500
      },
      "segments": [...],
      "irctc_validation": {
        "segments": [
          {
            "train_no": "12345",
            "from": "PGT",
            "to": "KOTA",
            "seats": {
              "available": 45,
              "class": "SL",
              "status": "AVAILABLE"
            },
            "fare": {
              "total": 2500,
              "base": 2000,
              "tax": 500,
              "currency": "INR"
            }
          }
        ],
        "valid": true,
        "errors": []
      }
    }
  ],
  "validation_metadata": {
    "validated_at": "2026-01-24T15:30:00",
    "travel_date": "25-01-2026",
    "routes_validated": 10,
    "irctc_api_used": true
  }
}
```

### 2. Live Station Endpoint
```
GET /api/live-station?station=PGT&hours=1
```

### 3. Seat Availability Endpoint
```
GET /api/seat-availability?train=12345&source=PGT&destination=KOTA&date=25-01-2026
```

### 4. Fare Endpoint
```
GET /api/fare?train=12345&source=PGT&destination=KOTA&date=25-01-2026
```

### 5. Validate Routes Endpoint
```
POST /api/validate-routes
Content-Type: application/json

{
  "routes": [...],
  "date": "25-01-2026"
}
```

### 6. Health Check
```
GET /api/health
```

## Error Handling

### API Timeout
If IRCTC API doesn't respond within 10 seconds, the function returns `None` and logs a warning.

```python
def get_seat_availability(...):
    response = requests.get(..., timeout=10)  # 10-second timeout
```

### Invalid Dates
Dates should be in `DD-MM-YYYY` format. Missing date defaults to today.

### Rate Limiting
IRCTC RapidAPI has rate limits:
- **Requests per minute**: Check RapidAPI dashboard
- **Handling**: Implement retry logic if needed

## Response Validation

Each route validates:
1. ✅ **Seats Available**: Returns seat count and class information
2. ✅ **Fare Valid**: Returns current ticket price
3. ✅ **Train Active**: Verifies train exists and runs on the date
4. ✅ **Timings**: Validates departure/arrival times

## Integration with Frontend

The frontend consumes the `/api/routes` endpoint and displays:

1. **Route List**: Top 10 routes with Pareto optimization
2. **Real-time Info**: Seat availability and fares from IRCTC
3. **Route Details**: Each segment shows validated data
4. **Validation Status**: Shows if route was successfully validated

### Sample Frontend Call

```javascript
// React component
const fetchRoutes = async (origin, destination) => {
  const response = await fetch(
    `http://localhost:5000/api/routes?origin=${origin}&destination=${destination}&max_transfers=3`,
    {
      headers: { 'Content-Type': 'application/json' }
    }
  );
  const data = await response.json();
  
  // Display routes with IRCTC validation info
  data.optimal_routes.forEach(route => {
    console.log(`Route ${route.route_id}: Valid=${route.irctc_validation.valid}`);
    route.irctc_validation.segments.forEach(seg => {
      console.log(`  Train ${seg.train_no}: ${seg.seats.available} seats, ₹${seg.fare.total}`);
    });
  });
};
```

## Testing

Use the included test script to verify integration:

```bash
python test_irctc_integration.py
```

This will test:
1. Live station data retrieval
2. Seat availability checking
3. Fare information fetching
4. Full route optimization with IRCTC validation
5. Batch validation endpoint

## Performance Considerations

### Optimization Timing
- **Route Generation**: 5-30 seconds
- **IRCTC Validation** (top 10 routes): 20-50 seconds
  - ~2-5 seconds per route × 10 routes
- **Total Time**: 25-80 seconds

### Caching
Results are cached in memory:
- Cache key: `{origin}_{destination}_{max_transfers}`
- Subsequent identical requests return immediately
- Cache survives server restart if using persistent storage

### Parallelization (Future)
Could parallelize IRCTC API calls:
```python
# Instead of sequential validation
for route in top_10_routes:
    validate_route_with_irctc(route, date)

# Use concurrent.futures
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(validate_route_with_irctc, routes, [date]*10)
```

## Troubleshooting

### IRCTC API Returns 401
**Cause**: Invalid API key
**Solution**: Verify API key in [api.py](api.py#L17)

### IRCTC API Returns 429
**Cause**: Rate limit exceeded
**Solution**: Implement exponential backoff or cache responses

### No Routes Generated
**Cause**: Station codes not in database or no train connections
**Solution**: Verify `Train_details.csv` contains the stations

### Validation Errors
**Cause**: IRCTC API endpoint not accessible or different response format
**Solution**: Check RapidAPI dashboard for API status, update parsing logic

## Future Enhancements

1. **Async Validation**: Use `asyncio` for parallel IRCTC calls
2. **Caching Strategy**: Redis for distributed caching
3. **Real-time Updates**: WebSocket for live seat/price updates
4. **Analytics**: Track which routes users select vs. IRCTC data
5. **Dynamic Pricing**: Show price trends over time
6. **Booking Integration**: Direct booking through IRCTC API

## Production Deployment

Before going to production:

1. **Move API Key to Environment Variables**
   ```python
   import os
   IRCTC_API_KEY = os.environ.get('IRCTC_API_KEY')
   ```

2. **Add Error Logging**
   ```python
   import logging
   logging.error(f"IRCTC API Error: {e}")
   ```

3. **Implement Rate Limiting**
   ```python
   from flask_limiter import Limiter
   limiter = Limiter(app)
   ```

4. **Add Request Validation**
   - Validate station codes against database
   - Validate date format
   - Validate train numbers

5. **Database Integration**
   - Store validation results
   - Track API usage
   - Monitor performance

6. **Monitoring & Alerts**
   - Monitor API response times
   - Alert on validation failures
   - Track API quotas

## Support & Documentation

- IRCTC RapidAPI: https://rapidapi.com/API-MATIC/api/irctc1
- Flask Documentation: https://flask.palletsprojects.com/
- Requests Library: https://requests.readthedocs.io/
