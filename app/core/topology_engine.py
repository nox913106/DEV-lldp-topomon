"""
Topology Engine - Builds and manages network topology graph
Handles link merging, utilization calculation, and topology queries
"""
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.device import Device
from app.models.link import RawLink, MergedLink
from app.models.group import DeviceGroupMember

logger = logging.getLogger(__name__)


@dataclass
class PortInfo:
    """Individual port information within a merged link"""
    local_port: str
    remote_port: str
    bandwidth_mbps: int
    in_bps: int = 0
    out_bps: int = 0
    utilization_percent: float = 0.0


@dataclass
class MergedLinkInfo:
    """Merged link between two devices"""
    device_a_id: int
    device_b_id: int
    device_a_hostname: str
    device_b_hostname: str
    total_bandwidth_mbps: int
    current_in_bps: int
    current_out_bps: int
    utilization_in_percent: float
    utilization_out_percent: float
    port_details: List[PortInfo] = field(default_factory=list)


class TopologyEngine:
    """
    Builds and manages network topology
    Merges multiple links between same device pairs
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_device_map(self) -> Dict[str, Device]:
        """Get mapping of hostname to device"""
        result = await self.db.execute(select(Device))
        devices = result.scalars().all()
        return {d.hostname: d for d in devices}
    
    async def merge_links(self) -> List[MergedLinkInfo]:
        """
        Merge raw links into aggregated links between device pairs
        
        Example:
            DeviceA:Gi0/1 <-> DeviceB:Gi0/1 (1Gbps)
            DeviceA:Gi0/2 <-> DeviceB:Gi0/2 (1Gbps)
            
            Result:
            DeviceA <-> DeviceB (2Gbps total)
        """
        # Get all raw links with device info
        result = await self.db.execute(
            select(RawLink, Device).join(Device, RawLink.local_device_id == Device.id)
        )
        raw_links = result.all()
        
        # Get device hostname map
        device_map = await self.get_device_map()
        
        # Group links by device pair (sorted to ensure consistent key)
        link_groups: Dict[Tuple[int, int], List[RawLink]] = {}
        
        for raw_link, local_device in raw_links:
            # Try to find the remote device
            remote_device = device_map.get(raw_link.remote_hostname)
            
            if not remote_device:
                # Remote device not in our database yet
                continue
            
            # Create consistent key (smaller id first)
            if local_device.id < remote_device.id:
                key = (local_device.id, remote_device.id)
            else:
                key = (remote_device.id, local_device.id)
            
            if key not in link_groups:
                link_groups[key] = []
            link_groups[key].append(raw_link)
        
        # Build merged links
        merged_links = []
        
        for (device_a_id, device_b_id), links in link_groups.items():
            # Get device info
            device_a = await self._get_device_by_id(device_a_id)
            device_b = await self._get_device_by_id(device_b_id)
            
            if not device_a or not device_b:
                continue
            
            # Aggregate port details
            port_details = []
            total_bandwidth = 0
            total_in_bps = 0
            total_out_bps = 0
            
            for link in links:
                # Estimate bandwidth from port name (simplified)
                bandwidth = self._estimate_bandwidth(link.local_port)
                total_bandwidth += bandwidth
                
                port_details.append(PortInfo(
                    local_port=link.local_port,
                    remote_port=link.remote_port,
                    bandwidth_mbps=bandwidth,
                    in_bps=0,  # Will be updated by collector
                    out_bps=0
                ))
            
            # Calculate utilization
            util_in = 0.0
            util_out = 0.0
            if total_bandwidth > 0:
                # Convert Mbps to bps for calculation
                total_bw_bps = total_bandwidth * 1_000_000
                util_in = (total_in_bps / total_bw_bps) * 100 if total_bw_bps > 0 else 0
                util_out = (total_out_bps / total_bw_bps) * 100 if total_bw_bps > 0 else 0
            
            merged_links.append(MergedLinkInfo(
                device_a_id=device_a_id,
                device_b_id=device_b_id,
                device_a_hostname=device_a.hostname,
                device_b_hostname=device_b.hostname,
                total_bandwidth_mbps=total_bandwidth,
                current_in_bps=total_in_bps,
                current_out_bps=total_out_bps,
                utilization_in_percent=util_in,
                utilization_out_percent=util_out,
                port_details=port_details
            ))
        
        return merged_links
    
    async def update_merged_links_in_db(self):
        """Update merged_links table from raw_links"""
        merged = await self.merge_links()
        
        for link_info in merged:
            # Check if merged link exists
            existing = await self.db.execute(
                select(MergedLink).where(
                    and_(
                        MergedLink.device_a_id == link_info.device_a_id,
                        MergedLink.device_b_id == link_info.device_b_id
                    )
                )
            )
            merged_link = existing.scalar_one_or_none()
            
            port_details_json = [
                {
                    "local_port": p.local_port,
                    "remote_port": p.remote_port,
                    "bandwidth_mbps": p.bandwidth_mbps,
                    "in_bps": p.in_bps,
                    "out_bps": p.out_bps
                }
                for p in link_info.port_details
            ]
            
            if merged_link:
                # Update existing
                merged_link.total_bandwidth_mbps = link_info.total_bandwidth_mbps
                merged_link.current_in_bps = link_info.current_in_bps
                merged_link.current_out_bps = link_info.current_out_bps
                merged_link.utilization_in_percent = link_info.utilization_in_percent
                merged_link.utilization_out_percent = link_info.utilization_out_percent
                merged_link.port_details = port_details_json
                merged_link.last_updated = datetime.utcnow()
            else:
                # Create new
                merged_link = MergedLink(
                    device_a_id=link_info.device_a_id,
                    device_b_id=link_info.device_b_id,
                    total_bandwidth_mbps=link_info.total_bandwidth_mbps,
                    current_in_bps=link_info.current_in_bps,
                    current_out_bps=link_info.current_out_bps,
                    utilization_in_percent=link_info.utilization_in_percent,
                    utilization_out_percent=link_info.utilization_out_percent,
                    port_details=port_details_json
                )
                self.db.add(merged_link)
        
        await self.db.commit()
        logger.info(f"Updated {len(merged)} merged links")
    
    async def get_topology_for_view(
        self,
        view: str = "overview",
        group_id: Optional[int] = None,
        expand_device_id: Optional[int] = None
    ) -> Dict:
        """
        Get topology data for frontend visualization
        
        Views:
        - overview: Core + Distribution devices only, Access aggregated
        - group: Devices in a group + their upstream connections
        - full: All devices
        """
        if view == "overview":
            return await self._get_overview_topology()
        elif view == "group" and group_id:
            return await self._get_group_topology(group_id)
        else:
            return await self._get_full_topology()
    
    async def _get_overview_topology(self) -> Dict:
        """Get overview topology with only Core and Distribution devices"""
        # Get core and distribution devices
        result = await self.db.execute(
            select(Device).where(
                Device.device_type.in_(["core", "distribution", "dist", "router"])
            )
        )
        devices = result.scalars().all()
        
        if not devices:
            # Fallback: get all devices if no type assigned
            result = await self.db.execute(select(Device).limit(50))
            devices = result.scalars().all()
        
        return await self._build_topology_response(devices)
    
    async def _get_group_topology(self, group_id: int) -> Dict:
        """Get topology for a specific group including upstream devices"""
        # Get devices in group
        members = await self.db.execute(
            select(DeviceGroupMember.device_id).where(
                DeviceGroupMember.group_id == group_id
            )
        )
        device_ids = [m[0] for m in members.all()]
        
        if not device_ids:
            return {"nodes": [], "links": [], "last_updated": datetime.utcnow().isoformat()}
        
        # Get the devices
        result = await self.db.execute(
            select(Device).where(Device.id.in_(device_ids))
        )
        group_devices = result.scalars().all()
        
        # Find upstream devices (devices connected to group devices but not in group)
        upstream_ids = set()
        for device in group_devices:
            # Find links where this device is involved
            links = await self.db.execute(
                select(MergedLink).where(
                    or_(
                        MergedLink.device_a_id == device.id,
                        MergedLink.device_b_id == device.id
                    )
                )
            )
            for link in links.scalars():
                other_id = link.device_b_id if link.device_a_id == device.id else link.device_a_id
                if other_id not in device_ids:
                    upstream_ids.add(other_id)
        
        # Get upstream devices
        if upstream_ids:
            upstream_result = await self.db.execute(
                select(Device).where(Device.id.in_(list(upstream_ids)))
            )
            upstream_devices = upstream_result.scalars().all()
            all_devices = list(group_devices) + list(upstream_devices)
        else:
            all_devices = list(group_devices)
        
        return await self._build_topology_response(all_devices)
    
    async def _get_full_topology(self) -> Dict:
        """Get full topology with all devices"""
        result = await self.db.execute(select(Device))
        devices = result.scalars().all()
        return await self._build_topology_response(devices)
    
    async def _build_topology_response(self, devices: List[Device]) -> Dict:
        """Build topology response for frontend"""
        device_ids = [d.id for d in devices]
        
        # Get alert counts per device
        from app.models.alert import Alert
        alert_counts = {}
        if device_ids:
            alert_result = await self.db.execute(
                select(Alert.device_id).where(
                    and_(
                        Alert.device_id.in_(device_ids),
                        Alert.is_active == True
                    )
                )
            )
            for row in alert_result:
                device_id = row[0]
                alert_counts[device_id] = alert_counts.get(device_id, 0) + 1
        
        # Build nodes
        nodes = []
        for device in devices:
            nodes.append({
                "id": str(device.id),
                "hostname": device.hostname,
                "ip_address": device.ip_address,
                "device_type": device.device_type or "switch",
                "vendor": device.vendor or "unknown",
                "status": device.status or "unknown",
                "cpu_percent": device.cpu_percent,
                "memory_percent": device.memory_percent,
                "alert_count": alert_counts.get(device.id, 0)
            })
        
        # Get links between these devices
        links = []
        if len(device_ids) >= 2:
            link_result = await self.db.execute(
                select(MergedLink).where(
                    and_(
                        MergedLink.device_a_id.in_(device_ids),
                        MergedLink.device_b_id.in_(device_ids),
                        MergedLink.is_excluded == False
                    )
                )
            )
            
            for link in link_result.scalars():
                max_util = max(
                    link.utilization_in_percent or 0,
                    link.utilization_out_percent or 0
                )
                
                links.append({
                    "id": str(link.id),
                    "source": str(link.device_a_id),
                    "target": str(link.device_b_id),
                    "total_bandwidth_mbps": link.total_bandwidth_mbps or 0,
                    "utilization_in_percent": link.utilization_in_percent or 0,
                    "utilization_out_percent": link.utilization_out_percent or 0,
                    "status": self._get_link_status(max_util),
                    "port_details": link.port_details or []
                })
        
        return {
            "nodes": nodes,
            "links": links,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def _get_device_by_id(self, device_id: int) -> Optional[Device]:
        """Get device by ID"""
        result = await self.db.execute(
            select(Device).where(Device.id == device_id)
        )
        return result.scalar_one_or_none()
    
    def _estimate_bandwidth(self, port_name: str) -> int:
        """Estimate bandwidth from port name"""
        port_lower = port_name.lower()
        
        if any(x in port_lower for x in ["hundred", "hu", "100g"]):
            return 100000
        elif any(x in port_lower for x in ["forty", "fo", "40g"]):
            return 40000
        elif any(x in port_lower for x in ["ten", "te", "10g", "xg"]):
            return 10000
        elif any(x in port_lower for x in ["gigabit", "gi", "ge", "1g"]):
            return 1000
        elif any(x in port_lower for x in ["fast", "fa", "100m"]):
            return 100
        else:
            return 1000  # Default to 1Gbps
    
    def _get_link_status(self, utilization: float) -> str:
        """Determine link status based on utilization"""
        if utilization >= 90:
            return "critical"
        elif utilization >= 70:
            return "warning"
        elif utilization >= 50:
            return "elevated"
        return "normal"
