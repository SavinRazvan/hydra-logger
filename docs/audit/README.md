# Audit Artifacts

This folder stores audit evidence, not implementation plans.

Use these files to track code-to-doc alignment, findings severity, and follow-up actions over time.

## What To Store Here

- Per-run results files (for example: `module-docs-2026-03-15.results.md`)
- Coverage snapshots and tracking tables
- Standard templates used by agents and maintainers

## File Naming Convention

- Results: `<initiative>-YYYY-MM-DD.results.md`
- Keep one run per file so history remains traceable.

## Lifecycle

- `draft`: initial findings captured, pending validation
- `validated`: findings verified with code references
- `closed`: fixes completed or deferred with explicit rationale

## Severity Model

- `High`: correctness or user-facing behavior mismatch
- `Medium`: drift risk, incomplete standardization, or ambiguous guidance
- `Low`: clarity/consistency improvements without immediate risk

## Required Sections In Every Results File

1. Scope and inputs
2. Findings by severity (High/Medium/Low)
3. Evidence references (file paths and symbols)
4. Coverage matrix snapshot
5. Decisions (`fixed now` vs `deferred`)
6. Next 3 actions
7. Validation checklist
8. Owner/date/status

## Canonical Companions

- Planning artifacts belong in `docs/plans/`.
- Module-level baseline audit remains in `docs/MODULE_DOCS_AUDIT.md`.
