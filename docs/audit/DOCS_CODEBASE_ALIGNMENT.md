# Documentation ↔ codebase alignment — **master index**

**Role:** Single **hub** that **indexes** where truth lives (docs, code, tests, CI). It does not duplicate every module page; it **points** to them and lists **what to re-check** when code changes.

**Last full index refresh:** 2026-03-16 (pass: module pages + policy + cross-links + tests/benchmark index).

---

## Master documentation index

Grouped **canonical** docs. Prefer these paths when updating or auditing.

### Package & API

| Doc | Purpose |
|-----|---------|
| [README.md](../../README.md) | Install, quick start, user-facing overview, links |
| [docs/modules/README.md](../modules/README.md) | Module doc set contract + dependency view |
| [docs/modules/root-package.md](../modules/root-package.md) | `hydra_logger/__init__.py` exports vs `__all__` |
| [docs/modules/MODULE_COVERAGE_MATRIX.md](../modules/MODULE_COVERAGE_MATRIX.md) | Module → doc page coverage; links **back here** for deep sync |

### Per-module deep dives (`docs/modules/`)

| Doc | Code |
|-----|------|
| [config.md](../modules/config.md) | `hydra_logger/config/` |
| [factories.md](../modules/factories.md) | `hydra_logger/factories/` |
| [loggers.md](../modules/loggers.md) | `hydra_logger/loggers/`, `loggers/pipeline/` |
| [handlers.md](../modules/handlers.md) | `hydra_logger/handlers/` |
| [formatters.md](../modules/formatters.md) | `hydra_logger/formatters/` |
| [core.md](../modules/core.md) | `hydra_logger/core/` |
| [types.md](../modules/types.md) | `hydra_logger/types/` |
| [extensions.md](../modules/extensions.md) | `hydra_logger/extensions/` |
| [utils.md](../modules/utils.md) | `hydra_logger/utils/` |
| [cli.md](../modules/cli.md) | `hydra_logger/cli.py` |
| [module-governance.md](../modules/module-governance.md) | How to maintain module docs |

### Architecture & workflow

| Doc | Purpose |
|-----|---------|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Topology, data path, links to modules + **this file** |
| [WORKFLOW_ARCHITECTURE.md](../WORKFLOW_ARCHITECTURE.md) | Pipeline / orchestration narrative |
| [PERFORMANCE.md](../PERFORMANCE.md) | Benchmark context + profiles |
| [OPERATIONS.md](../OPERATIONS.md) | Runtime diagnostics, guardrails |

### Quality, testing, release

| Doc | Purpose |
|-----|---------|
| [TESTING.md](../TESTING.md) | Pytest layout, CI contract, examples/notebook gates |
| [ENVIRONMENT_SETUP.md](../ENVIRONMENT_SETUP.md) | `.hydra_env`, toolchain |
| [RELEASE_POLICY.md](../RELEASE_POLICY.md) | SemVer / compatibility |
| [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md) | Ship steps |

### Examples & tutorials (onboarding tree)

| Doc | Purpose |
|-----|---------|
| [examples/README.md](../../examples/README.md) | Examples root: layout, YAML vs Python, links |
| [examples/config/README.md](../../examples/config/README.md) | Preset catalog, path rules |
| [examples/tutorials/README.md](../../examples/tutorials/README.md) | CLI vs notebook tracks, runners |
| [examples/tutorials/notebooks/README.md](../../examples/tutorials/notebooks/README.md) | Notebook bootstrap, troubleshooting |
| [docs/tutorials/ENTERPRISE_NOTEBOOKS.md](../tutorials/ENTERPRISE_NOTEBOOKS.md) | Governance for notebooks |
| [EXAMPLES-AUDIT.md](EXAMPLES-AUDIT.md) | File-level inventory under `examples/` |

### Plans (intentional work, status)

| Doc | Purpose |
|-----|---------|
| [plans/INDEX.md](../plans/INDEX.md) | Initiative → plan → **implemented / in progress** |
| [plans/README.md](../plans/README.md) | How plans are used |
| [plans/config-from-path-enterprise.md](../plans/config-from-path-enterprise.md) | Config-from-disk design |
| [plans/notebook-onboarding-refresh.md](../plans/notebook-onboarding-refresh.md) | Notebook factory / onboarding |
| [plans/code-fix-hardening.md](../plans/code-fix-hardening.md) | Lifecycle / WS / extensions hardening |

### Benchmarks (repo `benchmark/`)

| Doc | Purpose |
|-----|---------|
| [benchmark/README.md](../../benchmark/README.md) | How to run profiles |
| [benchmarks/CONTRACT.md](../benchmarks/CONTRACT.md) | Artifact contract |
| [benchmarks/METRIC_DEFINITIONS.md](../benchmarks/METRIC_DEFINITIONS.md) | Metric meanings |
| [benchmarks/MIGRATION.md](../benchmarks/MIGRATION.md) | Benchmark migrations |

### Other `docs/` (specialized)

| Doc | Purpose |
|-----|---------|
| [EDA_MICROSERVICES_GUIDE.md](../EDA_MICROSERVICES_GUIDE.md) | EDA / microservices patterns |
| [LOGGER_CONFIGURATION_TEST.md](../LOGGER_CONFIGURATION_TEST.md) | Hands-on logger/config validation checklist |
| [AGENT_AUTOMATION.md](../AGENT_AUTOMATION.md) | Maintainer automation (`scripts/pr/*`, release preflight) |
| [SECURITY.md](../../SECURITY.md) | Security policy / disclosure (repo root) |
| `docs/private/` | Optional local-only notes (often gitignored; may be absent in a clone) |

### Sibling packages (not under `hydra_logger/`)

| Tree | Doc | Notes |
|------|-----|--------|
| `benchmark/` | [benchmark/README.md](../../benchmark/README.md), [docs/benchmarks/](../benchmarks/) | Performance harness + contracts; CI runs `ci_smoke` / `pr_gate` profiles |
| `tests/` | [TESTING.md](../TESTING.md), [tests/README.md](../../tests/README.md) | Module-aligned tests + `tests/examples`, `tests/benchmark`, `tests/scripts` |

### This directory (`docs/audit/`) — sign-offs & audits

| Doc | Purpose |
|-----|---------|
| **DOCS_CODEBASE_ALIGNMENT.md** (this file) | **Master index** + alignment procedure + finding log |
| [EXAMPLES-AUDIT.md](EXAMPLES-AUDIT.md) | `examples/` inventory + path matrix |
| [FINAL_ENTERPRISE_HARDENING_SIGNOFF.md](FINAL_ENTERPRISE_HARDENING_SIGNOFF.md) | Enterprise slice sign-off |
| [PYPI_PUBLISH_AND_VERIFY.md](PYPI_PUBLISH_AND_VERIFY.md) | PyPI release verification |
| [README.md](README.md) | Short directory index |

---

## Code ↔ enforcement index (what “locks” reality)

| Layer | Artifact | What it validates |
|-------|-----------|-------------------|
| Public API | `hydra_logger/__init__.py` `__all__` | Stable exports; keep in sync with `root-package.md` |
| Module tests | `tests/<module>/` | Behavior per `docs/TESTING.md` |
| Examples / tutorials | `tests/examples/` | Notebook factory, assets, `utility`, CLI runners |
| Benchmark package | `tests/benchmark/` | Package coverage gate for `benchmark/` (see CI + `TESTING.md`) |
| Maintainer scripts | `tests/scripts/` | Workflow / release helper tests |
| Headers | `scripts/pr/check_slim_headers.py` | Python metadata docstrings |
| Version metadata | `scripts/dev/check_version_consistency.py` | `hydra_logger.__version__` vs packaging |
| CI | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) | Test, lint, notebook-smoke, security, build, benchmarks |
| Notebook smoke | `scripts/dev/run_notebook_smoke.py` | Executes T01+T02 after checkout |

---

## Coverage matrix (module → primary doc)

| Code area | Primary doc |
|-----------|-------------|
| `hydra_logger/__init__.py` | `docs/modules/root-package.md`, `README.md` |
| `hydra_logger/cli.py` | `docs/modules/cli.md` |
| `hydra_logger/config/` | `docs/modules/config.md`, `docs/plans/config-from-path-enterprise.md` |
| `hydra_logger/core/` | `docs/modules/core.md` |
| `hydra_logger/factories/` | `docs/modules/factories.md` |
| `hydra_logger/formatters/` | `docs/modules/formatters.md` |
| `hydra_logger/handlers/` | `docs/modules/handlers.md` |
| `hydra_logger/loggers/` + `pipeline/` | `docs/modules/loggers.md`, `docs/WORKFLOW_ARCHITECTURE.md` |
| `hydra_logger/types/` | `docs/modules/types.md` |
| `hydra_logger/extensions/` | `docs/modules/extensions.md` |
| `hydra_logger/utils/` | `docs/modules/utils.md` |
| `examples/tutorials/*` | `examples/README.md`, `EXAMPLES-AUDIT.md`, `ENTERPRISE_NOTEBOOKS.md` |
| `benchmark/` (harness + profiles) | `benchmark/README.md`, `docs/PERFORMANCE.md`, `docs/benchmarks/*` |
| `tests/` | `docs/TESTING.md`, `tests/README.md` |

---

## Stale naming → canonical target

| Avoid (legacy) | Use instead |
|----------------|-------------|
| `examples/tutorials/python/` | `examples/tutorials/cli_tutorials/` |
| `examples/logs/tutorials/` | `examples/logs/cli-tutorials/` (CLI) or `examples/logs/notebooks/` (notebooks) |
| Notebook setup = `utility` only | `jupyter_workspace.py` → `prime_notebook_workspace()` → `shared/` + `utility/` |
| Embedded `_STANDALONE_CONFIGS` in notebooks | On-disk `examples/config/` only |

---

## Progress — next 3 actions (standing)

1. **Release:** bump `hydra_logger/__init__.py` `__version__`; grep `README.md`, `docs/RELEASE_POLICY.md`, PyPI-oriented docs for version strings.
2. **Config loader / `config_path`:** touch `docs/modules/config.md`, `docs/modules/factories.md`, `loader.py` docstring, and **this index** if behavior changes.
3. **New tutorial / notebook factory rule:** same PR updates `tests/examples/test_tutorial_assets.py`, `docs/TESTING.md`, `EXAMPLES-AUDIT.md`.

---

## How to re-run alignment quickly

1. `__all__` in `hydra_logger/__init__.py` ↔ `docs/modules/root-package.md`
2. `git ls-files hydra_logger/**/*.py` ↔ `MODULE_COVERAGE_MATRIX.md`
3. `rg 'tutorials/python|logs/tutorials|_STANDALONE' docs examples README.md` (extend patterns as needed)
4. `.hydra_env/bin/python -m pytest tests/examples -q` ↔ `docs/TESTING.md` claims

---

## Finding log — 2026-03-21 pass (historical)

### High (addressed that pass)

| Issue | Evidence | Fix |
|-------|-----------|-----|
| EXAMPLES-AUDIT implied notebook logs gitignored | `EXAMPLES-AUDIT.md` | Committed samples + `.gitignore` nuance |
| TESTING.md described preset embedding | vs `test_tutorial_assets.py` | Reworded |
| TESTING.md implied T17–T19 blocked on fixtures | vs stubs + `ENTERPRISE_NOTEBOOKS.md` | Clarified |
| Docs YAML-only file config | `yaml.safe_load` + JSON | `config.md`, `factories.md`, `loader.py` |

### Medium (addressed that pass)

| Issue | Notes |
|-------|--------|
| `plans/INDEX.md` missing notebook row | Added `notebook-onboarding-refresh.md` |
| `root-package.md` missing loader exports | Added `load_logging_config`, `clear_logging_config_cache` |
| EXAMPLES-AUDIT workspace narrative | Added `jupyter_workspace` chain |

### Low (ongoing)

| Issue | Notes |
|-------|--------|
| Version literals across docs | Drift on release |
| `utils/*` growth vs `utils.md` | Re-audit when exporting new helpers |

_Add new rows under a dated subsection when you run the next full audit._

### 2026-03-21 — `docs/modules/*` pass

- Synced module pages with `hydra_logger/*/ __init__.py` exports, pipeline layout, WebSocket simulated-transport behavior (INFO vs warning), `utils` internal vs public split, `core` vs root logger-manager exports, config package file list + `get_enterprise_config` import note, `types` `LogLayer` enum vs config model caveat.

### 2026-03-21 — remainder pass (policy, index, workflow)

- **`RELEASE_POLICY.md`:** fixed enterprise preset API (`get_named_config("enterprise")` / `get_enterprise_config`, not `ConfigurationTemplates.get_named_config`).
- **`MODULE_COVERAGE_MATRIX.md`:** `extensions/security` → **covered** (per `extensions.md` + `DataRedaction`).
- **`WORKFLOW_ARCHITECTURE.md`:** AsyncLogger sequence labels aligned with `info` / `*_async` methods.
- **`ARCHITECTURE.md`:** links to `OPERATIONS`, `LOGGER_CONFIGURATION_TEST`, `EDA_MICROSERVICES_GUIDE`, root `SECURITY.md`.
- **`DOCS_CODEBASE_ALIGNMENT.md`:** `SECURITY.md`, sibling `benchmark/` + `tests/` tables, enforcement rows for `tests/benchmark`, `tests/scripts`, `check_version_consistency.py`.

### 2026-03-16 — documentation ↔ codebase commit bundle

- **`README.md`:** quick link to this alignment hub.
- **`tests/README.md`:** `tests/benchmark/` + `tests/scripts/` in layout tree.
- **`root-package.md`:** symmetry check vs `hydra_logger.__all__`.
- **`scripts/dev/run_notebook_smoke.py`:** docstring note aligned with `TESTING.md` (T17–T19 / stubs).
- **`hydra_logger/config/loader.py`:** YAML+JSON docstrings (already in bundle).
- Restored committed tutorial **`.log`** samples under `examples/logs/` where they had been removed locally.

### 2026-03-21 — `README.md` benchmark snapshot (`pr_gate`)

- Replaced stale nightly-style bullets with **headline metrics** from latest `benchmark_latest.json` / `pr_gate` run; pointed readers to **`repetition_stats`** in JSON and to **`nightly_truth`** for heavy regression.
- Operations snippet: `benchmark/performance_benchmark.py --profile pr_gate`.

### 2026-03-21 — `README.md` enterprise surface

- **Public API snapshot** table aligned with `hydra_logger.__init__.__all__` + symmetry-check command.
- **Enterprise adoption** bullets (governance, security, audits, operations pointers).
- **Quick links:** `SECURITY.md`, `docs/modules/root-package.md`.
- **Examples:** `getSyncLogger`, `CompositeLogger(components=[...])`, `ConfigurationTemplates().get_template(...)`, `clear_logging_config_cache`, stderr interception opt-in; corrected template API (no `ConfigurationTemplates.get_named_config`).

