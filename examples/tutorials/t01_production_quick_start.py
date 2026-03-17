#!/usr/bin/env python3
"""
Role: Enterprise onboarding tutorial for production quick start logger patterns.
Used By:
 - Engineers following `examples/tutorials/README.md` onboarding tracks.
Depends On:
 - asyncio
 - hydra_logger
Notes:
 - Demonstrates sync, async, and composite patterns with production-safe defaults.
"""

import asyncio

from hydra_logger import (
    LogDestination,
    LoggingConfig,
    LogLayer,
    create_async_logger,
    create_composite_logger,
    create_logger,
)


def build_quick_start_config() -> LoggingConfig:
    return LoggingConfig(
        default_level="INFO",
        layers={
            "app": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(type="console", format="plain-text", use_colors=True),
                    LogDestination(
                        type="file",
                        path="logs/examples/tutorials/t01_sync.jsonl",
                        format="json-lines",
                    ),
                ],
            )
        },
    )


async def run_async_track(config: LoggingConfig) -> None:
    async with create_async_logger(config, name="tutorial-async") as logger:
        await logger.info("[T01] async logger initialized", layer="app")


def main() -> None:
    config = build_quick_start_config()

    with create_logger(config, logger_type="sync") as logger:
        logger.info("[T01] sync logger initialized", layer="app")

    asyncio.run(run_async_track(config))

    with create_composite_logger(config, name="tutorial-composite") as logger:
        logger.info("[T01] composite logger initialized", layer="app")

    print("T01 completed: production quick start")


if __name__ == "__main__":
    main()
