"""
Role: T17 enterprise benchmark comparison workflow tutorial script.
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
                        path='t17_enterprise_benchmark_comparison_workflow',
                        format='json-lines',
                    ),
                ]
            )
        }
    )

    with create_logger(config, logger_type='sync') as logger:
        logger.info('T17 enterprise benchmark comparison workflow started', layer='tutorial')
        logger.info('T17 enterprise benchmark comparison workflow completed', layer='tutorial')

    print_cli_tutorial_footer(
        code='T17',
        title='Enterprise benchmark comparison workflow',
        console='Hydra console lines above; JSONL records the benchmark lifecycle markers.',
        artifacts=['examples/logs/cli-tutorials/t17_enterprise_benchmark_comparison_workflow.jsonl'],
        takeaway='Use this script as the CLI twin of the T17 notebook for CI/smoke narratives.',
        notebook_rel='examples/tutorials/notebooks/t17_enterprise_benchmark_comparison_workflow.ipynb',
    )


if __name__ == '__main__':
    main()
