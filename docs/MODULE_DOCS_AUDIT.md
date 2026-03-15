# Module Docs Alignment Audit

Audit date: 2026-03-15

## Findings

### High

- Configuration models still advertise async destination families (`async_database`, `async_queue`, `async_cloud`) that do not currently map to concrete handlers in `hydra_logger/handlers/`.

### Medium

- `docs/ARCHITECTURE.md` and `docs/WORKFLOW_ARCHITECTURE.md` overlap heavily with module-level pages and can diverge unless the module docs are treated as canonical.
- Package-level `__init__.py` docstrings were cleaned, but should remain concise to avoid future drift.

### Low

- Prior documentation lacked a strict PR acceptance gate for module-doc completeness; this is now addressed in governance and PR template checklist sections.

## Code-Reality Baseline

### Package inventory (`hydra_logger/`)

- `config`
- `core`
- `extensions`
- `factories`
- `formatters`
- `handlers`
- `loggers`
- `types`
- `utils`

### Export inventory (`__all__` snapshot)

| Package | Export Count | Notes |
|---|---:|---|
| Root `hydra_logger` | 31 | Includes logger classes, factories, manager helpers, config/types/exceptions, and compatibility aliases. |
| `config` | 22 | Model + template exports only; all names currently bound. |
| `core` | 13 | Core constants, exceptions, and layer manager exports. |
| `extensions` | 5 | Base, security/format/perf extension types, manager. |
| `factories` | 9 | Logger creation helpers. |
| `formatters` | 9 | Base + plain/colored/json/structured formatters. |
| `handlers` | 21 | Console/file/rotating/network/null family surface. |
| `loggers` | 13 | Base logger, logger implementations, record strategy helpers. |
| `types` | 41 | Core types and enums with bound exports. |
| `utils` | 19 | Text/time/file utility family. |

### Export gaps requiring follow-up

- `config/__init__.py`, `types/__init__.py`, `handlers/__init__.py`, and root `hydra_logger/__init__.py` now have fully bound `__all__` exports.

## Coverage Matrix

| Module | Documented | Source Doc |
|---|---|---|
| Root package (`hydra_logger/__init__.py`) | Yes | `docs/modules/root-package.md` |
| `loggers/` | Yes | `docs/modules/loggers.md` |
| `handlers/` | Yes | `docs/modules/handlers.md` |
| `formatters/` | Yes | `docs/modules/formatters.md` |
| `config/` | Yes | `docs/modules/config.md` |
| `core/` | Yes | `docs/modules/core.md` |
| `factories/` | Yes | `docs/modules/factories.md` |
| `types/` | Yes | `docs/modules/types.md` |
| `extensions/` | Yes | `docs/modules/extensions.md` |
| `utils/` | Yes | `docs/modules/utils.md` |

Coverage status: 100 percent of current package directories have dedicated module documentation.

## Split/Migration Plan

| Old Section | New Canonical Target |
|---|---|
| Monolithic package structure narrative in `docs/ARCHITECTURE.md` | `docs/modules/README.md` and per-module pages |
| Main package export details | `docs/modules/root-package.md` |
| Logger workflow and lifecycle details | `docs/modules/loggers.md` |
| Handler support matrix and flow | `docs/modules/handlers.md` |
| Formatter selection and output behavior | `docs/modules/formatters.md` |
| Configuration model hierarchy | `docs/modules/config.md` |
| Core control-plane concerns | `docs/modules/core.md` |
| Factory creation workflow | `docs/modules/factories.md` |
| Types, enums, and record flow | `docs/modules/types.md` |
| Extension processing behavior | `docs/modules/extensions.md` |
| Utility dependency notes | `docs/modules/utils.md` |

## Progress Tracking Proposal

### Status table template

| Module | Status | Last Updated | Owner | Next Action |
|---|---|---|---|---|
| root-package | green/yellow/red | YYYY-MM-DD | @owner | verify exports |
| loggers | green/yellow/red | YYYY-MM-DD | @owner | verify runtime flow |
| handlers | green/yellow/red | YYYY-MM-DD | @owner | verify destination support |
| formatters | green/yellow/red | YYYY-MM-DD | @owner | verify formatter map |
| config | green/yellow/red | YYYY-MM-DD | @owner | verify schema and templates |
| core | green/yellow/red | YYYY-MM-DD | @owner | verify exceptions/constants |
| factories | green/yellow/red | YYYY-MM-DD | @owner | verify constructor surface |
| types | green/yellow/red | YYYY-MM-DD | @owner | verify exported symbols |
| extensions | green/yellow/red | YYYY-MM-DD | @owner | verify extension points |
| utils | green/yellow/red | YYYY-MM-DD | @owner | verify helper side effects |

### Immediate next 3 actions

1. Keep `docs/modules/README.md` as canonical index and keep top-level docs linked to it.
2. Keep package-level docstrings concise and aligned to the currently exported surface.
3. Decide whether async destination types in `config/models.py` are roadmap-only (documented as such) or should be implemented with real handlers.

## Release Notes (Docs Update)

### Completed in this pass

- Added and standardized module docs in `docs/modules/` with consistent structure and Mermaid flows.
- Replaced monolithic architecture workflow narratives with canonical, non-duplicative docs aligned to module pages.
- Added module-doc acceptance checklist section in `.github/pull_request_template.md`.
- Validated link integrity for `README.md`, `docs/ARCHITECTURE.md`, `docs/WORKFLOW_ARCHITECTURE.md`, and `docs/modules/*.md`.

### Intentionally deferred

- Runtime implementation or deprecation of async destination families in `hydra_logger/config/models.py`.
