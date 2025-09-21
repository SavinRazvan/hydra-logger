# 🧪 Hydra-Logger Test Management Guide

## Overview

This guide explains how to manage large numbers of test files (30+) efficiently using the Hydra-Logger test management system.

## 🚀 Quick Start

### Basic Commands

```bash
# Discover all tests
python3 run_tests.py --discover

# Run all tests
python3 run_tests.py

# Run tests in parallel (default)
python3 run_tests.py --parallel

# Run specific category
python3 run_tests.py --category performance

# Run specific test file
python3 run_tests.py --file test_sync_validation.py

# Show test statistics
python3 manage_tests.py stats
```

## 📁 Test Organization

### Test Categories

The system automatically categorizes tests based on filename and content:

- **`unit`**: Unit tests for individual components
- **`integration`**: Integration tests for component interactions  
- **`performance`**: Performance and benchmark tests
- **`validation`**: Validation and safeguard tests
- **`regression`**: Regression tests to prevent bugs
- **`stress`**: Stress tests for high load scenarios
- **`security`**: Security and vulnerability tests
- **`compatibility`**: Compatibility tests across environments

### File Naming Conventions

```
test_*.py              # Unit tests
*_test.py              # Integration tests
test_performance_*.py  # Performance tests
test_validation_*.py   # Validation tests
test_regression_*.py   # Regression tests
test_stress_*.py       # Stress tests
test_security_*.py     # Security tests
test_compatibility_*.py # Compatibility tests
```

## 🔧 Test Management Commands

### Discovery and Listing

```bash
# List all tests
python3 manage_tests.py list

# List tests by category
python3 manage_tests.py list --category unit

# Show test statistics
python3 manage_tests.py stats
```

### Creating New Tests

```bash
# Create unit test
python3 manage_tests.py create my_component_test unit

# Create performance test
python3 manage_tests.py create my_performance_test performance

# Create test in specific directory
python3 manage_tests.py create my_test unit --directory tests/custom
```

### Test Execution

```bash
# Run all tests
python3 run_tests.py

# Run tests in parallel (recommended for 30+ tests)
python3 run_tests.py --parallel

# Run tests sequentially
python3 run_tests.py --sequential

# Run specific category
python3 run_tests.py --category performance

# Run specific test
python3 run_tests.py --file test_sync_validation.py

# Run with custom worker count
python3 run_tests.py --workers 16

# Run with timeout
python3 run_tests.py --timeout 600
```

### Test Maintenance

```bash
# Clean up test files (dry run)
python3 manage_tests.py cleanup

# Actually clean up
python3 manage_tests.py cleanup --execute

# Save test results
python3 run_tests.py --output results.json
```

## ⚙️ Configuration

### Test Configuration (`test_config.yaml`)

```yaml
# Test discovery patterns
discovery:
  patterns:
    - "test_*.py"
    - "*_test.py"
    - "tests/**/test_*.py"

# Test categories
categories:
  unit:
    priority: 1
    timeout: 60
    parallel: true
  
  performance:
    priority: 2
    timeout: 300
    parallel: false  # Sequential for accurate timing

# Execution settings
execution:
  max_workers: 32
  parallel_by_default: true
```

## 📊 Performance Optimization

### For 30+ Test Files

1. **Use Parallel Execution**:
   ```bash
   python3 run_tests.py --parallel --workers 16
   ```

2. **Categorize Tests by Priority**:
   - Unit tests: Run first (fastest)
   - Validation tests: Run second
   - Performance tests: Run last (slowest)

3. **Optimize Test Timeouts**:
   - Unit tests: 60 seconds
   - Integration tests: 120 seconds
   - Performance tests: 300 seconds

4. **Use Test Dependencies**:
   - Run unit tests before integration tests
   - Run validation tests before performance tests

### Memory Management

```bash
# Run tests with memory monitoring
python3 run_tests.py --parallel --workers 8

# Clean up between test categories
python3 run_tests.py --category unit
python3 run_tests.py --category integration
python3 run_tests.py --category performance
```

## 🔍 Test Monitoring

### Real-time Monitoring

```bash
# Run with detailed output
python3 run_tests.py --summary

# Save results for analysis
python3 run_tests.py --output test_results.json

# Run specific tests with retry
python3 run_tests.py --category performance --retry 2
```

### Performance Metrics

The system automatically extracts:
- Messages per second (msg/s)
- Object pool hit rates
- Memory usage
- Execution times

## 🚨 Troubleshooting

### Common Issues

1. **Tests Running Slowly**:
   ```bash
   # Increase workers
   python3 run_tests.py --workers 32
   
   # Run categories separately
   python3 run_tests.py --category unit
   python3 run_tests.py --category integration
   ```

2. **Memory Issues**:
   ```bash
   # Reduce workers
   python3 run_tests.py --workers 4
   
   # Run sequentially
   python3 run_tests.py --sequential
   ```

3. **Test Timeouts**:
   ```bash
   # Increase timeout
   python3 run_tests.py --timeout 600
   
   # Run specific slow tests
   python3 run_tests.py --file test_performance.py
   ```

### Debug Mode

```bash
# Run with verbose output
python3 run_tests.py --summary

# Run single test for debugging
python3 run_tests.py --file test_sync_validation.py

# Check test discovery
python3 run_tests.py --discover
```

## 📈 Best Practices

### For Large Test Suites (30+ files)

1. **Organize by Category**:
   ```
   tests/
   ├── unit/
   │   ├── test_loggers.py
   │   ├── test_handlers.py
   │   └── test_formatters.py
   ├── integration/
   │   ├── test_workflows.py
   │   └── test_async_sync.py
   ├── performance/
   │   ├── test_benchmarks.py
   │   └── test_stress.py
   └── validation/
       ├── test_safeguards.py
       └── test_validation.py
   ```

2. **Use Test Dependencies**:
   - Unit tests must pass before integration tests
   - Validation tests must pass before performance tests

3. **Optimize Test Execution**:
   - Run fast tests first
   - Use parallel execution for independent tests
   - Run performance tests sequentially

4. **Monitor Performance**:
   - Track test execution times
   - Monitor memory usage
   - Set appropriate timeouts

### CI/CD Integration

```yaml
# GitHub Actions example
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Tests
        run: |
          python3 run_tests.py --parallel --workers 8
          python3 manage_tests.py cleanup --execute
```

## 🎯 Advanced Usage

### Custom Test Patterns

```yaml
# test_config.yaml
discovery:
  patterns:
    - "test_*.py"
    - "*_test.py"
    - "validation_*.py"
    - "safeguard_*.py"
    - "benchmark_*.py"
```

### Test Dependencies

```yaml
dependencies:
  prerequisites:
    unit: []
    integration: ["unit"]
    performance: ["unit", "validation"]
    regression: ["unit", "integration"]
```

### Performance Thresholds

```yaml
performance_thresholds:
  min_messages_per_second: 10000
  min_object_pool_hit_rate: 0.8
  max_memory_usage_mb: 50
  max_test_duration_seconds: 300
```

## 📚 Examples

### Running All Tests

```bash
# Basic run
python3 run_tests.py

# With custom settings
python3 run_tests.py --parallel --workers 16 --timeout 300 --output results.json
```

### Running Specific Tests

```bash
# Unit tests only
python3 run_tests.py --category unit

# Performance tests only
python3 run_tests.py --category performance

# Specific test file
python3 run_tests.py --file test_sync_validation.py
```

### Test Management

```bash
# Create new test
python3 manage_tests.py create my_test unit

# Show statistics
python3 manage_tests.py stats

# Clean up
python3 manage_tests.py cleanup --execute
```

## 🎉 Conclusion

The Hydra-Logger test management system provides:

- **Automatic Test Discovery**: Finds all test files automatically
- **Parallel Execution**: Runs tests efficiently with multiple workers
- **Category Management**: Organizes tests by type and priority
- **Performance Monitoring**: Tracks performance metrics automatically
- **Easy Maintenance**: Provides utilities for test management

This system scales from small test suites to large collections of 30+ test files, ensuring efficient execution and easy maintenance.
