#!/usr/bin/env python3
"""
Role: Enterprise onboarding tutorial for enterprise profile quick validation.
Used By:
 - Engineers following `examples/tutorials/README.md` onboarding tracks.
Depends On:
 - hydra_logger
Notes:
 - Demonstrates `get_enterprise_config` defaults and verifies runtime behavior.
 - Sets `base_log_dir` / `log_dir_name` so file sinks match `examples/logs/cli-tutorials/` (see `examples/config/README.md`).
"""

import os
import sys
from pathlib import Path

from hydra_logger import LogDestination, create_logger
from hydra_logger.config.defaults import get_enterprise_config

_TUTORIALS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TUTORIALS_ROOT not in sys.path:
    sys.path.insert(0, _TUTORIALS_ROOT)

from shared.cli_tutorial_footer import print_cli_tutorial_footer


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

    # Align with YAML tutorials: write under examples/logs/cli-tutorials/ (not cwd/logs/...).
    config.base_log_dir = "examples/logs"
    config.log_dir_name = "cli-tutorials"
    for layer_name, layer in config.layers.items():
        for destination in layer.destinations:
            if destination.type in {"file", "async_file"} and destination.path:
                stem = Path(Path(destination.path).name).stem
                destination.path = f"t10_{layer_name}_{stem}"

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

    file_paths: list[str] = []
    for _layer_name, layer in config.layers.items():
        for destination in layer.destinations:
            if destination.type in {"file", "async_file"} and destination.path:
                resolved = config.resolve_log_path(destination.path, destination.format)
                try:
                    rel = str(Path(resolved).relative_to(Path.cwd().resolve()))
                except ValueError:
                    rel = resolved
                if rel not in file_paths:
                    file_paths.append(rel)
    file_paths.sort()

    print_cli_tutorial_footer(
        code="T10",
        title="Enterprise profile (defaults + tutorial path shim)",
        console="Hydra colored lines above; profile notes printed before the logger runs.",
        artifacts=file_paths,
        takeaway="get_enterprise_config() seeds a baseline; tutorials rewrite file paths + relax absolute-path policy.",
        notebook_rel=None,
    )


if __name__ == "__main__":
    main()
