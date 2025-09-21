"""
Audit Logging Component for Hydra-Logger

This module provides comprehensive audit logging with event tracking,
security monitoring, and compliance reporting. It supports multiple
event types, severity levels, and export formats for regulatory compliance.

FEATURES:
- Comprehensive audit event logging
- Security event tracking and monitoring
- Access control event logging
- Data operation auditing
- Configuration change tracking
- Event search and filtering
- Multiple export formats (JSON, CSV)
- Configurable retention policies

EVENT TYPES:
- Security: Security-related events
- Access: Access control events
- Data: Data operation events
- Configuration: Configuration changes

USAGE:
    from hydra_logger.security import AuditLogger
    
    # Create audit logger
    audit = AuditLogger(enabled=True, retention_days=2555)
    
    # Log security event
    event_id = audit.log_security_event(
        user="admin",
        action="login",
        resource="system",
        threat_level="low"
    )
    
    # Log access event
    audit.log_access_event(
        user="user1",
        action="read",
        resource="logs",
        granted=True
    )
    
    # Search audit events
    events = audit.search_audit_events(
        filters={"user": "admin", "severity": "critical"}
    )
    
    # Export audit trail
    audit_data = audit.export_audit_trail(format="json")
"""

import json
import time
from typing import Any, Dict, List, Optional, Union
from ..interfaces.security import SecurityInterface


class AuditLogger(SecurityInterface):
    """Real audit logging component for security and compliance tracking."""
    
    def __init__(self, enabled: bool = True, retention_days: int = 2555):
        self._enabled = enabled
        self._initialized = True
        self._audit_events = []
        self._retention_days = retention_days
        self._event_count = 0
        self._critical_events = 0
        self._warning_events = 0
        self._info_events = 0
    
    def log_audit_event(self, event_type: str, user: str, action: str, 
                        resource: str, details: Optional[Dict[str, Any]] = None,
                        severity: str = "info", ip_address: Optional[str] = None) -> str:
        """
        Log an audit event.
        
        Args:
            event_type: Type of audit event
            user: User performing the action
            action: Action being performed
            resource: Resource being accessed/modified
            details: Additional event details
            severity: Event severity (critical, warning, info)
            ip_address: IP address of the user
            
        Returns:
            Event ID for reference
        """
        if not self._enabled:
            return ""
        
        event_id = self._generate_event_id()
        timestamp = time.time()
        
        audit_event = {
            "event_id": event_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "user": user,
            "action": action,
            "resource": resource,
            "severity": severity,
            "ip_address": ip_address or "127.0.0.1",
            "details": details or {},
            "session_id": self._get_session_id(user),
            "user_agent": "Hydra-Logger"  # In real implementation, get from context
        }
        
        self._audit_events.append(audit_event)
        self._event_count += 1
        
        # Track severity counts
        if severity == "critical":
            self._critical_events += 1
        elif severity == "warning":
            self._warning_events += 1
        else:
            self._info_events += 1
        
        # Cleanup old events based on retention policy
        self._cleanup_old_events()
        
        return event_id
    
    def log_security_event(self, user: str, action: str, resource: str, 
                          threat_level: str = "medium", details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a security-related audit event.
        
        Args:
            user: User involved in the security event
            action: Security action or event
            resource: Resource involved
            threat_level: Threat level (low, medium, high, critical)
            details: Additional security details
            
        Returns:
            Event ID for reference
        """
        severity = "critical" if threat_level in ["high", "critical"] else "warning"
        return self.log_audit_event(
            event_type="security",
            user=user,
            action=action,
            resource=resource,
            details=details,
            severity=severity
        )
    
    def log_access_event(self, user: str, action: str, resource: str, 
                        granted: bool, details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log an access control event.
        
        Args:
            user: User attempting access
            action: Access action (read, write, delete, admin)
            resource: Resource being accessed
            granted: Whether access was granted
            details: Additional access details
            
        Returns:
            Event ID for reference
        """
        event_type = "access_granted" if granted else "access_denied"
        severity = "warning" if not granted else "info"
        
        access_details = details or {}
        access_details["access_granted"] = granted
        
        return self.log_audit_event(
            event_type=event_type,
            user=user,
            action=action,
            resource=resource,
            details=access_details,
            severity=severity
        )
    
    def log_data_event(self, user: str, action: str, resource: str, 
                      data_type: str, record_count: int = 1, 
                      details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a data-related audit event.
        
        Args:
            user: User performing the data operation
            action: Data action (create, read, update, delete, export)
            resource: Data resource or table
            data_type: Type of data being accessed
            record_count: Number of records affected
            details: Additional data operation details
            
        Returns:
            Event ID for reference
        """
        data_details = details or {}
        data_details.update({
            "data_type": data_type,
            "record_count": record_count,
            "operation_timestamp": time.time()
        })
        
        severity = "info"
        if action in ["delete", "export"]:
            severity = "warning"
        elif action in ["admin", "bulk_delete"]:
            severity = "critical"
        
        return self.log_audit_event(
            event_type="data_operation",
            user=user,
            action=action,
            resource=resource,
            details=data_details,
            severity=severity
        )
    
    def log_configuration_event(self, user: str, action: str, resource: str,
                               old_value: Optional[Any] = None, new_value: Optional[Any] = None,
                               details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a configuration change audit event.
        
        Args:
            user: User making the configuration change
            action: Configuration action (create, update, delete)
            resource: Configuration resource being changed
            old_value: Previous configuration value
            new_value: New configuration value
            details: Additional configuration details
            
        Returns:
            Event ID for reference
        """
        config_details = details or {}
        if old_value is not None:
            config_details["old_value"] = str(old_value)
        if new_value is not None:
            config_details["new_value"] = str(new_value)
        
        severity = "warning" if action in ["delete", "update"] else "info"
        
        return self.log_audit_event(
            event_type="configuration_change",
            user=user,
            action=action,
            resource=resource,
            details=config_details,
            severity=severity
        )
    
    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        timestamp = int(time.time() * 1000)
        return f"audit_{timestamp}_{self._event_count}"
    
    def _get_session_id(self, user: str) -> str:
        """Get or generate a session ID for the user."""
        # In real implementation, this would track actual user sessions
        return f"session_{user}_{int(time.time() / 3600)}"  # Hour-based session
    
    def _cleanup_old_events(self) -> None:
        """Remove audit events older than retention period."""
        if not self._retention_days:
            return
        
        cutoff_time = time.time() - (self._retention_days * 24 * 3600)
        self._audit_events = [
            event for event in self._audit_events
            if event["timestamp"] > cutoff_time
        ]
    
    def search_audit_events(self, filters: Optional[Dict[str, Any]] = None, 
                           limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search audit events based on filters.
        
        Args:
            filters: Dictionary of filters to apply
            limit: Maximum number of events to return
            
        Returns:
            List of matching audit events
        """
        if not filters:
            return self._audit_events[-limit:] if limit > 0 else self._audit_events
        
        filtered_events = []
        for event in self._audit_events:
            if self._event_matches_filters(event, filters):
                filtered_events.append(event)
                if len(filtered_events) >= limit:
                    break
        
        return filtered_events
    
    def _event_matches_filters(self, event: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if an event matches the given filters."""
        for key, value in filters.items():
            if key not in event:
                return False
            
            if isinstance(value, (list, tuple)):
                if event[key] not in value:
                    return False
            elif event[key] != value:
                return False
        
        return True
    
    def get_audit_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get audit summary for the specified number of days.
        
        Args:
            days: Number of days to summarize
            
        Returns:
            Audit summary statistics
        """
        cutoff_time = time.time() - (days * 24 * 3600)
        recent_events = [
            event for event in self._audit_events
            if event["timestamp"] > cutoff_time
        ]
        
        event_types = {}
        users = {}
        resources = {}
        severity_counts = {"critical": 0, "warning": 0, "info": 0}
        
        for event in recent_events:
            # Count event types
            event_types[event["event_type"]] = event_types.get(event["event_type"], 0) + 1
            
            # Count users
            users[event["user"]] = users.get(event["user"], 0) + 1
            
            # Count resources
            resources[event["resource"]] = resources.get(event["resource"], 0) + 1
            
            # Count severities
            severity_counts[event["severity"]] += 1
        
        return {
            "period_days": days,
            "total_events": len(recent_events),
            "event_types": event_types,
            "active_users": len(users),
            "top_users": sorted(users.items(), key=lambda x: x[1], reverse=True)[:10],
            "top_resources": sorted(resources.items(), key=lambda x: x[1], reverse=True)[:10],
            "severity_distribution": severity_counts,
            "generated_at": time.time()
        }
    
    def export_audit_trail(self, format: str = "json", filters: Optional[Dict[str, Any]] = None) -> str:
        """
        Export audit trail in specified format.
        
        Args:
            format: Export format (json, csv)
            filters: Filters to apply to exported data
            
        Returns:
            Exported audit trail as string
        """
        events = self.search_audit_events(filters, limit=0)  # No limit for export
        
        if format.lower() == "json":
            return json.dumps(events, indent=2, default=str)
        elif format.lower() == "csv":
            return self._export_to_csv(events)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_to_csv(self, events: List[Dict[str, Any]]) -> str:
        """Export events to CSV format."""
        if not events:
            return ""
        
        headers = list(events[0].keys())
        csv_lines = [",".join(headers)]
        
        for event in events:
            row = []
            for header in headers:
                value = event.get(header, "")
                # Escape commas and quotes in CSV
                if isinstance(value, str) and ("," in value or '"' in value):
                    value = '"' + value.replace('"', '""') + '"'
                row.append(str(value))
            csv_lines.append(",".join(row))
        
        return "\n".join(csv_lines)
    
    def get_audit_stats(self) -> Dict[str, Any]:
        """Get audit logging statistics."""
        return {
            "total_events": self._event_count,
            "critical_events": self._critical_events,
            "warning_events": self._warning_events,
            "info_events": self._info_events,
            "retention_days": self._retention_days,
            "current_events": len(self._audit_events),
            "enabled": self._enabled
        }
    
    def reset_stats(self) -> None:
        """Reset audit statistics."""
        self._event_count = 0
        self._critical_events = 0
        self._warning_events = 0
        self._info_events = 0
    
    def set_retention_policy(self, days: int) -> bool:
        """Set audit event retention policy."""
        if days < 0:
            return False
        
        self._retention_days = days
        self._cleanup_old_events()
        return True
    
    # SecurityInterface implementation
    def is_enabled(self) -> bool:
        return self._enabled
    
    def enable(self) -> None:
        self._enabled = True
    
    def disable(self) -> None:
        self._enabled = False
    
    def get_security_level(self) -> str:
        return "high" if self._enabled else "disabled"
    
    def get_threat_count(self) -> int:
        return self._critical_events + self._warning_events
    
    def get_security_stats(self) -> Dict[str, Any]:
        return self.get_audit_stats()
    
    def reset_security_stats(self) -> None:
        self.reset_stats()
    
    def is_secure(self) -> bool:
        return self._enabled and self._initialized
