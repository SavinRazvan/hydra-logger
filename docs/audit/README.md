# Audit artifacts

This directory holds **maintainer-facing audit and sign-off** records: traceability
from assessment findings to code, tests, and docs.

| Document | Purpose |
| --- | --- |
| [**DOCS_CODEBASE_ALIGNMENT.md**](DOCS_CODEBASE_ALIGNMENT.md) | **Master index:** every major doc path, enforcement (tests/CI), coverage matrix, re-run commands, finding log. Start here for “are docs and code aligned?” |
| [EXAMPLES-AUDIT.md](EXAMPLES-AUDIT.md) | `examples/` tree inventory, CLI vs notebook outputs, preset list. |
| [FINAL_ENTERPRISE_HARDENING_SIGNOFF.md](FINAL_ENTERPRISE_HARDENING_SIGNOFF.md) | Resolved / intentional / deferred matrix with evidence links (enterprise hardening slice). |
| [PYPI_PUBLISH_AND_VERIFY.md](PYPI_PUBLISH_AND_VERIFY.md) | Ordered steps to build, upload, tag, GitHub Release, and run `check_pypi_parity.py --require-match`. |

Related:

- [Release checklist](../RELEASE_CHECKLIST.md)
- [Release policy](../RELEASE_POLICY.md)
- [Module coverage matrix](../modules/MODULE_COVERAGE_MATRIX.md)
