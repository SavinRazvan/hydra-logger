#!/usr/bin/env python3
"""
13 - High Concurrency Logging

Demonstrates logging from many threads to test thread-safety and log integrity.
"""
import threading
import time
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

def log_worker(logger, thread_id, n):
    for i in range(n):
        logger.info("CONCURRENCY", f"Thread {thread_id} log {i+1}")
        time.sleep(0.01)

def main():
    print("🔀 High Concurrency Logging Demo\n" + "="*40)
    config = LoggingConfig(layers={
        "CONCURRENCY": LogLayer(
            level="INFO",
            destinations=[LogDestination(type="file", path="logs/high_concurrency/threaded.log", format="text")]
        )
    })
    logger = HydraLogger(config)
    threads = []
    for t in range(10):
        thread = threading.Thread(target=log_worker, args=(logger, t+1, 20))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    print("\n✅ High concurrency logging complete! Check logs/high_concurrency/threaded.log.")

if __name__ == "__main__":
    main() 