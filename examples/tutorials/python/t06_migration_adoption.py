#!/usr/bin/env python3
"""
Role: Enterprise onboarding tutorial for migration and adoption strategy.
Used By:
 - Engineers following `examples/tutorials/README.md` onboarding tracks.
Depends On:
 - hydra_logger
 - logging
Notes:
 - Demonstrates side-by-side migration from standard logging to layered Hydra Logger.
"""

import logging

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_logger


def legacy_logger() -> logging.Logger:
    logger = logging.getLogger("legacy-service")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("[legacy] %(levelname)s %(message)s"))
        logger.addHandler(handler)
    return logger


def main() -> None:
    legacy = legacy_logger()
    legacy.info("side-by-side migration started")

    config = LoggingConfig(
        layers={
            "migration": LogLayer(
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/tutorials/t06_migration.jsonl",
                        format="json-lines",
                    )
                ]
            )
        }
    )
    with create_logger(config, logger_type="sync") as logger:
        logger.info("[T06] migrated event written", layer="migration")
        logger.info("[T06] rollback toggle remains available", layer="migration")

    print("T06 completed: migration/adoption")


if __name__ == "__main__":
    main()
