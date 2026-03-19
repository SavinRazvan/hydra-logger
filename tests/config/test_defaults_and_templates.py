"""
Role: Pytest coverage for configuration defaults and template registry behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates named config resolution and template lifecycle.
"""

import pytest

from hydra_logger.config.configuration_templates import (
    ConfigurationTemplates as RegistryTemplates,
)
from hydra_logger.config.configuration_templates import (
    HydraLoggerError,
)
from hydra_logger.config.defaults import (
    ConfigurationTemplates,
    get_custom_config,
    get_default_config,
    get_development_config,
    get_enterprise_config,
    get_named_config,
    get_production_config,
    list_available_configs,
)
from hydra_logger.config.models import LogDestination, LoggingConfig, LogLayer


def test_default_and_production_configs_return_logging_config() -> None:
    default = get_default_config()
    production = get_production_config()
    enterprise = get_enterprise_config()
    assert default.default_level == "INFO"
    assert "default" in default.layers
    assert production.enable_security is True
    assert production.enable_sanitization is True
    assert enterprise.strict_reliability_mode is True
    assert enterprise.enforce_log_path_confinement is True


def test_custom_config_falls_back_to_console_when_no_destination_selected() -> None:
    cfg = get_custom_config(console_enabled=False, file_enabled=False)
    default_destinations = cfg.layers["default"].destinations
    assert len(default_destinations) == 1
    assert default_destinations[0].type == "async_console"


def test_get_named_config_rejects_unknown_name() -> None:
    with pytest.raises(ValueError, match="Unknown configuration name"):
        get_named_config("missing-profile")


def test_get_named_config_logs_unknown_name(caplog) -> None:
    with caplog.at_level("ERROR", logger="hydra_logger.config.defaults"):
        with pytest.raises(ValueError):
            get_named_config("missing-profile")
    assert "Unknown configuration name requested: missing-profile" in caplog.text


def test_template_registry_supports_register_validate_and_cleanup() -> None:
    registry = RegistryTemplates()

    @registry.register_template("unit_test_profile", "test profile")
    def _builder():
        return get_default_config()

    assert registry.has_template("unit_test_profile")
    assert registry.validate_template("unit_test_profile") is True
    registry.clear_custom_templates()
    assert not registry.has_template("unit_test_profile")


def test_defaults_named_config_custom_and_registry_listing() -> None:
    custom = get_named_config(
        "custom",
        default_level="ERROR",
        file_enabled=True,
        file_path="nested/path/app.log",
    )
    assert custom.default_level == "ERROR"
    assert custom.layers["default"].destinations[1].path == "app.log"

    development = get_development_config()
    assert development.default_level == "DEBUG"
    assert "debug" in development.layers

    listed = list_available_configs()
    assert {"default", "development", "production", "enterprise", "custom"}.issubset(
        set(listed.keys())
    )

    assert get_named_config("default").default_level == "INFO"
    assert get_named_config("development").default_level == "DEBUG"
    assert get_named_config("production").enable_security is True
    assert get_named_config("enterprise").strict_reliability_mode is True


def test_defaults_custom_config_error_path_logs_and_reraises(caplog) -> None:
    with caplog.at_level("ERROR", logger="hydra_logger.config.defaults"):
        with pytest.raises(Exception, match="Invalid level"):
            get_custom_config(default_level="TRACE")
    assert "Failed building custom logging configuration" in caplog.text


def test_production_config_console_override_branch(monkeypatch) -> None:
    def fake_custom_config(**_kwargs) -> LoggingConfig:
        return LoggingConfig(
            layers={
                "default": LogLayer(
                    level="INFO",
                    destinations=[LogDestination(type="console", use_colors=True)],
                )
            }
        )

    monkeypatch.setattr(
        ConfigurationTemplates,
        "get_custom_config",
        staticmethod(fake_custom_config),
    )
    production = ConfigurationTemplates.get_production_config()
    destination = production.layers["default"].destinations[0]
    assert destination.type == "async_console"
    assert destination.use_colors is False


def test_custom_config_optional_layers_and_custom_layer_merge() -> None:
    custom_layers = {
        "custom_audit": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(type="file", path="audit.log", format="plain-text")
            ],
        )
    }
    cfg = get_custom_config(
        warning_layer=True,
        info_layer=True,
        critical_layer=True,
        custom_layers=custom_layers,
    )

    assert "warning" in cfg.layers
    assert "info" in cfg.layers
    assert "critical" in cfg.layers
    assert "custom_audit" in cfg.layers


def test_configuration_templates_registry_error_paths() -> None:
    registry = RegistryTemplates()

    with pytest.raises(HydraLoggerError, match="non-empty string"):
        registry.register_template("", "bad")

    with pytest.raises(HydraLoggerError, match="must be a callable function"):
        registry.register_template("bad", "bad")(None)  # type: ignore[arg-type]

    with pytest.raises(HydraLoggerError, match="Unknown configuration template"):
        registry.get_template("missing")

    @registry.register_template("broken_builder", "broken")
    def _broken_builder():
        raise RuntimeError("builder failed")

    with pytest.raises(
        HydraLoggerError, match="Failed to create configuration template"
    ):
        registry.get_template("broken_builder")

    with pytest.raises(HydraLoggerError, match="validation failed"):
        registry.validate_template("broken_builder")


def test_configuration_templates_builtin_setup_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        RegistryTemplates,
        "register_template",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("forced setup failure")
        ),
    )
    with pytest.raises(RuntimeError, match="forced setup failure"):
        RegistryTemplates()


def test_configuration_templates_convenience_wrappers() -> None:
    import importlib

    template_module = importlib.import_module(
        "hydra_logger.config.configuration_templates"
    )

    @template_module.register_configuration_template(
        "wrapper_unit_profile", "wrapper profile"
    )
    def _wrapper_profile():
        return get_default_config()

    assert template_module.has_configuration_template("wrapper_unit_profile")
    config = template_module.get_configuration_template("wrapper_unit_profile")
    assert config.default_level == "INFO"
    names = template_module.list_configuration_templates()
    assert "wrapper_unit_profile" in names
    assert (
        template_module.validate_configuration_template("wrapper_unit_profile") is True
    )
    template_module.configuration_templates.remove_template("wrapper_unit_profile")
