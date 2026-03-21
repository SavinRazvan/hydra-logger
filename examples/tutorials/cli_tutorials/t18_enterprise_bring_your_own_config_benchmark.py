"""
Role: T18 enterprise BYOC benchmark workflow tutorial script.
Used By:
 - examples/tutorials/README.md
Depends On:
 - hydra_logger public API
Notes:
 - Provides deterministic local outputs for onboarding flows.
"""

import os
import sys

from hydra_logger import LogDestination, LogLayer, LoggingConfig, create_logger

_TUTORIALS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TUTORIALS_ROOT not in sys.path:
    sys.path.insert(0, _TUTORIALS_ROOT)

from shared.cli_tutorial_footer import print_cli_tutorial_footer


def main() -> None:
    config = LoggingConfig(
        base_log_dir='examples/logs',
        log_dir_name='cli-tutorials',
        layers={
            'tutorial': LogLayer(
                destinations=[
                    LogDestination(type='console', format='colored', use_colors=False),
                    LogDestination(
                        type='file',
                        path='t18_enterprise_bring_your_own_config_benchmark',
                        format='json-lines',
                    ),
                ]
            )
        }
    )

    with create_logger(config, logger_type='sync') as logger:
        logger.info('T18 enterprise BYOC benchmark workflow started', layer='tutorial')
        logger.info('T18 enterprise BYOC benchmark workflow completed', layer='tutorial')

    print_cli_tutorial_footer(
        code='T18',
        title='Bring-your-own-config benchmark workflow',
        console='Hydra console lines above; JSONL captures BYOC markers.',
        artifacts=['examples/logs/cli-tutorials/t18_enterprise_bring_your_own_config_benchmark.jsonl'],
        takeaway='Swap in your YAML/JSON preset and keep the same benchmark harness.',
        notebook_rel='examples/tutorials/notebooks/t18_enterprise_bring_your_own_config_benchmark.ipynb',
    )


if __name__ == '__main__':
    main()
