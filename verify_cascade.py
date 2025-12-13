"""Verify cascade offline scenario"""
import asyncio
from app.db.database import async_session_maker
from app.models import Device, Alert
from sqlalchemy import select

async def verify():
    print("=" * 60)
    print("Verify Cascade Offline Scenario")
    print("=" * 60)
    
    async with async_session_maker() as db:
        # 1. Offline devices
        result = await db.execute(
            select(Device).where(Device.status == "offline")
        )
        offline_devices = result.scalars().all()
        
        print(f"\nOffline Devices ({len(offline_devices)}):")
        for d in offline_devices:
            print(f"   - {d.hostname} ({d.device_type})")
        
        # 2. device_offline alerts
        result = await db.execute(
            select(Alert, Device.hostname)
            .join(Device, Alert.device_id == Device.id)
            .where(Alert.alert_type == "device_offline")
            .order_by(Alert.id)
        )
        
        print(f"\nDevice Offline Alerts:")
        for alert, hostname in result:
            details = alert.details or {}
            is_root = details.get("is_root_cause", False)
            marker = "[ROOT CAUSE]" if is_root else "            "
            impact = details.get("impact_count", "-")
            print(f"   {marker} {hostname}: impact={impact}")
            if is_root:
                affected = details.get("affected_hostnames", [])
                print(f"                Affected: {', '.join(affected)}")

if __name__ == "__main__":
    asyncio.run(verify())
