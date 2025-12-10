"""
Topology schemas for API response
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PortDetail(BaseModel):
    """Port detail in a merged link"""
    local_port: str
    remote_port: str
    bandwidth_mbps: int
    in_bps: Optional[int] = None
    out_bps: Optional[int] = None


class TopologyNode(BaseModel):
    """Node in topology graph"""
    id: str
    hostname: str
    ip_address: str
    device_type: Optional[str] = None
    vendor: Optional[str] = None
    status: str
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    alert_count: int = 0
    # For aggregated nodes
    is_aggregated: bool = False
    child_count: int = 0


class TopologyLink(BaseModel):
    """Link in topology graph"""
    id: str
    source: str  # device_a id
    target: str  # device_b id
    total_bandwidth_mbps: int
    utilization_in_percent: float
    utilization_out_percent: float
    status: str  # normal, warning, critical
    port_details: List[PortDetail]


class TopologyResponse(BaseModel):
    """Full topology response"""
    nodes: List[TopologyNode]
    links: List[TopologyLink]
    last_updated: datetime


class ExcludeRuleCreate(BaseModel):
    """Schema for creating exclude rule"""
    rule_type: str  # hostname_pattern, port_pattern, device_pair
    pattern: Optional[str] = None
    device_a_id: Optional[int] = None
    device_b_id: Optional[int] = None


class ExcludeRuleResponse(BaseModel):
    """Schema for exclude rule response"""
    id: int
    rule_type: str
    pattern: Optional[str] = None
    device_a_id: Optional[int] = None
    device_b_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
