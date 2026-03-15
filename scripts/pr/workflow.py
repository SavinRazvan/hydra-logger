"""
Role: Runs deterministic PR workflow phases end-to-end.
Used By:
 - .agents/skills/PR_WORKFLOW.md
Depends On:
 - argparse
 - json
 - subprocess
Notes:
 - Wraps create/review/prepare/merge/finalize steps to reduce prompt-heavy orchestration.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


def _run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return proc.returncode, output


def _run_or_fail(cmd: list[str]) -> None:
    code, output = _run(cmd)
    if output:
        print(output)
    if code != 0:
        raise RuntimeError(f"command failed ({code}): {' '.join(cmd)}")


def _current_branch() -> str:
    code, output = _run(["git", "branch", "--show-current"])
    if code != 0:
        return "unknown"
    return output.strip() or "unknown"


def _resolve_pr_number(explicit_pr: str | None) -> str:
    if explicit_pr:
        return explicit_pr
    code, output = _run(["gh", "pr", "view", "--json", "number"])
    if code != 0:
        raise RuntimeError("unable to resolve current PR number; pass --pr explicitly")
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError("unable to parse gh pr view output") from exc
    number = payload.get("number")
    if number is None:
        raise RuntimeError("gh pr view returned no PR number")
    return str(number)


def _load_profile(path: str) -> dict[str, Any]:
    profile_path = Path(path)
    if not profile_path.exists():
        return {}
    try:
        return json.loads(profile_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON profile: {path}") from exc


def _arg_or_profile(cli_value: str | None, profile: dict[str, Any], key: str) -> str:
    if cli_value:
        return cli_value
    value = profile.get(key)
    return str(value).strip() if value is not None else ""


def _require(value: str, flag: str) -> str:
    if not value:
        raise RuntimeError(f"missing required value: {flag}")
    return value


def _phase_create(args: argparse.Namespace, profile: dict[str, Any]) -> None:
    actor = _require(_arg_or_profile(args.actor, profile, "actor"), "--actor")
    github_user = _require(
        _arg_or_profile(args.github_user, profile, "github_user"), "--github-user"
    )
    agents = _require(_arg_or_profile(args.agents, profile, "agents"), "--agents")
    title = _require(args.title or "", "--title")
    summaries = args.summary or []
    if not summaries:
        raise RuntimeError("missing required value: --summary (repeatable)")

    cmd = [
        "python",
        "scripts/pr/create.py",
        "--title",
        title,
        "--actor",
        actor,
        "--github-user",
        github_user,
        "--agents",
        agents,
    ]
    for summary in summaries:
        cmd.extend(["--summary", summary])
    for plan in args.test_plan or []:
        cmd.extend(["--test-plan", plan])
    if args.draft:
        cmd.append("--draft")

    _run_or_fail(cmd)


def _phase_review(pr_number: str, args: argparse.Namespace, profile: dict[str, Any]) -> None:
    actor = _require(_arg_or_profile(args.actor, profile, "actor"), "--actor")
    agents = _require(_arg_or_profile(args.agents, profile, "agents"), "--agents")
    github_user = _arg_or_profile(args.github_user, profile, "github_user")

    cmd = [
        "python",
        "scripts/pr/review.py",
        "--pr",
        pr_number,
        "--actor",
        actor,
        "--agents",
        agents,
    ]
    if github_user:
        cmd.extend(["--github-user", github_user])
    _run_or_fail(cmd)


def _phase_prepare(
    pr_number: str, args: argparse.Namespace, profile: dict[str, Any]
) -> None:
    actor = _require(_arg_or_profile(args.actor, profile, "actor"), "--actor")
    agents = _require(_arg_or_profile(args.agents, profile, "agents"), "--agents")
    github_user = _arg_or_profile(args.github_user, profile, "github_user")

    cmd = [
        "python",
        "scripts/pr/prepare.py",
        "--pr",
        pr_number,
        "--actor",
        actor,
        "--agents",
        agents,
    ]
    if github_user:
        cmd.extend(["--github-user", github_user])
    if args.skip_gates:
        cmd.append("--skip-gates")
    _run_or_fail(cmd)


def _phase_merge(pr_number: str, args: argparse.Namespace, profile: dict[str, Any]) -> None:
    actor = _require(_arg_or_profile(args.actor, profile, "actor"), "--actor")
    agents = _require(_arg_or_profile(args.agents, profile, "agents"), "--agents")
    github_user = _arg_or_profile(args.github_user, profile, "github_user")
    branch = _current_branch()

    precheck_cmd = [
        "python",
        "scripts/pr/merge.py",
        "--pr",
        pr_number,
        "--actor",
        actor,
        "--agents",
        agents,
        "--branch",
        branch,
        "--check-only",
    ]
    if github_user:
        precheck_cmd.extend(["--github-user", github_user])
    _run_or_fail(precheck_cmd)

    _run_or_fail(
        ["python", "scripts/pr/verify_publish.py", "--branch", _current_branch()]
    )
    _run_or_fail(["gh", "pr", "checks", pr_number, "--watch"])
    _run_or_fail(["gh", "pr", "merge", pr_number, "--merge"])

    code, output = _run(["gh", "pr", "view", pr_number, "--json", "mergeCommit"])
    if code != 0:
        raise RuntimeError("unable to fetch merge commit after merge")
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError("unable to parse merge commit payload") from exc
    merge_commit = payload.get("mergeCommit", {})
    merge_sha = str(merge_commit.get("oid", "")).strip()
    if not merge_sha:
        raise RuntimeError("merge commit oid missing after merge")

    write_cmd = [
        "python",
        "scripts/pr/merge.py",
        "--pr",
        pr_number,
        "--actor",
        actor,
        "--agents",
        agents,
        "--branch",
        branch,
        "--merge-sha",
        merge_sha,
    ]
    if github_user:
        write_cmd.extend(["--github-user", github_user])
    _run_or_fail(write_cmd)

    if args.auto_finalize:
        _phase_finalize(args)


def _phase_finalize(args: argparse.Namespace) -> None:
    branch = _current_branch()
    if branch == "main":
        target = _require(args.feature_branch or "", "--feature-branch on main")
    else:
        target = branch
    cmd = ["python", "scripts/pr/finalize.py", "--branch", target]
    if args.delete_merged_local:
        cmd.append("--delete-merged-local")
    _run_or_fail(cmd)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run PR workflow phases with deterministic script wrappers."
    )
    parser.add_argument(
        "--phase",
        required=True,
        choices=["create", "review", "prepare", "merge", "finalize", "full"],
        help="Workflow phase to run.",
    )
    parser.add_argument("--pr", default=None, help="PR number or URL.")
    parser.add_argument("--title", default=None, help="PR title (create/full only).")
    parser.add_argument(
        "--summary",
        action="append",
        default=[],
        help="PR summary bullet item (repeatable; create/full only).",
    )
    parser.add_argument(
        "--test-plan",
        action="append",
        default=[],
        help="PR test plan item/command (repeatable; create/full only).",
    )
    parser.add_argument("--actor", default=None, help="Author name.")
    parser.add_argument("--github-user", default=None, help="GitHub handle with @.")
    parser.add_argument("--agents", default=None, help="Agent pipeline text.")
    parser.add_argument("--draft", action="store_true", default=False)
    parser.add_argument("--skip-gates", action="store_true", default=False)
    parser.add_argument(
        "--auto-finalize",
        action="store_true",
        default=False,
        help="When used with --phase merge, run finalize automatically after merge.",
    )
    parser.add_argument(
        "--profile",
        default=".local/agent_profile.json",
        help="JSON profile path with defaults for actor/github_user/agents.",
    )
    parser.add_argument(
        "--feature-branch",
        default=None,
        help="Feature branch name for finalize when currently on main.",
    )
    parser.add_argument("--delete-merged-local", action="store_true", default=False)
    args = parser.parse_args()

    try:
        profile = _load_profile(args.profile)
        pr_number = _resolve_pr_number(args.pr) if args.phase != "create" else ""

        if args.phase == "create":
            _phase_create(args, profile)
        elif args.phase == "review":
            _phase_review(pr_number, args, profile)
        elif args.phase == "prepare":
            _phase_prepare(pr_number, args, profile)
        elif args.phase == "merge":
            _phase_merge(pr_number, args, profile)
        elif args.phase == "finalize":
            _phase_finalize(args)
        elif args.phase == "full":
            _phase_create(args, profile)
            pr_number = _resolve_pr_number(args.pr)
            _phase_review(pr_number, args, profile)
            _phase_prepare(pr_number, args, profile)
            _phase_merge(pr_number, args, profile)
            _phase_finalize(args)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
