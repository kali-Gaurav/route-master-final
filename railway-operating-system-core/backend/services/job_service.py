# services/job_service.py
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from ..models import Job
from ..schemas.job import JobCreate, JobUpdate
import logging

logger = logging.getLogger(__name__)

class JobService:
    def __init__(self, db: Session):
        self.db = db

    def get_job(self, job_id: UUID) -> Optional[Job]:
        """Get job by ID"""
        return self.db.query(Job).filter(Job.id == job_id).first()

    def get_jobs_by_tenant(self, tenant_id: UUID, skip: int = 0, limit: int = 100) -> List[Job]:
        """Get jobs for a specific tenant"""
        return self.db.query(Job).filter(Job.tenant_id == tenant_id).offset(skip).limit(limit).all()

    def get_jobs_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Job]:
        """Get jobs created by a specific user (if we add user_id to Job model)"""
        # For now, return all jobs - this would need user tracking
        return self.db.query(Job).offset(skip).limit(limit).all()

    def create_job(self, job: JobCreate) -> Job:
        """Create new job with logging"""
        try:
            db_job = Job(**job.model_dump())
            self.db.add(db_job)
            self.db.commit()
            self.db.refresh(db_job)
            logger.info(f"Job created: {db_job.id} (type: {db_job.type}, tenant: {db_job.tenant_id})")
            return db_job
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            self.db.rollback()
            raise

    def update_job(self, job_id: UUID, job_update: JobUpdate) -> Optional[Job]:
        """Update existing job with timestamp management"""
        try:
            db_job = self.get_job(job_id)
            if not db_job:
                return None

            update_data = job_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_job, field, value)

            # Update timestamps based on status changes
            if 'status' in update_data:
                if update_data['status'] == 'running' and not db_job.started_at:
                    db_job.started_at = datetime.utcnow()
                    logger.info(f"Job started: {job_id}")
                elif update_data['status'] in ['completed', 'failed'] and not db_job.completed_at:
                    db_job.completed_at = datetime.utcnow()
                    logger.info(f"Job {update_data['status']}: {job_id}")

            self.db.commit()
            self.db.refresh(db_job)
            return db_job
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {e}")
            self.db.rollback()
            raise

    def delete_job(self, job_id: UUID) -> bool:
        """Delete job"""
        db_job = self.get_job(job_id)
        if not db_job:
            return False

        self.db.delete(db_job)
        self.db.commit()
        return True

    def get_pending_jobs(self, limit: int = 50) -> List[Job]:
        """Get pending jobs for processing"""
        return self.db.query(Job).filter(Job.status == 'pending').order_by(Job.priority.desc(), Job.created_at).limit(limit).all()

    def mark_job_started(self, job_id: UUID) -> Optional[Job]:
        """Mark job as started"""
        return self.update_job(job_id, JobUpdate(status='running'))

    def mark_job_completed(self, job_id: UUID, result: dict = None) -> Optional[Job]:
        """Mark job as completed"""
        return self.update_job(job_id, JobUpdate(status='completed', result=result))

    def mark_job_failed(self, job_id: UUID, error_message: str) -> Optional[Job]:
        """Mark job as failed"""
        return self.update_job(job_id, JobUpdate(status='failed', error_message=error_message))