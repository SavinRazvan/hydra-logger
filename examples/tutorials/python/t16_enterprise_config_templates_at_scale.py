"""
Role: T16 enterprise config templates at scale tutorial script.
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
                        path='examples/logs/tutorials/t16_enterprise_config_templates_at_scale.jsonl',
                        format='json-lines',
                    ),
                ]
            )
        }
    )

    with create_logger(config, logger_type='sync') as logger:
        logger.info('T16 enterprise config templates at scale started', layer='tutorial')
        logger.info('T16 enterprise config templates at scale completed', layer='tutorial')


if __name__ == '__main__':
    main()
