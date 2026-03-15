"""
Role: Runs preparation gates and emits local prepare artifact.
Used By:
 - .agents/skills/prepare-pr/SKILL.md
Depends On:
 - argparse
 - pathlib
 - subprocess
Notes:
 - Runs required gates (`pytest -q` and strict slim-header check) and writes `.local/prep.md`.
 - Pass `--skip-gates` when gates were already verified externally.
 - The script writes attribution and gate evidence; agents append findings and residual risks.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

GATES = [
    ["python", "-m", "pytest", "-q"],
    ["python", "scripts/pr/check_slim_headers.py", "--all-python", "--strict"],
]


def _run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip()


def _current_branch() -> str:
    proc = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True
    )
    return proc.stdout.strip() or "unknown"


def _head_sha() -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    return proc.stdout.strip() or "unknown"


def _run_env_preflight(skip_env_check: bool) -> tuple[bool, str]:
    if skip_env_check:
        return True, ""

    code, out = _run([sys.executable, "scripts/dev/check_env_health.py", "--strict", "--json"])
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
    parser = argparse.ArgumentParser(
        description="Run PR prepare gates and artifact generation."
    )
    parser.add_argument("--pr", required=True, help="PR number or URL")
    parser.add_argument(
        "--actor", required=True, help="Actor display name performing prepare action"
    )
    parser.add_argument(
        "--github-user",
        default="",
        help='Optional GitHub handle (example: "@your-handle").',
    )
    parser.add_argument(
        "--agents",
        required=True,
        help='Agent list, e.g. "review-pr | prepare-pr | merge-pr"',
    )
    parser.add_argument(
        "--skip-gates",
        action="store_true",
        default=False,
        help=(
            "Skip running gates inside the script. Use when the agent already ran and "
            "verified all gates; the artifact will record gates as externally verified."
        ),
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

    local_dir = Path(".local")
    local_dir.mkdir(exist_ok=True)
    prep_file = local_dir / "prep.md"

    branch = _current_branch()
    head_sha = _head_sha()
    github_user = args.github_user.strip()

    attribution_lines = [
        f"- Action-By: {args.actor}",
        f"- Prepared-By: {args.actor}",
    ]
    if github_user:
        attribution_lines.append(f"- GitHub-User: {github_user}")
    attribution_lines.extend(
        [
            f"- Agent/s: {args.agents}",
            f"- Branch: {branch}",
            f"- HEAD SHA: {head_sha}",
        ]
    )

    lines = [
        f"# Prepare Artifact ({args.pr})",
        "",
        "## Attribution",
        *attribution_lines,
        "",
        "## Gate Results",
    ]

    failed = False
    if args.skip_gates:
        lines.append("- gates: externally verified by agent before this script call")
    else:
        for gate in GATES:
            code, output = _run(gate)
            label = "PASS" if code == 0 else "FAIL"
            lines.append(f"- `{' '.join(gate)}` -> {label}")
            if code != 0:
                failed = True
                lines.append("")
                lines.append("```text")
                lines.append(output)
                lines.append("```")

    lines.extend(
        [
            "",
            "## Status",
            "- PR is ready for /merge-pr" if not failed else "- NOT READY",
            "",
            "## Agent Notes",
            "- (agent: add resolved findings, residual risks, and follow-ups below)",
        ]
    )
    prep_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Created {prep_file}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
