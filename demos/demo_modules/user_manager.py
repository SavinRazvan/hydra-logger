"""
User Management Module

Handles user operations like creation, authentication, and profile management.
"""

import time
import random
from typing import Dict, Optional

class UserManager:
    """Manages user operations and authentication."""
    def __init__(self, logger):
        self.logger = logger
        self.users = {}
        self.logger.info("USER_MANAGER", "UserManager initialized")
    def create_user(self, username: str, email: str) -> Dict:
        """Create a new user account."""
        self.logger.info("USER_MANAGER", f"Creating user: {username} ({email})")
        try:
            time.sleep(0.1)
            user_id = random.randint(1000, 9999)
            user = {
                "id": user_id,
                "username": username,
                "email": email,
                "created_at": time.time()
            }
            self.users[user_id] = user
            self.logger.info("USER_MANAGER", f"User created successfully: ID {user_id}")
            return user
        except Exception as e:
            self.logger.error("USER_MANAGER", f"Failed to create user {username}: {str(e)}")
            raise
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate a user."""
        self.logger.info("USER_MANAGER", f"Authenticating user: {username}")
        try:
            time.sleep(0.05)
            user = next((u for u in self.users.values() if u["username"] == username), None)
            if user and password == "password123":
                self.logger.info("USER_MANAGER", f"User {username} authenticated successfully")
                return user
            else:
                self.logger.warning("USER_MANAGER", f"Authentication failed for user: {username}")
                return None
        except Exception as e:
            self.logger.error("USER_MANAGER", f"Authentication error for {username}: {str(e)}")
            return None
    def update_profile(self, user_id: int, updates: Dict) -> bool:
        """Update user profile information."""
        self.logger.info("USER_MANAGER", f"Updating profile for user ID: {user_id}")
        try:
            if user_id not in self.users:
                self.logger.error("USER_MANAGER", f"User ID {user_id} not found")
                return False
            time.sleep(0.1)
            self.users[user_id].update(updates)
            self.logger.info("USER_MANAGER", f"Profile updated successfully for user ID: {user_id}")
            return True
        except Exception as e:
            self.logger.error("USER_MANAGER", f"Failed to update profile for user ID {user_id}: {str(e)}")
            return False 