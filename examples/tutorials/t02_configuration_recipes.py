#!/usr/bin/env python3
"""
Role: Enterprise onboarding tutorial for configuration recipe patterns.
Used By:
 - Engineers following `examples/tutorials/README.md` onboarding tracks.
Depends On:
 - os
 - hydra_logger
Notes:
 - Demonstrates destination, format, and environment-driven configuration recipes.
"""

import os

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_logger


def build_recipe_config() -> LoggingConfig:
    log_level = os.getenv("HYDRA_TUTORIAL_LEVEL", "INFO")
    return LoggingConfig(
        default_level=log_level,
        layers={
            "api": LogLayer(
                level=log_level,
                destinations=[
                    LogDestination(type="console", format="colored", use_colors=True),
                    LogDestination(
                        type="file",
                        path="logs/examples/tutorials/t02_api.jsonl",
                        format="json-lines",
                    ),
                ],
            ),
            "audit": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/examples/tutorials/t02_audit.log",
                        format="plain-text",
                    ),
                ],
            ),
        },
    )


def main() -> None:
    config = build_recipe_config()
    with create_logger(config, logger_type="sync") as logger:
        logger.info("[T02] API request accepted", layer="api")
        logger.warning("[T02] API latency elevated", layer="api")
        logger.info("[T02] Audit event persisted", layer="audit")

    print("T02 completed: configuration recipes")


if __name__ == "__main__":
    main()
