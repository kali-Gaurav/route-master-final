# workers/tasks.py
from celery import Celery
from config import settings
import sys
import os

# Add the parent directory to the path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from database.connection import SessionLocal
from services.job_service import JobService

# Create Celery app
celery_app = Celery(
    "railway_worker",
    broker=settings.redis_url,
    backend=settings.redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(bind=True)
def process_job(self, job_id: str):
    """Process a background job"""
    db = SessionLocal()
    try:
        job_service = JobService(db)

        # Mark job as started
        job_service.mark_job_started(job_id)

        # Get job details
        job = job_service.get_job(job_id)
        if not job:
            raise Exception(f"Job {job_id} not found")

        # Process based on job type
        if job.type == "route_calculation":
            result = process_route_calculation(job.payload)
        elif job.type == "data_import":
            result = process_data_import(job.payload)
        elif job.type == "report_generation":
            result = process_report_generation(job.payload)
        else:
            raise Exception(f"Unknown job type: {job.type}")

        # Mark job as completed
        job_service.mark_job_completed(job_id, result)

        return result

    except Exception as exc:
        # Mark job as failed
        job_service.mark_job_failed(job_id, str(exc))
        raise self.retry(countdown=60, exc=exc)
    finally:
        db.close()

def process_route_calculation(payload: dict) -> dict:
    """Process route calculation job"""
    # Implement route calculation logic here
    # This would integrate with the route finding algorithms
    origin = payload.get("origin")
    destination = payload.get("destination")

    # Placeholder implementation
    return {
        "origin": origin,
        "destination": destination,
        "routes": [],
        "message": "Route calculation completed"
    }

def process_data_import(payload: dict) -> dict:
    """Process data import job"""
    # Implement data import logic here
    # This would handle CSV imports, ETL processes, etc.
    data_type = payload.get("data_type")
    source = payload.get("source")

    # Placeholder implementation
    return {
        "data_type": data_type,
        "source": source,
        "records_processed": 0,
        "message": "Data import completed"
    }

def process_report_generation(payload: dict) -> dict:
    """Process report generation job"""
    # Implement report generation logic here
    report_type = payload.get("report_type")
    parameters = payload.get("parameters", {})

    # Placeholder implementation
    return {
        "report_type": report_type,
        "parameters": parameters,
        "report_url": None,
        "message": "Report generation completed"
    }