"""
Role: Tests for YAML LoggingConfig loader (extends, strict, cache).
Used By:
 - Pytest discovery and CI.
Depends On:
 - hydra_logger.config.loader
Notes:
 - Covers happy paths, cycles, depth limits, and strict top-level validation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hydra_logger.config.loader import (
    clear_logging_config_cache,
    load_logging_config,
)


@pytest.fixture(autouse=True)
def _clear_config_cache() -> None:
    clear_logging_config_cache()
    yield
    clear_logging_config_cache()


def test_load_minimal_yaml(tmp_path: Path) -> None:
    p = tmp_path / "c.yaml"
    p.write_text(
        """
hydra_config_schema_version: 1
default_level: INFO
layers:
  a:
    level: INFO
    destinations:
      - type: console
        use_colors: false
""",
        encoding="utf-8",
    )
    cfg = load_logging_config(p)
    assert cfg.default_level == "INFO"
    assert cfg.hydra_config_schema_version == 1
    assert "a" in cfg.layers


def test_strict_unknown_fields_rejects_extra_top_level(tmp_path: Path) -> None:
    p = tmp_path / "c.yaml"
    p.write_text(
        """
default_level: INFO
unknown_top_level: true
layers:
  a:
    level: INFO
    destinations:
      - type: console
""",
        encoding="utf-8",
    )
    with pytest.raises(Exception):
        load_logging_config(p, strict_unknown_fields=True)


def test_use_config_cache_returns_same_instance(tmp_path: Path) -> None:
    p = tmp_path / "c.yaml"
    p.write_text(
        """
default_level: INFO
layers:
  a:
    level: INFO
    destinations:
      - type: console
""",
        encoding="utf-8",
    )
    a = load_logging_config(p, use_config_cache=True)
    b = load_logging_config(p, use_config_cache=True)
    assert a is b


def test_extends_merge_preserves_destinations(tmp_path: Path) -> None:
    base = tmp_path / "base.yaml"
    base.write_text(
        """
layers:
  app:
    level: INFO
    destinations:
      - type: console
        use_colors: false
""",
        encoding="utf-8",
    )
    child = tmp_path / "child.yaml"
    child.write_text(
        """
extends: base.yaml
default_level: DEBUG
layers:
  app:
    level: DEBUG
""",
        encoding="utf-8",
    )
    cfg = load_logging_config(child)
    assert cfg.default_level == "DEBUG"
    assert cfg.layers["app"].level == "DEBUG"
    assert len(cfg.layers["app"].destinations) == 1


def test_extends_cycle_raises(tmp_path: Path) -> None:
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text(
        "extends: b.yaml\ndefault_level: INFO\nlayers:\n  x:\n    level: INFO\n    destinations:\n      - type: console\n",
        encoding="utf-8",
    )
    b.write_text(
        "extends: a.yaml\ndefault_level: INFO\nlayers:\n  x:\n    level: INFO\n    destinations:\n      - type: console\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="cycle"):
        load_logging_config(a)


def test_extends_max_depth_raises(tmp_path: Path) -> None:
    # chain of 6 single-child extends: c0 -> c1 -> ... -> c5
    files = []
    for i in range(6):
        files.append(tmp_path / f"c{i}.yaml")
    for i in range(6):
        if i < 5:
            content = f"extends: c{i+1}.yaml\n"
        else:
            content = ""
        content += (
            "default_level: INFO\nlayers:\n  a:\n    level: INFO\n"
            "    destinations:\n      - type: console\n"
        )
        files[i].write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match="max depth"):
        load_logging_config(files[0], max_extends_depth=4)


def test_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        load_logging_config(Path("/nonexistent/hydra-logging.yaml"))
