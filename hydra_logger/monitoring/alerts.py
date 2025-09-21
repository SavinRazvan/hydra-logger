"""
Alert Management Component for Hydra-Logger

This module provides comprehensive alert management with configurable rules,
thresholds, and notification handlers. It monitors system conditions and
generates alerts when thresholds are exceeded or conditions are met.

FEATURES:
- Configurable alert rules and thresholds
- Multiple notification handlers (console, log, email, webhook)
- Alert lifecycle management (active, acknowledged, resolved)
- Alert history and analytics
- Custom alert rule creation

USAGE:
    from hydra_logger.monitoring import AlertManager, AlertSeverity
    
    # Create alert manager
    manager = AlertManager(enabled=True)
    
    # Start monitoring
    manager.start_monitoring()
    
    # Create an alert
    alert_id = manager.create_alert(
        name="High CPU Usage",
        message="CPU usage exceeded 80%",
        severity=AlertSeverity.WARNING
    )
    
    # Acknowledge alert
    manager.acknowledge_alert(alert_id, user="admin")
    
    # Resolve alert
    manager.resolve_alert(alert_id, user="admin", resolution="Restarted service")
"""

import time
import threading
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from ..interfaces.monitor import MonitorInterface


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    EXPIRED = "expired"


class AlertManager(MonitorInterface):
    """Real alert management component for monitoring and notifications."""
    
    def __init__(self, enabled: bool = True):
        self._enabled = enabled
        self._initialized = True
        self._monitoring = False
        
        # Alert storage
        self._alerts = {}
        self._alert_history = []
        self._max_history = 1000
        
        # Alert rules and thresholds
        self._alert_rules = {}
        self._default_thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "error_rate": 5.0,
            "response_time": 1.0,
            "queue_size": 1000
        }
        
        # Notification handlers
        self._notification_handlers = {}
        self._default_handlers = {
            "console": self._console_notification,
            "log": self._log_notification,
            "email": self._email_notification,
            "webhook": self._webhook_notification
        }
        
        # Threading
        self._lock = threading.Lock()
        self._alert_thread = None
        self._stop_event = threading.Event()
        self._check_interval = 10.0  # seconds
        
        # Statistics
        self._total_alerts = 0
        self._active_alerts = 0
        self._resolved_alerts = 0
        self._last_alert_time = 0.0
    
    def start_monitoring(self) -> bool:
        """Start alert monitoring."""
        if not self._enabled or self._monitoring:
            return False
        
        try:
            with self._lock:
                self._monitoring = True
                self._stop_event.clear()
                self._alert_thread = threading.Thread(target=self._monitor_loop, daemon=True)
                self._alert_thread.start()
                return True
        except Exception:
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop alert monitoring."""
        if not self._monitoring:
            return False
        
        try:
            with self._lock:
                self._monitoring = False
                self._stop_event.set()
                
                if self._alert_thread and self._alert_thread.is_alive():
                    self._alert_thread.join(timeout=5.0)
                
                return True
        except Exception:
            return False
    
    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._monitoring
    
    def _monitor_loop(self) -> None:
        """Main alert monitoring loop."""
        while not self._stop_event.is_set():
            try:
                self._check_alert_rules()
                self._cleanup_expired_alerts()
                time.sleep(self._check_interval)
            except Exception:
                # Continue monitoring even if individual operations fail
                pass
    
    def create_alert(self, name: str, message: str, severity: AlertSeverity = AlertSeverity.WARNING,
                     source: str = "system", metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new alert.
        
        Args:
            name: Alert name
            message: Alert message
            severity: Alert severity level
            source: Alert source
            metadata: Additional alert metadata
            
        Returns:
            Alert ID
        """
        if not self._enabled:
            return ""
        
        alert_id = self._generate_alert_id()
        current_time = time.time()
        
        alert = {
            "id": alert_id,
            "name": name,
            "message": message,
            "severity": severity.value,
            "source": source,
            "status": AlertStatus.ACTIVE.value,
            "created_at": current_time,
            "updated_at": current_time,
            "acknowledged_at": None,
            "resolved_at": None,
            "metadata": metadata or {},
            "occurrence_count": 1
        }
        
        with self._lock:
            self._alerts[alert_id] = alert
            self._alert_history.append(alert.copy())
            self._total_alerts += 1
            self._active_alerts += 1
            self._last_alert_time = current_time
            
            # Keep history size manageable
            if len(self._alert_history) > self._max_history:
                self._alert_history = self._alert_history[-self._max_history:]
        
        # Send notifications
        self._send_notifications(alert)
        
        return alert_id
    
    def acknowledge_alert(self, alert_id: str, user: str = "system", 
                         comment: Optional[str] = None) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert ID to acknowledge
            user: User acknowledging the alert
            comment: Optional comment
            
        Returns:
            True if alert acknowledged successfully
        """
        if not self._enabled or alert_id not in self._alerts:
            return False
        
        with self._lock:
            alert = self._alerts[alert_id]
            if alert["status"] == AlertStatus.ACTIVE.value:
                alert["status"] = AlertStatus.ACKNOWLEDGED.value
                alert["acknowledged_at"] = time.time()
                alert["updated_at"] = time.time()
                alert["metadata"]["acknowledged_by"] = user
                if comment:
                    alert["metadata"]["acknowledgement_comment"] = comment
                
                self._active_alerts -= 1
                return True
        
        return False
    
    def resolve_alert(self, alert_id: str, user: str = "system", 
                     resolution: Optional[str] = None) -> bool:
        """
        Resolve an alert.
        
        Args:
            alert_id: Alert ID to resolve
            user: User resolving the alert
            resolution: Optional resolution description
            
        Returns:
            True if alert resolved successfully
        """
        if not self._enabled or alert_id not in self._alerts:
            return False
        
        with self._lock:
            alert = self._alerts[alert_id]
            if alert["status"] in [AlertStatus.ACTIVE.value, AlertStatus.ACKNOWLEDGED.value]:
                alert["status"] = AlertStatus.RESOLVED.value
                alert["resolved_at"] = time.time()
                alert["updated_at"] = time.time()
                alert["metadata"]["resolved_by"] = user
                if resolution:
                    alert["metadata"]["resolution"] = resolution
                
                if alert["status"] == AlertStatus.ACTIVE.value:
                    self._active_alerts -= 1
                self._resolved_alerts += 1
                return True
        
        return False
    
    def add_alert_rule(self, name: str, condition: Callable, severity: AlertSeverity = AlertSeverity.WARNING,
                       source: str = "system", cooldown: int = 300) -> bool:
        """
        Add an alert rule.
        
        Args:
            name: Rule name
            condition: Function that returns True when alert should be triggered
            severity: Alert severity
            source: Alert source
            cooldown: Cooldown period in seconds between alerts
            
        Returns:
            True if rule added successfully
        """
        try:
            self._alert_rules[name] = {
                "condition": condition,
                "severity": severity,
                "source": source,
                "cooldown": cooldown,
                "last_triggered": 0
            }
            return True
        except Exception:
            return False
    
    def remove_alert_rule(self, name: str) -> bool:
        """Remove an alert rule."""
        if name in self._alert_rules:
            del self._alert_rules[name]
            return True
        return False
    
    def set_threshold(self, metric: str, threshold: float) -> bool:
        """Set alert threshold for a metric."""
        if metric in self._default_thresholds:
            self._default_thresholds[metric] = threshold
            return True
        return False
    
    def get_threshold(self, metric: str) -> Optional[float]:
        """Get alert threshold for a metric."""
        return self._default_thresholds.get(metric)
    
    def _check_alert_rules(self) -> None:
        """Check all alert rules for conditions."""
        if not self._enabled:
            return
        
        current_time = time.time()
        
        for rule_name, rule in self._alert_rules.items():
            try:
                # Check cooldown
                if current_time - rule["last_triggered"] < rule["cooldown"]:
                    continue
                
                # Check condition
                if rule["condition"]():
                    # Create alert
                    alert_name = f"rule_{rule_name}"
                    alert_message = f"Alert rule '{rule_name}' condition met"
                    
                    self.create_alert(
                        name=alert_name,
                        message=alert_message,
                        severity=rule["severity"],
                        source=rule["source"]
                    )
                    
                    # Update last triggered time
                    rule["last_triggered"] = current_time
                    
            except Exception:
                # Continue checking other rules
                pass
    
    def _cleanup_expired_alerts(self) -> None:
        """Clean up expired alerts (older than 30 days)."""
        if not self._enabled:
            return
        
        current_time = time.time()
        cutoff_time = current_time - (30 * 24 * 3600)  # 30 days
        
        with self._lock:
            expired_alerts = []
            
            for alert_id, alert in self._alerts.items():
                if alert["created_at"] < cutoff_time:
                    expired_alerts.append(alert_id)
            
            for alert_id in expired_alerts:
                alert = self._alerts[alert_id]
                alert["status"] = AlertStatus.EXPIRED.value
                alert["updated_at"] = current_time
                
                if alert["status"] == AlertStatus.ACTIVE.value:
                    self._active_alerts -= 1
    
    def _send_notifications(self, alert: Dict[str, Any]) -> None:
        """Send notifications for an alert."""
        if not self._enabled:
            return
        
        # Send to all registered handlers
        for handler_name, handler in self._notification_handlers.items():
            try:
                handler(alert)
            except Exception:
                # Continue with other handlers
                pass
        
        # Send to default handlers based on severity
        if alert["severity"] in [AlertSeverity.ERROR.value, AlertSeverity.CRITICAL.value]:
            try:
                self._default_handlers["console"](alert)
                self._default_handlers["log"](alert)
            except Exception:
                pass
    
    def _console_notification(self, alert: Dict[str, Any]) -> None:
        """Console notification handler."""
        severity_color = {
            AlertSeverity.INFO.value: "\033[36m",      # Cyan
            AlertSeverity.WARNING.value: "\033[33m",   # Yellow
            AlertSeverity.ERROR.value: "\033[31m",     # Red
            AlertSeverity.CRITICAL.value: "\033[35m"   # Magenta
        }
        reset_color = "\033[0m"
        
        color = severity_color.get(alert["severity"], "")
        print(f"{color}[ALERT] {alert['name']}: {alert['message']}{reset_color}")
    
    def _log_notification(self, alert: Dict[str, Any]) -> None:
        """Log notification handler."""
        # In real implementation, this would use the logging system
        pass
    
    def _email_notification(self, alert: Dict[str, Any]) -> None:
        """Email notification handler."""
        # In real implementation, this would send emails
        pass
    
    def _webhook_notification(self, alert: Dict[str, Any]) -> None:
        """Webhook notification handler."""
        # In real implementation, this would send webhooks
        pass
    
    def register_notification_handler(self, name: str, handler: Callable) -> bool:
        """Register a custom notification handler."""
        try:
            self._notification_handlers[name] = handler
            return True
        except Exception:
            return False
    
    def unregister_notification_handler(self, name: str) -> bool:
        """Unregister a notification handler."""
        if name in self._notification_handlers:
            del self._notification_handlers[name]
            return True
        return False
    
    def _generate_alert_id(self) -> str:
        """Generate a unique alert ID."""
        timestamp = int(time.time() * 1000)
        return f"alert_{timestamp}_{self._total_alerts}"
    
    def get_alerts(self, status: Optional[AlertStatus] = None, 
                   severity: Optional[AlertSeverity] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get alerts with optional filtering.
        
        Args:
            status: Filter by alert status
            severity: Filter by alert severity
            limit: Maximum number of alerts to return
            
        Returns:
            List of matching alerts
        """
        with self._lock:
            alerts = list(self._alerts.values())
            
            # Apply filters
            if status:
                alerts = [a for a in alerts if a["status"] == status.value]
            
            if severity:
                alerts = [a for a in alerts if a["severity"] == severity.value]
            
            # Sort by creation time (newest first)
            alerts.sort(key=lambda x: x["created_at"], reverse=True)
            
            return alerts[:limit] if limit > 0 else alerts
    
    def get_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific alert by ID."""
        return self._alerts.get(alert_id)
    
    def get_alert_history(self, days: int = 7, limit: int = 100) -> List[Dict[str, Any]]:
        """Get alert history for specified number of days."""
        cutoff_time = time.time() - (days * 24 * 3600)
        
        with self._lock:
            recent_alerts = [
                alert for alert in self._alert_history
                if alert["created_at"] > cutoff_time
            ]
            
            # Sort by creation time (newest first)
            recent_alerts.sort(key=lambda x: x["created_at"], reverse=True)
            
            return recent_alerts[:limit] if limit > 0 else recent_alerts
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics."""
        with self._lock:
            severity_counts = {}
            status_counts = {}
            
            for alert in self._alerts.values():
                severity_counts[alert["severity"]] = severity_counts.get(alert["severity"], 0) + 1
                status_counts[alert["status"]] = status_counts.get(alert["status"], 0) + 1
            
            return {
                "total_alerts": self._total_alerts,
                "active_alerts": self._active_alerts,
                "resolved_alerts": self._resolved_alerts,
                "severity_distribution": severity_counts,
                "status_distribution": status_counts,
                "last_alert_time": self._last_alert_time,
                "total_rules": len(self._alert_rules),
                "monitoring": self._monitoring,
                "enabled": self._enabled
            }
    
    def reset_stats(self) -> None:
        """Reset alert statistics."""
        with self._lock:
            self._total_alerts = 0
            self._active_alerts = 0
            self._resolved_alerts = 0
            self._last_alert_time = 0.0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current alert metrics."""
        return self.get_alert_stats()
    
    def reset_metrics(self) -> None:
        """Reset alert metrics."""
        self.reset_stats()
    
    def is_healthy(self) -> bool:
        """Check if alert system is healthy."""
        return self._active_alerts < 100  # Consider healthy if less than 100 active alerts
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get alert system health status."""
        return {
            "healthy": self.is_healthy(),
            "active_alerts": self._active_alerts,
            "total_alerts": self._total_alerts,
            "monitoring": self._monitoring,
            "enabled": self._enabled
        }
