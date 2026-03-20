# PyPI publish and verify (hydra-logger)

Use this **after** `main` is green and you intend to ship the version in
`hydra_logger/__init__.py`.

## 0. Pre-flight (local or CI)

```bash
# From repo root; use your venv as needed (.hydra_env, etc.)
python scripts/dev/check_version_consistency.py
python -m pytest -q
python scripts/pr/check_slim_headers.py --all-python --strict
python scripts/release/preflight.py
```

Fold **`CHANGELOG.md` `[Unreleased]`** into a new dated section if it contains
shipped work, and bump `__version__` if the release is newer than the last tag.

## 1. Build distributions

```bash
python -m build
twine check dist/*
```

## 2. Upload to PyPI

Configure credentials (API token recommended). Example:

```bash
twine upload dist/*
```

## 3. Tag and GitHub Release

Align the tag with **`__version__`** (leading `v` is convention only; be
consistent with past releases):

```bash
git tag -a "v0.5.3" -m "Release 0.5.3"
git push origin "v0.5.3"
```

Create a **GitHub Release** for that tag; attach `dist/*` (sdist + wheel) or link
to provenance from CI.

## 4. Verify public index parity (required)

Wait until the new version is visible on PyPI (often seconds; sometimes longer
behind caches):

```bash
python scripts/release/check_pypi_parity.py --require-match
```

- Exit **0**: repo `__version__` and `Development Status` from `setup.py` match
  PyPI JSON for `hydra-logger`.
- Exit **non-zero**: fix metadata or wait for index propagation; do not treat the
  release as verified until this passes.

Optional informational mode (no gate):

```bash
python scripts/release/check_pypi_parity.py
```

## 5. Record evidence

Capture in PR/release notes or `docs/audit/FINAL_ENTERPRISE_HARDENING_SIGNOFF.md`
**Maintainer attestation**: command, date, result, and CI URL if applicable.
