# Release policy and API compatibility

This document is the maintainer-facing contract for versioning, releases, and
consumer expectations.

## Semantic versioning

- **MAJOR**: intentional breaking changes to documented public APIs or default
  behaviors that require consumer action.
- **MINOR**: backward-compatible features, new optional configuration fields, or
  safe documentation-only clarifications that do not change runtime defaults.
- **PATCH**: bug fixes, diagnostics, and internal refactors without API surface
  changes.

## Public API

Stable imports are those documented in `README.md`, `docs/modules/`, and
`hydra_logger/__init__.py` (and subpackage `__init__.py` exports). Underscore
prefixed objects and modules marked experimental are not covered.

## Deprecation

- Deprecations are announced in `CHANGELOG.md` / release notes with a **minimum
  one minor version** warning period before removal, unless security-critical.
- Runtime `DeprecationWarning` may be used for programmatic call sites when the
  team opts in.

## Release artifacts

- **PyPI**: primary distribution channel; version must match `setup.py` /
  packaging metadata (enforced by `scripts/dev/check_version_consistency.py`).
- **GitHub Releases**: tag `v<version>` and attach `dist/*` (sdist + wheel) or
  link to CI-generated artifacts for supply-chain visibility.
- **GitHub Packages / private indices**: TLS and CA trust are environment
  concerns; prefer **GitHub Actions** with OIDC + `twine` over disabling TLS
  verification locally.

## Pre-release checklist

1. `python -m pytest -q` and coverage gates satisfied locally or in CI.
2. `python scripts/pr/check_slim_headers.py --all-python --strict` (or CI lint job).
3. `python scripts/release/preflight.py` when cutting a release branch.
4. Dependency audit artifacts from CI (`bandit`, `pip-audit`) reviewed for new
   high-severity items.
5. `CHANGELOG.md` updated with migration notes for any behavior or default
   change.

## Sign-off

Maintainers acknowledge that merges to `main` are release candidates: CI must
stay green on enforced formatters, tests, and documented security report
uploads. Escalate exceptions via PR notes with explicit risk and rollback steps.
