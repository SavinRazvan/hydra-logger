#!/usr/bin/env python3
"""
19 - Cloud Native

This example demonstrates cloud-native logging with Hydra-Logger.
Shows how to handle logging in cloud environments and containerized applications.
"""

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
import time
import uuid
import random
import os

def simulate_cloud_operation(logger, operation_name, cloud_provider):
    """Simulate a cloud operation."""
    operation_id = str(uuid.uuid4())
    
    logger.info("CLOUD", f"Cloud operation started",
                operation_id=operation_id,
                operation_name=operation_name,
                cloud_provider=cloud_provider,
                region=random.choice(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]),
                timestamp=time.time())
    
    # Simulate operation processing
    processing_time = random.uniform(0.5, 2.0)
    time.sleep(processing_time)
    
    logger.info("CLOUD", f"Cloud operation completed",
                operation_id=operation_id,
                operation_name=operation_name,
                cloud_provider=cloud_provider,
                duration=f"{processing_time:.3f}s",
                status="success")

def main():
    """Demonstrate cloud-native logging."""
    
    print("☁️ Cloud Native Demo")
    print("=" * 40)
    
    # Create cloud-native configuration
    config = LoggingConfig(
        layers={
            "CLOUD": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/cloud/operations.log",
                        format="json"
                    )
                ]
            ),
            "CONTAINER": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/cloud/containers.log",
                        format="text"
                    )
                ]
            ),
            "KUBERNETES": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/cloud/kubernetes.log",
                        format="json"
                    )
                ]
            ),
            "SCALING": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/cloud/scaling.log",
                        format="text"
                    )
                ]
            ),
            "DEPLOYMENT": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/cloud/deployment.log",
                        format="json"
                    )
                ]
            )
        }
    )
    
    # Initialize logger
    logger = HydraLogger(config)
    
    print("\n🐳 Container Orchestration")
    print("-" * 25)
    
    # Simulate container orchestration
    containers = [
        ("web-app", "nginx:latest", 8080),
        ("api-service", "node:16", 3000),
        ("database", "postgres:13", 5432),
        ("cache", "redis:6", 6379),
        ("monitoring", "prometheus:latest", 9090)
    ]
    
    for container_name, image, port in containers:
        container_id = str(uuid.uuid4())[:8]
        
        logger.info("CONTAINER", f"Container {container_name} started",
                   container_id=container_id,
                   container_name=container_name,
                   image=image,
                   port=port,
                   status="running",
                   timestamp=time.time())
    
    print("\n☸️ Kubernetes Operations")
    print("-" * 25)
    
    # Simulate Kubernetes operations
    k8s_operations = [
        ("pod_creation", "web-app-pod"),
        ("service_exposure", "web-app-service"),
        ("config_map_update", "app-config"),
        ("secret_rotation", "database-secret"),
        ("ingress_configuration", "web-ingress")
    ]
    
    for operation_name, resource_name in k8s_operations:
        logger.info("KUBERNETES", f"K8s {operation_name}",
                   operation_name=operation_name,
                   resource_name=resource_name,
                   namespace="default",
                   cluster="production-cluster",
                   timestamp=time.time())
    
    print("\n📈 Auto Scaling")
    print("-" * 15)
    
    # Simulate auto scaling
    scaling_events = [
        ("scale_up", "web-app", 3, 5),
        ("scale_down", "api-service", 4, 2),
        ("scale_up", "cache", 2, 4),
        ("scale_down", "monitoring", 3, 1)
    ]
    
    for event_type, service_name, old_replicas, new_replicas in scaling_events:
        logger.info("SCALING", f"Auto scaling {event_type}",
                   event_type=event_type,
                   service_name=service_name,
                   old_replicas=old_replicas,
                   new_replicas=new_replicas,
                   trigger="cpu_usage" if "up" in event_type else "low_traffic",
                   timestamp=time.time())
    
    print("\n🚀 Cloud Deployments")
    print("-" * 20)
    
    # Simulate cloud deployments
    cloud_providers = ["AWS", "GCP", "Azure"]
    deployment_types = ["blue_green", "rolling", "canary"]
    
    for provider in cloud_providers:
        for deployment_type in deployment_types:
            simulate_cloud_operation(logger, f"{deployment_type}_deployment", provider)
    
    print("\n🔧 Infrastructure as Code")
    print("-" * 25)
    
    # Simulate IaC operations
    iac_operations = [
        ("terraform_apply", "AWS", "vpc_creation"),
        ("terraform_apply", "AWS", "ec2_instances"),
        ("terraform_apply", "GCP", "compute_engine"),
        ("terraform_apply", "Azure", "virtual_machines")
    ]
    
    for operation_name, provider, resource_type in iac_operations:
        logger.info("CLOUD", f"IaC {operation_name}",
                   operation_name=operation_name,
                   cloud_provider=provider,
                   resource_type=resource_type,
                   state_file="terraform.tfstate",
                   timestamp=time.time())
    
    print("\n🔄 CI/CD Pipeline")
    print("-" * 20)
    
    # Simulate CI/CD pipeline
    pipeline_stages = [
        ("code_commit", "feature/new-api"),
        ("build", "docker_image"),
        ("test", "unit_tests"),
        ("security_scan", "vulnerability_check"),
        ("deploy_staging", "staging_environment"),
        ("deploy_production", "production_environment")
    ]
    
    for stage_name, stage_description in pipeline_stages:
        logger.info("DEPLOYMENT", f"CI/CD {stage_name}",
                   stage_name=stage_name,
                   stage_description=stage_description,
                   pipeline_id="pipeline_001",
                   build_number=random.randint(100, 999),
                   status="success",
                   timestamp=time.time())
    
    print("\n📊 Cloud Monitoring")
    print("-" * 20)
    
    # Simulate cloud monitoring
    cloud_metrics = [
        ("cpu_utilization", "EC2", 75.5),
        ("memory_usage", "RDS", 65.2),
        ("network_io", "ELB", 1024.5),
        ("disk_usage", "EBS", 85.3),
        ("request_count", "API Gateway", 1500)
    ]
    
    for metric_name, service, value in cloud_metrics:
        logger.info("CLOUD", f"Cloud metric: {metric_name}",
                   metric_name=metric_name,
                   service=service,
                   value=f"{value:.1f}",
                   unit="%" if "utilization" in metric_name or "usage" in metric_name else "MB/s" if "io" in metric_name else "requests",
                   cloud_provider="AWS",
                   region="us-east-1",
                   timestamp=time.time())
    
    print("\n🔐 Cloud Security")
    print("-" * 20)
    
    # Simulate cloud security events
    security_events = [
        ("access_denied", "unauthorized_api_call"),
        ("security_group_update", "firewall_rule_modified"),
        ("certificate_rotation", "ssl_cert_renewed"),
        ("encryption_enabled", "data_at_rest_encrypted"),
        ("compliance_check", "gdpr_compliance_verified")
    ]
    
    for event_type, description in security_events:
        logger.info("CLOUD", f"Security event: {event_type}",
                   event_type=event_type,
                   description=description,
                   severity="medium",
                   cloud_provider="AWS",
                   timestamp=time.time())
    
    print("\n💰 Cost Management")
    print("-" * 20)
    
    # Simulate cost management
    cost_metrics = [
        ("compute_cost", "EC2", 1250.50),
        ("storage_cost", "S3", 85.25),
        ("network_cost", "CloudFront", 45.75),
        ("database_cost", "RDS", 320.00),
        ("monitoring_cost", "CloudWatch", 15.50)
    ]
    
    for cost_type, service, amount in cost_metrics:
        logger.info("CLOUD", f"Cost metric: {cost_type}",
                   cost_type=cost_type,
                   service=service,
                   amount=f"${amount:.2f}",
                   currency="USD",
                   period="monthly",
                   cloud_provider="AWS",
                   timestamp=time.time())
    
    print("\n🌐 Multi-Cloud Operations")
    print("-" * 25)
    
    # Simulate multi-cloud operations
    multi_cloud_operations = [
        ("load_balancing", "AWS", "GCP"),
        ("data_sync", "Azure", "AWS"),
        ("disaster_recovery", "GCP", "Azure"),
        ("hybrid_deployment", "on_premise", "AWS")
    ]
    
    for operation_name, source, target in multi_cloud_operations:
        logger.info("CLOUD", f"Multi-cloud {operation_name}",
                   operation_name=operation_name,
                   source_provider=source,
                   target_provider=target,
                   latency=random.uniform(50, 200),
                   bandwidth=random.uniform(100, 1000),
                   timestamp=time.time())
    
    print("\n✅ Cloud native demo completed!")
    print("📝 Check the logs/cloud/ directory for cloud logs")
    
    # Show cloud native summary
    print("\n📊 Cloud Native Summary:")
    print("-" * 30)
    print(f"• Containers deployed: {len(containers)}")
    print(f"• Kubernetes operations: {len(k8s_operations)}")
    print(f"• Scaling events: {len(scaling_events)}")
    print(f"• Cloud providers: {len(cloud_providers)}")
    print(f"• Deployment types: {len(deployment_types)}")
    print(f"• Pipeline stages: {len(pipeline_stages)}")
    print(f"• Security events: {len(security_events)}")

if __name__ == "__main__":
    main() 