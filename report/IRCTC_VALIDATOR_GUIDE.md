# IRCTC VALIDATOR - QUICK USAGE GUIDE

## Overview

The `irctc_validator.py` module validates trains using **real IRCTC seat searches**. This is critical because it proves trains are actually available on the date users want to travel.

**Key Benefit:** Routes contain only trains that have actual available seats.

---

## Installation

1. Ensure dependencies installed:
```bash
pip install -r requirements.txt
# Includes: irctc-client, sqlalchemy, python-dotenv
```

2. Make sure these files exist:
```
database.py           (ORM models)
irctc_client.py      (IRCTC API wrapper)
logger.py            (Logging setup)
config.py            (Configuration)
```

---

## Basic Usage

### Single Train Validation

```python
from irctc_validator import IRCTCValidator

# Initialize
validator = IRCTCValidator()

# Validate one train
result = validator.validate_train(
    train_no="16320",           # Train number
    date="2026-02-15",          # Date (YYYY-MM-DD)
    source="NDLS",              # Origin station code
    destination="KOTA"          # Destination station code
)

# Check result
print(f"Train: {result.train_no}")
print(f"Available: {result.is_available}")  # True = has seats, False = WL
print(f"Seats: {result.seats_available}")    # Number of available seats
print(f"Lowest Fare: ₹{result.lowest_fare}") # Estimated minimum fare
print(f"Time: {result.validation_time_ms:.1f}ms")  # How fast

# Example output:
# Train: 16320
# Available: True
# Seats: 45
# Lowest Fare: ₹450
# Time: 2345.3ms
```

---

## Batch Validation (Multiple Trains)

```python
# Validate 3 trains in parallel
trains_to_check = [
    ("16320", "2026-02-15"),
    ("12951", "2026-02-15"),
    ("14309", "2026-02-15"),
]

results = validator.validate_trains_batch(
    trains_to_check,
    max_parallel=5  # Up to 5 concurrent API calls
)

# Process results
for result in results:
    if result.is_available:
        print(f"✓ {result.train_no}: {result.seats_available} seats")
    else:
        print(f"✗ {result.train_no}: Waitlisted/Unavailable")
```

---

## Using Cache

Validation results are **cached for 12 hours** to avoid hammering IRCTC API.

```python
# First call → hits IRCTC API
result1 = validator.validate_train("16320", "2026-02-15")
# Time: ~2-5 seconds

# Second call → uses cache (same train, same date)
result2 = validator.validate_train("16320", "2026-02-15")
# Time: <1ms (instant!)

print(result2.cached)  # True if from cache

# Check cache statistics
stats = validator.get_validation_statistics()
print(f"Cache hits: {stats['cached']}")
print(f"Cache size: {stats['cache_size']}")

# Clear cache if needed
validator.clear_cache()
```

---

## Update Database Status

Validation results automatically update train status:

```python
result = validator.validate_train("16320", "2026-02-15")

# Update database
validator.update_train_status_from_validation(result)

# In database:
# - If result.is_available = True  → train.status = ACTIVE
# - If result.is_available = False → train.status = INACTIVE
# - If error/timeout             → don't change (keep existing)

# Check what was updated
session = validator.db.get_session()
train = session.query(Train).filter_by(train_no="16320").first()
print(f"Status: {train.status}")        # ACTIVE or INACTIVE
print(f"Last validated: {train.last_validated}")
session.close()
```

---

## Validate Entire Dataset

```python
# Validate all 11,000+ trains (on a specific date)
report = validator.validate_all_trains(
    date="2026-02-15",
    limit=None  # limit=100 to test with fewer trains
)

# Report shows:
print(f"Total validations: {report.total_validations}")
print(f"Successful: {report.successful}")
print(f"Available: {report.available}")
print(f"Waitlisted: {report.waitlisted}")
print(f"Unavailable: {report.unavailable}")
print(f"Success rate: {report.success_rate:.1f}%")
print(f"Availability rate: {report.availability_rate:.1f}%")
print(f"Confidence score: {report.confidence_score:.1f}")

# Save report
validator.save_validation_report(report, "data/validation_report.json")
```

---

## Integration with Route Generation

```python
# When generating routes, use validated trains only

from optimization_engine import RouteOptimizer
from irctc_validator import IRCTCValidator

# Get validated trains
validator = IRCTCValidator()

# Load all trains, filter ACTIVE only
session = db.get_session()
active_trains = session.query(Train).filter(
    Train.status == TrainStatus.ACTIVE
).all()
session.close()

# Generate routes using only active trains
optimizer = RouteOptimizer()
routes = optimizer.generate_routes(
    source="NDLS",
    destination="KOTA",
    date="2026-02-15",
    available_trains=active_trains  # Only ACTIVE trains
)

print(f"Generated {len(routes)} routes")
# All routes guaranteed to have only available trains!
```

---

## Error Handling

```python
from irctc_validator import ValidationStatus

result = validator.validate_train("16320", "2026-02-15")

if result.status == ValidationStatus.VALIDATED:
    print("✓ Validation successful")
    if result.is_available:
        print(f"  Seats available: {result.seats_available}")
    else:
        print("  All seats waitlisted")

elif result.status == ValidationStatus.INVALID:
    print("✗ Train not found on this date")

elif result.status == ValidationStatus.TIMEOUT:
    print("✗ IRCTC API timeout (will retry later)")

elif result.status == ValidationStatus.ERROR:
    print(f"✗ Error: {result.error_message}")

else:
    print(f"? Unknown status: {result.status}")

# Validation time helpful for debugging
print(f"API response time: {result.validation_time_ms}ms")
if result.validation_time_ms > 10000:
    print("⚠ Slow validation - consider checking IRCTC API health")
```

---

## Statistics & Monitoring

```python
# Get current statistics
stats = validator.get_validation_statistics()

print("=== VALIDATION STATISTICS ===")
print(f"Total validations: {stats['total_validations']}")
print(f"Successful: {stats['successful']}")
print(f"Failed: {stats['failed']}")
print(f"Cache hits: {stats['cached']}")
print(f"Cache size: {stats['cache_size']} entries")
print(f"Cache TTL: {stats['cache_ttl_hours']} hours")
print(f"Average time: {stats['avg_time_ms']:.1f}ms")
print(f"Trains marked ACTIVE: {stats['trains_marked_active']}")
print(f"Trains marked INACTIVE: {stats['trains_marked_inactive']}")

# Success rate calculation
if stats['total_validations'] > 0:
    success_rate = stats['successful'] / stats['total_validations'] * 100
    cache_hit_rate = stats['cached'] / stats['total_validations'] * 100
    
    print(f"\nSuccess rate: {success_rate:.1f}%")
    print(f"Cache hit rate: {cache_hit_rate:.1f}%")
```

---

## Scheduling Regular Validation

```python
from scheduler import DataPipelineScheduler

scheduler = DataPipelineScheduler()

# Run validation every 12 hours
# (Already integrated in scheduler!)
scheduler.schedule_validation()

# Check what's scheduled
status = scheduler.get_status()
print(status)
```

---

## Common Scenarios

### Scenario 1: User Searches for Route

```python
# Backend receives: NDLS → KOTA, 2026-02-15

# 1. Check if validation cache exists
validator = IRCTCValidator()
is_active = validator.is_train_active("16320", "2026-02-15")

if is_active is None:
    # Not yet validated
    result = validator.validate_train("16320", "2026-02-15", "NDLS", "KOTA")
elif is_active:
    # Cache says: train is active ✓
    pass
else:
    # Cache says: train is WL/unavailable ✗
    pass

# 2. Include in route generation
# (Only if is_active == True or True)
```

### Scenario 2: Batch Validation Every Night

```python
# Run at 02:00 AM daily
def nightly_validation():
    validator = IRCTCValidator()
    
    # Get all unknown/old trains
    session = db.get_session()
    trains_needing_validation = session.query(Train).filter(
        (Train.status == TrainStatus.UNKNOWN) |
        (Train.last_validated < datetime.now() - timedelta(days=7))
    ).all()
    session.close()
    
    # Validate in batches
    train_dates = [
        (train.train_no, (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"))
        for train in trains_needing_validation
    ]
    
    results = validator.validate_trains_batch(train_dates, max_parallel=5)
    
    # Update all statuses
    for result in results:
        validator.update_train_status_from_validation(result)
    
    # Generate report
    print(f"Validated {len(results)} trains")
    
    # Send alert if many inactive
    inactive = sum(1 for r in results if not r.is_available)
    if inactive / len(results) > 0.2:  # >20% inactive
        # Send alert: many trains inactive today!
        pass
```

### Scenario 3: Debugging a Route Issue

```python
# User says: "Route shows train 16320 but seats are WL on IRCTC"

# Debug:
validator = IRCTCValidator()

# 1. Check cache
result = validator.validate_train("16320", "2026-02-15", "NDLS", "KOTA")
print(f"Cached result: available={result.is_available}, cached={result.cached}")

# 2. Force refresh (clear cache)
validator.clear_cache()
result = validator.validate_train("16320", "2026-02-15", "NDLS", "KOTA")
print(f"Fresh result: available={result.is_available}")

# 3. Check database status
session = validator.db.get_session()
train = session.query(Train).filter_by(train_no="16320").first()
print(f"DB status: {train.status}")
print(f"Last validated: {train.last_validated}")
session.close()

# 4. What went wrong?
if result.error_message:
    print(f"Error: {result.error_message}")
    print(f"Time: {result.validation_time_ms}ms")
    # Maybe IRCTC API was down?
```

---

## Performance Tips

1. **Cache aggressively** - 12 hours is good default
2. **Batch operations** - Validate 5-10 trains in parallel, not sequentially
3. **Validate off-peak** - Run full validation at 2-4 AM to avoid user search time
4. **Monitor API health** - If avg response time >10 seconds, IRCTC API might be slow
5. **Clear old cache** - If memory gets high, can manually clear cache

---

## Troubleshooting

**Q: "Validation always times out"**
- A: IRCTC API might be down. Check IRCTC website manually.
- A: Network might be slow. Check internet connection.
- A: Try reducing `max_parallel` from 5 to 2

**Q: "Cache never fills"**
- A: Check if you're hitting same (train_no, date) combinations
- A: Can check: `validator.get_validation_statistics()['cache_size']`

**Q: "Routes still show WL trains"**
- A: Status not updated in database. Call `update_train_status_from_validation()`
- A: Status updated but route generator not using status filter. Check `optimization_engine.py`

**Q: "Validation is slow"**
- A: Normal first run: 2-5 seconds per train
- A: Cached results: <1ms
- A: Batch validation: use `max_parallel=5` for speed

---

## File Reference

```
irctc_validator.py          ← Main implementation
├── IRCTCValidator class
├── ValidationResult dataclass
├── TrainValidationReport dataclass
└── ValidationStatus enum

Integration points:
├── irctc_client.py         (API calls)
├── database.py             (Train model)
├── logger.py               (Logging)
└── config.py               (Settings)
```

---

**Last Updated:** 2026-01-25
**Version:** 1.0 Production
**Status:** Ready for integration with route generation engine
