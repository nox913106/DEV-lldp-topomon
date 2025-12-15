"""
Device model - Network device information
"""
from sqlalchemy import Column, Integer, String, Float, BigInteger, DateTime, ForeignKey, Enum as SQLEnum, Boolean
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
    model = Column(String(100))  # Device model (e.g., "WS-C3850-48P")
    firmware_version = Column(String(100))  # Firmware/OS version
    device_type = Column(String(50))  # router, switch, firewall
    
    # SNMP Settings
    snmp_community = Column(String(255), nullable=True)
    snmp_version = Column(String(10), default="v2c")  # "v2c" or "v3"
    snmpv3_username = Column(String(255), nullable=True)
    snmpv3_auth_protocol = Column(String(20), nullable=True)  # MD5, SHA, SHA256
    snmpv3_auth_password = Column(String(255), nullable=True)
    snmpv3_priv_protocol = Column(String(20), nullable=True)  # DES, AES, AES256
    snmpv3_priv_password = Column(String(255), nullable=True)
    
    # Auto-discovery setting (default True)
    auto_discover = Column(Boolean, default=True)
    
    # Parent device for hierarchy (e.g., access switch -> distribution -> core)
    parent_device_id = Column(Integer, ForeignKey("devices.id"), nullable=True, index=True)
    
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
    parent = relationship("Device", remote_side=[id], backref="children", foreign_keys=[parent_device_id])
    alert_profile = relationship("AlertProfile", back_populates="devices")
    raw_links = relationship("RawLink", back_populates="local_device", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="device", cascade="all, delete-orphan")
    group_memberships = relationship("DeviceGroupMember", back_populates="device", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Device(id={self.id}, hostname='{self.hostname}', ip='{self.ip_address}')>"
