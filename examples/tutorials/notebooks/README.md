# Tutorial notebooks

Jupyter notebooks for **hands-on onboarding**. Each notebook:

1. Adds `examples/tutorials` to `sys.path`, then calls `utility.notebook_bootstrap()` so **cwd = repo root**. **Start Jupyter from the repo root**, or set `HYDRA_LOGGER_REPO`.
2. **Multiple cells** (especially T01): setup → imports → config → domain → `create_sync_logger` + logs → optional file tails. Use **Run All** for the full story.
3. Intro lists **what to check** (console and/or `examples/logs/tutorials/`).

## Regenerate from source

```bash
python3 examples/tutorials/notebooks/temp_nb_factory/generate_notebooks.py
```

- Scenario code: `temp_nb_factory/scenarios.py`
- Layout + T01 template: `temp_nb_factory/generate_notebooks.py`

## Kernel

Use `.hydra_env` as the Jupyter kernel so `import hydra_logger` matches CI and `run_all_examples.py`.
