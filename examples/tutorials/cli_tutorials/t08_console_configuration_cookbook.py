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

import os
import sys

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_logger

_TUTORIALS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TUTORIALS_ROOT not in sys.path:
    sys.path.insert(0, _TUTORIALS_ROOT)

from shared.cli_tutorial_footer import print_cli_tutorial_footer


def scenario_colored_plaintext() -> None:
    config = LoggingConfig(
        base_log_dir="examples/logs",
        log_dir_name="cli-tutorials",
        layers={
            "app": LogLayer(
                destinations=[
                    LogDestination(type="console", format="plain-text", use_colors=True),
                    LogDestination(
                        type="file",
                        path="t08_colored_plaintext",
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
        base_log_dir="examples/logs",
        log_dir_name="cli-tutorials",
        layers={
            "app": LogLayer(
                destinations=[
                    LogDestination(type="console", format="plain-text", use_colors=False),
                    LogDestination(
                        type="file",
                        path="t08_no_color",
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
        base_log_dir="examples/logs",
        log_dir_name="cli-tutorials",
        layers={
            "api": LogLayer(
                destinations=[
                    LogDestination(type="console", format="colored", use_colors=True),
                    LogDestination(
                        type="file",
                        path="t08_layer_api",
                        format="json-lines",
                    ),
                ]
            ),
            "audit": LogLayer(
                destinations=[
                    LogDestination(type="console", format="plain-text", use_colors=False),
                    LogDestination(
                        type="file",
                        path="t08_layer_audit",
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
    print_cli_tutorial_footer(
        code="T08",
        title="Console configuration cookbook",
        console="Several Hydra console blocks above (colors on/off + per-layer policies).",
        artifacts=[
            "examples/logs/cli-tutorials/t08_colored_plaintext.jsonl",
            "examples/logs/cli-tutorials/t08_no_color.log",
            "examples/logs/cli-tutorials/t08_layer_api.jsonl",
            "examples/logs/cli-tutorials/t08_layer_audit.log",
        ],
        takeaway="Console format and use_colors are per-destination; files mirror each scenario.",
        notebook_rel="examples/tutorials/notebooks/t08_console_configuration_cookbook.ipynb",
    )


if __name__ == "__main__":
    main()
