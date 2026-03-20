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

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_logger


def build_layered_config() -> LoggingConfig:
    return LoggingConfig(
        default_level="INFO",
        layers={
            "api": LogLayer(
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/tutorials/t03_layers_api.jsonl",
                        format="json-lines",
                    ),
                ]
            ),
            "database": LogLayer(
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/tutorials/t03_layers_database.jsonl",
                        format="json-lines",
                    )
                ]
            ),
            "auth": LogLayer(
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/tutorials/t03_layers_auth.jsonl",
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

    print("T03 completed: layers customization")


if __name__ == "__main__":
    main()
