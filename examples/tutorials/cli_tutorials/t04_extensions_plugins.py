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

import os
import sys

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_logger
from hydra_logger.extensions import ExtensionManager, SecurityExtension

_TUTORIALS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TUTORIALS_ROOT not in sys.path:
    sys.path.insert(0, _TUTORIALS_ROOT)

from shared.cli_tutorial_footer import print_cli_tutorial_footer


class CustomSecurityExtension(SecurityExtension):
    """Minimal custom extension for registration tutorial."""


def main() -> None:
    config = LoggingConfig(
        base_log_dir="examples/logs",
        log_dir_name="cli-tutorials",
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
                        path="t04_extensions",
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

    print_cli_tutorial_footer(
        code="T04",
        title="Extensions / plugin registration",
        console="No Hydra console sink; this script is file-only + extension manager side effects.",
        artifacts=["examples/logs/cli-tutorials/t04_extensions.jsonl"],
        takeaway="Register custom extension types, then enable/disable named instances.",
        notebook_rel="examples/tutorials/notebooks/t04_extensions_plugins.ipynb",
    )


if __name__ == "__main__":
    main()
