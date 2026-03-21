"""
Role: T19 enterprise nightly drift snapshot tutorial script.
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
                        path='t19_enterprise_nightly_drift_snapshot',
                        format='json-lines',
                    ),
                ]
            )
        }
    )

    with create_logger(config, logger_type='sync') as logger:
        logger.info('T19 enterprise nightly drift snapshot started', layer='tutorial')
        logger.info('T19 enterprise nightly drift snapshot completed', layer='tutorial')

    print_cli_tutorial_footer(
        code='T19',
        title='Nightly drift snapshot narrative',
        console='Hydra console lines above; JSONL is the snapshot artifact.',
        artifacts=['examples/logs/cli-tutorials/t19_enterprise_nightly_drift_snapshot.jsonl'],
        takeaway='Automate a single JSONL line per nightly run for diff-friendly drift tracking.',
        notebook_rel='examples/tutorials/notebooks/t19_enterprise_nightly_drift_snapshot.ipynb',
    )


if __name__ == '__main__':
    main()
