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
from app.api import devices, topology, alerts, profiles, groups, discovery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Get static files path
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.app_name}...")
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
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


