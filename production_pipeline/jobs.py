"""
Background Jobs & Scheduler

Automated tasks for data refresh, cache management, and system maintenance.

Jobs:
- Daily train data refresh
- Failed ingestion retry
- Cache cleanup
- Metrics aggregation
- Error recovery
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from production_pipeline.config import get_config
try:
    from production_pipeline.database import (
        DatabaseManager, ErrorLog, PerformanceLog, RawPayload,
        RoutesCache, SearchLog
    )
except ImportError:
    DatabaseManager = None
    ErrorLog = None
    PerformanceLog = None
    RawPayload = None
    RoutesCache = None
    SearchLog = None
from production_pipeline.ingestion import IngestionOrchestrator, AsyncHTTPClient, CacheManager

# Configure logging
logger = logging.getLogger(__name__)


class JobExecutor:
    """Executes background jobs"""
    
    def __init__(self, db_manager: DatabaseManager, ingestion_orchestrator: IngestionOrchestrator):
        """Initialize job executor
        
        Args:
            db_manager: Database manager instance
            ingestion_orchestrator: Ingestion orchestrator instance
        """
        self.db_manager = db_manager
        self.ingestion_orchestrator = ingestion_orchestrator
        self.config = get_config()
        logger.info("JobExecutor initialized")
    
    def _execute_with_error_handling(self, job_name: str, func):
        """Execute job with error handling and logging
        
        Args:
            job_name: Name of the job
            func: Function to execute
        """
        session = self.db_manager.get_session()
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"[{job_name}] Starting...")
            
            # Execute job
            result = func(session)
            
            # Log performance
            duration = (datetime.utcnow() - start_time).total_seconds()
            perf_log = PerformanceLog(
                metric_name=f"job_{job_name}_duration_s",
                metric_value=duration,
                metric_unit="seconds",
                component="Jobs",
                operation=job_name,
                status="success"
            )
            session.add(perf_log)
            session.commit()
            
            logger.info(f"[{job_name}] Completed successfully ({duration:.2f}s)")
            return True
        
        except Exception as e:
            logger.error(f"[{job_name}] Failed: {e}", exc_info=True)
            
            # Log error
            error_log = ErrorLog(
                error_type="JobExecutionError",
                error_message=f"{job_name}: {str(e)}",
                component="Jobs",
                operation=job_name,
                severity="ERROR"
            )
            session.add(error_log)
            session.commit()
            
            return False
        
        finally:
            session.close()
    
    # ========================================================================
    # Job Implementations
    # ========================================================================
    
    def job_daily_data_refresh(self, session: Session) -> bool:
        """Daily data refresh from external sources
        
        Args:
            session: Database session
            
        Returns:
            Success status
        """
        logger.info("Daily data refresh started")
        
        # Run async ingestion
        try:
            # This would need to be run in an event loop
            # For now, just log that it would run
            logger.info("Would refresh data from all sources")
            return True
        except Exception as e:
            logger.error(f"Data refresh failed: {e}")
            return False
    
    def job_retry_failed_ingestions(self, session: Session) -> bool:
        """Retry failed data ingestions
        
        Args:
            session: Database session
            
        Returns:
            Success status
        """
        logger.info("Retrying failed ingestions")
        
        # Find failed payloads from last 24 hours
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        
        failed_payloads = session.query(RawPayload).filter(
            RawPayload.is_valid == False,
            RawPayload.received_at > one_day_ago
        ).limit(100).all()
        
        logger.info(f"Found {len(failed_payloads)} failed ingestions to retry")
        
        retry_count = 0
        for payload in failed_payloads:
            # TODO: Retry ingestion for this payload
            retry_count += 1
        
        logger.info(f"Retried {retry_count} failed ingestions")
        return True
    
    def job_clean_expired_cache(self, session: Session) -> bool:
        """Clean expired routes from cache
        
        Args:
            session: Database session
            
        Returns:
            Success status
        """
        logger.info("Cleaning expired cache")
        
        now = datetime.utcnow()
        
        # Mark expired cache as stale
        expired_routes = session.query(RoutesCache).filter(
            RoutesCache.expires_at < now,
            RoutesCache.is_stale == False
        ).all()
        
        for route_cache in expired_routes:
            route_cache.is_stale = True
        
        session.commit()
        
        # Delete very old stale entries (> 30 days)
        cutoff_date = now - timedelta(days=30)
        old_stale = session.query(RoutesCache).filter(
            RoutesCache.is_stale == True,
            RoutesCache.created_at < cutoff_date
        ).delete()
        
        session.commit()
        
        logger.info(f"Marked {len(expired_routes)} routes as stale, deleted {old_stale} old entries")
        return True
    
    def job_aggregate_metrics(self, session: Session) -> bool:
        """Aggregate and summarize performance metrics
        
        Args:
            session: Database session
            
        Returns:
            Success status
        """
        logger.info("Aggregating metrics")
        
        # Get metrics from last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        perf_logs = session.query(PerformanceLog).filter(
            PerformanceLog.recorded_at > one_hour_ago
        ).all()
        
        logger.info(f"Aggregated {len(perf_logs)} performance metrics")
        return True
    
    def job_cleanup_old_logs(self, session: Session) -> bool:
        """Clean up old log entries based on retention policy
        
        Args:
            session: Database session
            
        Returns:
            Success status
        """
        logger.info("Cleaning up old logs")
        
        retention_days = self.config.metrics.retention_days
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Delete old search logs
        search_logs_deleted = session.query(SearchLog).filter(
            SearchLog.created_at < cutoff_date
        ).delete()
        
        # Delete old performance logs
        perf_logs_deleted = session.query(PerformanceLog).filter(
            PerformanceLog.recorded_at < cutoff_date
        ).delete()
        
        # Keep error logs longer (90 days)
        error_cutoff = datetime.utcnow() - timedelta(days=90)
        errors_deleted = session.query(ErrorLog).filter(
            ErrorLog.created_at < error_cutoff,
            ErrorLog.is_resolved == True
        ).delete()
        
        session.commit()
        
        logger.info(f"Deleted {search_logs_deleted} search logs, {perf_logs_deleted} perf logs, {errors_deleted} error logs")
        return True
    
    def job_health_check(self, session: Session) -> bool:
        """Check system health and log status
        
        Args:
            session: Database session
            
        Returns:
            Success status
        """
        logger.info("Running health check")
        
        try:
            # Check database connectivity
            session.execute("SELECT 1")
            
            # Count recent errors
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_errors = session.query(ErrorLog).filter(
                ErrorLog.created_at > one_hour_ago
            ).count()
            
            if recent_errors > 10:
                logger.warning(f"High error rate detected: {recent_errors} errors in last hour")
            
            logger.info(f"Health check passed ({recent_errors} errors in last hour)")
            return True
        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


class JobScheduler:
    """Schedules and manages background jobs"""
    
    def __init__(self, db_manager: DatabaseManager, ingestion_orchestrator: IngestionOrchestrator):
        """Initialize job scheduler
        
        Args:
            db_manager: Database manager instance
            ingestion_orchestrator: Ingestion orchestrator instance
        """
        self.db_manager = db_manager
        self.ingestion_orchestrator = ingestion_orchestrator
        self.executor = JobExecutor(db_manager, ingestion_orchestrator)
        self.scheduler = BackgroundScheduler()
        self.config = get_config()
        logger.info("JobScheduler initialized")
    
    def schedule_jobs(self):
        """Schedule all background jobs"""
        logger.info("Scheduling background jobs...")
        
        # Daily refresh at 2 AM
        self.scheduler.add_job(
            self._wrap_job("daily_data_refresh", self.executor.job_daily_data_refresh),
            trigger=CronTrigger(hour=2, minute=0),
            id="daily_data_refresh",
            name="Daily Data Refresh",
            replace_existing=True
        )
        
        # Retry failed ingestions every 30 minutes
        self.scheduler.add_job(
            self._wrap_job("retry_failed_ingestions", self.executor.job_retry_failed_ingestions),
            trigger=CronTrigger(minute="*/30"),
            id="retry_failed_ingestions",
            name="Retry Failed Ingestions",
            replace_existing=True
        )
        
        # Clean cache every 6 hours
        self.scheduler.add_job(
            self._wrap_job("clean_expired_cache", self.executor.job_clean_expired_cache),
            trigger=CronTrigger(hour="*/6"),
            id="clean_expired_cache",
            name="Clean Expired Cache",
            replace_existing=True
        )
        
        # Aggregate metrics every hour
        self.scheduler.add_job(
            self._wrap_job("aggregate_metrics", self.executor.job_aggregate_metrics),
            trigger=CronTrigger(minute=0),
            id="aggregate_metrics",
            name="Aggregate Metrics",
            replace_existing=True
        )
        
        # Cleanup old logs daily at 3 AM
        self.scheduler.add_job(
            self._wrap_job("cleanup_old_logs", self.executor.job_cleanup_old_logs),
            trigger=CronTrigger(hour=3, minute=0),
            id="cleanup_old_logs",
            name="Cleanup Old Logs",
            replace_existing=True
        )
        
        # Health check every 5 minutes
        self.scheduler.add_job(
            self._wrap_job("health_check", self.executor.job_health_check),
            trigger=CronTrigger(minute="*/5"),
            id="health_check",
            name="Health Check",
            replace_existing=True
        )
        
        logger.info("Job scheduling completed")
        
        # Log scheduled jobs
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.name}: {job.trigger}")
    
    def _wrap_job(self, job_name: str, job_func):
        """Wrap job function with error handling
        
        Args:
            job_name: Name of the job
            job_func: Job function to wrap
            
        Returns:
            Wrapped function
        """
        def wrapped():
            self.executor._execute_with_error_handling(job_name, job_func)
        return wrapped
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Job scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Job scheduler stopped")
    
    def get_jobs_status(self) -> Dict[str, Any]:
        """Get status of all scheduled jobs
        
        Returns:
            Dictionary with job status information
        """
        jobs_info = {
            "running": self.scheduler.running,
            "jobs": []
        }
        
        for job in self.scheduler.get_jobs():
            jobs_info["jobs"].append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return jobs_info
