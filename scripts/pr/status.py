"""
Role: Repository automation for status.
Used By:
 - Repository maintainers invoking automation commands.
Depends On:
 - argparse
 - json
 - pathlib
 - subprocess
 - sys
 - typing
Notes:
 - Implements PR workflow automation for status actions.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return proc.returncode, output


def _current_branch() -> str:
    code, out = _run(["git", "branch", "--show-current"])
    if code != 0:
        return "unknown"
    return out.strip() or "unknown"


def _upstream(branch: str) -> str:
    code, out = _run(["git", "rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}"])
    if code != 0:
        return ""
    return out.strip()


def _dirty_status() -> list[str]:
    code, out = _run(["git", "status", "--short"])
    if code != 0 or not out:
        return []
    return [line for line in out.splitlines() if line.strip()]


def _bool_file(path: str) -> bool:
    return Path(path).exists()


def _prep_ready() -> bool:
    prep_path = Path(".local/prep.md")
    if not prep_path.exists():
        return False
    content = prep_path.read_text(encoding="utf-8")
    return "PR is ready for /merge-pr" in content


def _gh_pr_payload() -> dict[str, Any]:
    code, out = _run(
        [
            "gh",
            "pr",
            "view",
            "--json",
            "number,url,state,headRefName,baseRefName,mergeStateStatus,statusCheckRollup",
        ]
    )
    if code != 0:
        return {}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {}


def _checks_summary(checks: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"pass": 0, "pending": 0, "fail": 0, "other": 0}
    for check in checks:
        state = str(check.get("conclusion") or check.get("status") or "").lower()
        if state in {"success", "pass", "passed"}:
            summary["pass"] += 1
        elif state in {"queued", "in_progress", "pending", "expected"}:
            summary["pending"] += 1
        elif state in {"failure", "failed", "error", "timed_out", "cancelled"}:
            summary["fail"] += 1
        else:
            summary["other"] += 1
    return summary


def _run_env_preflight(skip_env_check: bool) -> tuple[bool, str]:
    if skip_env_check:
        return True, ""

    code, out = _run(
        [
            sys.executable,
            "scripts/dev/check_env_health.py",
            "--strict",
            "--auto-upgrade-toolchain",
            "--json",
        ]
    )
    if code == 0:
        return True, ""

    details = out or "environment preflight failed"
    try:
        payload = json.loads(details)
        checks = payload.get("checks", [])
        hints = [
            str(check.get("recommended_fix", "")).strip()
            for check in checks
            if check.get("status") in {"warn", "fail"}
        ]
        hint_text = "\n".join(f"- {hint}" for hint in hints if hint)
        if hint_text:
            details = (
                f"environment preflight failed ({payload.get('status', 'unknown')}).\n"
                f"Suggested fixes:\n{hint_text}"
            )
    except json.JSONDecodeError:
        pass
    return False, details


def main() -> int:
    parser = argparse.ArgumentParser(description="Show compact PR workflow status.")
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Emit JSON (default); when omitted, emits readable text.",
    )
    parser.add_argument(
        "--skip-env-check",
        action="store_true",
        default=False,
        help="Skip `.hydra_env` preflight (emergency use only).",
    )
    args = parser.parse_args()

    preflight_ok, preflight_details = _run_env_preflight(args.skip_env_check)
    if not preflight_ok:
        print(f"ERROR: {preflight_details}")
        print("Use --skip-env-check to override temporarily.")
        return 2

    branch = _current_branch()
    upstream = _upstream(branch) if branch != "unknown" else ""
    dirty = _dirty_status()
    pr_payload = _gh_pr_payload()
    checks = pr_payload.get("statusCheckRollup", []) if pr_payload else []
    checks_summary = _checks_summary(checks if isinstance(checks, list) else [])

    status: dict[str, Any] = {
        "branch": branch,
        "upstream": upstream,
        "upstream_ok": bool(upstream and upstream == f"origin/{branch}"),
        "dirty_count": len(dirty),
        "dirty_paths": dirty,
        "artifacts": {
            "review": _bool_file(".local/review.md"),
            "prep": _bool_file(".local/prep.md"),
            "merge": _bool_file(".local/merge.md"),
            "prep_ready": _prep_ready(),
        },
        "pr": {
            "number": pr_payload.get("number"),
            "url": pr_payload.get("url"),
            "state": pr_payload.get("state"),
            "head": pr_payload.get("headRefName"),
            "base": pr_payload.get("baseRefName"),
            "merge_state": pr_payload.get("mergeStateStatus"),
            "checks_summary": checks_summary,
        },
    }

    if args.json:
        print(json.dumps(status, indent=2))
        return 0

    print(f"branch: {status['branch']}")
    print(f"upstream: {status['upstream'] or '<none>'}")
    print(f"dirty_count: {status['dirty_count']}")
    print(
        "artifacts:"
        f" review={status['artifacts']['review']}"
        f" prep={status['artifacts']['prep']}"
        f" merge={status['artifacts']['merge']}"
        f" prep_ready={status['artifacts']['prep_ready']}"
    )
    print(
        "pr:"
        f" #{status['pr']['number']} state={status['pr']['state']}"
        f" merge_state={status['pr']['merge_state']}"
        f" checks={status['pr']['checks_summary']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
