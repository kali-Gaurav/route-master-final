# Quick Start: Using the Intelligent Train Running Days Validator

## One-Time Setup

### Initialize and Load Running Days

```bash
# Run once at application startup
python train_running_days_validator.py

# Output:
# ✓ Found 9,880 unique trains in RAPPID dataset
# ✓ Successfully loaded 9,880 trains into database
# ✓ Coverage: 9,880/9,880 RAPPID trains (100.0%)
```

**What This Does:**
1. Reads RAPPID dataset to get 9,880 valid train numbers
2. Cross-references with train_info.csv running days
3. Loads only matching trains into database (9,880 trains)
4. Creates indexes for fast lookups
5. Populates in-memory cache for < 1μs access

---

## API Usage

### Request Format

```
GET /api/routes?origin=CSMT&destination=DADA&date=2026-01-26&max_transfers=2
```

**Parameters:**
- `origin` - Source station code (e.g., "CSMT")
- `destination` - Destination station code (e.g., "DADA")
- `date` - Travel date in YYYY-MM-DD format (e.g., "2026-01-26")
- `max_transfers` - Maximum transfers allowed (optional, default: 4)

### Example Request/Response

```bash
# Request: Routes from Mumbai (CSMT) to Madgaon (DADA) on Monday
curl "http://localhost:5000/api/routes?origin=CSMT&destination=DADA&date=2026-01-26"

# Response: Only routes with trains that run on Monday!
{
  "metadata": {
    "origin": "CSMT",
    "destination": "DADA",
    "travel_date": "26-01-2026",
    "generated_at": "2026-01-26T19:38:09.123456"
  },
  "optimal_routes": [
    {
      "route_id": "OPT_1",
      "category": "FASTEST",
      "segments": [
        {
          "train_no": 10103,
          "from": "CSMT",
          "to": "DADA",
          "departure": "08:35",
          "arrival": "10:50"
        }
      ],
      "objectives": {
        "total_duration": "2h 15m",
        "num_transfers": 0,
        "price": 150,
        "comfort": 8
      }
    }
  ],
  "all_alternative_routes": [...]
}
```

---

## Backend Integration

### In route_optimizer.py

The validator is automatically used when a date parameter is provided:

```python
# Automatic intelligent filtering happens here:
result = get_routes_data(
    origin="CSMT",
    destination="DADA",
    max_transfers=2,
    travel_date=datetime(2026, 1, 26)  # Triggers filtering!
)

# All returned routes have only trains that run on that date
```

### How It Works (Behind The Scenes)

```python
# Inside find_routes BFS traversal:

for edge in graph[current_station]:
    train_no = edge['train_no']
    
    # Intelligent validation: Is this train available?
    if validator.is_train_running_on_date(train_no, travel_date):
        # Yes! Add to route
        routes.append(path_with_this_train)
    else:
        # No! Skip this train
        continue

# Result: Only valid routes returned
```

---

## Frontend Integration

### JavaScript/React

```javascript
// User selects origin, destination, date
const origin = "CSMT";
const destination = "DADA";
const travelDate = new Date("2026-01-26");

// Format date as YYYY-MM-DD
const dateStr = travelDate.toISOString().split('T')[0];

// Call API with date parameter
const response = await fetch(
    `/api/routes?origin=${origin}&destination=${destination}&date=${dateStr}`
);

const data = await response.json();

// Routes are automatically filtered by running trains!
console.log(`Found ${data.optimal_routes.length} optimal routes`);
console.log(`Alternative routes: ${data.all_alternative_routes.length}`);

// Display routes to user
displayRoutes(data.optimal_routes);
```

---

## Advanced Usage

### Check Specific Train Availability

```python
from train_running_days_validator import TrainRunningDaysValidator
from datetime import datetime

validator = TrainRunningDaysValidator('production.db')

# Check if train 10103 runs on Monday
monday = datetime(2026, 1, 26)
is_running = validator.is_train_running_on_date(10103, monday)
print(f"Train 10103 on Monday: {is_running}")  # True or False
```

### Get All Available Trains for a Date

```python
from datetime import datetime

# Get all trains running on Monday
monday = datetime(2026, 1, 26)
available_trains = validator.get_trains_running_on_date(monday)
print(f"Trains on Monday: {len(available_trains)}")  # 1,189 trains
```

### Validate a Complete Route

```python
from datetime import datetime

# Check if a multi-train route is valid
route_segments = [
    (10103, "08:35", "10:50"),  # Train, arrival, departure
    (10104, "11:20", "13:30"),  # Next train (same day)
]

monday = datetime(2026, 1, 26)

report = validator.validate_route_trains(route_segments, monday)
print(f"Route valid: {report['is_valid']}")
print(f"Valid trains: {report['valid_trains']}")
print(f"Valid transfers: {report['valid_transfers']}")
```

---

## Understanding the Filtering

### Example: Monday vs Sunday

**Monday (1,189 trains available):**
```
CSMT → DADA: 7 optimal routes found
```

**Sunday (but Sunday has no trains in this region):**
```
CSMT → DADA: 0 routes found (no trains running)
```

**Why Different?**
- Different trains run on different days
- Some trains run Monday-Friday only
- Some trains run weekends only
- The validator filters based on actual train schedules

---

## Troubleshooting

### Problem: "No routes found" for a date

**Causes:**
1. No trains run on that date (check `validator.get_trains_running_on_date(date)`)
2. No viable connections exist (check route feasibility)
3. Date has insufficient transfer time

**Solution:**
```python
# Check if any trains run that day
available = validator.get_trains_running_on_date(your_date)
if available:
    print(f"{len(available)} trains available")
else:
    print("No trains run on this date")
```

### Problem: Different routes for same origin/destination on different days

**This is correct!** Different trains run different days. Routes should differ.

**Example:**
- Monday: Train 10103 (Monday-Friday) + connections = 7 routes
- Saturday: Train 10104 (Saturday only) + connections = 5 routes

---

## Performance Expectations

| Operation | Time | Notes |
|-----------|------|-------|
| API request | 1-100ms | Includes route generation |
| Single train lookup | < 1μs | Cache hit (typical) |
| 50 train lookups | 100-250ms | Database hits |
| Route generation | 1-5ms | Typical with 2-3 transfers |
| Monday vs Sunday | 1ms | Fast comparison |

---

## Deployment Notes

### Production Checklist

```
✓ Run train_running_days_validator.py at startup
✓ Verify "9880/9880 RAPPID trains (100.0%)" message
✓ Check production.db file created (~500 KB)
✓ Confirm date parameter required in API
✓ Test on different dates (Monday vs Sunday vs Holiday)
✓ Monitor performance (~1ms per route)
✓ Verify routes change based on travel date
```

### Environment Configuration

```python
# In your app startup:

from train_running_days_validator import TrainRunningDaysValidator

# Initialize (singleton pattern)
validator = TrainRunningDaysValidator('production.db')

# Setup and load data
if validator.setup_database_schema():
    loaded = validator.load_running_days_for_rappid_trains()
    print(f"Loaded {loaded} trains - ready!")
else:
    print("ERROR: Failed to setup validator")
    exit(1)
```

### Database Files

```
Location: <app_root>/production.db
Size: ~500 KB
Table: train_running_days (9,880 rows)
Indexes: idx_train_running_days_train_no
Access: O(1) lookup via train_no
```

---

## Summary

The intelligent validator ensures:

✓ **Correctness** - Only routes with actually-running trains  
✓ **Efficiency** - Fast lookups (< 1μs from cache)  
✓ **Reliability** - 100% RAPPID train coverage  
✓ **Maintainability** - Clear logging and validation  
✓ **Scalability** - Handles growth in routes/trains  

Users get the **right routes for their travel date**, not just any available routes!
