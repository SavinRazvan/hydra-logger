# Logger Configuration Test Guide (Start to Finish)

This guide is a practical checklist for configuring `hydra_logger` end-to-end and validating each option in small, testable steps.

Use this when you want to verify:

- logger type selection (`sync`, `async`, `composite`, `composite-async`)
- layer and destination routing
- levels at global/layer/destination scope
- formats, file-extension rules, and colors
- extension enablement/configuration/runtime control
- reliability and path-confinement controls

---

## 0) Quick Setup

```bash
.hydra_env/bin/python -m pip install -e ".[dev]"
```

Create a scratch script:

```bash
mkdir -p logs/manual
touch logs/manual/.gitkeep
```

---

## 1) Imports You Need

```python
from hydra_logger import LogDestination, LoggingConfig, LogLayer
from hydra_logger import create_logger, create_async_logger
from hydra_logger import create_composite_logger, create_composite_async_logger
from hydra_logger.extensions import ExtensionManager, SecurityExtension
```

---

## 2) Logger Creation Options

`create_logger(..., logger_type=...)` supports:

- `sync`
- `async`
- `composite`
- `composite-async`

Quick validation:

```python
sync_logger = create_logger(logger_type="sync")
async_logger = create_logger(logger_type="async")
composite_logger = create_logger(logger_type="composite")
composite_async_logger = create_logger(logger_type="composite-async")
```

---

## 3) Levels (Valid Values Everywhere)

Valid levels for `default_level`, `LogLayer.level`, and `LogDestination.level`:

- `NOTSET`
- `DEBUG`
- `INFO`
- `WARNING`
- `ERROR`
- `CRITICAL`

Inheritance model:

- destination level overrides layer level for that destination
- layer level overrides `default_level` for that layer
- `default_level` is global fallback

---

## 4) Destination Types and Fields

`LogDestination.type` supports:

- `console`
- `file`
- `null`
- `async_console`
- `async_file`
- `async_cloud`

Core fields:

- `level`
- `path` (required for `file`)
- `format`
- `use_colors` (console)
- `max_size`, `backup_count`
- `max_queue_size`
- `extra` (handler-specific extras)

Async/cloud-related fields:

- `url`
- `connection_string`
- `queue_url`
- `service_type` (required for `async_cloud`)
- `credentials`
- `retry_count`
- `retry_delay`
- `timeout`
- `max_connections`

---

## 5) Format Options and File Extension Rules

Accepted `format` values:

- text: `plain-text`, `fast-plain`, `detailed`
- json: `json-lines`, `json`
- colored: `colored`
- structured: `csv`, `syslog`, `gelf`, `logstash`
- binary: `binary`, `binary-compact`, `binary-extended`

Important file rules:

- `.jsonl` requires `json-lines`
- `.json` requires `json-lines`
- `.csv` requires `csv`
- `.bin` requires `binary-compact`
- `.log` is flexible (any format; defaults to `plain-text` if omitted)

---

## 6) Layer Options

`LogLayer` fields:

- `level`
- `destinations` (must not be empty)
- `color`
- `enabled`

Allowed color names:

- `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`
- `bright_black`, `bright_red`, `bright_green`, `bright_yellow`
- `bright_blue`, `bright_magenta`, `bright_cyan`, `bright_white`

ANSI codes (like `\033[31m`) are also accepted.

---

## 7) Global LoggingConfig Options

`LoggingConfig` supports:

- core:
  - `default_level`
  - `layers`
  - `layer_colors`
- security/extensions:
  - `enable_security`
  - `enable_sanitization`
  - `enable_data_protection`
  - `enable_plugins`
  - `enable_performance_monitoring`
  - `extensions`
  - `security_level` (`low|medium|high|strict`)
- monitoring:
  - `monitoring_detail_level` (`basic|standard|detailed`)
  - `monitoring_sample_rate`
  - `monitoring_background`
- path controls:
  - `base_log_dir`
  - `log_dir_name`
  - `enforce_log_path_confinement`
  - `allow_absolute_log_paths`
- performance/reliability:
  - `buffer_size`
  - `flush_interval`
  - `strict_reliability_mode`
  - `reliability_error_policy` (`silent|warn|raise`)

---

## 8) Full End-to-End Test Configuration

Use this as a comprehensive smoke config:

```python
from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_logger

config = LoggingConfig(
    default_level="INFO",
    enable_security=True,
    enable_sanitization=True,
    enable_data_protection=True,
    enable_performance_monitoring=True,
    security_level="medium",
    monitoring_detail_level="standard",
    monitoring_sample_rate=100,
    monitoring_background=True,
    base_log_dir="logs",
    log_dir_name="manual",
    enforce_log_path_confinement=False,
    allow_absolute_log_paths=True,
    buffer_size=8192,
    flush_interval=1.0,
    strict_reliability_mode=False,
    reliability_error_policy="warn",
    extensions={
        "data_protection": {
            "enabled": True,
            "type": "security",
            "patterns": ["email", "phone", "api_key", "password", "token"],
        },
        "formatting": {
            "enabled": False,
            "type": "formatting",
        },
        "performance": {
            "enabled": False,
            "type": "performance",
        },
    },
    layers={
        "api": LogLayer(
            level="INFO",
            color="bright_blue",
            destinations=[
                LogDestination(
                    type="console",
                    format="colored",
                    use_colors=True,
                    level="DEBUG",
                ),
                LogDestination(
                    type="file",
                    path="logs/manual/api.jsonl",
                    format="json-lines",
                    level="INFO",
                ),
                LogDestination(
                    type="file",
                    path="logs/manual/api.log",
                    format="plain-text",
                    level="WARNING",
                ),
            ],
        ),
        "security": LogLayer(
            level="WARNING",
            color="red",
            destinations=[
                LogDestination(
                    type="console",
                    format="plain-text",
                    use_colors=False,
                ),
                LogDestination(
                    type="file",
                    path="logs/manual/security.jsonl",
                    format="json-lines",
                ),
            ],
        ),
    },
)

with create_logger(config, logger_type="sync") as logger:
    logger.debug("debug example", layer="api")
    logger.info("info example", layer="api")
    logger.warning("warning example", layer="api")
    logger.error("security alert password=secret123", layer="security")
```

Run:

```bash
.hydra_env/bin/python your_script.py
```

Validate:

- `logs/manual/api.jsonl` exists
- `logs/manual/api.log` exists
- `logs/manual/security.jsonl` exists
- console output shows colored API logs
- security message is redacted when data-protection is active

---

## 9) Extension Runtime Controls (Manual Test)

Built-in extension types available in `ExtensionManager`:

- `security`
- `formatting`
- `performance`

Runtime operations:

- `register_extension_type(name, extension_class)`
- `create_extension(name, extension_type, enabled=False, **config)`
- `enable_extension(name)` / `disable_extension(name)`
- `configure_extension(name, **config)`
- `set_processing_order([...])`
- `process_data(data)`
- `get_extension_status()`, `list_enabled_extensions()`, `get_extension_metrics()`

Example:

```python
from hydra_logger.extensions import ExtensionManager, SecurityExtension


class CustomSecurityExtension(SecurityExtension):
    pass


manager = ExtensionManager()
manager.register_extension_type("custom_security", CustomSecurityExtension)
manager.create_extension(
    "enterprise_policy",
    "custom_security",
    enabled=True,
    patterns=["password", "token"],
)
print(manager.get_extension_status())
```

---

## 10) Failure Cases You Should Intentionally Test

- invalid level (expect validation error)
- `file` destination without `path` (expect validation error)
- `async_cloud` without `service_type` (expect validation error)
- format mismatch (`.jsonl` + `plain-text`) (expect validation error)
- layer with empty destinations (expect validation error)

---

## 11) Test Checklist (Copy/Paste)

- [ ] Logger type selected and created successfully
- [ ] Layers route events as expected
- [ ] Destination-level filtering works
- [ ] File format/extension constraints validated
- [ ] Colors rendered only where configured
- [ ] Security/data protection behavior verified
- [ ] Extension manager runtime controls verified
- [ ] Reliability/path options validated for your environment
- [ ] Generated logs are present and parseable

---

## 12) Recommended Next Step

If you want this turned into automated tests, mirror this guide under:

- `tests/config/`
- `tests/extensions/`
- `tests/examples/`

and split checks into:

- happy path
- validation/failure path
- runtime toggles/regression checks
