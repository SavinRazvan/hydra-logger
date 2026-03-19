"""
Role: Pytest guardrails for runtime blocking-call regressions.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - pathlib
 - re
Notes:
 - Prevents introducing blocking runtime calls in hydra_logger modules.
"""

import re
from pathlib import Path

FORBIDDEN_CALLS = (re.compile(r"\btime\.sleep\("),)
ALLOWED_FILES = {
    "hydra_logger/utils/stderr_interceptor.py",
}


def test_runtime_modules_do_not_use_forbidden_blocking_calls() -> None:
    root = Path("hydra_logger")
    findings = []
    for path in sorted(root.rglob("*.py")):
        rel = path.as_posix()
        if rel in ALLOWED_FILES:
            continue
        content = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(content.splitlines(), start=1):
            if any(pattern.search(line) for pattern in FORBIDDEN_CALLS):
                findings.append(f"{rel}:{line_no}: forbidden runtime blocking call")

    assert findings == [], "Forbidden runtime blocking calls found:\n" + "\n".join(
        findings
    )
