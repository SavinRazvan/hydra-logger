"""
Role: Per-tutorial notebook code bodies and short output hints.
Used By:
 - examples/tutorials/notebooks/temp_nb_factory/generate_notebooks.py
Depends On:
 - typing
Notes:
 - Code is appended after bootstrap (repo root cwd only). Keep scenarios linear and short.
"""

from __future__ import annotations

from typing import Dict, List

# Short hints for the intro markdown "Check" list.
SCENARIO_INSPECT: Dict[str, List[str]] = {
    "t02": ["Overlay extends `base_default.yaml`; you should see a DEBUG line on console."],
    "t03": ["Logs split by layer: `examples/logs/tutorials/api.jsonl` vs `worker.jsonl`."],
    "t04": ["`model_copy` adds a security extension; password-like fields may be redacted in files."],
    "t08": ["Colored console + JSONL file from `dev_console_file.yaml`."],
    "t09": ["File-only preset: output in `examples/logs/tutorials/prod_app.jsonl`."],
    "t12": ["Typed `network_http` on layer `ship` (outbound may fail offline; config is the point)."],
    "t13": ["Typed `network_ws` on layer `stream`."],
    "t14": ["Batched HTTP preset — compare YAML to T12."],
    "t16": ["Enterprise starter → `examples/logs/tutorials/enterprise_app.jsonl`."],
    "t17": ["Prints an excerpt of `benchmark/results/benchmark_latest_summary.md` if it exists."],
    "t18": ["Prints latest `benchmark_latest.json` under `benchmark/results/tutorials/t18_byoc/` if present."],
    "t19": ["Prints an excerpt of `benchmark/results/benchmark_latest_drift.md` if it exists."],
    "t20": ["Same enterprise preset as T16 — strict paths + JSONL."],
}


def build_scenario_code(tutorial_id: str) -> str:
    """Return Python source for the tutorial (after bootstrap)."""
    if tutorial_id == "t02":
        return '''from hydra_logger import create_sync_logger

CONFIG_PATH = repo_root / "examples" / "config" / "base_overlay_debug.yaml"

with create_sync_logger(
    config_path=CONFIG_PATH,
    strict_unknown_fields=True,
    name="tutorial-t02",
) as logger:
    logger.debug("overlay enables DEBUG on app", layer="app", context={"tutorial": "t02"})
    logger.info("merged config active", layer="app")
'''

    if tutorial_id == "t03":
        return '''from hydra_logger import create_sync_logger

CONFIG_PATH = repo_root / "examples" / "config" / "enterprise_multi_layer_api_worker.yaml"

with create_sync_logger(
    config_path=CONFIG_PATH,
    strict_unknown_fields=True,
    name="tutorial-t03",
) as logger:
    logger.info("request ok", layer="api", context={"route": "/v1/orders"})
    logger.info("job running", layer="worker", context={"job_id": "job-1"})
'''

    if tutorial_id == "t04":
        return '''from hydra_logger import create_sync_logger
from hydra_logger.config.loader import load_logging_config

path = repo_root / "examples" / "config" / "dev_console_file.yaml"
cfg = load_logging_config(path, strict_unknown_fields=True)
cfg = cfg.model_copy(
    update={
        "extensions": {
            "security_redaction": {
                "enabled": True,
                "type": "security",
                "patterns": ["password", "secret"],
            }
        }
    }
)

with create_sync_logger(cfg, strict_unknown_fields=True, name="tutorial-t04") as logger:
    logger.info("login", layer="app", extra={"password": "do-not-log-raw"})
'''

    if tutorial_id == "t08":
        return '''from hydra_logger import create_sync_logger

CONFIG_PATH = repo_root / "examples" / "config" / "dev_console_file.yaml"

with create_sync_logger(
    config_path=CONFIG_PATH,
    strict_unknown_fields=True,
    name="tutorial-t08",
) as logger:
    logger.info("info", layer="app")
    logger.warning("warning", layer="app")
    logger.error("error", layer="app")
'''

    if tutorial_id == "t09":
        return '''from hydra_logger import create_sync_logger

CONFIG_PATH = repo_root / "examples" / "config" / "prod_jsonl_strict.yaml"

with create_sync_logger(
    config_path=CONFIG_PATH,
    strict_unknown_fields=True,
    name="tutorial-t09",
) as logger:
    logger.info("event", layer="app", context={"order_id": "ORD-1"})
'''

    if tutorial_id == "t12":
        return '''from hydra_logger import create_sync_logger

CONFIG_PATH = repo_root / "examples" / "config" / "network_http_basic.yaml"

with create_sync_logger(
    config_path=CONFIG_PATH,
    strict_unknown_fields=True,
    name="tutorial-t12",
) as logger:
    logger.info("ship", layer="ship", context={"batch_id": "b1"})
'''

    if tutorial_id == "t13":
        return '''from hydra_logger import create_sync_logger

CONFIG_PATH = repo_root / "examples" / "config" / "network_ws_basic.yaml"

with create_sync_logger(
    config_path=CONFIG_PATH,
    strict_unknown_fields=True,
    name="tutorial-t13",
) as logger:
    logger.info("stream", layer="stream", context={"session_id": "s1"})
'''

    if tutorial_id == "t14":
        return '''from hydra_logger import create_sync_logger

CONFIG_PATH = repo_root / "examples" / "config" / "network_http_batched.yaml"

with create_sync_logger(
    config_path=CONFIG_PATH,
    strict_unknown_fields=True,
    name="tutorial-t14",
) as logger:
    logger.info("batched", layer="ship", context={"batch_id": "b14"})
'''

    if tutorial_id == "t16":
        return '''from hydra_logger import create_sync_logger

CONFIG_PATH = repo_root / "examples" / "config" / "enterprise_onboarding_starter.yaml"

with create_sync_logger(
    config_path=CONFIG_PATH,
    strict_unknown_fields=True,
    name="tutorial-t16",
) as logger:
    logger.info("enterprise template", layer="app", context={"env": "notebook"})
'''

    if tutorial_id == "t17":
        return '''from pathlib import Path

p = repo_root / "benchmark" / "results" / "benchmark_latest_summary.md"
if p.is_file():
    print(p.read_text(encoding="utf-8")[:1800])
else:
    print("Missing:", p)
'''

    if tutorial_id == "t18":
        return '''import json
from pathlib import Path

base = repo_root / "benchmark" / "results" / "tutorials" / "t18_byoc"
if not base.is_dir():
    print("Missing:", base)
else:
    for d in sorted(base.iterdir(), reverse=True):
        f = d / "benchmark_latest.json"
        if f.is_file():
            print(json.dumps(json.loads(f.read_text(encoding="utf-8")), indent=2)[:2000])
            break
    else:
        print("No benchmark_latest.json under", base)
'''

    if tutorial_id == "t19":
        return '''from pathlib import Path

p = repo_root / "benchmark" / "results" / "benchmark_latest_drift.md"
if p.is_file():
    print(p.read_text(encoding="utf-8")[:1800])
else:
    print("Missing:", p)
'''

    if tutorial_id == "t20":
        return '''from hydra_logger import create_sync_logger

CONFIG_PATH = repo_root / "examples" / "config" / "enterprise_onboarding_starter.yaml"

with create_sync_logger(
    config_path=CONFIG_PATH,
    strict_unknown_fields=True,
    name="tutorial-t20",
) as logger:
    logger.info("onboarding check", layer="app", context={"tutorial": "t20"})
'''

    raise KeyError(f"Unknown scenario tutorial_id={tutorial_id!r}")
