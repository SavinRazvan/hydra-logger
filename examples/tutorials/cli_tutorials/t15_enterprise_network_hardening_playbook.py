"""
Role: Enterprise network hardening tutorial script.
Used By:
 - examples/tutorials/README.md
Depends On:
 - hydra_logger public API
Notes:
 - Demonstrates strict reliability posture with deterministic local outputs.
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
        strict_reliability_mode=True,
        reliability_error_policy='warn',
        layers={
            'network_hardening': LogLayer(
                destinations=[
                    LogDestination(type='console', format='colored', use_colors=False),
                    LogDestination(
                        type='file',
                        path='t15_network_hardening_results',
                        format='json-lines',
                    ),
                ]
            )
        },
    )

    with create_logger(config, logger_type='sync') as logger:
        logger.info('T15 network hardening started', layer='network_hardening')
        logger.info('Strict reliability mode enabled', layer='network_hardening')

    print_cli_tutorial_footer(
        code='T15',
        title='Enterprise network hardening playbook',
        console='Hydra console lines above; JSONL captures the same events for review.',
        artifacts=['examples/logs/cli-tutorials/t15_network_hardening_results.jsonl'],
        takeaway='Pair strict_reliability_mode with explicit network layer logging for audits.',
        notebook_rel=None,
    )


if __name__ == '__main__':
    main()
