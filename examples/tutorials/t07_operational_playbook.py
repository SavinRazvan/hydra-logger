#!/usr/bin/env python3
"""
Role: Enterprise onboarding tutorial for operational validation and rollout checks.
Used By:
 - Engineers following `examples/tutorials/README.md` onboarding tracks.
Depends On:
 - hydra_logger
 - subprocess
 - sys
Notes:
 - Demonstrates preflight checks and smoke validation steps for onboarding rollout.
"""

import subprocess
import sys

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_logger


def main() -> None:
    version_check = subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    pip_health_status = "pass" if version_check.returncode == 0 else "fail"

    config = LoggingConfig(
        layers={
            "ops": LogLayer(
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/examples/tutorials/t07_ops.jsonl",
                        format="json-lines",
                    ),
                ]
            )
        }
    )

    with create_logger(config, logger_type="sync") as logger:
        logger.info(
            "[T07] preflight complete",
            layer="ops",
            extra={"pip_health_status": pip_health_status},
        )
        logger.info("[T07] smoke checks passed", layer="ops")

    print("T07 completed: operational playbook")


if __name__ == "__main__":
    main()
