# Contributing to Hydra-Logger

Thank you for your interest in contributing to Hydra-Logger! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/YOUR_USERNAME/hydra-logger.git`
3. **Create** a feature branch: `git checkout -b feature/amazing-feature`
4. **Install** in development mode: `pip install -e .`
5. **Install** dev dependencies: `pip install -r requirements-dev.txt`
6. **Make** your changes
7. **Test** your changes: `python -m pytest tests/`
8. **Commit** your changes: `git commit -m "Add amazing feature"`
9. **Push** to your branch: `git push origin feature/amazing-feature`
10. **Open** a Pull Request

## 📋 Development Setup

### Prerequisites
- Python 3.8+
- Git
- pip

### Installation
```bash
# Clone the repository
git clone https://github.com/SavinRazvan/hydra-logger.git
cd hydra-logger

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
```

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=hydra_logger --cov-report=html

# Run specific test file
python -m pytest tests/test_logger.py

# Run with verbose output
python -m pytest tests/ -v
```

### Running Examples
```bash
# Basic usage example
python demos/examples/basic_usage.py

# Multi-module demo
python demos/multi_module_demo.py

# Multi-file workflow demo
python demos/multi_file_workflow_demo.py
```

## 🏗️ Project Structure

```
hydra-logger/
├── hydra_logger/           # Main package code
│   ├── __init__.py
│   ├── compatibility.py    # Backward compatibility
│   ├── config.py          # Configuration management
│   └── logger.py          # Core logging functionality
├── demos/                  # Examples and demonstrations
│   ├── examples/          # Basic usage examples
│   ├── demo_modules/      # Example modules for demos
│   └── *.py              # Demo scripts
├── tests/                 # Test suite
├── docs/                  # Documentation (future)
├── .github/              # GitHub workflows and templates
└── *.md                  # Documentation files
```

## 📝 Code Style

### Python Code
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and single-purpose
- Use meaningful variable and function names

### Example
```python
def create_file_handler(destination: LogDestination, layer_level: str) -> RotatingFileHandler:
    """
    Create a rotating file handler for logging.
    
    Args:
        destination: Configuration for the file destination
        layer_level: Logging level for this layer
        
    Returns:
        Configured rotating file handler
        
    Raises:
        ValueError: If path is missing or invalid
        OSError: If file system operations fail
    """
    if not destination.path:
        raise ValueError("Path is required for file destinations")
    
    # Implementation...
```

### Documentation
- Update relevant documentation files
- Add examples for new features
- Update CHANGELOG.md for significant changes
- Write clear commit messages

## 🧪 Testing Guidelines

### Writing Tests
- Write tests for all new functionality
- Aim for 100% code coverage
- Test both success and error cases
- Use descriptive test names
- Group related tests in classes

### Example Test
```python
class TestNewFeature:
    """Test the new feature functionality."""
    
    def test_new_feature_success(self):
        """Test successful operation of new feature."""
        # Arrange
        expected = "expected_result"
        
        # Act
        result = new_feature()
        
        # Assert
        assert result == expected
    
    def test_new_feature_error_handling(self):
        """Test error handling in new feature."""
        with pytest.raises(ValueError, match="Invalid input"):
            new_feature(invalid_input=True)
```

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=hydra_logger --cov-report=term-missing

# Run specific test
python -m pytest tests/test_logger.py::TestHydraLogger::test_basic_logging
```

## 🔄 Pull Request Process

### Before Submitting
1. **Test** your changes thoroughly
2. **Update** documentation if needed
3. **Add** tests for new functionality
4. **Update** CHANGELOG.md if adding features or fixing bugs
5. **Ensure** all tests pass
6. **Check** code style and formatting

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Examples updated if needed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment**: Python version, OS, package versions
2. **Steps to reproduce**: Clear, step-by-step instructions
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Code example**: Minimal code to reproduce the issue
6. **Error messages**: Full error traceback if applicable

## 💡 Feature Requests

When requesting features, please include:

1. **Use case**: Why this feature is needed
2. **Proposed solution**: How you think it should work
3. **Alternatives considered**: Other approaches you've thought about
4. **Impact**: How this affects existing functionality

## 📚 Documentation

### Adding Examples
- Place new examples in `demos/examples/`
- Update `demos/examples/README.md` if needed
- Test examples to ensure they work

### Updating Documentation
- Keep documentation up-to-date with code changes
- Use clear, concise language
- Include code examples where helpful
- Test all code examples in documentation

## 🤝 Community Guidelines

- Be respectful and inclusive
- Help others learn and contribute
- Provide constructive feedback
- Follow the project's code of conduct
- Celebrate contributions and improvements

## 📞 Getting Help

- **Issues**: Use GitHub Issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Documentation**: Check README.md, QUICK_START.md, and TUTORIAL.md

## 🏆 Recognition

Contributors will be recognized in:
- CHANGELOG.md for significant contributions
- README.md for major contributors
- GitHub repository contributors list

Thank you for contributing to Hydra-Logger! 🚀 