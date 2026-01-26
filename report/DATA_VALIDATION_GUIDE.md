# Train Data Quality Validation System

## Overview

This document describes the **production-grade data quality validation system** for the train routing engine. This system enforces 10 deterministic data quality tests that protect your routing engine from corruption by automatically removing records that fail critical railway constraints.

**Golden Rule**: It is always better to lose 5% of data than corrupt 0.1% of routes.

---

## Validation Architecture

### Level 1: Critical Tests (Hard Fail → Delete Row)

If a row fails **ANY** of these 7 tests, it is **immediately removed**.

These tests protect the routing engine from corruption.

| Test | Rule | Action on Failure |
|------|------|-------------------|
| **Test 1: Train Number Validity** | Train No must be numeric and between 1-99999 | DELETE ROW |
| **Test 2: Station Code Validity** | Station Code must be 2-5 chars, A-Z/digits only, NOT numeric-only | DELETE ROW |
| **Test 3: Sequence Number (SEQ)** | SEQ must be numeric integer >= 1 | DELETE ROW |
| **Test 4: Time Format** | Arrival/Departure must be HH:MM:SS format | DELETE ROW |
| **Test 5: Distance Validity** | Distance must be numeric, >= 0, <= 5000 | DELETE ROW |
| **Test 6: Distance Monotonic** | Distance must be strictly increasing within same train | DELETE ROW |
| **Test 7: Source/Destination & First/Last Logic** | Same source/destination per train; SEQ=1→distance=0; last→departure=00:00:00 | DELETE ROW |

### Level 2: Soft Tests (Warning Only → Keep Row)

These tests do **NOT** delete rows, only log warnings.

| Test | Rule | Action on Failure |
|------|------|-------------------|
| **Test 8: Station Name Length** | Station Name length >= 3 chars | WARN only |
| **Test 9: Train Name Length** | Train Name length >= 3 chars | WARN only |
| **Test 10: Time Ordering** | Arrival time <= Departure time (except overnight cases) | WARN only |

---

## Test Details

### Critical Tests

#### Test 1: Train Number Validity

**Rule**: Train number must be:
- Numeric (not text like "K", "ABC")
- In range [1, 99999]
- Not NULL

**Examples**:
- ✅ PASS: 107, 108, 16320
- ❌ FAIL: "K", "ABC", null, 0, 100000

**Why**: Invalid train numbers break the routing graph and cause route lookup failures.

---

#### Test 2: Station Code Validity

**Rule**: Station code must be:
- Length: 2-5 characters
- Characters: Only A-Z (uppercase) and 0-9 (digits)
- NOT numeric-only (e.g., "214" fails)

**Examples**:
- ✅ PASS: SWV, KRMI, THVM, MAO (2-5 chars, A-Z/digits)
- ❌ FAIL: "214" (numeric-only), "3" (too short), "R" (too short), "@SW" (invalid char), "" (empty)

**Why**: Station codes are database keys. Invalid codes corrupt the graph.

---

#### Test 3: Sequence Number (SEQ)

**Rule**: SEQ must be:
- Numeric integer (not "12:17:00", not "ABC")
- >= 1 (not 0, not -1)

**Examples**:
- ✅ PASS: 1, 2, 3, 4, 100
- ❌ FAIL: "12:17:00" (time format), 0, -1, "ABC"

**Why**: SEQ defines the order of stops. Non-integers or invalid ranges corrupt the stop sequence.

---

#### Test 4: Time Format Validation

**Rule**: Both Arrival and Departure times must be:
- HH:MM:SS format (00:00:00 to 23:59:59)
- Special case: 00:00:00 is allowed ONLY for:
  - First stop arrival (SEQ=1)
  - Last stop departure (end-of-day marker)

**Examples**:
- ✅ PASS: 00:00:00 (first arrival), 10:25:00, 21:06:00, 23:59:59
- ❌ FAIL: "MAO" (station name, not time), "19:00" (wrong format), "7pm" (text), "BIJAPUR JN" (station name)

**Why**: Invalid time formats break time-based routing calculations and overnight journey logic.

---

#### Test 5: Distance Validity

**Rule**: Distance must be:
- Numeric (not text)
- >= 0 (no negative distances)
- <= 5000 (reasonable max distance)

**Examples**:
- ✅ PASS: 0, 32, 49, 78, 1500, 5000
- ❌ FAIL: "BIJAPUR JN" (text), -10 (negative), 6000 (exceeds max), 5001

**Why**: Distance is a metric for routing. Invalid values break distance-based optimization.

---

#### Test 6: Distance Monotonic Increase (Per Train)

**Rule**: For each train, distances must be **strictly increasing**:
```
SEQ 1: 0
SEQ 2: must be > 0
SEQ 3: must be > SEQ 2
...
SEQ n: must be > SEQ (n-1)
```

No equal distances, no decreasing distances.

**Examples**:
- ✅ PASS: 0 → 32 → 49 → 78 (strictly increasing)
- ❌ FAIL: 0 → 32 → 32 → 78 (equal not allowed), 0 → 32 → 25 → 78 (decreasing)

**Why**: Non-monotonic distances indicate data corruption or route reversals, breaking the routing engine.

---

#### Test 7: Source/Destination Consistency & First/Last Logic

**Rule A**: Per-train consistency:
- All rows for the same train must have the **same Source Station**
- All rows for the same train must have the **same Destination Station**

**Example Fail**:
```
Row 1: Train 107, Source = SWV
Row 2: Train 107, Source = MAO  ← INCONSISTENT! FAIL
```

**Rule B**: First and Last Station Logic:
- **First stop (SEQ=1)**: Distance MUST be 0
- **Last stop**: Departure time MUST be 00:00:00 (end-of-day marker)

**Example**:
```
Train 107:
  SEQ 1: distance=0 ✅, departure=10:25:00 ✅
  SEQ 2: distance=32 ✅, departure=11:08:00 ✅
  SEQ 4: distance=78 ✅, departure=00:00:00 ✅ (last departure)
```

**Why**: Inconsistent source/destination indicates corrupted train definitions. Invalid first/last stops break journey start/end logic.

---

### Soft Tests (Non-Blocking)

#### Test 8: Station Name Length

**Rule**: Station Name must be >= 3 characters.

**Action**: Log warning, but keep the row.

---

#### Test 9: Train Name Length

**Rule**: Train Name must be >= 3 characters.

**Action**: Log warning, but keep the row.

---

#### Test 10: Time Ordering

**Rule**: Arrival time should be <= Departure time.

**Exception**: Overnight cases (departure < arrival) are allowed and logged as warnings.

---

## Decision Rule

```python
for each row:
    if row fails ANY critical test:
        DELETE ROW
        Log deletion reason
    else:
        KEEP ROW
        if row fails any soft test:
            Log warning (non-blocking)
```

---

## Validation Report Output

The validator produces:

1. **Train_details_CLEANED.csv**: Cleaned dataset (critical tests passed only)
2. **VALIDATION_REPORT.txt**: Detailed deletion log and statistics

### Sample Report

```
Total rows processed: 186,124
Rows DELETED (critical failures): 47,532 (25.5%)
Rows KEPT (pass critical tests): 138,592 (74.5%)

DELETIONS BY REASON:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Distance 33.0 not > previous 364.0: 1,254 rows
Station Code length invalid: 892 rows
Train No "K" is not numeric: 456 rows
First station distance not 0: 234 rows
...
```

---

## Running the Validator

### Prerequisites
```bash
pip install pandas
```

### Execute
```bash
python validate_train_data.py
```

### Output Files
- `Train_details_CLEANED.csv` — Cleaned dataset
- `VALIDATION_REPORT.txt` — Detailed report

---

## Why This System Is Production-Grade

This validation approach mirrors what:
- **Google Maps** uses before building road networks
- **Uber** uses for route optimization
- **Airline systems** use for flight routing
- **Railway systems** use for safety

It's not just "cleaning CSV". It's:

✅ **Schema Enforcement** — Ensures data types match database expectations  
✅ **Business Logic Validation** — Enforces railway-specific constraints  
✅ **Graph Safety** — Ensures routing engine won't crash or infinite-loop  

---

## Key Principles

### 1. Fail Fast, Fail Hard (Critical Tests)

Any record failing a critical test is **immediately removed**. No exceptions. This prevents:
- Infinite loops in pathfinding
- Wrong route calculations
- Fake availability claims
- Broken optimization algorithms

### 2. Graceful Degradation (Soft Tests)

Soft test failures are logged but don't delete rows. This allows:
- Minor data quality issues to be tracked
- Business teams to decide if action is needed
- No false positives from overly strict rules

### 3. Deterministic, Not Statistical

This system uses:
- ✅ Exact range checks (not histograms)
- ✅ Schema validation (not ML models)
- ✅ Business rule enforcement (not anomaly detection)
- ❌ NOT machine learning
- ❌ NOT guessing

---

## Common Issues & Solutions

### Issue: Many rows deleted due to "Distance not strictly increasing"

**Cause**: Your dataset may have:
- Bidirectional routes (A→B→C→B) mixed in the same train
- Stop sequences that aren't linear

**Solution**: Check your raw data source. This is a valid data quality issue.

### Issue: "Train No X" deleted because non-numeric

**Cause**: Your CSV has garbage data (e.g., "K" instead of "102")

**Solution**: Clean the source before importing, or update data entry procedures.

### Issue: Station Code validation seems strict

**Cause**: Indian railway codes are 2-5 chars, A-Z + digits

**Valid examples**: SWV, MAO, THVM, NDLS, CST

If your data has 1-char codes like "R", it's likely corrupted.

---

## Integration with Routing Engine

```python
# BEFORE: Original dataset (uncleaned)
routes = build_routing_graph('Train_details.csv')  # ❌ Risk of corruption

# AFTER: Use cleaned data
cleaned_data = pd.read_csv('Train_details_CLEANED.csv')
routes = build_routing_graph(cleaned_data)  # ✅ Safe to use
```

---

## Recommended Monitoring

Add this to your data pipeline:

```python
def validate_and_clean(csv_path: str):
    validator = TrainDataValidator(csv_path)
    clean_df, stats = validator.validate()
    
    # Alert if deletion rate exceeds threshold
    if stats['retention_rate'] < 70:
        send_alert(f"Data quality alert: {stats['retention_rate']:.1f}% retained")
    
    # Log for analysis
    log_stats(stats)
    
    return clean_df
```

---

## Test Matrix Reference

For documentation and auditing:

| # | Test Name | Type | Input | Output |
|---|-----------|------|-------|--------|
| 1 | Train No numeric | Critical | Train No | DELETE or KEEP |
| 2 | Station Code format | Critical | Station Code | DELETE or KEEP |
| 3 | SEQ numeric | Critical | SEQ | DELETE or KEEP |
| 4 | Time HH:MM:SS | Critical | Arrival, Departure | DELETE or KEEP |
| 5 | Distance numeric | Critical | Distance | DELETE or KEEP |
| 6 | Distance monotonic | Critical | Distance per train | DELETE or KEEP |
| 7 | Source/Dest consistency | Critical | Source, Destination | DELETE or KEEP |
| 8 | Station name length | Soft | Station Name | WARN or KEEP |
| 9 | Train name length | Soft | Train Name | WARN or KEEP |
| 10 | Time ordering | Soft | Arrival, Departure | WARN or KEEP |

---

## One-Liner for Reports

> Our system enforces 10 deterministic data quality tests. Any record failing critical railway constraints is automatically removed before entering the routing engine.

---

## Version History

- **v1.0** (2026-01-25): Initial production release
  - 7 critical tests
  - 3 soft tests
  - Deterministic validation only
  - No ML/guessing

---

## Support

For issues or questions about validation rules:
1. Check the test details above
2. Review the deletion log in `VALIDATION_REPORT.txt`
3. Examine sample deleted rows for patterns
4. Escalate to data governance team if systematic issues found
