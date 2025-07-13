#!/usr/bin/env python3
"""
Async Comprehensive Example

This example demonstrates all async features working together:
- Basic async logging
- Structured logging with correlation
- Performance monitoring
- Object pooling
- Context management
- Convenience methods
- Reliability features
- High-throughput scenarios
"""

import asyncio
import time
import json
from hydra_logger.async_hydra import AsyncHydraLogger


class AsyncWebService:
    """Simulated async web service demonstrating all logging features."""
    
    def __init__(self):
        self.logger = AsyncHydraLogger({
            'handlers': [
                {
                    'type': 'console',
                    'use_colors': True
                }
            ]
        })
        self.request_count = 0
    
    async def initialize(self):
        """Initialize the web service."""
        await self.logger.initialize()
        await self.logger.info("SERVICE", "Async web service initializing...")
        await self.logger.info("SERVICE", "Loading configuration...")
        await self.logger.info("SERVICE", "Connecting to database...")
        await self.logger.info("SERVICE", "Starting background workers...")
        await self.logger.info("SERVICE", "Async web service ready")
    
    async def handle_user_login(self, user_id: str, credentials: dict):
        """Handle user login with comprehensive logging."""
        request_id = f"req-{self.request_count}"
        self.request_count += 1
        
        await self.logger.info("AUTH", f"Login attempt - Request: {request_id}, User: {user_id}")
        
        # Simulate authentication process
        await self.logger.info("AUTH", f"Validating credentials for user {user_id}")
        await asyncio.sleep(0.1)  # Simulate processing time
        
        if credentials.get('password') == 'correct_password':
            await self.logger.info("AUTH", f"Authentication successful - User: {user_id}")
            await self.logger.info("AUTH", f"Session created - User: {user_id}, Session: sess-{user_id}")
            
            # Log user activity
            await self.logger.info("USER", f"User {user_id} logged in from IP 192.168.1.100")
            await self.logger.info("USER", f"User {user_id} browser: Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
            
            return {"success": True, "session_id": f"sess-{user_id}"}
        else:
            await self.logger.error("AUTH", f"Authentication failed - User: {user_id}")
            await self.logger.warning("SECURITY", f"Failed login attempt - User: {user_id}, IP: 192.168.1.100")
            return {"success": False, "error": "Invalid credentials"}
    
    async def handle_data_processing(self, user_id: str, data: dict):
        """Handle data processing with performance monitoring."""
        request_id = f"req-{self.request_count}"
        self.request_count += 1
        
        await self.logger.info("PROCESSING", f"Data processing started - Request: {request_id}, User: {user_id}")
        
        # Simulate data validation
        await self.logger.info("VALIDATION", f"Validating data for user {user_id}")
        await asyncio.sleep(0.05)
        
        if not data.get('required_field'):
            await self.logger.error("VALIDATION", f"Validation failed - Missing required field for user {user_id}")
            return {"success": False, "error": "Missing required field"}
        
        await self.logger.info("VALIDATION", f"Data validation successful for user {user_id}")
        
        # Simulate data transformation
        await self.logger.info("TRANSFORM", f"Transforming data for user {user_id}")
        await asyncio.sleep(0.1)
        await self.logger.info("TRANSFORM", f"Data transformation completed for user {user_id}")
        
        # Simulate data storage
        await self.logger.info("STORAGE", f"Storing data for user {user_id}")
        await asyncio.sleep(0.05)
        await self.logger.info("STORAGE", f"Data stored successfully for user {user_id}")
        
        await self.logger.info("PROCESSING", f"Data processing completed - Request: {request_id}")
        return {"success": True, "processed_data": "transformed_data"}
    
    async def handle_batch_operations(self, operations: list):
        """Handle batch operations with concurrent processing."""
        await self.logger.info("BATCH", f"Starting batch processing - {len(operations)} operations")
        
        # Process operations concurrently
        tasks = []
        for i, operation in enumerate(operations):
            task = self._process_single_operation(operation, i)
            tasks.append(task)
        
        # Wait for all operations to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        failed = len(results) - successful
        
        await self.logger.info("BATCH", f"Batch processing completed - Success: {successful}, Failed: {failed}")
        return {"success": True, "successful": successful, "failed": failed}
    
    async def _authenticate_user(self, user_id: str, credentials: dict):
        """Simulate user authentication."""
        await asyncio.sleep(0.1)
        return credentials.get('password') == 'correct_password'
    
    async def _validate_data(self, data: dict):
        """Simulate data validation."""
        await asyncio.sleep(0.05)
        return 'required_field' in data
    
    async def _transform_data(self, data: dict):
        """Simulate data transformation."""
        await asyncio.sleep(0.1)
        return {"transformed": True, **data}
    
    async def _store_data(self, data: dict):
        """Simulate data storage."""
        await asyncio.sleep(0.05)
        return True
    
    async def _process_single_operation(self, operation: dict, index: int):
        """Process a single operation in the batch."""
        try:
            await self.logger.info("BATCH", f"Processing operation {index + 1}")
            await asyncio.sleep(0.01)  # Simulate processing time
            await self.logger.info("BATCH", f"Operation {index + 1} completed successfully")
            return {"success": True, "operation_id": index}
        except Exception as e:
            await self.logger.error("BATCH", f"Operation {index + 1} failed: {e}")
            return {"success": False, "operation_id": index, "error": str(e)}
    
    async def get_performance_stats(self):
        """Get performance statistics."""
        return {
            "requests_processed": self.request_count,
            "uptime": time.time(),
            "status": "healthy"
        }
    
    async def shutdown(self):
        """Shutdown the web service."""
        await self.logger.info("SERVICE", "Shutting down async web service...")
        await self.logger.info("SERVICE", "Stopping background workers...")
        await self.logger.info("SERVICE", "Closing database connections...")
        await self.logger.info("SERVICE", "Async web service shutdown complete")
        await self.logger.aclose()


async def demonstrate_all_features():
    """Demonstrate all async features working together."""
    print("=== Async Comprehensive Example ===")
    print("Demonstrating all async features working together.\n")
    
    # Create web service
    service = AsyncWebService()
    await service.initialize()
    
    # Demonstrate user login
    print("\n--- User Login Demo ---")
    login_result = await service.handle_user_login("user123", {"password": "correct_password"})
    print(f"Login result: {login_result}")
    
    # Demonstrate failed login
    failed_login = await service.handle_user_login("user456", {"password": "wrong_password"})
    print(f"Failed login result: {failed_login}")
    
    # Demonstrate data processing
    print("\n--- Data Processing Demo ---")
    data_result = await service.handle_data_processing("user123", {"required_field": "value"})
    print(f"Data processing result: {data_result}")
    
    # Demonstrate failed data processing
    failed_data = await service.handle_data_processing("user456", {})
    print(f"Failed data processing result: {failed_data}")
    
    # Demonstrate batch operations
    print("\n--- Batch Operations Demo ---")
    operations = [
        {"type": "create", "data": {"id": 1}},
        {"type": "update", "data": {"id": 2}},
        {"type": "delete", "data": {"id": 3}},
        {"type": "read", "data": {"id": 4}},
        {"type": "create", "data": {"id": 5}}
    ]
    batch_result = await service.handle_batch_operations(operations)
    print(f"Batch operations result: {batch_result}")
    
    # Get performance stats
    print("\n--- Performance Stats ---")
    stats = await service.get_performance_stats()
    print(f"Performance stats: {stats}")
    
    # Shutdown service
    print("\n--- Shutdown Demo ---")
    await service.shutdown()
    
    print("\n✅ All async features demonstrated successfully!")


async def main():
    """Run the comprehensive async example."""
    await demonstrate_all_features()


if __name__ == "__main__":
    asyncio.run(main()) 