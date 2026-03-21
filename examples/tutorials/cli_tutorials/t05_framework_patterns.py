#!/usr/bin/env python3
"""
Role: Enterprise onboarding tutorial for framework integration logging patterns.
Used By:
 - Engineers following `examples/tutorials/README.md` onboarding tracks.
Depends On:
 - asyncio
 - hydra_logger
Notes:
 - Demonstrates API and async worker patterns with correlation context propagation.
"""

import asyncio
import os
import sys

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_async_logger

_TUTORIALS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TUTORIALS_ROOT not in sys.path:
    sys.path.insert(0, _TUTORIALS_ROOT)

from shared.cli_tutorial_footer import print_cli_tutorial_footer


async def api_handler(logger, request_id: str) -> None:
    context = {"correlation_id": request_id, "route": "/orders"}
    await logger.info("[T05] request accepted", layer="api", context=context)
    await logger.info("[T05] request completed", layer="api", context=context)


async def worker_handler(logger, request_id: str) -> None:
    context = {"correlation_id": request_id, "job": "reconcile-orders"}
    await logger.info("[T05] worker started", layer="worker", context=context)
    await logger.info("[T05] worker finished", layer="worker", context=context)


async def main() -> None:
    config = LoggingConfig(
        base_log_dir="examples/logs",
        log_dir_name="cli-tutorials",
        layers={
            "api": LogLayer(
                destinations=[
                    LogDestination(
                        type="file",
                        path="t05_framework_api",
                        format="json-lines",
                    )
                ]
            ),
            "worker": LogLayer(
                destinations=[
                    LogDestination(
                        type="file",
                        path="t05_framework_worker",
                        format="json-lines",
                    )
                ]
            ),
        }
    )

    async with create_async_logger(config, name="framework-track") as logger:
        await asyncio.gather(
            api_handler(logger, "req-501"),
            worker_handler(logger, "req-501"),
        )

    print_cli_tutorial_footer(
        code="T05",
        title="Framework patterns (async logger + correlation)",
        console="No Hydra console output here — both layers use file sinks only.",
        artifacts=[
            "examples/logs/cli-tutorials/t05_framework_api.jsonl",
            "examples/logs/cli-tutorials/t05_framework_worker.jsonl",
        ],
        takeaway="Async handlers share correlation_id `req-501`; compare api vs worker JSONL.",
        notebook_rel=None,
    )


if __name__ == "__main__":
    asyncio.run(main())
