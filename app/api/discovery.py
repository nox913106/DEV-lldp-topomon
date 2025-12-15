"""
Discovery API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from app.db.database import get_db

router = APIRouter()

# In-memory job status (in production, use Redis)
discovery_jobs = {}


class DiscoveryStartRequest(BaseModel):
    seed_device_id: int


class DiscoveryStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: dict
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


async def run_discovery(job_id: str, seed_device_id: int):
    """Background task for running discovery"""
    # TODO: Implement actual discovery logic using SNMP
    discovery_jobs[job_id]["status"] = "running"
    
    # Placeholder - will be implemented in SNMP collector
    import asyncio
    await asyncio.sleep(2)
    
    discovery_jobs[job_id]["status"] = "completed"
    discovery_jobs[job_id]["completed_at"] = datetime.utcnow()
    discovery_jobs[job_id]["progress"] = {
        "discovered": 0,
        "pending": 0,
        "failed": 0
    }


@router.post("/start", response_model=DiscoveryStatusResponse)
async def start_discovery(
    request: DiscoveryStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Start device discovery from a seed device"""
    job_id = str(uuid.uuid4())[:8]
    
    discovery_jobs[job_id] = {
        "job_id": job_id,
        "status": "started",
        "progress": {"discovered": 0, "pending": 1, "failed": 0},
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "error": None
    }
    
    background_tasks.add_task(run_discovery, job_id, request.seed_device_id)
    
    return DiscoveryStatusResponse(**discovery_jobs[job_id])


@router.get("/status", response_model=Optional[DiscoveryStatusResponse])
async def get_discovery_status(job_id: Optional[str] = None):
    """Get discovery job status"""
    if job_id and job_id in discovery_jobs:
        return DiscoveryStatusResponse(**discovery_jobs[job_id])
    
    # Return latest job if no job_id specified
    if discovery_jobs:
        latest = max(discovery_jobs.values(), key=lambda x: x["started_at"])
        return DiscoveryStatusResponse(**latest)
    
    return None


class ManualDiscoveryRequest(BaseModel):
    ip: str
    community: str = "public"
    recursive: bool = True


class DeviceDiscovered(BaseModel):
    ip: str
    hostname: Optional[str] = None
    is_new: bool = False


class ManualDiscoveryResponse(BaseModel):
    success: bool
    discovered_count: int = 0
    added_count: int = 0
    devices: list = []
    error: Optional[str] = None


@router.post("/manual", response_model=ManualDiscoveryResponse)
async def manual_discover(request: ManualDiscoveryRequest, db: AsyncSession = Depends(get_db)):
    """
    Manually discover devices starting from an IP address
    """
    try:
        from sqlalchemy import select
        from app.models.device import Device
        from app.core.snmp_oids import detect_vendor, LLDP_REM_SYS_NAME, IF_DESCR
        from datetime import datetime
        
        discovered_devices = []
        added_count = 0
        
        async def discover_single_device(ip: str, community: str) -> dict:
            """Discover a single device and return its info"""
            hostname = None
            sys_descr = None
            vendor = "unknown"
            
            try:
                from pysnmp.hlapi.asyncio import (
                    getCmd, SnmpEngine, CommunityData, 
                    UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
                )
                
                # Get sysName
                errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
                    SnmpEngine(),
                    CommunityData(community),
                    UdpTransportTarget((ip, 161), timeout=5.0, retries=1),
                    ContextData(),
                    ObjectType(ObjectIdentity('1.3.6.1.2.1.1.5.0')),  # sysName
                    ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0'))   # sysDescr
                )
                
                if not errorIndication and not errorStatus and varBinds:
                    hostname = varBinds[0][1].prettyPrint()
                    sys_descr = varBinds[1][1].prettyPrint() if len(varBinds) > 1 else ""
                    vendor = detect_vendor(sys_descr)
                    
            except ImportError:
                pass
            except Exception as e:
                print(f"SNMP connection to {ip} failed: {e}")
            
            return {
                "ip": ip,
                "hostname": hostname or f"device-{ip.replace('.', '-')}",
                "sys_descr": sys_descr or "",
                "vendor": vendor
            }
        
        async def get_lldp_neighbors(ip: str, community: str) -> list:
            """Get LLDP neighbors from a device"""
            neighbors = []
            
            try:
                from pysnmp.hlapi.asyncio import (
                    bulkCmd, SnmpEngine, CommunityData, 
                    UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
                )
                
                # Walk LLDP remote system names
                iterator = bulkCmd(
                    SnmpEngine(),
                    CommunityData(community),
                    UdpTransportTarget((ip, 161), timeout=5.0, retries=1),
                    ContextData(),
                    0, 25,
                    ObjectType(ObjectIdentity(LLDP_REM_SYS_NAME)),
                    lexicographicMode=False
                )
                
                async for errorIndication, errorStatus, errorIndex, varBinds in iterator:
                    if errorIndication or errorStatus:
                        break
                    
                    for varBind in varBinds:
                        oid_str = str(varBind[0])
                        if LLDP_REM_SYS_NAME in oid_str:
                            remote_hostname = varBind[1].prettyPrint()
                            if remote_hostname and remote_hostname not in neighbors:
                                neighbors.append(remote_hostname)
                        else:
                            break
                    
                    if len(neighbors) >= 50:
                        break
                        
            except ImportError:
                pass
            except Exception as e:
                print(f"LLDP discovery for {ip} failed: {e}")
            
            return neighbors
        
        # Discover the initial device
        device_info = await discover_single_device(request.ip, request.community)
        
        # Check if device already exists
        result = await db.execute(
            select(Device).where(Device.ip_address == request.ip)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing device info
            existing.hostname = device_info["hostname"]
            existing.vendor = device_info["vendor"]
            existing.last_seen = datetime.utcnow()
            existing.status = "managed"
            await db.commit()
            
            discovered_devices.append({
                "ip": request.ip,
                "hostname": existing.hostname,
                "is_new": False
            })
        else:
            # Add new device
            new_device = Device(
                hostname=device_info["hostname"],
                ip_address=request.ip,
                snmp_community=request.community,
                device_type="access",
                vendor=device_info["vendor"],
                status="managed",
                last_seen=datetime.utcnow()
            )
            db.add(new_device)
            await db.commit()
            await db.refresh(new_device)
            
            discovered_devices.append({
                "ip": request.ip,
                "hostname": new_device.hostname,
                "is_new": True
            })
            added_count += 1
        
        # Recursive discovery: discover LLDP neighbors
        if request.recursive:
            lldp_neighbors = await get_lldp_neighbors(request.ip, request.community)
            print(f"Found {len(lldp_neighbors)} LLDP neighbors: {lldp_neighbors}")
            
            # For each neighbor, we need to resolve its IP
            # This is complex in real world - neighbors are identified by hostname
            # For now, we just log them. In production, you'd need to:
            # 1. Query CDP/LLDP cache for IP addresses
            # 2. Or use DNS to resolve hostnames
            # 3. Or maintain a mapping table
            
        return ManualDiscoveryResponse(
            success=True,
            discovered_count=len(discovered_devices),
            added_count=added_count,
            devices=discovered_devices
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ManualDiscoveryResponse(
            success=False,
            error=str(e)
        )

