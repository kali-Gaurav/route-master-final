# Railway Operating System - Database Architecture & Route Finding Workflow

## Database Tables and Data Structure

### Core Tables Overview

The railway operating system uses a comprehensive PostgreSQL database with 5 primary tables that store all railway data:

#### 1. **Stations Table** (`stations`)
**Purpose**: Stores information about all railway stations in the network.

**Key Fields**:
- `id` (UUID): Primary key
- `code` (String, 10 chars): Station code (e.g., "HWH", "MAS", "PUNE")
- `name` (String, 255 chars): Full station name
- `latitude`/`longitude` (DECIMAL): Geographic coordinates
- `state`, `zone`, `division`, `district`: Administrative divisions
- `platform_count`, `track_count`: Infrastructure details
- `facilities`: WiFi, parking, food court, ATM, medical facility flags
- `is_active`: Operational status
- `is_junction`: Whether station allows transfers

**Sample Data**:
```json
{
  "code": "HWH",
  "name": "Howrah Junction",
  "latitude": 22.5822,
  "longitude": 88.3378,
  "state": "West Bengal",
  "zone": "Eastern Railway",
  "platform_count": 23,
  "is_junction": true,
  "has_wifi": true,
  "has_food_court": true
}
```

#### 2. **Trains Table** (`trains`)
**Purpose**: Stores information about all trains operating in the network.

**Key Fields**:
- `id` (UUID): Primary key
- `number` (String, 20 chars): Train number (e.g., "12841")
- `name` (String, 255 chars): Train name (e.g., "Coromandel Express")
- `type` (String, 50 chars): Train type - "express", "superfast", "passenger", "rajdhani"
- `operator`: Railway zone/operator
- `max_speed_kmph`: Maximum speed
- `total_coaches`: Number of coaches
- `classes_available`: Array of class types ["1A", "2A", "3A", "SL", "2S"]
- `is_active`: Operational status

**Sample Data**:
```json
{
  "number": "12841",
  "name": "Coromandel Express",
  "type": "superfast",
  "operator": "Southern Railway",
  "max_speed_kmph": 130,
  "total_coaches": 24,
  "classes_available": ["1A", "2A", "3A", "SL"],
  "is_active": true
}
```

#### 3. **Routes Table** (`routes`)
**Purpose**: Defines the path and schedule information for each train journey.

**Key Fields**:
- `id` (UUID): Primary key
- `train_id` (UUID): Foreign key to trains table
- `origin_station_id`/`dest_station_id`: Foreign keys to stations table
- `distance_km`: Total distance of the route
- `duration_minutes`: Total travel time
- `stops` (JSONB): Array of intermediate stations with arrival/departure times
- `intermediate_stations` (JSONB): Quick lookup array of station codes
- `days_of_operation`: Array of integers [0-6] for Mon-Sun operation
- `route_type`: "direct", "connecting", "circular"
- `is_active`: Operational status

**Sample Data**:
```json
{
  "train_id": "uuid-12841",
  "origin_station_id": "uuid-hwh",
  "dest_station_id": "uuid-mas",
  "distance_km": 1659.0,
  "duration_minutes": 540,
  "stops": [
    {"code": "HWH", "arrival": null, "departure": "14:10:00"},
    {"code": "MAS", "arrival": "23:10:00", "departure": null}
  ],
  "intermediate_stations": ["HWH", "MAS"],
  "days_of_operation": [0,1,2,3,4,5,6],
  "route_type": "direct"
}
```

#### 4. **Schedules Table** (`schedules`)
**Purpose**: Stores specific schedule information for routes on particular dates.

**Key Fields**:
- `id` (UUID): Primary key
- `route_id` (UUID): Foreign key to routes table
- `departure_time`/`arrival_time`: Time strings (HH:MM:SS)
- `platform`: Platform number
- `valid_from`/`valid_to`: Date range when schedule is valid
- `is_active`: Schedule status

**Sample Data**:
```json
{
  "route_id": "uuid-route-12841",
  "departure_time": "14:10:00",
  "arrival_time": "23:10:00",
  "platform": "5",
  "valid_from": "2024-01-01",
  "valid_to": "2024-12-31"
}
```

#### 5. **Fares Table** (`fares`)
**Purpose**: Stores fare information for different classes on routes.

**Key Fields**:
- `id` (UUID): Primary key
- `route_id` (UUID): Foreign key to routes table
- `class_type`: Class of travel ("1A", "2A", "3A", "SL", "2S")
- `base_fare`: Base price for the class
- `reservation_charge`, `superfast_charge`, `tatkal_charge`: Additional charges

**Sample Data**:
```json
{
  "route_id": "uuid-route-12841",
  "class_type": "2A",
  "base_fare": 2850.00,
  "reservation_charge": 50.00,
  "superfast_charge": 75.00
}
```

## Data Usage and Relationships

### How Data is Used

1. **Station Data**: Used for origin/destination validation, geographic calculations, facility information
2. **Train Data**: Used for train identification, capacity planning, class availability
3. **Route Data**: Core routing information, distance calculations, schedule validation
4. **Schedule Data**: Time-specific information, platform assignments, validity periods
5. **Fare Data**: Pricing calculations, class availability, revenue management

### Database Relationships

```
Stations (1) ──── (Many) Routes (Many) ──── (1) Trains
    │                    │
    └────────────────────┼─────────────────────┘
                         │
                    Schedules (Many)
                         │
                    Fares (Many)
```

## Route Finding Workflow

### Input Parameters
When a user searches for routes, they provide:
- **Origin Station**: Station code or name (e.g., "HWH", "Howrah")
- **Destination Station**: Station code or name (e.g., "MAS", "Chennai")
- **Travel Date**: Date in YYYY-MM-DD format (e.g., "2024-01-15")
- **Preferences**: Optional filters (max transfers, preferred class, etc.)

### Step-by-Step Route Finding Process

#### Step 1: Input Validation
```
User Input: Origin="HWH", Destination="MAS", Date="2024-01-15"
↓
Validate Stations Exist:
- Query: SELECT id, code, name FROM stations WHERE code='HWH' OR name ILIKE '%HWH%'
- Query: SELECT id, code, name FROM stations WHERE code='MAS' OR name ILIKE '%MAS%'
- Result: HWH_ID = uuid-hwh, MAS_ID = uuid-mas
```

#### Step 2: Find Direct Routes (0 Transfers)
```
Query Direct Routes:
SELECT r.*, t.number, t.name, t.type, s.departure_time, s.arrival_time, f.base_fare
FROM routes r
JOIN trains t ON r.train_id = t.id
LEFT JOIN schedules s ON r.id = s.route_id
LEFT JOIN fares f ON r.id = f.route_id
WHERE r.origin_station_id = 'HWH_ID'
  AND r.dest_station_id = 'MAS_ID'
  AND r.is_active = true
  AND r.days_of_operation @> ARRAY[date.weekday()]
  AND s.valid_from <= '2024-01-15' AND s.valid_to >= '2024-01-15'

Result: [
  {
    "train_no": "12841",
    "train_name": "Coromandel Express",
    "departure": "14:10:00",
    "arrival": "23:10:00",
    "duration": 540,
    "distance": 1659.0,
    "fare_2a": 2850.00
  }
]
```

#### Step 3: Find 1-Transfer Routes
```
If insufficient direct routes, find connecting routes:

For each intermediate station (junction stations):
1. Find routes from Origin to Junction
2. Find routes from Junction to Destination
3. Calculate transfer time and total duration
4. Validate train availability and waiting time

Example: HWH → KGP → MAS
- Route 1: HWH to KGP (local train)
- Route 2: KGP to MAS (connecting train)
- Transfer time: 30 minutes minimum
- Total duration: Route1.duration + Route2.duration + transfer_time
```

#### Step 4: Find 2-Transfer Routes
```
For complex journeys requiring 2 transfers:

Origin → Junction1 → Junction2 → Destination

Example: DEL → BPL → NGP → MAS
- Route 1: DEL to BPL
- Route 2: BPL to NGP
- Route 3: NGP to MAS
- Transfer times: 30 min at each junction
- Total duration: Sum of all segments + transfer times
```

#### Step 5: Validate Route Viability

For each potential route, validate:

**Time Validation:**
- Departure time must be before arrival time
- Transfer waiting time must be ≥ 30 minutes
- Total journey must complete within 24 hours

**Train Availability:**
- Check if trains are operational (`is_active = true`)
- Verify schedule validity for travel date
- Ensure sufficient capacity

**Station Connectivity:**
- Origin and destination stations must exist
- Intermediate stations must be valid junctions
- Route must be geographically logical

**Business Rules:**
- Maximum 3 transfers allowed
- No circular routes
- Valid fare classes available

#### Step 6: Calculate Route Metrics

For each valid route:
```python
# Calculate total duration
total_duration = sum(segment.duration_minutes for segment in segments)
transfer_time = (len(segments) - 1) * 30  # 30 min per transfer
final_duration = total_duration + transfer_time

# Calculate total distance
total_distance = sum(segment.distance_km for segment in segments)

# Calculate total cost
total_cost = sum(segment.fare for segment in segments)

# Calculate arrival time
departure_datetime = datetime.combine(travel_date, departure_time)
arrival_datetime = departure_datetime + timedelta(minutes=final_duration)
```

#### Step 7: Apply Preferences and Sorting

**Sort Options:**
- **Duration**: Shortest total travel time
- **Cost**: Lowest total fare
- **Transfers**: Fewest number of transfers
- **Departure Time**: Earliest departure

**Filter Options:**
- Maximum transfers (0-3)
- Preferred train types
- Fare class availability
- Maximum journey time

#### Step 8: Format Response

Return structured data:
```json
{
  "direct_routes": [
    {
      "type": "direct",
      "train_no": "12841",
      "train_name": "Coromandel Express",
      "departure": "14:10:00",
      "arrival": "23:10:00",
      "duration_minutes": 540,
      "distance_km": 1659.0,
      "fare": {"2A": 2850.00, "3A": 1850.00},
      "availability": "available"
    }
  ],
  "transfer_routes": [
    {
      "type": "transfer",
      "segments": [
        {
          "train_no": "18615",
          "from": "HWH",
          "to": "KGP",
          "departure": "08:30:00",
          "arrival": "10:45:00"
        },
        {
          "train_no": "12833",
          "from": "KGP",
          "to": "MAS",
          "departure": "11:30:00",
          "arrival": "22:15:00"
        }
      ],
      "transfer_station": "KGP",
      "transfer_time_minutes": 45,
      "total_duration_minutes": 825,
      "total_distance_km": 1720.0,
      "total_fare": 3200.00
    }
  ],
  "total_found": 5,
  "search_criteria": {
    "origin": "HWH",
    "destination": "MAS",
    "date": "2024-01-15",
    "max_transfers": 2
  }
}
```

## Data Flow Architecture

### API Layer → Service Layer → Database Layer

1. **API Layer** (`/api/v1/routes/search`):
   - Receives user input (origin, destination, date)
   - Validates input parameters
   - Calls route service

2. **Service Layer** (`RouteService.search_routes()`):
   - Parses search criteria
   - Calls database manager for route finding
   - Formats results for API response

3. **Database Layer** (`RailwayDatabaseManager.find_routes_comprehensive()`):
   - Executes complex SQL queries with joins
   - Uses eager loading for performance
   - Applies business logic validation
   - Returns structured route data

### Performance Optimizations

- **Indexes**: Composite indexes on frequently queried fields
- **Eager Loading**: Pre-load related data to avoid N+1 queries
- **Connection Pooling**: Reuse database connections
- **Caching**: Cache frequently accessed station/train data
- **Pagination**: Limit results to prevent memory issues

### Data Integrity Checks

- **Foreign Key Constraints**: Ensure referential integrity
- **Check Constraints**: Validate data ranges and formats
- **Business Rules**: Custom validation logic
- **Temporal Validation**: Date/time consistency checks
- **Reference Data Validation**: Valid train types, route types, fare classes

This comprehensive system ensures reliable, fast, and accurate route finding across the entire railway network with support for complex multi-transfer journeys.</content>
<parameter name="filePath">c:\Users\Gaurav Nagar\OneDrive\Documents\testingfolder_v3\railway-operating-system-core\DATABASE_WORKFLOW_DOCUMENTATION.md