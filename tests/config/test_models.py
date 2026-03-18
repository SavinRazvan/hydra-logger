"""
Role: Pytest coverage for configuration model validation behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates model defaults, validators, and path resolution.
"""

from pathlib import Path

import pytest

from hydra_logger.config.models import (
    ConsoleHandlerConfig,
    FileHandlerConfig,
    HandlerConfig,
    LogDestination,
    LogLayer,
    LoggingConfig,
    MemoryHandlerConfig,
    ModularConfig,
)
from hydra_logger.config.validation import normalize_level


def test_logging_config_auto_creates_default_layer_when_missing() -> None:
    config = LoggingConfig(layers={})
    assert "default" in config.layers
    assert config.layers["default"].destinations[0].type == "console"


def test_logging_config_validates_core_ranges() -> None:
    with pytest.raises(ValueError, match="Buffer size must be positive"):
        LoggingConfig(buffer_size=0)
    with pytest.raises(ValueError, match="Flush interval cannot be negative"):
        LoggingConfig(flush_interval=-1)
    with pytest.raises(ValueError, match="Monitoring sample rate must be at least 1"):
        LoggingConfig(monitoring_sample_rate=0)


def test_logging_config_resolve_log_path_applies_format_extension(tmp_path: Path) -> None:
    config = LoggingConfig(base_log_dir=str(tmp_path))
    resolved = config.resolve_log_path("service.log", format_type="json-lines")
    assert resolved.endswith(".jsonl")
    assert Path(resolved).parent.exists()


def test_log_destination_requires_path_for_file_destinations() -> None:
    with pytest.raises(ValueError, match="Path is required for file destinations"):
        LogDestination(type="file")


def test_normalize_level_logs_invalid_values(caplog) -> None:
    with caplog.at_level("ERROR", logger="hydra_logger.config.validation"):
        with pytest.raises(ValueError, match="Invalid level"):
            normalize_level("not-a-level")
    assert "Invalid log level received" in caplog.text


def test_log_destination_validators_and_extension_rules() -> None:
    auto_json = LogDestination(type="file", path="events.jsonl")
    assert auto_json.format == "json-lines"

    auto_log = LogDestination(type="file", path="events.log")
    assert auto_log.format == "plain-text"

    with pytest.raises(ValueError, match="Format mismatch"):
        LogDestination(type="file", path="events.csv", format="json-lines")

    with pytest.raises(ValueError, match="Service type is required"):
        LogDestination(type="async_cloud")

    with pytest.raises(ValueError, match="Invalid log format"):
        LogDestination(type="console", format="bad-format")

    with pytest.raises(ValueError, match="Invalid log level"):
        LogDestination(type="console", level="invalid")

    assert LogDestination(type="console", level="warning").level == "WARNING"
    assert LogDestination(type="console", level=None).level is None
    assert LogDestination(type="console", format="").format is None


def test_log_layer_validators_for_level_color_and_destinations() -> None:
    layer = LogLayer(
        level="debug",
        color="Bright_Cyan",
        destinations=[LogDestination(type="console")],
    )
    assert layer.level == "DEBUG"
    assert layer.color == "bright_cyan"

    ansi_layer = LogLayer(
        level="INFO",
        color="\033[31m",
        destinations=[LogDestination(type="console")],
    )
    assert ansi_layer.color == "\033[31m"

    with pytest.raises(ValueError, match="Invalid color"):
        LogLayer(level="INFO", color="ultraviolet", destinations=[LogDestination(type="console")])

    with pytest.raises(ValueError, match="Layer must have at least one destination"):
        LogLayer(level="INFO", destinations=[])

    with pytest.raises(ValueError, match="Invalid level"):
        LogLayer(level="TRACE", destinations=[LogDestination(type="console")])

    assert LogLayer(level="INFO", color=None, destinations=[LogDestination(type="console")]).color is None


def test_logging_config_runtime_helpers_and_toggles(tmp_path: Path) -> None:
    cfg = LoggingConfig(
        default_level="INFO",
        base_log_dir=str(tmp_path / "base"),
        log_dir_name="app",
        layers={
            "api": LogLayer(
                level="WARNING",
                destinations=[
                    LogDestination(type="console"),
                    LogDestination(type="console", level="ERROR"),
                ],
            )
        },
    )

    assert cfg.get_layer_threshold("missing") == 20
    assert cfg.get_layer_threshold("api") == 30
    assert cfg.get_destination_level("api", 1) == 40
    assert cfg.get_destination_level("api", 99) == 30
    assert cfg.get_destination_level("missing") == 20

    cfg.update_security_level("high")
    assert cfg.security_level == "high"
    with pytest.raises(ValueError, match="Invalid security level"):
        cfg.update_security_level("very_high")

    cfg.update_monitoring_config(detail_level="detailed", sample_rate=55, background=False)
    assert cfg.monitoring_detail_level == "detailed"
    assert cfg.monitoring_sample_rate == 55
    assert cfg.monitoring_background is False

    with pytest.raises(ValueError, match="Invalid monitoring detail level"):
        cfg.update_monitoring_config(detail_level="verbose")
    with pytest.raises(ValueError, match="Invalid sample rate"):
        cfg.update_monitoring_config(sample_rate=0)

    cfg.toggle_feature("security", True)
    cfg.toggle_feature("sanitization", True)
    cfg.toggle_feature("plugins", True)
    cfg.toggle_feature("monitoring", True)
    with pytest.raises(ValueError, match="Unknown feature"):
        cfg.toggle_feature("unknown", True)

    summary = cfg.get_configuration_summary()
    assert summary["security"]["enabled"] is True
    assert summary["monitoring"]["enabled"] is True
    assert summary["paths"]["default_log_path"]


def test_logging_config_path_resolution_and_fallback(monkeypatch, tmp_path: Path) -> None:
    cfg = LoggingConfig(base_log_dir=str(tmp_path / "root"), layers={})
    cfg._verbose = True

    default_path = cfg.get_default_log_path()
    assert default_path.endswith("root")

    ensured = cfg.ensure_log_directory(str(tmp_path / "custom-dir"))
    assert Path(ensured).exists()

    absolute_target = tmp_path / "absolute.log"
    resolved_abs = cfg.resolve_log_path(str(absolute_target), format_type="csv")
    assert resolved_abs.endswith(".csv")

    resolved_prefixed = cfg.resolve_log_path("logs/prefixed.log")
    assert str(Path.cwd() / "logs" / "prefixed.log") == resolved_prefixed

    resolved_relative = cfg.resolve_log_path("events.log", format_type="binary-compact")
    assert resolved_relative.endswith(".bin")

    original_mkdir = Path.mkdir
    calls = {"count": 0}

    def flaky_mkdir(self, *args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise OSError("primary path creation failed")
        return original_mkdir(self, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", flaky_mkdir)
    fallback_path = cfg.resolve_log_path("fallback.log")
    assert "logs" in fallback_path

    cfg_no_base = LoggingConfig(layers={})
    assert "logs" in cfg_no_base.get_default_log_path()
    ensured_default = cfg_no_base.ensure_log_directory()
    assert Path(ensured_default).exists()

    tilde_resolved = cfg.resolve_log_path("~/hydra-test.log")
    assert "hydra-test.log" in tilde_resolved

    cfg_rel_base = LoggingConfig(base_log_dir="relative-logs", layers={})
    rel_resolved = cfg_rel_base.resolve_log_path("subdir/app.log")
    assert "relative-logs" in rel_resolved


def test_logging_config_path_confinement_and_absolute_path_controls(tmp_path: Path) -> None:
    base_dir = tmp_path / "base"
    cfg_compat = LoggingConfig(
        base_log_dir=str(base_dir),
        layers={},
        enforce_log_path_confinement=False,
        allow_absolute_log_paths=True,
    )
    escaped = cfg_compat.resolve_log_path("../escaped.log")
    assert escaped.endswith("escaped.log")

    cfg_strict = LoggingConfig(
        base_log_dir=str(base_dir),
        layers={},
        enforce_log_path_confinement=True,
        allow_absolute_log_paths=True,
    )
    with pytest.raises(ValueError, match="escapes configured base directory"):
        cfg_strict.resolve_log_path("../escaped.log")

    outside_abs = tmp_path / "outside.log"
    cfg_abs_blocked = LoggingConfig(
        base_log_dir=str(base_dir),
        layers={},
        enforce_log_path_confinement=False,
        allow_absolute_log_paths=False,
    )
    with pytest.raises(ValueError, match="Absolute log path is disabled"):
        cfg_abs_blocked.resolve_log_path(str(outside_abs))

    inside_abs = base_dir / "service.log"
    cfg_abs_allowed = LoggingConfig(
        base_log_dir=str(base_dir),
        layers={},
        enforce_log_path_confinement=True,
        allow_absolute_log_paths=True,
    )
    resolved_inside = cfg_abs_allowed.resolve_log_path(str(inside_abs))
    assert str(inside_abs.resolve()) == resolved_inside


def test_logging_config_strict_confinement_does_not_use_fallback_on_mkdir_failure(
    monkeypatch, tmp_path: Path
) -> None:
    cfg = LoggingConfig(
        base_log_dir=str(tmp_path / "root"),
        layers={},
        enforce_log_path_confinement=True,
    )
    monkeypatch.setattr(Path, "mkdir", lambda *_a, **_k: (_ for _ in ()).throw(OSError("mkdir-fail")))
    with pytest.raises(ValueError, match="strict path confinement"):
        cfg.resolve_log_path("safe.log")


def test_logging_config_validation_and_layer_management() -> None:
    cfg = LoggingConfig(layers={})
    layer = LogLayer(level="INFO", destinations=[LogDestination(type="console")])
    cfg.add_layer("api", layer)
    assert cfg.get_layer_destinations("api")
    cfg.remove_layer("api")
    assert cfg.get_layer_destinations("api") == []

    invalid_layer = LogLayer.model_construct(level="INFO", destinations=[])
    invalid_cfg = LoggingConfig.model_construct(
        default_level="INFO",
        layers={"broken": invalid_layer},
    )
    with pytest.raises(ValueError, match="Configuration validation failed"):
        invalid_cfg.validate_configuration()

    invalid_dest = LogDestination.model_construct(type="file", path=None, level=None)
    bad_layer = LogLayer.model_construct(level="INFO", destinations=[invalid_dest])
    invalid_cfg_2 = LoggingConfig.model_construct(default_level="INFO", layers={"bad": bad_layer})
    with pytest.raises(ValueError, match="Configuration validation failed"):
        invalid_cfg_2.validate_configuration()


def test_logging_config_field_boundaries_and_handler_models() -> None:
    with pytest.raises(ValueError, match="Invalid default level"):
        LoggingConfig(default_level="TRACE")
    with pytest.raises(ValueError, match="Buffer size cannot exceed 1MB"):
        LoggingConfig(buffer_size=2 * 1024 * 1024)
    with pytest.raises(ValueError, match="Flush interval cannot exceed 1 hour"):
        LoggingConfig(flush_interval=3601)
    with pytest.raises(ValueError, match="Monitoring sample rate cannot exceed 10,000"):
        LoggingConfig(monitoring_sample_rate=10001)
    assert LoggingConfig(monitoring_sample_rate=10000).monitoring_sample_rate == 10000

    handler = HandlerConfig(type="base")
    file_handler = FileHandlerConfig(file_path="a.log")
    console_handler = ConsoleHandlerConfig(stream="stderr")
    memory_handler = MemoryHandlerConfig(capacity=50)
    modular = ModularConfig.from_dict({"handlers": [handler], "level": "WARNING"})
    legacy = modular.to_legacy_format()

    assert file_handler.type == "file"
    assert console_handler.stream == "stderr"
    assert memory_handler.capacity == 50
    assert legacy["level"] == "WARNING"
    assert legacy["handlers"][0]["type"] == "base"


def test_get_destination_level_final_default_fallback_with_constructed_layer() -> None:
    layer_without_level = LogLayer.model_construct(
        level=None,
        destinations=[LogDestination(type="console", level=None)],
    )
    cfg = LoggingConfig.model_construct(default_level="INFO", layers={"x": layer_without_level})
    assert cfg.get_destination_level("x", 0) == 20


def test_normalize_level_handles_non_string_conversion_failure(caplog) -> None:
    class BadStr:
        def __str__(self) -> str:
            raise RuntimeError("boom")

    with caplog.at_level("ERROR", logger="hydra_logger.config.validation"):
        with pytest.raises(RuntimeError, match="boom"):
            normalize_level(BadStr())
    assert "Failed to normalize log level value" in caplog.text


def test_models_remaining_validation_and_path_resolution_branches(
    monkeypatch, tmp_path: Path
) -> None:
    class _Info:
        def __init__(self, data):
            self.data = data

    with pytest.raises(ValueError, match="Path is required for file destinations"):
        LogDestination.validate_file_path("   ", _Info({"type": "file"}))
    with pytest.raises(ValueError, match="Service type is required for async cloud destinations"):
        LogDestination.validate_async_cloud_service(" ", _Info({"type": "async_cloud"}))
    assert (
        LogDestination.validate_async_cloud_service(
            "kinesis", _Info({"type": "async_cloud"})
        )
        == "kinesis"
    )

    # Layer exists but has no explicit level -> default fallback branch.
    no_level_layer = LogLayer.model_construct(
        level=None, destinations=[LogDestination(type="console", level=None)]
    )
    cfg_threshold = LoggingConfig.model_construct(
        default_level="INFO", layers={"no-level": no_level_layer}
    )
    assert cfg_threshold.get_layer_threshold("no-level") == 20

    # Destination has no level but layer does -> layer fallback branch.
    layer_level_only = LogLayer.model_construct(
        level="WARNING", destinations=[LogDestination(type="console", level=None)]
    )
    cfg_destination = LoggingConfig.model_construct(
        default_level="INFO", layers={"layer-level": layer_level_only}
    )
    assert cfg_destination.get_destination_level("layer-level", 0) == 30

    # Hit "~" branch where expanduser still yields a relative path.
    cfg = LoggingConfig(base_log_dir=str(tmp_path / "base"), log_dir_name="svc", layers={})
    monkeypatch.setattr("hydra_logger.config.models.os.path.isabs", lambda path: path.startswith("/"))
    monkeypatch.setattr(
        "hydra_logger.config.models.os.path.expanduser",
        lambda _path: "relative-home/logs/event.log",
    )
    resolved_tilde_relative = cfg.resolve_log_path("~/event.log")
    assert "relative-home/logs/event.log" in resolved_tilde_relative
    assert str(tmp_path / "base" / "svc") in resolved_tilde_relative

    # Hit non-tilde branch with base_log_dir + log_dir_name.
    resolved_relative = cfg.resolve_log_path("service/activity.log")
    assert str(tmp_path / "base" / "svc") in resolved_relative

    # Hit default "logs/" branches when no base directory is configured.
    cfg_no_base = LoggingConfig(layers={})
    monkeypatch.setattr("pathlib.Path.cwd", classmethod(lambda cls: Path("relative-cwd")))
    monkeypatch.setattr(
        "hydra_logger.config.models.os.path.expanduser",
        lambda _path: "relative-home/no-base.log",
    )
    tilde_no_base = cfg_no_base.resolve_log_path("~/no-base.log")
    assert "logs" in tilde_no_base
    non_tilde_no_base = cfg_no_base.resolve_log_path("plain-relative.log")
    assert "logs" in non_tilde_no_base

    valid_cfg = LoggingConfig(
        layers={"default": LogLayer(level="INFO", destinations=[LogDestination(type="console")])}
    )
    assert valid_cfg.validate_configuration() is True
