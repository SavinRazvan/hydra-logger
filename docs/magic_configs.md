# 🪄 Custom Magic Config System

Hydra-Logger's magic config system lets you define and reuse logging configurations with a single line of code.

## Registering a Custom Config

```python
from hydra_logger import HydraLogger, LoggingConfig

@HydraLogger.register_magic("my_app", description="My app's logging config")
def my_app_config():
    return LoggingConfig(layers={"APP": LogLayer(...)})
```

## Using a Custom Config

```python
logger = HydraLogger.for_my_app()
```

## Listing Available Configs

```python
print(HydraLogger.list_magic_configs())
```

## Built-in Magic Configs
- `for_production()`
- `for_development()`
- `for_testing()`
- `for_microservice()`
- `for_web_app()`
- `for_api_service()`
- `for_background_worker()`

## Best Practices
- Use descriptive names for configs
- Document the purpose of each config with the `description` argument
- Share configs across your team or organization
- Use magic configs for environment-specific, team, or app-specific setups

## Example: Environment-Specific Configs

```python
@HydraLogger.register_magic("staging")
def staging_config():
    return LoggingConfig(...)

@HydraLogger.register_magic("production")
def production_config():
    return LoggingConfig(...)

logger = HydraLogger.for_staging()
``` 