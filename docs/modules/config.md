# Config Module (`hydra_logger/config`)

## Scope

Defines configuration models and template helpers used to build logger/runtime configuration.

## Responsibilities

- Define schema and defaults for logger runtime behavior.
- Model layer/destination relationships.
- Provide template and helper entry points for common setups.

## Key Files

- `models.py` - schema objects (`LoggingConfig`, `LogLayer`, `LogDestination`, and related configs).
- `loader.py` - load and validate YAML from disk (`extends`, optional cache, strict unknown fields).
- `defaults.py` - default/template helper utilities.
- `configuration_templates.py` - template registry and lookup helpers.
- `__init__.py` - exported config API surface.

## Configuration Hierarchy

```mermaid
graph TD
  A[LoggingConfig] --> B[Layer map]
  B --> C[LogLayer]
  C --> D[Destinations list]
  D --> E[LogDestination]
```

## Configuration To Runtime Path

```mermaid
flowchart TD
  A["Create LoggingConfig"] --> B["Pass config to logger/factory"]
  B --> C[Logger sets up layers]
  C --> D[Destinations mapped to handlers]
  D --> E["Handlers receive formatter + level"]
```

## File-based YAML (enterprise path)

Load a validated `LoggingConfig` once at startup (not per log line):

```python
from pathlib import Path

from hydra_logger import create_sync_logger
from hydra_logger.config.loader import load_logging_config

config = load_logging_config(Path("config/logging.yaml"))
logger = create_sync_logger(config, name="app")

# or keyword-only:
logger = create_sync_logger(config_path=Path("config/logging.yaml"), name="app")
```

YAML features:

- **`extends`**: path or list of paths (relative to the including file) merged before validation; depth and graph size are capped (see `load_logging_config` docstring).
- **`hydra_config_schema_version`**: optional integer field on the root model for migration tracking.
- **`strict_unknown_fields=True`**: fail on unknown top-level keys when loading.

Network destinations may set:

- **`http_payload_encoder`**: registered name for a Python-side encoder (see `docs/plans/config-from-path-enterprise.md`).
- **`http_batch_size` / `http_batch_flush_interval`**: optional batching for HTTP sinks.
- **`use_real_websocket_transport`** (for `network_ws` only): when `True`, `WebSocketHandler` uses real WebSocket I/O (requires the `network` extra / `websockets`). Default remains simulated transport for config-driven `network_ws` until this flag is set.

Canonical design notes: [`plans/config-from-path-enterprise.md`](../plans/config-from-path-enterprise.md).

## Caveats

- `async_cloud` is maintained as a schema-level integration point; database/queue async sink fields are reserved for custom or future integrations and are not built-in handler families.
- Typed network destination variants are first-class in `LogDestination`:
  - `network_http` (`url` required, scheme `http|https`)
  - `network_ws` (`url` required, scheme `ws|wss`)
  - `network_socket` (`host` + `port` required)
  - `network_datagram` (`host` + `port` required)
- Legacy `network` remains a transitional alias that maps to `network_http` when `url` is provided and emits a deprecation warning.

## Network Destination Examples

```python
from hydra_logger.config.models import LoggingConfig, LogDestination, LogLayer

config = LoggingConfig(
    layers={
        "http": LogLayer(
            destinations=[
                LogDestination(
                    type="network_http",
                    url="https://logs.example.com/ingest",
                    timeout=5.0,
                    retry_count=3,
                    retry_delay=0.5,
                )
            ]
        ),
        "websocket": LogLayer(
            destinations=[
                LogDestination(
                    type="network_ws",
                    url="wss://stream.example.com/events",
                    timeout=10.0,
                    retry_count=5,
                    retry_delay=1.0,
                )
            ]
        ),
    }
)
```

## Public Surface (module-level)

- Core schema: `LoggingConfig`, `LogLayer`, `LogDestination`
- Additional config models from `models.py`
- Template/default helpers from `defaults.py` and `configuration_templates.py`

## Maintenance Notes

- After schema changes in `models.py`, update examples in README and module docs.
- Re-check template names and defaults against real template registry functions.

## Maintenance Checklist

- [ ] Schema fields in docs match `models.py`.
- [ ] Template names and registry behavior are current.
- [ ] Exported symbols in `config/__init__.py` are validated against bound names.
- [ ] Destination and integration fields are clearly marked as built-in vs custom/roadmap.
