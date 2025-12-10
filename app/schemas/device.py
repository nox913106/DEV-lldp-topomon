"""
Device schemas for API request/response
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DeviceBase(BaseModel):
    """Base device schema"""
    hostname: str = Field(..., min_length=1, max_length=255)
    ip_address: str = Field(..., min_length=7, max_length=45)
    vendor: Optional[str] = None
    device_type: Optional[str] = None
    snmp_community: str = Field(..., min_length=1, max_length=255)


class DeviceCreate(DeviceBase):
    """Schema for creating a new device"""
    alert_profile_id: Optional[int] = None
    auto_discover: bool = False


class DeviceUpdate(BaseModel):
    """Schema for updating a device"""
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    vendor: Optional[str] = None
    device_type: Optional[str] = None
    snmp_community: Optional[str] = None
    alert_profile_id: Optional[int] = None
    status: Optional[str] = None


class DeviceResponse(DeviceBase):
    """Schema for device response"""
    id: int
    alert_profile_id: Optional[int] = None
    status: str
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    uptime_seconds: Optional[int] = None
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """Schema for device list response"""
    devices: List[DeviceResponse]
    total: int
