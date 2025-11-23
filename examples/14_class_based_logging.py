#!/usr/bin/env python3
"""
Example 14: Class-Based Logging
Demonstrates how logging works with classes, methods, and inheritance.
Shows function tracking for class methods, instance methods, static methods, and properties.
"""
from hydra_logger import LoggingConfig, LogLayer, LogDestination, create_logger

# Configure logger with multiple destinations to see different formats
config = LoggingConfig(
    layers={
        "app": LogLayer(
            destinations=[
                LogDestination(type="console", format="colored", use_colors=True),
                LogDestination(type="file", path="logs/examples/14_class_based_logging_app.jsonl", format="json-lines")
            ]
        ),
        "service": LogLayer(
            destinations=[
                LogDestination(type="file", path="logs/examples/14_class_based_logging_service.log", format="json")
            ]
        ),
        "model": LogLayer(
            destinations=[
                LogDestination(type="file", path="logs/examples/14_class_based_logging_model.log", format="json")
            ]
        )
    }
)

logger = create_logger(config, logger_type="sync")


# Base class with logging
class BaseService:
    """Base service class demonstrating logging in base classes."""
    
    def __init__(self, service_name: str):
        """Initialize the service."""
        self.service_name = service_name
        logger.info(f"[14] Initializing {service_name}", layer="service")
    
    def start(self):
        """Start the service."""
        logger.info(f"[14] Starting {self.service_name}", layer="service")
    
    def stop(self):
        """Stop the service."""
        logger.info(f"[14] Stopping {self.service_name}", layer="service")
    
    @staticmethod
    def validate_config(config: dict) -> bool:
        """Validate configuration (static method)."""
        logger.debug(f"[14] Validating configuration: {config}", layer="service")
        return True
    
    @classmethod
    def create_default(cls):
        """Create default instance (class method)."""
        logger.info(f"[14] Creating default {cls.__name__}", layer="service")
        return cls("default")


# Derived class demonstrating inheritance
class UserService(BaseService):
    """User service demonstrating logging in derived classes."""
    
    def __init__(self, service_name: str, user_count: int = 0):
        """Initialize user service."""
        super().__init__(service_name)
        self.user_count = user_count
        logger.info(f"[14] User service initialized with {user_count} users", layer="service")
    
    def create_user(self, username: str, email: str):
        """Create a new user."""
        logger.info(f"[14] Creating user: {username} ({email})", layer="service")
        # Simulate user creation
        self.user_count += 1
        logger.debug(f"[14] User count now: {self.user_count}", layer="service")
        return {"id": self.user_count, "username": username, "email": email}
    
    def delete_user(self, user_id: int):
        """Delete a user."""
        logger.warning(f"[14] Deleting user with ID: {user_id}", layer="service")
        # Simulate user deletion
        if self.user_count > 0:
            self.user_count -= 1
            logger.debug(f"[14] User count now: {self.user_count}", layer="service")
    
    def get_stats(self):
        """Get service statistics."""
        logger.info(f"[14] Retrieving statistics for {self.service_name}", layer="service")
        return {"user_count": self.user_count, "service": self.service_name}


# Model class demonstrating logging in data models
class UserModel:
    """User model demonstrating logging in model classes."""
    
    def __init__(self, user_id: int, username: str, email: str):
        """Initialize user model."""
        self.user_id = user_id
        self.username = username
        self.email = email
        logger.debug(f"[14] User model created: {username} (ID: {user_id})", layer="model")
    
    @property
    def display_name(self):
        """Get display name (property with logging)."""
        logger.debug(f"[14] Getting display name for user {self.user_id}", layer="model")
        return f"{self.username} ({self.email})"
    
    def update_email(self, new_email: str):
        """Update user email."""
        logger.info(f"[14] Updating email for user {self.user_id}: {new_email}", layer="model")
        old_email = self.email
        self.email = new_email
        logger.debug(f"[14] Email updated: {old_email} -> {new_email}", layer="model")
    
    def to_dict(self):
        """Convert to dictionary."""
        logger.debug(f"[14] Converting user {self.user_id} to dict", layer="model")
        return {
            "id": self.user_id,
            "username": self.username,
            "email": self.email
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create instance from dictionary (class method)."""
        logger.info(f"[14] Creating {cls.__name__} from dict", layer="model")
        return cls(
            user_id=data.get("id"),
            username=data.get("username"),
            email=data.get("email")
        )
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format (static method)."""
        logger.debug(f"[14] Validating email: {email}", layer="model")
        is_valid = "@" in email and "." in email.split("@")[1]
        if not is_valid:
            logger.warning(f"[14] Invalid email format: {email}", layer="model")
        return is_valid


# Controller class demonstrating logging in controllers
class UserController:
    """Controller class demonstrating logging in controllers."""
    
    def __init__(self, service: UserService):
        """Initialize controller."""
        self.service = service
        logger.info(f"[14] UserController initialized", layer="app")
    
    def handle_create_request(self, username: str, email: str):
        """Handle user creation request."""
        logger.info(f"[14] Handling create request for {username}", layer="app")
        # Validate email
        if not UserModel.validate_email(email):
            logger.error(f"[14] Invalid email provided: {email}", layer="app")
            return None
        # Create user
        user_data = self.service.create_user(username, email)
        logger.info(f"[14] User created successfully: {user_data['id']}", layer="app")
        return user_data
    
    def handle_delete_request(self, user_id: int):
        """Handle user deletion request."""
        logger.warning(f"[14] Handling delete request for user {user_id}", layer="app")
        self.service.delete_user(user_id)
        logger.info(f"[14] User {user_id} deleted successfully", layer="app")
    
    def handle_stats_request(self):
        """Handle stats request."""
        logger.debug(f"[14] Handling stats request", layer="app")
        stats = self.service.get_stats()
        logger.info(f"[14] Stats retrieved: {stats}", layer="app")
        return stats


# Demonstration of all class-based logging patterns
def main():
    """Main function demonstrating class-based logging."""
    logger.info("[14] Starting class-based logging demonstration", layer="app")
    
    # 1. Base class instantiation and methods
    logger.info("[14] === Testing BaseService ===", layer="app")
    base_service = BaseService("BaseService")
    base_service.start()
    BaseService.validate_config({"key": "value"})  # Static method
    BaseService.create_default()  # Class method
    base_service.stop()
    
    # 2. Derived class with inheritance
    logger.info("[14] === Testing UserService (inherited) ===", layer="app")
    user_service = UserService("UserService", user_count=5)
    user_service.start()
    user_service.create_user("john_doe", "john@example.com")
    user_service.create_user("jane_smith", "jane@example.com")
    user_service.delete_user(1)
    user_service.get_stats()
    user_service.stop()
    
    # 3. Model class with properties and class methods
    logger.info("[14] === Testing UserModel ===", layer="app")
    user1 = UserModel(1, "alice", "alice@example.com")
    _ = user1.display_name  # Property access
    user1.update_email("alice.new@example.com")
    user_dict = user1.to_dict()
    user2 = UserModel.from_dict({"id": 2, "username": "bob", "email": "bob@example.com"})
    UserModel.validate_email("invalid-email")  # Static method
    UserModel.validate_email("valid@example.com")  # Static method
    
    # 4. Controller class orchestrating services
    logger.info("[14] === Testing UserController ===", layer="app")
    controller = UserController(user_service)
    controller.handle_create_request("charlie", "charlie@example.com")
    controller.handle_create_request("diana", "invalid-email")  # Invalid email
    controller.handle_delete_request(2)
    controller.handle_stats_request()
    
    logger.info("[14] Class-based logging demonstration completed", layer="app")


if __name__ == "__main__":
    # Use context manager for automatic cleanup
    with create_logger(config) as logger:
        # Need to set logger in global scope for classes to use it
        import sys
        current_module = sys.modules[__name__]
        setattr(current_module, 'logger', logger)
        main()
    print("Example 14 completed: Class-Based Logging")
