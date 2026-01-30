"""
Analytics Service Package
Advanced analytics and business intelligence for Railway Operating System
"""

__version__ = "1.0.0"
__author__ = "Railway OS Development Team"

from .main import app
from .models import (
    AnalyticsMetric, AnalyticsReport, AnalyticsDashboard,
    APIMetrics, RouteSearchMetrics, CacheMetrics,
    UserEngagementMetrics, BusinessMetrics
)
from .dashboard import Dashboard, ReportGenerator
from .etl_pipeline import AnalyticsETLPipeline, DataQualityChecker

__all__ = [
    'app',
    'AnalyticsMetric',
    'AnalyticsReport',
    'AnalyticsDashboard',
    'APIMetrics',
    'RouteSearchMetrics',
    'CacheMetrics',
    'UserEngagementMetrics',
    'BusinessMetrics',
    'Dashboard',
    'ReportGenerator',
    'AnalyticsETLPipeline',
    'DataQualityChecker'
]