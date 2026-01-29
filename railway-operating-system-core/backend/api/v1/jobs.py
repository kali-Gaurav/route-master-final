# api/v1/jobs.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from ...db_connection import get_db
from ...models import Job
from ...schemas.job import JobCreate, JobUpdate, Job as JobSchema, JobStatus
from ...services.job_service import JobService
from ...core.auth import get_current_active_user
from ...models import User

router = APIRouter()

@router.get("/", response_model=List[JobSchema])
async def get_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),  # Reduced from 100, max now 500
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user jobs"""
    job_service = JobService(db)
    if current_user.role in ["admin", "developer"]:
        # Admins can see all jobs for their tenant
        return job_service.get_jobs_by_tenant(current_user.tenant_id, skip=skip, limit=limit) if current_user.tenant_id else []
    else:
        # Regular users see their tenant's jobs
        return job_service.get_jobs_by_tenant(current_user.tenant_id, skip=skip, limit=limit) if current_user.tenant_id else []

@router.get("/{job_id}", response_model=JobSchema)
async def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get job status and result"""
    job_service = JobService(db)
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check if user has access to this job
    if current_user.role not in ["admin", "developer"] and job.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return job

@router.post("/", response_model=JobSchema)
async def create_job(
    job: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Submit new job"""
    job_service = JobService(db)

    # Set tenant_id from current user if not provided
    if not job.tenant_id:
        job.tenant_id = current_user.tenant_id

    # Check permissions
    if current_user.role not in ["admin", "developer", "operator"] and job.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Cannot create jobs for other tenants")

    return job_service.create_job(job)

@router.put("/{job_id}", response_model=JobSchema)
async def update_job(
    job_id: UUID,
    job_update: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update job (admin only)"""
    job_service = JobService(db)
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Only admins can update jobs
    if current_user.role not in ["admin", "developer"]:
        raise HTTPException(status_code=403, detail="Only admins can update jobs")

    updated_job = job_service.update_job(job_id, job_update)
    if not updated_job:
        raise HTTPException(status_code=404, detail="Job not found")
    return updated_job

@router.delete("/{job_id}")
async def delete_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Cancel job"""
    job_service = JobService(db)
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check permissions
    if current_user.role not in ["admin", "developer"] and job.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Only allow deletion of pending jobs
    if job.status != "pending":
        raise HTTPException(status_code=400, detail="Can only cancel pending jobs")

    if not job_service.delete_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")

    return {"message": "Job cancelled successfully"}

@router.get("/{job_id}/status", response_model=JobStatus)
async def get_job_status(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get job status"""
    job_service = JobService(db)
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check permissions
    if current_user.role not in ["admin", "developer"] and job.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return JobStatus(
        id=job.id,
        status=job.status,
        progress=None,  # Could be calculated based on job type
        message=job.error_message
    )