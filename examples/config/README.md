# Tutorial config presets

YAML/JSON under this folder backs **`examples/tutorials/python/`** and **`examples/tutorials/notebooks/`**.
Run tutorials from the **repository root** so relative paths resolve like CI.

## File destination paths

Presets that write under `examples/logs/tutorials/` use **`base_log_dir: examples/logs`** and
**`log_dir_name: tutorials`**, plus a **short** destination `path` (e.g. `t01_app` → `t01_app.jsonl`).

If you use `path: examples/logs/tutorials/foo.jsonl` **without** setting the log root, the library
joins it to the default `./logs` directory → files appear under `logs/examples/logs/...` instead of
`examples/logs/tutorials/`.

## Naming convention

- `base_*` — baseline presets
- `dev_*` — development
- `prod_*` — production / strict
- `network_*` — typed network destinations
- `enterprise_*` — enterprise policy starters
- `tutorial_*` — notebook/script pairs (e.g. T01)

## Preset list

- `base_default.yaml`, `base_minimal.yaml`, `base_overlay_debug.yaml`
- `dev_console_file.yaml`, `dev_console_file.json`
- `prod_jsonl_strict.yaml`
- `network_http_basic.yaml`, `network_http_batched.yaml`, `network_ws_basic.yaml`, `network_socket_datagram.yaml`
- `enterprise_multi_layer_api_worker.yaml`, `enterprise_onboarding_starter.yaml`
- `tutorial_t01_enterprise_layers.yaml` — T01: `app` / `audit` / `error` layers

## Quick smoke (repo root)

```bash
.hydra_env/bin/python -c "from hydra_logger import create_sync_logger; \
logger=create_sync_logger(config_path='examples/config/dev_console_file.yaml'); \
logger.info('preset ok', layer='app'); logger.close()"
```

## Notes

- Prefer **`load_logging_config`** / **`create_sync_logger(config_path=...)`** for YAML; JSON can be
  loaded with `json.loads` and passed as a dict where supported.
- Network presets may need **`pip install 'hydra-logger[network]'`** and real connectivity for delivery;
  tutorials still validate **config + handler wiring**.

See also:

- `examples/tutorials/README.md` — [Tutorials index](../tutorials/README.md)
- `examples/README.md` — [Examples root](../README.md)
