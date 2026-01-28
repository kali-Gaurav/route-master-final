# 🗺️ VISUAL ARCHITECTURE & FLOW DIAGRAMS

**Document**: Visual reference guide  
**Date**: January 28, 2026  
**Purpose**: Understand system architecture at a glance

---

## 🏗️ CURRENT STATE vs TARGET STATE

### CURRENT STATE (What You Have)

```
┌─────────────────────────────────────────────────────────────┐
│                    CURRENT SETUP                             │
└─────────────────────────────────────────────────────────────┘

railway-operating-system-core/             route-master-final/
├── production.db                          ├── production.db (unclear if same)
├── database.py         ←─────┐            ├── api.py
├── route_finder.py     ←─┐   │            ├── api_v2.py  
├── main.py (CLI)         │   │            ├── api_v3.py
│  │                      │   │            ├── api_multi_transfer.py
│  └──► Terminal UI       │   │            ├── src/
│                         │   │            │   ├── App.tsx
│                         │   │            │   ├── components/
│                         │   │            │   └── pages/
│   PROBLEM:             │   │            │
│   └─ NO CONNECTION ────┘   │            └─ VAGUE API STRUCTURE
│                             │
│   ISSUE: Two duplicate     │ ISSUE: Multiple API versions
│           databases          │         create confusion
│                              │
└──────────────────────────────┘
                  ↑
        DISCONNECTED SYSTEMS
```

---

### TARGET STATE (What You're Building)

```
┌────────────────────────────────────────────────────────────────┐
│                   TARGET ARCHITECTURE                           │
└────────────────────────────────────────────────────────────────┘

                     ┌─────────────────┐
                     │   USERS/WEB     │
                     │   BROWSERS      │
                     └────────┬────────┘
                              │
                    ┌─────────▼────────┐
                    │ FRONTEND LAYER   │
                    │                  │
                    │ React + TypeScript
                    │ - Station Search │
                    │ - Route Finder   │
                    │ - Results View   │
                    │                  │
                    │ Port: 5173/3000  │
                    └────────┬────────┘
                             │
                    HTTP REST API
                      (JSON)
                             │
                    ┌────────▼────────┐
                    │ BACKEND LAYER   │
                    │                 │
                    │ FastAPI         │
                    │ - Unified API   │
                    │ - v1 endpoints  │
                    │ - Type-safe     │
                    │                 │
                    │ Port: 8000      │
                    └────────┬────────┘
                             │
                   SQL Queries
                     (sqlite)
                             │
                    ┌────────▼────────┐
                    │ DATABASE LAYER  │
                    │                 │
                    │ SQLite3         │
                    │ production.db   │
                    │ - 8,118 stations
                    │ - 11,309 trains │
                    │ - 166,488 routes
                    │                 │
                    └─────────────────┘

            ✓ UNIFIED SYSTEM
            ✓ CLEAR LAYERS
            ✓ TYPE-SAFE
            ✓ SCALABLE
```

---

## 📊 DATA FLOW DIAGRAM

### Route Search Request

```
USER INTERACTION:
User enters: NDLS → BRC

         │
         ▼
┌──────────────────────────┐
│ Frontend (React)         │
│ RouteSearch Component    │
│                          │
│ State:                   │
│ origin = "NDLS"         │
│ destination = "BRC"     │
│ maxTransfers = 2        │
└────────┬─────────────────┘
         │
         │ HTTP POST
         │ Content-Type: application/json
         │
         ▼
┌──────────────────────────────────┐
│ Backend (FastAPI)                │
│ POST /api/v1/routes/search       │
│                                  │
│ Validates:                       │
│ - origin exists                  │
│ - destination exists             │
│ - maxTransfers valid (0-3)       │
│                                  │
│ Calls: RouteService.search()     │
└────────┬──────────────────────────┘
         │
         │ SQL Query
         │
         ▼
┌──────────────────────────┐
│ Database (SQLite3)       │
│                          │
│ Query:                   │
│ SELECT * FROM routes    │
│ WHERE origin = "NDLS"   │
│ AND dest = "BRC"        │
│ AND transfers <= 2      │
│                          │
│ Returns: 47 routes      │
└────────┬─────────────────┘
         │
         │ SQL Results
         │
         ▼
┌──────────────────────────────────┐
│ Backend (FastAPI)                │
│ Format Response                  │
│                                  │
│ Convert to JSON:                 │
│ {                                │
│   "success": true,               │
│   "data": [...routes...],        │
│   "total": 47                    │
│ }                                │
└────────┬──────────────────────────┘
         │
         │ HTTP Response (JSON)
         │
         ▼
┌──────────────────────────┐
│ Frontend (React)         │
│ RouteCard Components     │
│                          │
│ Display:                 │
│ Route 1 - 2 transfers    │
│ Route 2 - 1 transfer     │
│ Route 3 - 0 transfers    │
│ ...                      │
└──────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│ User sees results        │
│ in browser               │
└──────────────────────────┘
```

---

## 🔄 COMPONENT INTERACTION

```
┌─────────────────────────────────────────────────────────────┐
│           FRONTEND (React TypeScript)                       │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          App.tsx                                    │   │
│  │  ┌────────────────────────────────────────────┐    │   │
│  │  │ Index Page                                 │    │   │
│  │  │  ┌──────────────────────────────────────┐ │    │   │
│  │  │  │ RouteSearch Component                │ │    │   │
│  │  │  │  ┌──────────────┐  ┌────────────┐  │ │    │   │
│  │  │  │  │StationSearch │  │RouteFilters│  │ │    │   │
│  │  │  │  │   origin     │  │max transfer│  │ │    │   │
│  │  │  │  └──────────────┘  └────────────┘  │ │    │   │
│  │  │  │        │                            │ │    │   │
│  │  │  │        └──► [Find Routes Button]    │ │    │   │
│  │  │  │                 │                    │ │    │   │
│  │  │  │                 ▼                    │ │    │   │
│  │  │  │        railwayAPI.searchRoutes()    │ │    │   │
│  │  │  │                 │                    │ │    │   │
│  │  │  │                 ▼                    │ │    │   │
│  │  │  │        ┌────────────────┐            │ │    │   │
│  │  │  │        │ useQuery Hook  │            │ │    │   │
│  │  │  │        │ (React Query)  │            │ │    │   │
│  │  │  │        └────────────────┘            │ │    │   │
│  │  │  │                 │                    │ │    │   │
│  │  │  └─────────────────┼────────────────────┘ │    │   │
│  │  │                    │                      │    │   │
│  │  │                    ▼                      │    │   │
│  │  │  ┌──────────────────────────────────────┐ │    │   │
│  │  │  │ Routes Display                       │ │    │   │
│  │  │  │  ├─ RouteCard 1                      │ │    │   │
│  │  │  │  ├─ RouteCard 2                      │ │    │   │
│  │  │  │  └─ RouteCard 3                      │ │    │   │
│  │  │  └──────────────────────────────────────┘ │    │   │
│  │  │                                           │    │   │
│  │  └──────────────────────────────────────────┘    │   │
│  │                                                    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                    ▲
                    │
              FETCH/AXIOS
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│              BACKEND (FastAPI Python)                       │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  app/main.py (FastAPI Application)                 │   │
│  │                                                     │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │ CORS & Middleware                           │  │   │
│  │  │ ├─ CORSMiddleware (allow frontend)          │  │   │
│  │  │ ├─ GZIPMiddleware (compression)             │  │   │
│  │  │ └─ LoggingMiddleware (request logging)      │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  │                                                     │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │ Routes (api/routes.py)                       │  │   │
│  │  │ POST /api/v1/routes/search                   │  │   │
│  │  │   └─► RouteService.search_routes()          │  │   │
│  │  │ GET /api/v1/stations                        │  │   │
│  │  │   └─► StationService.get_stations()         │  │   │
│  │  │ GET /api/v1/trains/{train_no}               │  │   │
│  │  │   └─► TrainService.get_train_info()         │  │   │
│  │  │ GET /api/v1/fares                           │  │   │
│  │  │   └─► FareService.calculate_fares()         │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  │                                                     │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │ Services (services/)                        │  │   │
│  │  │ ├─ RouteService                             │  │   │
│  │  │ │  └─ search_routes()                       │  │   │
│  │  │ ├─ StationService                           │  │   │
│  │  │ │  ├─ get_all_stations()                    │  │   │
│  │  │ │  ├─ search_station()                      │  │   │
│  │  │ │  └─ get_station_info()                    │  │   │
│  │  │ ├─ TrainService                             │  │   │
│  │  │ │  ├─ get_train_info()                      │  │   │
│  │  │ │  └─ get_trains_by_route()                 │  │   │
│  │  │ └─ FareService                              │  │   │
│  │  │    └─ calculate_fares()                     │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  │                                                     │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │ Database Layer (database.py)                │  │   │
│  │  │ ├─ get_connection()                         │  │   │
│  │  │ ├─ execute_query()                          │  │   │
│  │  │ └─ Connection Pooling                       │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                    ▲
                    │
               SQL QUERIES
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                DATABASE (SQLite3)                           │
│                                                              │
│  production.db                                              │
│  ├─ stations (8,118 records)                               │
│  ├─ trains (11,309 records)                                │
│  ├─ routes (166,488 records)                               │
│  └─ fares (indexed tables)                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 PROJECT STRUCTURE

```
railway-website/
│
├── 📁 backend/                          ← Python Backend
│   ├── app/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 main.py                  ← FastAPI app entry point
│   │   ├── 📄 config.py                ← Configuration
│   │   ├── 📄 database.py              ← DB connection
│   │   ├── 📄 exceptions.py            ← Error handling
│   │   └── 📄 middleware.py            ← CORS, logging
│   │
│   ├── api/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 routes.py                ← All endpoints
│   │   ├── 📄 schemas.py               ← Pydantic models
│   │   └── v1/
│   │       ├── 📄 routes.py
│   │       ├── 📄 stations.py
│   │       ├── 📄 trains.py
│   │       └── 📄 fares.py
│   │
│   ├── services/                       ← Business Logic
│   │   ├── 📄 __init__.py
│   │   ├── 📄 route_service.py         ← Route finding
│   │   ├── 📄 station_service.py       ← Station ops
│   │   ├── 📄 train_service.py         ← Train info
│   │   └── 📄 cache_service.py         ← Caching
│   │
│   ├── models/                         ← DB Models
│   │   ├── 📄 __init__.py
│   │   ├── 📄 station.py
│   │   ├── 📄 train.py
│   │   ├── 📄 route.py
│   │   └── 📄 fare.py
│   │
│   ├── tests/
│   │   ├── 📄 test_routes.py
│   │   ├── 📄 test_stations.py
│   │   └── 📄 conftest.py
│   │
│   ├── production.db                   ← SQLite Database
│   ├── 📄 requirements.txt
│   ├── 📄 .env.example
│   └── 📄 Dockerfile
│
├── 📁 frontend/                         ← React Frontend
│   ├── src/
│   │   ├── 📄 App.tsx
│   │   ├── 📄 main.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── 📄 RouteSearch.tsx
│   │   │   ├── 📄 StationSearch.tsx
│   │   │   ├── 📄 RouteCard.tsx
│   │   │   ├── 📄 RouteFilters.tsx
│   │   │   ├── 📄 Navbar.tsx
│   │   │   ├── 📄 Footer.tsx
│   │   │   └── ui/                     ← shadcn/ui components
│   │   │
│   │   ├── pages/
│   │   │   ├── 📄 Index.tsx            ← Home page
│   │   │   └── 📄 NotFound.tsx         ← 404 page
│   │   │
│   │   ├── services/
│   │   │   ├── 📄 api.ts               ← API client
│   │   │   └── 📄 cache.ts             ← Caching
│   │   │
│   │   ├── hooks/
│   │   │   ├── 📄 useRouteSearch.ts
│   │   │   └── 📄 useStationSearch.ts
│   │   │
│   │   ├── types/
│   │   │   ├── 📄 index.ts
│   │   │   ├── 📄 route.ts
│   │   │   └── 📄 station.ts
│   │   │
│   │   └── 📄 index.css                ← Global styles
│   │
│   ├── public/
│   │   └── 📄 index.html
│   │
│   ├── 📄 package.json
│   ├── 📄 vite.config.ts
│   ├── 📄 tsconfig.json
│   ├── 📄 tailwind.config.ts
│   └── 📄 Dockerfile
│
├── 📁 shared/                           ← Shared Types
│   ├── types/
│   │   ├── 📄 route.ts
│   │   ├── 📄 station.ts
│   │   └── 📄 train.ts
│   └── 📄 constants.ts
│
├── 📁 scripts/                          ← Utilities
│   ├── 📄 setup.sh                     ← Setup script
│   ├── 📄 seed_database.py             ← Data loading
│   ├── 📄 migrate.py                   ← DB migrations
│   └── 📄 start-dev.sh                 ← Start dev servers
│
├── 📁 docs/                             ← Documentation
│   ├── 📄 API.md                       ← API docs
│   ├── 📄 SETUP.md                     ← Setup guide
│   ├── 📄 DEPLOYMENT.md                ← Deploy guide
│   └── 📄 ARCHITECTURE.md              ← Architecture
│
├── 📁 dist/                             ← Build output
│
├── 📄 docker-compose.yml               ← Multi-container setup
├── 📄 .env.example                     ← Environment template
├── 📄 .gitignore
├── 📄 Makefile                         ← Common commands
├── 📄 README.md                        ← Main docs
└── 📄 .github/
    └── workflows/
        └── 📄 ci.yml                   ← GitHub Actions
```

---

## 🔄 DEVELOPMENT PHASES TIMELINE

```
WEEK 1: Foundation (Phase 1 & 2)
┌─────────────────────────────────────────────────┐
│ Day 1-2: Setup & Database                       │
│  ├─ Project structure                           │
│  ├─ Copy database                               │
│  └─ Environment setup                           │
│                                                 │
│ Day 3-4: Unified API                           │
│  ├─ Create FastAPI app                         │
│  ├─ Implement services                         │
│  └─ Add endpoints                              │
│                                                 │
│ Day 5: Testing                                  │
│  ├─ Unit tests                                 │
│  └─ API tests                                  │
└─────────────────────────────────────────────────┘

WEEK 2: Frontend Integration (Phase 3)
┌─────────────────────────────────────────────────┐
│ Day 1-2: API Integration                        │
│  ├─ Update API client                          │
│  └─ Connect to backend                         │
│                                                 │
│ Day 3-4: Feature Development                    │
│  ├─ Station search                             │
│  ├─ Route search                               │
│  └─ Result display                             │
│                                                 │
│ Day 5: Polish                                   │
│  ├─ UI improvements                            │
│  └─ Bug fixes                                  │
└─────────────────────────────────────────────────┘

WEEK 3-4: Deployment (Phase 4 & 5)
┌─────────────────────────────────────────────────┐
│ Week 3:                                         │
│  ├─ Comprehensive testing                      │
│  ├─ Performance optimization                   │
│  ├─ Docker setup                               │
│  └─ Documentation                              │
│                                                 │
│ Week 4:                                         │
│  ├─ Production deployment                      │
│  ├─ Monitoring setup                           │
│  ├─ Final testing                              │
│  └─ Launch!                                    │
└─────────────────────────────────────────────────┘
```

---

## 🎯 SUCCESS METRICS

```
API Performance:
┌──────────────────────────────────────────────┐
│ Route Search:        <200ms  ✓               │
│ Station Lookup:      <100ms  ✓               │
│ Train Info:          <150ms  ✓               │
│ API Overall:         <500ms  ✓               │
└──────────────────────────────────────────────┘

Frontend Performance:
┌──────────────────────────────────────────────┐
│ Page Load:           <2s     ✓               │
│ Search Response:     <1s     ✓               │
│ Bundle Size:         <500KB  ✓               │
│ Lighthouse Score:    >90     ✓               │
└──────────────────────────────────────────────┘

System Metrics:
┌──────────────────────────────────────────────┐
│ Uptime:              99.9%   ✓               │
│ Error Rate:          <0.1%   ✓               │
│ Concurrent Users:    1000+   ✓               │
│ Database Size:       <100MB  ✓               │
└──────────────────────────────────────────────┘
```

---

## 🚀 DEPLOYMENT ARCHITECTURE

```
┌─────────────────────────────────────────────────────┐
│           PRODUCTION DEPLOYMENT                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│              CLIENTS (Web Browsers)                 │
│  Chrome, Firefox, Safari, Edge, Mobile Browsers    │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────▼──────────┐
        │   CDN (Optional)    │
        │  Cloudflare/Vercel  │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  Load Balancer      │
        │  (if scaling)       │
        └──────────┬──────────┘
                   │
         ┌─────────┴────────┐
         │                  │
    ┌────▼────┐        ┌────▼────┐
    │Frontend  │        │Frontend  │
    │Instance1 │   ...  │Instance2 │
    │(Vercel)  │        │(Railway) │
    └────┬─────┘        └────┬─────┘
         │                   │
         └───────────┬───────┘
                     │
          ┌──────────▼──────────┐
          │  API Load Balancer  │
          │  (if scaling)       │
          └──────────┬──────────┘
                     │
         ┌───────────┼──────────┐
         │           │          │
    ┌────▼───┐  ┌────▼───┐ ┌────▼───┐
    │Backend  │  │Backend  │ │Backend  │
    │Instance1│  │Instance2│ │Instance3│
    │(Railway)│  │ (Render)│ │  (AWS) │
    └────┬────┘  └────┬────┘ └────┬────┘
         │            │            │
         └────────────┼────────────┘
                      │
          ┌───────────▼──────────┐
          │  Database Server     │
          │  SQLite (local) OR   │
          │  PostgreSQL (cloud)  │
          │  with replication    │
          └──────────────────────┘
```

---

## 🎓 TECHNOLOGY RELATIONSHIP

```
React ◄──► TypeScript ◄──► Vite
 │              │           │
 │              │           │
 ▼              ▼           ▼
Components   Type Safety   Fast Build
              & Validation  & HMR


FastAPI ◄──► Pydantic ◄──► SQLAlchemy
 │              │              │
 │              │              │
 ▼              ▼              ▼
Endpoints    Validation   Database ORM
             & Docs       (Optional)


┌──────────────────────────────────────┐
│         Integration Point            │
│   REST API JSON Communication        │
│   HTTP/HTTPS + Request/Response      │
└──────────────────────────────────────┘


Both ◄──────────────────────► Docker
 │                              │
 │                              │
 ▼                              ▼
Containerized            Consistent Environment
Deployment              Dev/Prod Parity
```

---

## 📊 DATA RELATIONSHIPS

```
STATION TABLE
┌──────────────────────────────────────┐
│ id (PK)                              │
│ code (UNIQUE, FK in routes & trains)│
│ name                                 │
│ state                               │
│ zone                                │
│ latitude, longitude                 │
└──────────────────────────────────────┘
        ▲                    ▲
        │                    │
        └─────┬──────────────┘
              │
      ┌───────┴────────┐
      │                │
┌─────▼──────┐  ┌─────▼──────┐
│ROUTES (FK) │  │TRAINS (FK)  │
│  origin    │  │  route_orig │
│  dest      │  │  route_dest │
│  train_no  │  │  name       │
│  transfers │  │  departure  │
│  duration  │  │  arrival    │
│  fare_base │  │  days       │
└────────────┘  └─────┬──────┘
                      │
                ┌─────▼──────┐
                │FARES (FK)  │
                │ train_no   │
                │ class      │
                │ base_fare  │
                │ tax        │
                │ total      │
                └────────────┘
```

---

**Visual Guide Complete** ✅

These diagrams provide quick reference for understanding:
- System architecture
- Data flow
- Component interaction
- Project structure
- Development timeline
- Deployment setup
- Technology relationships

Use these as quick references while reading the detailed documents!
