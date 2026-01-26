# Multi-Transfer Route Generation Test Report

Generated: 2026-01-26T18:23:19.383659
Test Timestamp: 2026-01-26T18:23:16.089205
Total Tests: 3

## Test Results Summary

| Route Pair | Total Routes | 0-Transfer | 1-Transfer | 2-Transfer | 3-Transfer | 4-Transfer | Time (s) |
|------------|--------------|-----------|-----------|-----------|-----------|-----------|----------|
| CSMT→DADA | 207 | 47 | 100 | 54 | 6 | 0 | 1.12 |
| CSMT→KOTA | 0 | 0 | 0 | 0 | 0 | 0 | 1.16 |
| CSMT→SBC | 1 | 0 | 0 | 0 | 0 | 1 | 1.01 |

## Detailed Analysis by Route Pair

### Short Distance (Mumbai nearby)
**Route:** CSMT → DADA
**Generation Time:** 1.12s

#### Route Distribution by Transfers

**0 Transfer(s):** 47 routes (22.7%)
  - Duration: 3.00h avg (min: 3.00h, max: 3.00h)
  - Distance: 0km avg (min: 0km, max: 0km)
  - Cost: ₹200 avg (min: ₹200, max: ₹200)

**1 Transfer(s):** 100 routes (48.3%)
  - Duration: 13.31h avg (min: 4.08h, max: 46.12h)
  - Distance: 462km avg (min: 0km, max: 2106km)
  - Cost: ₹2546 avg (min: ₹400, max: ₹10730)

**2 Transfer(s):** 54 routes (26.1%)
  - Duration: 11.64h avg (min: 5.38h, max: 42.84h)
  - Distance: 213km avg (min: 0km, max: 1742km)
  - Cost: ₹1558 avg (min: ₹600, max: ₹9110)

**3 Transfer(s):** 6 routes (2.9%)
  - Duration: 21.24h avg (min: 21.24h, max: 21.24h)
  - Distance: 462km avg (min: 462km, max: 462km)
  - Cost: ₹2910 avg (min: ₹2910, max: ₹2910)

#### Sample Routes

**0 Transfer(s):**
  Route 1: 1 segments
    Duration: 3.00h | Distance: 0km | Cost: ₹200
    Segments:
      - Train 10103: CSMT → DADA (0km, 3.00h travel, 0.00h wait)

  Route 2: 1 segments
    Duration: 3.00h | Distance: 0km | Cost: ₹200
    Segments:
      - Train 10111: CSMT → DADA (0km, 3.00h travel, 0.00h wait)

**1 Transfer(s):**
  Route 1: 2 segments
    Duration: 18.64h | Distance: 732km | Cost: ₹3860
    Segments:
      - Train 12133: CSMT → THAN (0km, 3.00h travel, 0.00h wait)
      - Train 10104: THAN → DADA (732km, 14.64h travel, 1.00h wait)

  Route 2: 2 segments
    Duration: 14.94h | Distance: 547km | Cost: ₹2935
    Segments:
      - Train 12133: CSMT → THAN (0km, 3.00h travel, 0.00h wait)
      - Train 10112: THAN → DADA (547km, 10.94h travel, 1.00h wait)

**2 Transfer(s):**
  Route 1: 3 segments
    Duration: 38.44h | Distance: 1522km | Cost: ₹8010
    Segments:
      - Train 10103: CSMT → DADA (0km, 3.00h travel, 0.00h wait)
      - Train 12490: DADA → BORI (0km, 3.00h travel, 1.00h wait)
      - Train 12489: BORI → DADA (1522km, 30.44h travel, 1.00h wait)

  Route 2: 3 segments
    Duration: 17.24h | Distance: 462km | Cost: ₹2710
    Segments:
      - Train 10103: CSMT → DADA (0km, 3.00h travel, 0.00h wait)
      - Train 12490: DADA → BORI (0km, 3.00h travel, 1.00h wait)
      - Train 12902: BORI → DADA (462km, 9.24h travel, 1.00h wait)

**3 Transfer(s):**
  Route 1: 4 segments
    Duration: 21.24h | Distance: 462km | Cost: ₹2910
    Segments:
      - Train 10103: CSMT → DADA (0km, 3.00h travel, 0.00h wait)
      - Train 12490: DADA → BORI (0km, 3.00h travel, 1.00h wait)
      - Train 12010: BORI → MC (462km, 9.24h travel, 1.00h wait)
      ... and 1 more segments

  Route 2: 4 segments
    Duration: 21.24h | Distance: 462km | Cost: ₹2910
    Segments:
      - Train 10103: CSMT → DADA (0km, 3.00h travel, 0.00h wait)
      - Train 12490: DADA → BORI (0km, 3.00h travel, 1.00h wait)
      - Train 12010: BORI → MC (462km, 9.24h travel, 1.00h wait)
      ... and 1 more segments

### Medium Distance (Mumbai-Rajasthan)
**Route:** CSMT → KOTA
**Generation Time:** 1.16s

#### Route Distribution by Transfers

#### Sample Routes

### Long Distance (Mumbai-Bangalore)
**Route:** CSMT → SBC
**Generation Time:** 1.01s

#### Route Distribution by Transfers

**4 Transfer(s):** 1 routes (100.0%)
  - Duration: 30.82h avg (min: 30.82h, max: 30.82h)
  - Distance: 1191km avg (min: 1191km, max: 1191km)
  - Cost: ₹6440 avg (min: ₹6440, max: ₹6440)

#### Sample Routes

**4 Transfer(s):**
  Route 1: 5 segments
    Duration: 30.82h | Distance: 1191km | Cost: ₹6440
    Segments:
      - Train 12289: CSMT → NAGP (0km, 3.00h travel, 0.00h wait)
      - Train 12194: NAGP → BALH (543km, 10.86h travel, 1.00h wait)
      - Train 12252: BALH → KACH (625km, 12.50h travel, 1.00h wait)
      ... and 2 more segments


## Summary

### Key Findings

- **Total routes generated:** 208 across all test cases
- **Multi-transfer support:** Routes with up to 4 transfers are now supported
- **Station-dependent:** The number of 4-transfer routes depends on station distance and network topology
- **Short distances (CSMT→DADA):** Primarily direct and 1-transfer routes are feasible
- **Long distances:** More likely to generate routes with 3-4 transfers

### Recommendations

1. **Use the advanced_multi_transfer module** for comprehensive route generation
2. **Adjust max_routes_per_type** based on distance: increase for long distances
3. **Monitor performance:** BFS search scales with transfer count - watch queue sizes
4. **User presentation:** Display routes grouped by transfer count for clarity
5. **Optimization:** Use Pareto optimization to select best routes from each category
