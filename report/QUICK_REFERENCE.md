# Quick Reference Card

## Running Tests

```bash
# Everything (all 5 layers)
python run_tests.py
python test_master_orchestrator.py

# Individual layers
python test_layer1_dataset_validation.py
python test_layer2_ingestion.py
python test_layer3_live_reality.py
python test_layer4_routing.py
python test_layer5_stress.py

# Specific layer only
python test_master_orchestrator.py --only-layer 1

# Skip layer
python test_master_orchestrator.py --skip-layer 3

# Performance monitoring
python performance_monitor.py
```

## Test Results

```
✅ PASS   → System ready for production
⚠️ WARN   → Fix warnings before deployment  
❌ FAIL   → Critical issues, do NOT deploy
```

## Performance Targets

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| P50 Response | <100ms | >200ms | >500ms |
| P95 Response | <200ms | >300ms | >1000ms |
| P99 Response | <500ms | >1000ms | >2000ms |
| Success Rate | >99% | <98% | <95% |
| Cache Hit Rate | >50% | <30% | <10% |
| CPU Utilization | <70% | >75% | >85% |
| Memory Utilization | <80% | >85% | >90% |
| API Errors | <0.1% | >1% | >5% |
| Data Freshness | <30min | >60min | >120min |
| Data Accuracy | >98% | <95% | <90% |

## File Structure

```
route-master-final/
├── test_layer1_dataset_validation.py   [472 lines]
├── test_layer2_ingestion.py            [451 lines]
├── test_layer3_live_reality.py         [528 lines]
├── test_layer4_routing.py              [486 lines]
├── test_layer5_stress.py               [421 lines]
├── test_master_orchestrator.py         [432 lines]
├── performance_monitor.py              [586 lines]
├── run_tests.py                        [Quick start script]
├── test_config.ini                     [Configuration]
├── TESTING_GUIDE.md                    [Full documentation]
├── TESTING_IMPLEMENTATION_SUMMARY.md   [Implementation details]
└── QUICK_REFERENCE.md                  [This file]
```

## Key Test Concepts

### Layer 1: Data Quality
- Dataset is clean, complete, valid
- No duplicates, no corruption
- All fields have correct types
- Business logic constraints met

### Layer 2: Ingestion Reliability
- RAPPID API fetches work correctly
- Cache prevents re-fetches
- No data loss or corruption
- Error handling works

### Layer 3: Real-World Accuracy
- Your data matches IRCTC
- Station sequences correct
- Times are accurate
- No invented data

### Layer 4: Routing Works
- Routes generate correctly
- Seats are available
- Booking flows work
- Multi-leg journeys valid

### Layer 5: Production Ready
- Handles 1000+ concurrent requests
- Recovers from failures
- No data loss on restart
- Performance meets targets

## Reports Generated

After each test run:
- `test_layer1_report.json`
- `test_layer2_report.json`
- `test_layer3_report.json`
- `test_layer4_report.json`
- `test_layer5_report.json`
- `test_master_report.json`
- `performance_metrics.json`

## Optimization Quick Actions

| Issue | Quick Fix |
|-------|-----------|
| High P99 latency | `↑ cache_size` |
| Low cache hit | `↑ cache_ttl` or `↑ cache_size` |
| High CPU | `↑ worker_threads` |
| High memory | `↓ cache_size` or optimize queries |
| Stale data | `↓ refresh_interval` |
| DB slow | Add indexes, optimize queries |

## Common Commands

```bash
# Run and show only pass/fail
python test_master_orchestrator.py 2>&1 | grep -E "PASS|FAIL|WARN"

# Run Layer 1 and save output
python test_layer1_dataset_validation.py | tee layer1.log

# Check report status
cat test_master_report.json | grep -i "overall_status"

# View all issues
cat test_master_report.json | grep -i "issues" | head -20

# Performance summary
cat performance_metrics.json | python -m json.tool | head -40

# Run with timing
time python test_master_orchestrator.py
```

## Success Indicators

✅ All layers PASS
✅ P99 response < 500ms  
✅ Cache hit rate > 50%
✅ API success > 99%
✅ Zero data loss
✅ Data matches IRCTC (Layer 3)
✅ No duplicates found
✅ No corruption detected

## When to Retest

- After code changes
- Before deployment
- Weekly for production monitoring
- After infrastructure changes
- When performance degrades
- Before major announcements

## Interpretation Guide

### Dataset Validation (Layer 1)
```
PASS = Clean dataset, safe to use
FAIL = Data quality issues, fix before continuing
```

### Ingestion Testing (Layer 2)
```
PASS = Reliable data fetching, can trust RAPPID pipeline
FAIL = Fetching issues, fix API integration
```

### Live Reality (Layer 3)
```
PASS = Your data matches IRCTC (verified real)
FAIL = Data mismatch with reality, reconcile
```

### Routing Test (Layer 4)
```
PASS = Routes work, bookings will succeed
FAIL = Routing logic broken, fix algorithm
```

### Stress Test (Layer 5)
```
PASS = Production ready, handles load
FAIL = Performance issues, optimize before launch
```

## Exit Codes

```
0 = PASS (all tests successful)
1 = WARN (some tests had warnings)
2 = FAIL (critical failures)
```

## Performance Optimization Workflow

1. **Collect Metrics**
   ```bash
   python performance_monitor.py
   ```

2. **Review Recommendations**
   Check `performance_metrics.json` for suggestions

3. **Implement Changes**
   Update config in `test_config.ini`

4. **Verify Improvement**
   ```bash
   python test_master_orchestrator.py
   python performance_monitor.py
   ```

5. **Monitor Over Time**
   Run nightly tests to track trends

## Troubleshooting Quick Guide

| Problem | Check | Fix |
|---------|-------|-----|
| Layer 1 FAIL | Dataset CSV format | Ensure UTF-8, valid headers |
| Layer 2 FAIL | RAPPID API | Check credentials, rate limits |
| Layer 3 FAIL | Train data mismatch | Reconcile with IRCTC |
| Layer 4 FAIL | Routing logic | Debug algorithm |
| Layer 5 FAIL | Performance | Run optimization |

## Team Workflow

```
Developer
  ↓
Run: python run_tests.py
  ↓
All PASS? ─NO→ Fix issues, retry
  ↓ YES
Code Review
  ↓
Merge to develop
  ↓
CI/CD: Automated tests
  ↓
All PASS? ─NO→ Rollback
  ↓ YES
Deploy to staging
  ↓
Manual testing
  ↓
Deploy to production
```

## Documentation Map

- **Getting Started** → TESTING_GUIDE.md
- **Implementation Details** → TESTING_IMPLEMENTATION_SUMMARY.md
- **Configuration** → test_config.ini
- **Quick Reference** → This file

## Contact Points

- 📧 Check test reports for detailed errors
- 📊 View performance_metrics.json for optimization tips
- 📚 See TESTING_GUIDE.md for comprehensive info
- 🔧 Adjust test_config.ini for your needs

---

**Quick Start**: `python run_tests.py`

**Status**: Production Ready ✅

**Last Updated**: January 25, 2026
