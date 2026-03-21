"""
Role: Pytest coverage for enterprise tutorial asset integrity.
Used By:
 - Pytest discovery and CI quality gates.
Depends On:
 - pathlib
Notes:
 - Validates onboarding tutorial files, committed notebook contracts, optional generator alignment when
   present, and on-disk ``examples/config`` coverage for tutorials.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TUTORIAL_DIR = ROOT / "examples" / "tutorials" / "cli_tutorials"
NB_FACTORY = ROOT / "examples" / "tutorials" / "notebooks" / "temp_nb_factory"
_NB_FACTORY_CORE = NB_FACTORY / "nb_factory_core.py"

requires_nb_factory = pytest.mark.skipif(
    not _NB_FACTORY_CORE.is_file(),
    reason="Optional local notebook generator not present (directory may be gitignored)",
)


def _import_nb_factory_core():
    import sys

    fac = str(NB_FACTORY)
    if fac not in sys.path:
        sys.path.insert(0, fac)
    path = NB_FACTORY / "nb_factory_core.py"
    spec = importlib.util.spec_from_file_location("nb_factory_core_testmod", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _current_tutorial_files() -> list[str]:
    """Return current tutorial scripts from the canonical CLI track directory."""
    return sorted(path.name for path in TUTORIAL_DIR.glob("t*.py"))


def test_tutorial_scripts_exist() -> None:
    for filename in _current_tutorial_files():
        assert (
            TUTORIAL_DIR / filename
        ).exists(), f"Missing tutorial script: {filename}"


def test_jupyter_workspace_module_exists() -> None:
    """Factory and notebooks expect ``examples/tutorials/jupyter_workspace.py``."""
    assert (ROOT / "examples" / "tutorials" / "jupyter_workspace.py").is_file()


def test_tutorial_readme_references_all_tracks() -> None:
    readme = (ROOT / "examples" / "tutorials" / "README.md").read_text(encoding="utf-8")
    for filename in _current_tutorial_files():
        assert filename in readme


def test_example_readme_points_to_tutorials() -> None:
    readme = (ROOT / "examples" / "README.md").read_text(encoding="utf-8")
    assert "examples/tutorials/README.md" in readme


@requires_nb_factory
def test_nb_factory_per_notebook_generators_align_with_specs() -> None:
    core = _import_nb_factory_core()
    scripts = sorted(NB_FACTORY.glob("generate_t*.py"))
    assert len(scripts) == len(core.TUTORIAL_SPECS)
    for spec in core.TUTORIAL_SPECS:
        stem = str(spec["filename"]).replace(".ipynb", "")
        path = NB_FACTORY / f"generate_{stem}.py"
        assert path.is_file(), f"missing generator for {spec['filename']}"
    assert (NB_FACTORY / "factory_import_setup.py").is_file()
    assert (NB_FACTORY / "nb_factory_core.py").is_file()
    assert (NB_FACTORY / "generate_notebooks.py").is_file()


def _notebook_joined_source(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    chunks: list[str] = []
    for cell in data.get("cells", []):
        src = cell.get("source", "")
        if isinstance(src, list):
            chunks.append("".join(src))
        else:
            chunks.append(str(src))
    return "\n".join(chunks)


def test_generated_notebooks_use_repo_examples_config_no_embedded_copies() -> None:
    """Notebooks resolve the clone and load YAML/JSON from ``examples/config/`` (no temp mirrors)."""
    nb_dir = ROOT / "examples" / "tutorials" / "notebooks"
    for path in sorted(nb_dir.glob("t*.ipynb")):
        text = _notebook_joined_source(path)
        assert "_STANDALONE_CONFIGS" not in text, path.name
        assert "prime_notebook_workspace" in text, path.name
        assert "_load_jupyter_workspace_module" in text, path.name
        assert "jupyter_workspace.py" in text, path.name
        assert "_resolved_notebook_cwd" in text, path.name

    for name in (
        "t17_enterprise_benchmark_comparison_workflow.ipynb",
        "t18_enterprise_bring_your_own_config_benchmark.ipynb",
        "t19_enterprise_nightly_drift_snapshot.ipynb",
    ):
        text = _notebook_joined_source(nb_dir / name)
        assert "benchmark/results/" in text
        assert "Tutorial: wrote minimal benchmark stubs" in text

    t01 = _notebook_joined_source(nb_dir / "t01_production_quick_start.ipynb")
    assert "_T01_STANDALONE_YAML" not in t01


def test_generated_notebooks_delegate_setup_to_jupyter_workspace() -> None:
    """§1 loads jupyter_workspace.py and calls prime_notebook_workspace (all generated t*)."""
    nb_dir = ROOT / "examples" / "tutorials" / "notebooks"
    for path in sorted(nb_dir.glob("t*.ipynb")):
        text = _notebook_joined_source(path)
        assert "jupyter_workspace.py" in text, path.name
        assert "prime_notebook_workspace" in text, path.name


@requires_nb_factory
def test_config_extends_closure_covers_t02_and_t03_presets() -> None:
    """On-disk ``extends:`` closure matches what T02/T03 need (no embedded notebook copies)."""
    core = _import_nb_factory_core()
    t02 = core.spec_by_filename("t02_configuration_recipes.ipynb")
    c02 = core.config_extends_closure_filenames(str(t02["config"]))
    assert "tutorial_t02_configuration_recipes.yaml" in c02
    assert "base_default.yaml" in c02
    assert "network_http_basic.yaml" not in c02

    t03 = core.spec_by_filename("t03_layers_customization.ipynb")
    c03 = core.config_extends_closure_filenames(str(t03["config"]))
    assert "enterprise_multi_layer_api_worker.yaml" in c03


def test_t03_json_peek_preset_exists_on_disk() -> None:
    """T03 §3b reads ``examples/config/dev_console_file.json`` from the repository."""
    p = ROOT / "examples" / "config" / "dev_console_file.json"
    assert p.is_file()


@requires_nb_factory
def test_tutorial_specs_config_files_exist_under_examples_config() -> None:
    """Every ``TUTORIAL_SPECS`` ``config`` must exist under ``examples/config/`` (notebook ``CONFIG_PATH``)."""
    core = _import_nb_factory_core()
    cfg_dir = ROOT / "examples" / "config"
    for spec in core.TUTORIAL_SPECS:
        name = spec.get("config")
        assert name, spec["id"]
        assert (cfg_dir / str(name)).is_file(), f"missing examples/config/{name} for {spec['filename']}"


def test_benchmark_notebooks_have_config_path_and_benchmark_iterate() -> None:
    """T17–T19: §3 paired preset + iterate text points at benchmark/results (not YAML-only)."""
    nb_dir = ROOT / "examples" / "tutorials" / "notebooks"
    for name in (
        "t17_enterprise_benchmark_comparison_workflow.ipynb",
        "t18_enterprise_bring_your_own_config_benchmark.ipynb",
        "t19_enterprise_nightly_drift_snapshot.ipynb",
    ):
        text = _notebook_joined_source(nb_dir / name)
        assert "Paired preset" in text, name
        assert 'CONFIG_PATH = repo_root / "examples" / "config" /' in text, name
        assert "refresh **`benchmark/results/`**" in text, name


def _notebook_cells(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("cells", []))


def test_generated_notebooks_have_clean_vcs_state() -> None:
    """Committed notebooks: no stored execution counts or outputs (clear outputs before commit)."""
    nb_dir = ROOT / "examples" / "tutorials" / "notebooks"
    for path in sorted(nb_dir.glob("t*.ipynb")):
        for cell in _notebook_cells(path):
            assert cell.get("id"), f"{path.name} missing cell id"
            if cell.get("cell_type") != "code":
                continue
            assert cell.get("execution_count") is None, path.name
            assert cell.get("outputs") == [], path.name


def test_pip_install_cells_tagged_skip_ci() -> None:
    """§0 ``%pip`` cells are tagged so CI smoke can strip them (editable install already present)."""
    nb_dir = ROOT / "examples" / "tutorials" / "notebooks"
    for name in ("t01_production_quick_start.ipynb", "t02_configuration_recipes.ipynb"):
        for cell in _notebook_cells(nb_dir / name):
            if cell.get("cell_type") != "code":
                continue
            src = cell.get("source", "")
            if isinstance(src, list):
                text = "".join(src)
            else:
                text = str(src)
            if "%pip install" not in text:
                continue
            tags = (cell.get("metadata") or {}).get("tags") or []
            assert "skip-ci" in tags, name
