# Audit Coverage Matrix

Module-level tracking for documentation alignment audits.

| Module/Area | Canonical Doc | Last Audited | Status | Owner | Next Action |
|---|---|---|---|---|---|
| root package (`hydra_logger/__init__.py`) | `docs/modules/root-package.md` | 2026-03-15 | green | @maintainer | Keep exports and aliases synchronized |
| `loggers` | `docs/modules/loggers.md` | 2026-03-15 | green | @maintainer | Keep exports synchronized with `__all__` |
| `handlers` | `docs/modules/handlers.md` | 2026-03-15 | green | @maintainer | Keep family list aligned to `handlers/__init__.py` |
| `formatters` | `docs/modules/formatters.md` | 2026-03-15 | green | @maintainer | Keep selector and fallback behavior current |
| `config` | `docs/modules/config.md` | 2026-03-15 | green | @maintainer | Keep built-in vs custom integration fields explicitly documented |
| `core` | `docs/modules/core.md` | 2026-03-15 | green | @maintainer | Keep caveats and public surface aligned to exports |
| `factories` | `docs/modules/factories.md` | 2026-03-15 | green | @maintainer | Keep root and module factory surfaces aligned |
| `types` | `docs/modules/types.md` | 2026-03-15 | green | @maintainer | Keep enum surface and dependent docs synchronized |
| `extensions` | `docs/modules/extensions.md` | 2026-03-15 | green | @maintainer | Keep public extension exports synchronized |
| `utils` | `docs/modules/utils.md` | 2026-03-15 | green | @maintainer | Keep public helper exports synchronized |

## Status Legend

- `green`: aligned and complete
- `yellow`: aligned with follow-up needed
- `red`: major mismatch or missing coverage
