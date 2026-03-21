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
import os
import sys

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_logger

_TUTORIALS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TUTORIALS_ROOT not in sys.path:
    sys.path.insert(0, _TUTORIALS_ROOT)

from shared.cli_tutorial_footer import print_cli_tutorial_footer


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
        base_log_dir="examples/logs",
        log_dir_name="cli-tutorials",
        layers={
            "migration": LogLayer(
                destinations=[
                    LogDestination(
                        type="file",
                        path="t06_migration",
                        format="json-lines",
                    )
                ]
            )
        }
    )
    with create_logger(config, logger_type="sync") as logger:
        logger.info("[T06] migrated event written", layer="migration")
        logger.info("[T06] rollback toggle remains available", layer="migration")

    print_cli_tutorial_footer(
        code="T06",
        title="Migration / adoption (stdlib logging + Hydra side by side)",
        console="`[legacy]` line is stdlib; Hydra lines are not printed (file-only layer).",
        artifacts=["examples/logs/cli-tutorials/t06_migration.jsonl"],
        takeaway="Run legacy and Hydra in parallel during rollout; Hydra events land in JSONL.",
        notebook_rel=None,
    )


if __name__ == "__main__":
    main()
