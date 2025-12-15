"""
Settings API endpoints
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import json
import os

from app.db.database import get_db
from app.config import get_settings
from app.core.discovery_scheduler import start_discovery_scheduler, stop_discovery_scheduler, get_discovery_scheduler

router = APIRouter()
settings = get_settings()

# Settings file path
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "settings.json")


class SNMPSettings(BaseModel):
    default_community: str = "public"
    poll_interval: int = 60
    snmp_timeout: int = 5
    snmp_retries: int = 2
    allowed_subnets: List[str] = []
    enable_subnet_restriction: bool = False
    discovery_enabled: bool = True
    discovery_interval: int = 3600


def load_settings() -> SNMPSettings:
    """Load settings from file"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                return SNMPSettings(**data)
    except Exception as e:
        print(f"Error loading settings: {e}")
    
    return SNMPSettings()


def save_settings(settings_data: SNMPSettings):
    """Save settings to file"""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings_data.model_dump(), f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")


@router.get("", response_model=SNMPSettings)
async def get_snmp_settings():
    """Get current SNMP and discovery settings"""
    return load_settings()


@router.post("")
async def save_snmp_settings(settings_data: SNMPSettings):
    """Save SNMP and discovery settings"""
    save_settings(settings_data)
    
    # Restart discovery scheduler with new settings
    if settings_data.discovery_enabled and settings_data.allowed_subnets:
        await start_discovery_scheduler(
            subnets=settings_data.allowed_subnets,
            community=settings_data.default_community,
            interval=settings_data.discovery_interval
        )
    else:
        stop_discovery_scheduler()
    
    return {"success": True, "message": "Settings saved"}


@router.get("/discovery/status")
async def get_discovery_status():
    """Get current discovery scheduler status"""
    scheduler = get_discovery_scheduler()
    
    if scheduler and scheduler.running:
        return {
            "running": True,
            "subnets": scheduler.allowed_subnets,
            "interval": scheduler.interval
        }
    
    return {"running": False}


@router.post("/discovery/trigger")
async def trigger_discovery():
    """Manually trigger a discovery cycle"""
    scheduler = get_discovery_scheduler()
    
    if scheduler and scheduler.running:
        # Run discovery in background
        import asyncio
        asyncio.create_task(scheduler.run_discovery_cycle())
        return {"success": True, "message": "Discovery cycle started"}
    
    return {"success": False, "message": "Discovery scheduler not running"}
