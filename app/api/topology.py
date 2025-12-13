"""
Topology API endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime

from app.db.database import get_db
from app.models.device import Device
from app.models.link import MergedLink, ExcludeRule
from app.models.alert import Alert
from app.schemas.topology import (
    TopologyResponse, TopologyNode, TopologyLink, PortDetail,
    ExcludeRuleCreate, ExcludeRuleResponse
)

router = APIRouter()


def get_link_status(utilization: float) -> str:
    """Determine link status based on utilization"""
    if utilization >= 90:
        return "critical"
    elif utilization >= 70:
        return "warning"
    elif utilization >= 50:
        return "elevated"
    return "normal"


@router.get("", response_model=TopologyResponse)
async def get_topology(
    view: str = Query("overview", description="View type: overview, group, full"),
    group_id: Optional[int] = Query(None, description="Group ID for group view"),
    expand: Optional[int] = Query(None, description="Device ID to expand neighbors"),
    db: AsyncSession = Depends(get_db)
):
    """Get topology data for visualization"""
    
    # Get all devices based on view type
    if view == "overview":
        # Show Core, Distribution, and Firewall in overview
        query = select(Device).where(
            Device.device_type.in_(["core", "router", "distribution", "dist", "firewall"])
        )
        result = await db.execute(query)
        devices = result.scalars().all()
        # If no core/dist devices, show all devices
        if not devices:
            result = await db.execute(select(Device))
            devices = result.scalars().all()
        group_device_ids = None  # Not a group view
    elif view == "group" and group_id:
        # Get devices in specific group + their parent devices (hierarchy-based)
        from app.models.group import DeviceGroupMember
        member_query = select(DeviceGroupMember.device_id).where(
            DeviceGroupMember.group_id == group_id
        )
        member_result = await db.execute(member_query)
        group_device_ids = [row[0] for row in member_result.fetchall()]
        
        if group_device_ids:
            # Get group member devices
            result = await db.execute(
                select(Device).where(Device.id.in_(group_device_ids))
            )
            group_devices = result.scalars().all()
            
            # Find parent devices using parent_device_id (hierarchy navigation)
            parent_ids = set()
            for device in group_devices:
                if device.parent_device_id:
                    parent_ids.add(device.parent_device_id)
            
            # Get parent devices (1 level up)
            all_device_ids = set(group_device_ids) | parent_ids
            
            query = select(Device).where(Device.id.in_(all_device_ids))
            result = await db.execute(query)
            devices = result.scalars().all()
        else:
            devices = []
            group_device_ids = []
    else:
        # Full map - all devices
        query = select(Device)
        result = await db.execute(query)
        devices = result.scalars().all()
        group_device_ids = None  # Not a group view
    
    device_ids = [d.id for d in devices]
    
    # Get alert counts per device
    alert_counts = {}
    if device_ids:
        alert_query = select(Alert.device_id).where(
            Alert.device_id.in_(device_ids),
            Alert.is_active == True
        )
        alert_result = await db.execute(alert_query)
        for row in alert_result:
            device_id = row[0]
            alert_counts[device_id] = alert_counts.get(device_id, 0) + 1
    
    # Build nodes
    nodes = []
    for device in devices:
        nodes.append(TopologyNode(
            id=str(device.id),
            hostname=device.hostname,
            ip_address=device.ip_address,
            device_type=device.device_type,
            vendor=device.vendor,
            status=device.status or "unknown",
            cpu_percent=device.cpu_percent,
            memory_percent=device.memory_percent,
            alert_count=alert_counts.get(device.id, 0)
        ))
    
    # Get merged links between these devices
    links = []
    if len(device_ids) >= 2:
        # For group view, only show links where at least one end is a group member
        if group_device_ids is not None and len(group_device_ids) > 0:
            # Links where at least one device is in the group
            from sqlalchemy import or_
            link_query = select(MergedLink).where(
                MergedLink.device_a_id.in_(device_ids),
                MergedLink.device_b_id.in_(device_ids),
                MergedLink.is_excluded == False,
                or_(
                    MergedLink.device_a_id.in_(group_device_ids),
                    MergedLink.device_b_id.in_(group_device_ids)
                )
            )
        else:
            # Full view - show all links between devices
            link_query = select(MergedLink).where(
                MergedLink.device_a_id.in_(device_ids),
                MergedLink.device_b_id.in_(device_ids),
                MergedLink.is_excluded == False
            )
        link_result = await db.execute(link_query)
        merged_links = link_result.scalars().all()
        
        for link in merged_links:
            # Parse port details from port_pairs
            port_details = []
            if link.port_pairs:
                for pd in link.port_pairs:
                    port_details.append(PortDetail(
                        local_port=pd.get("a", pd.get("local_port", "")),
                        remote_port=pd.get("b", pd.get("remote_port", "")),
                        bandwidth_mbps=pd.get("bandwidth_mbps", 0),
                        in_bps=pd.get("in_bps"),
                        out_bps=pd.get("out_bps")
                    ))
            
            max_util = max(
                link.utilization_in_percent or 0,
                link.utilization_out_percent or 0
            )
            
            links.append(TopologyLink(
                id=str(link.id),
                source=str(link.device_a_id),
                target=str(link.device_b_id),
                total_bandwidth_mbps=link.total_bandwidth_mbps or 0,
                utilization_in_percent=link.utilization_in_percent or 0,
                utilization_out_percent=link.utilization_out_percent or 0,
                status=get_link_status(max_util),
                port_details=port_details
            ))
    
    return TopologyResponse(
        nodes=nodes,
        links=links,
        last_updated=datetime.utcnow()
    )


@router.get("/exclude-rules", response_model=list[ExcludeRuleResponse])
async def list_exclude_rules(db: AsyncSession = Depends(get_db)):
    """List all exclude rules"""
    result = await db.execute(select(ExcludeRule))
    return result.scalars().all()


@router.post("/exclude-rules", response_model=ExcludeRuleResponse)
async def create_exclude_rule(
    rule: ExcludeRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new exclude rule"""
    db_rule = ExcludeRule(
        rule_type=rule.rule_type,
        pattern=rule.pattern,
        device_a_id=rule.device_a_id,
        device_b_id=rule.device_b_id
    )
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    return db_rule


@router.delete("/exclude-rules/{rule_id}")
async def delete_exclude_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an exclude rule"""
    result = await db.execute(
        select(ExcludeRule).where(ExcludeRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if rule:
        await db.delete(rule)
        await db.commit()
    return {"status": "deleted"}
