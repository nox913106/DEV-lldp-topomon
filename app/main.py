"""
FastAPI main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
import os

from app.config import get_settings
from app.db.database import init_db
from app.api import devices, topology, alerts, profiles, groups, discovery, snmp, settings
from app.core.discovery_scheduler import start_discovery_scheduler
from app.api.settings import load_settings as load_app_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings_config = get_settings()

# Get static files path
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings_config.app_name}...")
    await init_db()
    logger.info("Database initialized")
    
    # Start discovery scheduler if enabled
    app_settings = load_app_settings()
    if app_settings.discovery_enabled and app_settings.allowed_subnets:
        await start_discovery_scheduler(
            subnets=app_settings.allowed_subnets,
            community=app_settings.default_community,
            interval=app_settings.discovery_interval
        )
        logger.info("Discovery Scheduler started")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings_config.app_name}...")


# Create FastAPI application
app = FastAPI(
    title=settings_config.app_name,
    description="LLDP/CDP Network Topology Monitor",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(devices.router, prefix="/api/v1/devices", tags=["Devices"])
app.include_router(topology.router, prefix="/api/v1/topology", tags=["Topology"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(profiles.router, prefix="/api/v1/profiles", tags=["Alert Profiles"])
app.include_router(groups.router, prefix="/api/v1/groups", tags=["Device Groups"])
app.include_router(discovery.router, prefix="/api/v1/discovery", tags=["Discovery"])
app.include_router(snmp.router, prefix="/api/v1/snmp", tags=["SNMP Testing"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["Settings"])

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    """Serve the main web interface"""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/devices")
async def devices_page():
    """Serve the devices management page"""
    return FileResponse(os.path.join(STATIC_DIR, "devices.html"))


@app.get("/alerts")
async def alerts_page():
    """Serve the alerts dashboard page"""
    return FileResponse(os.path.join(STATIC_DIR, "alerts.html"))


@app.get("/groups")
async def groups_page():
    """Serve the groups management page"""
    return FileResponse(os.path.join(STATIC_DIR, "groups.html"))


@app.get("/settings")
async def settings_page():
    """Serve the settings page"""
    return FileResponse(os.path.join(STATIC_DIR, "settings.html"))


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


