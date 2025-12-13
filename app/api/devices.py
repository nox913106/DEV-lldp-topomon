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
    search: str = None,
    vendor: str = None,
    sort_by: str = "hostname",
    sort_order: str = "asc",
    db: AsyncSession = Depends(get_db)
):
    """List all devices with optional filtering"""
    from sqlalchemy import or_, asc, desc
    
    query = select(Device)
    
    # Apply filters
    if status:
        query = query.where(Device.status == status)
    if vendor:
        query = query.where(Device.vendor == vendor)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Device.hostname.ilike(search_pattern),
                Device.ip_address.ilike(search_pattern)
            )
        )
    
    # Apply sorting
    sort_column = getattr(Device, sort_by, Device.hostname)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Get total count before pagination
    count_query = select(func.count(Device.id))
    if status:
        count_query = count_query.where(Device.status == status)
    if vendor:
        count_query = count_query.where(Device.vendor == vendor)
    if search:
        count_query = count_query.where(
            or_(
                Device.hostname.ilike(f"%{search}%"),
                Device.ip_address.ilike(f"%{search}%")
            )
        )
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    # Apply pagination (skip limit=0 means ALL)
    if limit > 0:
        query = query.offset(skip).limit(limit)
    else:
        query = query.offset(skip)
    
    result = await db.execute(query)
    devices = result.scalars().all()
    
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


@router.get("/{device_id}/hierarchy")
async def get_device_hierarchy(
    device_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get device hierarchy (upstream ancestors + downstream children)
    Returns:
    - device: The target device info
    - ancestors: List of upstream devices (parent -> grandparent -> ...)
    - children: List of direct child devices
    """
    # Get the target device
    result = await db.execute(
        select(Device).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )
    
    # Get ancestor chain (walk up the parent_device_id)
    ancestors = []
    current = device
    while current.parent_device_id:
        parent_result = await db.execute(
            select(Device).where(Device.id == current.parent_device_id)
        )
        parent = parent_result.scalar_one_or_none()
        if parent:
            ancestors.append({
                "id": parent.id,
                "hostname": parent.hostname,
                "ip_address": parent.ip_address,
                "device_type": parent.device_type,
                "status": parent.status,
                "vendor": parent.vendor
            })
            current = parent
        else:
            break
    
    # Get ALL descendants recursively (children + grandchildren + ...)
    async def get_all_descendants(parent_id: int) -> list:
        """Recursively get all descendants of a device"""
        descendants = []
        result = await db.execute(
            select(Device).where(Device.parent_device_id == parent_id)
        )
        direct_children = result.scalars().all()
        
        for child in direct_children:
            descendants.append({
                "id": child.id,
                "hostname": child.hostname,
                "ip_address": child.ip_address,
                "device_type": child.device_type,
                "status": child.status,
                "vendor": child.vendor
            })
            # Recursively get grandchildren
            grandchildren = await get_all_descendants(child.id)
            descendants.extend(grandchildren)
        
        return descendants
    
    children_list = await get_all_descendants(device_id)
    
    return {
        "device": {
            "id": device.id,
            "hostname": device.hostname,
            "ip_address": device.ip_address,
            "device_type": device.device_type,
            "status": device.status,
            "vendor": device.vendor,
            "model": device.model,
            "firmware_version": device.firmware_version,
            "cpu_percent": device.cpu_percent,
            "memory_percent": device.memory_percent
        },
        "ancestors": ancestors,  # [parent, grandparent, ...]
        "children": children_list
    }


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
