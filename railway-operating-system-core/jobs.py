"""Job management module for ROS worker."""

from infrastructure import JobManager
import json
from typing import Dict, Any, List, Optional

def enqueue_job(command: str, payload: Dict[str, Any]) -> Optional[str]:
    """Enqueue a job and return job_id."""
    return JobManager.enqueue(command, payload)

def list_jobs(limit: int = 100) -> List[Dict[str, Any]]:
    """List all jobs."""
    return JobManager.list_all(limit=limit)

def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job details by job_id."""
    return JobManager.get(job_id)

def get_job_logs(job_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get job logs (placeholder - JobManager doesn't have logs yet)."""
    # TODO: Implement job logging in JobManager
    return []
