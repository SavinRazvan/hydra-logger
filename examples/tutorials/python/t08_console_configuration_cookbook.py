#!/usr/bin/env python3
"""
Role: Enterprise onboarding tutorial for console output configuration recipes.
Used By:
 - Engineers following `examples/tutorials/README.md` onboarding tracks.
Depends On:
 - hydra_logger
Notes:
 - Demonstrates console color policies, format switching, and per-layer console behavior.
"""

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_logger


def scenario_colored_plaintext() -> None:
    config = LoggingConfig(
        layers={
            "app": LogLayer(
                destinations=[
                    LogDestination(type="console", format="plain-text", use_colors=True),
                    LogDestination(
                        type="file",
                        path="examples/logs/tutorials/t08_colored_plaintext.jsonl",
                        format="json-lines",
                    ),
                ]
            )
        }
    )
    with create_logger(config, logger_type="sync") as logger:
        logger.info("[T08] colored plaintext console enabled", layer="app")
        logger.warning("[T08] warning with ANSI colors", layer="app")


def scenario_no_color_console() -> None:
    config = LoggingConfig(
        layers={
            "app": LogLayer(
                destinations=[
                    LogDestination(type="console", format="plain-text", use_colors=False),
                    LogDestination(
                        type="file",
                        path="examples/logs/tutorials/t08_no_color.log",
                        format="plain-text",
                    ),
                ]
            )
        }
    )
    with create_logger(config, logger_type="sync") as logger:
        logger.info("[T08] non-color console policy", layer="app")
        logger.error("[T08] deterministic plain-text output", layer="app")


def scenario_layer_specific_console() -> None:
    config = LoggingConfig(
        layers={
            "api": LogLayer(
                destinations=[
                    LogDestination(type="console", format="colored", use_colors=True),
                    LogDestination(
                        type="file",
                        path="examples/logs/tutorials/t08_layer_api.jsonl",
                        format="json-lines",
                    ),
                ]
            ),
            "audit": LogLayer(
                destinations=[
                    LogDestination(type="console", format="plain-text", use_colors=False),
                    LogDestination(
                        type="file",
                        path="examples/logs/tutorials/t08_layer_audit.log",
                        format="plain-text",
                    ),
                ]
            ),
        }
    )
    with create_logger(config, logger_type="sync") as logger:
        logger.info("[T08] api layer uses colored console", layer="api")
        logger.info("[T08] audit layer uses non-colored console", layer="audit")


def main() -> None:
    scenario_colored_plaintext()
    scenario_no_color_console()
    scenario_layer_specific_console()
    print("T08 completed: console configuration cookbook")


if __name__ == "__main__":
    main()
