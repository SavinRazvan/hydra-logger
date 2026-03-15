# Module Documentation Governance

This playbook standardizes how module docs are updated and verified.

## Acceptance Criteria

Treat a module docs change as complete only when all are true:

- Every affected package under `hydra_logger/` has a matching page in `docs/modules/`.
- Each page includes scope, key files, behavior/API, flow diagram, caveats, and maintenance notes.
- Cross-doc references (`README.md`, `docs/ARCHITECTURE.md`, `docs/modules/README.md`) remain valid.
- `docs/MODULE_DOCS_AUDIT.md` reflects current module coverage and open gaps.

## Update Triggers

Update module docs when any of these change:

- Public exports in `__init__.py` files.
- Module boundaries (`hydra_logger/<module>/` added, removed, renamed).
- Runtime behavior in logger flow, handler dispatch, or formatter selection.
- Configuration schema fields in `hydra_logger/config/models.py`.
- New or removed extension points.

## Update Workflow

```mermaid
flowchart LR
  A[Code change merged in branch] --> B[Identify touched module(s)]
  B --> C[Update module doc pages]
  C --> D[Update cross-links and index]
  D --> E[Run docs alignment audit]
  E --> F[Review in PR checklist]
  F --> G[Merge when docs and code match]
```

## Required Checklist (Per PR)

- [ ] Touched modules listed in PR description.
- [ ] Corresponding file in `docs/modules/` updated.
- [ ] `docs/modules/README.md` index updated when module boundaries changed.
- [ ] Mermaid diagrams adjusted when workflow changed.
- [ ] `docs/MODULE_DOCS_AUDIT.md` findings reviewed and refreshed when needed.

## Structure Standards

Each module page should include:

1. Scope and responsibility.
2. Key files map.
3. Public API surface (if exported).
4. Runtime flow or lifecycle notes.
5. Known risks or caveats.
6. Maintenance notes (what to re-check after changes).

## Definition Of Done

A module docs update is done when:

- The module page reflects current files and exported symbols.
- At least one workflow diagram remains accurate after the change.
- Related references in `README.md` and `docs/ARCHITECTURE.md` still point to valid docs.
