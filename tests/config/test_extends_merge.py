"""
Role: Tests for YAML extends deep-merge semantics.
Used By:
 - Pytest discovery and CI.
Depends On:
 - hydra_logger.config.loader
Notes:
 - Validates list replacement and nested dict merge for template stacks.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hydra_logger.config.loader import clear_logging_config_cache, load_logging_config


@pytest.fixture(autouse=True)
def _clear_config_cache() -> None:
    clear_logging_config_cache()
    yield
    clear_logging_config_cache()


def test_list_in_overlay_replaces_base_list(tmp_path: Path) -> None:
    base = tmp_path / "base.yaml"
    base.write_text(
        """
layers:
  app:
    level: INFO
    destinations:
      - type: console
""",
        encoding="utf-8",
    )
    over = tmp_path / "over.yaml"
    over.write_text(
        """
extends: base.yaml
layers:
  app:
    destinations:
      - type: "null"
""",
        encoding="utf-8",
    )
    cfg = load_logging_config(over)
    assert len(cfg.layers["app"].destinations) == 1
    assert cfg.layers["app"].destinations[0].type == "null"


def test_multiple_extends_parents_merge_in_order(tmp_path: Path) -> None:
    p1 = tmp_path / "p1.yaml"
    p1.write_text(
        """
layers:
  a:
    level: INFO
    destinations:
      - type: console
""",
        encoding="utf-8",
    )
    p2 = tmp_path / "p2.yaml"
    p2.write_text(
        """
default_level: ERROR
""",
        encoding="utf-8",
    )
    child = tmp_path / "child.yaml"
    child.write_text(
        """
extends:
  - p1.yaml
  - p2.yaml
default_level: INFO
""",
        encoding="utf-8",
    )
    cfg = load_logging_config(child)
    assert cfg.default_level == "INFO"
    assert cfg.layers["a"].level == "INFO"
