---
name: Bug report
about: Create a report to help us improve Hydra-Logger
title: '[BUG] '
labels: ['bug', 'needs-triage']
assignees: ''
---

## 🐛 Bug Description

A clear and concise description of what the bug is.

## 🔄 Steps to Reproduce

1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## ✅ Expected Behavior

A clear and concise description of what you expected to happen.

## ❌ Actual Behavior

A clear and concise description of what actually happened.

## 📋 Environment

- **OS**: [e.g. Ubuntu 20.04, Windows 10, macOS 12.0]
- **Python Version**: [e.g. 3.8.10, 3.9.7, 3.11.0]
- **Hydra-Logger Version**: [e.g. 0.4.0]
- **Other Dependencies**: [e.g. pydantic==2.0.0]

## 📝 Code Example

```python
from hydra_logger import HydraLogger

# Your code here
logger = HydraLogger()
logger.info("TEST", "This should work")
```

## 📄 Error Messages

```
Traceback (most recent call last):
  File "example.py", line 10, in <module>
    logger.info("TEST", "message")
ValueError: Invalid log level
```

## 🔍 Additional Context

Add any other context about the problem here, such as:
- Configuration files used
- Log files generated
- Related issues or pull requests

## 📋 Checklist

- [ ] I have searched existing issues to avoid duplicates
- [ ] I have provided a minimal code example
- [ ] I have included error messages and tracebacks
- [ ] I have specified my environment details
- [ ] I have tested with the latest version of Hydra-Logger 