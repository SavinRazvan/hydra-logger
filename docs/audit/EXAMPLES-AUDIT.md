# EXAMPLES Audit

## Scope And Goal

This audit captures every file currently under `examples/` and records:

- file path
- intended goal/purpose
- onboarding track/group
- risk or cleanup notes for refactor follow-up

The focus is repository-internal evidence only (file names and in-repo content intent), to prepare the next refactor pass.

## Current layout (maintained)

Use this as the **source of truth** for onboarding; the big table below is partly **historical**.

- **Python tutorials:** `examples/tutorials/python/t01_*.py` … `t20_*.py`
- **Notebooks:** `examples/tutorials/notebooks/t##_*.ipynb` (regenerate via `temp_nb_factory/generate_notebooks.py`)
- **Notebook bootstrap:** `examples/tutorials/utility/` (`notebook_bootstrap`, `HYDRA_LOGGER_REPO`, repo-root cwd)
- **Configs:** `examples/config/*.yaml` (see `examples/config/README.md` for `base_log_dir` / path rules)
- **Outputs:** `examples/logs/tutorials/` (gitignored)
- **Smoke runner:** `examples/run_all_examples.py` (all Python tutorials)
- **Tests:** `tests/examples/` (`pytest tests/examples -q`) — assets, runner, branch coverage, `utility`
- **Docs:** `examples/README.md`, `examples/tutorials/README.md`, `examples/tutorials/notebooks/README.md`

## Full Inventory: File Name -> Goal

| File | Goal / Purpose | Track | Notes |
|---|---|---|---|
| `examples/README.md` | Main entrypoint; canonical layout + links to tutorials/tests. | docs/onboarding | Keep in sync with `tutorials/README.md`. |
| `examples/01_format_control.py` | Show per-destination output format control (`json`, plain, `json-lines`). | legacy/foundations | Keep as legacy baseline. |
| `examples/02_destination_control.py` | Show per-layer destination routing (`auth`, `api`, `error`). | legacy/foundations | Good behavior-oriented sample. |
| `examples/03_extension_control.py` | Show config-level extension enable/disable behavior. | legacy/extensions | Overlaps with `13_...` and `tutorials/t04`. |
| `examples/04_runtime_control.py` | Show runtime extension manager registration and toggling. | legacy/extensions | Demo-style broad fallback handling; simplify later. |
| `examples/05_custom_configurations.py` | Show custom layered configuration with security extension. | legacy/config | Partially overlaps tutorial config track. |
| `examples/06_basic_colored_logging.py` | Show basic colored console logging and file output. | legacy/console-format | Uses `.log` file with `json-lines` format; naming mismatch. |
| `examples/07_multi_layer_colored_logging.py` | Show layer-specific color output across domains. | legacy/layers | Multiple layers share same file path; can confuse separation. |
| `examples/08_mixed_console_file_output.py` | Show mixed console (colored) and file (plain) routing. | legacy/console-format | Solid practical example. |
| `examples/09_all_logger_types_colors.py` | Show sync, async, and composite logger usage side-by-side. | legacy/quick-start | Useful comparison sample. |
| `examples/10_disable_colors.py` | Show disabling console colors while keeping structured output. | legacy/console-format | `.log` name with `json-lines` format mismatch. |
| `examples/11_quick_start_basic.py` | Basic sync quick start with context and extra fields. | legacy/quick-start | Contains `sys.path` bootstrap hack; normalize later. |
| `examples/12_quick_start_async.py` | Basic async quick start using `create_async_logger`. | legacy/quick-start | Good concise async starter. |
| `examples/13_extension_system_example.py` | Show security/data-protection extension workflow. | legacy/extensions | Significant overlap with `tutorials/t04`. |
| `examples/14_class_based_logging.py` | Show class-based/OOP usage patterns and lifecycle methods. | legacy/framework-patterns | Large and advanced; not beginner-first. |
| `examples/15_eda_microservices_patterns.py` | Show EDA/microservice logging patterns and graceful shutdown. | legacy/operations | Strong advanced reference. |
| `examples/16_multi_layer_web_app.py` | Simulate multi-layer web app with concurrent logging flow. | legacy/framework-patterns | Heavy complexity for onboarding tier 1. |
| `examples/17_network_typed_destinations.py` | Show typed network destination usage with deterministic stubs. | legacy/network | Overlaps `tutorials/t12`-`t15`. |
| `examples/run_all_examples.py` | Execute all `examples/tutorials/python/*.py` and report pass/fail. | operations/tooling | Covered by `tests/examples/`; notebooks not executed in CI by default. |
| `examples/config/README.md` | Explain config preset library and loading flow. | docs/config | Clear and reusable. |
| `examples/config/minimal.yaml` | Minimal valid YAML logger config starter. | config/foundation | Currently duplicates `base.yaml`. |
| `examples/config/base.yaml` | Base preset intended for extension overlays. | config/foundation | Currently same content as `minimal.yaml`. |
| `examples/config/overlay.yaml` | Overlay for `extends` composition (e.g., debug level). | config/composition | Good `extends` teaching asset. |
| `examples/config/development_console_file.yaml` | Dev preset: console + file destinations via YAML. | config/dev | Clear and useful. |
| `examples/config/development_console_file.json` | JSON variant of development preset. | config/dev | Useful for JSON-driven environments. |
| `examples/config/production_jsonl_strict.yaml` | Strict production preset with reliability/path controls. | config/prod | High-value production baseline. |
| `examples/config/multi_layer_api_worker.yaml` | Multi-layer starter for API/worker/database split. | config/architecture | Good service template starter. |
| `examples/config/with_network_http.yaml` | Basic typed `network_http` preset. | config/network | Good starter. |
| `examples/config/with_network_http_batched.yaml` | HTTP preset with batch/retry behavior. | config/network | Good advanced network preset. |
| `examples/config/with_network_ws.yaml` | Basic typed `network_ws` preset. | config/network | Keep notes on simulated-vs-real WS behavior in docs. |
| `examples/config/with_network_socket_datagram.yaml` | Socket + datagram typed destination preset. | config/network | Good transport cookbook piece. |
| `examples/config/enterprise_onboarding_starter.yaml` | Enterprise onboarding preset combining strict + ops/network. | config/enterprise | Good enterprise starter artifact. |
| `examples/tutorials/README.md` | Tutorial index, validation commands, track matrix. | tutorials/docs | Single consolidated doc (no duplicate blocks). |
| `examples/tutorials/python/t01_production_quick_start.py` | YAML + `create_sync_logger` + layered DI demo. | tutorials/quick-start | Pairs with notebook T01 (multi-cell). |
| `examples/tutorials/python/t02_*.py` … `t19_*.py` | (same goals as before; paths now under `python/`). | tutorials/* | See tutorial README matrix. |
| `examples/tutorials/python/t20_notebook_hydra_config_onboarding.py` | Script twin for T20 notebook theme. | tutorials/notebook | Notebook lives under `notebooks/`. |
| `examples/tutorials/notebooks/t##_*.ipynb` | Generated hands-on tutorials; T01 multi-cell. | tutorials/notebook | Source: `temp_nb_factory/`. |
| `examples/tutorials/utility/` | Notebook path/bootstrap helpers. | tutorials/tooling | Used by generated notebook first cells. |
| `examples/tutorials/notebooks/temp_nb_factory/` | `generate_notebooks.py`, `scenarios.py`. | tutorials/tooling | Regenerate ipynb after edits. |

## Cross-File Findings

### 1) Path And Reference Consistency

- **Resolved:** notebooks live under `examples/tutorials/notebooks/`; READMEs updated.

### 2) Overlap And Redundancy

- Legacy extension examples (`03`, `04`, `13`) overlap with tutorial canonical flow (`t04`).
- Legacy network example (`17`) overlaps with `t12`-`t15`.
- `config/minimal.yaml` and `config/base.yaml` are currently semantically duplicated.

### 3) Potentially Stale Compatibility Shims

- `tutorials/t10_enterprise_profile_config.py` and `tutorials/t11_enterprise_policy_layers.py` contain compatibility-style runtime adjustments that should be revalidated against current runtime defaults.

### 4) Onboarding Flow Friction

- **Reduced:** `run_all_examples.py` runs Python tutorials; `tests/examples` adds CI coverage.
- Legacy numbered scripts removed from tree (archival only).

## Suggested Refactor Priorities (Input For Next Instructions)

1. Fix notebook path references in both README files.
2. Decide canonical path:
   - keep legacy numbered examples as archive/reference, or
   - map each legacy file to a tutorial and deprecate duplicates.
3. Remove/modernize compatibility shims in `t10` and `t11` if no longer required.
4. Introduce a tutorial runner (or expand `run_all_examples.py`) to validate tutorial scripts as first-class onboarding.
5. Differentiate `base.yaml` from `minimal.yaml` (or document intentional duplication).

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
- `examples/tutorials/python/`
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

- Introduce `examples/tutorials/python/` and `examples/tutorials/notebooks/`.
- Move or recreate files under the new layout while preserving tutorial IDs in names.
- Keep compatibility wrappers (or redirect docs) temporarily to avoid breaking user paths.

### Phase 3: Content Normalization

- Align all tutorial outputs to deterministic artifact paths under `examples/logs/tutorials/`.
- Remove stale compatibility shims in `t10` and `t11` if runtime no longer requires them.
- Ensure each tutorial references concrete config presets from `examples/config/`.

### Phase 4: Validation And Guardrails

- Expand tutorial validation beyond legacy `run_all_examples.py`.
- Add tutorial-track runner/checker for both `.py` and notebook smoke validation.
- Keep deterministic command contract using `.hydra_env/bin/python`.

### Phase 5: Legacy Consolidation

- Keep legacy examples only as compatibility references.
- Mark duplicate legacy files as superseded by canonical tutorial IDs.
- Plan eventual archival once tutorial parity is complete.

## Audit Conclusion

The `examples/` tree is rich and valuable, with strong enterprise tutorial coverage (`t01`-`t19`) and reusable config presets. The main cleanup opportunities are consistency and consolidation: fix cross-link path drift, reduce legacy/tutorial duplication, and ensure runtime-shim content reflects current behavior. This makes the next refactor safer and improves onboarding clarity.

## Implementation Status: Canonical Rebuild

Status: **applied**; docs/tests aligned with layout below (see also **Current layout** above).

### Canonical Structure Applied

- `examples/config/`
- `examples/tutorials/python/`
- `examples/tutorials/notebooks/` (+ `temp_nb_factory/` generator)
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
| `examples/tutorials/t##_*.py` | `examples/tutorials/python/t##_*.py` |
| `examples/notebooks/t20_notebook_hydra_config_onboarding.ipynb` | `examples/tutorials/notebooks/t20_notebook_hydra_config_onboarding.ipynb` |
| (new notebooks track) | `examples/tutorials/notebooks/t##_*.ipynb` |
| (new shared helpers) | `examples/tutorials/shared/*.py` |

### Legacy Policy Applied

- Legacy numbered examples (`examples/01_...` through `examples/17_...`) are non-canonical.
- Canonical onboarding is now tutorial-first under `examples/tutorials/`.
- Tracking and migration are documented here; historical copies may remain in private archive paths managed outside canonical docs.
