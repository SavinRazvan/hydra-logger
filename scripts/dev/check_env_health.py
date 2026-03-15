"""
Role: Environment health guard for local toolchain stability.
Used By:
 - scripts/pr/workflow.py before PR workflow phases.
 - Maintainers validating `.hydra_env` integrity before local commands.
Depends On:
 - argparse
 - json
 - pathlib
 - subprocess
 - tempfile
Notes:
 - Detects broken/mixed environment states and prints deterministic fix hints.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS_PASS = "pass"
STATUS_WARN = "warn"
STATUS_FAIL = "fail"


@dataclass
class CheckResult:
    check_id: str
    status: str
    evidence: str
    recommended_fix: str

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.check_id,
            "status": self.status,
            "evidence": self.evidence,
            "recommended_fix": self.recommended_fix,
        }


def _run(cmd: list[str], env: dict[str, str] | None = None) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return proc.returncode, output


def _status_from_results(results: list[CheckResult]) -> str:
    if any(result.status == STATUS_FAIL for result in results):
        return "broken"
    if any(result.status == STATUS_WARN for result in results):
        return "degraded"
    return "healthy"


def _check_mixed_env_layout(env_path: Path) -> CheckResult:
    pyvenv_cfg = env_path / "pyvenv.cfg"
    conda_meta = env_path / "conda-meta"

    has_pyvenv = pyvenv_cfg.exists()
    has_conda_meta = conda_meta.exists()

    if has_pyvenv and has_conda_meta:
        return CheckResult(
            check_id="mixed_env_layout",
            status=STATUS_FAIL,
            evidence=(
                f"Detected both `{pyvenv_cfg}` and `{conda_meta}`. "
                "This indicates mixed venv/conda layout."
            ),
            recommended_fix=(
                "Recreate `.hydra_env` from a single environment model. "
                "Remove `.hydra_env` then run the canonical setup flow from "
                "`docs/ENVIRONMENT_SETUP.md`."
            ),
        )

    if not env_path.exists():
        return CheckResult(
            check_id="mixed_env_layout",
            status=STATUS_FAIL,
            evidence=f"Environment path `{env_path}` does not exist.",
            recommended_fix=(
                "Create `.hydra_env` using the canonical setup instructions in "
                "`docs/ENVIRONMENT_SETUP.md`."
            ),
        )

    return CheckResult(
        check_id="mixed_env_layout",
        status=STATUS_PASS,
        evidence="Environment layout is consistent (single model detected).",
        recommended_fix="No action needed.",
    )


def _check_python_subprocess_import(python_bin: Path) -> CheckResult:
    cmd = [
        str(python_bin),
        "-c",
        "import subprocess; import _posixsubprocess; print('ok')",
    ]
    code, output = _run(cmd)
    if code != 0:
        return CheckResult(
            check_id="python_subprocess_import",
            status=STATUS_FAIL,
            evidence=output or "subprocess import check failed",
            recommended_fix=(
                "Your interpreter is missing low-level subprocess support. "
                "Recreate `.hydra_env` with a healthy Python distribution."
            ),
        )
    return CheckResult(
        check_id="python_subprocess_import",
        status=STATUS_PASS,
        evidence="Interpreter imports `subprocess` and `_posixsubprocess`.",
        recommended_fix="No action needed.",
    )


def _check_pip_health(python_bin: Path) -> CheckResult:
    version_code, version_out = _run([str(python_bin), "-m", "pip", "--version"])
    if version_code != 0:
        return CheckResult(
            check_id="pip_health",
            status=STATUS_FAIL,
            evidence=version_out or "`python -m pip --version` failed",
            recommended_fix=(
                "Reinstall pip inside `.hydra_env` (for example, with "
                "`python -m ensurepip --upgrade`) and reinstall project dependencies."
            ),
        )

    check_code, check_out = _run([str(python_bin), "-m", "pip", "check"])
    if check_code != 0:
        return CheckResult(
            check_id="pip_health",
            status=STATUS_WARN,
            evidence=check_out or "`python -m pip check` reported issues",
            recommended_fix=(
                "Resolve dependency mismatches reported by `python -m pip check` "
                "inside `.hydra_env`."
            ),
        )

    return CheckResult(
        check_id="pip_health",
        status=STATUS_PASS,
        evidence=version_out,
        recommended_fix="No action needed.",
    )


def _check_mypy_available(python_bin: Path) -> CheckResult:
    code, output = _run([str(python_bin), "-m", "mypy", "--version"])
    if code != 0:
        return CheckResult(
            check_id="mypy_available",
            status=STATUS_WARN,
            evidence=output or "`python -m mypy --version` failed",
            recommended_fix="Install dev dependencies in `.hydra_env` (`pip install -e .[dev]`).",
        )
    return CheckResult(
        check_id="mypy_available",
        status=STATUS_PASS,
        evidence=output,
        recommended_fix="No action needed.",
    )


def _check_pyright_available(env_path: Path, cache_path: Path) -> CheckResult:
    python_bin = env_path / "bin" / "python"
    tool_env = os.environ.copy()
    tool_env["XDG_CACHE_HOME"] = str(cache_path)

    code, output = _run([str(python_bin), "-m", "pyright", "--version"], env=tool_env)
    if code != 0:
        return CheckResult(
            check_id="pyright_available",
            status=STATUS_WARN,
            evidence=output or "`python -m pyright --version` failed",
            recommended_fix=(
                "Install dev dependencies and ensure pyright cache paths are writable. "
                "Use `XDG_CACHE_HOME=.tmp_tools/.cache` when running pyright if needed."
            ),
        )
    return CheckResult(
        check_id="pyright_available",
        status=STATUS_PASS,
        evidence=output,
        recommended_fix="No action needed.",
    )


def _check_writable_path(path: Path, check_id: str, fix_hint: str) -> CheckResult:
    try:
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path, delete=True) as tmp:
            tmp.write(b"health-check")
            tmp.flush()
    except OSError as exc:
        return CheckResult(
            check_id=check_id,
            status=STATUS_FAIL,
            evidence=f"Path `{path}` is not writable: {exc}",
            recommended_fix=fix_hint,
        )

    return CheckResult(
        check_id=check_id,
        status=STATUS_PASS,
        evidence=f"Path `{path}` is writable.",
        recommended_fix="No action needed.",
    )


def _build_payload(env_path: Path, results: list[CheckResult]) -> dict[str, Any]:
    return {
        "status": _status_from_results(results),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python": str(env_path / "bin" / "python"),
        "env_path": str(env_path),
        "checks": [result.to_dict() for result in results],
    }


def _print_human(payload: dict[str, Any], fix_hints_only: bool) -> None:
    status = payload["status"]
    print(f"Environment health: {status}")
    print(f"Env path: {payload['env_path']}")
    print(f"Python: {payload['python']}")
    print("")

    for check in payload["checks"]:
        if fix_hints_only:
            if check["status"] == STATUS_PASS:
                continue
            print(f"- {check['id']}: {check['recommended_fix']}")
            continue

        print(f"- {check['id']}: {check['status']}")
        print(f"  evidence: {check['evidence']}")
        if check["status"] != STATUS_PASS:
            print(f"  fix: {check['recommended_fix']}")


def _exit_code(status: str, strict: bool) -> int:
    if status == "healthy":
        return 0
    if status == "degraded":
        return 2 if strict else 1
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate `.hydra_env` health before local workflow commands."
    )
    parser.add_argument(
        "--env-path",
        default=".hydra_env",
        help="Environment path to validate (default: .hydra_env).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Emit machine-readable JSON payload.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Treat degraded state as blocking.",
    )
    parser.add_argument(
        "--fix-hints-only",
        action="store_true",
        default=False,
        help="Print only remediation hints for non-pass checks.",
    )
    args = parser.parse_args()

    env_path = Path(args.env_path).resolve()
    python_bin = env_path / "bin" / "python"
    cache_path = Path(".tmp_tools/.cache").resolve()

    results: list[CheckResult] = []
    results.append(_check_mixed_env_layout(env_path))

    if not python_bin.exists():
        results.append(
            CheckResult(
                check_id="python_binary_exists",
                status=STATUS_FAIL,
                evidence=f"Python binary not found at `{python_bin}`.",
                recommended_fix=(
                    "Recreate `.hydra_env` and confirm the interpreter exists at "
                    "`.hydra_env/bin/python`."
                ),
            )
        )
    else:
        results.append(_check_python_subprocess_import(python_bin))
        results.append(_check_pip_health(python_bin))
        results.append(_check_mypy_available(python_bin))
        results.append(_check_pyright_available(env_path, cache_path))

    results.append(
        _check_writable_path(
            env_path,
            check_id="env_path_writable",
            fix_hint=(
                "Fix ownership/permissions for `.hydra_env` so your user can write to it "
                "(for example: `chown -R $USER:$USER .hydra_env`)."
            ),
        )
    )
    results.append(
        _check_writable_path(
            cache_path,
            check_id="pyright_cache_permissions",
            fix_hint=(
                "Ensure `.tmp_tools/.cache` is writable and run pyright with "
                "`XDG_CACHE_HOME=.tmp_tools/.cache`."
            ),
        )
    )

    payload = _build_payload(env_path, results)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        _print_human(payload, fix_hints_only=args.fix_hints_only)

    return _exit_code(str(payload["status"]), strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
