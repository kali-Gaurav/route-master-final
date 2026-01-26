"""
Automated Scheduler for Living Dataset Pipeline

Runs on schedule:
- Weekly full refresh: Validate UNKNOWN trains, refresh >30-day-old trains
- Daily backups: Create database backups
- Daily health checks: Monitor system metrics
- Hourly cache cleanup: Remove expired cache entries

Uses APScheduler for reliable task scheduling
"""

import sys
from datetime import datetime, timedelta
from typing import Dict, Optional
import time

try:
    from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
    from apscheduler.triggers.cron import CronTrigger  # type: ignore
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False
    print("⚠️  APScheduler not installed. Install with: pip install apscheduler")

from config import SCHEDULER_CONFIG
from logger import LoggerFactory, audit_logger
from database import db, Train, TrainStatus
from refresh_policy import refresh_engine
from rappid_fetcher import fetcher
from incremental_updater import incremental_updater
from validator import validator
from quality_scorer import scorer
from backup_manager import backup_manager
from alerting_system import alertingSystem

scheduler_logger = LoggerFactory.get_logger("scheduler")


class DataPipelineScheduler:
    """Main scheduler for the living dataset pipeline"""
    
    def __init__(self):
        self.logger = LoggerFactory.get_logger("scheduler")
        self.scheduler = None
        self.is_running = False
        self.last_refresh_time = None
        self.refresh_stats = {
            "weekly_refreshes": 0,
            "trains_refreshed": 0,
            "api_calls_made": 0,
            "errors_encountered": 0
        }
        
        if HAS_APSCHEDULER:
            self.scheduler = BackgroundScheduler()
        else:
            self.logger.warning("APScheduler not available - scheduler will run in manual mode")
    
    def schedule_weekly_refresh(self):
        """Schedule weekly full refresh"""
        if not HAS_APSCHEDULER:
            self.logger.warning("APScheduler required for scheduled refresh")
            return
        
        day = SCHEDULER_CONFIG.get("weekly_refresh_day", "sunday").lower()
        time_str = SCHEDULER_CONFIG.get("weekly_refresh_time", "02:00")
        hour, minute = map(int, time_str.split(":"))
        
        trigger = CronTrigger(day_of_week=day, hour=hour, minute=minute)
        self.scheduler.add_job(
            self.run_weekly_refresh,
            trigger=trigger,
            id="weekly_refresh",
            name="Weekly Dataset Refresh",
            misfire_grace_time=600
        )
        
        self.logger.info(
            f"Weekly refresh scheduled for {day} at {time_str} UTC",
            extra={"day": day, "time": time_str}
        )
    
    def schedule_daily_backups(self):
        """Schedule daily database backups"""
        if not HAS_APSCHEDULER:
            return
        
        self.scheduler.add_job(
            self.run_daily_backup,
            trigger=CronTrigger(hour=3, minute=0),  # 03:00 UTC
            id="daily_backup",
            name="Daily Database Backup",
            misfire_grace_time=600
        )
        
        self.logger.info("Daily backups scheduled for 03:00 UTC")
    
    def schedule_health_checks(self):
        """Schedule periodic health checks"""
        if not HAS_APSCHEDULER:
            return
        
        interval_minutes = SCHEDULER_CONFIG.get("health_check_interval_minutes", 30)
        
        self.scheduler.add_job(
            self.run_health_check,
            trigger=CronTrigger(minute=f"*/{interval_minutes}"),
            id="health_check",
            name="System Health Check",
            misfire_grace_time=60
        )
        
        self.logger.info(f"Health checks scheduled every {interval_minutes} minutes")
    
    def schedule_daily_validation(self):
        """Schedule daily data validation"""
        if not HAS_APSCHEDULER:
            return
        
        time_str = SCHEDULER_CONFIG.get("daily_validation_time", "12:00")
        hour, minute = map(int, time_str.split(":"))
        
        self.scheduler.add_job(
            self.run_daily_validation,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="daily_validation",
            name="Daily Data Validation",
            misfire_grace_time=600
        )
        
        self.logger.info(f"Daily validation scheduled for {time_str} UTC")
    
    def run_weekly_refresh(self) -> Dict:
        """Execute weekly refresh cycle"""
        start_time = datetime.utcnow()
        self.logger.info("=" * 60)
        self.logger.info("STARTING WEEKLY REFRESH CYCLE")
        self.logger.info("=" * 60)
        
        stats = {
            "start_time": start_time.isoformat(),
            "trains_total": 0,
            "trains_refreshed": 0,
            "trains_skipped": 0,
            "api_calls": 0,
            "errors": 0,
            "duration_seconds": 0
        }
        
        try:
            session = db.get_session()
            
            # Get all trains
            all_trains = session.query(Train).all()
            stats["trains_total"] = len(all_trains)
            
            self.logger.info(f"Found {len(all_trains)} trains to process")
            
            # Get refresh decisions
            train_dicts = [
                {
                    "train_no": t.train_no,
                    "status": t.status,
                    "last_updated": t.last_updated,
                    "last_fetched": t.last_fetched,
                    "is_frequently_searched": False
                }
                for t in all_trains
            ]
            
            decisions = refresh_engine.batch_refresh_decisions(train_dicts)
            
            # Log report
            report = refresh_engine.generate_refresh_report(decisions)
            self.logger.info(report, extra={"report": report})
            
            # Prioritize
            trains_to_refresh = refresh_engine.prioritize_refresh_batch(decisions)
            self.logger.info(f"Prioritized {len(trains_to_refresh)} trains for refresh")
            
            # Fetch and update
            for i, train_no in enumerate(trains_to_refresh[:50]):  # Limit to 50 per cycle
                try:
                    success, data, error = fetcher.fetch_train_details(train_no)
                    stats["api_calls"] += 1
                    
                    if success and data:
                        fetcher.save_raw_response(train_no, data)
                        stats["trains_refreshed"] += 1
                        
                        # Validate
                        structured = incremental_updater._transform_to_structured(train_no, data)
                        val_report = validator.validate_trains([structured])
                        
                        # Score
                        quality_score = scorer.score_train(structured)
                        
                        # Update database
                        train = session.query(Train).filter(Train.train_no == train_no).first()
                        if train:
                            train.status = TrainStatus.ACTIVE
                            train.last_fetched = datetime.utcnow()
                            train.data_quality_score = quality_score.overall_score
                            train.is_verified = True
                            session.commit()
                        
                        if (i + 1) % 10 == 0:
                            self.logger.info(f"Progress: {i + 1}/{len(trains_to_refresh)}")
                    
                    else:
                        stats["trains_skipped"] += 1
                        if error:
                            self.logger.warning(f"Failed to fetch {train_no}: {error}")
                            stats["errors"] += 1
                
                except Exception as e:
                    stats["errors"] += 1
                    self.logger.error(f"Error processing {train_no}: {e}", exc_info=True)
            
            # Cleanup old backups
            deleted, kept = backup_manager.cleanup_old_backups()
            self.logger.info(f"Backup cleanup: deleted {deleted}, kept {kept}")
            
            # Check alerts
            inactive_count = session.query(Train).filter(
                Train.status == TrainStatus.INACTIVE
            ).count()
            active_count = session.query(Train).filter(
                Train.status == TrainStatus.ACTIVE
            ).count()
            
            alert = alertingSystem.check_inactive_trains_threshold(
                stats["trains_total"], inactive_count
            )
            if alert:
                alertingSystem.send_alert(alert)
            
            # Calculate duration
            stats["duration_seconds"] = (datetime.utcnow() - start_time).total_seconds()
            
            # Log success
            self.logger.info(
                "WEEKLY REFRESH COMPLETED SUCCESSFULLY",
                extra=stats
            )
            
            # Audit log
            audit_logger.log_data_modification(
                operation="weekly_refresh",
                table="trains",
                records_affected=stats["trains_refreshed"],
                changes={
                    "trains_refreshed": stats["trains_refreshed"],
                    "trains_skipped": stats["trains_skipped"],
                    "api_calls": stats["api_calls"],
                    "duration_seconds": stats["duration_seconds"]
                }
            )
            
            # Update tracking
            self.last_refresh_time = datetime.utcnow()
            self.refresh_stats["weekly_refreshes"] += 1
            self.refresh_stats["trains_refreshed"] += stats["trains_refreshed"]
            self.refresh_stats["api_calls_made"] += stats["api_calls"]
            self.refresh_stats["errors_encountered"] += stats["errors"]
            
            return stats
        
        except Exception as e:
            stats["errors"] += 1
            self.logger.error(f"Weekly refresh failed: {e}", exc_info=True)
            audit_logger.log_error_event(
                error_type="WEEKLY_REFRESH_FAILURE",
                message=f"Weekly refresh failed: {str(e)}",
                context=stats,
                severity="CRITICAL"
            )
            return stats
        
        finally:
            session.close()
    
    def run_daily_backup(self) -> bool:
        """Execute daily backup"""
        try:
            self.logger.info("Starting daily backup")
            backup_path = backup_manager.create_backup()
            
            if backup_path:
                is_valid = backup_manager.verify_backup(backup_path)
                if is_valid:
                    self.logger.info(f"Daily backup completed successfully: {backup_path}")
                    return True
                else:
                    self.logger.error("Backup verification failed")
                    audit_logger.log_error_event(
                        error_type="BACKUP_VERIFICATION_FAILURE",
                        message="Daily backup verification failed",
                        context={"backup_file": str(backup_path)},
                        severity="CRITICAL"
                    )
                    return False
            return False
        
        except Exception as e:
            self.logger.error(f"Daily backup failed: {e}", exc_info=True)
            return False
    
    def run_health_check(self):
        """Execute system health check"""
        try:
            session = db.get_session()
            
            total = session.query(Train).count()
            active = session.query(Train).filter(Train.status == TrainStatus.ACTIVE).count()
            inactive = session.query(Train).filter(Train.status == TrainStatus.INACTIVE).count()
            unknown = session.query(Train).filter(Train.status == TrainStatus.UNKNOWN).count()
            
            # Calculate freshness
            from datetime import datetime, timedelta
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            fresh_count = session.query(Train).filter(
                Train.last_updated >= recent_cutoff
            ).count()
            freshness_percent = (fresh_count / total * 100) if total > 0 else 0
            
            health_status = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_trains": total,
                "active_trains": active,
                "inactive_trains": inactive,
                "unknown_trains": unknown,
                "freshness_percent": freshness_percent,
                "last_refresh": self.last_refresh_time.isoformat() if self.last_refresh_time else None,
                "scheduler_stats": self.refresh_stats
            }
            
            self.logger.info(
                "Health check completed",
                extra=health_status
            )
            
            # Check thresholds
            if freshness_percent < 60:
                alert = alertingSystem.check_data_freshness(freshness_percent / 100)
                if alert:
                    alertingSystem.send_alert(alert)
            
            session.close()
            return health_status
        
        except Exception as e:
            self.logger.error(f"Health check failed: {e}", exc_info=True)
            return None
    
    def run_daily_validation(self):
        """Execute daily data validation"""
        try:
            self.logger.info("Starting daily validation")
            
            session = db.get_session()
            trains = session.query(Train).limit(100).all()
            
            train_dicts = [
                {
                    "train_no": t.train_no,
                    "train_name": t.train_name,
                    "status": t.status.value if t.status else "UNKNOWN",
                    "last_updated": t.last_updated
                }
                for t in trains
            ]
            
            report = validator.validate_trains(train_dicts)
            validator.save_report(report)
            
            self.logger.info(
                f"Daily validation completed: {report.error_count} errors, {report.warning_count} warnings"
            )
            
            # Check thresholds
            if report.error_count > 100:
                alert = alertingSystem.check_validation_errors(report.error_count)
                if alert:
                    alertingSystem.send_alert(alert)
            
            session.close()
            return report
        
        except Exception as e:
            self.logger.error(f"Daily validation failed: {e}", exc_info=True)
            return None
    
    def start(self):
        """Start the scheduler"""
        if not HAS_APSCHEDULER:
            self.logger.error("APScheduler required to run scheduler. Install with: pip install apscheduler")
            return False
        
        try:
            self.schedule_weekly_refresh()
            self.schedule_daily_backups()
            self.schedule_health_checks()
            self.schedule_daily_validation()
            
            self.scheduler.start()
            self.is_running = True
            
            self.logger.info(
                "Scheduler started successfully",
                extra={
                    "jobs": len(self.scheduler.get_jobs()),
                    "scheduled_jobs": [job.id for job in self.scheduler.get_jobs()]
                }
            )
            
            audit_logger.log_error_event(
                error_type="SCHEDULER_START",
                message="Scheduler started",
                context={"jobs": [job.id for job in self.scheduler.get_jobs()]},
                severity="INFO"
            )
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {e}", exc_info=True)
            return False
    
    def stop(self):
        """Stop the scheduler"""
        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown()
                self.is_running = False
                self.logger.info("Scheduler stopped")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping scheduler: {e}", exc_info=True)
            return False
    
    def get_status(self) -> Dict:
        """Get scheduler status"""
        return {
            "is_running": self.is_running,
            "last_refresh": self.last_refresh_time.isoformat() if self.last_refresh_time else None,
            "stats": self.refresh_stats,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in (self.scheduler.get_jobs() if self.scheduler else [])
            ]
        }


# Global scheduler instance
pipeline_scheduler = DataPipelineScheduler()


if __name__ == "__main__":
    print("Starting Living Dataset Pipeline Scheduler")
    print("Press Ctrl+C to stop")
    
    success = pipeline_scheduler.start()
    
    if success:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
            pipeline_scheduler.stop()
            print("Scheduler stopped")
            sys.exit(0)
    else:
        print("Failed to start scheduler")
        sys.exit(1)