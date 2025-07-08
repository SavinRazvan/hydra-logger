#!/usr/bin/env python3
"""
16 - Cloud Integration

Demonstrates logging events as if exporting to a cloud logging service.
"""
import time
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

def main():
    print("☁️ Cloud Integration Demo\n" + "="*40)
    config = LoggingConfig(layers={
        "CLOUD": LogLayer(
            level="INFO",
            destinations=[LogDestination(type="file", path="logs/cloud_integration/cloud.log", format="json")]
        )
    })
    logger = HydraLogger(config)
    # Simulate cloud log events
    logger.info("CLOUD", "User login event", user_id="123", region="us-east-1", cloud="AWS")
    logger.info("CLOUD", "Resource created", resource_type="VM", resource_id="vm-001", cloud="GCP")
    logger.info("CLOUD", "Alert triggered", severity="high", message="CPU usage > 90%", cloud="Azure")
    print("\n✅ Cloud integration demo complete! Check logs/cloud_integration/cloud.log.")

if __name__ == "__main__":
    main() 