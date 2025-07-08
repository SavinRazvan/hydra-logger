#!/usr/bin/env python3
"""
07 - Performance Monitoring

This example demonstrates performance monitoring with Hydra-Logger.
Shows how to track and log performance metrics.
"""

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
import time
import random
import psutil
import threading
import os

def simulate_work(duration):
    """Simulate work for a given duration."""
    time.sleep(duration)

def get_system_metrics():
    """Get current system metrics."""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    return {
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'memory_used_mb': memory.used / (1024 * 1024),
        'disk_percent': disk.percent,
        'disk_free_gb': disk.free / (1024 * 1024 * 1024)
    }

def main():
    """Demonstrate performance monitoring."""
    
    print("📊 Performance Monitoring Demo")
    print("=" * 40)
    
    # Create configuration with performance monitoring
    config = LoggingConfig(
        layers={
            "PERF": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/performance/metrics.json",
                        format="json"
                    ),
                    LogDestination(
                        type="file",
                        path="logs/performance/summary.csv",
                        format="csv"
                    )
                ]
            ),
            "SYSTEM": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/performance/system.log",
                        format="text"
                    )
                ]
            ),
            "OPERATIONS": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/performance/operations.log",
                        format="text"
                    )
                ]
            )
        }
    )
    
    # Initialize logger
    logger = HydraLogger(config)
    
    print("\n🔄 Starting performance monitoring...")
    print("-" * 40)
    
    # Monitor system performance
    print("\n📈 System Performance Monitoring")
    print("-" * 30)
    
    for i in range(5):
        metrics = get_system_metrics()
        
        logger.info("SYSTEM", "System metrics recorded",
                   cpu_percent=metrics['cpu_percent'],
                   memory_percent=metrics['memory_percent'],
                   memory_used_mb=f"{metrics['memory_used_mb']:.1f}",
                   disk_percent=metrics['disk_percent'],
                   disk_free_gb=f"{metrics['disk_free_gb']:.1f}")
        
        logger.info("PERF", "Performance snapshot",
                   timestamp=time.time(),
                   cpu_percent=metrics['cpu_percent'],
                   memory_percent=metrics['memory_percent'],
                   disk_percent=metrics['disk_percent'])
        
        time.sleep(1)
    
    # Simulate different operations with performance tracking
    print("\n⚡ Operation Performance Tracking")
    print("-" * 30)
    
    operations = [
        ("Database Query", 0.05, 0.1),
        ("API Request", 0.1, 0.2),
        ("File Processing", 0.2, 0.5),
        ("Data Analysis", 0.5, 1.0),
        ("Report Generation", 1.0, 2.0)
    ]
    
    for operation_name, min_duration, max_duration in operations:
        start_time = time.time()
        
        # Simulate operation
        duration = random.uniform(min_duration, max_duration)
        simulate_work(duration)
        
        actual_duration = (time.time() - start_time) * 1000
        
        # Log operation performance
        logger.info("OPERATIONS", f"{operation_name} completed",
                   operation=operation_name,
                   duration_ms=f"{actual_duration:.2f}",
                   status="success")
        
        logger.info("PERF", "Operation performance",
                   operation=operation_name,
                   duration_ms=f"{actual_duration:.2f}",
                   timestamp=time.time())
        
        print(f"  ✅ {operation_name}: {actual_duration:.2f}ms")
    
    # Simulate concurrent operations
    print("\n🔄 Concurrent Operations")
    print("-" * 25)
    
    def concurrent_operation(operation_id):
        start_time = time.time()
        duration = random.uniform(0.1, 0.3)
        simulate_work(duration)
        actual_duration = (time.time() - start_time) * 1000
        
        logger.info("OPERATIONS", f"Concurrent operation {operation_id} completed",
                   operation_id=operation_id,
                   duration_ms=f"{actual_duration:.2f}",
                   thread_id=threading.current_thread().ident)
        
        logger.info("PERF", "Concurrent operation performance",
                   operation_id=operation_id,
                   duration_ms=f"{actual_duration:.2f}",
                   thread_id=threading.current_thread().ident)
    
    # Start concurrent operations
    threads = []
    for i in range(3):
        thread = threading.Thread(target=concurrent_operation, args=(i+1,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Final performance summary
    print("\n📊 Performance Summary")
    print("-" * 20)
    
    final_metrics = get_system_metrics()
    logger.info("SYSTEM", "Final system metrics",
               cpu_percent=final_metrics['cpu_percent'],
               memory_percent=final_metrics['memory_percent'],
               memory_used_mb=f"{final_metrics['memory_used_mb']:.1f}",
               disk_percent=final_metrics['disk_percent'],
               disk_free_gb=f"{final_metrics['disk_free_gb']:.1f}")
    
    logger.info("PERF", "Performance monitoring completed",
               total_operations=len(operations) + 3,
               monitoring_duration="5 seconds",
               final_cpu_percent=final_metrics['cpu_percent'],
               final_memory_percent=final_metrics['memory_percent'])
    
    print("\n✅ Performance monitoring demo completed!")
    print("📝 Check the logs/performance/ directory for detailed metrics")
    
    # Show generated files
    print("\n📁 Generated Files:")
    print("-" * 20)
    perf_dir = "logs/performance"
    if os.path.exists(perf_dir):
        for file in sorted(os.listdir(perf_dir)):
            file_path = os.path.join(perf_dir, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                print(f"  {file} ({size} bytes)")

if __name__ == "__main__":
    main() 