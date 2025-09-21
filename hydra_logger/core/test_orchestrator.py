"""
Comprehensive Test Orchestration System for Hydra-Logger

This module provides a sophisticated test orchestration system designed to
efficiently manage and execute large numbers of test files with advanced
features like parallel execution, intelligent categorization, and comprehensive
result analysis.

ARCHITECTURE:
- TestOrchestrator: Main orchestration engine with test management
- TestResult: Individual test execution results with metadata
- TestSuite: Organized test collections with priority and dependencies
- Test Discovery: Automatic test file discovery and categorization

TEST MANAGEMENT FEATURES:
- Automatic test discovery and categorization
- Intelligent test file analysis
- Priority-based test execution
- Dependency management between test suites
- Parallel and sequential execution modes
- Performance monitoring and metrics

EXECUTION MODES:
- Parallel Execution: Run multiple tests simultaneously
- Sequential Execution: Run tests one at a time
- Hybrid Execution: Mix of parallel and sequential based on test type
- Priority-based Execution: Execute high-priority tests first

RESULT ANALYSIS:
- Comprehensive result aggregation
- Performance metrics extraction
- Failure analysis and categorization
- Test execution statistics
- Detailed reporting and summaries

USAGE EXAMPLES:

Basic Test Orchestration:
    from hydra_logger.core.test_orchestrator import TestOrchestrator
    
    orchestrator = TestOrchestrator("/path/to/project")
    
    # Discover and run all tests
    results = orchestrator.run_all_tests(parallel=True)
    print(f"Tests completed: {results['summary']['total_tests']}")

Test Discovery and Categorization:
    from hydra_logger.core.test_orchestrator import TestOrchestrator
    
    orchestrator = TestOrchestrator()
    discovered_tests = orchestrator.discover_tests()
    
    print("Discovered tests by category:")
    for category, tests in discovered_tests.items():
        print(f"{category}: {len(tests)} tests")

Parallel Test Execution:
    from hydra_logger.core.test_orchestrator import TestOrchestrator
    
    orchestrator = TestOrchestrator()
    test_files = ["test_logger.py", "test_handlers.py", "test_formatters.py"]
    
    results = orchestrator.run_tests_parallel(test_files, "unit")
    for result in results:
        print(f"{result.test_file}: {result.status} ({result.execution_time:.3f}s)")

Test Suite Management:
    from hydra_logger.core.test_orchestrator import TestOrchestrator, TestSuite
    
    orchestrator = TestOrchestrator()
    
    # Create custom test suite
    test_suite = TestSuite(
        name="integration_tests",
        test_files=["test_integration.py", "test_e2e.py"],
        category="integration",
        priority=1,
        dependencies=["unit_tests"]
    )
    
    orchestrator.create_test_suites({"integration_tests": test_suite})

Result Analysis and Reporting:
    from hydra_logger.core.test_orchestrator import TestOrchestrator
    
    orchestrator = TestOrchestrator()
    results = orchestrator.run_all_tests()
    
    # Generate and print summary
    summary = orchestrator.generate_summary(results['total_time'])
    orchestrator.print_summary(summary)
    
    # Save results to file
    orchestrator.save_results("test_results.json")
"""

import os
import sys
import time
import subprocess
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
import glob


@dataclass
class TestResult:
    """Result of a single test execution."""
    test_file: str
    test_category: str
    status: str  # 'PASS', 'FAIL', 'SKIP', 'ERROR'
    execution_time: float
    output: str
    error_message: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None


@dataclass
class TestSuite:
    """A collection of related tests."""
    name: str
    test_files: List[str]
    category: str
    priority: int  # 1 = highest, 5 = lowest
    dependencies: List[str] = None  # Other test suites this depends on


class TestOrchestrator:
    """
    Orchestrates execution of large numbers of test files.
    
    Features:
    - Automatic test discovery
    - Parallel execution
    - Test categorization
    - Result aggregation
    - Performance monitoring
    - Failure analysis
    - Test dependency management
    """
    
    def __init__(self, project_root: str = None):
        """Initialize test orchestrator."""
        self.project_root = project_root or os.getcwd()
        self.test_results: List[TestResult] = []
        self.test_suites: Dict[str, TestSuite] = {}
        self.max_workers = min(32, (os.cpu_count() or 1) * 4)
        self.parallel_execution = True
        
        # Test discovery patterns
        self.test_patterns = [
            "test_*.py",
            "*_test.py", 
            "test_*.py",
            "tests/**/test_*.py",
            "tests/**/*_test.py"
        ]
        
        # Test categories
        self.categories = {
            'unit': 'Unit tests for individual components',
            'integration': 'Integration tests for component interactions',
            'performance': 'Performance and benchmark tests',
            'validation': 'Validation and safeguard tests',
            'regression': 'Regression tests to prevent bugs',
            'stress': 'Stress tests for high load scenarios',
            'security': 'Security and vulnerability tests',
            'compatibility': 'Compatibility tests across environments'
        }
    
    def discover_tests(self) -> Dict[str, List[str]]:
        """Discover all test files in the project."""
        discovered_tests = {}
        
        for category in self.categories.keys():
            discovered_tests[category] = []
        
        # Search for test files
        for pattern in self.test_patterns:
            test_files = glob.glob(os.path.join(self.project_root, pattern), recursive=True)
            
            for test_file in test_files:
                # Categorize test based on filename and path
                category = self._categorize_test_file(test_file)
                if category in discovered_tests:
                    discovered_tests[category].append(test_file)
        
        # Remove duplicates and sort
        for category in discovered_tests:
            discovered_tests[category] = sorted(list(set(discovered_tests[category])))
        
        return discovered_tests
    
    def _categorize_test_file(self, test_file: str) -> str:
        """Categorize a test file based on its name and path."""
        filename = os.path.basename(test_file).lower()
        path_parts = test_file.lower().split(os.sep)
        
        # Check for explicit category indicators
        if 'unit' in filename or 'unit' in path_parts:
            return 'unit'
        elif 'integration' in filename or 'integration' in path_parts:
            return 'integration'
        elif 'performance' in filename or 'performance' in path_parts or 'benchmark' in filename:
            return 'performance'
        elif 'validation' in filename or 'validation' in path_parts or 'safeguard' in filename:
            return 'validation'
        elif 'regression' in filename or 'regression' in path_parts:
            return 'regression'
        elif 'stress' in filename or 'stress' in path_parts:
            return 'stress'
        elif 'security' in filename or 'security' in path_parts:
            return 'security'
        elif 'compatibility' in filename or 'compatibility' in path_parts:
            return 'compatibility'
        else:
            # Default categorization based on test content
            return self._analyze_test_content(test_file)
    
    def _analyze_test_content(self, test_file: str) -> str:
        """Analyze test file content to determine category."""
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read().lower()
            
            # Look for category indicators in content
            if 'performance' in content or 'msg/s' in content or 'benchmark' in content:
                return 'performance'
            elif 'validation' in content or 'safeguard' in content:
                return 'validation'
            elif 'integration' in content or 'workflow' in content:
                return 'integration'
            elif 'security' in content or 'vulnerability' in content:
                return 'security'
            else:
                return 'unit'  # Default to unit tests
        except Exception:
            return 'unit'
    
    def create_test_suites(self, discovered_tests: Dict[str, List[str]]) -> None:
        """Create test suites from discovered tests."""
        for category, test_files in discovered_tests.items():
            if test_files:
                # Determine priority based on category
                priority_map = {
                    'unit': 1,
                    'validation': 1,
                    'integration': 2,
                    'performance': 2,
                    'regression': 3,
                    'security': 3,
                    'stress': 4,
                    'compatibility': 5
                }
                
                priority = priority_map.get(category, 3)
                
                suite = TestSuite(
                    name=f"{category}_tests",
                    test_files=test_files,
                    category=category,
                    priority=priority
                )
                
                self.test_suites[suite.name] = suite
    
    def run_single_test(self, test_file: str, category: str) -> TestResult:
        """Run a single test file and return results."""
        start_time = time.time()
        
        try:
            # Run the test
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=self.project_root
            )
            
            execution_time = time.time() - start_time
            
            # Determine status
            if result.returncode == 0:
                status = 'PASS'
                error_message = None
            else:
                status = 'FAIL'
                error_message = result.stderr
            
            # Extract performance metrics if available
            performance_metrics = self._extract_performance_metrics(result.stdout)
            
            return TestResult(
                test_file=test_file,
                test_category=category,
                status=status,
                execution_time=execution_time,
                output=result.stdout,
                error_message=error_message,
                performance_metrics=performance_metrics
            )
            
        except subprocess.TimeoutExpired:
            return TestResult(
                test_file=test_file,
                test_category=category,
                status='ERROR',
                execution_time=time.time() - start_time,
                output='',
                error_message='Test timed out after 5 minutes'
            )
        except Exception as e:
            return TestResult(
                test_file=test_file,
                test_category=category,
                status='ERROR',
                execution_time=time.time() - start_time,
                output='',
                error_message=str(e)
            )
    
    def _extract_performance_metrics(self, output: str) -> Optional[Dict[str, Any]]:
        """Extract performance metrics from test output."""
        metrics = {}
        
        # Look for common performance indicators
        lines = output.split('\n')
        for line in lines:
            if 'msg/s' in line:
                try:
                    # Extract messages per second
                    parts = line.split()
                    for part in parts:
                        if 'msg/s' in part:
                            value = float(part.replace('msg/s', '').replace(',', ''))
                            metrics['messages_per_second'] = value
                            break
                except ValueError:
                    pass
            
            elif 'hit rate' in line.lower():
                try:
                    # Extract hit rate
                    parts = line.split()
                    for part in parts:
                        if '.' in part and '%' not in part:
                            value = float(part)
                            if 0 <= value <= 1:
                                metrics['hit_rate'] = value
                                break
                except ValueError:
                    pass
        
        return metrics if metrics else None
    
    def run_tests_parallel(self, test_files: List[str], category: str) -> List[TestResult]:
        """Run tests in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tests
            future_to_test = {
                executor.submit(self.run_single_test, test_file, category): test_file
                for test_file in test_files
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_test):
                test_file = future_to_test[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # Create error result
                    results.append(TestResult(
                        test_file=test_file,
                        test_category=category,
                        status='ERROR',
                        execution_time=0.0,
                        output='',
                        error_message=str(e)
                    ))
        
        return results
    
    def run_tests_sequential(self, test_files: List[str], category: str) -> List[TestResult]:
        """Run tests sequentially."""
        results = []
        
        for test_file in test_files:
            result = self.run_single_test(test_file, category)
            results.append(result)
        
        return results
    
    def run_all_tests(self, parallel: bool = True) -> Dict[str, Any]:
        """Run all discovered tests."""
        print("🔍 DISCOVERING TESTS...")
        discovered_tests = self.discover_tests()
        
        print(f"📊 FOUND {sum(len(tests) for tests in discovered_tests.values())} TESTS")
        for category, tests in discovered_tests.items():
            if tests:
                print(f"  • {category}: {len(tests)} tests")
        
        # Create test suites
        self.create_test_suites(discovered_tests)
        
        # Run tests by priority
        print(f"\n🚀 RUNNING TESTS ({'PARALLEL' if parallel else 'SEQUENTIAL'})...")
        print("=" * 60)
        
        all_results = []
        total_start_time = time.time()
        
        # Sort suites by priority
        sorted_suites = sorted(
            self.test_suites.values(),
            key=lambda x: x.priority
        )
        
        for suite in sorted_suites:
            print(f"\n📋 RUNNING {suite.name.upper()} ({len(suite.test_files)} tests)")
            print("-" * 40)
            
            if parallel and len(suite.test_files) > 1:
                suite_results = self.run_tests_parallel(suite.test_files, suite.category)
            else:
                suite_results = self.run_tests_sequential(suite.test_files, suite.category)
            
            all_results.extend(suite_results)
            
            # Print suite summary
            passed = len([r for r in suite_results if r.status == 'PASS'])
            failed = len([r for r in suite_results if r.status == 'FAIL'])
            errors = len([r for r in suite_results if r.status == 'ERROR'])
            
            print(f"  ✅ Passed: {passed}")
            print(f"  ❌ Failed: {failed}")
            print(f"  🚨 Errors: {errors}")
        
        total_time = time.time() - total_start_time
        
        # Store results
        self.test_results = all_results
        
        # Generate summary
        summary = self.generate_summary(total_time)
        
        return summary
    
    def generate_summary(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive test summary."""
        total_tests = len(self.test_results)
        passed = len([r for r in self.test_results if r.status == 'PASS'])
        failed = len([r for r in self.test_results if r.status == 'FAIL'])
        errors = len([r for r in self.test_results if r.status == 'ERROR'])
        
        # Category breakdown
        category_stats = {}
        for result in self.test_results:
            category = result.test_category
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'passed': 0, 'failed': 0, 'errors': 0}
            
            category_stats[category]['total'] += 1
            if result.status == 'PASS':
                category_stats[category]['passed'] += 1
            elif result.status == 'FAIL':
                category_stats[category]['failed'] += 1
            else:
                category_stats[category]['errors'] += 1
        
        # Performance metrics
        performance_tests = [r for r in self.test_results if r.performance_metrics]
        avg_performance = 0
        if performance_tests:
            performances = [r.performance_metrics.get('messages_per_second', 0) for r in performance_tests]
            avg_performance = sum(performances) / len(performances) if performances else 0
        
        return {
            'total_tests': total_tests,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'success_rate': (passed / total_tests) * 100 if total_tests > 0 else 0,
            'total_time': total_time,
            'category_stats': category_stats,
            'average_performance': avg_performance,
            'failed_tests': [r for r in self.test_results if r.status in ['FAIL', 'ERROR']]
        }
    
    def print_summary(self, summary: Dict[str, Any]) -> None:
        """Print comprehensive test summary."""
        print(f"\n🎉 TEST EXECUTION COMPLETE")
        print("=" * 60)
        print(f"⏱️  Total Time: {summary['total_time']:.2f} seconds")
        print(f"📊 Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"🚨 Errors: {summary['errors']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        
        if summary['average_performance'] > 0:
            print(f"🚀 Average Performance: {summary['average_performance']:,.0f} msg/s")
        
        # Category breakdown
        print(f"\n📋 CATEGORY BREAKDOWN:")
        print("-" * 30)
        for category, stats in summary['category_stats'].items():
            success_rate = (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
            print(f"  {category}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Failed tests
        if summary['failed_tests']:
            print(f"\n❌ FAILED TESTS:")
            print("-" * 20)
            for test in summary['failed_tests']:
                print(f"  • {os.path.basename(test.test_file)}: {test.status}")
                if test.error_message:
                    print(f"    Error: {test.error_message[:100]}...")
    
    def save_results(self, filename: str = "test_results.json") -> None:
        """Save test results to JSON file."""
        results_data = {
            'timestamp': time.time(),
            'total_tests': len(self.test_results),
            'results': [
                {
                    'test_file': r.test_file,
                    'category': r.test_category,
                    'status': r.status,
                    'execution_time': r.execution_time,
                    'error_message': r.error_message,
                    'performance_metrics': r.performance_metrics
                }
                for r in self.test_results
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"💾 Results saved to {filename}")


# Global test orchestrator instance
test_orchestrator = TestOrchestrator()
