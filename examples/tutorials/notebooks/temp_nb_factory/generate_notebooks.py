"""
Role: Generate canonical tutorial notebooks with valid cell formatting.
Used By:
 - examples/tutorials/notebooks/temp_nb_factory (manual notebook regeneration).
Depends On:
 - json
 - pathlib
Notes:
 - Rebuilds notebook tutorial files with clean markdown/code cells (no escaped \n artifacts).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from scenarios import SCENARIO_INSPECT, build_scenario_code


ROOT = Path(__file__).resolve().parents[4]
NOTEBOOKS_DIR = ROOT / "examples" / "tutorials" / "notebooks"


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
        "config": "base_overlay_debug.yaml",
        "description": (
            "See how **one YAML extends another** (`extends`), merges fields, and changes runtime "
            "behavior — here, DEBUG lines on the `app` layer after merge."
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
            "`examples/logs/tutorials/dev_app.jsonl`."
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


def _markdown_cell(text: str) -> Dict[str, Any]:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text,
    }


def _code_cell(text: str) -> Dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text,
    }


def _notebook_metadata() -> Dict[str, Any]:
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


def _bootstrap_snippet() -> str:
    """Import tutorial helpers: repo root = cwd (or HYDRA_LOGGER_REPO). No parent walk."""
    return (
        "import os\n"
        "import sys\n"
        "from pathlib import Path\n\n"
        "REPO = Path(os.environ.get(\"HYDRA_LOGGER_REPO\", Path.cwd())).resolve()\n"
        "_tut = REPO / \"examples\" / \"tutorials\"\n"
        "if not (_tut / \"utility\").is_dir():\n"
        "    raise FileNotFoundError(\n"
        '        "Start Jupyter from the hydra-logger repo root, or set "\n'
        '        "HYDRA_LOGGER_REPO to that directory (must contain examples/tutorials/utility/)."\n'
        "    )\n"
        'sys.path.insert(0, str(_tut))\n\n'
        "from utility import notebook_bootstrap\n\n"
        "repo_root = notebook_bootstrap()\n\n"
    )


def _build_scenario_onboarding_notebook(spec: Dict[str, Any]) -> Dict[str, Any]:
    title = str(spec["title"])
    config_name = str(spec["config"])
    description = str(spec["description"])
    tutorial_id = str(spec["id"])

    inspect_lines = SCENARIO_INSPECT.get(
        tutorial_id,
        ["Console output from the cell below; file presets write under `examples/logs/tutorials/`."],
    )
    check = "\n".join(f"- {line}" for line in inspect_lines)

    intro = (
        f"# {title}\n\n"
        f"{description}\n\n"
        "- Kernel: `.hydra_env`\n"
        "- Start Jupyter from the **repo root**, or set `HYDRA_LOGGER_REPO`.\n"
        "- **§1** sets **repo root** cwd; **§2** imports hydra_logger and runs the scenario.\n"
        f"- Config (when used): `examples/config/{config_name}`\n\n"
        "## Check\n\n"
        f"{check}\n"
    )

    try:
        inner = build_scenario_code(tutorial_id)
    except KeyError:
        inner = (
            "from hydra_logger import create_sync_logger\n\n"
            f'CONFIG_PATH = repo_root / "examples" / "config" / "{config_name}"\n\n'
            "with create_sync_logger(\n"
            "    config_path=CONFIG_PATH,\n"
            "    strict_unknown_fields=True,\n"
            f'    name="tutorial-{tutorial_id}",\n'
            ") as logger:\n"
            f'    logger.info("tutorial {tutorial_id}", layer="app")\n'
        )

    return {
        "cells": [
            _markdown_cell(intro),
            _markdown_cell(
                "## 1. Repo setup\n\n"
                "Run once: `sys.path` + `chdir` so imports and YAML paths work like the CLI tutorials."
            ),
            _code_cell(_bootstrap_snippet()),
            _markdown_cell(
                "## 2. Imports + config path\n\n"
                "Then load the preset and emit logs (console and/or files under `examples/logs/tutorials/`)."
            ),
            _code_cell(inner),
            _markdown_cell(
                "## 3. Customize\n\n"
                "Edit `examples/config/`, re-run **§2**. For file output, open paths listed in the intro."
            ),
        ],
        "metadata": _notebook_metadata(),
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def _build_enterprise_di_notebook(spec: Dict[str, Any]) -> Dict[str, Any]:
    title = str(spec["title"])
    description = str(spec["description"])
    config_name = str(spec["config"])

    intro = (
        f"# {title}\n\n"
        f"{description}\n\n"
        "**Run sections in order**: setup → imports → optional YAML peek → your service code → "
        "build logger from YAML → see files.\n\n"
        "- Kernel: `.hydra_env`\n"
        "- Start Jupyter from the **repo root**, or set `HYDRA_LOGGER_REPO`.\n"
        f"- Config: `examples/config/{config_name}` — `base_log_dir` + `log_dir_name` → "
        "`examples/logs/tutorials/`.\n\n"
        "## Expect\n\n"
        "- **Console**: `app` + `error` layers.\n"
        "- **Files**: `t01_app.jsonl`, `t01_audit.log`, `t01_error.jsonl`.\n"
    )

    cell_imports = (
        "from dataclasses import dataclass\n"
        "from typing import Any\n\n"
        "from hydra_logger import create_sync_logger\n"
        "from hydra_logger.config.loader import load_logging_config\n\n"
        f'CONFIG_PATH = repo_root / "examples" / "config" / "{config_name}"\n'
        'LOG_DIR = repo_root / "examples" / "logs" / "tutorials"\n'
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
        '        print("(missing — run the logger cell first)")\n'
    )

    cells: List[Dict[str, Any]] = [
        _markdown_cell(intro),
        _markdown_cell("## 1. Repo setup\n\nPath + working directory."),
        _code_cell(_bootstrap_snippet()),
        _markdown_cell(
            "## 2. Imports + paths\n\n"
            "`CONFIG_PATH` = YAML file. `LOG_DIR` = where this tutorial writes files."
        ),
        _code_cell(cell_imports),
        _markdown_cell(
            "## 3. Load & inspect config (optional)\n\n"
            "`load_logging_config` validates YAML before `create_sync_logger`. Re-run after you edit the YAML."
        ),
        _code_cell(cell_peek),
        _markdown_cell(
            "## 4. Application code (DI)\n\n"
            "Pass `logger` in; use `layer`, `context`, `extra` for structured events."
        ),
        _code_cell(cell_domain),
        _markdown_cell(
            "## 5. Create logger from YAML + run scenarios\n\n"
            "More than one happy path + audit + error so console and files show real traffic."
        ),
        _code_cell(cell_run),
        _markdown_cell(
            "## 6. Read what landed on disk\n\n"
            "Re-run after **§5** to print tails of the tutorial log files."
        ),
        _code_cell(cell_outputs),
        _markdown_cell(
            "**Customize**: edit `tutorial_t01_enterprise_layers.yaml` (layers, levels, destinations), "
            "then re-run **§3** → **§5** → **§6**."
        ),
    ]

    return {
        "cells": cells,
        "metadata": _notebook_metadata(),
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def _build_notebook(spec: Dict[str, Any]) -> Dict[str, Any]:
    template: Optional[str] = spec.get("template")  # type: ignore[assignment]
    if template == "enterprise_di":
        return _build_enterprise_di_notebook(spec)
    return _build_scenario_onboarding_notebook(spec)


def main() -> None:
    NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)
    for spec in TUTORIAL_SPECS:
        notebook = _build_notebook(spec)
        output_path = NOTEBOOKS_DIR / spec["filename"]
        output_path.write_text(json.dumps(notebook, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
