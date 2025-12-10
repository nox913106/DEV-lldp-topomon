"""
Device Groups API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.database import get_db
from app.models.group import DeviceGroup, DeviceGroupMember
from app.models.device import Device

router = APIRouter()


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    display_order: Optional[int] = None


class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    parent_id: Optional[int]
    color: Optional[str]
    icon: Optional[str]
    display_order: Optional[int]
    created_at: datetime
    device_count: int = 0
    
    class Config:
        from_attributes = True


class DeviceAssignment(BaseModel):
    device_ids: List[int]


@router.get("", response_model=List[GroupResponse])
async def list_groups(db: AsyncSession = Depends(get_db)):
    """List all device groups"""
    result = await db.execute(select(DeviceGroup))
    groups = result.scalars().all()
    
    # Get device counts
    response = []
    for group in groups:
        count_result = await db.execute(
            select(DeviceGroupMember).where(DeviceGroupMember.group_id == group.id)
        )
        count = len(count_result.scalars().all())
        
        response.append(GroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            parent_id=group.parent_id,
            color=group.color,
            icon=group.icon,
            display_order=group.display_order,
            created_at=group.created_at,
            device_count=count
        ))
    
    return response


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group: GroupCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new device group"""
    db_group = DeviceGroup(
        name=group.name,
        description=group.description,
        parent_id=group.parent_id,
        color=group.color,
        icon=group.icon
    )
    db.add(db_group)
    await db.commit()
    await db.refresh(db_group)
    
    return GroupResponse(
        id=db_group.id,
        name=db_group.name,
        description=db_group.description,
        parent_id=db_group.parent_id,
        color=db_group.color,
        icon=db_group.icon,
        display_order=db_group.display_order,
        created_at=db_group.created_at,
        device_count=0
    )


@router.get("/{group_id}/devices")
async def get_group_devices(
    group_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get devices in a group"""
    # Get group members
    result = await db.execute(
        select(DeviceGroupMember).where(DeviceGroupMember.group_id == group_id)
    )
    members = result.scalars().all()
    device_ids = [m.device_id for m in members]
    
    if not device_ids:
        return {"devices": [], "total": 0}
    
    # Get devices
    devices_result = await db.execute(
        select(Device).where(Device.id.in_(device_ids))
    )
    devices = devices_result.scalars().all()
    
    return {
        "devices": [{"id": d.id, "hostname": d.hostname, "ip_address": d.ip_address} for d in devices],
        "total": len(devices)
    }


@router.post("/{group_id}/devices")
async def assign_devices_to_group(
    group_id: int,
    assignment: DeviceAssignment,
    db: AsyncSession = Depends(get_db)
):
    """Assign devices to a group"""
    # Verify group exists
    result = await db.execute(
        select(DeviceGroup).where(DeviceGroup.id == group_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Add device memberships
    added = 0
    for device_id in assignment.device_ids:
        # Check if already a member
        existing = await db.execute(
            select(DeviceGroupMember).where(
                DeviceGroupMember.device_id == device_id,
                DeviceGroupMember.group_id == group_id
            )
        )
        if not existing.scalar_one_or_none():
            member = DeviceGroupMember(device_id=device_id, group_id=group_id)
            db.add(member)
            added += 1
    
    await db.commit()
    return {"status": "success", "added": added}


@router.delete("/{group_id}/devices")
async def remove_devices_from_group(
    group_id: int,
    assignment: DeviceAssignment,
    db: AsyncSession = Depends(get_db)
):
    """Remove devices from a group"""
    removed = 0
    for device_id in assignment.device_ids:
        result = await db.execute(
            select(DeviceGroupMember).where(
                DeviceGroupMember.device_id == device_id,
                DeviceGroupMember.group_id == group_id
            )
        )
        member = result.scalar_one_or_none()
        if member:
            await db.delete(member)
            removed += 1
    
    await db.commit()
    return {"status": "success", "removed": removed}


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a device group"""
    result = await db.execute(
        select(DeviceGroup).where(DeviceGroup.id == group_id)
    )
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    await db.delete(group)
    await db.commit()
