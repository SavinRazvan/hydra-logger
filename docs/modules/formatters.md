# Formatters Module (`hydra_logger/formatters`)

## Scope

Converts `LogRecord` objects into destination-specific string payloads.

## Responsibilities

- Provide stable formatting contracts for handlers.
- Keep format selection predictable and backward compatible.
- Ensure console/non-console output rules are explicit.

## Key Files

- `base.py` - formatter base interface.
- `text_formatter.py` - plain text output.
- `colored_formatter.py` - ANSI-colored output.
- `json_formatter.py` - JSON Lines formatter.
- `structured_formatter.py` - structured outputs (CSV, Syslog, GELF, Logstash).
- `__init__.py` - formatter exports and `get_formatter()` selection helper.

## Formatter Selection Flow

```mermaid
flowchart LR
  A[Destination format string] --> B[get_formatter(format_type, use_colors)]
  B --> C{Known type?}
  C -->|yes| D[Specific formatter instance]
  C -->|no| E[PlainTextFormatter fallback]
  D --> F[format(record)]
  E --> F
```

## Operational Notes

- Console pathways may force colored formatting based on `use_colors`.
- Non-console handlers should stay non-colored for machine readability.
- Unknown format strings currently fall back to plain text.

## Public Surface (module-level)

- `BaseFormatter`
- `PlainTextFormatter`
- `ColoredFormatter`
- `JsonLinesFormatter`
- Structured formatters: `CsvFormatter`, `SyslogFormatter`, `GelfFormatter`, `LogstashFormatter`
- Selector: `get_formatter()`

## Caveats And Known Gaps

- Some format aliases are normalized in logger code paths; keep alias docs aligned with real format mapping behavior.

## Maintenance Notes

- Update format mapping logic in logger implementations when adding new formatter keys.
- Keep formatter output stable where downstream systems parse logs.

## Maintenance Checklist

- [ ] Formatter list matches `formatters/__init__.py`.
- [ ] `get_formatter()` fallback behavior is documented.
- [ ] New format keys are reflected in logger mapping and docs.
