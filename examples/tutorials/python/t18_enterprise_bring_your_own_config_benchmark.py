"""
Role: T18 enterprise BYOC benchmark workflow tutorial script.
Used By:
 - examples/tutorials/README.md
Depends On:
 - hydra_logger public API
Notes:
 - Provides deterministic local outputs for onboarding flows.
"""

from hydra_logger import LogDestination, LogLayer, LoggingConfig, create_logger


def main() -> None:
    config = LoggingConfig(
        layers={
            'tutorial': LogLayer(
                destinations=[
                    LogDestination(type='console', format='colored', use_colors=False),
                    LogDestination(
                        type='file',
                        path='examples/logs/tutorials/t18_enterprise_bring_your_own_config_benchmark.jsonl',
                        format='json-lines',
                    ),
                ]
            )
        }
    )

    with create_logger(config, logger_type='sync') as logger:
        logger.info('T18 enterprise BYOC benchmark workflow started', layer='tutorial')
        logger.info('T18 enterprise BYOC benchmark workflow completed', layer='tutorial')


if __name__ == '__main__':
    main()
