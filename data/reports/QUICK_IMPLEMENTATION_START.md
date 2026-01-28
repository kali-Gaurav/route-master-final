# 🚀 Quick Implementation Start Guide

**Status**: Ready to implement  
**Estimated Time**: 4 weeks  
**Difficulty**: Intermediate

---

## 📁 FILE ORGANIZATION

Your current structure has duplicate code. Here's how to reorganize:

### Current Issues
```
✗ railway-operating-system-core/production.db   (Database 1)
✗ route-master-final/production.db               (Database 2 - unclear if same)
✗ Multiple API files (api.py, api_v2.py, api_v3.py, api_multi_transfer.py)
✗ Database logic duplicated across both projects
```

### Target Structure
```
railway-website/                     ← NEW ROOT
├── backend/                         ← NEW: Unified backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  ← FastAPI app
│   │   ├── config.py                ← Settings
│   │   ├── database.py              ← SQLAlchemy setup
│   │   ├── deps.py                  ← Dependencies
│   │   ├── exceptions.py            ← Error handling
│   │   └── middleware.py            ← CORS, logging, etc
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py                ← All endpoints
│   │   ├── schemas.py               ← Pydantic models
│   │   └── v1/
│   │       ├── routes.py
│   │       ├── stations.py
│   │       ├── trains.py
│   │       └── fares.py
│   │
│   ├── services/                    ← Business logic
│   │   ├── __init__.py
│   │   ├── route_service.py
│   │   ├── station_service.py
│   │   ├── train_service.py
│   │   └── cache_service.py
│   │
│   ├── models/                      ← Database models
│   │   ├── __init__.py
│   │   ├── station.py
│   │   ├── train.py
│   │   ├── route.py
│   │   └── fare.py
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_routes.py
│   │   ├── test_stations.py
│   │   └── conftest.py
│   │
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
│
├── frontend/                        ← (Updated from route-master-final)
│   ├── src/
│   │   ├── components/
│   │   │   ├── RouteSearch.tsx      ← Main search
│   │   │   ├── StationSearch.tsx    ← Station input
│   │   │   ├── RouteCard.tsx        ← Result display
│   │   │   ├── RouteFilters.tsx     ← NEW: Advanced filters
│   │   │   └── ...
│   │   │
│   │   ├── services/
│   │   │   ├── api.ts               ← API client
│   │   │   └── cache.ts             ← Caching logic
│   │   │
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── types/
│   │   └── ...
│   │
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
│
├── shared/                          ← NEW: Shared types
│   ├── types/
│   │   ├── index.ts
│   │   ├── route.ts
│   │   ├── station.ts
│   │   └── train.ts
│   └── constants.ts
│
├── scripts/                         ← NEW: Utilities
│   ├── setup.sh                     ← Initial setup
│   ├── seed_database.py             ← Copy/migrate data
│   ├── migrate.py                   ← Database migrations
│   └── start-dev.sh                 ← Start both servers
│
├── docker-compose.yml               ← NEW: Local development
├── .env.example                     ← NEW: Environment template
├── Makefile                         ← NEW: Common commands
├── README.md                        ← NEW: Main docs
└── docs/
    ├── API.md                       ← NEW: API documentation
    ├── SETUP.md                     ← NEW: Setup guide
    ├── DEPLOYMENT.md                ← NEW: Deploy guide
    └── ARCHITECTURE.md              ← NEW: System design
```

---

## 🔄 STEP 1: COPY & CONSOLIDATE

### Task 1a: Copy Existing Database

```bash
# In Windows PowerShell or Git Bash
cd railway-website/backend

# Copy the working database from railway-operating-system-core
Copy-Item -Path "..\railway-operating-system-core\production.db" -Destination ".\production.db" -Force

# Verify it has data
python scripts/verify_database.py
```

### Task 1b: Copy Route Finding Logic

Extract functions from `railway-operating-system-core/route_finder.py`:

**Backend: `backend/services/route_service.py`**

```python
"""
Route finding service - Migrated from railway-operating-system-core
"""

import sqlite3
from typing import List, Dict, Any

class RouteService:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def search_routes(
        self,
        origin: str,
        destination: str,
        max_transfers: int = 3,
        days: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search all possible routes between two stations.
        Migrated from route_finder.py search_routes()
        """
        # Copy implementation from railway-operating-system-core
        pass
```

### Task 1c: Copy Station Lookup

**Backend: `backend/services/station_service.py`**

```python
"""
Station service - Get station details, search, autocomplete
Migrated from railway-operating-system-core/database.py
"""

class StationService:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_all_stations(self) -> List[Dict]:
        """Get all stations"""
        # Copy from database.py get_all_stations()
        pass
    
    def search_station(self, query: str) -> List[Dict]:
        """Search stations by name or code"""
        # Copy from database.py search_station()
        pass
    
    def get_station_info(self, station_code: str) -> Dict:
        """Get detailed station info"""
        # Copy from database.py get_station_info()
        pass
```

---

## 🔧 STEP 2: CREATE UNIFIED API

### Task 2a: Create FastAPI Main App

**File: `backend/app/main.py`**

```python
"""
Main FastAPI Application
Unifies all route, station, train, and fare endpoints
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware
import logging

from app.config import settings
from app.api.routes import router as api_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app
app = FastAPI(
    title="Indian Railway Network API",
    version="1.0.0",
    description="Complete railway route and schedule system"
)

# Middleware
app.add_middleware(GZIPMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    return response

# Include routes
app.include_router(api_router, prefix="/api/v1")

# Health check
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    return {
        "message": "Indian Railway Network API",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
```

### Task 2b: Create API Routes

**File: `backend/app/api/routes.py`**

```python
"""
Main API router - combines all endpoints
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List

from app.services.route_service import RouteService
from app.services.station_service import StationService
from app.services.train_service import TrainService
from app.api.schemas import (
    RouteSearchRequest,
    RouteSearchResponse,
    StationInfo,
    TrainInfo
)

router = APIRouter()

# Initialize services
route_service = RouteService(db_path="production.db")
station_service = StationService(db_path="production.db")
train_service = TrainService(db_path="production.db")

# ============================================================================
# ROUTES ENDPOINTS
# ============================================================================

@router.post("/routes/search")
async def search_routes(request: RouteSearchRequest) -> RouteSearchResponse:
    """
    Search for routes between two stations
    
    Parameters:
    - origin: Station code (e.g., "NDLS")
    - destination: Station code (e.g., "BRC")
    - max_transfers: Maximum transfers (0-3)
    - days: Days of week (MON, TUE, etc.)
    """
    try:
        routes = route_service.search_routes(
            origin=request.origin,
            destination=request.destination,
            max_transfers=request.max_transfers or 3,
            days=request.days
        )
        return RouteSearchResponse(
            success=True,
            data=routes,
            total=len(routes)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routes")
async def get_routes(
    origin: str,
    destination: str,
    max_transfers: int = Query(3, ge=0, le=3)
) -> RouteSearchResponse:
    """GET version of route search"""
    return await search_routes(
        RouteSearchRequest(
            origin=origin,
            destination=destination,
            max_transfers=max_transfers
        )
    )

# ============================================================================
# STATIONS ENDPOINTS
# ============================================================================

@router.get("/stations", response_model=List[StationInfo])
async def get_stations(
    search: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100)
) -> List[StationInfo]:
    """
    Get stations, optionally filtered by search term
    
    Parameters:
    - search: Search term (name or code)
    - limit: Maximum results (default 10)
    """
    if search:
        return station_service.search_station(search)[:limit]
    return station_service.get_all_stations()[:limit]


@router.get("/stations/{station_code}", response_model=StationInfo)
async def get_station(station_code: str) -> StationInfo:
    """Get detailed information about a specific station"""
    info = station_service.get_station_info(station_code)
    if not info:
        raise HTTPException(status_code=404, detail="Station not found")
    return info

# ============================================================================
# TRAINS ENDPOINTS
# ============================================================================

@router.get("/trains/{train_no}", response_model=TrainInfo)
async def get_train(train_no: int) -> TrainInfo:
    """Get detailed information about a specific train"""
    info = train_service.get_train_info(train_no)
    if not info:
        raise HTTPException(status_code=404, detail="Train not found")
    return info


@router.get("/trains")
async def search_trains(
    train_no: Optional[int] = Query(None),
    origin: Optional[str] = Query(None),
    destination: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """Search trains by number or route"""
    if train_no:
        return [train_service.get_train_info(train_no)]
    
    if origin and destination:
        return train_service.get_trains_by_route(origin, destination)[:limit]
    
    raise HTTPException(status_code=400, detail="Provide train_no or origin+destination")

# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get("/stats")
async def get_stats():
    """Get system statistics"""
    return {
        "stations": station_service.count_stations(),
        "trains": train_service.count_trains(),
        "routes": route_service.count_routes(),
        "last_updated": "2026-01-28"
    }
```

### Task 2c: Create Data Schemas

**File: `backend/app/api/schemas.py`**

```python
"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class RouteSegment(BaseModel):
    train_no: int
    train_name: str
    from_station: str
    to_station: str
    from_station_code: str
    to_station_code: str
    departure_time: str
    arrival_time: str
    days_running: str
    duration: str

class Route(BaseModel):
    route_id: str
    origin: str
    origin_code: str
    destination: str
    destination_code: str
    segments: List[RouteSegment]
    total_transfers: int
    total_duration: str
    base_fare: int
    confidence_score: float = Field(ge=0, le=1)

class RouteSearchRequest(BaseModel):
    origin: str = Field(..., min_length=3, max_length=10)
    destination: str = Field(..., min_length=3, max_length=10)
    max_transfers: Optional[int] = Field(3, ge=0, le=3)
    days: Optional[List[str]] = None
    departure_date: Optional[str] = None

class RouteSearchResponse(BaseModel):
    success: bool
    data: List[Route]
    total: int
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class StationInfo(BaseModel):
    code: str
    name: str
    state: Optional[str] = None
    zone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class TrainInfo(BaseModel):
    train_no: int
    name: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    duration: str
    days_running: str
    stops: List[dict] = []
    fares: dict = {}
```

---

## 📱 STEP 3: UPDATE FRONTEND

### Task 3a: Update API Client

**File: `frontend/src/services/api.ts`**

```typescript
/**
 * API Client - Communicates with unified backend
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface SearchParams {
  origin: string;
  destination: string;
  maxTransfers?: number;
  days?: string[];
}

export interface Route {
  route_id: string;
  origin: string;
  origin_code: string;
  destination: string;
  destination_code: string;
  segments: Segment[];
  total_transfers: number;
  total_duration: string;
  base_fare: number;
  confidence_score: number;
}

export interface Station {
  code: string;
  name: string;
  state?: string;
  zone?: string;
  latitude?: number;
  longitude?: number;
}

export interface SearchResponse {
  success: boolean;
  data: Route[];
  total: number;
  timestamp: string;
}

// Main API functions
export const railwayAPI = {
  // Route search
  searchRoutes: async (params: SearchParams): Promise<SearchResponse> => {
    const response = await fetch(`${API_URL}/routes/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        origin: params.origin,
        destination: params.destination,
        max_transfers: params.maxTransfers,
        days: params.days
      })
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    
    return response.json();
  },

  // Get stations (for autocomplete)
  getStations: async (search?: string): Promise<Station[]> => {
    const url = new URL(`${API_URL}/stations`);
    if (search) url.searchParams.append('search', search);
    if (search) url.searchParams.append('limit', '20');
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch stations');
    return response.json();
  },

  // Get single station
  getStation: async (code: string): Promise<Station> => {
    const response = await fetch(`${API_URL}/stations/${code}`);
    if (!response.ok) throw new Error('Station not found');
    return response.json();
  },

  // Get train info
  getTrain: async (trainNo: number) => {
    const response = await fetch(`${API_URL}/trains/${trainNo}`);
    if (!response.ok) throw new Error('Train not found');
    return response.json();
  },

  // Get stats
  getStats: async () => {
    const response = await fetch(`${API_URL}/stats`);
    if (!response.ok) throw new Error('Failed to fetch stats');
    return response.json();
  },

  // Health check
  health: async () => {
    const response = await fetch('/api/health');
    return response.json();
  }
};
```

### Task 3b: Update Route Search Component

**File: `frontend/src/components/RouteSearch.tsx`** (Update existing)

```typescript
import { useState } from 'react';
import { railwayAPI } from '@/services/api';
import { RouteCard } from './RouteCard';
import { StationSearch } from './StationSearch';
import { RouteFilters } from './RouteFilters';

export function RouteSearch() {
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [maxTransfers, setMaxTransfers] = useState(3);
  const [loading, setLoading] = useState(false);
  const [routes, setRoutes] = useState([]);
  const [error, setError] = useState('');

  const handleSearch = async () => {
    if (!origin || !destination) {
      setError('Please select both stations');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const response = await railwayAPI.searchRoutes({
        origin,
        destination,
        maxTransfers
      });
      
      if (response.success) {
        setRoutes(response.data);
      } else {
        setError('No routes found');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <StationSearch 
          value={origin}
          onChange={setOrigin}
          placeholder="From"
        />
        <StationSearch 
          value={destination}
          onChange={setDestination}
          placeholder="To"
        />
      </div>

      <RouteFilters 
        maxTransfers={maxTransfers}
        onMaxTransfersChange={setMaxTransfers}
      />

      <button 
        onClick={handleSearch}
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 rounded"
      >
        {loading ? 'Searching...' : 'Find Routes'}
      </button>

      {error && <div className="text-red-600">{error}</div>}

      <div className="space-y-2">
        {routes.map((route) => (
          <RouteCard key={route.route_id} route={route} />
        ))}
      </div>
    </div>
  );
}
```

---

## 🐳 STEP 4: DOCKER SETUP

### Task 4a: Backend Dockerfile

**File: `backend/Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Copy database
COPY production.db .

# Expose port
EXPOSE 8000

# Run
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Task 4b: Docker Compose

**File: `docker-compose.yml`** (Root)

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
      - DATABASE_URL=sqlite:///data/production.db
    volumes:
      - ./backend/production.db:/app/production.db
    command: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend
    environment:
      - VITE_API_URL=http://localhost:8000/api/v1
    command: npm run dev

volumes:
  data:
```

**Run with:**
```bash
docker-compose up
```

---

## ✅ STEP 5: VERIFICATION CHECKLIST

After implementing each step, verify:

```
STEP 1: Copy Database
[ ] production.db copied to backend/
[ ] Verify database has tables: stations, trains, routes
[ ] Test query: SELECT COUNT(*) FROM stations
[ ] Expected: 8118

STEP 2: Create API
[ ] All endpoints accessible
[ ] GET /api/health returns 200
[ ] GET /api/v1/stations returns data
[ ] POST /api/v1/routes/search works
[ ] Error handling in place
[ ] CORS enabled

STEP 3: Update Frontend
[ ] npm install works
[ ] API client can connect
[ ] Stations autocomplete works
[ ] Route search returns results
[ ] No console errors

STEP 4: Docker
[ ] Backend builds: docker build ./backend
[ ] Frontend builds: docker build ./frontend
[ ] docker-compose up starts both
[ ] Services communicate correctly

STEP 5: Ready for Deployment
[ ] All tests passing
[ ] Documentation complete
[ ] Environment variables configured
[ ] Database backed up
[ ] Ready to deploy
```

---

## 🚀 QUICK COMMAND REFERENCE

```bash
# Backend setup
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# Frontend setup
cd frontend
npm install
npm run dev

# Test API
curl http://localhost:8000/api/health
curl http://localhost:8000/api/v1/stations?search=delhi

# Docker
docker-compose up --build
docker-compose down

# Database
sqlite3 backend/production.db ".tables"
sqlite3 backend/production.db ".schema stations"
```

---

**Next Step**: Start with STEP 1 (Copy & Consolidate) and work through systematically.
