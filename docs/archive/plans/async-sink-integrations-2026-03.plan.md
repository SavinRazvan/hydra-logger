# Async Sink Integrations Roadmap Plan

- Date: 2026-03-15
- Owner: @SavinRazvan
- Status: superseded
- Expected audit results file: `docs/audit/async-sink-integrations-2026-03-15.results.md`

Superseded by: `.cursor/plans/master-architecture-no-drift_5a0a318c.plan.md`

## Outcome

Define and implement a staged roadmap for async sink integrations that clearly separates built-in handler capabilities from custom extension points, preventing ambiguous documentation and reducing runtime expectation mismatch.

## Scope And Source Of Truth

- Runtime code targets:
  - `hydra_logger/handlers/`
  - `hydra_logger/loggers/`
  - `hydra_logger/config/models.py`
  - `hydra_logger/config/defaults.py`
- Docs targets:
  - `docs/modules/handlers.md`
  - `docs/modules/config.md`
  - `README.md` destination/support sections
  - `docs/MODULE_DOCS_AUDIT.md`
- Audit references:
  - `docs/audit/module-docs-2026-03-15.results.md` (deferred item source)
  - `docs/audit/MATRIX.md`
- Out of scope:
  - Full redesign of logger architecture
  - Non-async handler family refactors with no integration relevance

## Problem Statement

Current docs correctly mark some integration fields as custom/roadmap, but runtime and docs need an explicit contract:

- What is built-in and production-supported now
- What is configurable but requires custom implementation
- What is planned for future built-in support

Without this, users can misinterpret configuration fields as guaranteed built-in capability.

## Execution Phases

1. Baseline and classify current sink capabilities.
2. Define integration contract and support tiers.
3. Create delivery slices for next built-in async sinks.
4. Add compatibility and migration notes.
5. Validate behavior/docs parity and capture audit evidence.

## Detailed Implementation Blueprint

### Phase 1 - Capability inventory

Inventory current built-in async-capable destination families and document:

- guaranteed built-in support
- partial support with caveats
- unsupported (custom implementation required)

Produce a table keyed by destination type and runtime path.

### Phase 2 - Contract and support tiers

Define support levels in docs and config schema:

- `built_in`: implemented and tested in core handlers
- `custom_extension`: configuration accepted but behavior requires custom plugin/handler
- `roadmap`: planned but not yet implemented

Reflect tiers in:

- `docs/modules/config.md`
- `docs/modules/handlers.md`
- relevant config model field descriptions

### Phase 3 - Delivery slices

Choose the next 1-2 high-value built-in integrations and specify:

- minimal viable behavior
- failure semantics and retry/backpressure strategy
- observability requirements (logging/metrics)
- test coverage requirements

Each slice should be independently shippable and reversible.

### Phase 4 - Compatibility and migration

Define migration notes for users currently relying on custom integrations:

- non-breaking defaults
- opt-in flags where behavior changes
- deprecation strategy for ambiguous config fields (if needed)

### Phase 5 - Validation

Validate that docs, config models, and runtime behavior are aligned:

- config accepts only documented contracts
- runtime error messages identify unsupported built-in assumptions
- module docs and README match implemented behavior

## Acceptance Criteria

- [ ] A source-of-truth capability matrix exists for async sink destinations.
- [ ] Support tiers are explicitly defined and reflected in docs/config.
- [ ] Deferred ambiguity in module docs audit is resolved or explicitly re-deferred with rationale.
- [ ] At least one concrete delivery slice is scoped with implementation-ready requirements.
- [ ] Audit results file records decisions (`fixed now` vs `deferred`) with evidence.

## Definition Of Done

- [ ] Users can identify built-in vs custom vs roadmap sink support without ambiguity.
- [ ] Runtime and docs communicate unsupported paths consistently.
- [ ] Roadmap slices are prioritized and ready for engineering execution.
- [ ] Audit evidence captured in dated results artifact.

## Risks And Mitigations

- Risk: Over-promising integrations not yet implemented.
  - Mitigation: enforce support-tier labeling and CI/docs checks.
- Risk: Breaking existing custom integrations.
  - Mitigation: preserve compatibility defaults and provide migration notes.
- Risk: Scope creep from broad integration surface.
  - Mitigation: prioritize 1-2 slices and defer remaining items explicitly.

## Audit Linkage

- Planned results artifact: `docs/audit/async-sink-integrations-2026-03-15.results.md`
- Related historical audits:
  - `docs/audit/module-docs-2026-03-15.results.md`
