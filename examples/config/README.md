# Tutorial Config Presets

Use these presets for canonical tutorial onboarding.

## File destination paths

Presets that write under `examples/logs/tutorials/` set **`base_log_dir: examples/logs`**
and **`log_dir_name: tutorials`**, then use a **short** destination `path` (for example
`t01_app`, resolved to `t01_app.jsonl` by format).

If you use a long path like `examples/logs/tutorials/foo.jsonl` **without** adjusting the
log root, the library joins it against the default `./logs` working directory, which lands
files under `logs/examples/logs/...` (easy to “lose” when browsing `examples/logs/...`).

## Naming Convention

- `base_*` - baseline presets
- `dev_*` - development presets
- `prod_*` - production presets
- `network_*` - network transport presets
- `enterprise_*` - enterprise policy presets

## Presets

- `base_default.yaml`
- `base_minimal.yaml`
- `base_overlay_debug.yaml`
- `dev_console_file.yaml`
- `dev_console_file.json`
- `prod_jsonl_strict.yaml`
- `network_http_basic.yaml`
- `network_http_batched.yaml`
- `network_ws_basic.yaml`
- `network_socket_datagram.yaml`
- `enterprise_multi_layer_api_worker.yaml`
- `enterprise_onboarding_starter.yaml`
- `tutorial_t01_enterprise_layers.yaml` — T01 notebook/script: `app` / `audit` / `error` layers

These files are the canonical preset names for docs, tests, and tutorials.
# Tutorial Config Presets

This folder contains standardized configuration presets used by tutorials.

## Naming Convention

- `base_*` - baseline starter presets
- `dev_*` - development-focused presets
- `prod_*` - production-focused presets
- `network_*` - transport-specific network presets
- `enterprise_*` - enterprise policy presets

## Presets

- `base_default.yaml`
- `base_minimal.yaml`
- `base_overlay_debug.yaml`
- `dev_console_file.yaml`
- `dev_console_file.json`
- `prod_jsonl_strict.yaml`
- `network_http_basic.yaml`
- `network_http_batched.yaml`
- `network_ws_basic.yaml`
- `network_socket_datagram.yaml`
- `enterprise_multi_layer_api_worker.yaml`
- `enterprise_onboarding_starter.yaml`
- `tutorial_t01_enterprise_layers.yaml`

Use these presets directly from tutorials or as templates for custom onboarding scenarios.
# Config Presets For Onboarding

This folder contains ready-to-use configuration presets that help teams onboard
with `config_path` quickly.

## Quick Start

```bash
.hydra_env/bin/python -c "from hydra_logger import create_sync_logger; \
logger=create_sync_logger(config_path='examples/config/development_console_file.yaml'); \
logger.info('Config preset boot', layer='app'); logger.close()"
```

## Preset Guide

- `minimal.yaml`: smallest valid config (single console destination).
- `base.yaml`: baseline root config used by `extends` overlays.
- `overlay.yaml`: simple debug overlay example over `base.yaml`.
- `development_console_file.yaml`: developer-friendly console + file JSON lines.
- `production_jsonl_strict.yaml`: strict reliability and confined file paths.
- `multi_layer_api_worker.yaml`: API/worker/database layered routing starter.
- `with_network_http.yaml`: typed `network_http` destination starter.
- `with_network_http_batched.yaml`: HTTP destination with batching enabled.
- `with_network_ws.yaml`: typed `network_ws` destination starter.
- `with_network_socket_datagram.yaml`: socket/datagram destination starter.
- `enterprise_onboarding_starter.yaml`: production profile plus network ingest layer.
- `development_console_file.json`: JSON variant for teams managing config in JSON stores.

## Notes

- `load_logging_config` currently loads YAML files; JSON configs can be loaded with
  `json.loads(...)` and passed as dict to `create_logger`.
- Some network examples are designed for shape validation and local integration
  wiring. Real remote delivery depends on runtime connectivity and optional extras.
