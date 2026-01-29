# ROUTE VERIFICATION RULES & VALIDATION FRAMEWORK

## Overview
Comprehensive set of rules for verifying routes in the Railway Operating System. These rules ensure data integrity, operational feasibility, safety compliance, and business logic adherence.

---

## 1. BASIC DATA INTEGRITY RULES

### 1.1 Route Existence & Identification
- **Rule 1.1.1**: Route ID must be unique across entire system
  - Error: Duplicate route ID detected
  - Check: `SELECT COUNT(*) FROM routes WHERE route_id = '{route_id}'`

- **Rule 1.1.2**: Route must have non-null route_id and route_name
  - Error: Route ID or name is NULL
  - Check: `WHERE route_id IS NULL OR route_name IS NULL`

- **Rule 1.1.3**: Route name must be between 3-100 characters
  - Error: Route name length invalid
  - Check: `LENGTH(route_name) BETWEEN 3 AND 100`

- **Rule 1.1.4**: Route must have valid creation timestamp
  - Error: Invalid or missing creation time
  - Check: `created_at <= CURRENT_TIMESTAMP AND created_at >= '2020-01-01'`

### 1.2 Route Code & Numbering
- **Rule 1.2.1**: Route code must be unique and non-null
  - Error: Duplicate or missing route code
  - Check: `route_code IS NOT NULL AND COUNT(*) = 1`

- **Rule 1.2.2**: Route code format must be alphanumeric (optional: "ROUTE_" prefix)
  - Error: Invalid route code format
  - Check: `route_code ~ '^[A-Z0-9_]+$'`

- **Rule 1.2.3**: Route number must be positive if present
  - Error: Invalid route number
  - Check: `route_number IS NULL OR route_number > 0`

---

## 2. STATION & LOCATION RULES

### 2.1 Origin & Destination Stations
- **Rule 2.1.1**: Route must have both origin and destination stations
  - Error: Origin or destination station missing
  - Check: `origin_station_id IS NOT NULL AND destination_station_id IS NOT NULL`

- **Rule 2.1.2**: Origin and destination must be different stations
  - Error: Route starts and ends at same station
  - Check: `origin_station_id != destination_station_id`

- **Rule 2.1.3**: Both origin and destination stations must exist in database
  - Error: Station not found in system
  - Check: `EXISTS (SELECT 1 FROM stations WHERE station_id = origin_station_id)`

- **Rule 2.1.4**: Both stations must have valid status (active)
  - Error: Station is inactive or closed
  - Check: `station.status = 'active'`

- **Rule 2.1.5**: Both stations must have valid geographic coordinates
  - Error: Station location missing or invalid
  - Check: `latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180`

### 2.2 Intermediate Stops
- **Rule 2.2.1**: Intermediate stops must be a valid JSON array (if present)
  - Error: Invalid stops JSON format
  - Check: `stops IS NULL OR stops::text ~ '^\[.*\]$'`

- **Rule 2.2.2**: No intermediate stop can be origin or destination
  - Error: Stop duplicates origin or destination
  - Check: `NOT (stop_id = origin_station_id OR stop_id = destination_station_id)`

- **Rule 2.2.3**: All intermediate stops must exist in database
  - Error: Stop station not found
  - Check: `EXISTS (SELECT 1 FROM stations WHERE station_id = stop_id)`

- **Rule 2.2.4**: All intermediate stops must be active/operational
  - Error: Stop station is inactive
  - Check: `station.status = 'active'`

- **Rule 2.2.5**: Stops must be ordered geographically or by sequence
  - Error: Stops are out of order
  - Check: Stops follow logical geographic progression

- **Rule 2.2.6**: No duplicate stops in the route
  - Error: Same station appears multiple times as stops
  - Check: `COUNT(DISTINCT stop_id) = JSON_ARRAY_LENGTH(stops)`

- **Rule 2.2.7**: Number of stops must be reasonable (max 50 stops)
  - Error: Too many intermediate stops
  - Check: `JSON_ARRAY_LENGTH(stops) <= 50`

---

## 3. DISTANCE & DURATION RULES

### 3.1 Distance Validation
- **Rule 3.1.1**: Distance must be positive (> 0)
  - Error: Invalid or missing distance
  - Check: `distance > 0`

- **Rule 3.1.2**: Distance must be reasonable (max 5000 km)
  - Error: Distance exceeds maximum limit
  - Check: `distance <= 5000`

- **Rule 3.1.3**: Distance must be minimum 1 km
  - Error: Distance too short
  - Check: `distance >= 1`

- **Rule 3.1.4**: Distance must match stop sequence
  - Error: Calculated distance doesn't match recorded distance
  - Check: `ABS(distance - CALCULATED_DISTANCE) < distance * 0.1` (within 10% tolerance)

- **Rule 3.1.5**: Distance with stops must be reasonable
  - Error: Distance to first stop > total distance
  - Check: `SUM(distance_to_stops) <= distance`

### 3.2 Duration Validation
- **Rule 3.2.1**: Duration must be positive (> 0 minutes)
  - Error: Invalid or missing duration
  - Check: `duration_minutes > 0`

- **Rule 3.2.2**: Duration must be reasonable (max 2880 minutes = 48 hours)
  - Error: Duration exceeds maximum limit
  - Check: `duration_minutes <= 2880`

- **Rule 3.2.3**: Duration must be minimum 5 minutes
  - Error: Duration too short for any real route
  - Check: `duration_minutes >= 5`

- **Rule 3.2.4**: Duration must align with distance and train speed
  - Error: Duration doesn't match distance/speed ratio
  - Check: `EXPECTED_DURATION * 0.8 <= duration_minutes <= EXPECTED_DURATION * 1.5`

- **Rule 3.2.5**: Duration includes stops and station halts
  - Error: Duration too short given number of stops
  - Check: `duration_minutes >= (number_of_stops * halt_time_minutes) + calculated_travel_time`

### 3.3 Speed Validation
- **Rule 3.3.1**: Average speed must be calculated (distance / duration)
  - Error: Cannot calculate speed
  - Check: `speed = distance / (duration_minutes / 60)`

- **Rule 3.3.2**: Average speed must be reasonable (5-300 km/h for trains)
  - Error: Speed is unrealistic
  - Check: `AVERAGE_SPEED BETWEEN 5 AND 300`

- **Rule 3.3.3**: Average speed must match train type
  - Error: Speed inconsistent with train type
  - Check: `AVERAGE_SPEED <= train.max_speed`

---

## 4. TRAIN & CAPACITY RULES

### 4.1 Train Assignment
- **Rule 4.1.1**: Route must have assigned train(s)
  - Error: No train assigned to route
  - Check: `train_id IS NOT NULL`

- **Rule 4.1.2**: Assigned train must exist in database
  - Error: Train not found
  - Check: `EXISTS (SELECT 1 FROM trains WHERE train_id = train_id)`

- **Rule 4.1.3**: Assigned train must be active/operational
  - Error: Train is inactive or under maintenance
  - Check: `train.status = 'active'`

- **Rule 4.1.4**: Train must be suitable for route distance
  - Error: Train range insufficient for route
  - Check: `train.max_range >= distance`

- **Rule 4.1.5**: Train must be capable of speed required
  - Error: Train cannot achieve required speed
  - Check: `train.max_speed >= REQUIRED_SPEED`

### 4.2 Capacity Rules
- **Rule 4.2.1**: Route must have capacity information
  - Error: Missing capacity data
  - Check: `total_capacity > 0`

- **Rule 4.2.2**: Total capacity must match train capacity
  - Error: Route capacity doesn't match train
  - Check: `ABS(total_capacity - train.total_seats) < 5` (within tolerance)

- **Rule 4.2.3**: Seat classes breakdown must sum to total
  - Error: Seat class breakdown incorrect
  - Check: `(seats_first + seats_second + seats_general) = total_capacity`

- **Rule 4.2.4**: Each seat class must be non-negative
  - Error: Negative seat count
  - Check: `seats_first >= 0 AND seats_second >= 0 AND seats_general >= 0`

- **Rule 4.2.5**: First class allocation must be reasonable (max 10%)
  - Error: First class exceeds reasonable percentage
  - Check: `seats_first / total_capacity <= 0.10`

- **Rule 4.2.6**: Second class allocation must be reasonable (10-30%)
  - Error: Second class allocation unrealistic
  - Check: `0.10 <= (seats_second / total_capacity) <= 0.30`

---

## 5. SCHEDULE & TIMING RULES

### 5.1 Departure & Arrival Times
- **Rule 5.1.1**: Departure time must be earlier than arrival time
  - Error: Departure >= arrival time
  - Check: `departure_time < arrival_time`

- **Rule 5.1.2**: Both departure and arrival times must be valid
  - Error: Invalid time format
  - Check: Time format is HH:MM (24-hour)

- **Rule 5.1.3**: Time difference must match duration
  - Error: Duration doesn't match time difference
  - Check: `(arrival_time - departure_time) IN MINUTES = duration_minutes`

- **Rule 5.1.4**: Operating days must be specified
  - Error: No operating days defined
  - Check: `operating_days IS NOT NULL AND operating_days != '[]'`

- **Rule 5.1.5**: Operating days must contain valid day codes
  - Error: Invalid day code
  - Check: Each day IN ('MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN')

- **Rule 5.1.6**: At least one operating day must be selected
  - Error: No days selected
  - Check: `JSON_ARRAY_LENGTH(operating_days) > 0`

### 5.2 Stop Timings
- **Rule 5.2.1**: Arrival at each stop must be after departure from previous stop
  - Error: Stop timing is out of sequence
  - Check: `arrival_at_stop[i] > departure_from_stop[i-1]`

- **Rule 5.2.2**: Halt duration at stops must be reasonable (5-30 minutes)
  - Error: Halt time is unrealistic
  - Check: `halt_time BETWEEN 5 AND 30 MINUTES`

- **Rule 5.2.3**: Total halt time must not exceed 50% of journey
  - Error: Too much time spent at stops
  - Check: `SUM(halt_times) <= duration_minutes * 0.5`

- **Rule 5.2.4**: Stop arrival times must be strictly increasing
  - Error: Stops are not in chronological order
  - Check: `arrival_times ARE STRICTLY INCREASING`

---

## 6. FARE & PRICING RULES

### 6.1 Fare Structure
- **Rule 6.1.1**: Route must have fare information
  - Error: Missing fare data
  - Check: `base_fare IS NOT NULL`

- **Rule 6.1.2**: Base fare must be positive
  - Error: Invalid or negative base fare
  - Check: `base_fare > 0`

- **Rule 6.1.3**: Base fare must be reasonable (currency units)
  - Error: Fare is unrealistic
  - Check: `base_fare BETWEEN 1 AND 100000`

- **Rule 6.1.4**: Fare should correlate with distance
  - Error: Fare per km is unrealistic
  - Check: `FARE_PER_KM BETWEEN 0.5 AND 50`

- **Rule 6.1.5**: Surcharges must be specified
  - Error: Missing surcharge definitions
  - Check: `surcharges IS NOT NULL AND surcharges != '{}'`

- **Rule 6.1.6**: Surcharge percentages must be reasonable (0-100%)
  - Error: Invalid surcharge percentage
  - Check: `surcharge_value BETWEEN 0 AND 100`

### 6.2 Discount Rules
- **Rule 6.2.1**: Discount types must be valid
  - Error: Invalid discount type
  - Check: Discount type IN ('child', 'senior', 'student', 'bulk', 'loyalty')

- **Rule 6.2.2**: Discount percentages must not exceed 100%
  - Error: Discount >= 100%
  - Check: `discount_percentage < 100`

- **Rule 6.2.3**: Discount percentages must be reasonable (0-50%)
  - Error: Discount seems too high
  - Check: `discount_percentage BETWEEN 0 AND 50`

- **Rule 6.2.4**: Child discount must be <= senior discount
  - Error: Child discount higher than senior
  - Check: `child_discount <= senior_discount`

---

## 7. ROUTE RELATIONSHIP RULES

### 7.1 Transfer Compatibility
- **Rule 7.1.1**: Direct routes (0 transfers) must not have connecting routes
  - Error: Route marked as direct but has transfers
  - Check: `transfer_count = 0 AND no_connecting_routes`

- **Rule 7.1.2**: Routes with 1+ transfers must have valid connection points
  - Error: Transfer point invalid
  - Check: Transfer points must exist and be on both routes

- **Rule 7.1.3**: Transfer time must be sufficient (min 10 minutes)
  - Error: Insufficient transfer time
  - Check: `transfer_time >= 10 MINUTES`

- **Rule 7.1.4**: Transfer routes must not create circular paths
  - Error: Route creates infinite loop
  - Check: No cycles in route graph

- **Rule 7.1.5**: Route sequence must be logical
  - Error: Route transfers don't follow geographic logic
  - Check: Transfer routes progress logically toward destination

### 7.2 Alternative Routes
- **Rule 7.2.1**: If alternative route exists, it must be marked
  - Error: Alternative route not recorded
  - Check: `is_alternative_route = TRUE if alternatives_exist`

- **Rule 7.2.2**: Alternative routes must have similar origin/destination
  - Error: Alternative route to different locations
  - Check: `alternative.origin = main.origin AND alternative.destination = main.destination`

- **Rule 7.2.3**: Alternative routes must differ in significant way
  - Error: Alternative route is too similar to main
  - Check: Significant difference in duration, stops, or fare

- **Rule 7.2.4**: Alternative routes must have performance comparison
  - Error: No comparison metrics
  - Check: Has duration_diff, fare_diff, stops_diff

---

## 8. PERFORMANCE & RELIABILITY RULES

### 8.1 On-Time Performance
- **Rule 8.1.1**: On-time percentage must be recorded
  - Error: Missing on-time data
  - Check: `on_time_percentage IS NOT NULL`

- **Rule 8.1.2**: On-time percentage must be 0-100%
  - Error: Invalid percentage value
  - Check: `on_time_percentage BETWEEN 0 AND 100`

- **Rule 8.1.3**: Routes with <70% on-time should be flagged
  - Warning: Low reliability
  - Check: `on_time_percentage < 70` (flag for review)

- **Rule 8.1.4**: Cancelled trips must be tracked
  - Error: Cancellation rate not recorded
  - Check: `cancellation_rate IS NOT NULL`

- **Rule 8.1.5**: Cancellation rate must be 0-100%
  - Error: Invalid cancellation percentage
  - Check: `cancellation_rate BETWEEN 0 AND 100`

### 8.2 Safety Rules
- **Rule 8.2.1**: Route must have safety status
  - Error: Safety status not defined
  - Check: `safety_status IN ('approved', 'pending', 'restricted', 'closed')`

- **Rule 8.2.2**: Unsafe routes must not be active
  - Error: Unsafe route is operating
  - Check: `IF safety_status = 'closed' THEN route_status != 'active'`

- **Rule 8.2.3**: Speed limits must be enforced
  - Error: Route speed exceeds limit
  - Check: `ROUTE_SPEED <= SPEED_LIMIT_FOR_REGION`

- **Rule 8.2.4**: Grade/incline must be within limits (if applicable)
  - Error: Route has dangerous grade
  - Check: `grade <= MAX_TRAIN_GRADE (typically 5%)`

---

## 9. OPERATIONAL & MAINTENANCE RULES

### 9.1 Maintenance & Status
- **Rule 9.1.1**: Route must have valid status
  - Error: Invalid route status
  - Check: `route_status IN ('active', 'inactive', 'suspended', 'under_maintenance')`

- **Rule 9.1.2**: Inactive routes must have reason documented
  - Error: No reason for inactivity
  - Check: `IF route_status != 'active' THEN reason IS NOT NULL`

- **Rule 9.1.3**: Routes under maintenance must have scheduled completion
  - Error: Maintenance has no end date
  - Check: `IF route_status = 'under_maintenance' THEN maintenance_end_date IS NOT NULL`

- **Rule 9.1.4**: Maintenance end date must be in future
  - Error: Maintenance date is in past
  - Check: `maintenance_end_date > CURRENT_DATE`

- **Rule 9.1.5**: Last maintenance date must be recent (within 6 months)
  - Warning: Route overdue for maintenance
  - Check: `DATEDIFF(CURRENT_DATE, last_maintenance_date) <= 180 days`

### 9.2 Approval & Verification
- **Rule 9.2.1**: Routes must be approved before operation
  - Error: Active route is not approved
  - Check: `IF route_status = 'active' THEN is_approved = TRUE`

- **Rule 9.2.2**: Approved routes must have approval date
  - Error: Approval date missing
  - Check: `IF is_approved = TRUE THEN approved_date IS NOT NULL`

- **Rule 9.2.3**: Approval date must be before or on operation start
  - Error: Approval after operation start
  - Check: `approved_date <= operation_start_date`

- **Rule 9.2.4**: Route must have verification timestamp
  - Error: No verification recorded
  - Check: `verified_at IS NOT NULL`

---

## 10. DATA QUALITY RULES

### 10.1 Completeness
- **Rule 10.1.1**: All mandatory fields must be populated
  - Error: Missing required field
  - Check: route_id, route_name, origin, destination, distance, duration, etc.

- **Rule 10.1.2**: Optional fields should be null or valid
  - Error: Optional field has invalid value
  - Check: null or valid value only

- **Rule 10.1.3**: JSON fields must be well-formed
  - Error: Malformed JSON
  - Check: Valid JSON syntax

- **Rule 10.1.4**: Text fields must not contain invalid characters
  - Error: Invalid character in text
  - Check: No control characters or SQL injection attempts

### 10.2 Consistency
- **Rule 10.2.1**: Route metrics must be internally consistent
  - Error: Metrics contradict each other
  - Check: distance, duration, speed relationships valid

- **Rule 10.2.2**: Associated records must align with route
  - Error: Related data inconsistency
  - Check: Schedules, fares, trains match route spec

- **Rule 10.2.3**: Timestamps must be logical
  - Error: Timestamp ordering is wrong
  - Check: created_at < updated_at < deleted_at (if applicable)

- **Rule 10.2.4**: No conflicting status states
  - Error: Contradictory status flags
  - Check: Cannot be both active and deleted, etc.

### 10.3 Freshness
- **Rule 10.3.1**: Route data should be recently verified
  - Warning: Data not verified recently
  - Check: `DATEDIFF(CURRENT_DATE, verified_at) <= 90 days`

- **Rule 10.3.2**: Operating schedule should be current
  - Warning: Schedule may be outdated
  - Check: If date > 1 year old, flag for update

---

## 11. GEOGRAPHIC & NETWORK RULES

### 11.1 Geographic Validity
- **Rule 11.1.1**: Origin and destination must be different locations
  - Error: Same origin and destination
  - Check: Coordinates differ significantly

- **Rule 11.1.2**: Route distance must match geographic calculation
  - Error: Recorded distance doesn't match coordinates
  - Check: Haversine calculation within 10% tolerance

- **Rule 11.1.3**: All stops must be geographically between origin and destination
  - Error: Stop is outside route path
  - Check: Intermediate stops don't create backtracking

- **Rule 11.1.4**: No stops should be closer to origin than previous stop
  - Error: Route backtracks
  - Check: Distance progression is monotonic

### 11.2 Network Connectivity
- **Rule 11.2.1**: Route must connect valid network nodes
  - Error: Route connects to non-existent nodes
  - Check: All stations exist and are networked

- **Rule 11.2.2**: No isolated routes
  - Warning: Route has no connections
  - Check: Route connects to at least 1 other route

- **Rule 11.2.3**: Network must be well-connected
  - Warning: Sparse network detected
  - Check: Most stations accessible within 2 transfers

---

## 12. TEMPORAL RULES

### 12.1 Date & Time Validity
- **Rule 12.1.1**: All dates must be valid calendar dates
  - Error: Invalid date format or value
  - Check: Date validation

- **Rule 12.1.2**: Operating date range must be valid
  - Error: Start date > end date
  - Check: `operation_start_date <= operation_end_date` (if both present)

- **Rule 12.1.3**: No routes scheduled too far in future
  - Warning: Schedule >2 years ahead
  - Check: Schedules should be within reasonable planning horizon

- **Rule 12.1.4**: Historical routes must have end dates
  - Error: Inactive route has no end date
  - Check: `IF is_historic = TRUE THEN end_date IS NOT NULL`

---

## 13. REGULATORY & COMPLIANCE RULES

### 13.1 License & Certification
- **Rule 13.1.1**: Route operator must be licensed
  - Error: Operator license missing or expired
  - Check: Operator has valid license

- **Rule 13.1.2**: Route must meet regulatory standards
  - Error: Route doesn't comply with regulations
  - Check: Safety and operational standards met

- **Rule 13.1.3**: Environmental compliance must be documented
  - Error: No environmental assessment
  - Check: Route meets environmental standards

### 13.2 Accessibility & Inclusivity
- **Rule 13.2.1**: Route must accommodate disabled passengers
  - Error: No accessibility features
  - Check: Wheelchair access, audio/visual announcements provided

- **Rule 13.2.2**: Stations must have accessibility facilities
  - Error: Stop station lacks accessibility
  - Check: All stations on route have required facilities

---

## 14. ANOMALY DETECTION RULES

### 14.1 Statistical Anomalies
- **Rule 14.1.1**: Fare must not deviate >3 standard deviations from mean
  - Anomaly: Unusual pricing
  - Check: `ABS(fare - AVG_FARE) <= 3 * STDEV`

- **Rule 14.1.2**: Duration must not deviate >2 SD from similar routes
  - Anomaly: Suspiciously fast or slow
  - Check: Compare with routes of similar distance

- **Rule 14.1.3**: Capacity should match train type
  - Anomaly: Unusual capacity
  - Check: Capacity typical for train class

### 14.2 Logical Anomalies
- **Rule 14.2.1**: Distance cannot exceed geographical maximum
  - Anomaly: Distance unrealistically large
  - Check: `distance <= EARTH_CIRCUMFERENCE`

- **Rule 14.2.2**: Duration cannot be less than time needed to traverse distance
  - Anomaly: Impossibly fast speed
  - Check: `duration >= distance / MAX_TRAIN_SPEED`

- **Rule 14.2.3**: On-time performance cannot improve without explanation
  - Anomaly: Sudden performance improvement
  - Check: Flag for review if improvement > 20%

---

## VERIFICATION IMPLEMENTATION

### Database Trigger for Automatic Verification
```sql
CREATE TRIGGER verify_route_before_insert_update
BEFORE INSERT OR UPDATE ON routes
FOR EACH ROW
EXECUTE FUNCTION verify_route_data();
```

### Python Verification Class
```python
class RouteVerifier:
    def __init__(self):
        self.rules = self.load_all_rules()
    
    def verify_route(self, route_data):
        """Run all verification rules on route data"""
        violations = []
        warnings = []
        
        for rule in self.rules:
            result = rule.check(route_data)
            if result['type'] == 'error':
                violations.append(result)
            elif result['type'] == 'warning':
                warnings.append(result)
        
        return {
            'is_valid': len(violations) == 0,
            'violations': violations,
            'warnings': warnings,
            'passed_rules': len(self.rules) - len(violations),
            'total_rules': len(self.rules)
        }
```

### CLI Verification Command
```bash
python -m database.verify_routes --route-id ROUTE_123 --detailed
python -m database.verify_routes --all --export-report report.json
python -m database.verify_routes --check-network --visualize
```

---

## SEVERITY LEVELS

| Level | Impact | Action |
|-------|--------|--------|
| **CRITICAL** | Route cannot operate | Block operation immediately |
| **ERROR** | Route invalid | Reject changes |
| **WARNING** | Route suboptimal | Flag for review |
| **INFO** | Route note | Log only |

---

## TESTING CHECKLIST

- [ ] All mandatory fields present
- [ ] Data types are correct
- [ ] Relationships are valid
- [ ] Calculations are accurate
- [ ] Status is consistent
- [ ] Temporal ordering is correct
- [ ] Geographic data is valid
- [ ] Capacity matches train
- [ ] Performance metrics reasonable
- [ ] All rules pass

---

## SUMMARY

Total Rules: 100+
Categories: 14
Critical Rules: 25+
Warning Rules: 15+
Info Rules: 20+

All routes must pass verification before becoming operational.
