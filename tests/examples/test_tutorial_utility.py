"""
Role: Tests for `examples/tutorials/utility` (notebook bootstrap helpers).
Used By:
 - Pytest discovery / CI.
Depends On:
 - pathlib
 - sys
Notes:
 - Imports utility via the same path layout notebooks use.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TUTORIALS = ROOT / "examples" / "tutorials"


def _import_utility():
    s = str(TUTORIALS)
    if s not in sys.path:
        sys.path.insert(0, s)
    import utility  # noqa: WPS433 — intentional dynamic path

    return utility


def test_utility_resolved_cwd_recovers_when_getcwd_fails(
    monkeypatch, tmp_path: Path
) -> None:
    """Mirrors Jupyter: cwd points at a removed directory → Path.cwd() raises."""
    utility = _import_utility()
    monkeypatch.chdir(tmp_path)
    real_getcwd = os.getcwd

    def _broken_getcwd() -> str:
        raise FileNotFoundError(2, "No such file or directory")

    monkeypatch.setattr(os, "getcwd", _broken_getcwd)
    out = utility.resolved_cwd()
    monkeypatch.setattr(os, "getcwd", real_getcwd)
    assert out == Path(tempfile.gettempdir()).resolve()
    assert Path.cwd().resolve() == out


def test_utility_find_repo_root_matches_tests_layout() -> None:
    utility = _import_utility()
    assert utility.find_repo_root(ROOT) == ROOT


def test_utility_tutorial_paths() -> None:
    utility = _import_utility()
    cfg = utility.tutorial_config_path("base_default.yaml", repo_root=ROOT)
    logs = utility.tutorial_logs_dir(repo_root=ROOT)
    assert cfg == ROOT / "examples" / "config" / "base_default.yaml"
    assert logs == ROOT / "examples" / "logs" / "notebooks"


def test_tutorial_t02_named_preset_file_exists() -> None:
    t02 = ROOT / "examples" / "config" / "tutorial_t02_configuration_recipes.yaml"
    assert t02.is_file()
    text = t02.read_text(encoding="utf-8")
    assert "extends:" in text
    assert "base_default.yaml" in text


def test_prepare_notebook_workspace_honors_hydra_logger_repo(
    monkeypatch, tmp_path: Path
) -> None:
    """Kernel cwd elsewhere + HYDRA_LOGGER_REPO → chdir to clone and return repo root."""
    utility = _import_utility()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HYDRA_LOGGER_REPO", str(ROOT))
    root, flag = utility.prepare_notebook_workspace(warn_if_not_hydra_env=False)
    assert flag is True
    assert root.resolve() == ROOT.resolve()
    assert Path.cwd().resolve() == ROOT.resolve()


def test_prepare_notebook_workspace_repo_candidate_without_env(
    monkeypatch, tmp_path: Path
) -> None:
    """When env is unset, optional repo_candidate still allows discovery from a foreign cwd."""
    utility = _import_utility()
    monkeypatch.delenv("HYDRA_LOGGER_REPO", raising=False)
    monkeypatch.chdir(tmp_path)
    root, flag = utility.prepare_notebook_workspace(
        warn_if_not_hydra_env=False,
        repo_candidate=ROOT,
    )
    assert flag is True
    assert root.resolve() == ROOT.resolve()
    assert Path.cwd().resolve() == ROOT.resolve()


def test_do_notebook_setup_matches_prepare_with_repo_candidate(
    monkeypatch, tmp_path: Path
) -> None:
    """do_notebook_setup(repo_candidate=...) returns the same root as prepare_notebook_workspace."""
    utility = _import_utility()
    monkeypatch.delenv("HYDRA_LOGGER_REPO", raising=False)
    monkeypatch.chdir(tmp_path)
    a = utility.do_notebook_setup(warn_if_not_hydra_env=False, repo_candidate=ROOT)
    b, _ = utility.prepare_notebook_workspace(
        warn_if_not_hydra_env=False,
        repo_candidate=ROOT,
    )
    assert a.resolve() == b.resolve() == ROOT.resolve()


def test_run_notebook_workspace_setup_returns_repo_root(monkeypatch, tmp_path: Path) -> None:
    """path_bootstrap.run_notebook_workspace_setup uses __file__-based project_root."""
    monkeypatch.delenv("HYDRA_LOGGER_REPO", raising=False)
    monkeypatch.chdir(tmp_path)
    s = str(TUTORIALS)
    if s not in sys.path:
        sys.path.insert(0, s)
    from shared.path_bootstrap import run_notebook_workspace_setup

    root = run_notebook_workspace_setup(warn_if_not_hydra_env=False)
    assert root.resolve() == ROOT.resolve()


def test_prime_notebook_workspace_returns_repo_root(monkeypatch, tmp_path: Path) -> None:
    """jupyter_workspace.prime_notebook_workspace matches path_bootstrap when cwd is foreign."""
    monkeypatch.delenv("HYDRA_LOGGER_REPO", raising=False)
    monkeypatch.chdir(tmp_path)
    s = str(TUTORIALS)
    if s not in sys.path:
        sys.path.insert(0, s)
    from jupyter_workspace import prime_notebook_workspace

    root = prime_notebook_workspace(warn_if_not_hydra_env=False)
    assert root.resolve() == ROOT.resolve()
