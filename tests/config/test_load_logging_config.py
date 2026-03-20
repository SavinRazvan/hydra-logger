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
from pydantic import BaseModel

from hydra_logger.config import loader as loader_module
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


def test_extends_validation_and_yaml_root_guardrails(tmp_path: Path) -> None:
    bad_extends_item = tmp_path / "bad_extends_item.yaml"
    bad_extends_item.write_text(
        """
extends:
  - ok.yaml
  - 123
default_level: INFO
layers:
  a:
    level: INFO
    destinations:
      - type: console
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="non-empty strings"):
        load_logging_config(bad_extends_item)

    bad_extends_type = tmp_path / "bad_extends_type.yaml"
    bad_extends_type.write_text(
        """
extends: 123
default_level: INFO
layers:
  a:
    level: INFO
    destinations:
      - type: console
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="string or a list"):
        load_logging_config(bad_extends_type)

    empty_yaml = tmp_path / "empty.yaml"
    empty_yaml.write_text("", encoding="utf-8")
    # Empty YAML normalizes to {} and still validates with model defaults.
    cfg = load_logging_config(empty_yaml)
    assert cfg is not None

    list_root = tmp_path / "list_root.yaml"
    list_root.write_text("- item", encoding="utf-8")
    with pytest.raises(ValueError, match="YAML root must be a mapping"):
        load_logging_config(list_root)


def test_extends_merged_nodes_guardrail_raises(tmp_path: Path) -> None:
    base = tmp_path / "base_nodes.yaml"
    base.write_text(
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
    child = tmp_path / "child_nodes.yaml"
    child.write_text(
        """
extends: base_nodes.yaml
layers:
  a:
    level: DEBUG
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="max_merged_nodes"):
        load_logging_config(child, max_merged_nodes=5)


def test_loader_internal_type_guard_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg_file = tmp_path / "strict.yaml"
    cfg_file.write_text(
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

    class FakeModel(BaseModel):
        dummy: int = 1

    monkeypatch.setattr(
        loader_module.StrictLoggingConfig,
        "model_validate",
        classmethod(lambda cls, _data: FakeModel()),
    )
    with pytest.raises(TypeError, match="not LoggingConfig"):
        load_logging_config(cfg_file, strict_unknown_fields=True)
