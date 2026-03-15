# AGENTS.md

## Project Intent

`hydra-logger` is a modular Python logging library focused on:

- multiple logger types (sync, async, composite)
- multiple destinations and formats
- extensibility with low runtime overhead
- KISS-oriented, maintainable implementation

Keep work aligned with library ergonomics, reliability, and clear user-facing APIs.

## First Files To Read

1. `README.md`
2. `docs/ARCHITECTURE.md`
3. `docs/WORKFLOW_ARCHITECTURE.md`
4. `docs/PERFORMANCE.md`

## Engineering Guardrails

- Preserve backwards-compatible behavior for public imports in `hydra_logger/` unless an intentional breaking change is documented.
- Prefer small, reversible changes over large rewrites.
- Add or update tests in `tests/` whenever behavior changes.
- Avoid introducing project-specific process overhead that does not improve this repository.
- Keep imports at the top of files and follow existing Python style conventions.
- For Python code file headers, use slim metadata docstrings (`Role`, `Used By`, `Depends On`, `Notes`) and avoid redundant `File`/`Path` fields.
- Keep header compliance green with `python scripts/pr/check_slim_headers.py --all-python --strict`.

## Local Environment

- Canonical local environment: `.hydra_env` (project-local Conda prefix environment)
- Keep machine-specific artifacts out of version control (`.local/`, local logs, temporary files).

## PR Workflow Skills

Project-level skills live in `.agents/skills/`:

- `review-pr`
- `prepare-pr`
- `merge-pr`
- `audit-module-docs-alignment` (docs/code alignment audit for module documentation)
- `test-module-coverage` (module-focused tests, edge-case coverage, and coverage reporting)

Shared workflow guidance is in `.agents/skills/PR_WORKFLOW.md`.

Helper scripts:

- `python scripts/pr/review.py --pr <id-or-url> --actor "<name>" --agents "review-pr" [--github-user "<handle>"]`
- `python scripts/pr/prepare.py --pr <id-or-url> --actor "<name>" --agents "review-pr | prepare-pr" [--github-user "<handle>"]`
- `python scripts/pr/merge.py --pr <id-or-url> --actor "<name>" --agents "review-pr | prepare-pr | merge-pr" [--github-user "<handle>"]`
- `python scripts/pr/verify_publish.py --branch <current_branch>`
- `python scripts/pr/finalize.py --branch <feature_branch>`

## Cursor Project Config

- Keep repository-level Cursor config minimal and `hydra-logger` specific.
- Active project rules are in `.cursor/rules/`:
  - `pr-workflow-enforcement.mdc`
  - `execution-workflow-gates.mdc`
  - `slim-file-header.mdc`
- Worktree bootstrap is in `.cursor/worktrees.json` and should target Conda `.hydra_env` via `environment.yml`.
- Do not add external-project research packs or provider-specific architecture policies unless this repository explicitly adopts them.
