# Testing Guide

This document provides comprehensive information about testing Hydra-Logger, including test structure, coverage requirements, and how to run tests effectively.

## Table of Contents

- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Format-Specific Tests](#format-specific-tests)
- [Integration Tests](#integration-tests)
- [Performance Tests](#performance-tests)
- [Best Practices](#best-practices)

## Test Structure

The test suite is organized into several modules, each focusing on specific aspects of the Hydra-Logger functionality:

```
tests/
├── test_config.py           # Configuration model tests
├── test_logger.py           # Core logger functionality tests
├── test_compatibility.py    # Backward compatibility tests
└── test_integration.py      # Integration and real-world tests
```

### Test Categories

#### **Unit Tests** (`test_config.py`, `test_logger.py`)
- Configuration model validation
- Logger initialization and configuration
- Individual method functionality
- Error handling and edge cases

#### **Compatibility Tests** (`test_compatibility.py`)
- Backward compatibility with `setup_logging()`
- Migration function testing
- Legacy interface validation

#### **Integration Tests** (`test_integration.py`)
- End-to-end logging scenarios
- Multi-layer configuration testing
- Real-world usage patterns
- File system operations

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with short traceback
pytest --tb=short

# Run specific test file
pytest tests/test_logger.py

# Run specific test class
pytest tests/test_logger.py::TestHydraLogger

# Run specific test method
pytest tests/test_logger.py::TestHydraLogger::test_basic_logging
```

### Coverage Analysis

```bash
# Run tests with coverage report
pytest --cov=hydra_logger --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=hydra_logger --cov-report=html

# Generate XML coverage report for CI
pytest --cov=hydra_logger --cov-report=xml

# Run with coverage and fail if below threshold
pytest --cov=hydra_logger --cov-fail-under=97
```

### Test Filtering

```bash
# Run only fast tests (exclude slow integration tests)
pytest -m "not slow"

# Run only integration tests
pytest -m "integration"

# Run tests matching a pattern
pytest -k "json"

# Run tests excluding a pattern
pytest -k "not file"
```

## Test Coverage

### Current Coverage Status

- **Total Tests**: 146 tests
- **Coverage**: 97%
- **Coverage Target**: 97% minimum

### Coverage Breakdown

#### **Core Modules**
- `hydra_logger/__init__.py`: 100%
- `hydra_logger/config.py`: 97%
- `hydra_logger/logger.py`: 97%
- `hydra_logger/compatibility.py`: 100%

#### **Coverage Gaps**
The remaining 3% consists of:
- Import fallback scenarios (tomllib/tomli)
- Rare error conditions
- Edge cases in format handling

### Coverage Requirements

#### **Minimum Requirements**
- **97% overall coverage** for all code
- **100% coverage** for critical paths
- **95% coverage** for error handling code

#### **Coverage Exclusions**
- Import statements for optional dependencies
- Debug/development code paths
- Platform-specific code

## Format-Specific Tests

### JSON Format Tests

```python
def test_structured_json_formatter(self, temp_dir):
    """Test the structured JSON formatter output."""
    config = LoggingConfig(
        layers={
            "STRUCTURED_JSON": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path=os.path.join(temp_dir, "structured.json"),
                        format="json"
                    ),
                ],
            )
        }
    )

    logger = HydraLogger(config)
    logger.info("STRUCTURED_JSON", "Test structured JSON")

    # Verify file was created
    filepath = os.path.join(temp_dir, "structured.json")
    assert os.path.exists(filepath)

    with open(filepath, "r") as f:
        content = f.read().strip()
        log_entry = json.loads(content)
        
        # Verify all required fields are present
        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert "logger" in log_entry
        assert "message" in log_entry
        assert "filename" in log_entry
        assert "lineno" in log_entry
        
        # Verify data types and values
        assert log_entry["level"] == "INFO"
        assert log_entry["message"] == "Test structured JSON"
        assert log_entry["logger"] == "STRUCTURED_JSON"
        assert log_entry["lineno"] > 0
```

### JSON Lines Format Tests

```python
def test_json_lines_format(self, temp_dir):
    """Test that JSON format produces valid JSON Lines (one JSON object per line)."""
    config = LoggingConfig(
        layers={
            "JSON_LINES": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path=os.path.join(temp_dir, "json_lines.json"),
                        format="json"
                    ),
                ],
            )
        }
    )

    logger = HydraLogger(config)
    
    # Log multiple messages
    logger.info("JSON_LINES", "First message")
    logger.warning("JSON_LINES", "Second message")
    logger.error("JSON_LINES", "Third message")

    # Verify file was created
    filepath = os.path.join(temp_dir, "json_lines.json")
    assert os.path.exists(filepath)

    with open(filepath, "r") as f:
        lines = f.readlines()
        
        # Verify we have exactly 3 lines
        assert len(lines) == 3
        
        # Verify each line is valid JSON
        for i, line in enumerate(lines):
            log_entry = json.loads(line.strip())
            assert "message" in log_entry
            assert "level" in log_entry
            assert "timestamp" in log_entry
```

### CSV Format Tests

```python
def test_csv_format(self, temp_dir):
    """Test CSV format output."""
    config = LoggingConfig(
        layers={
            "CSV_TEST": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path=os.path.join(temp_dir, "test.csv"),
                        format="csv"
                    ),
                ],
            )
        }
    )

    logger = HydraLogger(config)
    logger.info("CSV_TEST", "Test CSV message")

    filepath = os.path.join(temp_dir, "test.csv")
    assert os.path.exists(filepath)

    with open(filepath, "r") as f:
        lines = f.readlines()
        
        # Verify header
        assert "timestamp,level,logger,message,filename,lineno" in lines[0]
        
        # Verify data line
        data_line = lines[1].strip()
        assert "INFO" in data_line
        assert "CSV_TEST" in data_line
        assert "Test CSV message" in data_line
```

### Syslog Format Tests

```python
def test_syslog_format(self, temp_dir):
    """Test syslog format output."""
    config = LoggingConfig(
        layers={
            "SYSLOG_TEST": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path=os.path.join(temp_dir, "test.log"),
                        format="syslog"
                    ),
                ],
            )
        }
    )

    logger = HydraLogger(config)
    logger.info("SYSLOG_TEST", "Test syslog message")

    filepath = os.path.join(temp_dir, "test.log")
    assert os.path.exists(filepath)

    with open(filepath, "r") as f:
        content = f.read().strip()
        
        # Verify syslog format
        assert content.startswith("<")
        assert "SYSLOG_TEST" in content
        assert "Test syslog message" in content
```

### GELF Format Tests

```python
def test_gelf_format(self, temp_dir):
    """Test GELF format output."""
    config = LoggingConfig(
        layers={
            "GELF_TEST": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path=os.path.join(temp_dir, "test.gelf"),
                        format="gelf"
                    ),
                ],
            )
        }
    )

    logger = HydraLogger(config)
    logger.info("GELF_TEST", "Test GELF message")

    filepath = os.path.join(temp_dir, "test.gelf")
    assert os.path.exists(filepath)

    with open(filepath, "r") as f:
        content = f.read().strip()
        log_entry = json.loads(content)
        
        # Verify GELF format
        assert log_entry["version"] == "1.1"
        assert "host" in log_entry
        assert log_entry["short_message"] == "Test GELF message"
        assert log_entry["level"] == 6  # INFO level
        assert log_entry["_logger"] == "GELF_TEST"
```

## Integration Tests

### Multi-Layer Configuration Tests

```python
def test_multi_layer_configuration(self, temp_dir):
    """Test complex multi-layer configuration."""
    config = LoggingConfig(
        layers={
            "APP": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(type="file", path=os.path.join(temp_dir, "app.log"), format="plain-text"),
                    LogDestination(type="console", format="json")
                ]
            ),
            "API": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(type="file", path=os.path.join(temp_dir, "api.json"), format="json")
                ]
            ),
            "ERRORS": LogLayer(
                level="ERROR",
                destinations=[
                    LogDestination(type="file", path=os.path.join(temp_dir, "errors.log"), format="plain-text")
                ]
            )
        }
    )

    logger = HydraLogger(config)
    
    # Test all layers
    logger.info("APP", "Application started")
    logger.debug("API", "API request received")
    logger.error("ERRORS", "Database error occurred")
    
    # Verify all files were created
    assert os.path.exists(os.path.join(temp_dir, "app.log"))
    assert os.path.exists(os.path.join(temp_dir, "api.json"))
    assert os.path.exists(os.path.join(temp_dir, "errors.log"))
```

### Configuration File Tests

```python
def test_yaml_configuration(self, temp_dir):
    """Test loading configuration from YAML file."""
    config_content = """
layers:
  TEST:
    level: INFO
    destinations:
      - type: file
        path: test.log
        format: json
    """
    
    config_file = os.path.join(temp_dir, "test.yaml")
    with open(config_file, "w") as f:
        f.write(config_content)
    
    logger = HydraLogger.from_config(config_file)
    logger.info("TEST", "Test message")
    
    # Verify log file was created
    log_file = os.path.join(temp_dir, "test.log")
    assert os.path.exists(log_file)
```

### Error Handling Tests

```python
def test_invalid_configuration(self):
    """Test handling of invalid configuration."""
    with pytest.raises(ValidationError):
        LoggingConfig(
            layers={
                "INVALID": LogLayer(
                    level="INVALID_LEVEL",  # Invalid log level
                    destinations=[]
                )
            }
        )

def test_missing_file_path(self):
    """Test handling of missing file path for file destination."""
    with pytest.raises(ValidationError):
        LogDestination(type="file", format="json")  # Missing path

def test_invalid_format(self):
    """Test handling of invalid log format."""
    with pytest.raises(ValueError):
        LogDestination(type="file", path="test.log", format="invalid_format")
```

## Performance Tests

### Concurrent Logging Tests

```python
def test_concurrent_logging(self, temp_dir):
    """Test thread-safe concurrent logging."""
    import threading
    import time
    
    config = LoggingConfig(
        layers={
            "CONCURRENT": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path=os.path.join(temp_dir, "concurrent.log"),
                        format="plain-text"
                    )
                ]
            )
        }
    )
    
    logger = HydraLogger(config)
    
    def log_messages(thread_id):
        for i in range(100):
            logger.info("CONCURRENT", f"Thread {thread_id} message {i}")
            time.sleep(0.001)
    
    # Start multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=log_messages, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Verify all messages were logged
    log_file = os.path.join(temp_dir, "concurrent.log")
    with open(log_file, "r") as f:
        lines = f.readlines()
        assert len(lines) == 500  # 5 threads * 100 messages each
```

### File Rotation Tests

```python
def test_file_rotation(self, temp_dir):
    """Test file rotation functionality."""
    config = LoggingConfig(
        layers={
            "ROTATION": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path=os.path.join(temp_dir, "rotation.log"),
                        max_size="1KB",
                        backup_count=3,
                        format="plain-text"
                    )
                ]
            )
        }
    )
    
    logger = HydraLogger(config)
    
    # Generate enough logs to trigger rotation
    large_message = "X" * 100  # 100 character message
    for i in range(50):
        logger.info("ROTATION", f"Message {i}: {large_message}")
    
    # Verify rotation files were created
    base_path = os.path.join(temp_dir, "rotation.log")
    assert os.path.exists(base_path)
    
    # Check for backup files
    backup_files = [f for f in os.listdir(temp_dir) if f.startswith("rotation.log.")]
    assert len(backup_files) > 0
```

## Best Practices

### Test Organization

1. **Use descriptive test names** that clearly indicate what is being tested
2. **Group related tests** in test classes
3. **Use fixtures** for common setup and teardown
4. **Keep tests independent** - each test should be able to run in isolation

### Test Data Management

1. **Use temporary directories** for file-based tests
2. **Clean up test files** after each test
3. **Use unique file names** to avoid conflicts
4. **Mock external dependencies** when appropriate

### Coverage Strategy

1. **Test all public methods** and their variations
2. **Test error conditions** and edge cases
3. **Test configuration validation** thoroughly
4. **Test format-specific functionality** for each supported format

### Performance Considerations

1. **Use appropriate timeouts** for performance tests
2. **Test with realistic data sizes**
3. **Monitor memory usage** during concurrent tests
4. **Test file rotation** with various file sizes

### Continuous Integration

1. **Run tests on multiple Python versions**
2. **Include coverage reporting** in CI pipeline
3. **Fail builds** if coverage drops below threshold
4. **Run format-specific tests** for all supported formats

## Running Tests in CI/CD

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
    
    - name: Run tests with coverage
      run: |
        pytest --cov=hydra_logger --cov-report=xml --cov-fail-under=97
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml
```

This comprehensive testing approach ensures that Hydra-Logger is robust, reliable, and maintains high quality across all supported features and formats. 