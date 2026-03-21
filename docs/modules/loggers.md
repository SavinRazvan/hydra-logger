# Loggers Module (`hydra_logger/loggers`)

## Scope

Implements logger runtimes: synchronous, asynchronous, and composite forms.

## Responsibilities

- Create `LogRecord` instances through shared base behavior.
- Route records to layer-specific handlers.
- Provide sync and async lifecycle/cleanup semantics.
- Expose high-level logging methods (`debug` through `critical`).

## Key Files

- `base.py` - abstract logger contract and shared lifecycle behavior.
- `sync_logger.py` - sync logging path, layer routing, and handler dispatch.
- `async_logger.py` - async logging path and async/sync fallback behavior.
- `composite_logger.py` - fan-out logger patterns for multiple components.
- `pipeline/record_builder.py` - hot-path record construction service.
- `pipeline/layer_router.py` - layer resolution and routing service.
- `pipeline/handler_dispatcher.py` - destination dispatch orchestration.
- `pipeline/extension_processor.py` - extension execution in logging flow.
- `pipeline/component_dispatcher.py` - composite component fan-out dispatch.
- `pipeline/__init__.py` - exports `RecordBuilder`, `LayerRouter`, `HandlerDispatcher`, `ExtensionProcessor`, `ComponentDispatcher` (pipeline internals; not re-listed on `hydra_logger.loggers` root `__all__`).
- `__init__.py` - module export surface, record-creation helpers, convenience `getLogger()` (local shim to factory).

## Runtime Flow

```mermaid
flowchart TD
  A["log/info/warning/error"] --> B["BaseLogger.create_log_record"]
  B --> C{Logger type}
  C -->|SyncLogger| D[Sync layer resolution]
  C -->|AsyncLogger| E[Async emit path]
  C -->|"Composite*"| F["Fan-out to components"]
  D --> G[Handlers]
  E --> G
  F --> G
  G --> H["Formatter + destination output"]
```

## Key Behaviors

- `BaseLogger` centralizes performance profile selection for record creation.
- `SyncLogger` applies per-layer threshold checks before dispatching handlers.
- `AsyncLogger` supports async contexts, queue-runtime mode, and sync fallback behavior.
- Composite loggers coordinate multiple logger instances and aggregate health; composite async defaults to a direct-I/O path unless configured otherwise.

## Public Surface (`hydra_logger.loggers` / `loggers/__init__.py`)

- **Loggers:** `BaseLogger`, `PerformanceProfiles`, `SyncLogger`, `AsyncLogger`, `CompositeLogger`, `CompositeAsyncLogger`
- **Record creation (re-exported from `types.records`):** `RecordCreationStrategy`, `get_record_creation_strategy`, `create_log_record`, `MINIMAL_STRATEGY`, `CONTEXT_STRATEGY`, `AUTO_CONTEXT_STRATEGY`
- **Convenience:** `getLogger` (delegates to `factories.create_logger`; prefer root `hydra_logger.getLogger` for consistency with `getSyncLogger` / `getAsyncLogger`)

For pipeline classes, import `hydra_logger.loggers.pipeline` explicitly (tests / advanced introspection).

## Caveats

- Some logger docstrings describe legacy capabilities; rely on implementation and exports, not historical narrative comments.
- Composite async internals include direct I/O buffering logic; evaluate carefully before changing defaults.
- Legacy **plugin** hooks (`enable_plugins`, `_execute_pre_log_plugins` / `_execute_post_log_plugins`) are no-ops; extension behavior is driven by **`LoggingConfig.extensions`** and the factory-built **`ExtensionManager`** on the config (`_extension_manager`). Data protection reuses the **`SecurityExtension`** instance from that manager when `enable_data_protection` is true.
- **`close()` / `aclose()`** failures on individual handlers are surfaced via **`hydra_logger.utils.reliability_lifecycle`** (internal diagnostics + `handler_close_failures` on `get_health_status()`), and honor **`strict_reliability_mode`** / **`reliability_error_policy`**.

## Maintenance Notes

- After editing any logger file, re-check method parity for `debug/info/warning/error/critical`.
- Verify close/cleanup behavior for both sync and async context managers.

## Maintenance Checklist

- [ ] Logger method parity is preserved across implementations.
- [ ] Layer routing behavior is documented and unchanged, or docs are updated.
- [ ] Context-manager close semantics still match implementation.
