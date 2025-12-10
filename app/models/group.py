"""
Device group models
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class DeviceGroup(Base):
    """Device group for organizing devices"""
    __tablename__ = "device_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey("device_groups.id"), index=True)
    color = Column(String(20))
    icon = Column(String(50))
    display_order = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Self-referential relationship for nested groups
    children = relationship("DeviceGroup", backref="parent", remote_side=[id])
    members = relationship("DeviceGroupMember", back_populates="group", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DeviceGroup(id={self.id}, name='{self.name}')>"


class DeviceGroupMember(Base):
    """Many-to-many relationship between devices and groups"""
    __tablename__ = "device_group_members"
    
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True)
    group_id = Column(Integer, ForeignKey("device_groups.id", ondelete="CASCADE"), primary_key=True, index=True)
    
    # Relationships
    device = relationship("Device", back_populates="group_memberships")
    group = relationship("DeviceGroup", back_populates="members")
