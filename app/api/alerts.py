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
    details: Optional[dict] = None  # Contains is_root_cause, is_suppressed, etc.
    
    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int


class AcknowledgeRequest(BaseModel):
    acknowledged_by: str
    reason: Optional[str] = None
    suppress_value: Optional[int] = None  # Duration value (e.g., 30)
    suppress_unit: Optional[str] = None  # 'minutes', 'hours', 'days', or 'until_resolved'


class UnsuppressRequest(BaseModel):
    unsuppressed_by: str


class EditHistoryRequest(BaseModel):
    reason: str


class DeleteHistoryRequest(BaseModel):
    deleted_by: str
    delete_reason: str
    restore_notifications: bool = False  # Whether to restore notifications after delete


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
    """Acknowledge an alert and optionally suppress notifications"""
    from datetime import timedelta
    
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with id {alert_id} not found"
        )
    
    now = datetime.utcnow()
    alert.acknowledged_at = now
    alert.acknowledged_by = request.acknowledged_by
    alert.acknowledge_reason = request.reason
    
    # Calculate suppress_until based on unit
    suppress_duration_str = None
    if request.suppress_unit == 'until_resolved':
        alert.is_suppressed = True
        alert.suppress_until = None  # null means until resolved
        suppress_duration_str = 'until_resolved'
    elif request.suppress_value and request.suppress_unit:
        alert.is_suppressed = True
        if request.suppress_unit == 'minutes':
            alert.suppress_until = now + timedelta(minutes=request.suppress_value)
            suppress_duration_str = f"{request.suppress_value} minutes"
        elif request.suppress_unit == 'hours':
            alert.suppress_until = now + timedelta(hours=request.suppress_value)
            suppress_duration_str = f"{request.suppress_value} hours"
        elif request.suppress_unit == 'days':
            alert.suppress_until = now + timedelta(days=request.suppress_value)
            suppress_duration_str = f"{request.suppress_value} days"
    
    # Add to history
    history = AlertHistory(
        alert_id=alert_id,
        event_type="acknowledged",
        details={
            "acknowledged_by": request.acknowledged_by,
            "reason": request.reason,
            "suppress_duration": suppress_duration_str,
            "suppress_until": alert.suppress_until.isoformat() if alert.suppress_until else None
        }
    )
    db.add(history)
    
    await db.commit()
    
    return {
        "status": "acknowledged",
        "alert_id": alert_id,
        "is_suppressed": alert.is_suppressed,
        "suppress_until": alert.suppress_until.isoformat() if alert.suppress_until else "until_resolved" if alert.is_suppressed else None
    }


@router.get("/{alert_id}/history")
async def get_alert_history(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get alert history (acknowledgment records)"""
    # Verify alert exists
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with id {alert_id} not found"
        )
    
    # Get history records
    result = await db.execute(
        select(AlertHistory).where(AlertHistory.alert_id == alert_id).order_by(AlertHistory.event_time.desc())
    )
    history = result.scalars().all()
    
    return {
        "alert_id": alert_id,
        "is_suppressed": alert.is_suppressed,
        "suppress_until": alert.suppress_until.isoformat() if alert.suppress_until else None,
        "history": [
            {
                "id": h.id,
                "event_type": h.event_type,
                "event_time": h.event_time.isoformat() if h.event_time else None,
                "acknowledged_by": h.details.get("acknowledged_by") if h.details else None,
                "reason": h.details.get("reason") if h.details else None,
                "suppress_duration": h.details.get("suppress_duration") if h.details else None,
                "is_deleted": h.is_deleted,
                "deleted_at": h.deleted_at.isoformat() if h.deleted_at else None,
                "deleted_by": h.deleted_by,
                "delete_reason": h.delete_reason
            }
            for h in history
        ]
    }


@router.post("/{alert_id}/unsuppress")
async def unsuppress_alert(
    alert_id: int,
    request: UnsuppressRequest,
    db: AsyncSession = Depends(get_db)
):
    """Cancel suppression and restore notifications"""
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with id {alert_id} not found"
        )
    
    alert.is_suppressed = False
    alert.suppress_until = None
    
    # Add to history
    history = AlertHistory(
        alert_id=alert_id,
        event_type="unsuppressed",
        details={"unsuppressed_by": request.unsuppressed_by}
    )
    db.add(history)
    
    await db.commit()
    
    return {"status": "unsuppressed", "alert_id": alert_id}


@router.put("/{alert_id}/history/{history_id}")
async def edit_history_reason(
    alert_id: int,
    history_id: int,
    request: EditHistoryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Edit a history record's reason"""
    result = await db.execute(
        select(AlertHistory).where(
            AlertHistory.id == history_id,
            AlertHistory.alert_id == alert_id
        )
    )
    history = result.scalar_one_or_none()
    
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"History record with id {history_id} not found"
        )
    
    if history.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit a deleted record"
        )
    
    # Update details
    if history.details:
        history.details = {**history.details, "reason": request.reason}
    else:
        history.details = {"reason": request.reason}
    
    await db.commit()
    
    return {"status": "updated", "history_id": history_id}


@router.delete("/{alert_id}/history/{history_id}")
async def delete_history_reason(
    alert_id: int,
    history_id: int,
    request: DeleteHistoryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a history record"""
    result = await db.execute(
        select(AlertHistory).where(
            AlertHistory.id == history_id,
            AlertHistory.alert_id == alert_id
        )
    )
    history = result.scalar_one_or_none()
    
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"History record with id {history_id} not found"
        )
    
    # Soft delete
    history.is_deleted = True
    history.deleted_at = datetime.utcnow()
    history.deleted_by = request.deleted_by
    history.delete_reason = request.delete_reason
    
    # Optionally restore notifications
    if request.restore_notifications:
        result = await db.execute(
            select(Alert).where(Alert.id == alert_id)
        )
        alert = result.scalar_one_or_none()
        if alert:
            alert.is_suppressed = False
            alert.suppress_until = None
    
    await db.commit()
    
    return {
        "status": "deleted",
        "history_id": history_id,
        "notifications_restored": request.restore_notifications
    }
