# Notebook onboarding refresh (implemented)

## Phase 1 — complete

- **Storyboard (T01-shaped):** §0 pip → §1 setup (bootstrap, `source_hidden`) → §2 imports → §3 config path → §5 scenario → §6 results (code or markdown-only) → iterate note.
- **Configs:** Notebooks load only from **`examples/config/`** in the clone (`_find_hydra_repo` + `prepare_notebook_workspace`); no embedded / temp-mirrored preset trees.
- **Typography:** Generated markdown avoids `#` / `##`; uses `####` titles, `**§N — …**`, and `<small>` hints.
- **Tests:** `tests/examples/test_tutorial_assets.py` — on-disk `extends:` closure checks, clean VCS state, no `_STANDALONE_CONFIGS` in committed notebooks.

## Phase 2 — complete

- **README:** `examples/tutorials/notebooks/README.md` — prerequisites, clone resolution, troubleshooting, T16 vs T20, CI smoke, VCS conventions.
- **Governance:** `docs/tutorials/ENTERPRISE_NOTEBOOKS.md` — config ownership, sensitive data, operations (linked from notebooks README).
- **Clean diffs:** `write_notebook_json` + `normalize_notebook_for_version_control` clear `outputs` / `execution_count`.
- **§0 CI:** `%pip` code cells tagged `skip-ci`; `scripts/dev/run_notebook_smoke.py` strips them before execute.
- **Extras:** `setup.py` → `notebook_smoke` (`nbformat`, `nbconvert`, `ipykernel`).
- **CI:** `.github/workflows/ci.yml` job `notebook-smoke` (T01+T02).
- **Policy:** T17–T19 excluded from smoke until fixtures exist — documented in `docs/TESTING.md` and `docs/audit/EXAMPLES-AUDIT.md`.
- **Tests:** clean VCS state + `skip-ci` tag assertions.

## Workstream M — Single workspace API (complete)

- **`utility.prepare_notebook_workspace()`** in `examples/tutorials/utility/__init__.py`: honors
  `HYDRA_LOGGER_REPO` (`chdir` when valid), optional `repo_candidate` for tests, then
  `notebook_bootstrap()`; returns `(repo_root, True)`.
- **§1 cells:** minimal stdlib stub + `_find_hydra_repo` + `prepare_notebook_workspace(repo_candidate=...)`
  (no temp `examples/config/` materialization).
- **Tests:** `tests/examples/test_tutorial_utility.py`, `test_generated_notebooks_use_prepare_notebook_workspace`
  in `test_tutorial_assets.py`.
- **Docs:** `examples/tutorials/notebooks/README.md` — §1 workspace API.

## Source of truth

- `examples/tutorials/notebooks/*.ipynb` (committed notebooks)
- `examples/tutorials/utility/__init__.py` (workspace API)
- `scripts/dev/run_notebook_smoke.py`
