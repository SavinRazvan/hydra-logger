#!/usr/bin/env python3
"""
Role: Enterprise onboarding tutorial for policy-driven layers and routing controls.
Used By:
 - Engineers following `examples/tutorials/README.md` onboarding tracks.
Depends On:
 - hydra_logger
Notes:
 - Demonstrates enterprise profile layering, destination-level filtering, and context routing.
"""

from hydra_logger import LogDestination, LogLayer, create_logger
from hydra_logger.config.defaults import get_enterprise_config


def main() -> None:
    config = get_enterprise_config()

    print("T11 enterprise policy demo:")
    print(f" - strict_reliability_mode={config.strict_reliability_mode}")
    print(f" - reliability_error_policy={config.reliability_error_policy}")
    print(f" - enforce_log_path_confinement={config.enforce_log_path_confinement}")
    print(f" - allow_absolute_log_paths={config.allow_absolute_log_paths}")

    # The current enterprise defaults include an unregistered extension type.
    if config.extensions and "async_runtime" in config.extensions:
        config.extensions.pop("async_runtime", None)
        print(" - note: removed unsupported extension type: async_runtime")

    # Probe strict path policy so users can see it in action.
    try:
        config.resolve_log_path("logs/examples/tutorials/t11_probe.jsonl")
        print(" - path confinement probe: accepted")
    except Exception as exc:
        print(f" - path confinement probe: blocked ({exc})")

    # Keep tutorial runnable with current absolute-path resolution behavior.
    config.allow_absolute_log_paths = True

    config.layers["api"] = LogLayer(
        level="INFO",
        destinations=[
            # Destination-level override: console sees INFO+.
            LogDestination(type="console", format="colored", use_colors=True, level="INFO"),
            # File receives WARNING+ only.
            LogDestination(
                type="file",
                path="logs/examples/tutorials/t11_api_warn.jsonl",
                format="json-lines",
                level="WARNING",
            ),
        ],
    )
    config.layers["audit"] = LogLayer(
        level="WARNING",
        destinations=[
            LogDestination(
                type="file",
                path="logs/examples/tutorials/t11_audit.log",
                format="plain-text",
                level="WARNING",
            )
        ],
    )
    config.layers["security"] = LogLayer(
        level="WARNING",
        destinations=[
            LogDestination(type="console", format="plain-text", use_colors=False),
            LogDestination(
                type="file",
                path="logs/examples/tutorials/t11_security.jsonl",
                format="json-lines",
            ),
        ],
    )

    with create_logger(config, logger_type="sync") as logger:
        logger.info(
            "[T11] API request started",
            layer="api",
            context={"request_id": "req-1001", "tenant_id": "tenant-a"},
        )
        logger.warning(
            "[T11] API latency threshold exceeded",
            layer="api",
            context={"request_id": "req-1001", "latency_ms": 812},
        )
        logger.warning(
            "[T11] Audit policy warning",
            layer="audit",
            context={"actor": "admin", "action": "role_update"},
        )
        logger.error(
            "[T11] Security event token=abcd1234 password=secret123",
            layer="security",
            context={"request_id": "req-1001", "source": "waf"},
        )

    print("T11 completed: enterprise policy layers and routing")
    print("Expected artifacts:")
    print(" - logs/examples/tutorials/t11_api_warn.jsonl")
    print(" - logs/examples/tutorials/t11_audit.log")
    print(" - logs/examples/tutorials/t11_security.jsonl")


if __name__ == "__main__":
    main()
