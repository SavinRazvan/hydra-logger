# Plan index (public)

| Initiative | Plan | Status |
|---|---|---|
| Config from path, YAML templates, safe vendor hooks | [`config-from-path-enterprise.md`](config-from-path-enterprise.md) | implemented (see code: `hydra_logger.config.loader`, encoder registry) |
| Code-fix hardening (lifecycle, WS config, extensions) | [`code-fix-hardening.md`](code-fix-hardening.md) | implemented (see `hydra_logger.utils.reliability_lifecycle`, `LogDestination.use_real_websocket_transport`) |

## Notes

- Update status as slices merge.
- Link related audit or benchmark evidence from `docs/audit/` or `benchmark/results/` when applicable.
