# Integration Guide: Train Running Days Validator

## Quick Start

### 1. Initialize the Validator in Your Application

```python
# In your main API file (api.py)
from train_running_days_validator import TrainRunningDaysValidator
from datetime import datetime

# Initialize once at startup
train_validator = TrainRunningDaysValidator('production.db')

# Load running days from CSV (run this once or when data updates)
def initialize_train_data():
    """Run this once at application startup"""
    count = train_validator.load_running_days_from_csv('dataset/train_info.csv')
    logger.info(f"✅ Loaded running days for {count} trains")

# Call at app startup
initialize_train_data()
```

### 2. Update Route Search API

```python
@app.route('/api/routes', methods=['GET'])
def get_routes():
    """
    Updated route search with date validation
    
    Query params:
    - origin: Source station code (required)
    - destination: Destination station code (required)
    - date: Travel date in YYYY-MM-DD format (required)
    - max_transfers: Maximum transfers allowed (optional, default: 2)
    """
    
    origin = request.args.get('origin', '').upper()
    destination = request.args.get('destination', '').upper()
    date_str = request.args.get('date')  # CRITICAL: Required now
    
    # Validate inputs
    if not all([origin, destination, date_str]):
        return jsonify({
            'error': 'Missing required parameters: origin, destination, date',
            'example': '/api/routes?origin=CSMT&destination=DADA&date=2026-01-26'
        }), 400
    
    # Parse date
    try:
        travel_date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({
            'error': 'Invalid date format. Use YYYY-MM-DD',
            'example': '/api/routes?origin=CSMT&destination=DADA&date=2026-01-26'
        }), 400
    
    # Check if past date
    if travel_date.date() < datetime.now().date():
        return jsonify({
            'error': 'Cannot search for past dates',
            'date_requested': date_str,
            'today': datetime.now().strftime('%Y-%m-%d')
        }), 400
    
    try:
        # ✅ Get only trains running on this date
        available_trains = train_validator.get_trains_running_on_date(travel_date)
        
        if not available_trains:
            return jsonify({
                'error': f'No trains available on {date_str}',
                'date': date_str,
                'suggestion': 'Try a different date'
            }), 404
        
        # Generate routes (existing logic, but with available_trains filter)
        routes = generate_routes_for_date(
            origin=origin,
            destination=destination,
            available_trains=available_trains,
            max_transfers=int(request.args.get('max_transfers', 2))
        )
        
        if not routes:
            return jsonify({
                'error': 'No routes found',
                'origin': origin,
                'destination': destination,
                'date': date_str
            }), 404
        
        # ✅ Validate each route's trains and transfers
        validated_routes = []
        for route in routes:
            validation_report = train_validator.validate_route_trains(
                route['trains'],  # List of (train_no, arrival_time, departure_time)
                travel_date
            )
            
            if validation_report['is_valid']:
                route['validation'] = validation_report
                validated_routes.append(route)
        
        return jsonify({
            'status': 'success',
            'travel_date': date_str,
            'origin': origin,
            'destination': destination,
            'total_routes': len(validated_routes),
            'routes': validated_routes
        }), 200
    
    except Exception as e:
        logger.error(f"Error in route search: {str(e)}")
        return jsonify({'error': str(e)}), 500
```

### 3. Helper Function: Generate Routes for Date

```python
def generate_routes_for_date(origin, destination, available_trains, max_transfers=2):
    """
    Generate routes using only trains available on the travel date
    
    Args:
        origin: Source station code
        destination: Destination station code
        available_trains: List of train numbers running on the date
        max_transfers: Maximum transfers allowed
        
    Returns:
        List of valid routes
    """
    
    routes = []
    
    # Query database for direct routes using only available_trains
    direct_routes = db.execute(f'''
        SELECT DISTINCT train_no, arrival_time, departure_time, total_duration
        FROM routes
        WHERE source_station = ? 
        AND destination_station = ?
        AND train_no IN ({','.join(map(str, available_trains))})
        ORDER BY total_duration
        LIMIT 10
    ''', (origin, destination))
    
    for route in direct_routes:
        routes.append({
            'type': 'direct',
            'trains': [(route['train_no'], route['arrival_time'], route['departure_time'])],
            'total_duration': route['total_duration']
        })
    
    # For transfers, use similar logic but with transfer validation
    if max_transfers > 0:
        transfer_routes = find_transfer_routes(
            origin, destination, available_trains, max_transfers
        )
        routes.extend(transfer_routes)
    
    return routes
```

### 4. Frontend Update

```typescript
// Before: Just origin and destination
// const url = `/api/routes?origin=CSMT&destination=DADA`;

// After: Include travel date
const handleSearch = async () => {
    if (!origin || !destination || !travelDate) {
        toast.error('Please select origin, destination, and date');
        return;
    }
    
    // Format date as YYYY-MM-DD
    const formattedDate = new Date(travelDate)
        .toISOString()
        .split('T')[0];
    
    try {
        const response = await fetch(
            `/api/routes?origin=${origin.code}&destination=${destination.code}&date=${formattedDate}`
        );
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to fetch routes');
        }
        
        const data = await response.json();
        setRoutes(data.routes);
        
    } catch (error) {
        toast.error(`Search failed: ${error.message}`);
    }
};
```

### 5. Testing

```python
# Test 1: Load running days
from train_running_days_validator import TrainRunningDaysValidator
validator = TrainRunningDaysValidator('production.db')
validator.load_running_days_from_csv('dataset/train_info.csv')

# Test 2: Check specific train
from datetime import datetime
date = datetime(2026, 1, 26)  # Monday
is_running = validator.is_train_running_on_date(10103, date)
print(f"Train 10103 on Monday: {is_running}")

# Test 3: Get available trains
available = validator.get_trains_running_on_date(date)
print(f"Total trains on Monday: {len(available)}")

# Test 4: Validate route
route_trains = [
    (10103, '08:35', '10:50'),
    (10104, '11:20', '13:30'),
]
report = validator.validate_route_trains(route_trains, date)
print(f"Route valid: {report['is_valid']}")
```

### 6. Backward Compatibility

If you want to support both old (without date) and new (with date) APIs:

```python
@app.route('/api/routes', methods=['GET'])
def get_routes():
    origin = request.args.get('origin', '').upper()
    destination = request.args.get('destination', '').upper()
    date_str = request.args.get('date')
    
    # If no date provided, use today
    if not date_str:
        travel_date = datetime.now()
        logger.warning(f"No date provided, using today: {travel_date.strftime('%Y-%m-%d')}")
    else:
        try:
            travel_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    # Rest of code...
```

---

## API Response Examples

### Success Response
```json
{
  "status": "success",
  "travel_date": "2026-01-26",
  "origin": "CSMT",
  "destination": "DADA",
  "total_routes": 3,
  "routes": [
    {
      "type": "direct",
      "trains": [
        [10103, "08:35", "10:50"]
      ],
      "total_duration": "2h 15m",
      "validation": {
        "is_valid": true,
        "valid_trains": [
          {
            "segment": 1,
            "train_no": 10103,
            "date": "2026-01-26"
          }
        ],
        "valid_transfers": [],
        "notes": []
      }
    }
  ]
}
```

### Error Response - Invalid Date
```json
{
  "error": "Invalid date format. Use YYYY-MM-DD",
  "example": "/api/routes?origin=CSMT&destination=DADA&date=2026-01-26"
}
```

### Error Response - Past Date
```json
{
  "error": "Cannot search for past dates",
  "date_requested": "2026-01-20",
  "today": "2026-01-26"
}
```

### Error Response - No Trains Available
```json
{
  "error": "No trains available on 2026-01-26",
  "date": "2026-01-26",
  "suggestion": "Try a different date"
}
```

---

## Environment Variables (Optional)

Add to `.env` for configuration:

```bash
# Train running days
TRAIN_DATA_CSV=dataset/train_info.csv
MIN_TRANSFER_TIME=15  # Minutes between trains for transfer
ENABLE_DATE_VALIDATION=true
```

---

## Verification Checklist

- [ ] `train_running_days_validator.py` created
- [ ] Database table `train_running_days` created
- [ ] Running days loaded from `dataset/train_info.csv`
- [ ] API updated to accept `date` parameter
- [ ] Route validation checks `travel_date`
- [ ] Frontend sends `date` in API calls
- [ ] Transfer logic handles day-crossing
- [ ] Tests pass for:
  - [ ] Single-day routes
  - [ ] Multi-day transfer routes
  - [ ] Midnight-crossing transfers
  - [ ] Invalid dates
  - [ ] Unavailable trains

---

## Summary

✅ **Problem:** Routes didn't check if trains actually run on the requested date  
✅ **Solution:** Integrated TrainRunningDaysValidator  
✅ **Benefits:**
- Only real, available trains suggested
- Proper handling of day-crossing transfers
- Reliable booking confirmations
- Production-ready system

**This is critical for system reliability!**
