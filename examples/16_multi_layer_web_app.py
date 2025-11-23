#!/usr/bin/env python3
"""
Example 16: Multi-Layer Web Application Logging

Demonstrates how to use Hydra-Logger with multiple layers in a web application.
Each layer (API, Database, Frontend, Auth) writes to separate log files.

Key Features:
    - Multiple concurrent routes/requests
    - Separate layers for different concerns
    - Individual log files per layer
    - Professional web application structure
"""
import asyncio
import random
from typing import Dict, Any
from hydra_logger import LoggingConfig, LogLayer, LogDestination, create_async_logger

# ============================================================================
# CONFIGURATION: Multi-Layer Setup for Web Application
# ============================================================================

config = LoggingConfig(
    layers={
        "api": LogLayer(
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/examples/16_api_requests.jsonl",
                    format="json-lines"
                ),
                LogDestination(
                    type="console",
                    format="colored",
                    use_colors=True
                )
            ]
        ),
        "database": LogLayer(
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/examples/16_database_operations.jsonl",
                    format="json-lines"
                )
            ]
        ),
        "frontend": LogLayer(
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/examples/16_frontend_events.jsonl",
                    format="json-lines"
                ),
                LogDestination(
                    type="console",
                    format="colored",
                    use_colors=True
                )
            ]
        ),
        "auth": LogLayer(
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/examples/16_authentication.jsonl",
                    format="json-lines"
                )
            ]
        ),
        "middleware": LogLayer(
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/examples/16_middleware.jsonl",
                    format="json-lines"
                )
            ]
        )
    }
)

# ============================================================================
# WEB APPLICATION SIMULATION
# ============================================================================

class WebApplication:
    """Simulates a multi-layer web application."""
    
    def __init__(self, logger):
        self.logger = logger
        self.request_id_counter = 0
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        self.request_id_counter += 1
        return f"req-{self.request_id_counter:06d}"
    
    async def handle_api_request(self, method: str, endpoint: str, user_id: str = None):
        """Handle API requests - logs to 'api' layer."""
        request_id = self._generate_request_id()
        
        await self.logger.info(
            f"[16] API Request: {method} {endpoint}",
            layer="api",
            context={
                "request_id": request_id,
                "method": method,
                "endpoint": endpoint,
                "user_id": user_id,
                "ip_address": f"192.168.1.{random.randint(1, 254)}"
            }
        )
        
        # Simulate processing (reduced delays for faster examples)
        await asyncio.sleep(random.uniform(0.01, 0.02))  # Reduced from 0.05-0.15s
        
        await self.logger.info(
            f"[16] API Response: {method} {endpoint} - 200 OK",
            layer="api",
            context={
                "request_id": request_id,
                "status_code": 200,
                "response_time_ms": random.randint(50, 150)
            }
        )
        
        return request_id
    
    async def query_database(self, operation: str, table: str, query_id: str = None):
        """Execute database queries - logs to 'database' layer."""
        if not query_id:
            query_id = f"query-{random.randint(1000, 9999)}"
        
        await self.logger.debug(
            f"[16] DB Query: {operation} on {table}",
            layer="database",
            context={
                "query_id": query_id,
                "operation": operation,
                "table": table,
                "rows_affected": random.randint(0, 100)
            }
        )
        
        # Simulate query execution (reduced delays for faster examples)
        await asyncio.sleep(random.uniform(0.005, 0.01))  # Reduced from 0.01-0.05s
        
        await self.logger.info(
            f"[16] DB Query Completed: {operation} on {table}",
            layer="database",
            context={
                "query_id": query_id,
                "execution_time_ms": random.randint(5, 50)
            }
        )
    
    async def handle_frontend_event(self, event_type: str, page: str, user_id: str):
        """Handle frontend events - logs to 'frontend' layer."""
        await self.logger.info(
            f"[16] Frontend Event: {event_type} on {page}",
            layer="frontend",
            context={
                "event_type": event_type,
                "page": page,
                "user_id": user_id,
                "user_agent": "Mozilla/5.0",
                "session_id": f"session-{random.randint(10000, 99999)}"
            }
        )
    
    async def authenticate_user(self, username: str, login_method: str):
        """Authenticate users - logs to 'auth' layer."""
        await self.logger.info(
            f"[16] Authentication Attempt: {username} via {login_method}",
            layer="auth",
            context={
                "username": username,
                "login_method": login_method,
                "ip_address": f"192.168.1.{random.randint(1, 254)}"
            }
        )
        
        # Simulate authentication
        await asyncio.sleep(random.uniform(0.01, 0.02))  # Reduced from 0.1-0.2s
        
        success = random.random() > 0.1  # 90% success rate
        
        if success:
            await self.logger.info(
                f"[16] Authentication Success: {username}",
                layer="auth",
                context={
                    "username": username,
                    "token_issued": True,
                    "session_duration": 3600
                }
            )
        else:
            await self.logger.warning(
                f"[16] Authentication Failed: {username}",
                layer="auth",
                context={
                    "username": username,
                    "reason": "Invalid credentials"
                }
            )
        
        return success
    
    async def process_middleware(self, middleware_type: str, request_id: str):
        """Process middleware - logs to 'middleware' layer."""
        await self.logger.debug(
            f"[16] Middleware: {middleware_type} processing request {request_id}",
            layer="middleware",
            context={
                "middleware_type": middleware_type,
                "request_id": request_id,
                "processing_time_ms": random.randint(1, 10)
            }
        )

# ============================================================================
# ROUTE SIMULATIONS
# ============================================================================

async def simulate_user_login(app: WebApplication, username: str):
    """Simulate user login flow."""
    # Auth layer
    await app.authenticate_user(username, "password")
    
    # Frontend layer
    await app.handle_frontend_event("page_load", "/dashboard", username)
    await app.handle_frontend_event("click", "dashboard", username)

async def simulate_api_endpoint(app: WebApplication, endpoint: str, method: str = "GET"):
    """Simulate API endpoint requests."""
    user_id = f"user-{random.randint(1, 100)}"
    
    # Middleware layer
    request_id = app._generate_request_id()
    await app.process_middleware("rate_limiter", request_id)
    await app.process_middleware("cors", request_id)
    
    # API layer
    await app.handle_api_request(method, endpoint, user_id)
    
    # Database layer (if needed)
    if "/users" in endpoint or "/data" in endpoint:
        await app.query_database("SELECT", "users", f"query-{request_id}")
    if "POST" in method or "PUT" in method:
        await app.query_database("UPDATE", "users", f"query-{request_id}")

async def simulate_dashboard_load(app: WebApplication, user_id: str):
    """Simulate dashboard page load."""
    # Frontend events
    await app.handle_frontend_event("page_load", "/dashboard", user_id)
    await app.handle_frontend_event("data_fetch", "/dashboard", user_id)
    
    # API calls
    await app.handle_api_request("GET", "/api/dashboard/stats", user_id)
    await app.handle_api_request("GET", "/api/dashboard/notifications", user_id)
    
    # Database queries
    await app.query_database("SELECT", "user_preferences", f"query-user-{user_id}")
    await app.query_database("SELECT", "notifications", f"query-notif-{user_id}")

# ============================================================================
# MAIN SIMULATION
# ============================================================================

async def main():
    """Run multi-layer web application simulation."""
    print("\n" + "=" * 80)
    print("Example 16: Multi-Layer Web Application Logging")
    print("=" * 80)
    print("\nSimulating web application with multiple layers:")
    print(" - API Layer: HTTP requests/responses")
    print(" - Database Layer: Query operations")
    print(" - Frontend Layer: User interactions")
    print(" - Auth Layer: Authentication events")
    print(" - Middleware Layer: Request processing")
    print()
    
    # Use async context manager for automatic cleanup
    async with create_async_logger(config, name="WebApp") as logger:
        app = WebApplication(logger)
        
        # Simulate concurrent user sessions
        tasks = []
        
        # Simulate 3 user logins (reduced from 5 for faster examples)
        print("Simulating user logins (Auth layer)...")
        for i in range(3):
            tasks.append(simulate_user_login(app, f"user{i+1}"))
        
        # Simulate 5 API endpoint requests (reduced from 10 for faster examples)
        print("Simulating API requests (API layer)...")
        api_endpoints = [
            "/api/users/profile",
            "/api/products/list",
            "/api/orders/create",
            "/api/data/analytics",
            "/api/users/update"
        ]
        for endpoint in api_endpoints:  # Reduced from * 2
            method = random.choice(["GET", "POST", "PUT"])
            tasks.append(simulate_api_endpoint(app, endpoint, method))
        
        # Simulate 2 dashboard loads (reduced from 3 for faster examples)
        print("Simulating dashboard loads (All layers)...")
        for i in range(2):
            tasks.append(simulate_dashboard_load(app, f"user{i+1}"))
        
        # Run all simulations concurrently
        print(f"\nExecuting {len(tasks)} concurrent operations...\n")
        await asyncio.gather(*tasks, return_exceptions=True)
    
    print("\nExample 16 completed: Multi-Layer Web Application")
    print("\nLog files created:")
    print(" - logs/examples/16_api_requests.jsonl")
    print(" - logs/examples/16_database_operations.jsonl")
    print(" - logs/examples/16_frontend_events.jsonl")
    print(" - logs/examples/16_authentication.jsonl")
    print(" - logs/examples/16_middleware.jsonl")
    print("\nEach layer writes to its own log file for easy analysis!")

if __name__ == "__main__":
    asyncio.run(main())
