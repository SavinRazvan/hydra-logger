# Tutorial config presets

YAML/JSON under this folder backs **`examples/tutorials/notebooks/`** and **`examples/tutorials/cli_tutorials/`**.
Run tutorials from the **repository root** so relative paths resolve like CI.

## Where logs go (two buckets)

| Track | Directory | How it is set |
|-------|-----------|----------------|
| **Notebooks** (`.ipynb` loading these presets in repo mode) | `examples/logs/notebooks/` | Presets use **`base_log_dir: examples/logs`** and **`log_dir_name: notebooks`**, plus a **short** `path` stem (e.g. `t01_app` → `t01_app.jsonl`). |
| **CLI scripts** (`cli_tutorials/t*.py`) | `examples/logs/cli-tutorials/` | Each script sets `LoggingConfig(..., base_log_dir="examples/logs", log_dir_name="cli-tutorials", ...)` so CLI output stays separate from notebook runs. |

**T01 CLI** loads `tutorial_t01_enterprise_layers.yaml` from this folder (notebook-oriented `log_dir_name`) and overrides **`log_dir_name` to `cli-tutorials`** in code so the CLI path stays consistent.

If you use `path: examples/logs/notebooks/foo.jsonl` **without** setting `base_log_dir` / `log_dir_name`, the library joins relative paths under the default `./logs` root → you get nested paths like `logs/examples/logs/...` instead of `examples/logs/notebooks/`.

**Jupyter notebooks** resolve the clone and read these files from **`examples/config/`** as-is (set
`HYDRA_LOGGER_REPO` if the kernel cwd is not the repo root). There is no temp copy of presets.

## Naming convention

- `base_*` — baseline presets
- `dev_*` — development
- `prod_*` — production / strict
- `network_*` — typed network destinations
- `enterprise_*` — enterprise policy starters
- `tutorial_*` — notebook/script pairs (e.g. T01)

## Preset list

- `base_default.yaml`, `base_minimal.yaml`, `base_overlay_debug.yaml`
- `dev_console_file.yaml`, `dev_console_file.json` — JSON demonstrates the same `LoggingConfig` shape as YAML (see **T03** notebook §3b).
- `prod_jsonl_strict.yaml`
- `network_http_basic.yaml`, `network_http_batched.yaml`, `network_ws_basic.yaml`, `network_socket_datagram.yaml` — HTTP/WS basics attach **console + JSONL** sinks (`t12_*` / `t13_*` / `t14_*` stems) for visible artifacts under **`examples/logs/notebooks/`** when notebooks load these YAML files (repo mode). HTTP presets use **`connection_probe: false`** on `httpbin.org/post` (HEAD would return **405**). **`network_ws_basic`** keeps **`use_real_websocket_transport: false`** so T13 runs without outbound DNS/TCP (WSL/CI-safe); set **`true`** for a real echo server when the network resolves.
- `enterprise_multi_layer_api_worker.yaml`, `enterprise_onboarding_starter.yaml`
- `tutorial_t01_enterprise_layers.yaml` — T01: `app` / `audit` / `error` layers
- `tutorial_t02_configuration_recipes.yaml` — T02: `extends: base_default.yaml` + DEBUG overlay on `app`
  (same idea as `base_overlay_debug.yaml`, tutorial-named entry point)
- **Benchmark notebooks (T17–T19)** — §5 reads `benchmark/results/` only; §3 still sets `CONFIG_PATH` to a **paired**
  preset so the file is on disk next to the narrative: **T17/T18** → `base_default.yaml`, **T19** → `prod_jsonl_strict.yaml`.

## Quick smoke (repo root)

```bash
.hydra_env/bin/python -c "from hydra_logger import create_sync_logger; \
logger=create_sync_logger(config_path='examples/config/dev_console_file.yaml'); \
logger.info('preset ok', layer='app'); logger.close()"
```

## Notes

- Prefer **`load_logging_config`** / **`create_sync_logger(config_path=...)`** for YAML.
- JSON on disk: `json.loads(path.read_text())` then **`LoggingConfig.model_validate(...)`** (see T03 notebook).
- Network presets may need **`pip install 'hydra-logger[network]'`** and real connectivity for delivery;
  tutorials still validate **config + handler wiring**.

See also:

- `examples/tutorials/README.md` — [Tutorials index](../tutorials/README.md)
- `examples/README.md` — [Examples root](../README.md)
