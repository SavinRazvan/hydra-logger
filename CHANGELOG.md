# Changelog

All notable, verified changes to Hydra-Logger are documented here.

## Governance Note

- `CHANGELOG.md` is the canonical, auditable release log.
- Historical, pre-standard entries were archived to `docs/archive/CHANGELOG_legacy.md`.
- New releases must add concise notes here, grouped by Added/Changed/Fixed.

## [Unreleased]

### Added

- Optional **real WebSocket** transport via `WebSocketHandler(..., use_real_websocket_transport=True)`
  (requires `websockets` / `network` extra).
- `scripts/release/check_pypi_parity.py` and optional `preflight.py --pypi-parity` for
  post-publish PyPI metadata verification.
- Shared messaging for integration-only destinations (`hydra_logger.utils.destination_contracts`).
- Corpus tests documenting regex redaction limits (`tests/extensions/security/test_data_redaction_corpus.py`).

### Changed

- CI lint/security jobs use explicit **report + gate** steps instead of shell `|| true` swallowing.
- Documentation: reliability defaults vs enterprise presets, operator baseline, redaction limits.

## [0.5.3] - 2026-03-19

### Changed

- CI lint: `flake8` now fails the build on pyflakes/pycodestyle issues under black’s
  line length (88); `E501` and cyclomatic complexity remain intentionally deferred
  (see `docs/TESTING.md`, `.flake8`).

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
