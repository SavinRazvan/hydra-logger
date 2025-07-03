"""
Utility Functions Module

Common utility functions used across the application.
"""

import hashlib
import json
import time
from typing import Dict, Any, Optional

class Utils:
    """Utility functions for the application."""
    def __init__(self, logger):
        self.logger = logger
        self.logger.info("UTILS", "Utils initialized")
    def generate_user_id(self, username: str, email: str) -> str:
        self.logger.debug("UTILS", f"Generating user ID for: {username}")
        try:
            data = f"{username}:{email}:{time.time()}"
            user_id = hashlib.md5(data.encode()).hexdigest()[:8]
            self.logger.debug("UTILS", f"Generated user ID: {user_id} for user: {username}")
            return user_id
        except Exception as e:
            self.logger.error("UTILS", f"Error generating user ID for {username}: {str(e)}")
            raise
    def validate_email(self, email: str) -> bool:
        self.logger.debug("UTILS", f"Validating email: {email}")
        try:
            if '@' in email and '.' in email.split('@')[1]:
                self.logger.debug("UTILS", f"Email validation passed: {email}")
                return True
            else:
                self.logger.warning("UTILS", f"Email validation failed: {email}")
                return False
        except Exception as e:
            self.logger.error("UTILS", f"Error validating email {email}: {str(e)}")
            return False
    def format_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.debug("UTILS", "Formatting user data")
        try:
            formatted_data = {
                "id": user_data.get("id"),
                "username": user_data.get("username", "").lower(),
                "email": user_data.get("email", "").lower(),
                "created_at": user_data.get("created_at", time.time()),
                "updated_at": time.time()
            }
            self.logger.debug("UTILS", f"User data formatted successfully for user ID: {formatted_data.get('id')}")
            return formatted_data
        except Exception as e:
            self.logger.error("UTILS", f"Error formatting user data: {str(e)}")
            raise
    def create_audit_log(self, action: str, user_id: int, details: Dict = None) -> Dict:
        self.logger.info("UTILS", f"Creating audit log for action: {action}, user ID: {user_id}")
        try:
            audit_entry = {
                "timestamp": time.time(),
                "action": action,
                "user_id": user_id,
                "details": details or {},
                "session_id": f"session_{int(time.time())}"
            }
            self.logger.info("UTILS", f"Audit log created successfully for action: {action}")
            return audit_entry
        except Exception as e:
            self.logger.error("UTILS", f"Error creating audit log for action {action}: {str(e)}")
            raise
    def encrypt_sensitive_data(self, data: str) -> str:
        self.logger.debug("UTILS", "Encrypting sensitive data")
        try:
            encrypted = hashlib.sha256(data.encode()).hexdigest()
            self.logger.debug("UTILS", "Sensitive data encrypted successfully")
            return encrypted
        except Exception as e:
            self.logger.error("UTILS", f"Error encrypting sensitive data: {str(e)}")
            raise 