# Testing Guide

This guide covers how to test Hydra-Logger, generate coverage reports, and interpret the results.

## Running Tests

### Basic Test Execution

```bash
# Run all tests
python -m pytest

# Run tests with verbose output
python -m pytest -v

# Run tests with short traceback
python -m pytest --tb=short

# Run specific test file
python -m pytest tests/test_logger.py

# Run specific test function
python -m pytest tests/test_logger.py::test_hydra_logger_basic
```

### Test Configuration

The project uses `pyproject.toml` for pytest configuration:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=hydra_logger",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
]
```

## Coverage Reporting

### Generating Coverage Reports

```bash
# Generate coverage with terminal output
python -m pytest --cov=hydra_logger

# Generate HTML coverage report
python -m pytest --cov=hydra_logger --cov-report=html

# Generate XML coverage report (for CI/CD)
python -m pytest --cov=hydra_logger --cov-report=xml

# Generate all coverage formats
python -m pytest --cov=hydra_logger --cov-report=term-missing --cov-report=html --cov-report=xml
```

### Understanding Coverage Output

#### Terminal Output
```
Name                    Stmts   Miss  Cover   Missing
-----------------------------------------------------
hydra_logger/__init__.py     10      0   100%
hydra_logger/compatibility.py     45      0   100%
hydra_logger/config.py     85      0   100%
hydra_logger/logger.py    120      1    99%   245
-----------------------------------------------------
TOTAL                       260      1    99%
```

#### HTML Coverage Report

When you run `--cov-report=html`, it creates an `htmlcov/` directory with:

- `index.html` - Main coverage report
- Individual HTML files for each module
- CSS and JavaScript for interactive features

**To view the HTML report:**
```bash
# On macOS
open htmlcov/index.html

# On Linux
xdg-open htmlcov/index.html

# On Windows
start htmlcov/index.html
```

### Coverage Configuration

The coverage settings are configured in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["hydra_logger"]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/__pycache__/*",
    "*/migrations/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]
```

## Test Categories

### Unit Tests

```bash
# Run only unit tests (exclude integration tests)
python -m pytest -m "not integration"

# Run specific unit test categories
python -m pytest tests/test_logger.py      # Core logger functionality
python -m pytest tests/test_config.py      # Configuration handling
python -m pytest tests/test_compatibility.py  # Backward compatibility
```

### Integration Tests

```bash
# Run integration tests
python -m pytest -m "integration"

# Run specific integration test
python -m pytest tests/test_integration.py
```

### Slow Tests

```bash
# Skip slow tests
python -m pytest -m "not slow"

# Run only slow tests
python -m pytest -m "slow"
```

## Test Development

### Writing New Tests

#### Test File Structure
```python
import pytest
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

class TestNewFeature:
    """Test class for new feature."""
    
    def test_basic_functionality(self):
        """Test basic functionality of new feature."""
        # Arrange
        logger = HydraLogger()
        
        # Act
        result = logger.some_new_method("test")
        
        # Assert
        assert result is not None
    
    def test_edge_case(self):
        """Test edge case handling."""
        # Test implementation
        pass
    
    @pytest.mark.integration
    def test_integration_scenario(self):
        """Test integration with other components."""
        # Integration test implementation
        pass
```

#### Test Markers

```python
import pytest

@pytest.mark.slow
def test_slow_operation():
    """This test takes a long time to run."""
    pass

@pytest.mark.integration
def test_with_database():
    """This test requires a database connection."""
    pass

@pytest.mark.parametrize("input_value,expected", [
    ("test1", "result1"),
    ("test2", "result2"),
])
def test_parameterized(input_value, expected):
    """Test with multiple input values."""
    assert process(input_value) == expected
```

### Test Utilities

#### Temporary Files and Directories

```python
import pytest
import tempfile
import os
from pathlib import Path

class TestWithFiles:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_file_creation(self, temp_dir):
        """Test creating files in temporary directory."""
        log_file = os.path.join(temp_dir, "test.log")
        
        # Test file creation
        with open(log_file, 'w') as f:
            f.write("test log content")
        
        assert os.path.exists(log_file)
        assert os.path.getsize(log_file) > 0
```

#### Mocking

```python
import pytest
from unittest.mock import Mock, patch, MagicMock

class TestWithMocks:
    def test_with_mocked_file_system(self):
        """Test with mocked file system operations."""
        with patch('os.makedirs') as mock_makedirs:
            with patch('builtins.open', mock_open()) as mock_file:
                logger = HydraLogger()
                logger.info("TEST", "test message")
                
                # Verify makedirs was called
                mock_makedirs.assert_called()
                
                # Verify file was opened
                mock_file.assert_called()
    
    def test_with_mocked_logging(self):
        """Test with mocked logging module."""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            logger = HydraLogger()
            logger.info("TEST", "test message")
            
            # Verify logging was called
            mock_logger.info.assert_called()
```

## Continuous Integration

### GitHub Actions

The project includes a CI workflow in `.github/workflows/ci.yml`:

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.11, 3.12, 3.13]
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run tests with coverage
      run: |
        python -m pytest --cov=hydra_logger --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Local CI Simulation

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run linting
black --check .
flake8 .
mypy hydra_logger/

# Run tests with coverage
python -m pytest --cov=hydra_logger --cov-report=xml

# Run security checks
bandit -r hydra_logger/
safety check
```

## Coverage Analysis

### Understanding Coverage Metrics

#### Line Coverage
- **100%** - Every line of code is executed during tests
- **95-99%** - Excellent coverage, minor gaps
- **80-94%** - Good coverage, some areas need attention
- **<80%** - Poor coverage, significant gaps

#### Branch Coverage
- Tests both true and false branches of conditional statements
- More comprehensive than line coverage
- Identifies untested code paths

### Improving Coverage

#### Identify Gaps
```bash
# Generate detailed coverage report
python -m pytest --cov=hydra_logger --cov-report=term-missing

# Look for "Missing" column to see uncovered lines
```

#### Add Tests for Missing Coverage

```python
# Example: Adding test for error handling
def test_file_permission_error():
    """Test handling of file permission errors."""
    with patch('builtins.open', side_effect=PermissionError):
        logger = HydraLogger()
        # Should handle permission error gracefully
        logger.info("TEST", "test message")
        # Verify no exception is raised
```

#### Exclude Unreachable Code

```python
# In your code, mark unreachable lines
if False:  # pragma: no cover
    # This code is never reached
    unreachable_function()

# Or use coverage comments
def some_function():
    if condition:
        return True
    # pragma: no cover
    return False  # This line is never reached
```

## Best Practices

### Test Organization

1. **Group related tests** in test classes
2. **Use descriptive test names** that explain what is being tested
3. **Follow AAA pattern**: Arrange, Act, Assert
4. **Keep tests independent** - no shared state between tests
5. **Use fixtures** for common setup and teardown

### Coverage Goals

- **Aim for 90%+ line coverage** for production code
- **Focus on critical paths** and error handling
- **Don't chase 100%** if it means testing unreachable code
- **Use integration tests** to cover complex scenarios

### Performance

```bash
# Run tests in parallel (if pytest-xdist is installed)
python -m pytest -n auto

# Profile slow tests
python -m pytest --durations=10

# Run only fast tests during development
python -m pytest -m "not slow"
```

## Troubleshooting

### Common Issues

#### Coverage Not Working
```bash
# Ensure pytest-cov is installed
pip install pytest-cov

# Check coverage configuration
python -m pytest --cov=hydra_logger --cov-report=term
```

#### HTML Report Not Generated
```bash
# Check if htmlcov directory exists
ls -la htmlcov/

# Regenerate HTML report
python -m pytest --cov=hydra_logger --cov-report=html --cov-report=term
```

#### Tests Failing
```bash
# Run with verbose output
python -m pytest -v

# Run with full traceback
python -m pytest --tb=long

# Run specific failing test
python -m pytest tests/test_specific.py::test_function -v
```

### Debugging Tests

```python
import pytest
import logging

# Enable debug logging during tests
logging.basicConfig(level=logging.DEBUG)

def test_with_debug():
    """Test with debug information."""
    logger = logging.getLogger(__name__)
    logger.debug("Debug information")
    
    # Your test code here
    assert True
```

## Summary

- **Run tests**: `python -m pytest`
- **Generate coverage**: `python -m pytest --cov=hydra_logger --cov-report=html`
- **View HTML report**: Open `htmlcov/index.html` in browser
- **Don't commit htmlcov**: It's in `.gitignore` for good reason
- **Aim for 90%+ coverage**: Focus on critical paths and error handling
- **Use CI/CD**: Automated testing and coverage reporting

The `htmlcov` directory is a valuable tool for understanding test coverage but should never be committed to version control. Generate it locally when you need to analyze coverage gaps or share coverage reports with your team. 