# Core Module (`hydra_logger/core`)

## Scope

Provides foundational constants, exceptions, and runtime management helpers.

## Responsibilities

- Centralize core exceptions and constants.
- Provide layer/logger management primitives used by higher modules.
- Keep internal control-plane semantics consistent across runtime types.

## Key Files

- `constants.py` - shared constants/enums used by runtime components.
- `exceptions.py` - exception hierarchy for logger/config/handler errors.
- `layer_management.py` - layer routing and layer configuration objects.
- `logger_management.py` - logger lookup/manager style helpers.
- `base.py` - base runtime constructs used by internals.
- `__init__.py` - core exports.

## Control Plane Flow

```mermaid
flowchart LR
  A[Logger initialization] --> B[Layer configuration validation]
  B --> C[Manager lookup or creation]
  C --> D[Runtime error pathways via core exceptions]
```

## Public Surface (module-level)

- Constants: `Colors`, `QueuePolicy`, `ShutdownPhase`
- Layer management: `LayerManager`, `LayerConfiguration`
- Exceptions: `HydraLoggerError` family

## Maintenance Notes

- Keep core exceptions stable; external callers may catch them directly.
- Sync naming with `hydra_logger/__init__.py` re-exports when adding/removing symbols.

## Maintenance Checklist

- [ ] Exception hierarchy changes are documented.
- [ ] Exported constants and manager helpers are synchronized with root exports.
- [ ] Layer-management behavior changes are reflected in logger docs.
