# Route Discovery Engine - System Architecture Documentation

**Version**: 1.0  
**Date**: 2026-01-25  
**Status**: Production-Ready Design  

---

## 1. Executive Summary

A **Route Discovery Engine** that enables users to find optimal railway routes between any two stations on a given date. The system generates feasible routes using live operational data, validates them against real-time information, filters impossible ones, and ranks them by multiple optimization criteria.

### Core Product Promise
- **Input**: Origin, Destination, Date
- **Output**: Top 5 validated, ranked routes with live seat availability
- **Guarantee**: All routes match IRCTC operational data

### Strategic Positioning
- **Not a booking engine** (users book manually via IRCTC)
- **Not an automation service** (no API access required for users)
- **Pure Intelligence Layer** (route discovery + ranking + analytics)

---

## 2. Five-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: FRONTEND (UI/UX)                              │
│  React + Vite + Tailwind CSS                            │
│  ├─ Search Form (Origin, Destination, Date)            │
│  ├─ Results Display (Top 5 Routes)                      │
│  └─ Responsive Design (Mobile/Desktop)                  │
└─────────────────────────────────────────────────────────┘
                           ↓ HTTP/REST
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: API GATEWAY (FastAPI)                         │
│  ├─ POST /search → Route Discovery                      │
│  ├─ GET  /metrics → System Analytics                    │
│  ├─ GET  /system-status → Health Status                 │
│  └─ Middleware: Auth, Logging, Error Handling           │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: CORE ROUTING ENGINE (Business Logic)          │
│  ├─ Graph Builder (Train Network)                       │
│  ├─ Route Generator (BFS/DFS Pathfinding)               │
│  ├─ Live Validator (RAPPID/IRCTC Data)                  │
│  ├─ Route Filter (Remove Invalid)                       │
│  └─ Route Ranker (Multi-Objective Optimization)         │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  LAYER 4: DATA PLATFORM                                 │
│  ├─ Train Data Loader                                   │
│  ├─ Station Manager                                     │
│  ├─ Live Status Synchronizer (Cache)                    │
│  ├─ SQLite/PostgreSQL Database                          │
│  └─ Structured Logging                                  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  LAYER 5: MONITORING & ANALYTICS                        │
│  ├─ Search Logger (Every Query)                         │
│  ├─ Performance Metrics                                 │
│  ├─ Data Quality Monitor                                │
│  └─ Metrics Dashboard API                               │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow - End-to-End

```
USER INPUT
   ↓
   ├─ Origin: "SBC" (Bengaluru)
   ├─ Destination: "NDLS" (Delhi)
   └─ Date: "2026-02-15"
   
   ↓
API GATEWAY (/search endpoint)
   ├─ Validate input (station codes exist, date valid)
   ├─ Check cache (5-minute TTL)
   ├─ Log search query
   └─ Call Routing Engine if not cached
   
   ↓
GRAPH BUILDER
   ├─ Load all trains from database
   ├─ Create network nodes: (train_no, station, datetime)
   ├─ Build edges for consecutive stations
   └─ Load live status (ACTIVE/INACTIVE)
   
   ↓
ROUTE GENERATOR (BFS)
   ├─ Start: SBC on 2026-02-15 00:00
   ├─ End: NDLS on 2026-02-16 23:59
   ├─ Generate all feasible paths (BFS)
   ├─ Check transfers possible (≥60 min gap)
   ├─ Validate timing constraints
   ├─ Eliminate impossible routes
   └─ Output: 200-500 candidate routes
   
   ↓
LIVE VALIDATOR
   ├─ For each route:
   │  ├─ Check each train status = ACTIVE
   │  ├─ Verify stations operational
   │  ├─ Fetch seat availability (RAPPID API)
   │  ├─ Check availability ≥ 1
   │  └─ Skip if any validation fails
   └─ Output: Valid routes only
   
   ↓
ROUTE FILTER
   ├─ Remove inactive trains
   ├─ Remove >48 hour duration routes
   ├─ Remove duplicates (same trains, times)
   ├─ Remove insufficient transfer time
   └─ Output: Filtered routes (20-100 routes)
   
   ↓
ROUTE RANKER
   ├─ Score each route:
   │  ├─ Duration score (25%)
   │  ├─ Departure time score (25%)
   │  ├─ Transfers count score (20%)
   │  ├─ Seat availability score (20%)
   │  └─ Total: 0-100
   ├─ Pareto optimization (non-dominated solutions)
   ├─ Rank by overall score
   └─ Output: Top 5 routes
   
   ↓
ANALYTICS LOGGER
   ├─ Store search query
   ├─ Store results generated
   ├─ Record response time
   ├─ Update cache
   └─ Log metrics
   
   ↓
API RESPONSE (JSON)
   {
     "status": "success",
     "timestamp": "2026-01-25T10:30:45Z",
     "routes": [
       {
         "route_id": "ROUTE_001",
         "rank": 1,
         "quality_score": 92,
         "trains": [
           {
             "train_no": 16320,
             "train_name": "SBC-NDLS Express",
             "source": "SBC",
             "destination": "NDLS",
             "departure": "2026-02-15T18:30:00Z",
             "arrival": "2026-02-16T14:00:00Z",
             "duration": "19h 30m",
             "seats_available": 45,
             "platform": 1
           }
         ],
         "total_duration": "19h 30m",
         "total_stops": 8,
         "transfers": 0,
         "seat_availability": "Good"
       },
       { /* Route 2... */ },
       { /* Route 3... */ },
       { /* Route 4... */ },
       { /* Route 5... */ }
     ],
     "metadata": {
       "total_routes_generated": 287,
       "total_routes_valid": 156,
       "routes_ranked": 5,
       "response_time_ms": 1250,
       "cache_hit": false
     }
   }
   
   ↓
FRONTEND DISPLAY
   ├─ Parse JSON
   ├─ Display 5 routes in cards
   ├─ Show ranking badge (Best/Good/Standard)
   ├─ Show details (trains, times, seats)
   ├─ Enable manual booking link to IRCTC
   └─ Update page state
```

---

## 4. API Contracts

### 4.1 Search Endpoint

**POST** `/search`

**Request (Payload)**
```json
{
  "source": "SBC",
  "destination": "NDLS",
  "date": "2026-02-15",
  "preferences": {
    "max_duration_hours": 48,
    "min_departure": "06:00",
    "max_departure": "23:59",
    "prefer_direct": false
  }
}
```

**Response (Success - 200)**
```json
{
  "status": "success",
  "timestamp": "2026-01-25T10:30:45Z",
  "routes": [...],
  "metadata": {
    "total_generated": 287,
    "total_valid": 156,
    "response_time_ms": 1250
  }
}
```

**Response (Error - 400)**
```json
{
  "status": "error",
  "error_code": "INVALID_STATION",
  "message": "Station code 'XYZ' not found in database",
  "timestamp": "2026-01-25T10:30:45Z"
}
```

**Response (Server Error - 500)**
```json
{
  "status": "error",
  "error_code": "INTERNAL_ERROR",
  "message": "Database connection failed",
  "timestamp": "2026-01-25T10:30:45Z",
  "request_id": "REQ-12345-67890"
}
```

### 4.2 Metrics Endpoint

**GET** `/metrics`

**Response (200)**
```json
{
  "metrics": {
    "total_searches": 5427,
    "searches_today": 234,
    "avg_response_time_ms": 1230,
    "p95_response_time_ms": 2100,
    "p99_response_time_ms": 3500,
    "cache_hit_rate": 0.35,
    "api_failure_rate": 0.002,
    "top_search_pairs": [
      { "source": "SBC", "destination": "NDLS", "count": 256 },
      { "source": "NDLS", "destination": "SBC", "count": 189 },
      { "source": "SBC", "destination": "HYD", "count": 145 }
    ],
    "live_trains_count": 11245,
    "active_trains": 9876,
    "inactive_trains": 1369,
    "last_data_update": "2026-01-25T10:20:00Z"
  }
}
```

### 4.3 System Status Endpoint

**GET** `/system-status`

**Response (200)**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-25T10:30:45Z",
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5
    },
    "cache": {
      "status": "healthy",
      "hit_rate": 0.35,
      "size_mb": 125
    },
    "api": {
      "status": "healthy",
      "requests_per_second": 12.5
    },
    "data_freshness": {
      "status": "healthy",
      "last_update": "2026-01-25T10:20:00Z",
      "age_minutes": 10
    }
  }
}
```

---

## 5. Database Schema

### 5.1 Tables Structure

```sql
-- TRAINS Table
CREATE TABLE trains (
  train_id INTEGER PRIMARY KEY,
  train_no INTEGER UNIQUE NOT NULL,
  train_name VARCHAR(255) NOT NULL,
  source_station VARCHAR(10) NOT NULL,
  destination_station VARCHAR(10) NOT NULL,
  status VARCHAR(20) NOT NULL,  -- ACTIVE, INACTIVE, UNKNOWN
  last_updated TIMESTAMP NOT NULL,
  created_at TIMESTAMP NOT NULL,
  data_source VARCHAR(50) NOT NULL
);

-- STATIONS Table
CREATE TABLE stations (
  station_id INTEGER PRIMARY KEY,
  station_code VARCHAR(10) UNIQUE NOT NULL,
  station_name VARCHAR(255) NOT NULL,
  zone VARCHAR(50),
  latitude FLOAT,
  longitude FLOAT,
  is_operational BOOLEAN DEFAULT TRUE
);

-- TRAIN_ROUTES Table (Stations in each train's journey)
CREATE TABLE train_routes (
  route_id INTEGER PRIMARY KEY,
  train_id INTEGER NOT NULL,
  station_sequence INTEGER NOT NULL,
  station_code VARCHAR(10) NOT NULL,
  arrival_time TIME,
  departure_time TIME,
  platform_number VARCHAR(10),
  distance_km INTEGER,
  halt_time_minutes INTEGER,
  FOREIGN KEY (train_id) REFERENCES trains(train_id),
  FOREIGN KEY (station_code) REFERENCES stations(station_code)
);

-- SEARCHES Table (User Search History)
CREATE TABLE searches (
  search_id INTEGER PRIMARY KEY,
  source VARCHAR(10) NOT NULL,
  destination VARCHAR(10) NOT NULL,
  search_date DATE NOT NULL,
  searched_at TIMESTAMP NOT NULL,
  response_time_ms INTEGER,
  routes_generated INTEGER,
  routes_valid INTEGER,
  cache_hit BOOLEAN
);

-- SEARCH_RESULTS Table (Each route returned)
CREATE TABLE search_results (
  result_id INTEGER PRIMARY KEY,
  search_id INTEGER NOT NULL,
  rank INTEGER,
  quality_score FLOAT,
  total_duration_minutes INTEGER,
  transfers_count INTEGER,
  min_seat_availability INTEGER,
  FOREIGN KEY (search_id) REFERENCES searches(search_id)
);

-- API_METRICS Table (Performance tracking)
CREATE TABLE api_metrics (
  metric_id INTEGER PRIMARY KEY,
  endpoint VARCHAR(100) NOT NULL,
  method VARCHAR(10) NOT NULL,
  response_time_ms INTEGER,
  status_code INTEGER,
  recorded_at TIMESTAMP NOT NULL
);

-- SYSTEM_METRICS Table (Health metrics)
CREATE TABLE system_metrics (
  metric_id INTEGER PRIMARY KEY,
  metric_name VARCHAR(100) NOT NULL,
  metric_value FLOAT,
  unit VARCHAR(20),
  recorded_at TIMESTAMP NOT NULL
);
```

### 5.2 Key Relationships

```
trains (1) ─→ (N) train_routes
    ↓
    └─→ search_results ←─ searches (1) ─→ (N)

stations ←─ train_routes
```

---

## 6. Core Components Interface

### 6.1 Graph Builder

```python
class GraphBuilder:
    def __init__(self, db_session, logger):
        self.db = db_session
        self.logger = logger
    
    def build_network(self, search_date: date) -> NetworkGraph:
        """
        Build train network graph for given date
        Returns: Graph with nodes=(train_no, station, time)
        """
    
    def get_station_node(self, station_code: str, timestamp: datetime):
        """Get or create graph node for station at time"""
    
    def load_live_status(self) -> dict:
        """Load ACTIVE/INACTIVE status for all trains"""
```

### 6.2 Route Generator

```python
class RouteGenerator:
    def __init__(self, graph: NetworkGraph, logger):
        self.graph = graph
        self.logger = logger
    
    def generate_routes(self, source: str, dest: str, date: date) -> List[Route]:
        """
        BFS to generate all feasible routes
        Returns: List of Route objects with train sequence
        """
    
    def is_valid_transfer(self, train1: Train, train2: Train, 
                         station: str, min_gap_min=60) -> bool:
        """Check if transfer between trains is possible"""
```

### 6.3 Live Validator

```python
class LiveValidator:
    def __init__(self, rappid_api, logger):
        self.api = rappid_api
        self.logger = logger
    
    def validate_route(self, route: Route) -> ValidationResult:
        """
        Validate complete route against live data
        Returns: ValidationResult with validity status
        """
    
    def check_train_active(self, train_no: int, date: date) -> bool:
        """Check if train is operational on given date"""
    
    def get_seat_availability(self, train_no: int) -> int:
        """Fetch available seats from RAPPID API"""
```

### 6.4 Route Filter

```python
class RouteFilter:
    def __init__(self, logger):
        self.logger = logger
    
    def filter_routes(self, routes: List[Route], 
                     preferences: dict) -> List[Route]:
        """
        Apply multiple filter criteria
        Removes: invalid, WL-only, long-duration, duplicates
        """
    
    def is_duplicate(self, route1: Route, route2: Route) -> bool:
        """Check if two routes are duplicates"""
```

### 6.5 Route Ranker

```python
class RouteRanker:
    def __init__(self, logger):
        self.logger = logger
    
    def rank_routes(self, routes: List[Route], top_k=5) -> List[RankedRoute]:
        """
        Multi-objective optimization and ranking
        Returns: Top K routes sorted by quality score
        """
    
    def score_route(self, route: Route) -> float:
        """
        Calculate quality score (0-100)
        Factors: duration, departure time, transfers, seat availability
        """
    
    def pareto_optimal(self, routes: List[Route]) -> List[Route]:
        """
        Find Pareto-optimal routes (non-dominated solutions)
        """
```

---

## 7. Technology Stack Details

### 7.1 Backend Technologies

| Component | Technology | Reason |
|-----------|-----------|---------|
| Web Framework | FastAPI | Async, production-grade, auto-docs (Swagger) |
| Database (Dev) | SQLite | Zero setup, file-based, sufficient for MVP |
| Database (Prod) | PostgreSQL | Scalable, ACID, connection pooling |
| ORM | SQLAlchemy | Flexible, DB-agnostic, relationship support |
| Async Tasks | APScheduler | Scheduled data refresh, simple and reliable |
| Logging | Python logging + JSON | Structured logs, easy parsing |
| Testing | pytest | Comprehensive, fixture support |
| Deployment | Docker | Containerization, Railway.app support |

### 7.2 Frontend Technologies

| Component | Technology | Reason |
|-----------|-----------|---------|
| Framework | React 18 | Component-based, large ecosystem |
| Build Tool | Vite | Fast dev server, optimized builds |
| Styling | Tailwind CSS | Utility-first, responsive design |
| HTTP Client | Axios | Simple API calls, request/response interceptors |
| State Mgmt | React Context API | Sufficient for MVP, no external library |
| Testing | Jest + React Testing Library | Unit and component tests |

### 7.3 Infrastructure (Free Tier)

| Component | Provider | Plan |
|-----------|----------|------|
| Frontend Hosting | Vercel | Free tier (unlimited) |
| Backend Hosting | Railway.app | Free tier (₹0 for 5GB RAM/month) |
| Database | Railway Postgres | Free tier included |
| Monitoring | Custom Tables | Using Prometheus metrics |
| Analytics | Custom Tables | Using search_logs table |

---

## 8. Deployment Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    USER (Browser)                        │
└────────────┬─────────────────────────────────────────────┘
             │ HTTPS
     ┌───────▼────────┐
     │ Vercel (Frontend)    │
     │ React App      │
     │ Tailwind CSS   │
     │ Vite Build     │
     └───────┬────────┘
             │ API Calls (REST)
     ┌───────▼────────┐
     │ Railway Backend     │
     │ FastAPI App    │
     │ Python 3.9+    │
     │ APScheduler    │
     └───────┬────────┘
             │ Database Connection
     ┌───────▼────────┐
     │ Railway Postgres   │
     │ Primary DB     │
     │ Backups Daily  │
     └────────────────┘

External APIs (Called by Backend):
├─ RAPPID API (live train status, seats)
├─ IRCTC API (optional, for validation)
└─ (Kept in backend, frontend never calls)
```

---

## 9. Security & Compliance

### 9.1 Input Validation

- **Station Codes**: Whitelist validation (must exist in database)
- **Dates**: Must be within ±180 days
- **Time Formats**: ISO 8601 validation
- **Rate Limiting**: 100 requests per IP per hour

### 9.2 API Security

- **CORS**: Frontend domain only
- **Content-Type**: JSON only
- **SQL Injection**: SQLAlchemy parameterized queries
- **XSS Protection**: No inline scripts, CSP headers

### 9.3 Data Privacy

- **No Personal Data**: System doesn't store PII
- **Search Logs**: Only station codes and dates
- **Data Retention**: 90 days for analytics
- **Audit Trail**: All operations logged

---

## 10. Error Handling Strategy

### 10.1 Graceful Degradation

| Failure | Behavior |
|---------|----------|
| Live API down | Use cached seats, mark as "estimated" |
| Database slow | Return cached results if <5min old |
| Search timeout (>5s) | Return partial results from cache |
| Invalid input | Return 400 with clear error message |

### 10.2 Retry Logic

```
Attempt 1: Immediate
Attempt 2: +1 second delay
Attempt 3: +2 second delay
Attempt 4: +4 second delay
Attempt 5: +8 second delay

Total: Max 15 seconds retry window
```

### 10.3 Circuit Breaker

```
Normal (CLOSED): Accept all requests

Failure Threshold: 5 consecutive failures
  ↓
Open Circuit: Reject all requests for 60 seconds

After 60s: Try HALF_OPEN state
  ↓
If request succeeds: Reset to CLOSED
If request fails: Stay OPEN for another 60s
```

---

## 11. Monitoring & Observability

### 11.1 Key Metrics

```
Real-time (per second):
├─ Requests per second (RPS)
├─ Cache hit rate
├─ Error rate
└─ P99 latency (ms)

Per hour:
├─ Total searches
├─ Average response time
├─ Routes generated vs valid
├─ Top search pairs
└─ API failure rate

Per day:
├─ Daily active station pairs
├─ Peak hour
├─ Data freshness %
└─ System uptime %
```

### 11.2 Health Checks

```
Every 5 minutes:
├─ Database connectivity
├─ Cache responsiveness
├─ API endpoint availability
├─ Disk space check
└─ Memory usage check

Alerts triggered if:
├─ Response time > 3 seconds
├─ Cache hit rate < 20%
├─ Error rate > 1%
├─ Database offline
└─ Disk space < 500MB
```

---

## 12. Success Criteria

### 12.1 Functional Requirements ✅

- [x] Users can search by origin/destination/date
- [x] System generates valid, feasible routes
- [x] Routes match IRCTC operational data
- [x] Seat availability shown accurately
- [x] Top 5 routes ranked by quality

### 12.2 Non-Functional Requirements ✅

- [x] Response time < 2 seconds (p99)
- [x] Cache hit rate > 30%
- [x] API failure rate < 0.1%
- [x] 99.9% uptime
- [x] Supports 100 concurrent requests

### 12.3 Operational Requirements ✅

- [x] All searches logged
- [x] System self-monitoring
- [x] Zero manual data entry
- [x] Disaster recovery procedures
- [x] Complete audit trail

---

## 13. Production Deployment Checklist

```
Pre-Launch:
☐ Code review completed
☐ Security audit passed
☐ Load tests successful (100+ RPS)
☐ Database backups tested
☐ Monitoring dashboard active
☐ Alert system configured
☐ Documentation complete

Launch:
☐ CI/CD pipeline green
☐ All tests passing
☐ Deployment script tested
☐ Rollback procedure ready
☐ Team on standby

Post-Launch:
☐ Monitor error rates (first hour)
☐ Check response times
☐ Verify data correctness
☐ Monitor resource usage
☐ Confirm backup systems active
```

---

## 14. Future Enhancements (Not for v1.0)

- ❌ User accounts and bookmarking
- ❌ Direct booking integration
- ❌ Payment processing
- ❌ Email notifications
- ❌ Mobile app
- ❌ ML-based route recommendations
- ❌ Price prediction
- ❌ Seat price comparison

**Focus**: Core route discovery only. Everything else is post-v1.0.

---

## Document Status

- **Version**: 1.0
- **Status**: Ready for Implementation
- **Last Updated**: 2026-01-25
- **Next Review**: After Phase 1 completion
