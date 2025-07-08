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
from hydra_logger.async_hydra.async_logger import AsyncHydraLogger


class AsyncWebService:
    """Simulated async web service demonstrating all logging features."""
    
    def __init__(self):
        self.logger = AsyncHydraLogger(
            enable_object_pooling=True,
            pool_size=1000,
            batch_size=100,
            batch_timeout=0.1,
            enable_performance_monitoring=True,
            test_mode=True
        )
        self.request_count = 0
    
    async def handle_user_login(self, user_id: str, credentials: dict):
        """Handle user login with comprehensive logging."""
        request_id = f"req-{self.request_count:06d}"
        self.request_count += 1
        
        # Set correlation context
        with self.logger.correlation_context(
            request_id, 
            user_id=user_id
        ):
            # Log request start
            await self.logger.log_request(
                request_id=request_id,
                method="POST",
                path="/api/auth/login",
                status_code=200,
                duration=0.0  # Will be updated
            )
            
            start_time = time.time()
            
            try:
                # Simulate authentication process
                await self._authenticate_user(user_id, credentials)
                
                # Log successful login
                await self.logger.log_user_action(
                    user_id=user_id,
                    action="login",
                    resource="auth",
                    success=True
                )
                
                # Log performance metrics
                auth_duration = time.time() - start_time
                await self.logger.log_performance(
                    operation="user_authentication",
                    duration=auth_duration,
                    layer="PERFORMANCE"
                )
                
                # Structured log with context
                await self.logger.log_structured(
                    layer="SECURITY",
                    level="INFO",
                    message="User login successful",
                    correlation_id=request_id,
                    context={
                        "user_id": user_id,
                        "ip_address": "192.168.1.100",
                        "user_agent": "Mozilla/5.0",
                        "auth_method": "password",
                        "session_duration": 3600
                    },
                    format="json"
                )
                
                return {"success": True, "session_id": f"session-{user_id}"}
                
            except Exception as e:
                # Log error with context
                await self.logger.log_error_with_context(
                    error=e,
                    layer="AUTH",
                    context={
                        "user_id": user_id,
                        "request_id": request_id,
                        "auth_method": "password"
                    }
                )
                
                # Log failed user action
                await self.logger.log_user_action(
                    user_id=user_id,
                    action="login",
                    resource="auth",
                    success=False
                )
                
                raise
    
    async def handle_data_processing(self, user_id: str, data: dict):
        """Handle data processing with performance monitoring."""
        request_id = f"req-{self.request_count:06d}"
        self.request_count += 1
        
        with self.logger.correlation_context(request_id, user_id=user_id):
            start_time = time.time()
            
            # Log processing start
            await self.logger.info("PROCESSING", "Starting data processing")
            
            try:
                # Simulate data validation
                await self._validate_data(data)
                
                # Simulate data transformation
                transformed_data = await self._transform_data(data)
                
                # Simulate database storage
                await self._store_data(transformed_data)
                
                # Log performance metrics
                total_duration = time.time() - start_time
                await self.logger.log_performance(
                    operation="data_processing",
                    duration=total_duration,
                    layer="PERFORMANCE"
                )
                
                # Structured log with results
                await self.logger.log_structured(
                    layer="BUSINESS",
                    level="INFO",
                    message="Data processing completed",
                    correlation_id=request_id,
                    context={
                        "user_id": user_id,
                        "data_size": len(str(data)),
                        "processing_time": total_duration,
                        "records_processed": len(data.get("records", [])),
                        "status": "success"
                    },
                    format="dict"
                )
                
                return {"success": True, "processed_records": len(data.get("records", []))}
                
            except Exception as e:
                await self.logger.log_error_with_context(
                    error=e,
                    layer="PROCESSING",
                    context={
                        "user_id": user_id,
                        "request_id": request_id,
                        "data_size": len(str(data))
                    }
                )
                raise
    
    async def handle_batch_operations(self, operations: list):
        """Handle batch operations with high throughput."""
        print(f"Processing {len(operations)} batch operations...")
        
        start_time = time.time()
        tasks = []
        
        for i, operation in enumerate(operations):
            task = asyncio.create_task(
                self._process_single_operation(operation, i)
            )
            tasks.append(task)
        
        # Wait for all operations to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        successful = sum(1 for r in results if not isinstance(r, Exception))
        
        # Log batch results
        await self.logger.log_structured(
            layer="BATCH",
            level="INFO",
            message="Batch processing completed",
            context={
                "total_operations": len(operations),
                "successful_operations": successful,
                "failed_operations": len(operations) - successful,
                "total_time": total_time,
                "throughput": len(operations) / total_time
            },
            format="json"
        )
        
        return {
            "total": len(operations),
            "successful": successful,
            "failed": len(operations) - successful,
            "total_time": total_time
        }
    
    async def _authenticate_user(self, user_id: str, credentials: dict):
        """Simulate user authentication."""
        await asyncio.sleep(0.1)  # Simulate auth time
        
        if credentials.get("password") == "wrong_password":
            raise ValueError("Invalid credentials")
        
        await self.logger.info("AUTH", f"User {user_id} authenticated successfully")
    
    async def _validate_data(self, data: dict):
        """Simulate data validation."""
        await asyncio.sleep(0.05)  # Simulate validation time
        
        if not data.get("records"):
            raise ValueError("No records found in data")
        
        await self.logger.info("VALIDATION", "Data validation completed")
    
    async def _transform_data(self, data: dict):
        """Simulate data transformation."""
        await asyncio.sleep(0.1)  # Simulate transformation time
        
        transformed = {
            "transformed_records": len(data.get("records", [])),
            "timestamp": time.time()
        }
        
        await self.logger.info("TRANSFORM", "Data transformation completed")
        return transformed
    
    async def _store_data(self, data: dict):
        """Simulate database storage."""
        await asyncio.sleep(0.05)  # Simulate storage time
        
        await self.logger.info("STORAGE", "Data stored successfully")
    
    async def _process_single_operation(self, operation: dict, index: int):
        """Process a single operation in batch."""
        try:
            await asyncio.sleep(0.01)  # Simulate processing time
            
            await self.logger.info(
                "BATCH", 
                f"Processed operation {index}: {operation.get('type', 'unknown')}"
            )
            
            return {"success": True, "operation_id": index}
            
        except Exception as e:
            await self.logger.log_error_with_context(
                error=e,
                layer="BATCH",
                context={"operation_index": index, "operation": operation}
            )
            raise
    
    async def get_performance_stats(self):
        """Get performance statistics."""
        stats = await self.logger.get_async_performance_statistics()
        return stats
    
    async def shutdown(self):
        """Graceful shutdown."""
        await self.logger.graceful_shutdown(timeout=5.0)


async def demonstrate_all_features():
    """Demonstrate all async features working together."""
    print("🚀 Async Comprehensive Example")
    print("=" * 50)
    
    # Create web service
    service = AsyncWebService()
    
    # Test 1: User login flow
    print("\n=== Test 1: User Login Flow ===")
    try:
        result = await service.handle_user_login(
            user_id="user-123",
            credentials={"username": "john", "password": "correct_password"}
        )
        print(f"Login result: {result}")
    except Exception as e:
        print(f"Login failed: {e}")
    
    # Test 2: Failed login
    print("\n=== Test 2: Failed Login ===")
    try:
        result = await service.handle_user_login(
            user_id="user-456",
            credentials={"username": "jane", "password": "wrong_password"}
        )
        print(f"Login result: {result}")
    except Exception as e:
        print(f"Login failed as expected: {e}")
    
    # Test 3: Data processing
    print("\n=== Test 3: Data Processing ===")
    try:
        result = await service.handle_data_processing(
            user_id="user-789",
            data={
                "records": [{"id": 1}, {"id": 2}, {"id": 3}],
                "metadata": {"source": "api", "version": "1.0"}
            }
        )
        print(f"Processing result: {result}")
    except Exception as e:
        print(f"Processing failed: {e}")
    
    # Test 4: Batch operations
    print("\n=== Test 4: Batch Operations ===")
    operations = [
        {"type": "create", "data": {"name": "item1"}},
        {"type": "update", "data": {"id": 1, "name": "item1_updated"}},
        {"type": "delete", "data": {"id": 2}},
        {"type": "read", "data": {"id": 3}},
        {"type": "create", "data": {"name": "item2"}},
    ] * 20  # 100 operations total
    
    result = await service.handle_batch_operations(operations)
    print(f"Batch result: {result}")
    
    # Test 5: Performance statistics
    print("\n=== Test 5: Performance Statistics ===")
    stats = await service.get_performance_stats()
    if stats:
        print("Performance Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    # Test 6: Graceful shutdown
    print("\n=== Test 6: Graceful Shutdown ===")
    await service.shutdown()
    
    print("\n✅ All comprehensive tests completed successfully!")


async def main():
    """Run the comprehensive example."""
    await demonstrate_all_features()


if __name__ == "__main__":
    asyncio.run(main()) 