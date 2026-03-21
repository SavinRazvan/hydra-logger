# Module Coverage Matrix

This matrix tracks `hydra_logger/` documentation coverage against current package boundaries.

## Current Coverage

| Module | Primary docs | Coverage status | Priority | Notes |
|---|---|---|---|---|
| `hydra_logger/__init__.py` | `docs/modules/root-package.md` | covered | P3 | Public exports and compatibility aliases documented. |
| `hydra_logger/cli.py` | `docs/modules/cli.md` | covered | P2 | CLI behavior now documented explicitly. |
| `hydra_logger/loggers/` | `docs/modules/loggers.md` | covered | P3 | Sync/async/composite behavior documented. |
| `hydra_logger/loggers/pipeline/` | `docs/modules/loggers.md`, `docs/WORKFLOW_ARCHITECTURE.md` | covered | P1 | Includes `RecordBuilder`, `LayerRouter`, `HandlerDispatcher`, `ExtensionProcessor`, `ComponentDispatcher`. |
| `hydra_logger/handlers/` | `docs/modules/handlers.md` | covered | P3 | Destination families and semantics documented. |
| `hydra_logger/formatters/` | `docs/modules/formatters.md` | covered | P3 | Formatter model and fallback behavior documented. |
| `hydra_logger/config/` | `docs/modules/config.md` | covered | P2 | Schema-rich module; review on model changes. |
| `hydra_logger/core/` | `docs/modules/core.md` | covered | P3 | Constants, exceptions, managers documented. |
| `hydra_logger/factories/` | `docs/modules/factories.md` | covered | P3 | Factory entrypoints and creation flow documented. |
| `hydra_logger/types/` | `docs/modules/types.md` | covered | P2 | Broad enum/type surface requires periodic sync. |
| `hydra_logger/extensions/` | `docs/modules/extensions.md` | covered | P3 | Extension contracts and manager behavior documented. |
| `hydra_logger/extensions/security/` | `docs/modules/extensions.md` | covered | P3 | `DataRedaction` + `SecurityExtension` documented; dedicated page only if surface grows. |
| `hydra_logger/utils/` | `docs/modules/utils.md` | covered | P2 | Distinguishes public utility exports from internal utility helpers. |

## Review Cadence

- Deep docs ↔ code alignment checklist: [`../audit/DOCS_CODEBASE_ALIGNMENT.md`](../audit/DOCS_CODEBASE_ALIGNMENT.md).
- Re-check this matrix when module boundaries or package `__init__.py` exports change.
- Update `Priority` if runtime risk or API volatility changes.
- Keep references aligned with `docs/modules/README.md`.
