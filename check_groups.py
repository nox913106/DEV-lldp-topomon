"""Check group membership data"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.db.database import async_session_maker
from app.models.group import DeviceGroup, DeviceGroupMember
from app.models.device import Device
from app.models.alert import AlertProfile  # Required for relationships
from sqlalchemy import select

async def check():
    async with async_session_maker() as db:
        # Get all groups
        result = await db.execute(select(DeviceGroup))
        groups = result.scalars().all()
        print("=== Groups ===")
        for g in groups:
            print(f"  ID={g.id}, Name={g.name}")
        
        # Check each group's members
        for group in groups:
            result = await db.execute(
                select(DeviceGroupMember).where(DeviceGroupMember.group_id == group.id)
            )
            members = result.scalars().all()
            print(f"\n=== {group.name} (ID={group.id}) - {len(members)} members ===")
            for m in members:
                dev_result = await db.execute(select(Device).where(Device.id == m.device_id))
                dev = dev_result.scalar_one_or_none()
                if dev:
                    print(f"  Device ID={dev.id}, Hostname={dev.hostname}, Type={dev.device_type}")

if __name__ == "__main__":
    asyncio.run(check())
