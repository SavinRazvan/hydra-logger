"""
Role: Per-tutorial notebook code bodies split into imports, scenario, and optional results.
Used By:
 - ``nb_factory_core.py`` (and ``generate_*.py`` / ``generate_notebooks.py``).
Depends On:
 - typing
 Notes:
 - ``scenario_imports`` / ``scenario_main`` / ``scenario_results_code`` map to §2 / §5 / §6. §3 sets ``CONFIG_PATH`` in the factory.
 - Log tails use ``repo_root / "examples" / "logs" / "notebooks"`` (see ``_log_root_expr``).
"""

from __future__ import annotations

from typing import Dict, List, Optional

# Short hints for the intro markdown "Expect" line (≤2 bullets collapsed to one line in factory).
SCENARIO_INSPECT: Dict[str, List[str]] = {
    "t02": [
        "Preset extends `base_default.yaml`; console shows DEBUG then INFO on `app`.",
    ],
    "t03": [
        "Layers `api` / `worker` → `api.jsonl` and `worker.jsonl` under `examples/logs/notebooks/`.",
    ],
    "t04": ["Security extension may redact password-like fields in files."],
    "t08": ["Colored console + `dev_app.jsonl`."],
    "t09": ["File-only preset → `prod_app.jsonl`."],
    "t12": [
        "Console + `t12_network_http_layer.jsonl` under `examples/logs/notebooks/`; `network_http` may fail offline."
    ],
    "t13": [
        "Console + `t13_network_ws_layer.jsonl` under `examples/logs/notebooks/`; `network_ws` may fail offline."
    ],
    "t14": [
        "Console + `t14_network_http_layer.jsonl` under `examples/logs/notebooks/`; batched `network_http` may fail offline."
    ],
    "t16": ["Enterprise starter → `enterprise_app.jsonl`."],
    "t17": ["Excerpt of `benchmark/results/benchmark_latest_summary.md` if present."],
    "t18": ["Latest `benchmark_latest.json` under `t18_byoc/` if present."],
    "t19": ["Excerpt of `benchmark_latest_drift.md` if present."],
    "t20": ["Enterprise preset → JSONL under log dir."],
}


def _log_root_expr() -> str:
    """Expression for directory containing **notebook** log files (canonical repo layout)."""
    return '(repo_root / "examples" / "logs" / "notebooks")'


def scenario_imports(tutorial_id: str) -> str:
    """§2 — import lines only (no CONFIG_PATH)."""
    if tutorial_id == "t02":
        return "from hydra_logger import create_sync_logger\n"
    if tutorial_id in {"t03", "t08", "t09", "t12", "t13", "t14", "t16", "t20"}:
        return "from hydra_logger import create_sync_logger\n"
    if tutorial_id == "t04":
        return (
            "from hydra_logger import create_sync_logger\n"
            "from hydra_logger.config.loader import load_logging_config\n"
        )
    if tutorial_id == "t17":
        return "from pathlib import Path\n"
    if tutorial_id == "t18":
        return "import json\nfrom pathlib import Path\n"
    if tutorial_id == "t19":
        return "from pathlib import Path\n"
    raise KeyError(tutorial_id)


def scenario_main(tutorial_id: str) -> str:
    """§5 — body after CONFIG_PATH exists (benchmark: uses repo_root only)."""
    if tutorial_id == "t02":
        return (
            "with create_sync_logger(\n"
            "    config_path=CONFIG_PATH,\n"
            "    strict_unknown_fields=True,\n"
            '    name="tutorial-t02",\n'
            ") as logger:\n"
            '    logger.debug("overlay enables DEBUG on app", layer="app", context={"tutorial": "t02"})\n'
            '    logger.info("merged config active", layer="app")\n'
        )
    if tutorial_id == "t03":
        return (
            "with create_sync_logger(\n"
            "    config_path=CONFIG_PATH,\n"
            "    strict_unknown_fields=True,\n"
            '    name="tutorial-t03",\n'
            ") as logger:\n"
            '    logger.info("request ok", layer="api", context={"route": "/v1/orders"})\n'
            '    logger.info("job running", layer="worker", context={"job_id": "job-1"})\n'
        )
    if tutorial_id == "t04":
        return (
            "cfg = load_logging_config(CONFIG_PATH, strict_unknown_fields=True)\n"
            "cfg = cfg.model_copy(\n"
            "    update={\n"
            '        "extensions": {\n'
            '            "security_redaction": {\n'
            '                "enabled": True,\n'
            '                "type": "security",\n'
            '                "patterns": ["password", "secret"],\n'
            "            }\n"
            "        }\n"
            "    }\n"
            ")\n\n"
            "with create_sync_logger(cfg, strict_unknown_fields=True, name=\"tutorial-t04\") as logger:\n"
            '    logger.info("login", layer="app", extra={"password": "do-not-log-raw"})\n'
        )
    if tutorial_id == "t08":
        return (
            "with create_sync_logger(\n"
            "    config_path=CONFIG_PATH,\n"
            "    strict_unknown_fields=True,\n"
            '    name="tutorial-t08",\n'
            ") as logger:\n"
            '    logger.info("info", layer="app")\n'
            '    logger.warning("warning", layer="app")\n'
            '    logger.error("error", layer="app")\n'
        )
    if tutorial_id == "t09":
        return (
            "with create_sync_logger(\n"
            "    config_path=CONFIG_PATH,\n"
            "    strict_unknown_fields=True,\n"
            '    name="tutorial-t09",\n'
            ") as logger:\n"
            '    logger.info("event", layer="app", context={"order_id": "ORD-1"})\n'
        )
    if tutorial_id == "t12":
        return (
            "with create_sync_logger(\n"
            "    config_path=CONFIG_PATH,\n"
            "    strict_unknown_fields=True,\n"
            '    name="tutorial-t12",\n'
            ") as logger:\n"
            '    logger.info("ship", layer="ship", context={"batch_id": "b1"})\n'
        )
    if tutorial_id == "t13":
        return (
            "with create_sync_logger(\n"
            "    config_path=CONFIG_PATH,\n"
            "    strict_unknown_fields=True,\n"
            '    name="tutorial-t13",\n'
            ") as logger:\n"
            '    logger.info("stream", layer="stream", context={"session_id": "s1"})\n'
        )
    if tutorial_id == "t14":
        return (
            "with create_sync_logger(\n"
            "    config_path=CONFIG_PATH,\n"
            "    strict_unknown_fields=True,\n"
            '    name="tutorial-t14",\n'
            ") as logger:\n"
            '    logger.info("batched", layer="ship", context={"batch_id": "b14"})\n'
        )
    if tutorial_id == "t16":
        return (
            "with create_sync_logger(\n"
            "    config_path=CONFIG_PATH,\n"
            "    strict_unknown_fields=True,\n"
            '    name="tutorial-t16",\n'
            ") as logger:\n"
            '    logger.info("enterprise template", layer="app", context={"env": "notebook"})\n'
        )
    if tutorial_id == "t17":
        return (
            'p = repo_root / "benchmark" / "results" / "benchmark_latest_summary.md"\n'
            "if p.is_file():\n"
            '    print(p.read_text(encoding="utf-8")[:1800])\n'
            "else:\n"
            '    print("Missing:", p)\n'
        )
    if tutorial_id == "t18":
        return (
            'base = repo_root / "benchmark" / "results" / "tutorials" / "t18_byoc"\n'
            "if not base.is_dir():\n"
            '    print("Missing:", base)\n'
            "else:\n"
            "    for d in sorted(base.iterdir(), reverse=True):\n"
            '        f = d / "benchmark_latest.json"\n'
            "        if f.is_file():\n"
            '            print(json.dumps(json.loads(f.read_text(encoding="utf-8")), indent=2)[:2000])\n'
            "            break\n"
            "    else:\n"
            '        print("No benchmark_latest.json under", base)\n'
        )
    if tutorial_id == "t19":
        return (
            'p = repo_root / "benchmark" / "results" / "benchmark_latest_drift.md"\n'
            "if p.is_file():\n"
            '    print(p.read_text(encoding="utf-8")[:1800])\n'
            "else:\n"
            '    print("Missing:", p)\n'
        )
    if tutorial_id == "t20":
        return (
            "with create_sync_logger(\n"
            "    config_path=CONFIG_PATH,\n"
            "    strict_unknown_fields=True,\n"
            '    name="tutorial-t20",\n'
            ") as logger:\n"
            '    logger.info("onboarding check", layer="app", context={"tutorial": "t20"})\n'
        )
    raise KeyError(tutorial_id)


def scenario_results_code(tutorial_id: str) -> Optional[str]:
    """§6 — optional tail of log files (None = markdown-only §6)."""
    root = _log_root_expr()
    if tutorial_id == "t03":
        return (
            f"_root = {root}\n"
            'print("Last lines (if files exist):")\n'
            'for _name in ("api.jsonl", "worker.jsonl"):\n'
            "    _p = _root / _name\n"
            '    print(f"--- {_name} ---")\n'
            "    if _p.is_file():\n"
            "        for _line in _p.read_text(encoding=\"utf-8\").splitlines()[-6:]:\n"
            "            print(_line)\n"
        )
    if tutorial_id in {"t08", "t09", "t16", "t20"}:
        fname = {
            "t08": "dev_app.jsonl",
            "t09": "prod_app.jsonl",
            "t16": "enterprise_app.jsonl",
            "t20": "enterprise_app.jsonl",
        }[tutorial_id]
        return (
            f"_root = {root}\n"
            f'_p = _root / "{fname}"\n'
            f'print("--- {fname} (tail) ---")\n'
            "if _p.is_file():\n"
            "    for _line in _p.read_text(encoding=\"utf-8\").splitlines()[-8:]:\n"
            "        print(_line)\n"
            "else:\n"
            '    print("(missing — run §5 first)")\n'
        )
    if tutorial_id == "t04":
        return (
            f"_root = {root}\n"
            '_p = _root / "dev_app.jsonl"\n'
            'print("--- dev_app.jsonl (tail) ---")\n'
            "if _p.is_file():\n"
            "    for _line in _p.read_text(encoding=\"utf-8\").splitlines()[-8:]:\n"
            "        print(_line)\n"
            "else:\n"
            '    print("(missing — run §5 first)")\n'
        )
    return None


def is_benchmark_scenario(tutorial_id: str) -> bool:
    return tutorial_id in {"t17", "t18", "t19"}


def uses_hydra_config_path(tutorial_id: str) -> bool:
    return not is_benchmark_scenario(tutorial_id)


def build_scenario_code(tutorial_id: str) -> str:
    """Legacy concatenation for tests or callers expecting one block (always includes ``CONFIG_PATH``)."""
    imp = scenario_imports(tutorial_id)
    cfg = f'CONFIG_PATH = repo_root / "examples" / "config" / "{_config_name(tutorial_id)}"\n\n'
    return imp + cfg + scenario_main(tutorial_id)


def _config_name(tutorial_id: str) -> str:
    mapping = {
        "t02": "tutorial_t02_configuration_recipes.yaml",
        "t03": "enterprise_multi_layer_api_worker.yaml",
        "t04": "dev_console_file.yaml",
        "t08": "dev_console_file.yaml",
        "t09": "prod_jsonl_strict.yaml",
        "t12": "network_http_basic.yaml",
        "t13": "network_ws_basic.yaml",
        "t14": "network_http_batched.yaml",
        "t16": "enterprise_onboarding_starter.yaml",
        "t17": "base_default.yaml",
        "t18": "base_default.yaml",
        "t19": "prod_jsonl_strict.yaml",
        "t20": "enterprise_onboarding_starter.yaml",
    }
    return mapping[tutorial_id]
