"""
Discovery Scheduler - Automatically scans subnets to discover new devices
"""
import asyncio
import logging
import ipaddress
from datetime import datetime
from typing import List, Optional

from app.config import get_settings
from app.db.database import async_session_maker
from app.models.device import Device
from sqlalchemy import select

logger = logging.getLogger(__name__)
settings = get_settings()


class DiscoveryScheduler:
    """Handles automatic subnet scanning for device discovery"""
    
    def __init__(self, allowed_subnets: List[str], community: str, interval: int = 3600):
        self.allowed_subnets = allowed_subnets
        self.community = community
        self.interval = interval  # seconds between scans
        self.running = False
    
    async def start(self):
        """Start the discovery scheduler"""
        self.running = True
        logger.info(f"Discovery Scheduler starting (interval: {self.interval}s)")
        
        while self.running:
            try:
                await self.run_discovery_cycle()
            except Exception as e:
                logger.error(f"Discovery cycle error: {e}")
            
            await asyncio.sleep(self.interval)
    
    def stop(self):
        """Stop the discovery scheduler"""
        self.running = False
        logger.info("Discovery Scheduler stopped")
    
    async def run_discovery_cycle(self):
        """Run a single discovery cycle"""
        if not self.allowed_subnets:
            logger.debug("No subnets configured for discovery")
            return
        
        logger.info(f"Starting discovery cycle for {len(self.allowed_subnets)} subnets")
        
        total_discovered = 0
        total_added = 0
        
        for subnet_str in self.allowed_subnets:
            try:
                discovered, added = await self.scan_subnet(subnet_str)
                total_discovered += discovered
                total_added += added
            except Exception as e:
                logger.error(f"Error scanning subnet {subnet_str}: {e}")
        
        logger.info(f"Discovery cycle completed: discovered={total_discovered}, added={total_added}")
    
    async def scan_subnet(self, subnet_str: str) -> tuple:
        """Scan a subnet for devices"""
        try:
            network = ipaddress.ip_network(subnet_str, strict=False)
        except ValueError as e:
            logger.error(f"Invalid subnet: {subnet_str} - {e}")
            return (0, 0)
        
        # Limit scan size to prevent overload
        max_hosts = 256
        hosts = list(network.hosts())[:max_hosts]
        
        logger.info(f"Scanning subnet {subnet_str} ({len(hosts)} hosts)")
        
        discovered = 0
        added = 0
        
        # Scan in batches to avoid overwhelming the network
        batch_size = 20
        for i in range(0, len(hosts), batch_size):
            batch = hosts[i:i + batch_size]
            tasks = [self.probe_device(str(ip)) for ip in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict) and result.get("success"):
                    discovered += 1
                    if result.get("added"):
                        added += 1
        
        return (discovered, added)
    
    async def probe_device(self, ip: str) -> dict:
        """Probe a single IP for SNMP response"""
        try:
            from pysnmp.hlapi.asyncio import (
                getCmd, SnmpEngine, CommunityData,
                UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
            )
            from app.core.snmp_oids import detect_vendor, SYS_NAME, SYS_DESCR
            
            # Try SNMP GET sysName and sysDescr
            error_indication, error_status, error_index, var_binds = await getCmd(
                SnmpEngine(),
                CommunityData(self.community),
                UdpTransportTarget((ip, 161), timeout=2.0, retries=0),
                ContextData(),
                ObjectType(ObjectIdentity(SYS_NAME)),
                ObjectType(ObjectIdentity(SYS_DESCR))
            )
            
            if error_indication or error_status:
                return {"success": False, "ip": ip}
            
            if not var_binds:
                return {"success": False, "ip": ip}
            
            hostname = var_binds[0][1].prettyPrint()
            sys_descr = var_binds[1][1].prettyPrint() if len(var_binds) > 1 else ""
            vendor = detect_vendor(sys_descr)
            
            # Check if device already exists
            async with async_session_maker() as db:
                result = await db.execute(
                    select(Device).where(Device.ip_address == ip)
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    return {"success": True, "ip": ip, "added": False, "hostname": hostname}
                
                # Add new device
                new_device = Device(
                    hostname=hostname,
                    ip_address=ip,
                    snmp_community=self.community,
                    device_type="access",
                    vendor=vendor,
                    status="managed",
                    auto_discover=True,
                    last_seen=datetime.utcnow()
                )
                db.add(new_device)
                await db.commit()
                
                logger.info(f"Discovered new device: {hostname} ({ip})")
                return {"success": True, "ip": ip, "added": True, "hostname": hostname}
                
        except Exception as e:
            logger.debug(f"Probe failed for {ip}: {e}")
            return {"success": False, "ip": ip, "error": str(e)}


# Global scheduler instance
_scheduler: Optional[DiscoveryScheduler] = None


def get_discovery_scheduler() -> Optional[DiscoveryScheduler]:
    """Get the global discovery scheduler instance"""
    return _scheduler


async def start_discovery_scheduler(subnets: List[str], community: str, interval: int = 3600):
    """Start the global discovery scheduler"""
    global _scheduler
    
    if _scheduler and _scheduler.running:
        _scheduler.stop()
    
    _scheduler = DiscoveryScheduler(subnets, community, interval)
    asyncio.create_task(_scheduler.start())


def stop_discovery_scheduler():
    """Stop the global discovery scheduler"""
    global _scheduler
    
    if _scheduler:
        _scheduler.stop()
        _scheduler = None
