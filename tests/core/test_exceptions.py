"""
Role: Pytest coverage for core exception behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates detail payload propagation and readable string output.
"""

from hydra_logger.core.exceptions import (
    AnalyticsError,
    AsyncError,
    CompatibilityError,
    ConfigurationError,
    DataProtectionError,
    FactoryError,
    FormatterError,
    HandlerError,
    HydraLoggerError,
    LifecycleError,
    PerformanceError,
    PluginError,
    RegistryError,
    SecurityError,
    ValidationError,
)


def test_hydra_logger_error_string_and_details_roundtrip() -> None:
    err = HydraLoggerError("boom", {"module": "core"})
    assert str(err) == "boom - Details: {'module': 'core'}"
    assert err.get_details() == {"module": "core"}


def test_configuration_and_validation_error_fields() -> None:
    cfg = ConfigurationError("bad config", config_path="cfg.yml")
    val = ValidationError("bad value", field="level", value="TRACE", rule="known_level")
    assert cfg.config_path == "cfg.yml"
    assert val.field == "level"
    assert val.get_details()["rule"] == "known_level"


def test_handler_and_factory_error_include_context() -> None:
    handler_err = HandlerError("handler failed", handler_type="file", operation="emit")
    factory_err = FactoryError(
        "factory failed", component_type="logger", factory_method="create_logger"
    )
    assert "handler_type" in handler_err.get_details()
    assert factory_err.get_details()["factory_method"] == "create_logger"


def test_extended_exception_types_preserve_context_fields() -> None:
    formatter_err = FormatterError("fmt", formatter_type="json", format_string="{m}")
    async_err = AsyncError("async", operation="flush", coroutine_name="flush_worker")
    plugin_err = PluginError("plugin", plugin_name="redact", plugin_type="security")
    security_err = SecurityError(
        "sec", threat_type="xss", severity="high", source="req"
    )
    registry_err = RegistryError(
        "registry", component_type="handler", component_name="console", operation="add"
    )
    lifecycle_err = LifecycleError(
        "life", component="logger", lifecycle_phase="init", expected_phase="ready"
    )
    data_err = DataProtectionError(
        "dp", operation="mask", data_type="email", security_level="strict"
    )
    analytics_err = AnalyticsError(
        "metric", metric_name="latency", metric_value=10, aggregation_type="avg"
    )
    compat_err = CompatibilityError(
        "compat", old_version="0.1", new_version="0.2", feature="pipeline"
    )
    perf_err = PerformanceError("perf", operation="write", duration=0.5, threshold=0.2)

    assert formatter_err.get_details()["formatter_type"] == "json"
    assert async_err.get_details()["operation"] == "flush"
    assert plugin_err.get_details()["plugin_name"] == "redact"
    assert security_err.get_details()["severity"] == "high"
    assert registry_err.get_details()["component_name"] == "console"
    assert lifecycle_err.get_details()["expected_phase"] == "ready"
    assert data_err.get_details()["security_level"] == "strict"
    assert analytics_err.get_details()["metric_name"] == "latency"
    assert compat_err.get_details()["new_version"] == "0.2"
    assert perf_err.get_details()["threshold"] == 0.2


def test_exception_optional_detail_fields_are_included_when_provided() -> None:
    cfg = ConfigurationError("cfg", config_data={"k": "v"})
    handler = HandlerError("h", handler_name="console")
    async_err = AsyncError("a", event_loop_info={"running": True})
    plugin = PluginError("p", plugin_path="/tmp/plugin.py")
    factory = FactoryError("f", parameters={"retry": 3})

    assert cfg.get_details()["config_data"] == {"k": "v"}
    assert handler.get_details()["handler_name"] == "console"
    assert async_err.get_details()["event_loop_info"]["running"] is True
    assert plugin.get_details()["plugin_path"] == "/tmp/plugin.py"
    assert factory.get_details()["parameters"]["retry"] == 3
