"""
Access Control Component for Hydra-Logger

This module provides comprehensive role-based access control (RBAC) with
user management, permission tracking, and audit logging. It supports
multiple roles, resource-based permissions, and access attempt monitoring.

FEATURES:
- Role-based access control (RBAC)
- User role management and assignment
- Resource-based permission system
- Access attempt logging and monitoring
- Configurable role hierarchies
- Permission granting and revocation
- Access statistics and analytics

ROLES:
- Admin: Full system access
- Manager: Management level access
- User: Standard user access
- Readonly: Read-only access
- Guest: Limited guest access

USAGE:
    from hydra_logger.security import AccessController
    
    # Create access controller
    controller = AccessController(enabled=True)
    
    # Add user roles
    controller.add_user_role("user1", "admin")
    controller.add_user_role("user2", "user")
    
    # Check access permissions
    if controller.check_access("user1", "logs", "write"):
        # User has write access to logs
        pass
    
    # Get access statistics
    stats = controller.get_access_stats()
    print(f"Total access checks: {stats['total_checks']}")
"""

import time
from typing import Any, Dict, List, Optional, Set
from ..interfaces.security import SecurityInterface


class AccessController(SecurityInterface):
    """Real access control component with Role-Based Access Control (RBAC)."""
    
    def __init__(self, enabled: bool = True):
        self._enabled = enabled
        self._initialized = True
        self._access_checks = 0
        self._access_denied = 0
        self._roles = self._initialize_default_roles()
        self._permissions = self._initialize_permissions()
        self._user_roles = {}
        self._access_log = []
    
    def _initialize_default_roles(self) -> Dict[str, Dict[str, Any]]:
        """Initialize default roles."""
        return {
            "admin": {
                "description": "Full system access",
                "level": 100,
                "created": time.time()
            },
            "manager": {
                "description": "Management level access",
                "level": 80,
                "created": time.time()
            },
            "user": {
                "description": "Standard user access",
                "level": 50,
                "created": time.time()
            },
            "readonly": {
                "description": "Read-only access",
                "level": 20,
                "created": time.time()
            },
            "guest": {
                "description": "Limited guest access",
                "level": 10,
                "created": time.time()
            }
        }
    
    def _initialize_permissions(self) -> Dict[str, Dict[str, Any]]:
        """Initialize default permissions."""
        return {
            "logs": {
                "read": ["admin", "manager", "user", "readonly"],
                "write": ["admin", "manager", "user"],
                "delete": ["admin", "manager"],
                "admin": ["admin"]
            },
            "security": {
                "read": ["admin", "manager"],
                "write": ["admin"],
                "delete": ["admin"],
                "admin": ["admin"]
            },
            "configuration": {
                "read": ["admin", "manager"],
                "write": ["admin"],
                "delete": ["admin"],
                "admin": ["admin"]
            },
            "monitoring": {
                "read": ["admin", "manager", "user"],
                "write": ["admin", "manager"],
                "delete": ["admin"],
                "admin": ["admin"]
            }
        }
    
    def check_access(self, user: str, resource: str, action: str) -> bool:
        """
        Check if user has access to perform action on resource.
        
        Args:
            user: User identifier
            resource: Resource to access
            action: Action to perform
            
        Returns:
            True if access granted, False otherwise
        """
        if not self._enabled:
            return True
        
        self._access_checks += 1
        timestamp = time.time()
        
        # Get user roles
        user_roles = self._user_roles.get(user, ["guest"])
        
        # Check if any role has permission
        has_access = False
        for role in user_roles:
            if self._has_permission(role, resource, action):
                has_access = True
                break
        
        # Log access attempt
        self._log_access_attempt(user, resource, action, has_access, timestamp)
        
        if not has_access:
            self._access_denied += 1
        
        return has_access
    
    def _has_permission(self, role: str, resource: str, action: str) -> bool:
        """Check if role has permission for resource and action."""
        if role not in self._roles:
            return False
        
        if resource not in self._permissions:
            return False
        
        if action not in self._permissions[resource]:
            return False
        
        return role in self._permissions[resource][action]
    
    def _log_access_attempt(self, user: str, resource: str, action: str, granted: bool, timestamp: float):
        """Log access attempt for audit purposes."""
        log_entry = {
            "timestamp": timestamp,
            "user": user,
            "resource": resource,
            "action": action,
            "granted": granted,
            "ip_address": "127.0.0.1"  # In real implementation, get from context
        }
        self._access_log.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self._access_log) > 1000:
            self._access_log = self._access_log[-1000:]
    
    def add_user_role(self, user: str, role: str) -> bool:
        """
        Add role to user.
        
        Args:
            user: User identifier
            role: Role to add
            
        Returns:
            True if role added successfully
        """
        if role not in self._roles:
            return False
        
        if user not in self._user_roles:
            self._user_roles[user] = []
        
        if role not in self._user_roles[user]:
            self._user_roles[user].append(role)
        
        return True
    
    def remove_user_role(self, user: str, role: str) -> bool:
        """
        Remove role from user.
        
        Args:
            user: User identifier
            role: Role to remove
            
        Returns:
            True if role removed successfully
        """
        if user in self._user_roles and role in self._user_roles[user]:
            self._user_roles[user].remove(role)
            return True
        return False
    
    def get_user_roles(self, user: str) -> List[str]:
        """Get all roles for a user."""
        return self._user_roles.get(user, [])
    
    def create_role(self, name: str, description: str, level: int) -> bool:
        """
        Create a new role.
        
        Args:
            name: Role name
            description: Role description
            level: Role level (higher = more privileges)
            
        Returns:
            True if role created successfully
        """
        if name in self._roles:
            return False
        
        self._roles[name] = {
            "description": description,
            "level": level,
            "created": time.time()
        }
        return True
    
    def delete_role(self, name: str) -> bool:
        """
        Delete a role.
        
        Args:
            name: Role name to delete
            
        Returns:
            True if role deleted successfully
        """
        if name in ["admin", "guest"]:  # Protect critical roles
            return False
        
        if name in self._roles:
            del self._roles[name]
            
            # Remove role from all users
            for user_roles in self._user_roles.values():
                if name in user_roles:
                    user_roles.remove(name)
            
            # Remove role from permissions
            for resource_perms in self._permissions.values():
                for action_roles in resource_perms.values():
                    if name in action_roles:
                        action_roles.remove(name)
            
            return True
        return False
    
    def grant_permission(self, role: str, resource: str, action: str) -> bool:
        """
        Grant permission to a role.
        
        Args:
            role: Role to grant permission to
            resource: Resource to grant access to
            action: Action to grant permission for
            
        Returns:
            True if permission granted successfully
        """
        if role not in self._roles:
            return False
        
        if resource not in self._permissions:
            self._permissions[resource] = {}
        
        if action not in self._permissions[resource]:
            self._permissions[resource][action] = []
        
        if role not in self._permissions[resource][action]:
            self._permissions[resource][action].append(role)
        
        return True
    
    def revoke_permission(self, role: str, resource: str, action: str) -> bool:
        """
        Revoke permission from a role.
        
        Args:
            role: Role to revoke permission from
            resource: Resource to revoke access to
            action: Action to revoke permission for
            
        Returns:
            True if permission revoked successfully
        """
        if (resource in self._permissions and 
            action in self._permissions[resource] and 
            role in self._permissions[resource][action]):
            self._permissions[resource][action].remove(role)
            return True
        return False
    
    def get_access_stats(self) -> Dict[str, Any]:
        """Get access control statistics."""
        return {
            "total_checks": self._access_checks,
            "access_denied": self._access_denied,
            "access_granted": self._access_checks - self._access_denied,
            "total_users": len(self._user_roles),
            "total_roles": len(self._roles),
            "total_resources": len(self._permissions),
            "enabled": self._enabled
        }
    
    def get_access_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent access log entries."""
        return self._access_log[-limit:] if limit > 0 else self._access_log
    
    def reset_stats(self) -> None:
        """Reset access control statistics."""
        self._access_checks = 0
        self._access_denied = 0
        self._access_log = []
    
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
        return self._access_denied
    
    def get_security_stats(self) -> Dict[str, Any]:
        return self.get_access_stats()
    
    def reset_security_stats(self) -> None:
        self.reset_stats()
    
    def is_secure(self) -> bool:
        return self._enabled and self._initialized
