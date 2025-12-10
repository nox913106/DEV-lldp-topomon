"""
Device model - Network device information
"""
from sqlalchemy import Column, Integer, String, Float, BigInteger, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum


class DeviceStatus(str, enum.Enum):
    """Device status enumeration"""
    UNKNOWN = "unknown"
    MANAGED = "managed"
    UNMANAGED = "unmanaged"
    OFFLINE = "offline"
    EXCLUDED = "excluded"


class Device(Base):
    """Network device model"""
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(255), unique=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=False, index=True)
    vendor = Column(String(100))
    device_type = Column(String(50))  # router, switch, firewall
    snmp_community = Column(String(255), nullable=False)
    
    # Alert profile reference
    alert_profile_id = Column(Integer, ForeignKey("alert_profiles.id"))
    
    # Status and metrics
    status = Column(String(50), default=DeviceStatus.UNKNOWN)
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    uptime_seconds = Column(BigInteger)
    
    # Timestamps
    last_seen = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    alert_profile = relationship("AlertProfile", back_populates="devices")
    raw_links = relationship("RawLink", back_populates="local_device", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="device", cascade="all, delete-orphan")
    group_memberships = relationship("DeviceGroupMember", back_populates="device", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Device(id={self.id}, hostname='{self.hostname}', ip='{self.ip_address}')>"
