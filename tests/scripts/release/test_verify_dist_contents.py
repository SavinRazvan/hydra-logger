"""
Role: Pytest coverage for distribution content verification policy.
Used By:
 - Pytest discovery and release packaging validation.
Depends On:
 - importlib
 - pathlib
 - sys
 - tarfile
 - zipfile
Notes:
 - Creates synthetic wheel/sdist archives to validate policy behavior.
"""

from __future__ import annotations

import importlib.util
import io
import sys
import tarfile
import zipfile
from pathlib import Path
from tarfile import TarInfo


def _load_verify_module():
    repo_root = Path(__file__).resolve().parents[3]
    script_path = repo_root / "scripts" / "release" / "verify_dist_contents.py"
    spec = importlib.util.spec_from_file_location("verify_dist_contents", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_fake_wheel(
    path: Path, *, include_forbidden: bool = False, include_cli: bool = True
) -> None:
    with zipfile.ZipFile(path, mode="w") as archive:
        archive.writestr("hydra_logger/__init__.py", "__version__='0.0.0'")
        if include_cli:
            archive.writestr("hydra_logger/cli.py", "def main():\n    return 0\n")
        archive.writestr(
            "hydra_logger-0.0.0.dist-info/METADATA", "Metadata-Version: 2.1"
        )
        if include_forbidden:
            archive.writestr("benchmark/results/benchmark_latest.json", "{}")


def _write_fake_sdist(path: Path) -> None:
    with tarfile.open(path, mode="w:gz") as archive:
        payload: dict[str, bytes] = {
            "hydra_logger-0.0.0/hydra_logger/__init__.py": b"__version__='0.0.0'",
            "hydra_logger-0.0.0/hydra_logger/cli.py": b"def main():\n    return 0\n",
            "hydra_logger-0.0.0/PKG-INFO": b"Metadata-Version: 2.1",
        }
        for name, content in payload.items():
            info = TarInfo(name=name)
            info.size = len(content)
            archive.addfile(info, fileobj=io.BytesIO(content))


def test_verify_artifact_passes_for_valid_wheel_and_sdist(tmp_path: Path) -> None:
    module = _load_verify_module()
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()

    wheel_path = dist_dir / "hydra_logger-0.0.0-py3-none-any.whl"
    sdist_path = dist_dir / "hydra_logger-0.0.0.tar.gz"
    _write_fake_wheel(wheel_path)
    _write_fake_sdist(sdist_path)

    assert module.main(["--dist-dir", str(dist_dir)]) == 0


def test_verify_artifact_fails_when_required_file_missing(tmp_path: Path) -> None:
    module = _load_verify_module()
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()

    wheel_path = dist_dir / "hydra_logger-0.0.0-py3-none-any.whl"
    _write_fake_wheel(wheel_path, include_cli=False)

    assert module.main(["--dist-dir", str(dist_dir)]) == 1


def test_verify_artifact_fails_when_forbidden_path_present(tmp_path: Path) -> None:
    module = _load_verify_module()
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()

    wheel_path = dist_dir / "hydra_logger-0.0.0-py3-none-any.whl"
    _write_fake_wheel(wheel_path, include_forbidden=True)

    assert module.main(["--dist-dir", str(dist_dir)]) == 1
