"""
Discovery API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from app.db.database import get_db

router = APIRouter()

# In-memory job status (in production, use Redis)
discovery_jobs = {}


class DiscoveryStartRequest(BaseModel):
    seed_device_id: int


class DiscoveryStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: dict
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


async def run_discovery(job_id: str, seed_device_id: int):
    """Background task for running discovery"""
    # TODO: Implement actual discovery logic using SNMP
    discovery_jobs[job_id]["status"] = "running"
    
    # Placeholder - will be implemented in SNMP collector
    import asyncio
    await asyncio.sleep(2)
    
    discovery_jobs[job_id]["status"] = "completed"
    discovery_jobs[job_id]["completed_at"] = datetime.utcnow()
    discovery_jobs[job_id]["progress"] = {
        "discovered": 0,
        "pending": 0,
        "failed": 0
    }


@router.post("/start", response_model=DiscoveryStatusResponse)
async def start_discovery(
    request: DiscoveryStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Start device discovery from a seed device"""
    job_id = str(uuid.uuid4())[:8]
    
    discovery_jobs[job_id] = {
        "job_id": job_id,
        "status": "started",
        "progress": {"discovered": 0, "pending": 1, "failed": 0},
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "error": None
    }
    
    background_tasks.add_task(run_discovery, job_id, request.seed_device_id)
    
    return DiscoveryStatusResponse(**discovery_jobs[job_id])


@router.get("/status", response_model=Optional[DiscoveryStatusResponse])
async def get_discovery_status(job_id: Optional[str] = None):
    """Get discovery job status"""
    if job_id and job_id in discovery_jobs:
        return DiscoveryStatusResponse(**discovery_jobs[job_id])
    
    # Return latest job if no job_id specified
    if discovery_jobs:
        latest = max(discovery_jobs.values(), key=lambda x: x["started_at"])
        return DiscoveryStatusResponse(**latest)
    
    return None
