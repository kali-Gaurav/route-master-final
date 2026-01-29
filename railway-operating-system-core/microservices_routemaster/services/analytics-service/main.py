# ===============================================
# ANALYTICS SERVICE
# ===============================================
# Comprehensive data analytics and business intelligence service
# Provides advanced analytics, reporting, and dashboard capabilities

import os
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from uuid import UUID
import json
import pandas as pd
import numpy as np
from collections import defaultdict, Counter

# Add project root to path to enable shared module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, validator
import uvicorn
import httpx

from shared.models import DatabaseManager, Tenant, APIKey, AuditLog
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
    title="Railway OS Analytics Service",
    description="Advanced analytics and business intelligence for railway operations",
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

# ===============================================
# ANALYTICS MODELS
# ===============================================

class AnalyticsQuery(BaseModel):
    """Analytics query model"""
    tenant_id: UUID
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    metrics: List[str] = []
    dimensions: List[str] = []
    filters: Optional[Dict[str, Any]] = None
    group_by: Optional[List[str]] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0

class DashboardData(BaseModel):
    """Dashboard data model"""
    tenant_id: UUID
    dashboard_type: str  # 'overview', 'routes', 'performance', 'revenue'
    date_range: str = '30d'  # '7d', '30d', '90d', '1y'
    include_trends: bool = True

class ReportRequest(BaseModel):
    """Report generation request"""
    tenant_id: UUID
    report_type: str  # 'route_performance', 'revenue_analysis', 'user_engagement', 'system_health'
    format: str = 'json'  # 'json', 'csv', 'pdf', 'excel'
    parameters: Optional[Dict[str, Any]] = None
    email_recipients: Optional[List[str]] = None

class MetricResponse(BaseModel):
    """Analytics metric response"""
    metric_name: str
    value: Any
    change_percentage: Optional[float] = None
    trend: Optional[str] = None  # 'up', 'down', 'stable'
    period: str

class AnalyticsResponse(BaseModel):
    """General analytics response"""
    data: List[Dict[str, Any]]
    total_count: int
    summary: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

# ===============================================
# ANALYTICS ENGINE
# ===============================================

class AnalyticsEngine:
    """Advanced analytics engine for railway data"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def get_route_analytics(self, tenant_id: UUID, start_date: date = None,
                                end_date: date = None) -> Dict[str, Any]:
        """Get comprehensive route analytics"""
        try:
            schema_name = f"tenant_{tenant_id.hex}"

            # Route popularity analysis
            route_popularity_query = f"""
                SELECT
                    origin_station,
                    destination_station,
                    COUNT(*) as search_count,
                    AVG(route_score) as avg_score,
                    MIN(route_score) as min_score,
                    MAX(route_score) as max_score
                FROM {schema_name}.route_searches
                WHERE created_at >= $1 AND created_at <= $2
                GROUP BY origin_station, destination_station
                ORDER BY search_count DESC
                LIMIT 50
            """

            # Transfer pattern analysis
            transfer_analysis_query = f"""
                SELECT
                    transfers,
                    COUNT(*) as route_count,
                    AVG(duration_minutes) as avg_duration,
                    AVG(route_score) as avg_score
                FROM {schema_name}.route_results
                WHERE created_at >= $1 AND created_at <= $2
                GROUP BY transfers
                ORDER BY transfers
            """

            # Peak hours analysis
            peak_hours_query = f"""
                SELECT
                    EXTRACT(hour from created_at) as hour,
                    COUNT(*) as searches,
                    AVG(route_score) as avg_score
                FROM {schema_name}.route_searches
                WHERE created_at >= $1 AND created_at <= $2
                GROUP BY EXTRACT(hour from created_at)
                ORDER BY hour
            """

            # Station connectivity analysis
            station_connectivity_query = f"""
                SELECT
                    station_code,
                    station_name,
                    COUNT(DISTINCT route_id) as routes_served,
                    AVG(popularity_score) as avg_popularity
                FROM {schema_name}.stations s
                LEFT JOIN {schema_name}.route_stations rs ON s.station_id = rs.station_id
                GROUP BY station_code, station_name
                ORDER BY routes_served DESC
                LIMIT 20
            """

            async with self.db_manager.get_session(schema_name) as session:
                # Execute all queries
                route_popularity = await session.fetch(route_popularity_query, start_date, end_date)
                transfer_analysis = await session.fetch(transfer_analysis_query, start_date, end_date)
                peak_hours = await session.fetch(peak_hours_query, start_date, end_date)
                station_connectivity = await session.fetch(station_connectivity_query)

                return {
                    "route_popularity": [dict(row) for row in route_popularity],
                    "transfer_analysis": [dict(row) for row in transfer_analysis],
                    "peak_hours": [dict(row) for row in peak_hours],
                    "station_connectivity": [dict(row) for row in station_connectivity],
                    "generated_at": datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Error getting route analytics: {e}")
            raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

    async def get_performance_metrics(self, tenant_id: UUID, start_date: date = None,
                                    end_date: date = None) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            schema_name = f"tenant_{tenant_id.hex}"

            # API response time analysis
            response_time_query = f"""
                SELECT
                    endpoint,
                    COUNT(*) as total_requests,
                    AVG(response_time_ms) as avg_response_time,
                    MIN(response_time_ms) as min_response_time,
                    MAX(response_time_ms) as max_response_time,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time,
                    SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count
                FROM {schema_name}.api_metrics
                WHERE created_at >= $1 AND created_at <= $2
                GROUP BY endpoint
                ORDER BY total_requests DESC
            """

            # Route search performance
            route_performance_query = f"""
                SELECT
                    COUNT(*) as total_searches,
                    AVG(search_duration_ms) as avg_search_time,
                    MIN(search_duration_ms) as min_search_time,
                    MAX(search_duration_ms) as max_search_time,
                    SUM(CASE WHEN results_found > 0 THEN 1 ELSE 0 END) as successful_searches,
                    AVG(results_found) as avg_results_per_search
                FROM {schema_name}.route_search_metrics
                WHERE created_at >= $1 AND created_at <= $2
            """

            # Cache performance
            cache_performance_query = f"""
                SELECT
                    cache_type,
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits,
                    ROUND(
                        (SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END)::decimal / COUNT(*)) * 100,
                        2
                    ) as hit_rate_percentage
                FROM {schema_name}.cache_metrics
                WHERE created_at >= $1 AND created_at <= $2
                GROUP BY cache_type
            """

            async with self.db_manager.get_session(schema_name) as session:
                response_times = await session.fetch(response_time_query, start_date, end_date)
                route_perf = await session.fetchrow(route_performance_query, start_date, end_date)
                cache_perf = await session.fetch(cache_performance_query, start_date, end_date)

                return {
                    "api_performance": [dict(row) for row in response_times],
                    "route_performance": dict(route_perf) if route_perf else {},
                    "cache_performance": [dict(row) for row in cache_perf],
                    "generated_at": datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            raise HTTPException(status_code=500, detail=f"Performance metrics error: {str(e)}")

    async def get_business_analytics(self, tenant_id: UUID, start_date: date = None,
                                   end_date: date = None) -> Dict[str, Any]:
        """Get business intelligence analytics"""
        try:
            schema_name = f"tenant_{tenant_id.hex}"

            # Revenue analysis (if applicable)
            revenue_query = f"""
                SELECT
                    DATE_TRUNC('month', created_at) as month,
                    COUNT(*) as total_searches,
                    COUNT(DISTINCT user_id) as unique_users,
                    AVG(route_score) as avg_route_score
                FROM {schema_name}.route_searches
                WHERE created_at >= $1 AND created_at <= $2
                GROUP BY DATE_TRUNC('month', created_at)
                ORDER BY month DESC
            """

            # User engagement metrics
            engagement_query = f"""
                SELECT
                    user_type,
                    COUNT(*) as total_actions,
                    COUNT(DISTINCT user_id) as unique_users,
                    AVG(session_duration_minutes) as avg_session_duration,
                    MAX(last_activity) as last_activity
                FROM {schema_name}.user_engagement
                WHERE created_at >= $1 AND created_at <= $2
                GROUP BY user_type
            """

            # Geographic analysis
            geographic_query = f"""
                SELECT
                    region,
                    COUNT(*) as searches,
                    COUNT(DISTINCT user_id) as unique_users,
                    AVG(route_score) as avg_route_score
                FROM {schema_name}.route_searches rs
                JOIN {schema_name}.user_locations ul ON rs.user_id = ul.user_id
                WHERE rs.created_at >= $1 AND rs.created_at <= $2
                GROUP BY region
                ORDER BY searches DESC
            """

            async with self.db_manager.get_session(schema_name) as session:
                revenue_data = await session.fetch(revenue_query, start_date, end_date)
                engagement_data = await session.fetch(engagement_query, start_date, end_date)
                geographic_data = await session.fetch(geographic_query, start_date, end_date)

                return {
                    "revenue_analytics": [dict(row) for row in revenue_data],
                    "user_engagement": [dict(row) for row in engagement_data],
                    "geographic_analysis": [dict(row) for row in geographic_data],
                    "generated_at": datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Error getting business analytics: {e}")
            raise HTTPException(status_code=500, detail=f"Business analytics error: {str(e)}")

    async def generate_report(self, tenant_id: UUID, report_type: str,
                            parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate comprehensive reports"""
        try:
            if report_type == "route_performance":
                return await self.get_route_analytics(tenant_id,
                    parameters.get('start_date'), parameters.get('end_date'))
            elif report_type == "system_performance":
                return await self.get_performance_metrics(tenant_id,
                    parameters.get('start_date'), parameters.get('end_date'))
            elif report_type == "business_intelligence":
                return await self.get_business_analytics(tenant_id,
                    parameters.get('start_date'), parameters.get('end_date'))
            else:
                raise HTTPException(status_code=400, detail=f"Unknown report type: {report_type}")

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise HTTPException(status_code=500, detail=f"Report generation error: {str(e)}")

    async def get_dashboard_data(self, tenant_id: UUID, dashboard_type: str,
                               date_range: str = '30d') -> Dict[str, Any]:
        """Get dashboard data for visualizations"""
        try:
            # Calculate date range
            end_date = date.today()
            if date_range == '7d':
                start_date = end_date - timedelta(days=7)
            elif date_range == '30d':
                start_date = end_date - timedelta(days=30)
            elif date_range == '90d':
                start_date = end_date - timedelta(days=90)
            elif date_range == '1y':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)

            if dashboard_type == 'overview':
                # Get key metrics for overview dashboard
                route_analytics = await self.get_route_analytics(tenant_id, start_date, end_date)
                performance = await self.get_performance_metrics(tenant_id, start_date, end_date)

                return {
                    "total_searches": sum(r['search_count'] for r in route_analytics['route_popularity']),
                    "avg_route_score": np.mean([r['avg_score'] for r in route_analytics['route_popularity'] if r['avg_score']]),
                    "total_stations": len(route_analytics['station_connectivity']),
                    "avg_response_time": np.mean([p['avg_response_time'] for p in performance['api_performance'] if p['avg_response_time']]),
                    "cache_hit_rate": np.mean([c['hit_rate_percentage'] for c in performance['cache_performance'] if c['hit_rate_percentage']]),
                    "charts": {
                        "route_popularity": route_analytics['route_popularity'][:10],
                        "peak_hours": route_analytics['peak_hours'],
                        "transfer_distribution": route_analytics['transfer_analysis']
                    }
                }

            elif dashboard_type == 'routes':
                return await self.get_route_analytics(tenant_id, start_date, end_date)

            elif dashboard_type == 'performance':
                return await self.get_performance_metrics(tenant_id, start_date, end_date)

            elif dashboard_type == 'business':
                return await self.get_business_analytics(tenant_id, start_date, end_date)

            else:
                raise HTTPException(status_code=400, detail=f"Unknown dashboard type: {dashboard_type}")

        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            raise HTTPException(status_code=500, detail=f"Dashboard data error: {str(e)}")

# ===============================================
# DEPENDENCIES
# ===============================================

async def get_db_manager() -> DatabaseManager:
    """Get database manager instance"""
    return DatabaseManager()

async def get_analytics_engine(db_manager: DatabaseManager = Depends(get_db_manager)) -> AnalyticsEngine:
    """Get analytics engine instance"""
    return AnalyticsEngine(db_manager)

# ===============================================
# ANALYTICS ENDPOINTS
# ===============================================

@app.post("/v1/analytics/query", response_model=AnalyticsResponse)
async def query_analytics(
    query: AnalyticsQuery,
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
) -> AnalyticsResponse:
    """Execute custom analytics query"""
    try:
        # This is a simplified implementation - in production, you'd want more sophisticated query building
        if query.metrics == ["route_popularity"]:
            data = await analytics_engine.get_route_analytics(
                query.tenant_id, query.start_date, query.end_date
            )
            return AnalyticsResponse(
                data=data["route_popularity"],
                total_count=len(data["route_popularity"]),
                metadata={"query_type": "route_popularity"}
            )
        elif query.metrics == ["performance"]:
            data = await analytics_engine.get_performance_metrics(
                query.tenant_id, query.start_date, query.end_date
            )
            return AnalyticsResponse(
                data=data["api_performance"],
                total_count=len(data["api_performance"]),
                metadata={"query_type": "performance"}
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported metrics")

    except Exception as e:
        logger.error(f"Error in analytics query: {e}")
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")

@app.get("/v1/dashboard/{dashboard_type}")
async def get_dashboard(
    dashboard_type: str,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    date_range: str = Query("30d", description="Date range (7d, 30d, 90d, 1y)"),
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
) -> Dict[str, Any]:
    """Get dashboard data for visualizations"""
    return await analytics_engine.get_dashboard_data(tenant_id, dashboard_type, date_range)

@app.post("/v1/reports/generate")
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
) -> Dict[str, Any]:
    """Generate and optionally email reports"""
    try:
        report_data = await analytics_engine.generate_report(
            request.tenant_id, request.report_type, request.parameters
        )

        # If email recipients specified, send report via background task
        if request.email_recipients:
            background_tasks.add_task(
                send_report_email,
                request.email_recipients,
                request.report_type,
                report_data,
                request.format
            )

        return {
            "report_id": f"{request.tenant_id}_{request.report_type}_{datetime.utcnow().isoformat()}",
            "report_type": request.report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "data": report_data,
            "email_sent": bool(request.email_recipients)
        }

    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation error: {str(e)}")

@app.get("/v1/analytics/metrics")
async def get_metrics(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    metric_names: List[str] = Query(..., description="Metric names to retrieve"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
) -> List[MetricResponse]:
    """Get specific metrics with trends"""
    try:
        metrics = []

        for metric_name in metric_names:
            if metric_name == "total_searches":
                route_data = await analytics_engine.get_route_analytics(tenant_id, start_date, end_date)
                current_value = sum(r['search_count'] for r in route_data['route_popularity'])
                # Calculate previous period for trend
                prev_start = start_date - timedelta(days=(end_date - start_date).days) if start_date else None
                prev_end = start_date if start_date else None
                if prev_start and prev_end:
                    prev_data = await analytics_engine.get_route_analytics(tenant_id, prev_start, prev_end)
                    prev_value = sum(r['search_count'] for r in prev_data['route_popularity'])
                    change_pct = ((current_value - prev_value) / prev_value * 100) if prev_value > 0 else 0
                    trend = "up" if change_pct > 0 else "down" if change_pct < 0 else "stable"
                else:
                    change_pct = None
                    trend = None

                metrics.append(MetricResponse(
                    metric_name=metric_name,
                    value=current_value,
                    change_percentage=change_pct,
                    trend=trend,
                    period=f"{start_date} to {end_date}" if start_date and end_date else "all_time"
                ))

            elif metric_name == "avg_response_time":
                perf_data = await analytics_engine.get_performance_metrics(tenant_id, start_date, end_date)
                avg_time = np.mean([p['avg_response_time'] for p in perf_data['api_performance'] if p['avg_response_time']])
                metrics.append(MetricResponse(
                    metric_name=metric_name,
                    value=round(avg_time, 2) if not np.isnan(avg_time) else 0,
                    period=f"{start_date} to {end_date}" if start_date and end_date else "all_time"
                ))

        return metrics

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics error: {str(e)}")

@app.get("/v1/analytics/export/{export_type}")
async def export_data(
    export_type: str,
    tenant_id: UUID = Query(..., description="Tenant ID"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
) -> StreamingResponse:
    """Export analytics data in various formats"""
    try:
        if export_type == "route_analytics":
            data = await analytics_engine.get_route_analytics(tenant_id, start_date, end_date)

            # Convert to CSV
            df = pd.DataFrame(data['route_popularity'])
            csv_content = df.to_csv(index=False)

            return StreamingResponse(
                iter([csv_content]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=route_analytics.csv"}
            )

        elif export_type == "performance_metrics":
            data = await analytics_engine.get_performance_metrics(tenant_id, start_date, end_date)

            # Convert to JSON
            json_content = json.dumps(data, indent=2, default=str)

            return StreamingResponse(
                iter([json_content]),
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=performance_metrics.json"}
            )

        else:
            raise HTTPException(status_code=400, detail=f"Unknown export type: {export_type}")

    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

# ===============================================
# UTILITY FUNCTIONS
# ===============================================

async def send_report_email(recipients: List[str], report_type: str,
                          report_data: Dict[str, Any], format: str):
    """Send report via email (placeholder for actual email implementation)"""
    try:
        logger.info(f"Sending {report_type} report to {recipients} in {format} format")
        # In production, integrate with email service like SendGrid, AWS SES, etc.
        # For now, just log the action
    except Exception as e:
        logger.error(f"Error sending report email: {e}")

# ===============================================
# HEALTH CHECKS
# ===============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "analytics-service",
        "timestamp": datetime.utcnow().isoformat()
    }

# ===============================================
# LIFECYCLE EVENTS
# ===============================================

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Analytics Service starting up...")
    # Initialize any background tasks or connections here

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Analytics Service shutting down...")
    # Cleanup connections and resources here

# ===============================================
# MAIN ENTRY POINT
# ===============================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=API_CONFIG['port'],
        reload=API_CONFIG['debug_mode'],
        log_level=API_CONFIG['log_level'].lower()
    )