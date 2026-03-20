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

## PyPI classifiers

- **Development Status** is maintainer signaling on PyPI (maturity and review
  expectations). It is **not** a substitute for semver: treat runtime behavior
  and documented APIs as governed by the rules above.
- Moving toward **Production/Stable** requires explicit maintainer sign-off and
  normally ships with a **minor** or **major** release, updated consumer docs,
  and `CHANGELOG.md` notes.

## Runtime defaults vs enterprise presets

- Library **defaults** prioritize backward compatibility and gradual adoption
  (for example permissive reliability defaults and performance profiles called
  out in module docs).
- Stricter operational posture belongs in **documented presets** such as
  `get_enterprise_config()` and enterprise tutorials—not silent changes to
  implicit defaults.
- Changing **default** reliability, record profiling, or silent-drop behavior is
  normally a **MAJOR** bump with migration notes. If a team intentionally ships
  a default change on a **MINOR** line, it must be explicitly documented as safe
  with an opt-in migration path (prefer avoiding this pattern).

### Reliability and record profiling (operator contract)

| Control | Library default | Enterprise recommendation |
| --- | --- | --- |
| `strict_reliability_mode` | `False` | `True` in regulated / SRE-owned environments |
| `reliability_error_policy` | `"silent"` | `"warn"` or `"raise"` when dropped logs are unacceptable |
| Logger `performance_profile` / record creation | `"convenient"` (richer auto context) | `"minimal"` or `"balanced"` on hot paths (see `docs/PERFORMANCE.md`) |

- **Silent + NullHandler**: unsupported or integration-only destinations (for example
  `async_cloud` without a custom adapter) resolve to `NullHandler`; diagnostics follow
  `reliability_error_policy` / `strict_reliability_mode` (see tests under
  `tests/loggers/`).
- **Migration**: tightening defaults is a **MAJOR** change; today, adopt enterprise
  presets explicitly (`ConfigurationTemplates.get_named_config("enterprise")` or
  equivalent YAML) rather than assuming library defaults match production policy.

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
