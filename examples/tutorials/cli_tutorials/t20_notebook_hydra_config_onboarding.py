"""
Role: T20 notebook config onboarding runtime companion tutorial script.
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
                        path='t20_notebook_hydra_config_onboarding',
                        format='json-lines',
                    ),
                ]
            )
        }
    )

    with create_logger(config, logger_type='sync') as logger:
        logger.info('T20 notebook config onboarding runtime companion started', layer='tutorial')
        logger.info('T20 notebook config onboarding runtime companion completed', layer='tutorial')

    print_cli_tutorial_footer(
        code='T20',
        title='Notebook Hydra config onboarding (CLI companion)',
        console='Hydra console lines above; JSONL mirrors the notebook companion story.',
        artifacts=['examples/logs/cli-tutorials/t20_notebook_hydra_config_onboarding.jsonl'],
        takeaway='Run this after T20 in Jupyter to compare CLI vs notebook narratives.',
        notebook_rel='examples/tutorials/notebooks/t20_notebook_hydra_config_onboarding.ipynb',
    )


if __name__ == '__main__':
    main()
