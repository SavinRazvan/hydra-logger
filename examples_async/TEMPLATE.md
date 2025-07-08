# Example Template Structure

Each example folder should follow this structure:

```
XX_example_name/
├── main.py              # Main example code
├── config.py            # Configuration examples (if needed)
├── requirements.txt     # Dependencies (if needed)
├── README.md           # Detailed explanation
├── output/             # Sample output and logs
│   ├── logs/           # Generated log files
│   └── screenshots/    # Output screenshots
└── tests/              # Example tests (if applicable)
    └── test_example.py
```

## File Templates

### `main.py` Template
```python
"""
Example: [Brief description]

This example demonstrates [specific feature/pattern].
[Detailed explanation of what this example shows]

Key concepts:
- [Concept 1]
- [Concept 2]
- [Concept 3]
"""

import asyncio
import os
from hydra_logger import AsyncHydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

async def main():
    """Main example function."""
    
    # Setup logger
    logger = AsyncHydraLogger(
        enable_performance_monitoring=True,
        redact_sensitive=True
    )
    
    # Example logging
    await logger.info("APP", "Example started")
    
    # [Example-specific code]
    
    # Cleanup
    await logger.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### `README.md` Template
```markdown
# [Example Name]

## Overview
[Brief description of what this example demonstrates]

## Key Features
- [Feature 1]
- [Feature 2]
- [Feature 3]

## Prerequisites
- [Requirement 1]
- [Requirement 2]

## Running the Example
```bash
python main.py
```

## Expected Output
[Describe what output to expect]

## Configuration
[Explain any configuration options]

## Use Cases
[When to use this pattern]

## Related Examples
- [Related example 1]
- [Related example 2]
```

### `requirements.txt` Template
```
# Core dependencies
hydra-logger

# Example-specific dependencies (if any)
# fastapi
# aiohttp
# redis
```

## Example Categories

### Basic Examples (01-04)
- Focus on simple setup and configuration
- Minimal dependencies
- Clear, step-by-step explanations

### Intermediate Examples (05-10)
- Common patterns and features
- Practical use cases
- Performance considerations

### Advanced Examples (11-20)
- Production-ready implementations
- Integration with external services
- Scalability and reliability patterns

### Expert Examples (21-30)
- Specialized scenarios
- Complex integrations
- Enterprise patterns

## Naming Conventions

- **Folders**: `XX_category_name/` (e.g., `01_basic_setup/`)
- **Files**: Use descriptive names (e.g., `main.py`, `config.py`)
- **Functions**: Use clear, descriptive names
- **Variables**: Follow Python naming conventions

## Documentation Standards

- **Clear explanations**: Explain the "why" not just the "how"
- **Code comments**: Comment complex logic
- **Examples**: Include multiple variations
- **Best practices**: Highlight important patterns
- **Troubleshooting**: Include common issues and solutions
```

## 🎯 **Example Implementation Checklist**

- [ ] **Basic Setup**: Simple async logger initialization
- [ ] **Configuration**: Proper config examples
- [ ] **Error Handling**: Graceful error handling
- [ ] **Performance**: Performance monitoring examples
- [ ] **Documentation**: Clear README with explanations
- [ ] **Testing**: Example tests (where applicable)
- [ ] **Dependencies**: Minimal, clear requirements
- [ ] **Output**: Sample logs and screenshots
- [ ] **Best Practices**: Production-ready patterns
- [ ] **Extensibility**: Easy to modify and extend 