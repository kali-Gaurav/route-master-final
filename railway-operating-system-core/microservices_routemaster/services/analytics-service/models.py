# ===============================================
# ANALYTICS MODELS
# ===============================================
# Database models for analytics and reporting

from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
import json

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# ===============================================
# ANALYTICS DATA TABLES
# ===============================================

class AnalyticsMetric(Base):
    """Store computed analytics metrics"""
    __tablename__ = "analytics_metrics"

    metric_id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50), nullable=False)  # 'count', 'average', 'percentage', 'duration'
    dimensions = Column(JSONB, nullable=True)  # Additional grouping dimensions
    computed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    metadata = Column(JSONB, nullable=True)  # Additional metric metadata

    __table_args__ = (
        Index('idx_analytics_metrics_tenant_name', 'tenant_id', 'metric_name'),
        Index('idx_analytics_metrics_computed_at', 'computed_at'),
        Index('idx_analytics_metrics_period', 'period_start', 'period_end'),
    )

class AnalyticsReport(Base):
    """Store generated reports"""
    __tablename__ = "analytics_reports"

    report_id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    report_type = Column(String(100), nullable=False)
    report_title = Column(String(255), nullable=False)
    parameters = Column(JSONB, nullable=True)  # Report generation parameters
    data = Column(JSONB, nullable=False)  # Report data
    format = Column(String(20), nullable=False)  # 'json', 'csv', 'pdf', 'excel'
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    generated_by = Column(PGUUID(as_uuid=True), nullable=True)  # User who generated report
    file_path = Column(String(500), nullable=True)  # Path to stored report file
    expires_at = Column(DateTime, nullable=True)  # When report expires

    __table_args__ = (
        Index('idx_analytics_reports_tenant_type', 'tenant_id', 'report_type'),
        Index('idx_analytics_reports_generated_at', 'generated_at'),
    )

class AnalyticsDashboard(Base):
    """Store dashboard configurations"""
    __tablename__ = "analytics_dashboards"

    dashboard_id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    dashboard_name = Column(String(255), nullable=False)
    dashboard_type = Column(String(100), nullable=False)
    config = Column(JSONB, nullable=False)  # Dashboard configuration
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(PGUUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index('idx_analytics_dashboards_tenant', 'tenant_id'),
        Index('idx_analytics_dashboards_type', 'dashboard_type'),
    )

class AnalyticsQuery(Base):
    """Store analytics queries for caching and auditing"""
    __tablename__ = "analytics_queries"

    query_id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    query_hash = Column(String(64), nullable=False, unique=True)  # Hash of query for caching
    query_params = Column(JSONB, nullable=False)  # Query parameters
    result = Column(JSONB, nullable=True)  # Cached result
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    execution_time_ms = Column(Integer, nullable=False)
    cache_expires_at = Column(DateTime, nullable=True)
    is_cached = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index('idx_analytics_queries_tenant_hash', 'tenant_id', 'query_hash'),
        Index('idx_analytics_queries_executed_at', 'executed_at'),
    )

# ===============================================
# METRICS COLLECTION TABLES
# ===============================================

class APIMetrics(Base):
    """API performance metrics"""
    __tablename__ = "api_metrics"

    metric_id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    endpoint = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Float, nullable=False)
    request_size_bytes = Column(Integer, nullable=True)
    response_size_bytes = Column(Integer, nullable=True)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_id = Column(PGUUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_api_metrics_tenant_endpoint', 'tenant_id', 'endpoint'),
        Index('idx_api_metrics_created_at', 'created_at'),
        Index('idx_api_metrics_status', 'status_code'),
    )

class RouteSearchMetrics(Base):
    """Route search performance metrics"""
    __tablename__ = "route_search_metrics"

    metric_id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    search_id = Column(PGUUID(as_uuid=True), nullable=False)
    origin_station = Column(String(10), nullable=False)
    destination_station = Column(String(10), nullable=False)
    search_duration_ms = Column(Float, nullable=False)
    results_found = Column(Integer, nullable=False)
    route_score = Column(Float, nullable=True)
    algorithm_used = Column(String(50), nullable=True)
    cache_hit = Column(Boolean, default=False, nullable=False)
    user_id = Column(PGUUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_route_search_metrics_tenant', 'tenant_id'),
        Index('idx_route_search_metrics_created_at', 'created_at'),
        Index('idx_route_search_metrics_stations', 'origin_station', 'destination_station'),
    )

class CacheMetrics(Base):
    """Cache performance metrics"""
    __tablename__ = "cache_metrics"

    metric_id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    cache_type = Column(String(50), nullable=False)  # 'redis', 'memory', 'database'
    operation = Column(String(20), nullable=False)  # 'get', 'set', 'delete'
    cache_hit = Column(Boolean, nullable=False)
    key_pattern = Column(String(255), nullable=True)
    response_time_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_cache_metrics_tenant_type', 'tenant_id', 'cache_type'),
        Index('idx_cache_metrics_created_at', 'created_at'),
    )

class UserEngagementMetrics(Base):
    """User engagement and behavior metrics"""
    __tablename__ = "user_engagement"

    metric_id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=False)
    user_type = Column(String(50), nullable=True)  # 'registered', 'guest', 'api'
    action = Column(String(100), nullable=False)  # 'search', 'view_route', 'export', etc.
    session_id = Column(String(255), nullable=True)
    session_duration_minutes = Column(Float, nullable=True)
    page_url = Column(String(1000), nullable=True)
    referrer = Column(String(1000), nullable=True)
    device_type = Column(String(50), nullable=True)  # 'desktop', 'mobile', 'tablet'
    browser = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_user_engagement_tenant_user', 'tenant_id', 'user_id'),
        Index('idx_user_engagement_created_at', 'created_at'),
        Index('idx_user_engagement_action', 'action'),
    )

class UserLocation(Base):
    """User geographic location data"""
    __tablename__ = "user_locations"

    location_id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    user_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timezone = Column(String(50), nullable=True)
    isp = Column(String(255), nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_user_locations_tenant', 'tenant_id'),
        Index('idx_user_locations_geo', 'latitude', 'longitude'),
    )

# ===============================================
# BUSINESS INTELLIGENCE TABLES
# ===============================================

class BusinessMetrics(Base):
    """Business intelligence metrics"""
    __tablename__ = "business_metrics"

    metric_id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    category = Column(String(100), nullable=False)  # 'revenue', 'usage', 'performance', 'quality'
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    currency = Column(String(3), nullable=True)  # ISO currency code
    period_type = Column(String(20), nullable=False)  # 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    target_value = Column(Float, nullable=True)  # Target/KPI value
    benchmark_value = Column(Float, nullable=True)  # Industry benchmark
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_business_metrics_tenant_category', 'tenant_id', 'category'),
        Index('idx_business_metrics_period', 'period_start', 'period_end'),
    )

class AlertConfiguration(Base):
    """Analytics alert configurations"""
    __tablename__ = "alert_configurations"

    alert_id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    alert_name = Column(String(255), nullable=False)
    metric_name = Column(String(100), nullable=False)
    condition = Column(String(50), nullable=False)  # 'above', 'below', 'equals', 'changes_by'
    threshold_value = Column(Float, nullable=False)
    comparison_period = Column(String(50), nullable=True)  # 'previous_day', 'previous_week', etc.
    severity = Column(String(20), nullable=False)  # 'low', 'medium', 'high', 'critical'
    enabled = Column(Boolean, default=True, nullable=False)
    notification_channels = Column(JSONB, nullable=True)  # ['email', 'slack', 'webhook']
    notification_targets = Column(JSONB, nullable=True)  # Email addresses, webhook URLs, etc.
    cooldown_minutes = Column(Integer, default=60, nullable=False)  # Prevent alert spam
    last_triggered = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_alert_configurations_tenant', 'tenant_id'),
        Index('idx_alert_configurations_metric', 'metric_name'),
    )

class AlertHistory(Base):
    """Alert trigger history"""
    __tablename__ = "alert_history"

    history_id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    alert_id = Column(PGUUID(as_uuid=True), ForeignKey('alert_configurations.alert_id'), nullable=False)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    triggered_value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=False)
    condition = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    notification_sent = Column(Boolean, default=False, nullable=False)
    notification_details = Column(JSONB, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    alert_config = relationship("AlertConfiguration")

    __table_args__ = (
        Index('idx_alert_history_tenant', 'tenant_id'),
        Index('idx_alert_history_alert', 'alert_id'),
        Index('idx_alert_history_created_at', 'created_at'),
    )

# ===============================================
# DATA EXPORT TABLES
# ===============================================

class DataExport(Base):
    """Track data export operations"""
    __tablename__ = "data_exports"

    export_id = Column(PGUUID(as_uuid=True), primary_key=True, default=UUID)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    export_type = Column(String(100), nullable=False)  # 'analytics', 'metrics', 'reports'
    format = Column(String(20), nullable=False)  # 'csv', 'json', 'excel', 'pdf'
    parameters = Column(JSONB, nullable=True)  # Export parameters
    file_path = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    record_count = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False)  # 'pending', 'processing', 'completed', 'failed'
    error_message = Column(Text, nullable=True)
    requested_by = Column(PGUUID(as_uuid=True), nullable=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_data_exports_tenant', 'tenant_id'),
        Index('idx_data_exports_status', 'status'),
        Index('idx_data_exports_created_at', 'created_at'),
    )

# ===============================================
# ANALYTICS FUNCTIONS
# ===============================================

def create_analytics_tables(engine):
    """Create all analytics tables"""
    Base.metadata.create_all(bind=engine)

def drop_analytics_tables(engine):
    """Drop all analytics tables"""
    Base.metadata.drop_all(bind=engine)

# ===============================================
# UTILITY FUNCTIONS
# ===============================================

def get_metric_trend(current_value: float, previous_value: float) -> str:
    """Calculate metric trend"""
    if previous_value == 0:
        return "stable"
    change = (current_value - previous_value) / previous_value
    if change > 0.05:  # 5% increase
        return "up"
    elif change < -0.05:  # 5% decrease
        return "down"
    else:
        return "stable"

def calculate_percentage_change(current: float, previous: float) -> Optional[float]:
    """Calculate percentage change between two values"""
    if previous == 0:
        return None
    return round(((current - previous) / previous) * 100, 2)