"""
Role: T16 enterprise config templates at scale tutorial script.
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
                        path='t16_enterprise_config_templates_at_scale',
                        format='json-lines',
                    ),
                ]
            )
        }
    )

    with create_logger(config, logger_type='sync') as logger:
        logger.info('T16 enterprise config templates at scale started', layer='tutorial')
        logger.info('T16 enterprise config templates at scale completed', layer='tutorial')

    print_cli_tutorial_footer(
        code='T16',
        title='Enterprise config templates at scale',
        console='Hydra console lines above; JSONL is the durable artifact.',
        artifacts=['examples/logs/cli-tutorials/t16_enterprise_config_templates_at_scale.jsonl'],
        takeaway='Template-style configs stay identical across envs; vary only overlays.',
        notebook_rel='examples/tutorials/notebooks/t16_enterprise_config_templates_at_scale.ipynb',
    )


if __name__ == '__main__':
    main()
