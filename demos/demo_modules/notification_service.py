"""
Notification Service Module

Handles email and SMS notifications.
"""

import time
import random
from typing import List, Dict, Optional

class NotificationService:
    """Handles email and SMS notifications."""
    def __init__(self, logger):
        self.logger = logger
        self.email_queue = []
        self.sms_queue = []
        self.logger.info("NOTIFICATIONS", "NotificationService initialized")
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send an email notification."""
        self.logger.info("NOTIFICATIONS", f"Sending email to: {to_email}")
        try:
            time.sleep(0.2)
            if random.random() > 0.05:
                self.logger.info("NOTIFICATIONS", f"Email sent successfully to: {to_email}")
                return True
            else:
                self.logger.warning("NOTIFICATIONS", f"Failed to send email to: {to_email}")
                return False
        except Exception as e:
            self.logger.error("NOTIFICATIONS", f"Error sending email to {to_email}: {str(e)}")
            return False
    def send_sms(self, phone_number: str, message: str) -> bool:
        """Send an SMS notification."""
        self.logger.info("NOTIFICATIONS", f"Sending SMS to: {phone_number}")
        try:
            time.sleep(0.1)
            if random.random() > 0.03:
                self.logger.info("NOTIFICATIONS", f"SMS sent successfully to: {phone_number}")
                return True
            else:
                self.logger.warning("NOTIFICATIONS", f"Failed to send SMS to: {phone_number}")
                return False
        except Exception as e:
            self.logger.error("NOTIFICATIONS", f"Error sending SMS to {phone_number}: {str(e)}")
            return False
    def send_welcome_notification(self, user_data: Dict) -> bool:
        """Send welcome notification to new user."""
        self.logger.info("NOTIFICATIONS", f"Sending welcome notification to user: {user_data.get('username')}")
        try:
            email_sent = self.send_email(
                user_data.get('email'),
                "Welcome to Our Platform!",
                f"Hi {user_data.get('username')}, welcome to our platform!"
            )
            sms_sent = True
            if user_data.get('phone'):
                sms_sent = self.send_sms(
                    user_data.get('phone'),
                    f"Welcome {user_data.get('username')}! Your account is ready."
                )
            if email_sent and sms_sent:
                self.logger.info("NOTIFICATIONS", f"Welcome notifications sent successfully to user: {user_data.get('username')}")
                return True
            else:
                self.logger.warning("NOTIFICATIONS", f"Some welcome notifications failed for user: {user_data.get('username')}")
                return False
        except Exception as e:
            self.logger.error("NOTIFICATIONS", f"Error sending welcome notification to user {user_data.get('username')}: {str(e)}")
            return False
    def send_password_reset(self, email: str, reset_token: str) -> bool:
        """Send password reset notification."""
        self.logger.info("NOTIFICATIONS", f"Sending password reset to: {email}")
        try:
            reset_link = f"https://example.com/reset?token={reset_token}"
            email_sent = self.send_email(
                email,
                "Password Reset Request",
                f"Click here to reset your password: {reset_link}"
            )
            if email_sent:
                self.logger.info("NOTIFICATIONS", f"Password reset email sent successfully to: {email}")
                return True
            else:
                self.logger.warning("NOTIFICATIONS", f"Failed to send password reset email to: {email}")
                return False
        except Exception as e:
            self.logger.error("NOTIFICATIONS", f"Error sending password reset to {email}: {str(e)}")
            return False 