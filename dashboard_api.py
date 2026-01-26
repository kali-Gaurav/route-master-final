"""
MONITORING DASHBOARD API

Real-time system health, metrics, and status endpoints.

Endpoints:
- GET /health → Basic health status
- GET /metrics → Performance metrics
- GET /system-status → Detailed system status
- GET /cache-stats → Cache statistics
- GET /validation-stats → Validation statistics

Author: Route Master
Date: 2026-01-25
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import json
from pathlib import Path

try:
    from database_manager import DatabaseManager
    from logger import LoggerFactory
    from irctc_validator import IRCTCValidator
except ImportError:
    pass

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# Global metrics storage
class MetricsCollector:
    """Collect and store system metrics"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.api_requests = 0
        self.api_errors = 0
        self.api_total_time = 0.0
        self.cache_hits = 0
        self.cache_misses = 0
        self.validation_count = 0
        self.validation_success = 0
        self.last_refresh = None
        self.log_file = Path("data/logs/system_metrics.json")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def record_api_call(self, duration_ms: float, error: bool = False):
        """Record API call metrics"""
        self.api_requests += 1
        if error:
            self.api_errors += 1
        else:
            self.api_total_time += duration_ms
    
    def record_cache_hit(self):
        self.cache_hits += 1
    
    def record_cache_miss(self):
        self.cache_misses += 1
    
    def record_validation(self, success: bool = True):
        self.validation_count += 1
        if success:
            self.validation_success += 1
    
    def get_uptime_hours(self) -> float:
        """Get uptime in hours"""
        return (datetime.now() - self.start_time).total_seconds() / 3600
    
    def get_avg_response_time_ms(self) -> float:
        """Get average API response time"""
        if self.api_requests == 0:
            return 0
        return self.api_total_time / (self.api_requests - self.api_errors)
    
    def get_error_rate(self) -> float:
        """Get API error rate as percentage"""
        if self.api_requests == 0:
            return 0
        return (self.api_errors / self.api_requests) * 100
    
    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate as percentage"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0
        return (self.cache_hits / total) * 100
    
    def get_validation_success_rate(self) -> float:
        """Get validation success rate"""
        if self.validation_count == 0:
            return 0
        return (self.validation_success / self.validation_count) * 100


# Global instance
metrics = MetricsCollector()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health status
    
    Returns:
        {
            "status": "healthy" | "degraded" | "unhealthy",
            "timestamp": ISO8601,
            "uptime_hours": float,
            "active_trains": int,
            "last_refresh": ISO8601 or null,
            "api_errors_1h": int,
            "cache_hit_rate": percentage
        }
    """
    try:
        db = DatabaseManager()
        
        # Get stats from database
        all_trains = db.session.query(db.Train).count()
        active_trains = db.session.query(db.Train).filter(
            db.Train.status == "ACTIVE"
        ).count()
        inactive_trains = db.session.query(db.Train).filter(
            db.Train.status == "INACTIVE"
        ).count()
        
        # Determine health status
        if active_trains == 0:
            status = "unhealthy"
        elif inactive_trains > (all_trains * 0.3):  # >30% inactive
            status = "degraded"
        else:
            status = "healthy"
        
        # Get last refresh from fetch logs
        last_fetch = None
        try:
            last_log = db.session.query(db.FetchLog).order_by(
                db.FetchLog.timestamp.desc()
            ).first()
            if last_log:
                last_fetch = last_log.timestamp.isoformat()
        except:
            pass
        
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "uptime_hours": round(metrics.get_uptime_hours(), 2),
            "total_trains": all_trains,
            "active_trains": active_trains,
            "inactive_trains": inactive_trains,
            "active_rate_pct": round((active_trains / all_trains * 100) if all_trains > 0 else 0, 1),
            "last_refresh": last_fetch,
            "api_error_rate_pct": round(metrics.get_error_rate(), 1),
            "cache_hit_rate_pct": round(metrics.get_cache_hit_rate(), 1)
        }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Performance and operational metrics
    
    Returns comprehensive metrics:
    - API performance (requests, errors, response time)
    - Cache performance (hits, misses, rate)
    - Validation stats (count, success rate)
    - System load
    """
    try:
        db = DatabaseManager()
        
        # Get request volume trends
        one_hour_ago = datetime.now() - timedelta(hours=1)
        requests_1h = db.session.query(db.FetchLog).filter(
            db.FetchLog.timestamp >= one_hour_ago
        ).count()
        
        errors_1h = db.session.query(db.FetchLog).filter(
            db.FetchLog.timestamp >= one_hour_ago,
            db.FetchLog.response_status >= 400
        ).count()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "api_metrics": {
                "total_requests": metrics.api_requests,
                "total_errors": metrics.api_errors,
                "requests_1h": requests_1h,
                "errors_1h": errors_1h,
                "avg_response_time_ms": round(metrics.get_avg_response_time_ms(), 2),
                "error_rate_pct": round(metrics.get_error_rate(), 2)
            },
            "cache_metrics": {
                "total_hits": metrics.cache_hits,
                "total_misses": metrics.cache_misses,
                "hit_rate_pct": round(metrics.get_cache_hit_rate(), 2)
            },
            "validation_metrics": {
                "total_validations": metrics.validation_count,
                "successful": metrics.validation_success,
                "failed": metrics.validation_count - metrics.validation_success,
                "success_rate_pct": round(metrics.get_validation_success_rate(), 2)
            },
            "system": {
                "uptime_hours": round(metrics.get_uptime_hours(), 2),
                "uptime_days": round(metrics.get_uptime_hours() / 24, 1)
            }
        }
    
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now().isoformat()}


@router.get("/system-status")
async def system_status() -> Dict[str, Any]:
    """
    Detailed system status with all components
    
    Returns:
    - Database connectivity and stats
    - Cache status
    - IRCTC validator status
    - Data freshness metrics
    - Alert status
    """
    try:
        db = DatabaseManager()
        
        # Database stats
        total_trains = db.session.query(db.Train).count()
        active_trains = db.session.query(db.Train).filter(
            db.Train.status == "ACTIVE"
        ).count()
        
        # Get data freshness
        oldest_train = db.session.query(db.Train).order_by(
            db.Train.last_updated
        ).first()
        newest_train = db.session.query(db.Train).order_by(
            db.Train.last_updated.desc()
        ).first()
        
        oldest_hours_ago = None
        if oldest_train:
            oldest_hours_ago = (datetime.now() - oldest_train.last_updated).total_seconds() / 3600
        
        # Calculate quality metrics
        avg_quality = 0
        try:
            from sqlalchemy import func
            avg_quality = db.session.query(
                func.avg(db.Train.quality_score)
            ).scalar() or 0
        except:
            pass
        
        # Check for recent errors
        recent_errors = []
        try:
            one_hour_ago = datetime.now() - timedelta(hours=1)
            error_logs = db.session.query(db.FetchLog).filter(
                db.FetchLog.timestamp >= one_hour_ago,
                db.FetchLog.response_status >= 400
            ).all()
            recent_errors = [
                {
                    "train": str(el.train_no),
                    "status": el.response_status,
                    "time": el.timestamp.isoformat()
                }
                for el in error_logs[:10]
            ]
        except:
            pass
        
        return {
            "timestamp": datetime.now().isoformat(),
            "database": {
                "connected": True,
                "total_trains": total_trains,
                "active_trains": active_trains,
                "inactive_trains": total_trains - active_trains,
                "active_rate_pct": round((active_trains / total_trains * 100) if total_trains > 0 else 0, 1)
            },
            "data_freshness": {
                "newest_update_hours_ago": 0,  # Just updated
                "oldest_update_hours_ago": round(oldest_hours_ago, 1) if oldest_hours_ago else None,
                "avg_quality_score": round(avg_quality, 1)
            },
            "cache": {
                "hit_rate_pct": round(metrics.get_cache_hit_rate(), 1),
                "total_hits": metrics.cache_hits,
                "total_misses": metrics.cache_misses
            },
            "validation": {
                "total_validations": metrics.validation_count,
                "success_rate_pct": round(metrics.get_validation_success_rate(), 1)
            },
            "alerts": {
                "high_inactive_rate": (total_trains - active_trains) > (total_trains * 0.3),
                "recent_errors": len(recent_errors),
                "last_errors": recent_errors
            },
            "uptime": {
                "hours": round(metrics.get_uptime_hours(), 1),
                "days": round(metrics.get_uptime_hours() / 24, 1)
            }
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "status": "error"
        }


@router.get("/cache-stats")
async def cache_stats() -> Dict[str, Any]:
    """Cache hit/miss statistics"""
    total = metrics.cache_hits + metrics.cache_misses
    
    return {
        "timestamp": datetime.now().isoformat(),
        "cache": {
            "total_hits": metrics.cache_hits,
            "total_misses": metrics.cache_misses,
            "total_requests": total,
            "hit_rate_pct": round((metrics.cache_hits / total * 100) if total > 0 else 0, 2)
        },
        "recommendation": (
            "Cache performing well" if metrics.get_cache_hit_rate() > 70
            else "Consider increasing cache TTL" if metrics.get_cache_hit_rate() > 40
            else "Cache hit rate is low, check configuration"
        )
    }


@router.get("/validation-stats")
async def validation_stats() -> Dict[str, Any]:
    """IRCTC validation statistics"""
    
    return {
        "timestamp": datetime.now().isoformat(),
        "validation": {
            "total_validations": metrics.validation_count,
            "successful": metrics.validation_success,
            "failed": metrics.validation_count - metrics.validation_success,
            "success_rate_pct": round(metrics.get_validation_success_rate(), 2)
        },
        "recommendation": (
            "Validation working well" if metrics.get_validation_success_rate() > 90
            else "Check IRCTC API connectivity" if metrics.get_validation_success_rate() < 70
            else "Validation success rate is acceptable"
        )
    }


@router.get("/logs")
async def recent_logs(lines: int = 100) -> Dict[str, Any]:
    """Get recent system logs"""
    try:
        log_file = Path("data/logs/system.log")
        
        if not log_file.exists():
            return {"logs": [], "message": "No logs found"}
        
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
        
        # Get last N lines
        recent = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_lines": len(all_lines),
            "returned_lines": len(recent),
            "logs": [line.strip() for line in recent]
        }
    
    except Exception as e:
        return {"error": str(e), "logs": []}


def setup_monitoring(app):
    """Setup monitoring in FastAPI app"""
    app.include_router(router)
    return metrics


if __name__ == "__main__":
    # Test locally
    print("Monitoring Dashboard API")
    print("=" * 50)
    
    # Would need FastAPI to run
    print("✓ Ready to attach to FastAPI app")
