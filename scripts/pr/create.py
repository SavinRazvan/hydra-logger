"""
Role: Creates pull requests with required attribution metadata.
Used By:
 - .agents/skills/PR_WORKFLOW.md
Depends On:
 - argparse
 - subprocess
Notes:
 - Standardizes PR body sections and enforces attribution footer fields.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return proc.returncode, output


def _current_branch() -> str:
    code, out = _run(["git", "branch", "--show-current"])
    if code != 0:
        return "unknown"
    return out.strip() or "unknown"


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
            details = f"environment preflight failed ({payload.get('status', 'unknown')}).\nSuggested fixes:\n{hint_text}"
    except json.JSONDecodeError:
        pass
    return False, details


def _build_body(
    summary_items: list[str],
    test_plan_items: list[str],
    actor: str,
    github_user: str,
    agents: str,
    made_with: str,
) -> str:
    lines: list[str] = ["## Summary"]
    lines.extend([f"- {item}" for item in summary_items])
    lines.append("")
    lines.append("## Test plan")

    if test_plan_items:
        lines.extend([f"- [x] `{item}`" for item in test_plan_items])
    else:
        lines.append("- [ ] Add verification commands before merge")

    lines.extend(
        [
            "",
            "## Attribution",
            f"- Author: {actor}",
            f"- GitHub-User: {github_user}",
            f"- Agent/s: {agents}",
            f"- Made-with: {made_with}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a pull request with standardized attribution footer."
    )
    parser.add_argument("--title", required=True, help="PR title.")
    parser.add_argument(
        "--summary",
        action="append",
        required=True,
        help="Summary bullet item (repeat for multiple).",
    )
    parser.add_argument(
        "--test-plan",
        action="append",
        default=[],
        help="Verification command/item for test plan (repeat for multiple).",
    )
    parser.add_argument(
        "--actor",
        required=True,
        help="Human author name for attribution footer.",
    )
    parser.add_argument(
        "--github-user",
        required=True,
        help='GitHub handle with @ prefix (example: "@SavinRazvan").',
    )
    parser.add_argument(
        "--agents",
        required=True,
        help='Agent list (example: "review-pr | prepare-pr | merge-pr").',
    )
    parser.add_argument(
        "--made-with",
        default="Cursor",
        help='Tool attribution label (default: "Cursor").',
    )
    parser.add_argument(
        "--base",
        default="main",
        help='Base branch (default: "main").',
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        default=False,
        help="Create as draft PR.",
    )
    parser.add_argument(
        "--body-out",
        default=".local/pr_body.md",
        help="Path to write generated PR body before gh call.",
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

    if not args.github_user.startswith("@"):
        print('ERROR: --github-user must start with "@".')
        return 2

    branch = _current_branch()
    if not branch or branch == "main":
        print("ERROR: run this command from a non-main feature branch.")
        return 2

    body = _build_body(
        summary_items=args.summary,
        test_plan_items=args.test_plan,
        actor=args.actor,
        github_user=args.github_user,
        agents=args.agents,
        made_with=args.made_with,
    )

    body_path = Path(args.body_out)
    body_path.parent.mkdir(parents=True, exist_ok=True)
    body_path.write_text(body, encoding="utf-8")

    cmd = [
        "gh",
        "pr",
        "create",
        "--title",
        args.title,
        "--base",
        args.base,
        "--body-file",
        str(body_path),
    ]
    if args.draft:
        cmd.append("--draft")

    code, out = _run(cmd)
    if out:
        print(out)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
