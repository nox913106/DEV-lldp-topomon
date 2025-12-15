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
    app_secret_key: str = "change-this-to-random-string"
    
    # Database (默認使用 SQLite 方便本地測試)
    database_url: str = "sqlite+aiosqlite:///./topomon.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # SNMP Settings
    snmp_default_community: str = "public"
    snmp_timeout: int = 5
    snmp_retries: int = 2
    
    # Collector Settings
    collector_interval: int = 300  # 5 minutes
    collector_concurrent: int = 20
    
    # Discovery Settings
    discovery_enabled: bool = True
    discovery_interval: int = 3600  # 1 hour
    allowed_subnets: str = ""  # Comma-separated CIDR list
    
    # Log Export (Optional)
    log_export_enabled: bool = False
    log_export_type: str = "elasticsearch"
    elasticsearch_url: Optional[str] = None
    elasticsearch_index_prefix: str = "topomon-"
    
    # Graylog Settings (Optional)
    graylog_host: str = "localhost"
    graylog_port: int = 12201
    graylog_protocol: str = "udp"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # 忽略額外的環境變數


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
