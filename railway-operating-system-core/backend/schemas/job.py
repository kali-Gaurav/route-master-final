# schemas/job.py
from pydantic import BaseModel
from typing import Optional, Any
from uuid import UUID
from datetime import datetime

class JobBase(BaseModel):
    type: str
    priority: int = 1
    payload: Optional[dict] = None

class JobCreate(JobBase):
    tenant_id: Optional[UUID] = None

class JobUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[int] = None
    result: Optional[dict] = None
    error_message: Optional[str] = None

class Job(JobBase):
    id: UUID
    tenant_id: Optional[UUID]
    status: str
    result: Optional[dict]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class JobStatus(BaseModel):
    id: UUID
    status: str
    progress: Optional[float] = None
    message: Optional[str] = None