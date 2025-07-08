#!/usr/bin/env python3
"""
19 - Monitoring Integration

Demonstrates logging metrics/events in a format suitable for monitoring tools.
"""
import time
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

def main():
    print("📈 Monitoring Integration Demo\n" + "="*40)
    config = LoggingConfig(layers={
        "MONITOR": LogLayer(
            level="INFO",
            destinations=[LogDestination(type="file", path="logs/monitoring_integration/metrics.prom", format="text")]
        )
    })
    logger = HydraLogger(config)
    # Simulate Prometheus/Datadog metrics
    logger.info("MONITOR", "http_requests_total{method='GET',code='200'} 1027")
    logger.info("MONITOR", "memory_usage_bytes 524288000")
    logger.info("MONITOR", "custom_metric{label='value'} 42")
    print("\n✅ Monitoring integration demo complete! Check logs/monitoring_integration/metrics.prom.")

if __name__ == "__main__":
    main() 