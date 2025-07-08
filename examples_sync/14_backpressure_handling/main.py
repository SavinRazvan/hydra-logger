#!/usr/bin/env python3
"""
14 - Backpressure Handling

Demonstrates logger behavior when log production exceeds processing speed (backpressure).
"""
import threading
import time
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

def burst_logger(logger, n):
    for i in range(n):
        logger.info("BACKPRESSURE", f"Burst log {i+1}")
        # No sleep: simulate burst

def main():
    print("💥 Backpressure Handling Demo\n" + "="*40)
    config = LoggingConfig(layers={
        "BACKPRESSURE": LogLayer(
            level="INFO",
            destinations=[LogDestination(type="file", path="logs/backpressure/burst.log", format="text")]
        )
    })
    logger = HydraLogger(config)
    # Simulate a burst from multiple threads
    threads = []
    for _ in range(5):
        t = threading.Thread(target=burst_logger, args=(logger, 100))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    print("\n✅ Backpressure demo complete! Check logs/backpressure/burst.log.")

if __name__ == "__main__":
    main() 