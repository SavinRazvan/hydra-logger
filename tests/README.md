# 🧪 Hydra-Logger Test Suite

## 📁 Directory Structure

```
tests/
├── README.md                    # This file
├── docs/                        # Test documentation
│   ├── tests_procedures.md      # Detailed test procedures
│   └── TEST_MANAGEMENT_GUIDE.md # Test management guide
├── unit/                        # Unit tests for individual components
├── integration/                 # Integration tests for component interactions
├── performance/                 # Performance and benchmark tests
├── validation/                  # Validation and safeguard tests
├── regression/                  # Regression tests to prevent bugs
├── stress/                      # Stress tests for high load scenarios
├── security/                    # Security and vulnerability tests
├── compatibility/               # Compatibility tests across environments
├── coverage/                    # Test coverage reports and data
├── fixtures/                    # Test fixtures and sample data
└── utils/                       # Test utilities and helpers
```

## 🎯 Test Categories

### **Unit Tests** (`tests/unit/`)
- Test individual components in isolation
- Fast execution (< 60 seconds)
- No external dependencies
- 100% pass rate required

### **Integration Tests** (`tests/integration/`)
- Test component interactions
- Workflow validation
- Medium execution time (< 120 seconds)
- Requires unit tests to pass first

### **Performance Tests** (`tests/performance/`)
- Measure speed and throughput
- Memory usage validation
- Sequential execution only
- Performance thresholds must be met

### **Validation Tests** (`tests/validation/`)
- Safeguard compliance
- Correctness validation
- Critical for deployment
- Must pass before performance tests

### **Regression Tests** (`tests/regression/`)
- Prevent previously fixed bugs
- Historical issue validation
- Medium priority
- Requires unit + integration tests

### **Stress Tests** (`tests/stress/`)
- High load scenarios
- Resource exhaustion testing
- Sequential execution only
- Long execution time (< 600 seconds)

### **Security Tests** (`tests/security/`)
- PII detection validation
- Sanitization testing
- Vulnerability assessment
- Medium priority

### **Compatibility Tests** (`tests/compatibility/`)
- Cross-platform testing
- Python version compatibility
- Dependency validation
- Lowest priority

## 🚀 Quick Start

### **Run All Tests**
```bash
# From project root (recommended)
python3 run_tests.py

# Or directly from tests directory
python3 tests/run_tests.py
```

### **Run Specific Category**
```bash
python3 run_tests.py --category unit
python3 run_tests.py --category performance
```

### **Run Specific Test**
```bash
python3 run_tests.py --file tests/unit/test_loggers.py
```

### **Test Management**
```bash
# From project root (recommended)
python3 manage_tests.py stats
python3 manage_tests.py list
python3 manage_tests.py create my_test unit

# Or directly from tests directory
python3 tests/manage_tests.py stats
```

## 📊 Test Coverage

### **Coverage Requirements**
- **Unit Tests**: 100% coverage
- **Integration Tests**: 90% coverage
- **Performance Tests**: 80% coverage
- **Overall Coverage**: ≥ 95%

### **Coverage Reports**
```bash
# Generate coverage report
python3 -m pytest --cov=hydra_logger --cov-report=html tests/

# View coverage report
open tests/coverage/htmlcov/index.html
```

## 🛡️ Safety Rules

1. **Unit tests MUST pass first**
2. **Validation tests are mandatory**
3. **Performance tests are sequential only**
4. **Monitor system resources**
5. **Clean up after each test**

## 📚 Documentation

- **Test Procedures**: `tests/docs/tests_procedures.md`
- **Management Guide**: `tests/docs/TEST_MANAGEMENT_GUIDE.md`
- **Coverage Reports**: `tests/coverage/`

## 🔧 Maintenance

### **Daily**
- Run unit and validation tests
- Check test statistics
- Clean up artifacts

### **Weekly**
- Run full test suite
- Generate coverage reports
- Review performance trends

### **Monthly**
- Update test configurations
- Clean up old test files
- Review test coverage

## 🚨 Emergency Procedures

### **Test Failures**
1. Check individual test: `python3 run_tests.py --file <test.py>`
2. Check category: `python3 run_tests.py --category <category>`
3. Check system resources: `free -h && df -h`
4. Run with reduced workers: `python3 run_tests.py --workers 2`

### **Performance Issues**
1. Run tests sequentially: `python3 run_tests.py --sequential`
2. Reduce worker count: `python3 run_tests.py --workers 1`
3. Check memory usage: `ps aux --sort=-%mem`

## 📈 Success Metrics

- **Unit Tests**: 100% pass rate
- **Validation Tests**: 100% pass rate
- **Integration Tests**: 100% pass rate
- **Performance Tests**: Meet thresholds
- **Overall Success Rate**: ≥ 95%
