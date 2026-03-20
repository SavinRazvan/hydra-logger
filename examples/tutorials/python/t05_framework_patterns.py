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

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_async_logger


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
        layers={
            "api": LogLayer(
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/tutorials/t05_framework_api.jsonl",
                        format="json-lines",
                    )
                ]
            ),
            "worker": LogLayer(
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/tutorials/t05_framework_worker.jsonl",
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

    print("T05 completed: framework patterns")


if __name__ == "__main__":
    asyncio.run(main())
