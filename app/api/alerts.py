"""
Alerts API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.database import get_db
from app.models.alert import Alert, AlertHistory

router = APIRouter()


class AlertResponse(BaseModel):
    id: int
    device_id: Optional[int]
    link_id: Optional[int]
    alert_type: str
    severity: str
    message: Optional[str]
    current_value: Optional[float]
    threshold_value: Optional[float]
    is_active: bool
    triggered_at: datetime
    recovered_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    
    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int


class AcknowledgeRequest(BaseModel):
    acknowledged_by: str


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all alerts with optional filtering"""
    query = select(Alert)
    
    if is_active is not None:
        query = query.where(Alert.is_active == is_active)
    if severity:
        query = query.where(Alert.severity == severity)
    
    query = query.order_by(Alert.triggered_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    # Get total count
    from sqlalchemy import func
    count_query = select(func.count(Alert.id))
    if is_active is not None:
        count_query = count_query.where(Alert.is_active == is_active)
    if severity:
        count_query = count_query.where(Alert.severity == severity)
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    return AlertListResponse(alerts=alerts, total=total)


@router.get("/active", response_model=AlertListResponse)
async def list_active_alerts(
    db: AsyncSession = Depends(get_db)
):
    """List all active alerts"""
    query = select(Alert).where(Alert.is_active == True).order_by(Alert.triggered_at.desc())
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return AlertListResponse(alerts=alerts, total=len(alerts))


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific alert"""
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with id {alert_id} not found"
        )
    
    return alert


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    request: AcknowledgeRequest,
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge an alert"""
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with id {alert_id} not found"
        )
    
    alert.acknowledged_at = datetime.utcnow()
    alert.acknowledged_by = request.acknowledged_by
    
    # Add to history
    history = AlertHistory(
        alert_id=alert_id,
        event_type="acknowledged",
        details={"acknowledged_by": request.acknowledged_by}
    )
    db.add(history)
    
    await db.commit()
    
    return {"status": "acknowledged", "alert_id": alert_id}
