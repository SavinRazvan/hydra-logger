#!/usr/bin/env python3
"""
06 - Log Rotation

This example demonstrates log file rotation with Hydra-Logger.
Shows how to configure automatic log file rotation based on size and time.
"""

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
import time
import os

def main():
    """Demonstrate log file rotation."""
    
    print("🔄 Log Rotation Demo")
    print("=" * 40)
    
    # Create configuration with log rotation
    config = LoggingConfig(
        layers={
            "ROTATION": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/rotation/app.log",
                        max_size="1KB",  # Rotate when file reaches 1KB
                        backup_count=3,   # Keep 3 backup files
                        format="text"
                    )
                ]
            ),
            "TIME_ROTATION": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/rotation/time_based.log",
                        max_size="2KB",
                        backup_count=5,
                        format="text"
                    )
                ]
            ),
            "LARGE_ROTATION": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/rotation/large.log",
                        max_size="5KB",
                        backup_count=10,
                        format="text"
                    )
                ]
            )
        }
    )
    
    # Initialize logger
    logger = HydraLogger(config)
    
    print("\n📝 Generating logs to trigger rotation...")
    print("-" * 40)
    
    # Generate logs to trigger rotation
    for i in range(50):
        # Log with different sizes to trigger rotation
        if i < 20:
            # Small messages for ROTATION layer
            logger.info("ROTATION", f"Message {i+1}: Small log message")
        elif i < 35:
            # Medium messages for TIME_ROTATION layer
            logger.info("TIME_ROTATION", f"Message {i+1}: " + "Medium sized log message " * 5)
        else:
            # Large messages for LARGE_ROTATION layer
            logger.info("LARGE_ROTATION", f"Message {i+1}: " + "Large log message with lots of content " * 10)
        
        # Small delay to see rotation in action
        time.sleep(0.01)
    
    print("\n✅ Log rotation demo completed!")
    print("📝 Check the logs/rotation/ directory for rotated files")
    
    # Show the rotation results
    print("\n📁 Generated Files:")
    print("-" * 20)
    
    rotation_dir = "logs/rotation"
    if os.path.exists(rotation_dir):
        for file in sorted(os.listdir(rotation_dir)):
            file_path = os.path.join(rotation_dir, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                print(f"  {file} ({size} bytes)")
    
    # Show rotation explanation
    print("\n🔄 Rotation Explanation:")
    print("-" * 25)
    print("• app.log: Rotates when file reaches 1KB, keeps 3 backups")
    print("• time_based.log: Rotates when file reaches 2KB, keeps 5 backups")
    print("• large.log: Rotates when file reaches 5KB, keeps 10 backups")
    print("\n• Backup files are named with .1, .2, .3, etc.")
    print("• Oldest backup is deleted when max count is reached")

if __name__ == "__main__":
    main() 