"""
Devices API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.db.database import get_db
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse, DeviceListResponse

router = APIRouter()


@router.get("", response_model=DeviceListResponse)
async def list_devices(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    """List all devices with optional filtering"""
    query = select(Device)
    
    if status:
        query = query.where(Device.status == status)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    devices = result.scalars().all()
    
    # Get total count
    count_query = select(func.count(Device.id))
    if status:
        count_query = count_query.where(Device.status == status)
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    return DeviceListResponse(devices=devices, total=total)


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device: DeviceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new device (seed device for discovery)"""
    # Check if hostname already exists
    existing = await db.execute(
        select(Device).where(Device.hostname == device.hostname)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device with hostname '{device.hostname}' already exists"
        )
    
    db_device = Device(
        hostname=device.hostname,
        ip_address=device.ip_address,
        vendor=device.vendor,
        device_type=device.device_type,
        snmp_community=device.snmp_community,
        alert_profile_id=device.alert_profile_id,
        status="unknown"
    )
    
    db.add(db_device)
    await db.commit()
    await db.refresh(db_device)
    
    # TODO: If auto_discover is True, trigger discovery job
    
    return db_device


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific device by ID"""
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )
    
    return device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_update: DeviceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a device"""
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )
    
    # Update fields that are provided
    update_data = device_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)
    
    await db.commit()
    await db.refresh(device)
    
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a device"""
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )
    
    await db.delete(device)
    await db.commit()
