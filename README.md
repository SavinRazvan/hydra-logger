# Hydra-Logger

A high-performance, enterprise-grade logging library for Python applications.

## Features

- **High Performance**: Optimized for speed and memory efficiency
- **Multiple Handlers**: Console, file, network, and database logging
- **Async Support**: Full async/await support for modern Python applications
- **Flexible Configuration**: YAML, TOML, and environment-based configuration
- **Enterprise Ready**: Built for production environments

## Quick Start

```python
from hydra_logger import SyncLogger

# Create a logger
logger = SyncLogger()

# Log messages
logger.info("Application started")
logger.error("Something went wrong", extra={"user_id": 123})
```

## Installation

```bash
pip install hydra-logger
```

---

*Bugbot Review - Sun Sep 21 08:39:49 EEST 2025*
