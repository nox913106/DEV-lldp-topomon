"""
Alert and AlertProfile models
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class AlertProfile(Base):
    """Alert threshold profile"""
    __tablename__ = "alert_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    
    # Thresholds as JSONB
    # {link_utilization: {warning, critical, recovery_buffer}, cpu: {...}, ...}
    thresholds = Column(JSON, nullable=False)  # Changed to JSON for SQLite compat
    
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    devices = relationship("Device", back_populates="alert_profile")
    
    def __repr__(self):
        return f"<AlertProfile(id={self.id}, name='{self.name}')>"


class Alert(Base):
    """Active and historical alerts"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))
    link_id = Column(Integer, ForeignKey("merged_links.id", ondelete="CASCADE"))
    
    alert_type = Column(String(50), nullable=False)  # device_offline, link_high_utilization, cpu_high, etc.
    severity = Column(String(20), nullable=False)  # warning, critical, info
    message = Column(Text)
    
    current_value = Column(Float)
    threshold_value = Column(Float)
    
    is_active = Column(Boolean, default=True, index=True)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    recovered_at = Column(DateTime(timezone=True))
    acknowledged_at = Column(DateTime(timezone=True))
    acknowledged_by = Column(String(100))
    
    # Relationships
    device = relationship("Device", back_populates="alerts")
    link = relationship("MergedLink", back_populates="alerts")
    history = relationship("AlertHistory", back_populates="alert", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, type='{self.alert_type}', active={self.is_active})>"


class AlertHistory(Base):
    """Alert state change history"""
    __tablename__ = "alert_history"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50))  # triggered, escalated, recovered, acknowledged
    event_time = Column(DateTime(timezone=True), server_default=func.now())
    details = Column(JSON)  # Changed to JSON for SQLite compat
    
    # Relationships
    alert = relationship("Alert", back_populates="history")
