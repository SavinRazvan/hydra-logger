"""
API Client Module

Handles external API interactions and data fetching.
"""

import time
import random
import requests
from typing import Dict, List, Optional

class APIClient:
    """Handles external API interactions."""
    def __init__(self, logger, base_url: str = "https://api.example.com"):
        self.logger = logger
        self.base_url = base_url
        self.session = requests.Session()
        self.logger.info("API", f"APIClient initialized with base URL: {base_url}")
    def get_user_data(self, user_id: int) -> Optional[Dict]:
        """Fetch user data from external API."""
        self.logger.info("API", f"Fetching user data for user ID: {user_id}")
        try:
            time.sleep(0.3)
            if random.random() > 0.1:
                user_data = {
                    "id": user_id,
                    "name": f"User {user_id}",
                    "email": f"user{user_id}@example.com",
                    "profile": {
                        "bio": f"Bio for user {user_id}",
                        "avatar": f"https://example.com/avatars/{user_id}.jpg"
                    }
                }
                self.logger.info("API", f"Successfully fetched user data for user ID: {user_id}")
                return user_data
            else:
                self.logger.warning("API", f"User data not found for user ID: {user_id}")
                return None
        except Exception as e:
            self.logger.error("API", f"Failed to fetch user data for user ID {user_id}: {str(e)}")
            return None
    def update_user_profile(self, user_id: int, profile_data: Dict) -> bool:
        """Update user profile via external API."""
        self.logger.info("API", f"Updating user profile for user ID: {user_id}")
        try:
            time.sleep(0.2)
            if random.random() > 0.05:
                self.logger.info("API", f"Successfully updated user profile for user ID: {user_id}")
                return True
            else:
                self.logger.warning("API", f"Failed to update user profile for user ID: {user_id}")
                return False
        except Exception as e:
            self.logger.error("API", f"Error updating user profile for user ID {user_id}: {str(e)}")
            return False
    def send_notification(self, user_id: int, message: str) -> bool:
        """Send notification to user via external API."""
        self.logger.info("API", f"Sending notification to user ID: {user_id}")
        try:
            time.sleep(0.1)
            if random.random() > 0.02:
                self.logger.info("API", f"Notification sent successfully to user ID: {user_id}")
                return True
            else:
                self.logger.warning("API", f"Failed to send notification to user ID: {user_id}")
                return False
        except Exception as e:
            self.logger.error("API", f"Error sending notification to user ID {user_id}: {str(e)}")
            return False 