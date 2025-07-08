#!/usr/bin/env python3
"""
12 - Microservices

This example demonstrates microservices logging with Hydra-Logger.
Shows how to handle distributed logging across multiple services.
"""

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
import time
import uuid
import random

def generate_request_id():
    """Generate a unique request ID for tracing."""
    return str(uuid.uuid4())

def simulate_microservice(service_name, logger, request_id):
    """Simulate a microservice operation."""
    logger.info("SERVICE", f"{service_name} service started",
                service=service_name,
                request_id=request_id,
                timestamp=time.time())
    
    # Simulate processing time
    processing_time = random.uniform(0.1, 0.5)
    time.sleep(processing_time)
    
    # Simulate some operations
    logger.debug("SERVICE", f"{service_name} processing request",
                service=service_name,
                request_id=request_id,
                processing_time=f"{processing_time:.3f}s")
    
    # Simulate potential errors
    if random.random() < 0.1:  # 10% chance of error
        logger.error("SERVICE", f"{service_name} encountered error",
                    service=service_name,
                    request_id=request_id,
                    error="Service temporarily unavailable")
        return False
    
    logger.info("SERVICE", f"{service_name} service completed",
                service=service_name,
                request_id=request_id,
                duration=f"{processing_time:.3f}s")
    return True

def main():
    """Demonstrate microservices logging."""
    
    print("🏗️ Microservices Demo")
    print("=" * 40)
    
    # Create microservices configuration
    config = LoggingConfig(
        layers={
            "SERVICE": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/microservices/services.log",
                        format="json"
                    )
                ]
            ),
            "API_GATEWAY": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/microservices/gateway.log",
                        format="json"
                    )
                ]
            ),
            "DATABASE": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/microservices/database.log",
                        format="text"
                    )
                ]
            ),
            "CACHE": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/microservices/cache.log",
                        format="text"
                    )
                ]
            ),
            "AUTH": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/microservices/auth.log",
                        format="json"
                    )
                ]
            )
        }
    )
    
    # Initialize logger
    logger = HydraLogger(config)
    
    print("\n🌐 API Gateway Simulation")
    print("-" * 30)
    
    # Simulate API Gateway
    request_id = generate_request_id()
    logger.info("API_GATEWAY", "Request received",
                request_id=request_id,
                method="POST",
                endpoint="/api/users",
                user_agent="Mozilla/5.0",
                ip_address="192.168.1.100")
    
    # Simulate authentication
    logger.info("AUTH", "Authentication check",
                request_id=request_id,
                user_id="123",
                token_valid=True,
                permissions=["read", "write"])
    
    # Simulate database operations
    logger.debug("DATABASE", "Database query executed",
                request_id=request_id,
                query="SELECT * FROM users WHERE id = 123",
                duration="50ms",
                rows_returned=1)
    
    # Simulate cache operations
    logger.info("CACHE", "Cache miss",
                request_id=request_id,
                key="user:123",
                action="fetch_from_database")
    
    # Simulate microservices
    services = ["UserService", "OrderService", "PaymentService", "NotificationService"]
    
    print("\n🔧 Microservices Simulation")
    print("-" * 30)
    
    for service in services:
        success = simulate_microservice(service, logger, request_id)
        if not success:
            logger.error("API_GATEWAY", f"Service {service} failed",
                        request_id=request_id,
                        service=service,
                        status_code=503)
    
    # Simulate distributed tracing
    print("\n🔍 Distributed Tracing")
    print("-" * 25)
    
    trace_id = generate_request_id()
    span_id = 1
    
    logger.info("SERVICE", "Distributed trace started",
                trace_id=trace_id,
                span_id=span_id,
                service="API_GATEWAY")
    
    # Simulate service calls with tracing
    for i, service in enumerate(services):
        span_id += 1
        logger.info("SERVICE", f"Service call to {service}",
                    trace_id=trace_id,
                    span_id=span_id,
                    parent_span_id=1,
                    service=service)
        
        # Simulate nested service calls
        if service == "OrderService":
            nested_span_id = span_id + 100
            logger.info("SERVICE", "Inventory check",
                        trace_id=trace_id,
                        span_id=nested_span_id,
                        parent_span_id=span_id,
                        service="InventoryService")
    
    # Simulate load balancing
    print("\n⚖️ Load Balancing")
    print("-" * 20)
    
    instances = ["instance-1", "instance-2", "instance-3"]
    for i in range(5):
        request_id = generate_request_id()
        selected_instance = random.choice(instances)
        
        logger.info("API_GATEWAY", "Request routed to instance",
                    request_id=request_id,
                    instance=selected_instance,
                    load_balancer="round_robin")
        
        simulate_microservice("UserService", logger, request_id)
    
    # Simulate service discovery
    print("\n🔍 Service Discovery")
    print("-" * 20)
    
    service_registry = {
        "UserService": ["user-service-1:8080", "user-service-2:8080"],
        "OrderService": ["order-service-1:8081", "order-service-2:8081"],
        "PaymentService": ["payment-service-1:8082"],
        "NotificationService": ["notification-service-1:8083"]
    }
    
    for service_name, instances in service_registry.items():
        selected_instance = random.choice(instances)
        logger.info("SERVICE", "Service instance selected",
                    service=service_name,
                    instance=selected_instance,
                    available_instances=len(instances))
    
    # Simulate health checks
    print("\n💚 Health Checks")
    print("-" * 15)
    
    for service in services:
        health_status = "healthy" if random.random() > 0.1 else "unhealthy"
        response_time = random.uniform(10, 100)
        
        logger.info("SERVICE", "Health check completed",
                    service=service,
                    status=health_status,
                    response_time=f"{response_time:.2f}ms")
        
        if health_status == "unhealthy":
            logger.warning("SERVICE", "Service health check failed",
                          service=service,
                          action="remove_from_load_balancer")
    
    # Simulate circuit breaker
    print("\n🔌 Circuit Breaker")
    print("-" * 20)
    
    for service in services:
        failure_count = random.randint(0, 5)
        threshold = 3
        
        if failure_count >= threshold:
            logger.warning("SERVICE", "Circuit breaker opened",
                          service=service,
                          failure_count=failure_count,
                          threshold=threshold,
                          action="temporary_disable")
        else:
            logger.info("SERVICE", "Circuit breaker status",
                        service=service,
                        failure_count=failure_count,
                        threshold=threshold,
                        status="closed")
    
    # Simulate metrics collection
    print("\n📊 Metrics Collection")
    print("-" * 20)
    
    for service in services:
        request_count = random.randint(100, 1000)
        error_rate = random.uniform(0, 5)
        avg_response_time = random.uniform(50, 200)
        
        logger.info("SERVICE", "Service metrics",
                    service=service,
                    request_count=request_count,
                    error_rate=f"{error_rate:.2f}%",
                    avg_response_time=f"{avg_response_time:.2f}ms")
    
    print("\n✅ Microservices demo completed!")
    print("📝 Check the logs/microservices/ directory for distributed logs")
    
    # Show microservices summary
    print("\n📊 Microservices Summary:")
    print("-" * 30)
    print(f"• Services simulated: {len(services)}")
    print(f"• Request tracing: Enabled")
    print(f"• Load balancing: Round-robin")
    print(f"• Health checks: Active")
    print(f"• Circuit breaker: Implemented")
    print(f"• Metrics collection: Enabled")

if __name__ == "__main__":
    main() 