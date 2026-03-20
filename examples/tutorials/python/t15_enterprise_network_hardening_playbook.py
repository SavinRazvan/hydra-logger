"""
Role: Enterprise network hardening tutorial script.
Used By:
 - examples/tutorials/README.md
Depends On:
 - hydra_logger public API
Notes:
 - Demonstrates strict reliability posture with deterministic local outputs.
"""

from hydra_logger import LogDestination, LogLayer, LoggingConfig, create_logger


def main() -> None:
    config = LoggingConfig(
        strict_reliability_mode=True,
        reliability_error_policy='warn',
        layers={
            'network_hardening': LogLayer(
                destinations=[
                    LogDestination(type='console', format='colored', use_colors=False),
                    LogDestination(
                        type='file',
                        path='examples/logs/tutorials/t15_network_hardening_results.jsonl',
                        format='json-lines',
                    ),
                ]
            )
        },
    )

    with create_logger(config, logger_type='sync') as logger:
        logger.info('T15 network hardening started', layer='network_hardening')
        logger.info('Strict reliability mode enabled', layer='network_hardening')


if __name__ == '__main__':
    main()
