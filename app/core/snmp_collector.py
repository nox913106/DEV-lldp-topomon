"""
SNMP Collector - Collects LLDP/CDP and interface data from network devices
"""
import asyncio
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pysnmp.hlapi.asyncio import *

from app.core.snmp_oids import (
    LLDP_REM_SYS_NAME, LLDP_REM_PORT_ID, LLDP_REM_CHASSIS_ID,
    CDP_CACHE_DEVICE_ID, CDP_CACHE_DEVICE_PORT,
    IF_DESCR, IF_HIGH_SPEED, IF_HC_IN_OCTETS, IF_HC_OUT_OCTETS,
    SYS_NAME, SYS_DESCR, SYS_UPTIME,
    VENDOR_OIDS, detect_vendor
)

logger = logging.getLogger(__name__)


@dataclass
class DeviceInfo:
    """Device information from SNMP"""
    hostname: str
    sys_descr: str
    uptime_seconds: int
    vendor: str


@dataclass
class LLDPNeighbor:
    """LLDP neighbor information"""
    local_port: str
    local_port_index: int
    remote_hostname: str
    remote_port: str
    remote_chassis_id: str
    protocol: str = "lldp"


@dataclass
class InterfaceStats:
    """Interface statistics"""
    port_name: str
    port_index: int
    speed_mbps: int
    in_octets: int
    out_octets: int


@dataclass
class DeviceMetrics:
    """Device CPU/Memory metrics"""
    cpu_percent: float
    memory_percent: float


class SNMPCollector:
    """SNMP data collector for network devices"""
    
    def __init__(
        self,
        community: str = "public",
        timeout: int = 5,
        retries: int = 2
    ):
        self.community = community
        self.timeout = timeout
        self.retries = retries
    
    async def _snmp_get(self, ip: str, oid: str) -> Optional[Any]:
        """Perform SNMP GET operation"""
        try:
            iterator = getCmd(
                SnmpEngine(),
                CommunityData(self.community),
                UdpTransportTarget((ip, 161), timeout=self.timeout, retries=self.retries),
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            )
            
            error_indication, error_status, error_index, var_binds = await iterator
            
            if error_indication or error_status:
                logger.warning(f"SNMP error for {ip}: {error_indication or error_status}")
                return None
            
            if var_binds:
                return var_binds[0][1]
            return None
            
        except Exception as e:
            logger.error(f"SNMP GET failed for {ip}: {e}")
            return None
    
    async def _snmp_walk(self, ip: str, oid: str) -> Dict[str, Any]:
        """Perform SNMP WALK operation"""
        results = {}
        
        try:
            iterator = bulkCmd(
                SnmpEngine(),
                CommunityData(self.community),
                UdpTransportTarget((ip, 161), timeout=self.timeout, retries=self.retries),
                ContextData(),
                0, 25,  # non-repeaters, max-repetitions
                ObjectType(ObjectIdentity(oid)),
                lexicographicMode=False
            )
            
            async for error_indication, error_status, error_index, var_binds in iterator:
                if error_indication or error_status:
                    break
                
                for var_bind in var_binds:
                    oid_str = str(var_bind[0])
                    if oid_str.startswith(oid):
                        # Extract index from OID
                        index = oid_str[len(oid)+1:] if len(oid_str) > len(oid) else ""
                        results[index] = var_bind[1]
                    else:
                        # Walked past our OID tree
                        return results
            
        except Exception as e:
            logger.error(f"SNMP WALK failed for {ip}: {e}")
        
        return results
    
    async def get_device_info(self, ip: str) -> Optional[DeviceInfo]:
        """Get basic device information"""
        sys_name = await self._snmp_get(ip, SYS_NAME)
        sys_descr = await self._snmp_get(ip, SYS_DESCR)
        sys_uptime = await self._snmp_get(ip, SYS_UPTIME)
        
        if not sys_name:
            return None
        
        sys_descr_str = str(sys_descr) if sys_descr else ""
        vendor = detect_vendor(sys_descr_str)
        
        return DeviceInfo(
            hostname=str(sys_name),
            sys_descr=sys_descr_str,
            uptime_seconds=int(sys_uptime) // 100 if sys_uptime else 0,
            vendor=vendor
        )
    
    async def get_lldp_neighbors(self, ip: str) -> List[LLDPNeighbor]:
        """Get LLDP neighbor information"""
        neighbors = []
        
        # Walk LLDP remote system names
        sys_names = await self._snmp_walk(ip, LLDP_REM_SYS_NAME)
        port_ids = await self._snmp_walk(ip, LLDP_REM_PORT_ID)
        chassis_ids = await self._snmp_walk(ip, LLDP_REM_CHASSIS_ID)
        
        # Get local interface descriptions for mapping
        if_descrs = await self._snmp_walk(ip, IF_DESCR)
        
        for index, remote_name in sys_names.items():
            # Index format: time_mark.local_port_num.remote_index
            parts = index.split(".")
            if len(parts) >= 2:
                local_port_index = int(parts[1]) if parts[1].isdigit() else 0
                local_port = str(if_descrs.get(str(local_port_index), f"Port{local_port_index}"))
            else:
                local_port_index = 0
                local_port = "Unknown"
            
            remote_port = str(port_ids.get(index, "")) if index in port_ids else ""
            chassis_id = str(chassis_ids.get(index, "")) if index in chassis_ids else ""
            
            neighbors.append(LLDPNeighbor(
                local_port=local_port,
                local_port_index=local_port_index,
                remote_hostname=str(remote_name),
                remote_port=remote_port,
                remote_chassis_id=chassis_id,
                protocol="lldp"
            ))
        
        return neighbors
    
    async def get_cdp_neighbors(self, ip: str) -> List[LLDPNeighbor]:
        """Get CDP neighbor information (Cisco devices)"""
        neighbors = []
        
        device_ids = await self._snmp_walk(ip, CDP_CACHE_DEVICE_ID)
        device_ports = await self._snmp_walk(ip, CDP_CACHE_DEVICE_PORT)
        
        if_descrs = await self._snmp_walk(ip, IF_DESCR)
        
        for index, device_id in device_ids.items():
            # Index format: ifIndex.cdpCacheDeviceIndex
            parts = index.split(".")
            local_port_index = int(parts[0]) if parts and parts[0].isdigit() else 0
            local_port = str(if_descrs.get(str(local_port_index), f"Port{local_port_index}"))
            
            remote_port = str(device_ports.get(index, "")) if index in device_ports else ""
            
            neighbors.append(LLDPNeighbor(
                local_port=local_port,
                local_port_index=local_port_index,
                remote_hostname=str(device_id),
                remote_port=remote_port,
                remote_chassis_id="",
                protocol="cdp"
            ))
        
        return neighbors
    
    async def get_interface_stats(self, ip: str) -> List[InterfaceStats]:
        """Get interface traffic statistics"""
        stats = []
        
        if_descrs = await self._snmp_walk(ip, IF_DESCR)
        if_speeds = await self._snmp_walk(ip, IF_HIGH_SPEED)
        in_octets = await self._snmp_walk(ip, IF_HC_IN_OCTETS)
        out_octets = await self._snmp_walk(ip, IF_HC_OUT_OCTETS)
        
        for index, descr in if_descrs.items():
            try:
                port_index = int(index)
                speed = int(if_speeds.get(index, 0))
                in_oct = int(in_octets.get(index, 0))
                out_oct = int(out_octets.get(index, 0))
                
                # Skip interfaces with no speed (usually management/loopback)
                if speed > 0:
                    stats.append(InterfaceStats(
                        port_name=str(descr),
                        port_index=port_index,
                        speed_mbps=speed,
                        in_octets=in_oct,
                        out_octets=out_oct
                    ))
            except (ValueError, TypeError):
                continue
        
        return stats
    
    async def get_device_metrics(self, ip: str, vendor: str) -> Optional[DeviceMetrics]:
        """Get device CPU and memory metrics"""
        if vendor not in VENDOR_OIDS:
            return None
        
        oids = VENDOR_OIDS[vendor]
        cpu_percent = 0.0
        memory_percent = 0.0
        
        try:
            if "cpu" in oids:
                cpu_val = await self._snmp_get(ip, oids["cpu"])
                if cpu_val:
                    cpu_percent = float(cpu_val)
            elif "cpu_5min" in oids:
                cpu_val = await self._snmp_get(ip, oids["cpu_5min"])
                if cpu_val:
                    cpu_percent = float(cpu_val)
            
            if "memory" in oids:
                mem_val = await self._snmp_get(ip, oids["memory"])
                if mem_val:
                    memory_percent = float(mem_val)
            elif "memory_used" in oids and "memory_free" in oids:
                used = await self._snmp_get(ip, oids["memory_used"])
                free = await self._snmp_get(ip, oids["memory_free"])
                if used and free:
                    total = int(used) + int(free)
                    if total > 0:
                        memory_percent = (int(used) / total) * 100
            
            return DeviceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent
            )
            
        except Exception as e:
            logger.error(f"Failed to get metrics for {ip}: {e}")
            return None
    
    async def poll_device(self, ip: str) -> Dict:
        """Poll a single device for all data"""
        result = {
            "ip": ip,
            "success": False,
            "device_info": None,
            "lldp_neighbors": [],
            "cdp_neighbors": [],
            "interface_stats": [],
            "metrics": None
        }
        
        # Get device info
        device_info = await self.get_device_info(ip)
        if not device_info:
            return result
        
        result["device_info"] = device_info
        result["success"] = True
        
        # Get neighbors
        lldp = await self.get_lldp_neighbors(ip)
        result["lldp_neighbors"] = lldp
        
        # Try CDP for Cisco devices
        if "cisco" in device_info.vendor:
            cdp = await self.get_cdp_neighbors(ip)
            result["cdp_neighbors"] = cdp
        
        # Get interface stats
        stats = await self.get_interface_stats(ip)
        result["interface_stats"] = stats
        
        # Get metrics
        metrics = await self.get_device_metrics(ip, device_info.vendor)
        result["metrics"] = metrics
        
        return result
