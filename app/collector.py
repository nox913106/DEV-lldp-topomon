"""
Background collector service
Runs periodic SNMP polling of all managed devices
"""
import asyncio
import logging
from datetime import datetime

from app.config import get_settings
from app.db.database import async_session_maker
from app.core.snmp_collector import SNMPCollector
from app.models.device import Device, DeviceStatus
from app.models.link import RawLink, MergedLink
from sqlalchemy import select

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


async def poll_all_devices():
    """Poll all managed devices"""
    collector = SNMPCollector(
        community=settings.snmp_default_community,
        timeout=settings.snmp_timeout,
        retries=settings.snmp_retries
    )
    
    async with async_session_maker() as db:
        # Get all managed devices
        result = await db.execute(
            select(Device).where(Device.status != DeviceStatus.EXCLUDED)
        )
        devices = result.scalars().all()
        
        logger.info(f"Starting poll cycle for {len(devices)} devices")
        
        # Poll devices concurrently with limit
        semaphore = asyncio.Semaphore(settings.collector_concurrent)
        
        async def poll_with_semaphore(device):
            async with semaphore:
                return await poll_single_device(collector, device, db)
        
        tasks = [poll_with_semaphore(d) for d in devices]
        await asyncio.gather(*tasks)
        
        await db.commit()
        logger.info("Poll cycle completed")


async def poll_single_device(collector: SNMPCollector, device: Device, db):
    """Poll a single device and update database"""
    try:
        result = await collector.poll_device(device.ip_address)
        
        if result["success"]:
            # Update device info
            device.status = DeviceStatus.MANAGED
            device.last_seen = datetime.utcnow()
            
            if result["metrics"]:
                device.cpu_percent = result["metrics"].cpu_percent
                device.memory_percent = result["metrics"].memory_percent
            
            if result["device_info"]:
                device.vendor = result["device_info"].vendor
                device.uptime_seconds = result["device_info"].uptime_seconds
            
            # Update raw links
            for neighbor in result["lldp_neighbors"] + result["cdp_neighbors"]:
                # Check if link already exists
                existing = await db.execute(
                    select(RawLink).where(
                        RawLink.local_device_id == device.id,
                        RawLink.local_port == neighbor.local_port,
                        RawLink.remote_hostname == neighbor.remote_hostname
                    )
                )
                raw_link = existing.scalar_one_or_none()
                
                if raw_link:
                    raw_link.last_seen = datetime.utcnow()
                else:
                    raw_link = RawLink(
                        local_device_id=device.id,
                        local_port=neighbor.local_port,
                        local_port_index=neighbor.local_port_index,
                        remote_hostname=neighbor.remote_hostname,
                        remote_port=neighbor.remote_port,
                        remote_chassis_id=neighbor.remote_chassis_id,
                        protocol=neighbor.protocol
                    )
                    db.add(raw_link)
            
            logger.debug(f"Polled {device.hostname}: OK")
        else:
            # Mark device as potentially offline
            device.status = DeviceStatus.OFFLINE
            logger.warning(f"Polled {device.hostname}: FAILED")
            
    except Exception as e:
        logger.error(f"Error polling {device.hostname}: {e}")
        device.status = DeviceStatus.OFFLINE


async def main():
    """Main collector loop"""
    logger.info(f"SNMP Collector starting (interval: {settings.collector_interval}s)")
    
    while True:
        try:
            await poll_all_devices()
        except Exception as e:
            logger.error(f"Poll cycle error: {e}")
        
        await asyncio.sleep(settings.collector_interval)


if __name__ == "__main__":
    asyncio.run(main())
