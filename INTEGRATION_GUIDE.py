"""
QUICK INTEGRATION GUIDE

How to integrate all new modules into your FastAPI application.

Author: Route Master Development
Date: 2026-01-25
"""

# ========================================
# STEP 1: Update requirements.txt
# ========================================

# Add if not already present:
# fastapi==0.104.0
# pydantic==2.5.0
# sqlalchemy==2.0.0
# pandas==2.1.0
# numpy==1.24.0
# uvicorn==0.24.0


# ========================================
# STEP 2: Create main FastAPI app
# ========================================

# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import all router setup functions
from route_discovery_api import setup_route_discovery
from search_api import setup_search_api
from dashboard_api import setup_monitoring
from config import get_config

# Initialize FastAPI app
app = FastAPI(
    title="Route Master - Route Discovery API",
    description="Real-time railway route discovery with IRCTC validation",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup all routers
logger_discovery = setup_route_discovery(app)
setup_search_api(app)
metrics = setup_monitoring(app)

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "Route Master - Route Discovery API",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "route_discovery": "POST /routes/discover",
            "route_status": "GET /routes/status",
            "search_active": "GET /trains/active",
            "monitoring_health": "GET /monitoring/health",
            "monitoring_metrics": "GET /monitoring/metrics"
        },
        "documentation": "http://localhost:8000/docs"
    }

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000


# ========================================
# STEP 3: Initialize database
# ========================================

"""
Before running the app, initialize the database:

from database import DatabaseManager

db = DatabaseManager()
db.create_tables()

# Then load data:
from rappid_structured import RappidStructuredGenerator

gen = RappidStructuredGenerator()
stats = gen.process_all_trains()
csv_rows = gen.export_to_csv()

print(f"Loaded {stats['successful']} trains")
"""


# ========================================
# STEP 4: Start IRCTC Validation
# ========================================

"""
In background or scheduler:

from irctc_validator import IRCTCValidator
from active_only_router import ActiveOnlyRouter

# Validate all trains
validator = IRCTCValidator()
report = validator.validate_all_trains(date="2026-02-20", limit=100)

# Or update router
router = ActiveOnlyRouter()
router.load_active_trains()
stats = router.validate_inactive_trains(limit=100)

print(f"Validated: {stats['validated']} trains")
print(f"Became active: {stats['became_active']} trains")
"""


# ========================================
# STEP 5: Test route discovery
# ========================================

"""
Test with curl:

curl -X POST http://localhost:8000/routes/discover \\
  -H "Content-Type: application/json" \\
  -d '{
    "origin": "NDLS",
    "destination": "KOTA",
    "date": "2026-02-20",
    "max_transfers": 2,
    "limit": 10
  }'

Or with Python:

import requests

response = requests.post(
    "http://localhost:8000/routes/discover",
    json={
        "origin": "NDLS",
        "destination": "KOTA",
        "date": "2026-02-20",
        "max_transfers": 2,
        "limit": 10
    }
)

routes = response.json()
for route in routes['routes']:
    print(f"Route: {route['segments']} - Confidence: {route['confidence_score']}%")
"""


# ========================================
# STEP 6: Monitor system
# ========================================

"""
Check monitoring endpoints:

GET /monitoring/health
→ Basic health status, active train count, API error rate

GET /monitoring/metrics
→ Performance metrics, cache stats, validation stats

GET /monitoring/system-status
→ Database connectivity, data freshness, alerts

GET /monitoring/logs
→ Recent system logs

Example:
curl http://localhost:8000/monitoring/health | jq
"""


# ========================================
# STEP 7: Deploy with Docker
# ========================================

"""
Create Dockerfile:

FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

Build and run:
docker build -t route-master .
docker run -p 8000:8000 route-master
"""


# ========================================
# STEP 8: Environment variables
# ========================================

"""
Create .env file:

DATABASE_URL=postgresql://user:pass@localhost/route_master
IRCTC_API_KEY=your_key_here
LOG_LEVEL=INFO
CACHE_TTL_MINUTES=60
VALIDATION_CACHE_HOURS=12
SEAT_CHECK_CACHE_MINUTES=30
"""


# ========================================
# COMPLETE WORKFLOW
# ========================================

"""
1. Create main.py with FastAPI app
2. Run: python main.py
3. Or: uvicorn main:app --reload

The following will be available:

API Endpoints:
✓ POST /routes/discover - Route discovery (CORE)
✓ GET /routes/status - Service status
✓ GET /trains/active - Get ACTIVE trains
✓ GET /trains/status/{status} - Filter by status
✓ GET /trains/freshness - Sort by freshness
✓ GET /trains/quality - Sort by quality
✓ GET /trains/{train_no}/validation - Train validation info
✓ GET /trains/search - Advanced search
✓ GET /monitoring/health - Health status
✓ GET /monitoring/metrics - Performance metrics
✓ GET /monitoring/system-status - System details
✓ GET /monitoring/cache-stats - Cache statistics
✓ GET /monitoring/validation-stats - Validation stats
✓ GET /monitoring/logs - System logs

Features:
✓ Real-time route discovery
✓ IRCTC validation integration
✓ Transfer feasibility checking
✓ Live seat availability
✓ Multi-objective optimization
✓ Pareto-optimal routes
✓ Confidence scoring (0-100%)
✓ Response caching
✓ System monitoring
✓ Advanced search

Performance:
✓ < 200ms response time
✓ 11,000+ trains supported
✓ 60-minute route caching
✓ 12-hour validation cache
✓ 30-minute seat cache
"""


# ========================================
# TESTING
# ========================================

"""
Test with Python requests:

import requests

# Test 1: Route discovery
response = requests.post(
    "http://localhost:8000/routes/discover",
    json={
        "origin": "NDLS",
        "destination": "KOTA",
        "date": "2026-02-20",
        "max_transfers": 2
    }
)
print(f"Found {response.json()['total_routes_found']} routes")

# Test 2: Active trains
response = requests.get("http://localhost:8000/trains/active?limit=10")
print(f"Active trains: {len(response.json()['trains'])}")

# Test 3: Health check
response = requests.get("http://localhost:8000/monitoring/health")
print(f"System status: {response.json()['status']}")
print(f"Active rate: {response.json()['active_rate_pct']}%")

# Test 4: Search
response = requests.get("http://localhost:8000/trains/search?train_name=Rajdhani&status=ACTIVE")
print(f"Found {response.json()['count']} Rajdhani trains")
"""


# ========================================
# TROUBLESHOOTING
# ========================================

"""
If route discovery returns 0 routes:
→ Check if trains are ACTIVE: GET /trains/active
→ Run IRCTC validation: irctc_validator.validate_all_trains()
→ Check database: DatabaseManager().session.query(Train).count()

If seat checking fails:
→ Check IRCTC connectivity
→ Look at /monitoring/validation-stats
→ Check cache: GET /monitoring/cache-stats

If transfers show as invalid:
→ Check transfer times: transfer_validator.get_station_transfer_time()
→ Verify both trains are ACTIVE
→ Check timing: arrival + transfer_time <= departure

If monitoring shows high inactive rate:
→ Run batch validation on inactive trains
→ Check IRCTC API status
→ Increase validation frequency

Performance issues:
→ Check cache hit rate: GET /monitoring/cache-stats
→ Increase cache TTL in config.py
→ Monitor API response times: GET /monitoring/metrics
"""


# ========================================
# NEXT STEPS
# ========================================

"""
After deployment:

1. Load initial data
   - Run RAPPID fetcher
   - Process through structured generator
   - Load into database

2. Initial validation
   - Run IRCTC validator on all trains
   - Mark ACTIVE/INACTIVE status
   - Build route graph

3. User testing
   - Test with sample queries
   - Verify booking feasibility
   - Check confidence scores

4. Production deployment
   - Set up monitoring alerts
   - Configure backup strategy
   - Establish SLAs

5. Continuous operation
   - Run validation every 30-60 minutes
   - Monitor system health
   - Track user queries
   - Optimize based on feedback
"""

