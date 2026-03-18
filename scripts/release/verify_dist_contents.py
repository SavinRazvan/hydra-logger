"""
Role: Enforces distribution archive content policy before release.
Used By:
 - Release preflight checks.
 - CI build validation jobs.
Depends On:
 - argparse
 - pathlib
 - tarfile
 - zipfile
Notes:
 - Validates required package files and rejects local/runtime artifacts.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import tarfile
import zipfile


REQUIRED_PACKAGE_FILES = (
    "hydra_logger/__init__.py",
    "hydra_logger/cli.py",
)

FORBIDDEN_PREFIXES = (
    ".local/",
    ".cursor/",
    ".agents/",
    "logs/",
    "benchmark/results/",
    "agent-transcripts/",
)


def _list_artifacts(dist_dir: Path) -> list[Path]:
    wheel_paths = sorted(dist_dir.glob("*.whl"))
    sdist_paths = sorted(dist_dir.glob("*.tar.gz"))
    return [*wheel_paths, *sdist_paths]


def _is_sdist(path: Path) -> bool:
    return path.name.endswith(".tar.gz")


def _iter_member_names(artifact_path: Path) -> list[str]:
    if artifact_path.suffix == ".whl":
        with zipfile.ZipFile(artifact_path) as archive:
            return archive.namelist()
    if _is_sdist(artifact_path):
        with tarfile.open(artifact_path, mode="r:gz") as archive:
            return [member.name for member in archive.getmembers() if member.name]
    raise ValueError(f"Unsupported artifact type: {artifact_path.name}")


def _normalize_name(path_name: str, *, sdist: bool) -> str:
    normalized = path_name.replace("\\", "/").lstrip("./")
    if not sdist:
        return normalized

    parts = normalized.split("/", 1)
    if len(parts) == 2 and parts[0].startswith("hydra_logger-"):
        return parts[1]
    return normalized


def _contains_forbidden_path(member_names: list[str]) -> list[str]:
    forbidden: list[str] = []
    for name in member_names:
        normalized = name.lstrip("./")
        for prefix in FORBIDDEN_PREFIXES:
            if normalized == prefix.rstrip("/") or normalized.startswith(prefix):
                forbidden.append(name)
                break
    return forbidden


def _check_required_files(member_names: list[str]) -> list[str]:
    missing = [item for item in REQUIRED_PACKAGE_FILES if item not in member_names]
    return missing


def _check_metadata_presence(member_names: list[str], *, sdist: bool) -> bool:
    if sdist:
        return "PKG-INFO" in member_names
    return any(name.endswith(".dist-info/METADATA") for name in member_names)


def verify_artifact(artifact_path: Path) -> list[str]:
    raw_members = _iter_member_names(artifact_path)
    sdist = _is_sdist(artifact_path)
    members = [_normalize_name(name, sdist=sdist) for name in raw_members]

    errors: list[str] = []
    missing = _check_required_files(members)
    if missing:
        errors.append(f"{artifact_path.name}: missing required file(s): {', '.join(missing)}")

    if not _check_metadata_presence(members, sdist=sdist):
        if sdist:
            errors.append(f"{artifact_path.name}: missing PKG-INFO in sdist payload")
        else:
            errors.append(f"{artifact_path.name}: missing *.dist-info/METADATA in wheel payload")

    forbidden = _contains_forbidden_path(members)
    if forbidden:
        errors.append(
            f"{artifact_path.name}: contains forbidden path(s): {', '.join(sorted(forbidden)[:10])}"
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify distribution archive content against release policy."
    )
    parser.add_argument(
        "--dist-dir",
        default="dist",
        help="Directory containing wheel/sdist artifacts (default: dist).",
    )
    args = parser.parse_args(argv)

    dist_dir = Path(args.dist_dir)
    if not dist_dir.exists():
        print(f"Distribution directory does not exist: {dist_dir}")
        return 1

    artifacts = _list_artifacts(dist_dir)
    if not artifacts:
        print(f"No wheel/sdist artifacts found under {dist_dir}")
        return 1

    all_errors: list[str] = []
    for artifact in artifacts:
        all_errors.extend(verify_artifact(artifact))

    if all_errors:
        print("Distribution content verification failed:")
        for error in all_errors:
            print(f"- {error}")
        return 1

    print(f"Distribution content verification passed for {len(artifacts)} artifact(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
