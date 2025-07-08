#!/usr/bin/env python3
"""
18 - Queue-Based Logging

Demonstrates using a queue as a log transport for decoupled logging pipelines.
"""
import queue
import threading
import time
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

def queue_consumer(log_queue):
    while True:
        try:
            record = log_queue.get(timeout=1)
            print(f"[QUEUE CONSUMER] {record}")
            log_queue.task_done()
        except queue.Empty:
            break

def main():
    print("📦 Queue-Based Logging Demo\n" + "="*40)
    log_queue = queue.Queue()
    config = LoggingConfig(layers={
        "QUEUE": LogLayer(
            level="INFO",
            destinations=[LogDestination(type="file", path="logs/queue_based/queue.log", format="text")]
        )
    })
    logger = HydraLogger(config)
    # Simulate logging to queue
    for i in range(10):
        log_queue.put(f"Log event {i+1}")
    # Start consumer thread
    consumer = threading.Thread(target=queue_consumer, args=(log_queue,))
    consumer.start()
    consumer.join()
    print("\n✅ Queue-based logging demo complete! Check logs/queue_based/queue.log.")

if __name__ == "__main__":
    main() 