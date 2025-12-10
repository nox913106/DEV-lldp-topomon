"""
Application configuration management
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "DEV-lldp-topomon"
    app_debug: bool = False
    app_log_level: str = "INFO"
    
    # Database
    database_url: str = "postgresql+asyncpg://topomon:topomon@localhost:5432/topomon"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # SNMP Settings
    snmp_default_community: str = "public"
    snmp_timeout: int = 5
    snmp_retries: int = 2
    
    # Collector Settings
    collector_interval: int = 300  # 5 minutes
    collector_concurrent: int = 20
    
    # Log Export (Optional)
    log_export_enabled: bool = False
    log_export_type: str = "elasticsearch"
    elasticsearch_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
