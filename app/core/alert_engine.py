"""
Alert Engine - Handles threshold checking, alert state machine, and recovery logic
"""
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.device import Device
from app.models.link import MergedLink
from app.models.alert import Alert, AlertHistory, AlertProfile

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    """Types of alerts"""
    DEVICE_OFFLINE = "device_offline"
    DEVICE_ONLINE = "device_online"  # Recovery
    LINK_HIGH_UTILIZATION = "link_high_utilization"
    LINK_UTILIZATION_NORMAL = "link_utilization_normal"  # Recovery
    CPU_HIGH = "cpu_high"
    CPU_NORMAL = "cpu_normal"  # Recovery
    MEMORY_HIGH = "memory_high"
    MEMORY_NORMAL = "memory_normal"  # Recovery
    NEW_DEVICE_DISCOVERED = "new_device_discovered"
    NEW_LINK_DISCOVERED = "new_link_discovered"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ThresholdConfig:
    """Threshold configuration for a metric"""
    warning: float
    critical: float
    recovery_buffer: float = 10.0  # Hysteresis for recovery


@dataclass
class AlertEvent:
    """Represents an alert event to be processed"""
    alert_type: AlertType
    severity: AlertSeverity
    device_id: Optional[int] = None
    link_id: Optional[int] = None
    current_value: Optional[float] = None
    threshold_value: Optional[float] = None
    message: str = ""


class AlertEngine:
    """
    Alert engine with state machine for hysteresis
    
    Alert Lifecycle:
    1. TRIGGERED - First time threshold exceeded
    2. ACTIVE - Still exceeding threshold
    3. RECOVERING - Below threshold but within buffer
    4. RESOLVED - Below recovery threshold, alert closed
    """
    
    # Default thresholds (used when no profile assigned)
    DEFAULT_THRESHOLDS = {
        "link_utilization": ThresholdConfig(warning=70, critical=90, recovery_buffer=10),
        "cpu": ThresholdConfig(warning=80, critical=95, recovery_buffer=10),
        "memory": ThresholdConfig(warning=85, critical=95, recovery_buffer=10),
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._profile_cache: Dict[int, Dict] = {}
    
    async def get_device_thresholds(self, device: Device) -> Dict[str, ThresholdConfig]:
        """Get thresholds for a device based on its profile"""
        if device.alert_profile_id:
            if device.alert_profile_id in self._profile_cache:
                return self._profile_cache[device.alert_profile_id]
            
            result = await self.db.execute(
                select(AlertProfile).where(AlertProfile.id == device.alert_profile_id)
            )
            profile = result.scalar_one_or_none()
            
            if profile and profile.thresholds:
                thresholds = {}
                for key, values in profile.thresholds.items():
                    if isinstance(values, dict):
                        thresholds[key] = ThresholdConfig(
                            warning=values.get("warning", 70),
                            critical=values.get("critical", 90),
                            recovery_buffer=values.get("recovery_buffer", 10)
                        )
                self._profile_cache[device.alert_profile_id] = thresholds
                return thresholds
        
        return self.DEFAULT_THRESHOLDS
    
    async def check_device_status(self, device: Device) -> List[AlertEvent]:
        """Check device online/offline status"""
        events = []
        
        # Device offline detection
        if device.status == "offline":
            # Check if there's already an active offline alert
            existing = await self._get_active_alert(
                device_id=device.id,
                alert_type=AlertType.DEVICE_OFFLINE
            )
            
            if not existing:
                events.append(AlertEvent(
                    alert_type=AlertType.DEVICE_OFFLINE,
                    severity=AlertSeverity.CRITICAL,
                    device_id=device.id,
                    message=f"Device {device.hostname} is offline"
                ))
        
        elif device.status == "managed":
            # Check if there's an offline alert to resolve
            existing = await self._get_active_alert(
                device_id=device.id,
                alert_type=AlertType.DEVICE_OFFLINE
            )
            
            if existing:
                events.append(AlertEvent(
                    alert_type=AlertType.DEVICE_ONLINE,
                    severity=AlertSeverity.INFO,
                    device_id=device.id,
                    message=f"Device {device.hostname} is back online"
                ))
        
        return events
    
    async def check_device_metrics(self, device: Device) -> List[AlertEvent]:
        """Check CPU and memory thresholds"""
        events = []
        thresholds = await self.get_device_thresholds(device)
        
        # CPU check
        if device.cpu_percent is not None:
            cpu_thresh = thresholds.get("cpu", self.DEFAULT_THRESHOLDS["cpu"])
            cpu_events = await self._check_metric(
                device_id=device.id,
                metric_name="cpu",
                current_value=device.cpu_percent,
                threshold=cpu_thresh,
                alert_type_high=AlertType.CPU_HIGH,
                alert_type_normal=AlertType.CPU_NORMAL,
                device_name=device.hostname
            )
            events.extend(cpu_events)
        
        # Memory check
        if device.memory_percent is not None:
            mem_thresh = thresholds.get("memory", self.DEFAULT_THRESHOLDS["memory"])
            mem_events = await self._check_metric(
                device_id=device.id,
                metric_name="memory",
                current_value=device.memory_percent,
                threshold=mem_thresh,
                alert_type_high=AlertType.MEMORY_HIGH,
                alert_type_normal=AlertType.MEMORY_NORMAL,
                device_name=device.hostname
            )
            events.extend(mem_events)
        
        return events
    
    async def check_link_utilization(self, link: MergedLink) -> List[AlertEvent]:
        """Check link utilization thresholds"""
        events = []
        
        # Get device for thresholds (use device_a)
        device = await self._get_device(link.device_a_id)
        if not device:
            return events
        
        thresholds = await self.get_device_thresholds(device)
        link_thresh = thresholds.get("link_utilization", self.DEFAULT_THRESHOLDS["link_utilization"])
        
        # Use max of in/out utilization
        max_util = max(
            link.utilization_in_percent or 0,
            link.utilization_out_percent or 0
        )
        
        # Check threshold
        link_events = await self._check_metric(
            link_id=link.id,
            metric_name="link_utilization",
            current_value=max_util,
            threshold=link_thresh,
            alert_type_high=AlertType.LINK_HIGH_UTILIZATION,
            alert_type_normal=AlertType.LINK_UTILIZATION_NORMAL,
            device_name=f"Link {link.device_a_id} <-> {link.device_b_id}"
        )
        events.extend(link_events)
        
        return events
    
    async def _check_metric(
        self,
        metric_name: str,
        current_value: float,
        threshold: ThresholdConfig,
        alert_type_high: AlertType,
        alert_type_normal: AlertType,
        device_name: str,
        device_id: Optional[int] = None,
        link_id: Optional[int] = None
    ) -> List[AlertEvent]:
        """Generic metric threshold checking with hysteresis"""
        events = []
        
        # Get existing active alert
        existing = await self._get_active_alert(
            device_id=device_id,
            link_id=link_id,
            alert_type=alert_type_high
        )
        
        if current_value >= threshold.critical:
            if not existing:
                events.append(AlertEvent(
                    alert_type=alert_type_high,
                    severity=AlertSeverity.CRITICAL,
                    device_id=device_id,
                    link_id=link_id,
                    current_value=current_value,
                    threshold_value=threshold.critical,
                    message=f"{device_name} {metric_name} critical: {current_value:.1f}% (threshold: {threshold.critical}%)"
                ))
            elif existing.severity != AlertSeverity.CRITICAL.value:
                # Escalate to critical
                existing.severity = AlertSeverity.CRITICAL.value
                existing.current_value = current_value
                existing.threshold_value = threshold.critical
                existing.message = f"{device_name} {metric_name} critical: {current_value:.1f}%"
                
        elif current_value >= threshold.warning:
            if not existing:
                events.append(AlertEvent(
                    alert_type=alert_type_high,
                    severity=AlertSeverity.WARNING,
                    device_id=device_id,
                    link_id=link_id,
                    current_value=current_value,
                    threshold_value=threshold.warning,
                    message=f"{device_name} {metric_name} warning: {current_value:.1f}% (threshold: {threshold.warning}%)"
                ))
                
        elif existing:
            # Check recovery with hysteresis
            recovery_threshold = threshold.warning - threshold.recovery_buffer
            if current_value < recovery_threshold:
                events.append(AlertEvent(
                    alert_type=alert_type_normal,
                    severity=AlertSeverity.INFO,
                    device_id=device_id,
                    link_id=link_id,
                    current_value=current_value,
                    message=f"{device_name} {metric_name} recovered: {current_value:.1f}%"
                ))
        
        return events
    
    async def process_events(self, events: List[AlertEvent]):
        """Process alert events - create new alerts or resolve existing ones"""
        for event in events:
            if event.alert_type.value.endswith("_normal") or event.alert_type == AlertType.DEVICE_ONLINE:
                # Recovery event - resolve existing alert
                await self._resolve_alert(event)
            else:
                # New or ongoing alert
                await self._create_or_update_alert(event)
        
        await self.db.commit()
    
    async def _create_or_update_alert(self, event: AlertEvent):
        """Create new alert or update existing one"""
        # Check for existing
        base_type = event.alert_type.value.replace("_normal", "")
        existing = await self._get_active_alert(
            device_id=event.device_id,
            link_id=event.link_id,
            alert_type=AlertType(base_type) if base_type != event.alert_type.value else event.alert_type
        )
        
        if existing:
            # Update existing alert
            existing.current_value = event.current_value
            existing.severity = event.severity.value
            existing.message = event.message
            
            # Add to history
            history = AlertHistory(
                alert_id=existing.id,
                event_type="updated",
                details={"value": event.current_value, "severity": event.severity.value}
            )
            self.db.add(history)
        else:
            # Create new alert
            alert = Alert(
                device_id=event.device_id,
                link_id=event.link_id,
                alert_type=event.alert_type.value,
                severity=event.severity.value,
                message=event.message,
                current_value=event.current_value,
                threshold_value=event.threshold_value,
                is_active=True
            )
            self.db.add(alert)
            await self.db.flush()
            
            # Add to history
            history = AlertHistory(
                alert_id=alert.id,
                event_type="triggered",
                details={"value": event.current_value, "threshold": event.threshold_value}
            )
            self.db.add(history)
            
            logger.info(f"New alert: {event.alert_type.value} - {event.message}")
    
    async def _resolve_alert(self, event: AlertEvent):
        """Resolve an existing alert"""
        # Find the corresponding high alert type
        high_type = event.alert_type.value.replace("_normal", "_high")
        if event.alert_type == AlertType.DEVICE_ONLINE:
            high_type = AlertType.DEVICE_OFFLINE.value
        
        existing = await self._get_active_alert(
            device_id=event.device_id,
            link_id=event.link_id,
            alert_type=AlertType(high_type)
        )
        
        if existing:
            existing.is_active = False
            existing.recovered_at = datetime.utcnow()
            
            # Add to history
            history = AlertHistory(
                alert_id=existing.id,
                event_type="recovered",
                details={"value": event.current_value}
            )
            self.db.add(history)
            
            logger.info(f"Alert resolved: {event.message}")
    
    async def _get_active_alert(
        self,
        device_id: Optional[int] = None,
        link_id: Optional[int] = None,
        alert_type: Optional[AlertType] = None
    ) -> Optional[Alert]:
        """Get active alert matching criteria"""
        conditions = [Alert.is_active == True]
        
        if device_id:
            conditions.append(Alert.device_id == device_id)
        if link_id:
            conditions.append(Alert.link_id == link_id)
        if alert_type:
            conditions.append(Alert.alert_type == alert_type.value)
        
        result = await self.db.execute(
            select(Alert).where(and_(*conditions))
        )
        return result.scalar_one_or_none()
    
    async def _get_device(self, device_id: int) -> Optional[Device]:
        """Get device by ID"""
        result = await self.db.execute(
            select(Device).where(Device.id == device_id)
        )
        return result.scalar_one_or_none()
    
    async def run_check_cycle(self):
        """Run a complete alert check cycle for all devices and links"""
        all_events = []
        
        # Check all devices
        devices_result = await self.db.execute(select(Device))
        devices = devices_result.scalars().all()
        
        for device in devices:
            events = await self.check_device_status(device)
            all_events.extend(events)
            
            events = await self.check_device_metrics(device)
            all_events.extend(events)
        
        # Check all links
        links_result = await self.db.execute(select(MergedLink))
        links = links_result.scalars().all()
        
        for link in links:
            events = await self.check_link_utilization(link)
            all_events.extend(events)
        
        # Process all events
        await self.process_events(all_events)
        
        logger.info(f"Alert check cycle completed: {len(all_events)} events processed")
