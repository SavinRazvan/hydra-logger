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

import os
import subprocess
import sys

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_logger

_TUTORIALS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TUTORIALS_ROOT not in sys.path:
    sys.path.insert(0, _TUTORIALS_ROOT)

from shared.cli_tutorial_footer import print_cli_tutorial_footer


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
        base_log_dir="examples/logs",
        log_dir_name="cli-tutorials",
        layers={
            "ops": LogLayer(
                destinations=[
                    LogDestination(
                        type="file",
                        path="t07_ops",
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

    print_cli_tutorial_footer(
        code="T07",
        title="Operational playbook (preflight + structured ops log)",
        console="No Hydra console sink; ops events are JSONL-only.",
        artifacts=["examples/logs/cli-tutorials/t07_ops.jsonl"],
        extra_lines=[f"pip check exit code: {version_check.returncode}"],
        takeaway="Capture rollout/preflight signals as structured logs for audits.",
        notebook_rel=None,
    )


if __name__ == "__main__":
    main()
