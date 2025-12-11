"""
Link models - Raw and merged link information
"""
from sqlalchemy import Column, Integer, String, Float, BigInteger, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class RawLink(Base):
    """Raw LLDP/CDP link information (before merging)"""
    __tablename__ = "raw_links"
    
    id = Column(Integer, primary_key=True, index=True)
    local_device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    local_port = Column(String(100))
    local_port_index = Column(Integer)
    remote_hostname = Column(String(255))
    remote_port = Column(String(100))
    remote_chassis_id = Column(String(255))
    protocol = Column(String(10))  # lldp, cdp
    
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    local_device = relationship("Device", back_populates="raw_links")
    
    def __repr__(self):
        return f"<RawLink(local={self.local_port}, remote_host='{self.remote_hostname}')>"


class MergedLink(Base):
    """Merged link between two devices (aggregated from multiple raw links)"""
    __tablename__ = "merged_links"
    
    id = Column(Integer, primary_key=True, index=True)
    device_a_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    device_b_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    
    # Bandwidth and utilization
    total_bandwidth_mbps = Column(Integer)
    current_in_bps = Column(BigInteger)
    current_out_bps = Column(BigInteger)
    utilization_in_percent = Column(Float)
    utilization_out_percent = Column(Float)
    
    # Port details as JSON array
    # [{local_port, remote_port, bandwidth_mbps, in_bps, out_bps}, ...]
    port_pairs = Column(JSON)  # Changed from port_details, use JSON for SQLite compat
    
    is_excluded = Column(Boolean, default=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    device_a = relationship("Device", foreign_keys=[device_a_id])
    device_b = relationship("Device", foreign_keys=[device_b_id])
    alerts = relationship("Alert", back_populates="link", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MergedLink(a={self.device_a_id}, b={self.device_b_id}, bw={self.total_bandwidth_mbps}Mbps)>"


class ExcludeRule(Base):
    """Rules for excluding links from topology"""
    __tablename__ = "exclude_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_type = Column(String(50))  # hostname_pattern, port_pattern, device_pair
    pattern = Column(String(255))
    device_a_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))
    device_b_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
