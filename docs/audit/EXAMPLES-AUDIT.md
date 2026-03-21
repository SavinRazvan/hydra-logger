# EXAMPLES Audit

## Scope And Goal

This audit captures every file currently under `examples/` and records:

- file path
- intended goal/purpose
- onboarding track/group
- risk or cleanup notes for refactor follow-up

The focus is repository-internal evidence only (file names and in-repo content intent), to prepare the next refactor pass.

## Current layout (maintained)

Use this as the **source of truth** for onboarding.

- **CLI tutorial scripts:** `examples/tutorials/cli_tutorials/t01_*.py` … `t20_*.py`
- **Notebooks:** `examples/tutorials/notebooks/t##_*.ipynb` (committed; edit in Jupyter — clear outputs for VCS)
- **Notebook workspace:** `examples/tutorials/utility/` — `prepare_notebook_workspace()`, `notebook_bootstrap()`, `resolved_cwd()`, `HYDRA_LOGGER_REPO`, repo-root cwd
- **Shared (CLI-focused):** `examples/tutorials/shared/` — `run_all_cli_tutorials.py` (run all `t*.py` with streamed output), `cli_tutorial_footer.py` (Console / Files / Takeaway footer), `path_bootstrap.py`, `artifact_checks.py`, `tutorial_runtime.py`
- **Configs:** `examples/config/*` — see **Config presets (in tree)** below and `examples/config/README.md` (`base_log_dir` / short `path` stems)
- **Outputs:** `examples/logs/cli-tutorials/` (CLI) and `examples/logs/notebooks/` (notebooks; gitignored)
- **Smoke runners:** `examples/run_all_examples.py` (pass/fail summary); `examples/tutorials/shared/run_all_cli_tutorials.py` (streamed log of each script)
- **Tests:** `tests/examples/` (`pytest tests/examples -q`) — assets, runners, branch coverage, `utility`, footer/discovery tests
- **Docs:** `examples/README.md`, `examples/tutorials/README.md`, `examples/tutorials/notebooks/README.md`, `docs/TESTING.md`, `docs/tutorials/ENTERPRISE_NOTEBOOKS.md`

### Config presets (in tree)

`base_default.yaml`, `base_minimal.yaml`, `base_overlay_debug.yaml`, `dev_console_file.yaml`, `dev_console_file.json`, `prod_jsonl_strict.yaml`, `network_http_basic.yaml`, `network_http_batched.yaml`, `network_ws_basic.yaml`, `network_socket_datagram.yaml`, `enterprise_multi_layer_api_worker.yaml`, `enterprise_onboarding_starter.yaml`, `tutorial_t01_enterprise_layers.yaml`, `tutorial_t02_configuration_recipes.yaml`.

### Legacy numbered `examples/01_*.py` … `17_*.py`

**Not shipped in this repository.** Canonical onboarding is `t01`–`t20` under `examples/tutorials/cli_tutorials/` plus notebooks. Old filenames and pre-rename config paths are preserved in **Config Rename / Standardization Matrix** and **Tutorial Path Migration Matrix** at the end of this file for historical reference only.

## In-tree inventory (high level)

| Path / artifact | Role |
|---|---|
| `examples/README.md` | Examples root: YAML vs Python, layout, quick start |
| `examples/run_all_examples.py` | Run all CLI tutorials; colored pass/fail |
| `examples/config/README.md` | Preset catalog, path rules for `base_log_dir` / stems |
| `examples/tutorials/README.md` | Tutorial index, track matrix, validation commands |
| `examples/tutorials/cli_tutorials/t01_*.py` … `t20_*.py` | Runnable tutorials; `t01` YAML, most others in-code `LoggingConfig` with `base_log_dir` / `log_dir_name` |
| `examples/tutorials/notebooks/t##_*.ipynb` | Generated notebooks; CI smoke **T01+T02** only; T17–T19 need clone + `benchmark/results/` for full narrative |
| `examples/tutorials/utility/` | Jupyter workspace API (`prepare_notebook_workspace`, …) |
| `examples/tutorials/shared/*.py` | CLI path bootstrap, footers, `run_all_cli_tutorials`, stubs/checks |

## Cross-File Findings

### 0) CLI vs notebook log filenames

- **CLI `cli_tutorials/t*.py`** sets `log_dir_name: cli-tutorials` and `tNN_…` stems under `examples/logs/cli-tutorials/`.
- **Notebooks** load the same `examples/config/` presets with `log_dir_name: notebooks` → `examples/logs/notebooks/` (shorter stems like `dev_app.jsonl`).

### 1) Path And Reference Consistency

- **Resolved:** notebooks live under `examples/tutorials/notebooks/`; READMEs updated.

### 2) Overlap And Redundancy

- Archived legacy scripts (`examples/01_*.py`–`17_*.py`, not in tree) overlapped conceptually with `t04`, `t12`–`t15`, etc.; use tutorials instead.
- `base_minimal.yaml` vs `base_default.yaml` are related baselines; keep differences documented in `examples/config/README.md`.

### 3) Potentially Stale Compatibility Shims

- `tutorials/t10_enterprise_profile_config.py` and `tutorials/t11_enterprise_policy_layers.py` contain compatibility-style runtime adjustments that should be revalidated against current runtime defaults.

### 4) Onboarding Flow Friction

- **Reduced:** `run_all_examples.py` and `shared/run_all_cli_tutorials.py` run CLI tutorials; `tests/examples` adds CI coverage; notebook smoke covers T01+T02.
- Legacy numbered scripts removed from tree (archival only).

## Suggested Refactor Priorities (Input For Next Instructions)

1. Fix notebook path references in both README files.
2. Decide canonical path:
   - keep legacy numbered examples as archive/reference, or
   - map each legacy file to a tutorial and deprecate duplicates.
3. Remove/modernize compatibility shims in `t10` and `t11` if no longer required.
4. Introduce a tutorial runner (or expand `run_all_examples.py`) to validate tutorial scripts as first-class onboarding.
5. Keep `base_default.yaml` / `base_minimal.yaml` roles explicit in preset docs (avoid user confusion).

## Tutorial Track Mapping (Requested Split)

This section maps tutorials into two primary delivery formats for professional onboarding.

### A) Notebook-First Tutorials

Use notebooks where step-by-step execution, inline explanation, and interactive tuning are the main user value.

- `t02_configuration_recipes`
- `t03_layers_customization`
- `t04_extensions_plugins`
- `t08_console_configuration_cookbook`
- `t09_levels_columns_date_and_destinations`
- `t12_network_http_typed_destination`
- `t13_network_ws_resilient_typed_destination`
- `t14_network_local_http_simulation`
- `t16_enterprise_config_templates_at_scale`
- `t17_enterprise_benchmark_comparison_workflow`
- `t18_enterprise_bring_your_own_config_benchmark`
- `t19_enterprise_nightly_drift_snapshot`
- `t20_notebook_hydra_config_onboarding` (already notebook anchor)

### B) Python Script Tutorials (`.py`)

Keep script-first where users benefit from running complete scenarios and observing real console/log artifacts end-to-end.

- `t01_production_quick_start`
- `t05_framework_patterns`
- `t06_migration_adoption`
- `t07_operational_playbook`
- `t10_enterprise_profile_config`
- `t11_enterprise_policy_layers`
- `t15_enterprise_network_hardening_playbook`

### C) Recommended Hybrid Cases

These topics should have both notebook and `.py` variants:

- `t01`: quick start notebook for onboarding + `.py` for deterministic CLI smoke runs.
- `t04`: notebook for extension authoring + `.py` for runtime verification behavior.
- `t12`/`t13`/`t14`: notebook for understanding flow + `.py` for automated deterministic checks.

## Target Folder Design For New Organization

Proposed file structure for a clean, scalable onboarding system:

- `examples/config/`
  - canonical reusable presets (already present)
- `examples/tutorials/cli_tutorials/`
  - runnable `.py` tutorials focused on end-to-end execution
- `examples/tutorials/notebooks/`
  - notebook tutorials focused on learning and guided experimentation
- `examples/tutorials/shared/`
  - optional shared helpers used by both tracks (path setup, artifact assertions, small deterministic stubs)
- `examples/tutorials/README.md`
  - single index with clear "Choose your path" section
- `examples/legacy/`
  - legacy numbered samples retained temporarily with explicit deprecation mapping to tutorial IDs

## Design Rules For New Files

Every new tutorial file should follow one schema:

1. Goal and audience
2. Required config preset(s) from `examples/config`
3. Run command (or notebook entry cell)
4. Expected artifacts (logs/json summaries)
5. Customization knobs (levels, formats, layers, destinations, extensions)
6. Failure mode checks and troubleshooting
7. Production notes and migration pointers

## Tutorial Authoring Standard (Notebook + `.py`)

Use this as the mandatory writing contract for all new tutorial content.

### Role

- Write a tutorial guide, not a chat transcript.
- Teach directly to the user as a guided lesson.
- Optimize for beginner success through hands-on steps.

### Purpose

- Tutorials teach by doing.
- Each tutorial must lead to a concrete completed outcome.
- Keep a safe, linear path with visible progress.

### Out Of Scope (Do Not Add)

- Deep architecture explanations
- Full reference-style option catalogs
- Broad optimization advice and production strategy branches
- Multiple alternative pathways in the same beginner tutorial

### Tone And Voice

- Use imperative, direct, calm language.
- Address the reader as the actor (`Create`, `Run`, `Open`).
- Prefer short sentences and unambiguous instructions.

### Mandatory Structure

All tutorials (notebooks and script-based markdown/tutorial docs) should follow this structure:

1. `# Title` (clear outcome)
2. `## What you will build` (1-2 sentences)
3. `## Before you start` (minimal prerequisites)
4. `## Steps` (linear, one logical action per step)
5. `## Final result` (explicit success state)

### Step Contract (Required For Every Step)

Each step must contain:

- short guiding sentence
- `Do this:` action bullets
- `You should now see:` result bullets

Each step must avoid:

- unrelated multi-action jumps
- deep theory blocks
- hidden assumptions or skipped setup

### Flow And Cognitive Load Rules

- Keep steps linear and progressive.
- One idea per step.
- Avoid context switching across unrelated concerns.
- Keep only content required to complete the lesson.

### Visible Outcome Rule

- Every tutorial must produce visible evidence:
  - console output, generated artifact, or both.
- Every step should move the user measurably forward.

### Strict Template

Use this template baseline:

```markdown
# [Title]

## What you will build
[Short outcome]

## Before you start
- Requirement
- Requirement

---

## Step 1 - [Action]

First, [guiding sentence].

Do this:
- Instruction
- Instruction

You should now see:
- Result

---

## Step 2 - [Action]

Next, [guiding sentence].

Do this:
- Instruction

You should now see:
- Result

---

## Final result

You now have:
- Outcome
```

### Tutorial Quality Gate Checklist

Before marking tutorial content complete, verify:

- tutorial reads as a guided lesson
- beginner can run it without missing context
- each step has visible progress
- unnecessary explanation is removed
- final success state is explicit

## Phased Refactor Plan For `examples/`

### Phase 1: Information Architecture

- Finalize tutorial IDs and ownership by track (`Notebook`, `.py`, `Hybrid`).
- Add explicit mapping table from legacy numbered examples to canonical tutorial IDs.
- Correct notebook path references in `examples/README.md` and `examples/tutorials/README.md`.

### Phase 2: Structural Reorganization

- **Done:** `examples/tutorials/cli_tutorials/`, `notebooks/`, `shared/`, `utility/` are the canonical layout.
- Historical: compatibility wrappers were only needed during migration (see migration matrices below).

### Phase 3: Content Normalization

- Align outputs: CLI under `examples/logs/cli-tutorials/`, notebooks under `examples/logs/notebooks/`.
- Remove stale compatibility shims in `t10` and `t11` if runtime no longer requires them.
- Ensure each tutorial references concrete config presets from `examples/config/`.

### Phase 4: Validation And Guardrails

- **Largely done:** `tests/examples/` + `run_all_examples.py` + `shared/run_all_cli_tutorials.py`; notebook smoke (`run_notebook_smoke.py`, T01+T02).
- **Remaining:** optional broader notebook execute in CI (T17–T19 need benchmark fixtures or seeded `benchmark/results/`).
- Keep deterministic command contract using `.hydra_env/bin/python`.

### Phase 5: Legacy Consolidation

- Keep legacy examples only as compatibility references.
- Mark duplicate legacy files as superseded by canonical tutorial IDs.
- Plan eventual archival once tutorial parity is complete.

## Audit Conclusion

The `examples/` tree is **tutorial-first**: `t01`–`t20` CLI scripts, generated notebooks, shared runners/footers, and a small **renamed** preset library under `examples/config/`. Remaining work is incremental (shim revalidation in `t10`/`t11`, benchmark fixtures for full notebook smoke on T17–T19), not structural.

## Implementation Status: Canonical Rebuild

Status: **applied**; docs/tests aligned with layout below (see also **Current layout** above).

### Canonical Structure Applied

- `examples/config/`
- `examples/tutorials/cli_tutorials/`
- `examples/tutorials/notebooks/`
- `examples/tutorials/shared/`
- `examples/tutorials/utility/` (notebook bootstrap)
- `examples/run_all_examples.py`
- `tests/examples/` (pytest guardrails for tutorials + runner + utility)

### Config Rename / Standardization Matrix

| Old path | New canonical path |
|---|---|
| `examples/config/minimal.yaml` | `examples/config/base_minimal.yaml` |
| `examples/config/base.yaml` | `examples/config/base_default.yaml` |
| `examples/config/overlay.yaml` | `examples/config/base_overlay_debug.yaml` |
| `examples/config/development_console_file.yaml` | `examples/config/dev_console_file.yaml` |
| `examples/config/development_console_file.json` | `examples/config/dev_console_file.json` |
| `examples/config/production_jsonl_strict.yaml` | `examples/config/prod_jsonl_strict.yaml` |
| `examples/config/multi_layer_api_worker.yaml` | `examples/config/enterprise_multi_layer_api_worker.yaml` |
| `examples/config/with_network_http.yaml` | `examples/config/network_http_basic.yaml` |
| `examples/config/with_network_http_batched.yaml` | `examples/config/network_http_batched.yaml` |
| `examples/config/with_network_ws.yaml` | `examples/config/network_ws_basic.yaml` |
| `examples/config/with_network_socket_datagram.yaml` | `examples/config/network_socket_datagram.yaml` |
| `examples/config/enterprise_onboarding_starter.yaml` | `examples/config/enterprise_onboarding_starter.yaml` (unchanged) |

### Tutorial Path Migration Matrix

| Old path | New canonical path |
|---|---|
| `examples/tutorials/t##_*.py` | `examples/tutorials/cli_tutorials/t##_*.py` |
| `examples/notebooks/t20_notebook_hydra_config_onboarding.ipynb` | `examples/tutorials/notebooks/t20_notebook_hydra_config_onboarding.ipynb` |
| (new notebooks track) | `examples/tutorials/notebooks/t##_*.ipynb` |
| (new shared helpers) | `examples/tutorials/shared/*.py` |

### Legacy Policy Applied

- Legacy numbered examples (`examples/01_...` through `examples/17_...`) are non-canonical.
- Canonical onboarding is now tutorial-first under `examples/tutorials/`.
- Tracking and migration are documented here; historical copies may remain in private archive paths managed outside canonical docs.
