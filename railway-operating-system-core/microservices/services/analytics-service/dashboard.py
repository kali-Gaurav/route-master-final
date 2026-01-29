"""
Dashboard configuration and rendering engine
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from uuid import UUID
import json
import numpy as np

class Dashboard:
    """Dashboard configuration manager"""

    DASHBOARD_TEMPLATES = {
        "overview": {
            "title": "Railway Operations Overview",
            "widgets": [
                {
                    "id": "total_searches",
                    "type": "metric",
                    "title": "Total Searches",
                    "metric": "total_searches"
                },
                {
                    "id": "avg_route_score",
                    "type": "metric",
                    "title": "Average Route Score",
                    "metric": "avg_route_score"
                },
                {
                    "id": "cache_hit_rate",
                    "type": "metric",
                    "title": "Cache Hit Rate",
                    "metric": "cache_hit_rate"
                },
                {
                    "id": "route_popularity",
                    "type": "chart",
                    "chart_type": "bar",
                    "title": "Route Popularity",
                    "data_key": "route_popularity"
                },
                {
                    "id": "peak_hours",
                    "type": "chart",
                    "chart_type": "line",
                    "title": "Peak Hours Distribution",
                    "data_key": "peak_hours"
                },
                {
                    "id": "transfer_distribution",
                    "type": "chart",
                    "chart_type": "pie",
                    "title": "Transfer Distribution",
                    "data_key": "transfer_distribution"
                }
            ]
        },
        "performance": {
            "title": "System Performance",
            "widgets": [
                {
                    "id": "avg_response_time",
                    "type": "metric",
                    "title": "Average Response Time (ms)",
                    "metric": "avg_response_time"
                },
                {
                    "id": "error_rate",
                    "type": "metric",
                    "title": "Error Rate",
                    "metric": "error_rate"
                },
                {
                    "id": "api_performance",
                    "type": "chart",
                    "chart_type": "bar",
                    "title": "API Endpoint Performance",
                    "data_key": "api_performance"
                },
                {
                    "id": "cache_performance",
                    "type": "chart",
                    "chart_type": "line",
                    "title": "Cache Hit Rates",
                    "data_key": "cache_performance"
                }
            ]
        },
        "business": {
            "title": "Business Intelligence",
            "widgets": [
                {
                    "id": "monthly_searches",
                    "type": "chart",
                    "chart_type": "line",
                    "title": "Monthly Search Volume",
                    "data_key": "revenue_analytics"
                },
                {
                    "id": "user_engagement",
                    "type": "chart",
                    "chart_type": "bar",
                    "title": "User Engagement by Type",
                    "data_key": "user_engagement"
                },
                {
                    "id": "geographic_analysis",
                    "type": "chart",
                    "chart_type": "map",
                    "title": "Geographic Distribution",
                    "data_key": "geographic_analysis"
                }
            ]
        },
        "routes": {
            "title": "Route Analytics",
            "widgets": [
                {
                    "id": "top_routes",
                    "type": "chart",
                    "chart_type": "table",
                    "title": "Top 20 Routes",
                    "data_key": "route_popularity"
                },
                {
                    "id": "station_connectivity",
                    "type": "chart",
                    "chart_type": "network",
                    "title": "Station Connectivity Network",
                    "data_key": "station_connectivity"
                }
            ]
        }
    }

    @classmethod
    def get_dashboard_template(cls, dashboard_type: str) -> Dict[str, Any]:
        """Get dashboard template"""
        return cls.DASHBOARD_TEMPLATES.get(dashboard_type, cls.DASHBOARD_TEMPLATES["overview"])

    @classmethod
    def create_dashboard_html(cls, dashboard_data: Dict[str, Any], dashboard_type: str) -> str:
        """Create HTML representation of dashboard"""
        template = cls.get_dashboard_template(dashboard_type)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{template['title']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .dashboard {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }}
                .widget {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
                .metric {{ font-size: 24px; font-weight: bold; color: #0066cc; }}
                .trend {{ font-size: 12px; color: #666; }}
                .chart {{ min-height: 300px; }}
            </style>
        </head>
        <body>
            <h1>{template['title']}</h1>
            <div class="dashboard">
        """

        for widget in template['widgets']:
            html += cls._render_widget(widget, dashboard_data)

        html += """
            </div>
        </body>
        </html>
        """
        return html

    @classmethod
    def _render_widget(cls, widget: Dict[str, Any], data: Dict[str, Any]) -> str:
        """Render individual widget"""
        widget_type = widget.get('type')

        if widget_type == 'metric':
            return f"""
            <div class="widget">
                <h3>{widget['title']}</h3>
                <div class="metric">{data.get(widget['metric'], 'N/A')}</div>
                <div class="trend">Data updated recently</div>
            </div>
            """
        elif widget_type == 'chart':
            return f"""
            <div class="widget">
                <h3>{widget['title']}</h3>
                <div class="chart" id="{widget['id']}">
                    Chart: {widget.get('chart_type', 'unknown')}
                </div>
            </div>
            """
        else:
            return f"""
            <div class="widget">
                <h3>{widget['title']}</h3>
                <p>Widget type not supported</p>
            </div>
            """

class ReportGenerator:
    """Generate various types of reports"""

    @staticmethod
    def generate_route_performance_report(data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate route performance report"""
        return {
            "report_type": "route_performance",
            "title": "Route Performance Report",
            "sections": [
                {
                    "title": "Executive Summary",
                    "content": {
                        "total_routes_analyzed": len(data.get('route_popularity', [])),
                        "average_route_score": np.mean([r.get('avg_score', 0) for r in data.get('route_popularity', [])]) if data.get('route_popularity') else 0,
                        "top_route": data.get('route_popularity', [{}])[0] if data.get('route_popularity') else {}
                    }
                },
                {
                    "title": "Route Popularity",
                    "data": data.get('route_popularity', [])
                },
                {
                    "title": "Transfer Patterns",
                    "data": data.get('transfer_analysis', [])
                },
                {
                    "title": "Peak Hours",
                    "data": data.get('peak_hours', [])
                }
            ],
            "generated_at": datetime.utcnow().isoformat()
        }

    @staticmethod
    def generate_system_health_report(data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate system health report"""
        return {
            "report_type": "system_health",
            "title": "System Health Report",
            "sections": [
                {
                    "title": "Performance Metrics",
                    "data": data.get('api_performance', [])
                },
                {
                    "title": "Cache Performance",
                    "data": data.get('cache_performance', [])
                },
                {
                    "title": "Route Search Performance",
                    "data": data.get('route_performance', {})
                }
            ],
            "generated_at": datetime.utcnow().isoformat()
        }

    @staticmethod
    def generate_business_intelligence_report(data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate business intelligence report"""
        return {
            "report_type": "business_intelligence",
            "title": "Business Intelligence Report",
            "sections": [
                {
                    "title": "Revenue Analytics",
                    "data": data.get('revenue_analytics', [])
                },
                {
                    "title": "User Engagement",
                    "data": data.get('user_engagement', [])
                },
                {
                    "title": "Geographic Analysis",
                    "data": data.get('geographic_analysis', [])
                }
            ],
            "generated_at": datetime.utcnow().isoformat()
        }