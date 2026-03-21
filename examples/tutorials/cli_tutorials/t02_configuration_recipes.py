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
import sys

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_logger

_TUTORIALS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TUTORIALS_ROOT not in sys.path:
    sys.path.insert(0, _TUTORIALS_ROOT)

from shared.cli_tutorial_footer import print_cli_tutorial_footer


def build_recipe_config() -> LoggingConfig:
    log_level = os.getenv("HYDRA_TUTORIAL_LEVEL", "INFO")
    return LoggingConfig(
        base_log_dir="examples/logs",
        log_dir_name="cli-tutorials",
        default_level=log_level,
        layers={
            "api": LogLayer(
                level=log_level,
                destinations=[
                    LogDestination(type="console", format="colored", use_colors=True),
                    LogDestination(
                        type="file",
                        path="t02_api",
                        format="json-lines",
                    ),
                ],
            ),
            "audit": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="t02_audit",
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

    print_cli_tutorial_footer(
        code="T02",
        title="Configuration recipes (env-driven levels + multi-destination)",
        console="Colored Hydra lines on stdout; audit text is file-only (no duplicate console spam).",
        artifacts=[
            "examples/logs/cli-tutorials/t02_api.jsonl",
            "examples/logs/cli-tutorials/t02_audit.log",
        ],
        takeaway="HYDRA_TUTORIAL_LEVEL tweaks default_level; destinations can differ per layer.",
        notebook_rel="examples/tutorials/notebooks/t02_configuration_recipes.ipynb",
    )


if __name__ == "__main__":
    main()
