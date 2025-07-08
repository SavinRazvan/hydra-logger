#!/usr/bin/env python3
"""
17 - Database Logging

Demonstrates logging events to a database (simulated with SQL statements).
"""
import time
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

def log_to_db(logger, event, **fields):
    # Simulate DB log by printing SQL
    sql = f"INSERT INTO logs (event, {', '.join(fields.keys())}) VALUES ('{event}', {', '.join(repr(v) for v in fields.values())});"
    logger.info("DB", sql)

def main():
    print("🗄️ Database Logging Demo\n" + "="*40)
    config = LoggingConfig(layers={
        "DB": LogLayer(
            level="INFO",
            destinations=[LogDestination(type="file", path="logs/database_logging/db.log", format="text")]
        )
    })
    logger = HydraLogger(config)
    # Simulate DB log events
    log_to_db(logger, "user_login", user_id=123, status="success")
    log_to_db(logger, "order_created", order_id=456, amount=99.99)
    log_to_db(logger, "error", code=500, message="Internal Server Error")
    print("\n✅ Database logging demo complete! Check logs/database_logging/db.log.")

if __name__ == "__main__":
    main() 