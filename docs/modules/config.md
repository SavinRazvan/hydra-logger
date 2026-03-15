# Config Module (`hydra_logger/config`)

## Scope

Defines configuration models and template helpers used to build logger/runtime configuration.

## Responsibilities

- Define schema and defaults for logger runtime behavior.
- Model layer/destination relationships.
- Provide template and helper entry points for common setups.

## Key Files

- `models.py` - schema objects (`LoggingConfig`, `LogLayer`, `LogDestination`, and related configs).
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
  A[Create LoggingConfig] --> B[Pass config to logger/factory]
  B --> C[Logger sets up layers]
  C --> D[Destinations mapped to handlers]
  D --> E[Handlers receive formatter + level]
```

## Caveats

- `async_cloud` is maintained as a schema-level integration point; database/queue async sink fields are reserved for custom or future integrations and are not built-in handler families.

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
