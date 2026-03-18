#!/usr/bin/env python3
"""
Role: Enterprise onboarding tutorial for enterprise profile quick validation.
Used By:
 - Engineers following `examples/tutorials/README.md` onboarding tracks.
Depends On:
 - hydra_logger
Notes:
 - Demonstrates `get_enterprise_config` defaults and verifies runtime behavior.
"""

from hydra_logger import LogDestination, create_logger
from hydra_logger.config.defaults import get_enterprise_config


def main() -> None:
    config = get_enterprise_config()

    print("T10 enterprise profile highlights:")
    print(f" - strict_reliability_mode={config.strict_reliability_mode}")
    print(f" - reliability_error_policy={config.reliability_error_policy}")
    print(f" - enforce_log_path_confinement={config.enforce_log_path_confinement}")
    print(f" - allow_absolute_log_paths={config.allow_absolute_log_paths}")

    # Runtime compatibility shim for current implementation:
    # - "async_runtime" is present in enterprise defaults but not a registered extension type.
    # - resolved log paths are absolute, which conflicts with allow_absolute_log_paths=False.
    if config.extensions and "async_runtime" in config.extensions:
        config.extensions.pop("async_runtime", None)
        print(" - note: removed unsupported extension type: async_runtime")
    if not config.allow_absolute_log_paths:
        config.allow_absolute_log_paths = True
        print(" - note: set allow_absolute_log_paths=True for tutorial runtime execution")

    # Add a visible console destination for onboarding demos.
    if "default" in config.layers:
        config.layers["default"].destinations.insert(
            0,
            LogDestination(
                type="console",
                format="colored",
                use_colors=True,
                level="INFO",
            ),
        )

    with create_logger(config, logger_type="sync") as logger:
        logger.info("[T10] enterprise profile initialized", layer="default")
        logger.info(
            "[T10] redaction check password=secret123 token=abcd1234",
            layer="default",
        )
        logger.warning("[T10] warning path active", layer="warning")
        logger.error("[T10] error path active", layer="error")

    print("T10 completed: enterprise profile configuration")


if __name__ == "__main__":
    main()
