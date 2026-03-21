#!/usr/bin/env python3
"""
Role: Enterprise onboarding tutorial for layer taxonomy and routing policies.
Used By:
 - Engineers following `examples/tutorials/README.md` onboarding tracks.
Depends On:
 - hydra_logger
Notes:
 - Demonstrates per-layer destinations and context propagation for enterprise services.
"""

import os
import sys

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_logger

_TUTORIALS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TUTORIALS_ROOT not in sys.path:
    sys.path.insert(0, _TUTORIALS_ROOT)

from shared.cli_tutorial_footer import print_cli_tutorial_footer


def build_layered_config() -> LoggingConfig:
    return LoggingConfig(
        base_log_dir="examples/logs",
        log_dir_name="cli-tutorials",
        default_level="INFO",
        layers={
            "api": LogLayer(
                destinations=[
                    LogDestination(
                        type="file",
                        path="t03_layers_api",
                        format="json-lines",
                    ),
                ]
            ),
            "database": LogLayer(
                destinations=[
                    LogDestination(
                        type="file",
                        path="t03_layers_database",
                        format="json-lines",
                    )
                ]
            ),
            "auth": LogLayer(
                destinations=[
                    LogDestination(
                        type="file",
                        path="t03_layers_auth",
                        format="json-lines",
                    ),
                    LogDestination(type="console", format="plain-text", use_colors=True),
                ]
            ),
        },
    )


def main() -> None:
    config = build_layered_config()
    context = {"correlation_id": "onboarding-layer-001"}
    with create_logger(config, logger_type="sync") as logger:
        logger.info("[T03] auth token requested", layer="auth", context=context)
        logger.info("[T03] api request routed", layer="api", context=context)
        logger.info("[T03] database query executed", layer="database", context=context)

    print_cli_tutorial_footer(
        code="T03",
        title="Layer taxonomy + routing",
        console="One Hydra line from `auth` (console sink); api/db are file-only.",
        artifacts=[
            "examples/logs/cli-tutorials/t03_layers_api.jsonl",
            "examples/logs/cli-tutorials/t03_layers_database.jsonl",
            "examples/logs/cli-tutorials/t03_layers_auth.jsonl",
        ],
        takeaway="Same correlation_id is carried across layers; inspect JSONL files side by side.",
        notebook_rel="examples/tutorials/notebooks/t03_layers_customization.ipynb",
    )


if __name__ == "__main__":
    main()
