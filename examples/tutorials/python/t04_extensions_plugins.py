#!/usr/bin/env python3
"""
Role: Enterprise onboarding tutorial for extension and plugin customization.
Used By:
 - Engineers following `examples/tutorials/README.md` onboarding tracks.
Depends On:
 - hydra_logger
Notes:
 - Demonstrates built-in extension toggles and custom plugin type registration.
"""

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_logger
from hydra_logger.extensions import ExtensionManager, SecurityExtension


class CustomSecurityExtension(SecurityExtension):
    """Minimal custom extension for registration tutorial."""


def main() -> None:
    config = LoggingConfig(
        enable_security=True,
        extensions={
            "security_default": {
                "enabled": True,
                "type": "security",
                "patterns": ["email", "token"],
            }
        },
        layers={
            "app": LogLayer(
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/tutorials/t04_extensions.jsonl",
                        format="json-lines",
                    )
                ]
            )
        },
    )

    manager = ExtensionManager()
    manager.register_extension_type("custom_security", CustomSecurityExtension)
    manager.create_extension(
        "enterprise_policy",
        "custom_security",
        enabled=True,
        patterns=["password", "secret"],
    )
    manager.disable_extension("enterprise_policy")
    manager.enable_extension("enterprise_policy")

    with create_logger(config, logger_type="sync") as logger:
        logger.info("[T04] extension track initialized", layer="app")

    print("T04 completed: extensions/plugins")


if __name__ == "__main__":
    main()
