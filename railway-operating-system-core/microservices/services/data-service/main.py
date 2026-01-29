# ===============================================
# DATA SERVICE
# ===============================================
# Microservice providing database access to railway data
# Handles all database operations for the multi-tenant system

import os
import sys
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from uuid import UUID

# Add shared module to path
# Add project root to path to enable shared module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import uvicorn

from shared.models import DatabaseManager, create_tenant_models
from shared.config import (
    DATABASE_CONFIG, API_CONFIG, MONITORING_CONFIG,
    get_cors_origins, get_service_url
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, API_CONFIG['log_level']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Railway OS Data Service",
    description="Database access service for railway operating system",
    version="1.0.0",
    debug=API_CONFIG['debug_mode']
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global database manager
db_manager = None

# ===============================================
# DATA MODELS
# ===============================================

class StationResponse(BaseModel):
    station_id: int
    station_code: str
    station_name: str
    city: Optional[str]
    state: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    is_junction: bool

class TrainResponse(BaseModel):
    train_id: int
    train_no: int
    train_name: str
    train_type: Optional[str]
    source_station: Optional[str]
    destination_station: Optional[str]
    distance: Optional[int]
    duration_minutes: Optional[int]

class TrainScheduleResponse(BaseModel):
    schedule_id: int
    train_no: int
    station_code: str
    station_name: Optional[str]
    arrival_time: Optional[str]
    departure_time: Optional[str]
    day_of_journey: int
    distance_from_source: int

class RouteSearchRequest(BaseModel):
    source: str
    destination: str
    date: date

    @validator('source', 'destination')
    def validate_station_code(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Station code cannot be empty')
        return v.strip().upper()

class TenantContext(BaseModel):
    tenant_id: str
    tenant_name: str
    schema_name: str

# ===============================================
# DEPENDENCY INJECTION
# ===============================================

def get_tenant_context(tenant_id: str = Query(..., description="Tenant ID")) -> TenantContext:
    """Get tenant context for database operations"""
    try:
        # Validate tenant exists
        session = db_manager.get_session()
        result = session.execute("""
            SELECT tenant_name FROM system.tenants
            WHERE tenant_id = %s AND is_active = true
        """, (tenant_id,)).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Tenant not found or inactive")

        tenant_name = result[0]
        schema_name = db_manager.get_tenant_schema_name(tenant_id)

        return TenantContext(
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            schema_name=schema_name
        )
    except Exception as e:
        logger.error(f"Error getting tenant context: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ===============================================
# STATIONS ENDPOINTS
# ===============================================

@app.get("/v1/stations", response_model=List[StationResponse])
async def get_stations(
    tenant: TenantContext = Depends(get_tenant_context),
    search: Optional[str] = Query(None, description="Search by station code or name"),
    limit: int = Query(50, description="Maximum number of results", le=100)
):
    """Get stations for a tenant"""
    try:
        session = db_manager.get_session()
        schema_name = tenant.schema_name

        query = f"""
            SELECT station_id, station_code, station_name, city, state,
                   latitude, longitude, is_junction
            FROM {schema_name}.stations_master
        """

        params = []
        if search:
            query += " WHERE station_code ILIKE %s OR station_name ILIKE %s"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])

        query += " ORDER BY station_name LIMIT %s"
        params.append(limit)

        results = session.execute(query, params).fetchall()
        session.close()

        return [
            StationResponse(
                station_id=row[0],
                station_code=row[1],
                station_name=row[2],
                city=row[3],
                state=row[4],
                latitude=float(row[5]) if row[5] else None,
                longitude=float(row[6]) if row[6] else None,
                is_junction=row[7]
            )
            for row in results
        ]
    except Exception as e:
        logger.error(f"Error getting stations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/v1/stations/{station_code}", response_model=StationResponse)
async def get_station(
    station_code: str,
    tenant: TenantContext = Depends(get_tenant_context)
):
    """Get specific station by code"""
    try:
        session = db_manager.get_session()
        schema_name = tenant.schema_name

        result = session.execute(f"""
            SELECT station_id, station_code, station_name, city, state,
                   latitude, longitude, is_junction
            FROM {schema_name}.stations_master
            WHERE station_code = %s
        """, (station_code.upper(),)).fetchone()

        session.close()

        if not result:
            raise HTTPException(status_code=404, detail="Station not found")

        return StationResponse(
            station_id=result[0],
            station_code=result[1],
            station_name=result[2],
            city=result[3],
            state=result[4],
            latitude=float(result[5]) if result[5] else None,
            longitude=float(result[6]) if result[6] else None,
            is_junction=result[7]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting station: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ===============================================
# TRAINS ENDPOINTS
# ===============================================

@app.get("/v1/trains", response_model=List[TrainResponse])
async def get_trains(
    tenant: TenantContext = Depends(get_tenant_context),
    search: Optional[str] = Query(None, description="Search by train number or name"),
    limit: int = Query(50, description="Maximum number of results", le=100)
):
    """Get trains for a tenant"""
    try:
        session = db_manager.get_session()
        schema_name = tenant.schema_name

        query = f"""
            SELECT train_id, train_no, train_name, train_type,
                   source_station, destination_station, distance, duration_minutes
            FROM {schema_name}.trains_master
        """

        params = []
        if search:
            if search.isdigit():
                query += " WHERE train_no = %s"
                params.append(int(search))
            else:
                query += " WHERE train_name ILIKE %s"
                params.append(f"%{search}%")

        query += " ORDER BY train_no LIMIT %s"
        params.append(limit)

        results = session.execute(query, params).fetchall()
        session.close()

        return [
            TrainResponse(
                train_id=row[0],
                train_no=row[1],
                train_name=row[2],
                train_type=row[3],
                source_station=row[4],
                destination_station=row[5],
                distance=row[6],
                duration_minutes=row[7]
            )
            for row in results
        ]
    except Exception as e:
        logger.error(f"Error getting trains: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/v1/trains/{train_no}", response_model=TrainResponse)
async def get_train(
    train_no: int,
    tenant: TenantContext = Depends(get_tenant_context)
):
    """Get specific train by number"""
    try:
        session = db_manager.get_session()
        schema_name = tenant.schema_name

        result = session.execute(f"""
            SELECT train_id, train_no, train_name, train_type,
                   source_station, destination_station, distance, duration_minutes
            FROM {schema_name}.trains_master
            WHERE train_no = %s
        """, (train_no,)).fetchone()

        session.close()

        if not result:
            raise HTTPException(status_code=404, detail="Train not found")

        return TrainResponse(
            train_id=result[0],
            train_no=result[1],
            train_name=result[2],
            train_type=result[3],
            source_station=result[4],
            destination_station=result[5],
            distance=result[6],
            duration_minutes=result[7]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting train: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ===============================================
# TRAIN SCHEDULE ENDPOINTS
# ===============================================

@app.get("/v1/schedule/{train_no}", response_model=List[TrainScheduleResponse])
async def get_train_schedule(
    train_no: int,
    tenant: TenantContext = Depends(get_tenant_context)
):
    """Get schedule for a specific train"""
    try:
        session = db_manager.get_session()
        schema_name = tenant.schema_name

        results = session.execute(f"""
            SELECT schedule_id, train_no, station_code, station_name,
                   arrival_time, departure_time, day_of_journey, distance_from_source
            FROM {schema_name}.train_schedule
            WHERE train_no = %s
            ORDER BY day_of_journey, distance_from_source
        """, (train_no,)).fetchall()

        session.close()

        return [
            TrainScheduleResponse(
                schedule_id=row[0],
                train_no=row[1],
                station_code=row[2],
                station_name=row[3],
                arrival_time=str(row[4]) if row[4] else None,
                departure_time=str(row[5]) if row[5] else None,
                day_of_journey=row[6],
                distance_from_source=row[7]
            )
            for row in results
        ]
    except Exception as e:
        logger.error(f"Error getting train schedule: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ===============================================
# RUNNING DAYS ENDPOINTS
# ===============================================

@app.get("/v1/running-days/{train_no}")
async def get_train_running_days(
    train_no: int,
    tenant: TenantContext = Depends(get_tenant_context)
):
    """Get running days for a specific train"""
    try:
        session = db_manager.get_session()
        schema_name = tenant.schema_name

        result = session.execute(f"""
            SELECT mon, tue, wed, thu, fri, sat, sun
            FROM {schema_name}.train_running_days
            WHERE train_no = %s
        """, (train_no,)).fetchone()

        session.close()

        if not result:
            raise HTTPException(status_code=404, detail="Train running days not found")

        return {
            "train_no": train_no,
            "running_days": {
                "mon": bool(result[0]),
                "tue": bool(result[1]),
                "wed": bool(result[2]),
                "thu": bool(result[3]),
                "fri": bool(result[4]),
                "sat": bool(result[5]),
                "sun": bool(result[6])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting train running days: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ===============================================
# ROUTE DATA ENDPOINTS
# ===============================================

@app.get("/v1/route-data")
async def get_route_data(
    request: RouteSearchRequest,
    tenant: TenantContext = Depends(get_tenant_context)
):
    """Get all data needed for route finding"""
    try:
        session = db_manager.get_session()
        schema_name = tenant.schema_name

        # Get stations data
        stations = session.execute(f"""
            SELECT station_code, station_name, city, state, is_junction
            FROM {schema_name}.stations_master
            ORDER BY station_name
        """).fetchall()

        # Get train schedule data
        schedule = session.execute(f"""
            SELECT ts.train_no, ts.station_code, ts.station_name,
                   ts.arrival_time, ts.departure_time, ts.day_of_journey,
                   ts.distance_from_source, tm.train_name
            FROM {schema_name}.train_schedule ts
            JOIN {schema_name}.trains_master tm ON ts.train_no = tm.train_no
            ORDER BY ts.train_no, ts.day_of_journey, ts.distance_from_source
        """).fetchall()

        # Get running days data
        running_days = session.execute(f"""
            SELECT train_no, mon, tue, wed, thu, fri, sat, sun
            FROM {schema_name}.train_running_days
        """).fetchall()

        session.close()

        return {
            "stations": [
                {
                    "station_code": row[0],
                    "station_name": row[1],
                    "city": row[2],
                    "state": row[3],
                    "is_junction": bool(row[4])
                }
                for row in stations
            ],
            "train_schedule": [
                {
                    "train_no": row[0],
                    "station_code": row[1],
                    "station_name": row[2],
                    "arrival_time": str(row[3]) if row[3] else None,
                    "departure_time": str(row[4]) if row[4] else None,
                    "day_of_journey": row[5],
                    "distance_from_source": row[6],
                    "train_name": row[7]
                }
                for row in schedule
            ],
            "train_running_days": [
                {
                    "train_no": row[0],
                    "mon": bool(row[1]),
                    "tue": bool(row[2]),
                    "wed": bool(row[3]),
                    "thu": bool(row[4]),
                    "fri": bool(row[5]),
                    "sat": bool(row[6]),
                    "sun": bool(row[7])
                }
                for row in running_days
            ]
        }
    except Exception as e:
        logger.error(f"Error getting route data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ===============================================
# HEALTH CHECK ENDPOINT
# ===============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        session = db_manager.get_session()
        session.execute("SELECT 1").fetchone()
        session.close()

        return {
            "status": "healthy",
            "service": "data-service",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

# ===============================================
# LIFECYCLE MANAGEMENT
# ===============================================

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    global db_manager

    try:
        logger.info("Starting Data Service...")

        # Initialize database connection
        db_manager = DatabaseManager(DATABASE_CONFIG['url'])
        if not db_manager.connect():
            raise Exception("Failed to connect to database")

        logger.info("Data Service started successfully")

    except Exception as e:
        logger.error(f"Failed to start Data Service: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global db_manager

    try:
        if db_manager:
            db_manager.disconnect()
        logger.info("Data Service shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# ===============================================
# MAIN ENTRY POINT
# ===============================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8003")),
        reload=API_CONFIG['debug_mode']
    )