# Documentation Drift Hardening Plan

- Date: 2026-03-15
- Owner: @SavinRazvan
- Status: superseded
- Expected audit results file: `docs/audit/docs-drift-hardening-2026-03-15.results.md`

Superseded by: `.cursor/plans/master-architecture-no-drift_5a0a318c.plan.md`

## Outcome

Reduce documentation drift risk by standardizing module page structure, removing brittle static counts, and adding lightweight automated validation in CI for core documentation invariants.

## Scope And Source Of Truth

- Target docs:
  - `README.md`
  - `docs/modules/*.md`
  - `docs/modules/README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/WORKFLOW_ARCHITECTURE.md`
- Audit baselines:
  - `docs/MODULE_DOCS_AUDIT.md`
  - `docs/audit/MATRIX.md`
  - `docs/audit/module-docs-2026-03-15.results.md`
- New validation script:
  - `scripts/docs/validate_docs_contract.py`
- CI workflow target:
  - `.github/workflows/ci.yml` (or existing docs/lint workflow path)
- Out of scope:
  - Full prose rewrite of all docs
  - Functional code changes unrelated to docs/runtime contract clarity

## Audit-Derived Drivers

This plan directly addresses open low-risk drift findings from audit artifacts:

- Section naming inconsistency across module pages:
  - `Responsibilities` vs `Key Responsibilities`
  - `Caveats` vs `Caveats And Known Gaps`
- Static count drift risk in `README.md`:
  - text such as `Core Package: 49 Python files`

## Execution Phases

1. Define docs contract and normalization rules.
2. Standardize existing module pages to contract.
3. Remove static count claims and replace with durable wording.
4. Implement lightweight docs validation script.
5. Wire validation into CI and record audit evidence.

## Detailed Implementation Blueprint

### Phase 1 - Documentation contract

Define required section headers for every module page:

- `Scope`
- `Responsibilities`
- `Public Surface` (or `Behavior/API`, pick one canonical label)
- `Workflow/Flow`
- `Caveats And Known Gaps`
- `Maintenance Checklist`

Define canonical title/section normalization map to eliminate drift aliases.

### Phase 2 - Module page normalization

Apply consistent section names across `docs/modules/*.md`:

- rename non-canonical headings to canonical headings
- preserve existing technical content and Mermaid diagrams
- avoid semantic rewrites beyond naming and structure consistency

### Phase 3 - README hardening

Replace static counts with stable language:

- remove exact file counts that require manual updates
- describe scope using directory/package level statements
- if metrics are required, derive them from script output rather than static text

### Phase 4 - Validation script

Implement `scripts/docs/validate_docs_contract.py` with:

- module docs section presence checks
- check for forbidden static-count phrasing in `README.md`
- cross-link existence checks for canonical docs references
- output modes:
  - human-readable summary
  - `--json` for CI parsing

Exit code contract:

- `0` all checks pass
- `1` drift/warning findings in advisory mode
- `2` hard failures in strict mode

### Phase 5 - CI enforcement

Integrate validation in CI as non-blocking first (advisory), then strict after baseline stabilization.

Recommended progression:

1. advisory for 1-2 PR cycles
2. strict gating once false positives are resolved

## Acceptance Criteria

- [ ] All module docs use canonical section names.
- [ ] `README.md` has no brittle static file-count claims.
- [ ] `scripts/docs/validate_docs_contract.py` exists and validates agreed contract.
- [ ] CI executes docs contract validation on PRs.
- [ ] Audit results capture before/after evidence and residual deferred items.

## Definition Of Done

- [ ] Contract documented and applied repository-wide for module docs.
- [ ] Drift checks are automated and reproducible.
- [ ] CI runs docs contract validation deterministically.
- [ ] Findings and decisions are stored in dated audit results.

## Risks And Mitigations

- Risk: Overly strict checks generate noisy failures.
  - Mitigation: ship advisory-first and tighten incrementally.
- Risk: Section rename churn reduces blame clarity.
  - Mitigation: batch edits once, then enforce with script.
- Risk: Future contributors bypass docs updates.
  - Mitigation: include contract check in PR pipeline and template reminders.

## Audit Linkage

- Planned results artifact: `docs/audit/docs-drift-hardening-2026-03-15.results.md`
- Related historical audits:
  - `docs/audit/module-docs-2026-03-15.results.md`
  - `docs/audit/MATRIX.md`
