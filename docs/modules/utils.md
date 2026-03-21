# Utils Module (`hydra_logger/utils`)

## Scope

Utility layer for text, time, file, stderr interception, system detection, and error logging helpers.

## Responsibilities

- Provide shared helpers used by multiple runtime modules.
- Keep core utility APIs lightweight and reusable.
- Isolate specialized bootstrap behavior in explicit utility modules.

## Key Files

- `text_utility.py` - text processing/validation helpers.
- `time_utility.py` - timestamps and time formatting helpers.
- `file_utility.py` - file/path utility helpers.
- `stderr_interceptor.py` - stderr interception (**exported from root `hydra_logger`**, not from `hydra_logger.utils.__all__`).
- `system_detector.py` - runtime environment/system detection (internal).
- `error_logger.py` - internal error logging helpers.
- `internal_diagnostics.py`, `reliability_lifecycle.py`, `slo_metrics.py` - lifecycle/diagnostics hooks (internal; referenced from logger/handler docs).
- `destination_contracts.py` - destination typing helpers (internal).
- `__init__.py` - **narrow** public utility exports (see below).

## Utility Usage Pattern

```mermaid
flowchart LR
  A["Core/logger code"] --> B["time_utility"]
  A --> C[text_utility]
  A --> D[file_utility]
  A --> E[stderr_interceptor]
  B --> F[Consistent record fields]
  C --> F
  D --> F
  E --> F
```

## Public Surface (`hydra_logger.utils` / `utils/__init__.py`)

- Text: `TextProcessor`, `TextFormatter`, `TextValidator`, `TextSanitizer`, `TextAnalyzer`
- Time: `TimeUtility`, `TimestampFormatter`, `TimestampFormat`, `TimestampPrecision`, `TimestampConfig`, `DateFormatter`, `TimeZoneUtility`, `TimeRange`, `TimeInterval`
- File: `FileUtility`, `PathUtility`, `FileValidator`, `FileProcessor`, `DirectoryScanner`

**Root-only public API (not in `utils.__all__`):** `StderrInterceptor`, `start_stderr_interception`, `stop_stderr_interception` from `hydra_logger` top-level.

## Caveats And Known Gaps

- General utility exports are intentionally narrow; modules under `hydra_logger.utils` that are **not** in `utils/__init__.py` are **internal** unless promoted and documented.

## Maintenance Notes

- Avoid introducing side effects in general utilities beyond explicitly named bootstrap helpers.
- Keep utility imports lightweight because many runtime modules depend on them.

## Maintenance Checklist

- [ ] Utility exports remain focused and implementation-backed.
- [ ] New utility side effects are explicitly documented.
- [ ] Cross-module utility dependencies remain acyclic and lightweight.
