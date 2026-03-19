# Changelog

All notable, verified changes to Hydra-Logger are documented here.

## Governance Note

- `CHANGELOG.md` is the canonical, auditable release log.
- Historical, pre-standard entries were archived to `docs/archive/CHANGELOG_legacy.md`.
- New releases must add concise notes here, grouped by Added/Changed/Fixed.

## [0.5.2] - 2026-03-19

### Changed

- PyPI **Development Status** classifier updated to **Beta** (signals hardened CI
  and governance maturity; no intentional public API changes in this release).
- Documented how PyPI classifiers relate to semver and how runtime defaults differ
  from enterprise presets (`docs/RELEASE_POLICY.md`).

## [0.5.1] - 2026-03-18

### Changed

- Aligned documentation with current runtime behavior, module exports, and onboarding tutorial outputs.
- Updated package/runtime version references to `0.5.1` across canonical version-bearing files and templates.

## [0.5.0] - 2026-03-17

### Changed

- Rolled out project version `0.5.0` across canonical package metadata and dependent references.
- Added CI and workflow version-consistency enforcement via `scripts/dev/check_version_consistency.py`.
- Updated plan/audit tracking artifacts for release governance evidence.
