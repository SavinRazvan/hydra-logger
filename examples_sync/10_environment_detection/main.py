#!/usr/bin/env python3
"""
10 - Environment Detection

This example demonstrates environment detection with Hydra-Logger.
Shows how to automatically configure logging based on environment.
"""

from hydra_logger import HydraLogger
import os
import platform
import socket

def detect_environment():
    """Detect the current environment."""
    env_info = {
        'platform': platform.system(),
        'hostname': socket.gethostname(),
        'python_version': platform.python_version(),
        'environment': os.environ.get('ENVIRONMENT', 'development'),
        'is_docker': os.path.exists('/.dockerenv'),
        'is_kubernetes': 'KUBERNETES_SERVICE_HOST' in os.environ,
        'is_aws': 'AWS_REGION' in os.environ,
        'is_gcp': 'GOOGLE_CLOUD_PROJECT' in os.environ,
        'is_azure': 'AZURE_CLIENT_ID' in os.environ
    }
    return env_info

def main():
    """Demonstrate environment detection."""
    
    print("🌍 Environment Detection Demo")
    print("=" * 40)
    
    # Detect current environment
    env_info = detect_environment()
    
    print(f"\n🔍 Detected Environment:")
    print(f"  Platform: {env_info['platform']}")
    print(f"  Hostname: {env_info['hostname']}")
    print(f"  Python Version: {env_info['python_version']}")
    print(f"  Environment: {env_info['environment']}")
    print(f"  Docker: {env_info['is_docker']}")
    print(f"  Kubernetes: {env_info['is_kubernetes']}")
    print(f"  AWS: {env_info['is_aws']}")
    print(f"  GCP: {env_info['is_gcp']}")
    print(f"  Azure: {env_info['is_azure']}")
    
    # Create environment-specific configuration
    if env_info['environment'] == 'production':
        # Production configuration
        logger = HydraLogger(
            auto_detect=True,
            enable_performance_monitoring=True
        )
        print("\n🏭 Production Configuration Applied")
    elif env_info['is_docker'] or env_info['is_kubernetes']:
        # Container configuration
        logger = HydraLogger(
            auto_detect=True,
            enable_performance_monitoring=True
        )
        print("\n🐳 Container Configuration Applied")
    elif env_info['is_aws'] or env_info['is_gcp'] or env_info['is_azure']:
        # Cloud configuration
        logger = HydraLogger(
            auto_detect=True,
            enable_performance_monitoring=True
        )
        print("\n☁️ Cloud Configuration Applied")
    else:
        # Development configuration
        logger = HydraLogger(
            auto_detect=True,
            enable_performance_monitoring=False
        )
        print("\n🛠️ Development Configuration Applied")
    
    print("\n📝 Environment-Specific Logging")
    print("-" * 35)
    
    # Log environment information
    logger.info("ENV", "Environment detection completed",
                platform=env_info['platform'],
                hostname=env_info['hostname'],
                environment=env_info['environment'],
                is_container=env_info['is_docker'] or env_info['is_kubernetes'],
                is_cloud=env_info['is_aws'] or env_info['is_gcp'] or env_info['is_azure'])
    
    # Simulate different environment scenarios
    print("\n🌍 Environment Scenarios")
    print("-" * 25)
    
    # Scenario 1: Development
    print("\n🛠️ Scenario 1: Development Environment")
    os.environ['ENVIRONMENT'] = 'development'
    dev_logger = HydraLogger(auto_detect=True)
    dev_logger.info("DEV", "Development server started", port=8000, debug=True)
    dev_logger.debug("DEV", "Debug information enabled")
    
    # Scenario 2: Production
    print("\n🏭 Scenario 2: Production Environment")
    os.environ['ENVIRONMENT'] = 'production'
    prod_logger = HydraLogger(auto_detect=True)
    prod_logger.info("PROD", "Production server started", port=80, ssl=True)
    prod_logger.warning("PROD", "High memory usage detected", memory_percent=85)
    
    # Scenario 3: Docker
    print("\n🐳 Scenario 3: Docker Environment")
    os.environ['ENVIRONMENT'] = 'docker'
    docker_logger = HydraLogger(auto_detect=True)
    docker_logger.info("DOCKER", "Container started", container_id="abc123", image="app:v1.0")
    docker_logger.info("DOCKER", "Health check passed", status="healthy")
    
    # Scenario 4: Kubernetes
    print("\n☸️ Scenario 4: Kubernetes Environment")
    os.environ['ENVIRONMENT'] = 'kubernetes'
    os.environ['KUBERNETES_SERVICE_HOST'] = '10.0.0.1'
    k8s_logger = HydraLogger(auto_detect=True)
    k8s_logger.info("K8S", "Pod started", pod_name="app-pod", namespace="default")
    k8s_logger.info("K8S", "Service discovery", service="app-service", port=8080)
    
    # Scenario 5: AWS
    print("\n☁️ Scenario 5: AWS Environment")
    os.environ['ENVIRONMENT'] = 'aws'
    os.environ['AWS_REGION'] = 'us-east-1'
    aws_logger = HydraLogger(auto_detect=True)
    aws_logger.info("AWS", "EC2 instance started", instance_id="i-123456", region="us-east-1")
    aws_logger.info("AWS", "CloudWatch metrics", metric="CPUUtilization", value=45.2)
    
    # Scenario 6: GCP
    print("\n☁️ Scenario 6: GCP Environment")
    os.environ['ENVIRONMENT'] = 'gcp'
    os.environ['GOOGLE_CLOUD_PROJECT'] = 'my-project'
    gcp_logger = HydraLogger(auto_detect=True)
    gcp_logger.info("GCP", "Compute instance started", instance_name="app-instance", zone="us-central1-a")
    gcp_logger.info("GCP", "Stackdriver logging", log_level="INFO", project="my-project")
    
    # Scenario 7: Azure
    print("\n☁️ Scenario 7: Azure Environment")
    os.environ['ENVIRONMENT'] = 'azure'
    os.environ['AZURE_CLIENT_ID'] = 'azure-client-id'
    azure_logger = HydraLogger(auto_detect=True)
    azure_logger.info("AZURE", "VM started", vm_name="app-vm", resource_group="my-rg")
    azure_logger.info("AZURE", "Application Insights", app_name="my-app", instrumentation_key="abc123")
    
    # Environment-specific features
    print("\n⚙️ Environment-Specific Features")
    print("-" * 35)
    
    # Performance monitoring (production/cloud)
    if env_info['environment'] in ['production', 'aws', 'gcp', 'azure']:
        logger.info("PERF", "Performance monitoring enabled",
                   feature="auto_monitoring",
                   interval="60s",
                   metrics=["cpu", "memory", "disk"])
    
    # Security logging (production)
    if env_info['environment'] == 'production':
        logger.info("SECURITY", "Security logging enabled",
                   feature="audit_trail",
                   compliance="SOX",
                   retention="7_years")
    
    # Debug logging (development)
    if env_info['environment'] == 'development':
        logger.debug("DEBUG", "Debug logging enabled",
                   feature="detailed_logging",
                   level="DEBUG",
                   console_output=True)
    
    # Container-specific logging
    if env_info['is_docker'] or env_info['is_kubernetes']:
        logger.info("CONTAINER", "Container-specific logging enabled",
                   feature="structured_logging",
                   format="json",
                   stdout=True)
    
    print("\n✅ Environment detection demo completed!")
    print("📝 Check the logs/ directory for environment-specific logs")
    
    # Show environment summary
    print("\n📊 Environment Summary:")
    print("-" * 25)
    print(f"• Detected Environment: {env_info['environment']}")
    print(f"• Platform: {env_info['platform']}")
    print(f"• Container: {'Yes' if env_info['is_docker'] or env_info['is_kubernetes'] else 'No'}")
    print(f"• Cloud: {'Yes' if env_info['is_aws'] or env_info['is_gcp'] or env_info['is_azure'] else 'No'}")
    
    # Clean up environment variables
    for key in ['ENVIRONMENT', 'KUBERNETES_SERVICE_HOST', 'AWS_REGION', 'GOOGLE_CLOUD_PROJECT', 'AZURE_CLIENT_ID']:
        if key in os.environ:
            del os.environ[key]

if __name__ == "__main__":
    main() 