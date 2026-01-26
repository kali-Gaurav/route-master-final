# System Architecture & Data Flow

## Complete Testing Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                    ROUTE MASTER TESTING SYSTEM                       │
│                       (Complete Implementation)                       │
└──────────────────────────────────────────────────────────────────────┘

                         ┌─────────────────┐
                         │  run_tests.py   │
                         │ (Quick Start)   │
                         └────────┬────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │  test_master_orchestrator │
                    │   (Main Test Runner)      │
                    └─────────────┬─────────────┘
                                  │
         ┌────────────┬───────────┼───────────┬────────────┐
         │            │           │           │            │
    ┌────▼───┐  ┌─────▼────┐ ┌──▼───┐  ┌───▼─────┐  ┌───▼──────┐
    │ Layer  │  │  Layer   │ │Layer │  │ Layer   │  │  Layer   │
    │   1    │  │    2     │ │  3   │  │    4    │  │    5     │
    │Dataset │  │Ingestion │ │Reality│ │Routing  │  │Stress &  │
    │Validation│ │Testing   │ │Testing│ │Testing  │  │Reliability│
    └────┬───┘  └─────┬────┘ └──┬───┘  └───┬─────┘  └───┬──────┘
         │            │         │          │            │
         └────────────┼─────────┼──────────┼────────────┘
                      │
                ┌─────▼──────────┐
                │  Report        │
                │  Generation    │
                └─────┬──────────┘
                      │
        ┌─────────────┴──────────────┐
        │                            │
   ┌────▼────────┐          ┌────────▼────┐
   │ Master      │          │Performance  │
   │ Report JSON │          │ Metrics JSON│
   └─────────────┘          └──────┬──────┘
                                   │
                          ┌────────▼─────────┐
                          │performance_      │
                          │monitor.py        │
                          │(Optimization)    │
                          └──────────────────┘
```

## Test Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER RUNS: python run_tests.py             │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │ test_master_orchestrator.py      │
        │ Orchestrates all 5 layers        │
        └──────────────┬───────────────────┘
                       │
        ┌──────────────▼──────────────┐
        │ LAYER 1: Dataset Validation │
        │ Check: Clean & valid data   │
        └──────────────┬──────────────┘
                       │
                 Pass? ├─No──► FAIL & STOP
                       │
                 Yes   ▼
        ┌──────────────────────────────┐
        │ LAYER 2: Ingestion Testing   │
        │ Check: Reliable fetching     │
        └──────────────┬───────────────┘
                       │
                 Pass? ├─No──► WARN
                       │
                 Yes   ▼
        ┌──────────────────────────────┐
        │ LAYER 3: Live Reality Test   │
        │ Check: Real-world accuracy   │
        └──────────────┬───────────────┘
                       │
                 Pass? ├─No──► WARN
                       │
                 Yes   ▼
        ┌──────────────────────────────┐
        │ LAYER 4: Routing Test        │
        │ Check: Routing engine works  │
        └──────────────┬───────────────┘
                       │
                 Pass? ├─No──► WARN
                       │
                 Yes   ▼
        ┌──────────────────────────────┐
        │ LAYER 5: Stress & Reliability│
        │ Check: Handles load & fails  │
        └──────────────┬───────────────┘
                       │
                 Pass? ├─No──► WARN
                       │
                 Yes   ▼
        ┌──────────────────────────────┐
        │ ✅ ALL TESTS PASSED          │
        │ SYSTEM PRODUCTION READY      │
        └──────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │ Generate Reports                 │
        │ - Master report (JSON)           │
        │ - Layer reports (JSON)           │
        │ - Performance metrics (JSON)     │
        └──────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │ Show Results & Recommendations   │
        └──────────────────────────────────┘
```

## Data Validation Flow (Layer 1)

```
                    ┌─────────────┐
                    │ CSV Dataset │
                    │ (5000+ rows)│
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼───┐      ┌──────▼────┐     ┌────▼────┐
    │Schema  │      │   Type    │     │Duplicate│
    │Validate│      │ Validation│     │Detection│
    └────┬───┘      └──────┬────┘     └────┬────┘
         │                 │              │
         └─────────────────┼──────────────┘
                           │
                ┌──────────▼──────────┐
                │ Logical Constraints │
                │ (src ≠ dest, times) │
                └──────────┬──────────┘
                           │
                ┌──────────▼──────────┐
                │ Station Sequences   │
                │ Time Formats        │
                └──────────┬──────────┘
                           │
                 ┌─────────▼────────┐
                 │ Results: Pass/Fail│
                 └────────┬─────────┘
                          │
                ┌─────────▼───────────┐
                │Report Generation    │
                │(JSON with details)  │
                └─────────────────────┘
```

## Ingestion Testing Flow (Layer 2)

```
            ┌──────────────────┐
            │ RAPPID API       │
            │ (Real Railway DB)│
            └────────┬─────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
    ┌────▼──┐   ┌───▼────┐  ┌──▼─────┐
    │Single │   │ Batch  │  │Invalid  │
    │Train  │   │ 10     │  │ Trains  │
    │Fetch  │   │ Trains │  │ (Error  │
    │       │   │        │  │ Handling)
    └────┬──┘   └───┬────┘  └──┬─────┘
         │          │          │
         └────┬─────┴──────────┘
              │
         ┌────▼─────────────┐
         │ Cache Behavior   │
         │ (Hit/Miss Test)  │
         └────┬─────────────┘
              │
         ┌────▼──────────────┐
         │Data Corruption    │
         │Detection(Checksums)
         └────┬──────────────┘
              │
         ┌────▼──────────────┐
         │Refetch Prevention │
         │ (Loop Detection)  │
         └────┬──────────────┘
              │
         ┌────▼──────────────┐
         │Results: Pass/Fail │
         └────┬──────────────┘
              │
         ┌────▼──────────────┐
         │Report Generation  │
         └───────────────────┘
```

## Routing Testing Flow (Layer 4)

```
        ┌─────────────────────────┐
        │ Search Parameters       │
        │ - Origin/Destination    │
        │ - Travel Date           │
        │ - Preferences           │
        └────────────┬────────────┘
                     │
        ┌────────────▼─────────────┐
        │ Route Generation Engine  │
        │ Creates possible routes  │
        └────────────┬─────────────┘
                     │
        ┌────────────▼──────────────┐
        │ Validate Route            │
        │ - Sequence              │
        │ - Duration              │
        │ - Connections           │
        └────────────┬──────────────┘
                     │
        ┌────────────▼──────────────┐
        │ Check Seat Availability  │
        │ - Get live inventory     │
        │ - Filter WL (waitlist)   │
        │ - Confirm pricing        │
        └────────────┬──────────────┘
                     │
        ┌────────────▼──────────────┐
        │ Booking Simulation       │
        │ - Create booking         │
        │ - Process payment        │
        │ - Generate PNR           │
        └────────────┬──────────────┘
                     │
        ┌────────────▼──────────────┐
        │ Results: Pass/Fail       │
        └────────────┬──────────────┘
                     │
        ┌────────────▼──────────────┐
        │ Report Generation        │
        └──────────────────────────┘
```

## Performance Monitoring Loop

```
┌─────────────────────────────────┐
│ System Running (Production)     │
└────────────┬────────────────────┘
             │
    ┌────────▼────────────┐
    │ Collect Metrics     │
    │ - Every 60 seconds  │
    │ - 20+ metrics       │
    └────────┬────────────┘
             │
    ┌────────▼────────────┐
    │ Analyze Performance │
    │ Check vs Thresholds │
    │ - EXCELLENT         │
    │ - GOOD              │
    │ - WARNING           │
    │ - CRITICAL          │
    └────────┬────────────┘
             │
    ┌────────▼────────────┐
    │ Issues Found?       │
    └────┬────────┬───────┘
         │        │
      NO │        │ YES
         │    ┌───▼──────────────────┐
         │    │ Generate Recs        │
         │    │ - Specific actions   │
         │    │ - Expected improvement
         │    │ - Implementation time
         │    └───┬──────────────────┘
         │        │
         │    ┌───▼──────────────────┐
         │    │ Optional Auto-Tune   │
         │    │ - Adjust cache       │
         │    │ - Scale workers      │
         │    │ - Update TTL         │
         │    └───┬──────────────────┘
         │        │
         └────┬───┘
              │
       ┌──────▼─────────┐
       │ Save Report    │
       │ (JSON)         │
       └──────┬─────────┘
              │
              ▼
       ┌──────────────┐
       │ Alert if     │
       │ Critical     │
       └──────┬───────┘
              │
              ▼
       ┌──────────────────┐
       │ Continue Loop    │
       │ (60 seconds)     │
       └──────────────────┘
```

## System Integration Points

```
┌────────────────────────────────────────────────────────────┐
│                 Route Master Platform                      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────┐         ┌──────────────┐               │
│  │ API Layer    │         │Database      │               │
│  │              │         │              │               │
│  │ /search      │────┬────│ trains       │               │
│  │ /routes      │    │    │ stations     │               │
│  │ /book        │    │    │ schedules    │               │
│  └──────────────┘    │    └──────────────┘               │
│                      │                                    │
│  ┌──────────────┐    │    ┌──────────────┐               │
│  │Cache Layer   │◄───┴───►│RAPPID API    │               │
│  │              │         │Client        │               │
│  │ Redis/Memory │         │              │               │
│  └──────────────┘         └──────────────┘               │
│        ▲                                                  │
│        │                                                  │
│        └────────────────────────────────────┐             │
│                                             │             │
│  ┌──────────────┐        ┌────────────────▼─┐           │
│  │Test System   │        │Performance       │           │
│  │(5 Layers)    │───────►│Monitor & Tuner   │           │
│  │              │        │                  │           │
│  └──────────────┘        └──────────────────┘           │
│                                                          │
└────────────────────────────────────────────────────────────┘
```

## Report Structure

```
test_master_report.json
│
├── timestamp
├── overall_status (PASS/WARN/FAIL)
├── layers_tested (1-5)
├── layers_passed
├── layers_failed
├── total_duration_seconds
│
├── layer_results
│   ├── Layer 1
│   │   ├── name: "Dataset Validation"
│   │   ├── status: "PASS"
│   │   ├── duration_seconds
│   │   └── issues
│   │
│   ├── Layer 2
│   │   ├── name: "Ingestion Testing"
│   │   ├── status: "PASS"
│   │   ├── cache_hit_rate
│   │   └── ...
│   │
│   └── ... (Layers 3, 4, 5)
│
├── critical_issues []
└── recommendations []
```

## Performance Metrics Hierarchy

```
                    ┌─────────────┐
                    │System Health│
                    │(Overall)    │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
    ┌───▼────┐        ┌────▼────┐       ┌───▼───┐
    │API      │        │Data     │       │System │
    │Performance │        │Pipeline │       │Resources
    │            │        │         │       │
    ├─P50       ├──────┼─Freshness┼──────┼─CPU
    ├─P95       ├───Accuracy         ├─Memory
    ├─P99       ├──Latency           ├─Disk
    ├─Success % ├─Integrity          ├─Network
    └─Throughput┘                    └─Load
```

---

**Visual Architecture Complete** ✅

All diagrams and flows documented above.

For detailed information, see the TESTING_GUIDE.md file.
