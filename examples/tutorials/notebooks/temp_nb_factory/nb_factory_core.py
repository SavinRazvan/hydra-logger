"""
Role: Shared notebook JSON builders for tutorial factories.
Used By:
 - ``generate_*.py`` (per-notebook) and ``generate_notebooks.py`` (orchestrator).
Depends On:
 - json
 - pathlib
 - scenarios (SCENARIO_INSPECT, scenario helpers)
 Notes:
 - Single source of truth for cells and bootstrap; configs load from the real ``examples/config/`` tree (no embedded copies).
 - §1 loads ``examples/tutorials/jupyter_workspace.py`` via ``importlib``, then ``prime_notebook_workspace()``.
 - ``write_notebook_json`` strips ``execution_count`` and ``outputs``, assigns stable ``cell.id`` (nbformat), for clean git diffs.
 - **T17–T19**: optional stub files under ``benchmark/results/`` when real benchmark artifacts are missing.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from scenarios import (
    SCENARIO_INSPECT,
    is_benchmark_scenario,
    scenario_imports,
    scenario_main,
    scenario_results_code,
    uses_hydra_config_path,
)


def discover_repo_root() -> Path:
    """Resolve the hydra-logger repo root (robust if ``temp_nb_factory`` depth changes)."""
    here = Path(__file__).resolve()
    for parent in (here, *here.parents):
        if (parent / "setup.py").is_file() and (parent / "hydra_logger").is_dir():
            return parent
    raise RuntimeError(f"Could not find repo root above {here}")


ROOT = discover_repo_root()
NOTEBOOKS_DIR = ROOT / "examples" / "tutorials" / "notebooks"
EXAMPLES_CONFIG_DIR = ROOT / "examples" / "config"

# Benchmark narrative notebooks (may create minimal stubs under ``benchmark/results/`` when files are absent).
BENCHMARK_SCENARIO_IDS = frozenset({"t17", "t18", "t19"})


def _yaml_extends_parent(text: str) -> Optional[str]:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("extends:"):
            val = stripped.split(":", 1)[1].strip().strip("\"'")
            return val or None
    return None


def config_extends_closure_filenames(primary: str) -> frozenset[str]:
    """
    YAML preset name (e.g. ``tutorial_t02_configuration_recipes.yaml``) plus transitive ``extends:`` parents.

    Used by tests to assert on-disk presets cover each tutorial without embedding copies in notebooks.
    """
    visiting: set[str] = set()
    found: set[str] = set()

    def visit(name: str) -> None:
        if name in found:
            return
        if name in visiting:
            raise ValueError(f"extends cycle involving {name!r}")
        path = EXAMPLES_CONFIG_DIR / name
        if not path.is_file():
            raise FileNotFoundError(path)
        visiting.add(name)
        raw = path.read_text(encoding="utf-8")
        parent = _yaml_extends_parent(raw)
        if parent:
            visit(parent)
        visiting.remove(name)
        found.add(name)

    visit(primary)
    return frozenset(found)


TUTORIAL_SPECS: List[Dict[str, Any]] = [
    {
        "id": "t01",
        "filename": "t01_production_quick_start.ipynb",
        "title": "T01 Production Quick Start",
        "config": "tutorial_t01_enterprise_layers.yaml",
        "description": (
            "Enterprise-style onboarding: one YAML contract, logger at startup, "
            "inject into a small service, then log with `layer` + `context` (not raw f-strings)."
        ),
        "message": "",
        "template": "enterprise_di",
    },
    {
        "id": "t02",
        "filename": "t02_configuration_recipes.ipynb",
        "title": "T02 Configuration Recipes",
        "config": "tutorial_t02_configuration_recipes.yaml",
        "description": (
            "See how **one YAML extends another** (`extends`), merges fields, and changes runtime "
            "behavior — here, DEBUG lines on the `app` layer after merge. Preset: "
            "`examples/config/tutorial_t02_configuration_recipes.yaml`."
        ),
    },
    {
        "id": "t03",
        "filename": "t03_layers_customization.ipynb",
        "title": "T03 Layers Customization",
        "config": "enterprise_multi_layer_api_worker.yaml",
        "description": (
            "Route traffic by **layer name** (`api` vs `worker`): different handlers, different files, "
            "same logger — mirrors real services."
        ),
    },
    {
        "id": "t04",
        "filename": "t04_extensions_plugins.ipynb",
        "title": "T04 Extensions Plugins",
        "config": "dev_console_file.yaml",
        "description": (
            "Start from a file preset, then **attach extensions in code** (`model_copy` + "
            "`extensions`) before `create_sync_logger(config)` — easy to experiment, then freeze in YAML."
        ),
    },
    {
        "id": "t08",
        "filename": "t08_console_configuration_cookbook.ipynb",
        "title": "T08 Console Configuration Cookbook",
        "config": "dev_console_file.yaml",
        "description": (
            "Tune **console + file** together: run INFO/WARNING/ERROR and inspect both stdout and "
            "`examples/logs/notebooks/dev_app.jsonl`."
        ),
    },
    {
        "id": "t09",
        "filename": "t09_levels_columns_date_and_destinations.ipynb",
        "title": "T09 Levels Columns Date And Destinations",
        "config": "prod_jsonl_strict.yaml",
        "description": (
            "**File-only** strict preset: learn where output goes when there is no console destination "
            "(JSONL tail printed below)."
        ),
    },
    {
        "id": "t12",
        "filename": "t12_network_http_typed_destination.ipynb",
        "title": "T12 Network HTTP Typed Destination",
        "config": "network_http_basic.yaml",
        "description": (
            "Wire a typed **`network_http`** destination from YAML; emit one structured event on the "
            "`ship` layer (network may be blocked — config shape is the lesson)."
        ),
    },
    {
        "id": "t13",
        "filename": "t13_network_ws_resilient_typed_destination.ipynb",
        "title": "T13 Network WS Resilient Typed Destination",
        "config": "network_ws_basic.yaml",
        "description": (
            "Same idea for **`network_ws`**: validate layer + destination config and logger integration."
        ),
    },
    {
        "id": "t14",
        "filename": "t14_network_local_http_simulation.ipynb",
        "title": "T14 Network Local HTTP Simulation",
        "config": "network_http_batched.yaml",
        "description": (
            "Contrast **batched HTTP** settings with T12 — batch size, retries, and when to use each."
        ),
    },
    {
        "id": "t16",
        "filename": "t16_enterprise_config_templates_at_scale.ipynb",
        "title": "T16 Enterprise Config Templates At Scale",
        "config": "enterprise_onboarding_starter.yaml",
        "description": (
            "Exercise the **enterprise onboarding** preset: reliability flags + confined paths + "
            "structured JSONL output."
        ),
    },
    {
        "id": "t17",
        "filename": "t17_enterprise_benchmark_comparison_workflow.ipynb",
        "title": "T17 Enterprise Benchmark Comparison Workflow",
        "config": "base_default.yaml",
        "description": (
            "Connect logging configs to **benchmark evidence**: read the latest summary artifact from "
            "`benchmark/results/` (when present)."
        ),
    },
    {
        "id": "t18",
        "filename": "t18_enterprise_bring_your_own_config_benchmark.ipynb",
        "title": "T18 Enterprise Bring Your Own Config Benchmark",
        "config": "base_default.yaml",
        "description": (
            "Locate **BYOC benchmark JSON** under `benchmark/results/tutorials/t18_byoc/` and inspect a "
            "snapshot (your config, measured)."
        ),
    },
    {
        "id": "t19",
        "filename": "t19_enterprise_nightly_drift_snapshot.ipynb",
        "title": "T19 Enterprise Nightly Drift Snapshot",
        "config": "prod_jsonl_strict.yaml",
        "description": (
            "Read **`benchmark_latest_drift.md`** — a nightly-style drift signal for performance governance."
        ),
    },
    {
        "id": "t20",
        "filename": "t20_notebook_hydra_config_onboarding.ipynb",
        "title": "T20 Notebook Hydra Config Onboarding",
        "config": "enterprise_onboarding_starter.yaml",
        "description": (
            "Strict **path + reliability** onboarding in one preset: validate YAML, log once, confirm JSONL tail."
        ),
    },
]

SPEC_BY_FILENAME: Dict[str, Dict[str, Any]] = {s["filename"]: s for s in TUTORIAL_SPECS}


def spec_by_filename(filename: str) -> Dict[str, Any]:
    """Return the tutorial spec for a generated ``.ipynb`` filename."""
    try:
        return SPEC_BY_FILENAME[filename]
    except KeyError as e:
        known = ", ".join(sorted(SPEC_BY_FILENAME))
        raise KeyError(f"No tutorial spec for {filename!r}. Known: {known}") from e


def _snippet_one_line(text: str) -> str:
    """First sentence (or safe prefix) for intro cells — avoid chopping mid-backtick."""
    t = " ".join(text.split())
    for sep in (". ", "? ", "! "):
        idx = t.find(sep)
        if 10 < idx <= 240:
            return t[: idx + 1].strip()
    if len(t) <= 220:
        return t
    cut = t[:217].rsplit(" ", 1)[0]
    return cut + "…"


def _expect_hint(tutorial_id: str) -> str:
    lines = SCENARIO_INSPECT.get(tutorial_id, ["See console or log directory."])
    return lines[0]


def markdown_cell(text: str) -> Dict[str, Any]:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text,
    }


def code_cell(
    text: str,
    *,
    source_hidden: bool = False,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    meta: Dict[str, Any] = {}
    if source_hidden:
        meta["jupyter"] = {"source_hidden": True}
    if tags:
        meta["tags"] = list(tags)
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": meta,
        "outputs": [],
        "source": text,
    }


def notebook_metadata() -> Dict[str, Any]:
    return {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.11",
        },
    }


def bootstrap_snippet() -> str:
    """
    Collapsed §1: ``importlib`` loads ``jupyter_workspace.py`` (found from ``HYDRA_LOGGER_REPO`` or cwd).

    Setup logic lives in ``examples/tutorials/jupyter_workspace.py`` → ``shared.path_bootstrap`` → ``utility``.
    """
    return (
        "import importlib.util\n"
        "import os\n"
        "import tempfile\n"
        "from pathlib import Path\n\n"
        "def _resolved_notebook_cwd() -> Path:\n"
        "    try:\n"
        "        return Path.cwd().resolve()\n"
        "    except FileNotFoundError:\n"
        "        fb = Path(tempfile.gettempdir()).resolve()\n"
        "        os.chdir(fb)\n"
        "        return fb\n\n"
        "def _load_jupyter_workspace_module():\n"
        "    _starts: list[Path] = []\n"
        "    _env = os.environ.get(\"HYDRA_LOGGER_REPO\", \"\").strip()\n"
        "    if _env:\n"
        "        _starts.append(Path(_env).expanduser().resolve())\n"
        "    _starts.append(_resolved_notebook_cwd())\n"
        "    _seen: set[str] = set()\n"
        "    for _s in _starts:\n"
        "        for _b in (_s, *_s.parents):\n"
        '            _jw = _b / "examples" / "tutorials" / "jupyter_workspace.py"\n'
        "            try:\n"
        "                _key = str(_jw.resolve())\n"
        "            except (OSError, RuntimeError):\n"
        "                continue\n"
        "            if _key in _seen:\n"
        "                continue\n"
        "            _seen.add(_key)\n"
        "            if _jw.is_file():\n"
        '                _spec = importlib.util.spec_from_file_location("_hydra_tutorial_jw", _jw)\n'
        "                assert _spec and _spec.loader\n"
        "                _mod = importlib.util.module_from_spec(_spec)\n"
        "                _spec.loader.exec_module(_mod)\n"
        "                return _mod\n"
        "    raise FileNotFoundError(\n"
        '        "Could not find examples/tutorials/jupyter_workspace.py. Clone hydra-logger, set "\n'
        '        "HYDRA_LOGGER_REPO to the clone (or any directory inside it), or start Jupyter with cwd "\n'
        '        "inside that clone."\n'
        "    )\n\n"
        "repo_root = _load_jupyter_workspace_module().prime_notebook_workspace()\n"
    )


def scenario_benchmark_optional_stubs() -> str:
    """When ``benchmark/results/*`` files are missing, write minimal stubs so §5 still runs."""
    return (
        '_rb = repo_root / "benchmark" / "results"\n'
        "_rb.mkdir(parents=True, exist_ok=True)\n"
        "_wrote = False\n"
        '_s = _rb / "benchmark_latest_summary.md"\n'
        "if not _s.is_file():\n"
        "    _s.write_text(\n"
        '        "# Synthetic benchmark summary (tutorial fallback)\\n\\n"\n'
        '        "Replace by running repo benchmarks → `benchmark/results/benchmark_latest_summary.md`.\\n",\n'
        '        encoding="utf-8",\n'
        "    )\n"
        "    _wrote = True\n"
        '_d = _rb / "benchmark_latest_drift.md"\n'
        "if not _d.is_file():\n"
        "    _d.write_text(\n"
        '        "# Synthetic drift snapshot (tutorial fallback)\\n\\n"\n'
        '        "Replace with `benchmark/results/benchmark_latest_drift.md` after a real run.\\n",\n'
        '        encoding="utf-8",\n'
        "    )\n"
        "    _wrote = True\n"
        '_byoc = _rb / "tutorials" / "t18_byoc" / "stub_notebook_run"\n'
        "_byoc.mkdir(parents=True, exist_ok=True)\n"
        '_j = _byoc / "benchmark_latest.json"\n'
        "if not _j.is_file():\n"
        "    import json as _json\n"
        '    _j.write_text(_json.dumps({"synthetic": True, "tutorial": "t18"}), encoding="utf-8")\n'
        "    _wrote = True\n"
        "if _wrote:\n"
        '    print("Tutorial: wrote minimal benchmark stubs under", _rb)\n\n'
    )


def build_scenario_onboarding_notebook(spec: Dict[str, Any]) -> Dict[str, Any]:
    title = str(spec["title"])
    config_name = str(spec["config"])
    description = str(spec["description"])
    tutorial_id = str(spec["id"])
    needs_benchmarks = tutorial_id in BENCHMARK_SCENARIO_IDS

    if needs_benchmarks:
        intro = (
            f"#### {title}\n\n"
            "Reads **`benchmark/results/`** from your clone. "
            "<small>If files are missing, §1 writes **minimal stubs** there so the cells still run "
            "(replace with real benchmark outputs when you have them).</small>\n\n"
            "More: `examples/tutorials/notebooks/README.md`.\n"
        )
    else:
        intro = (
            f"#### {title}\n\n"
            f"{_snippet_one_line(description)}\n\n"
            f"`examples/config/{config_name}`\n\n"
            f"**Expect:** {_expect_hint(tutorial_id)} "
            "<small>More: `examples/tutorials/notebooks/README.md`.</small>\n"
        )

    cells: List[Dict[str, Any]] = [
        markdown_cell(intro),
        markdown_cell(
            "**§0 — pip**  \n"
            "<small>Optional if `import hydra_logger` already works.</small>\n"
        ),
        code_cell(
            "%pip install -q \"hydra-logger\"\n"
            "# Restart kernel if pip upgraded deps.\n",
            tags=["skip-ci"],
        ),
        markdown_cell(
            "**§1 — Setup**  \n"
            "<small>Notebook plumbing (usually **collapsed**): ``importlib`` loads ``jupyter_workspace.py``, "
            "then **one call** — ``prime_notebook_workspace()`` — (``shared.path_bootstrap`` → ``utility``). "
            "Clone root follows the loaded file, not Jupyter's cwd. Presets: ``examples/config/``. "
            "Details: `notebooks/README.md`.</small>\n"
        ),
        code_cell(bootstrap_snippet(), source_hidden=True),
    ]

    if needs_benchmarks:
        cells.append(code_cell(scenario_benchmark_optional_stubs(), source_hidden=True))

    cells.extend(
        [
            markdown_cell("**§2 — Imports**"),
            code_cell(scenario_imports(tutorial_id)),
        ]
    )

    if needs_benchmarks:
        cells.extend(
            [
                markdown_cell(
                    "**§3 — Paired preset (`examples/config/`)**  \n"
                    "<small>`CONFIG_PATH` is the canonical YAML in the repo for this tutorial id "
                    f"(`{config_name}`). **§5** only reads **`benchmark/results/`** — it does not load this file; "
                    "the path is here so you can open or extend configs next to benchmark workflows.</small>\n"
                ),
                code_cell(f'CONFIG_PATH = repo_root / "examples" / "config" / "{config_name}"\n'),
            ]
        )
    elif uses_hydra_config_path(tutorial_id):
        cells.extend(
            [
                markdown_cell(
                    "**§3 — Config path**  \n"
                    "<small>`CONFIG_PATH` is ``repo_root / \"examples\" / \"config\" / …`` — the same files "
                    "you edit in the repository.</small>\n"
                ),
                code_cell(f'CONFIG_PATH = repo_root / "examples" / "config" / "{config_name}"\n'),
            ]
        )
        if tutorial_id == "t03":
            cells.extend(
                [
                    markdown_cell(
                        "**§3b — JSON preset on disk**  \n"
                        "<small>`LoggingConfig` is the same whether you load YAML (§5) or validate JSON. "
                        "Here we peek at `dev_console_file.json` — §5 still uses the YAML `CONFIG_PATH`.</small>\n"
                    ),
                    code_cell(
                        "import json\n\n"
                        "from hydra_logger.config.models import LoggingConfig\n\n"
                        '_JSON_PRESET = repo_root / "examples" / "config" / "dev_console_file.json"\n'
                        '_raw = json.loads(_JSON_PRESET.read_text(encoding="utf-8"))\n'
                        "_from_json = LoggingConfig.model_validate(_raw)\n"
                        'print("JSON preset:", _JSON_PRESET.name, "→ layers:", list(_from_json.layers.keys()))\n'
                    ),
                ]
            )
    else:  # pragma: no cover — all scenario specs are benchmark or hydra-config tutorials
        raise AssertionError(f"No §3 branch for tutorial id {tutorial_id!r}")

    cells.extend(
        [
            markdown_cell("**§5 — Scenario**  \n<small>Your hydra-logger usage pattern.</small>\n"),
            code_cell(scenario_main(tutorial_id)),
        ]
    )

    res = scenario_results_code(tutorial_id)
    if res:
        cells.extend(
            [
                markdown_cell(
                    "**§6 — Results**  \n<small>Log file tails under ``examples/logs/notebooks/``.</small>\n"
                ),
                code_cell(res),
            ]
        )
    else:
        cells.append(
            markdown_cell(
                "**§6 — Results**  \n"
                f"<small>{_expect_hint(tutorial_id)}</small>\n"
            )
        )

    if needs_benchmarks:
        cells.append(
            markdown_cell(
                "**Iterate:** refresh **`benchmark/results/`** (run repo benchmarks or copy artifacts), then "
                "re-run **§5** → **§6**. Paired preset: **`examples/config/"
                f"{config_name}`**. <small>`notebooks/README.md`</small>\n"
            )
        )
    else:
        cells.append(
            markdown_cell(
                "**Iterate:** edit YAML under `examples/config/`, re-run **§5** (and **§6** if present). "
                "<small>Details: `notebooks/README.md`.</small>\n"
            )
        )

    return {
        "cells": cells,
        "metadata": notebook_metadata(),
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def build_enterprise_di_notebook(spec: Dict[str, Any]) -> Dict[str, Any]:
    title = str(spec["title"])
    description = str(spec["description"])
    config_name = str(spec["config"])
    intro = (
        f"#### {title}\n\n"
        f"{_snippet_one_line(description)}\n\n"
        "`examples/config/"
        f"{config_name}` — **Expect:** console (`app`, `error`) + "
        "`t01_app.jsonl`, `t01_audit.log`, `t01_error.jsonl`. "
        "<small>More: `examples/tutorials/notebooks/README.md`.</small>\n"
    )

    cell_imports = (
        "from dataclasses import dataclass\n"
        "from typing import Any\n\n"
        "from hydra_logger import create_sync_logger\n"
        "from hydra_logger.config.loader import load_logging_config\n\n"
        f'CONFIG_PATH = repo_root / "examples" / "config" / "{config_name}"\n'
        'LOG_DIR = repo_root / "examples" / "logs" / "notebooks"\n'
    )

    cell_peek = (
        "cfg = load_logging_config(CONFIG_PATH, strict_unknown_fields=True)\n"
        'print("layers:", list(cfg.layers.keys()))\n'
        'print("default_level:", cfg.default_level)\n'
    )

    cell_domain = (
        "@dataclass\n"
        "class PaymentRequest:\n"
        "    order_id: str\n"
        "    user_id: str\n"
        "    amount: float\n"
        '    currency: str = "USD"\n\n\n'
        "class PaymentService:\n"
        "    def __init__(self, logger: Any) -> None:\n"
        "        self.logger = logger\n\n"
        "    def process(self, req: PaymentRequest) -> dict[str, Any]:\n"
        '        self.logger.info(\n'
        '            "payment request received",\n'
        '            layer="app",\n'
        '            context={"order_id": req.order_id, "user_id": req.user_id},\n'
        '            extra={"amount": req.amount, "currency": req.currency},\n'
        "        )\n"
        "        if req.amount <= 0:\n"
        '            self.logger.warning(\n'
        '                "invalid payment amount",\n'
        '                layer="audit",\n'
        '                context={"order_id": req.order_id, "user_id": req.user_id},\n'
        '                extra={"amount": req.amount},\n'
        "            )\n"
        '            raise ValueError("Amount must be > 0")\n'
        "        if req.amount > 10000:\n"
        '            self.logger.error(\n'
        '                "payment exceeds policy threshold",\n'
        '                layer="error",\n'
        '                context={"order_id": req.order_id, "user_id": req.user_id},\n'
        '                extra={"amount": req.amount, "threshold": 10000},\n'
        "            )\n"
        '            raise RuntimeError("Risk policy blocked this payment")\n'
        '        self.logger.info(\n'
        '            "payment approved",\n'
        '            layer="app",\n'
        '            context={"order_id": req.order_id},\n'
        '            extra={"status": "approved"},\n'
        "        )\n"
        '        return {"ok": True, "order_id": req.order_id, "status": "approved"}\n'
    )

    cell_run = (
        "with create_sync_logger(\n"
        "    config_path=CONFIG_PATH,\n"
        "    strict_unknown_fields=True,\n"
        '    name="t01-tutorial",\n'
        ") as logger:\n"
        "    svc = PaymentService(logger)\n"
        '    svc.process(PaymentRequest(order_id="ORD-1001", user_id="U-1", amount=99.5))\n'
        '    svc.process(PaymentRequest(order_id="ORD-1004", user_id="U-4", amount=42.0))\n'
        '    svc.process(PaymentRequest(order_id="ORD-1005", user_id="U-5", amount=250.0))\n'
        "    logger.info(\n"
        '        "batch settlement completed",\n'
        '        layer="app",\n'
        '        context={"batch_id": "B-09"},\n'
        '        extra={"items": 3},\n'
        "    )\n"
        "    try:\n"
        '        svc.process(PaymentRequest(order_id="ORD-1002", user_id="U-2", amount=0))\n'
        "    except ValueError:\n"
        "        pass\n"
        "    try:\n"
        '        svc.process(PaymentRequest(order_id="ORD-1003", user_id="U-3", amount=15000))\n'
        "    except RuntimeError:\n"
        "        pass\n"
    )

    cell_outputs = (
        'print("File output (last lines):")\n'
        'for _name in ("t01_app.jsonl", "t01_audit.log", "t01_error.jsonl"):\n'
        "    _p = LOG_DIR / _name\n"
        '    print(f"--- {_name} ---")\n'
        "    if _p.is_file():\n"
        "        _lines = _p.read_text(encoding=\"utf-8\").splitlines()\n"
        "        for _line in _lines[-8:]:\n"
        "            print(_line)\n"
        "    else:\n"
        '        print("(missing — run §5 first)")\n'
    )

    cells: List[Dict[str, Any]] = [
        markdown_cell(intro),
        markdown_cell(
            "**§0 — pip**  \n"
            "<small>Optional if the package is already importable.</small>\n"
        ),
        code_cell(
            "%pip install -q \"hydra-logger\"\n"
            "# Restart kernel if pip upgraded deps.\n",
            tags=["skip-ci"],
        ),
        markdown_cell(
            "**§1 — Setup**  \n"
            "<small>Same as other tutorials: collapsed cell runs ``prime_notebook_workspace()`` via "
            "``examples/tutorials/jupyter_workspace.py``. ``CONFIG_PATH`` is under ``examples/config/``. "
            "Details: `notebooks/README.md`.</small>\n"
        ),
        code_cell(bootstrap_snippet(), source_hidden=True),
        markdown_cell(
            "**§2 — Imports + paths**  \n"
            "<small>`CONFIG_PATH`, `LOG_DIR`.</small>\n"
        ),
        code_cell(cell_imports),
        markdown_cell(
            "**§3 — Peek config (optional)**  \n"
            "<small>Validate YAML before constructing the logger.</small>\n"
        ),
        code_cell(cell_peek),
        markdown_cell(
            "**§4 — Application (DI)**  \n"
            "<small>Inject `logger`; use `layer` / `context` / `extra`.</small>\n"
        ),
        code_cell(cell_domain),
        markdown_cell(
            "**§5 — Logger + scenarios**  \n"
            "<small>`create_sync_logger` from YAML, then exercise paths.</small>\n"
        ),
        code_cell(cell_run),
        markdown_cell(
            "**§6 — File tails**  \n"
            "<small>Re-run after §5.</small>\n"
        ),
        code_cell(cell_outputs),
        markdown_cell(
            "**Iterate:** edit YAML at `CONFIG_PATH`, re-run **§3** → **§5** → **§6**. "
            "<small>`notebooks/README.md`</small>\n"
        ),
    ]

    return {
        "cells": cells,
        "metadata": notebook_metadata(),
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def build_tutorial_notebook(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Build nbformat JSON dict for one tutorial spec."""
    template: Optional[str] = spec.get("template")  # type: ignore[assignment]
    if template == "enterprise_di":
        return build_enterprise_di_notebook(spec)
    return build_scenario_onboarding_notebook(spec)


def normalize_notebook_for_version_control(notebook: Dict[str, Any]) -> None:
    """Clear execution state so committed ``.ipynb`` diffs stay small (no outputs / counts)."""
    seen_ids: set[str] = set()
    for idx, cell in enumerate(notebook.get("cells", [])):
        if cell.get("cell_type") == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
        src = cell.get("source", "")
        if isinstance(src, list):
            text = "".join(src)
        else:
            text = str(src)
        digest = hashlib.sha256(
            f"{idx}|{cell.get('cell_type')}|{text}".encode("utf-8")
        ).hexdigest()[:16]
        if digest in seen_ids:
            digest = hashlib.sha256(f"{digest}|{idx}".encode("ascii")).hexdigest()[:16]
        cell["id"] = digest
        seen_ids.add(str(cell["id"]))


def write_notebook_json(notebook: Dict[str, Any], output_path: Path) -> None:
    """Write notebook dict as indented JSON (``.ipynb``), VCS-normalized (no outputs)."""
    normalize_notebook_for_version_control(notebook)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(notebook, indent=2) + "\n", encoding="utf-8")
