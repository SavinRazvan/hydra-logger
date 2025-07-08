#!/usr/bin/env python3
"""
17 - Real-Time Monitoring

This example demonstrates real-time monitoring with Hydra-Logger.
Shows how to log real-time system metrics and alerts.
"""

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
import time
import random
import threading

def simulate_system_metrics():
    """Simulate system metrics."""
    return {
        'cpu_usage': random.uniform(20, 80),
        'memory_usage': random.uniform(30, 90),
        'disk_usage': random.uniform(40, 95),
        'network_io': random.uniform(10, 100),
        'active_connections': random.randint(50, 500),
        'response_time': random.uniform(50, 200)
    }

def simulate_alert(alert_type, severity, message):
    """Simulate an alert."""
    return {
        'alert_type': alert_type,
        'severity': severity,
        'message': message,
        'timestamp': time.time(),
        'alert_id': f"alert_{int(time.time())}"
    }

def main():
    """Demonstrate real-time monitoring."""
    
    print("📡 Real-Time Monitoring Demo")
    print("=" * 40)
    
    # Create real-time monitoring configuration
    config = LoggingConfig(
        layers={
            "METRICS": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/realtime/metrics.json",
                        format="json"
                    )
                ]
            ),
            "ALERTS": LogLayer(
                level="WARNING",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/realtime/alerts.log",
                        format="text"
                    ),
                    LogDestination(
                        type="console",
                        level="ERROR",
                        format="text"
                    )
                ]
            ),
            "PERFORMANCE": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/realtime/performance.csv",
                        format="csv"
                    )
                ]
            ),
            "HEALTH": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/realtime/health.log",
                        format="json"
                    )
                ]
            )
        }
    )
    
    # Initialize logger
    logger = HydraLogger(config)
    
    print("\n📊 System Metrics Monitoring")
    print("-" * 30)
    
    # Simulate continuous system monitoring
    monitoring_duration = 10  # seconds
    start_time = time.time()
    
    while time.time() - start_time < monitoring_duration:
        metrics = simulate_system_metrics()
        
        # Log system metrics
        logger.info("METRICS", "System metrics recorded",
                   cpu_usage=f"{metrics['cpu_usage']:.1f}%",
                   memory_usage=f"{metrics['memory_usage']:.1f}%",
                   disk_usage=f"{metrics['disk_usage']:.1f}%",
                   network_io=f"{metrics['network_io']:.1f} MB/s",
                   active_connections=metrics['active_connections'],
                   response_time=f"{metrics['response_time']:.1f}ms")
        
        # Log performance metrics
        logger.info("PERFORMANCE", "Performance metrics",
                   timestamp=time.time(),
                   cpu_usage=f"{metrics['cpu_usage']:.1f}",
                   memory_usage=f"{metrics['memory_usage']:.1f}",
                   disk_usage=f"{metrics['disk_usage']:.1f}",
                   network_io=f"{metrics['network_io']:.1f}")
        
        # Check for alerts
        if metrics['cpu_usage'] > 80:
            alert = simulate_alert("high_cpu", "warning", f"CPU usage is {metrics['cpu_usage']:.1f}%")
            logger.warning("ALERTS", "High CPU usage detected",
                          alert_id=alert['alert_id'],
                          cpu_usage=f"{metrics['cpu_usage']:.1f}%",
                          threshold="80%",
                          action="scale_up_resources")
        
        if metrics['memory_usage'] > 85:
            alert = simulate_alert("high_memory", "critical", f"Memory usage is {metrics['memory_usage']:.1f}%")
            logger.error("ALERTS", "Critical memory usage",
                        alert_id=alert['alert_id'],
                        memory_usage=f"{metrics['memory_usage']:.1f}%",
                        threshold="85%",
                        action="immediate_attention_required")
        
        if metrics['response_time'] > 150:
            alert = simulate_alert("slow_response", "warning", f"Response time is {metrics['response_time']:.1f}ms")
            logger.warning("ALERTS", "Slow response time detected",
                          alert_id=alert['alert_id'],
                          response_time=f"{metrics['response_time']:.1f}ms",
                          threshold="150ms",
                          action="optimize_performance")
        
        # Log health status
        health_status = "healthy" if metrics['cpu_usage'] < 70 and metrics['memory_usage'] < 80 else "degraded"
        logger.info("HEALTH", "System health check",
                   status=health_status,
                   cpu_usage=f"{metrics['cpu_usage']:.1f}%",
                   memory_usage=f"{metrics['memory_usage']:.1f}%",
                   disk_usage=f"{metrics['disk_usage']:.1f}%")
        
        time.sleep(1)  # Monitor every second
    
    print("\n🚨 Alert Simulation")
    print("-" * 20)
    
    # Simulate various alerts
    alerts = [
        ("service_down", "critical", "Database service is down"),
        ("disk_full", "critical", "Disk space is 95% full"),
        ("network_timeout", "warning", "Network timeout detected"),
        ("security_breach", "critical", "Unauthorized access detected"),
        ("backup_failed", "warning", "Scheduled backup failed"),
        ("certificate_expiry", "warning", "SSL certificate expires in 30 days"),
        ("high_error_rate", "critical", "Error rate is 15%"),
        ("resource_exhaustion", "critical", "System resources exhausted")
    ]
    
    for alert_type, severity, message in alerts:
        alert = simulate_alert(alert_type, severity, message)
        
        if severity == "critical":
            logger.error("ALERTS", f"Critical alert: {message}",
                        alert_id=alert['alert_id'],
                        alert_type=alert_type,
                        severity=severity,
                        timestamp=alert['timestamp'],
                        action="immediate_response_required")
        else:
            logger.warning("ALERTS", f"Warning alert: {message}",
                          alert_id=alert['alert_id'],
                          alert_type=alert_type,
                          severity=severity,
                          timestamp=alert['timestamp'],
                          action="monitor_closely")
    
    print("\n🔍 Service Health Monitoring")
    print("-" * 30)
    
    # Simulate service health checks
    services = [
        ("web_server", "healthy", 200),
        ("database", "healthy", 200),
        ("cache", "degraded", 503),
        ("api_gateway", "healthy", 200),
        ("message_queue", "unhealthy", 500)
    ]
    
    for service_name, status, response_code in services:
        logger.info("HEALTH", "Service health check",
                   service=service_name,
                   status=status,
                   response_code=response_code,
                   response_time=random.uniform(10, 100),
                   timestamp=time.time())
        
        if status != "healthy":
            logger.warning("ALERTS", f"Service {service_name} is {status}",
                          service=service_name,
                          status=status,
                          response_code=response_code,
                          action="investigate_service")
    
    print("\n📈 Performance Trending")
    print("-" * 25)
    
    # Simulate performance trending
    for i in range(5):
        # Simulate trending metrics
        cpu_trend = 60 + i * 5  # Increasing trend
        memory_trend = 70 + i * 3  # Increasing trend
        response_trend = 100 + i * 10  # Increasing trend
        
        logger.info("PERFORMANCE", "Performance trend analysis",
                   period=f"period_{i+1}",
                   cpu_trend=f"{cpu_trend:.1f}%",
                   memory_trend=f"{memory_trend:.1f}%",
                   response_trend=f"{response_trend:.1f}ms",
                   trend_direction="increasing" if i > 0 else "stable")
        
        # Alert on increasing trends
        if cpu_trend > 75:
            logger.warning("ALERTS", "CPU usage trending upward",
                          current_usage=f"{cpu_trend:.1f}%",
                          trend="increasing",
                          action="plan_capacity_increase")
    
    print("\n🌐 Network Monitoring")
    print("-" * 25)
    
    # Simulate network monitoring
    network_metrics = [
        ("bandwidth_usage", 75.5),
        ("packet_loss", 0.2),
        ("latency", 45.3),
        ("throughput", 1024.5),
        ("connection_count", 250)
    ]
    
    for metric_name, value in network_metrics:
        logger.info("METRICS", "Network metric recorded",
                   metric=metric_name,
                   value=f"{value:.1f}",
                   unit="%" if "usage" in metric_name or "loss" in metric_name else "ms" if "latency" in metric_name else "MB/s" if "throughput" in metric_name else "connections",
                   timestamp=time.time())
        
        # Alert on network issues
        if "packet_loss" in metric_name and value > 0.1:
            logger.warning("ALERTS", "High packet loss detected",
                          packet_loss=f"{value:.1f}%",
                          threshold="0.1%",
                          action="check_network_connectivity")
    
    print("\n📊 Real-Time Dashboard")
    print("-" * 25)
    
    # Simulate dashboard metrics
    dashboard_metrics = {
        "active_users": random.randint(100, 1000),
        "requests_per_second": random.randint(50, 200),
        "error_rate": random.uniform(0.1, 2.0),
        "uptime": 99.95,
        "last_deployment": "2025-01-27T10:30:00Z"
    }
    
    for metric_name, value in dashboard_metrics.items():
        logger.info("METRICS", "Dashboard metric updated",
                   metric=metric_name,
                   value=value,
                   unit="users" if "users" in metric_name else "req/s" if "requests" in metric_name else "%" if "rate" in metric_name or "uptime" in metric_name else "timestamp",
                   timestamp=time.time())
    
    print("\n✅ Real-time monitoring demo completed!")
    print("📝 Check the logs/realtime/ directory for monitoring logs")
    
    # Show monitoring summary
    print("\n📊 Monitoring Summary:")
    print("-" * 25)
    print(f"• Monitoring duration: {monitoring_duration} seconds")
    print(f"• Alerts generated: {len(alerts)}")
    print(f"• Services monitored: {len(services)}")
    print(f"• Network metrics: {len(network_metrics)}")
    print(f"• Dashboard metrics: {len(dashboard_metrics)}")

if __name__ == "__main__":
    main() 