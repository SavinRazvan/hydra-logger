# 🧪 Hydra-Logger Test Procedures Manual

## 📋 Overview

This document defines the **exact procedures** for running, managing, and maintaining tests in the Hydra-Logger project. Following these procedures ensures **correct and safe** test execution.

---

## 🎯 Test Categories & Responsibilities

### **1. Unit Tests** (`test_*.py` in `tests/unit/`)
- **Purpose**: Test individual components in isolation
- **Scope**: Single classes, methods, functions
- **Dependencies**: None (must run independently)
- **Timeout**: 60 seconds
- **Parallel**: ✅ Yes
- **Priority**: 1 (highest)

### **2. Integration Tests** (`*_test.py` in `tests/integration/`)
- **Purpose**: Test component interactions and workflows
- **Scope**: Multiple components working together
- **Dependencies**: Unit tests must pass first
- **Timeout**: 120 seconds
- **Parallel**: ✅ Yes
- **Priority**: 2

### **3. Performance Tests** (`test_performance_*.py` in `tests/performance/`)
- **Purpose**: Measure and validate performance metrics
- **Scope**: Speed, memory usage, throughput
- **Dependencies**: Unit + Validation tests must pass first
- **Timeout**: 300 seconds
- **Parallel**: ❌ No (sequential for accurate timing)
- **Priority**: 2

### **4. Validation Tests** (`test_validation_*.py` in `tests/validation/`)
- **Purpose**: Validate correctness and safeguard compliance
- **Scope**: All loggers, handlers, formatters
- **Dependencies**: Unit tests must pass first
- **Timeout**: 180 seconds
- **Parallel**: ✅ Yes
- **Priority**: 1 (highest)

### **5. Regression Tests** (`test_regression_*.py` in `tests/regression/`)
- **Purpose**: Prevent bugs from reoccurring
- **Scope**: Previously fixed issues
- **Dependencies**: Unit + Integration tests must pass first
- **Timeout**: 240 seconds
- **Parallel**: ✅ Yes
- **Priority**: 3

### **6. Stress Tests** (`test_stress_*.py` in `tests/stress/`)
- **Purpose**: Test under high load conditions
- **Scope**: System behavior under extreme conditions
- **Dependencies**: Unit + Performance tests must pass first
- **Timeout**: 600 seconds
- **Parallel**: ❌ No (sequential to avoid resource conflicts)
- **Priority**: 4

### **7. Security Tests** (`test_security_*.py` in `tests/security/`)
- **Purpose**: Validate security features and vulnerabilities
- **Scope**: PII detection, sanitization, encryption
- **Dependencies**: Unit + Validation tests must pass first
- **Timeout**: 180 seconds
- **Parallel**: ✅ Yes
- **Priority**: 3

### **8. Compatibility Tests** (`test_compatibility_*.py` in `tests/compatibility/`)
- **Purpose**: Test across different environments and versions
- **Scope**: Python versions, OS compatibility, dependencies
- **Dependencies**: Unit + Integration tests must pass first
- **Timeout**: 300 seconds
- **Parallel**: ✅ Yes
- **Priority**: 5 (lowest)

---

## 🚀 Test Execution Procedures

### **Phase 1: Pre-Test Setup**

#### **1.1 Environment Preparation**
```bash
# 1. Activate virtual environment
source .hydra_env/bin/activate

# 2. Verify Python version
python3 --version  # Should be 3.8+

# 3. Install dependencies
pip install -r requirements.txt

# 4. Clean previous test artifacts
python3 manage_tests.py cleanup --execute
```

#### **1.2 Test Discovery**
```bash
# 1. Discover all tests
python3 run_tests.py --discover

# 2. Verify test count and categories
python3 manage_tests.py stats

# 3. Check for missing dependencies
python3 run_tests.py --category unit --file test_sync_validation.py
```

#### **1.3 Safety Checks**
```bash
# 1. Run safeguards validation
python3 test_safeguards.py

# 2. Verify no critical issues
echo $?  # Should be 0

# 3. Check system resources
free -h  # Ensure sufficient memory
df -h    # Ensure sufficient disk space
```

### **Phase 2: Test Execution**

#### **2.1 Priority-Based Execution**

**Step 1: Critical Tests (Priority 1)**
```bash
# Run unit tests first
python3 run_tests.py --category unit --parallel --workers 8

# Verify all unit tests pass
if [ $? -ne 0 ]; then
    echo "❌ Unit tests failed - STOP execution"
    exit 1
fi

# Run validation tests
python3 run_tests.py --category validation --parallel --workers 4

# Verify all validation tests pass
if [ $? -ne 0 ]; then
    echo "❌ Validation tests failed - STOP execution"
    exit 1
fi
```

**Step 2: Integration Tests (Priority 2)**
```bash
# Run integration tests
python3 run_tests.py --category integration --parallel --workers 6

# Verify integration tests pass
if [ $? -ne 0 ]; then
    echo "❌ Integration tests failed - STOP execution"
    exit 1
fi

# Run performance tests (sequential)
python3 run_tests.py --category performance --sequential

# Verify performance tests pass
if [ $? -ne 0 ]; then
    echo "❌ Performance tests failed - STOP execution"
    exit 1
fi
```

**Step 3: Secondary Tests (Priority 3-5)**
```bash
# Run regression tests
python3 run_tests.py --category regression --parallel --workers 4

# Run security tests
python3 run_tests.py --category security --parallel --workers 4

# Run compatibility tests
python3 run_tests.py --category compatibility --parallel --workers 4
```

**Step 4: Stress Tests (Priority 4)**
```bash
# Run stress tests (sequential only)
python3 run_tests.py --category stress --sequential

# Monitor system resources during execution
```

#### **2.2 Full Test Suite Execution**
```bash
# Run all tests in correct order
python3 run_tests.py --parallel --workers 8 --timeout 300 --output full_test_results.json

# Generate comprehensive report
python3 manage_tests.py stats
```

### **Phase 3: Post-Test Analysis**

#### **3.1 Result Validation**
```bash
# 1. Check exit code
echo "Test execution exit code: $?"

# 2. Verify result file exists
ls -la test_results.json

# 3. Check for critical failures
python3 -c "
import json
with open('test_results.json', 'r') as f:
    data = json.load(f)
    failed = [r for r in data['results'] if r['status'] in ['FAIL', 'ERROR']]
    if failed:
        print(f'❌ {len(failed)} tests failed:')
        for f in failed:
            print(f'  - {f[\"test_file\"]}: {f[\"status\"]}')
        exit(1)
    else:
        print('✅ All tests passed')
"
```

#### **3.2 Performance Analysis**
```bash
# 1. Extract performance metrics
python3 -c "
import json
with open('test_results.json', 'r') as f:
    data = json.load(f)
    perf_tests = [r for r in data['results'] if r.get('performance_metrics')]
    if perf_tests:
        print('📊 Performance Metrics:')
        for test in perf_tests:
            metrics = test['performance_metrics']
            if 'messages_per_second' in metrics:
                print(f'  {test[\"test_file\"]}: {metrics[\"messages_per_second\"]:,.0f} msg/s')
"
```

#### **3.3 Cleanup**
```bash
# 1. Clean up test artifacts
python3 manage_tests.py cleanup --execute

# 2. Archive test results
mkdir -p test_archives/$(date +%Y%m%d_%H%M%S)
mv test_results.json test_archives/$(date +%Y%m%d_%H%M%S)/

# 3. Reset environment
deactivate
```

---

## 🛡️ Safety Procedures

### **Critical Safety Rules**

#### **Rule 1: Never Skip Unit Tests**
- Unit tests MUST pass before any other tests
- If unit tests fail, STOP all execution
- Fix unit test failures before proceeding

#### **Rule 2: Validation Tests Are Mandatory**
- Validation tests MUST pass before performance tests
- Safeguard tests MUST pass before any deployment
- If validation fails, investigate and fix immediately

#### **Rule 3: Performance Tests Are Sequential Only**
- Never run performance tests in parallel
- Performance tests need accurate timing
- Resource conflicts will corrupt results

#### **Rule 4: Resource Monitoring**
- Monitor memory usage during stress tests
- Stop execution if memory usage exceeds 80%
- Monitor disk space for log files

#### **Rule 5: Test Isolation**
- Each test must be independent
- No test should depend on another test's output
- Clean up after each test category

### **Error Handling Procedures**

#### **Test Failure Response**
```bash
# 1. Identify failed test
python3 run_tests.py --file <failed_test.py>

# 2. Check error message
cat test_output.log

# 3. Run with debug output
python3 -u <failed_test.py> 2>&1 | tee debug_output.log

# 4. Fix the issue
# Edit the test file or the code being tested

# 5. Re-run the specific test
python3 run_tests.py --file <failed_test.py>

# 6. Re-run the category
python3 run_tests.py --category <category>
```

#### **System Resource Issues**
```bash
# 1. Check system resources
free -h
df -h
ps aux | grep python

# 2. Kill hanging processes
pkill -f "python.*test"

# 3. Reduce parallel workers
python3 run_tests.py --workers 2

# 4. Run tests sequentially
python3 run_tests.py --sequential
```

---

## 📊 Test Monitoring Procedures

### **Real-Time Monitoring**

#### **During Test Execution**
```bash
# Terminal 1: Run tests
python3 run_tests.py --parallel --workers 8

# Terminal 2: Monitor resources
watch -n 5 'free -h && echo "---" && ps aux | grep python | head -10'

# Terminal 3: Monitor test progress
tail -f test_output.log
```

#### **Performance Monitoring**
```bash
# Monitor specific performance tests
python3 run_tests.py --category performance --sequential --summary

# Check performance metrics
python3 -c "
import json
with open('test_results.json', 'r') as f:
    data = json.load(f)
    for test in data['results']:
        if test.get('performance_metrics'):
            print(f'{test[\"test_file\"]}: {test[\"performance_metrics\"]}')
"
```

### **Test Result Analysis**

#### **Success Criteria**
- ✅ All unit tests pass (100%)
- ✅ All validation tests pass (100%)
- ✅ All integration tests pass (100%)
- ✅ Performance tests meet thresholds
- ✅ No memory leaks detected
- ✅ No resource exhaustion

#### **Performance Thresholds**
- **Minimum Performance**: 10,000 msg/s
- **Object Pool Hit Rate**: ≥ 80%
- **Memory Usage**: ≤ 50MB per test
- **Test Duration**: ≤ 300 seconds per test

---

## 🔧 Maintenance Procedures

### **Daily Maintenance**
```bash
# 1. Run critical tests
python3 run_tests.py --category unit
python3 run_tests.py --category validation

# 2. Check test statistics
python3 manage_tests.py stats

# 3. Clean up artifacts
python3 manage_tests.py cleanup --execute
```

### **Weekly Maintenance**
```bash
# 1. Run full test suite
python3 run_tests.py --parallel --workers 8

# 2. Generate comprehensive report
python3 manage_tests.py stats > weekly_report.txt

# 3. Archive old test results
find test_archives -name "*.json" -mtime +7 -delete
```

### **Monthly Maintenance**
```bash
# 1. Review test performance trends
python3 -c "
import json, glob
archives = glob.glob('test_archives/*/test_results.json')
# Analyze performance trends over time
"

# 2. Update test configurations
# Review and update test_config.yaml

# 3. Clean up old test files
find tests/ -name "*.pyc" -delete
find tests/ -name "__pycache__" -type d -exec rm -rf {} +
```

---

## 🚨 Emergency Procedures

### **Test System Failure**
```bash
# 1. Stop all test processes
pkill -f "python.*test"

# 2. Check system resources
free -h
df -h

# 3. Restart with minimal configuration
python3 run_tests.py --sequential --workers 1

# 4. If still failing, run individual tests
python3 run_tests.py --file test_sync_validation.py
```

### **Performance Degradation**
```bash
# 1. Identify slow tests
python3 -c "
import json
with open('test_results.json', 'r') as f:
    data = json.load(f)
    slow_tests = [r for r in data['results'] if r['execution_time'] > 60]
    for test in slow_tests:
        print(f'{test[\"test_file\"]}: {test[\"execution_time\"]:.2f}s')
"

# 2. Run slow tests individually
python3 run_tests.py --file <slow_test.py>

# 3. Optimize or fix slow tests
```

### **Memory Issues**
```bash
# 1. Check memory usage
free -h
ps aux --sort=-%mem | head -10

# 2. Kill memory-intensive processes
pkill -f "python.*test"

# 3. Run tests with reduced workers
python3 run_tests.py --workers 2

# 4. Run tests sequentially
python3 run_tests.py --sequential
```

---

## 📋 Checklist for Test Execution

### **Pre-Test Checklist**
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] System resources sufficient
- [ ] Previous test artifacts cleaned
- [ ] Test discovery completed
- [ ] Safeguards validation passed

### **During Test Checklist**
- [ ] Unit tests running and passing
- [ ] Validation tests running and passing
- [ ] Integration tests running and passing
- [ ] Performance tests running sequentially
- [ ] System resources monitored
- [ ] No hanging processes

### **Post-Test Checklist**
- [ ] All tests completed successfully
- [ ] Test results saved
- [ ] Performance metrics extracted
- [ ] Test artifacts cleaned up
- [ ] Results archived
- [ ] Environment reset

---

## 🎯 Success Metrics

### **Test Execution Success**
- **Unit Tests**: 100% pass rate
- **Validation Tests**: 100% pass rate
- **Integration Tests**: 100% pass rate
- **Performance Tests**: Meet thresholds
- **Overall Success Rate**: ≥ 95%

### **Performance Success**
- **Sync Loggers**: ≥ 40,000 msg/s
- **Async Loggers**: ≥ 140,000 msg/s
- **Object Pool Hit Rate**: ≥ 80%
- **Memory Usage**: ≤ 50MB per test
- **Test Duration**: ≤ 300 seconds per test

### **Quality Success**
- **No Critical Issues**: 0 critical failures
- **No Memory Leaks**: Stable memory usage
- **No Resource Exhaustion**: System resources stable
- **No Hanging Tests**: All tests complete within timeout

---

## 📞 Support and Escalation

### **Level 1: Self-Service**
- Check this procedures manual
- Run individual test files
- Check system resources
- Clean up test artifacts

### **Level 2: Investigation**
- Analyze test output logs
- Check test dependencies
- Review test configurations
- Monitor system performance

### **Level 3: Escalation**
- Contact development team
- Provide test logs and error messages
- Include system resource information
- Document steps taken

---

## 📚 Quick Reference

### **Essential Commands**
```bash
# Discover tests
python3 run_tests.py --discover

# Run all tests
python3 run_tests.py --parallel

# Run specific category
python3 run_tests.py --category unit

# Run specific test
python3 run_tests.py --file test_sync_validation.py

# Show statistics
python3 manage_tests.py stats

# Clean up
python3 manage_tests.py cleanup --execute
```

### **Emergency Commands**
```bash
# Stop all tests
pkill -f "python.*test"

# Run minimal tests
python3 run_tests.py --sequential --workers 1

# Check resources
free -h && df -h
```

---

**🎯 Remember: Following these procedures ensures correct and safe test execution. When in doubt, refer to this manual and follow the safety rules.**
