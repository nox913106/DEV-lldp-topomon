"""
Log Exporter - Sends logs and alerts to Elasticsearch and Graylog
"""
import logging
import json
import socket
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LogLevel(str, Enum):
    """Log severity levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: str
    level: str
    source: str
    message: str
    device_hostname: Optional[str] = None
    device_ip: Optional[str] = None
    alert_type: Optional[str] = None
    alert_severity: Optional[str] = None
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    extra: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, removing None values"""
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None}


class ElasticsearchExporter:
    """Export logs to Elasticsearch"""
    
    def __init__(self, url: str, index_prefix: str = "topomon-"):
        self.url = url.rstrip("/")
        self.index_prefix = index_prefix
        self.client = httpx.AsyncClient(timeout=10.0)
    
    def _get_index_name(self) -> str:
        """Get index name with date suffix"""
        date_suffix = datetime.utcnow().strftime("%Y.%m.%d")
        return f"{self.index_prefix}{date_suffix}"
    
    async def send(self, entry: LogEntry) -> bool:
        """Send log entry to Elasticsearch"""
        try:
            index_name = self._get_index_name()
            url = f"{self.url}/{index_name}/_doc"
            
            response = await self.client.post(
                url,
                json=entry.to_dict(),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in (200, 201):
                return True
            else:
                logger.warning(f"Elasticsearch response: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send to Elasticsearch: {e}")
            return False
    
    async def send_bulk(self, entries: list[LogEntry]) -> int:
        """Send multiple log entries using bulk API"""
        if not entries:
            return 0
        
        try:
            index_name = self._get_index_name()
            
            # Build bulk request body
            bulk_body = ""
            for entry in entries:
                bulk_body += json.dumps({"index": {"_index": index_name}}) + "\n"
                bulk_body += json.dumps(entry.to_dict()) + "\n"
            
            response = await self.client.post(
                f"{self.url}/_bulk",
                content=bulk_body,
                headers={"Content-Type": "application/x-ndjson"}
            )
            
            if response.status_code == 200:
                result = response.json()
                return len(entries) - len([i for i in result.get("items", []) if i.get("error")])
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to send bulk to Elasticsearch: {e}")
            return 0
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


class GraylogExporter:
    """Export logs to Graylog using GELF format"""
    
    def __init__(self, host: str, port: int = 12201, protocol: str = "udp"):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.socket = None
        
        if protocol == "udp":
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        elif protocol == "tcp":
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def _to_gelf(self, entry: LogEntry) -> Dict[str, Any]:
        """Convert log entry to GELF format"""
        # Map log levels to syslog levels
        level_map = {
            "DEBUG": 7,
            "INFO": 6,
            "WARNING": 4,
            "ERROR": 3,
            "CRITICAL": 2
        }
        
        gelf = {
            "version": "1.1",
            "host": "topomon",
            "short_message": entry.message[:250],
            "full_message": entry.message,
            "timestamp": datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00")).timestamp(),
            "level": level_map.get(entry.level, 6),
            "_source": entry.source
        }
        
        # Add custom fields
        if entry.device_hostname:
            gelf["_device_hostname"] = entry.device_hostname
        if entry.device_ip:
            gelf["_device_ip"] = entry.device_ip
        if entry.alert_type:
            gelf["_alert_type"] = entry.alert_type
        if entry.alert_severity:
            gelf["_alert_severity"] = entry.alert_severity
        if entry.metric_name:
            gelf["_metric_name"] = entry.metric_name
        if entry.metric_value is not None:
            gelf["_metric_value"] = entry.metric_value
        if entry.threshold_value is not None:
            gelf["_threshold_value"] = entry.threshold_value
        if entry.extra:
            for key, value in entry.extra.items():
                gelf[f"_{key}"] = value
        
        return gelf
    
    def send(self, entry: LogEntry) -> bool:
        """Send log entry to Graylog"""
        try:
            gelf_message = json.dumps(self._to_gelf(entry)).encode("utf-8")
            
            if self.protocol == "udp":
                self.socket.sendto(gelf_message, (self.host, self.port))
            elif self.protocol == "tcp":
                if not self.socket._closed:
                    self.socket.connect((self.host, self.port))
                self.socket.send(gelf_message + b"\0")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send to Graylog: {e}")
            return False
    
    def close(self):
        """Close the socket"""
        if self.socket:
            self.socket.close()


class LogExporter:
    """Unified log exporter that can send to multiple destinations"""
    
    def __init__(self):
        self.elasticsearch: Optional[ElasticsearchExporter] = None
        self.graylog: Optional[GraylogExporter] = None
        self._enabled = settings.log_export_enabled
        
        if self._enabled:
            self._initialize_exporters()
    
    def _initialize_exporters(self):
        """Initialize configured exporters"""
        export_type = settings.log_export_type
        
        if export_type == "elasticsearch" and settings.elasticsearch_url:
            self.elasticsearch = ElasticsearchExporter(
                url=settings.elasticsearch_url
            )
            logger.info(f"Elasticsearch exporter initialized: {settings.elasticsearch_url}")
        
        # Note: Graylog settings would need to be added to config
        # For now, we'll skip if not configured
    
    def create_entry(
        self,
        level: LogLevel,
        source: str,
        message: str,
        **kwargs
    ) -> LogEntry:
        """Create a log entry"""
        return LogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            level=level.value,
            source=source,
            message=message,
            **kwargs
        )
    
    async def log(
        self,
        level: LogLevel,
        source: str,
        message: str,
        **kwargs
    ):
        """Log a message to all configured destinations"""
        if not self._enabled:
            return
        
        entry = self.create_entry(level, source, message, **kwargs)
        
        if self.elasticsearch:
            await self.elasticsearch.send(entry)
        
        if self.graylog:
            self.graylog.send(entry)
    
    async def log_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        device_hostname: Optional[str] = None,
        device_ip: Optional[str] = None,
        metric_name: Optional[str] = None,
        metric_value: Optional[float] = None,
        threshold_value: Optional[float] = None
    ):
        """Log an alert event"""
        level = LogLevel.WARNING if severity == "warning" else LogLevel.CRITICAL
        
        await self.log(
            level=level,
            source="alert_engine",
            message=message,
            device_hostname=device_hostname,
            device_ip=device_ip,
            alert_type=alert_type,
            alert_severity=severity,
            metric_name=metric_name,
            metric_value=metric_value,
            threshold_value=threshold_value
        )
    
    async def log_discovery(
        self,
        event_type: str,
        device_hostname: str,
        device_ip: Optional[str] = None,
        extra: Optional[Dict] = None
    ):
        """Log a discovery event"""
        await self.log(
            level=LogLevel.INFO,
            source="discovery",
            message=f"Discovery event: {event_type} - {device_hostname}",
            device_hostname=device_hostname,
            device_ip=device_ip,
            extra=extra
        )
    
    async def close(self):
        """Close all exporters"""
        if self.elasticsearch:
            await self.elasticsearch.close()
        if self.graylog:
            self.graylog.close()


# Global exporter instance
_exporter: Optional[LogExporter] = None


def get_log_exporter() -> LogExporter:
    """Get or create the global log exporter"""
    global _exporter
    if _exporter is None:
        _exporter = LogExporter()
    return _exporter
