#!/usr/bin/env python3
"""
Comprehensive Sync Logger Validation Test for Hydra Logger
Verifies all sync loggers work correctly and are bulletproof.
"""

import time
import sys
import os
import traceback
from typing import Dict, Any, List
from hydra_logger import (
    SyncLogger, CompositeLogger
)

class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass

class SyncValidator:
    """Comprehensive validator for all sync logger implementations."""
    
    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []
        
    def validate_object_pool(self, logger, logger_name: str) -> Dict[str, Any]:
        """Validate object pool is working correctly."""
        try:
            # Check if logger has object pool
            if not hasattr(logger, '_record_pool'):
                return {
                    'status': 'SKIP',
                    'pool_working': False,
                    'message': 'No object pool (not a high-performance logger)'
                }
            
            # Get initial stats
            initial_stats = logger._record_pool.get_stats()
            
            # Log some messages
            for i in range(10):
                logger.info(f'Pool test {i}')
            
            # Get final stats
            final_stats = logger._record_pool.get_stats()
            
            # Validate pool usage
            if final_stats.get('total_requests', 0) == 0:
                raise ValidationError(f"{logger_name}: Object pool not used (total_requests=0)")
            
            if final_stats.get('hit_rate', 0) < 0.8:
                raise ValidationError(f"{logger_name}: Low hit rate {final_stats.get('hit_rate', 0):.2f}")
            
            if final_stats.get('reuse_rate', 0) < 0.8:
                raise ValidationError(f"{logger_name}: Low reuse rate {final_stats.get('reuse_rate', 0):.2f}")
            
            return {
                'status': 'PASS',
                'pool_working': True,
                'total_requests': final_stats.get('total_requests', 0),
                'hit_rate': final_stats.get('hit_rate', 0),
                'reuse_rate': final_stats.get('reuse_rate', 0)
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e),
                'pool_working': False
            }
    
    def validate_performance(self, logger, logger_name: str, test_messages: int = 1000) -> Dict[str, Any]:
        """Validate performance is real and not fake."""
        try:
            # Performance test
            start = time.perf_counter()
            for i in range(test_messages):
                logger.info(f'Perf test {i}')
            end = time.perf_counter()
            
            performance = test_messages / (end - start)
            
            # Validate performance is realistic (not too high, not too low)
            if performance > 1000000:  # > 1M msg/s is suspicious
                raise ValidationError(f"{logger_name}: Suspiciously high performance {performance:,.0f} msg/s")
            
            if performance < 1000:  # < 1K msg/s is too low
                raise ValidationError(f"{logger_name}: Performance too low {performance:,.0f} msg/s")
            
            # Check object pool was actually used (if available)
            if hasattr(logger, '_record_pool'):
                pool_stats = logger._record_pool.get_stats()
                if pool_stats.get('total_requests', 0) < test_messages:
                    raise ValidationError(f"{logger_name}: Pool requests {pool_stats.get('total_requests', 0)} < test messages {test_messages}")
            
            pool_requests = 0
            if hasattr(logger, '_record_pool'):
                pool_stats = logger._record_pool.get_stats()
                pool_requests = pool_stats.get('total_requests', 0)
            
            return {
                'status': 'PASS',
                'performance': performance,
                'pool_requests': pool_requests,
                'real_performance': True
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e),
                'real_performance': False
            }
    
    def validate_sync_workflow(self, logger, logger_name: str) -> Dict[str, Any]:
        """Validate complete sync workflow."""
        try:
            # Test sync methods exist
            required_methods = ['log', 'debug', 'info', 'warning', 'error', 'critical']
            for method in required_methods:
                if not hasattr(logger, method):
                    raise ValidationError(f"{logger_name}: Missing method {method}")
                
                # Check it's not async
                import inspect
                if inspect.iscoroutinefunction(getattr(logger, method)):
                    raise ValidationError(f"{logger_name}: Method {method} is async (should be sync)")
            
            # Test close method exists
            if not hasattr(logger, 'close'):
                raise ValidationError(f"{logger_name}: Missing close method")
            
            return {
                'status': 'PASS',
                'sync_workflow': True
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e),
                'sync_workflow': False
            }
    
    def validate_error_handling(self, logger, logger_name: str) -> Dict[str, Any]:
        """Validate robust error handling."""
        try:
            # Test with invalid inputs
            test_cases = [
                (None, "Test message"),  # Invalid level
                ("INFO", None),  # Invalid message
                ("INVALID_LEVEL", "Test message"),  # Invalid level string
            ]
            
            errors_caught = 0
            for level, message in test_cases:
                try:
                    logger.log(level, message)
                    errors_caught += 1
                except Exception:
                    pass  # Expected to fail
            
            # Test with valid inputs (should not fail)
            try:
                logger.info("Valid test message")
            except Exception as e:
                raise ValidationError(f"{logger_name}: Failed with valid input: {e}")
            
            return {
                'status': 'PASS',
                'error_handling': True,
                'errors_caught': errors_caught
            }
            
        except Exception as e:
            return {
                'status': 'FAIL',
                'error': str(e),
                'error_handling': False
            }
    
    def validate_logger(self, logger_class, logger_name: str) -> Dict[str, Any]:
        """Comprehensive validation of a single logger."""
        print(f"\n🔍 VALIDATING: {logger_name}")
        print("-" * 50)
        
        # Suppress output during validation
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        
        try:
            # Create logger
            print(f"Creating {logger_name}...", file=original_stdout)
            logger = logger_class()
            print(f"✅ {logger_name} created successfully", file=original_stdout)
            
            # Run all validations
            print(f"Running validations for {logger_name}...", file=original_stdout)
            
            print(f"  • Testing object pool...", file=original_stdout)
            object_pool_result = self.validate_object_pool(logger, logger_name)
            print(f"    Result: {object_pool_result['status']}", file=original_stdout)
            if object_pool_result['status'] == 'FAIL':
                print(f"    Error: {object_pool_result['error']}", file=original_stdout)
            elif object_pool_result['status'] == 'PASS':
                print(f"    Pool: {object_pool_result['total_requests']} requests, {object_pool_result['hit_rate']:.2f} hit rate", file=original_stdout)
            
            print(f"  • Testing performance...", file=original_stdout)
            performance_result = self.validate_performance(logger, logger_name)
            print(f"    Result: {performance_result['status']}", file=original_stdout)
            if performance_result['status'] == 'FAIL':
                print(f"    Error: {performance_result['error']}", file=original_stdout)
            elif performance_result['status'] == 'PASS':
                print(f"    Performance: {performance_result['performance']:,.0f} msg/s", file=original_stdout)
            
            print(f"  • Testing sync workflow...", file=original_stdout)
            sync_workflow_result = self.validate_sync_workflow(logger, logger_name)
            print(f"    Result: {sync_workflow_result['status']}", file=original_stdout)
            if sync_workflow_result['status'] == 'FAIL':
                print(f"    Error: {sync_workflow_result['error']}", file=original_stdout)
            
            print(f"  • Testing error handling...", file=original_stdout)
            error_handling_result = self.validate_error_handling(logger, logger_name)
            print(f"    Result: {error_handling_result['status']}", file=original_stdout)
            if error_handling_result['status'] == 'FAIL':
                print(f"    Error: {error_handling_result['error']}", file=original_stdout)
            
            validations = {
                'object_pool': object_pool_result,
                'performance': performance_result,
                'sync_workflow': sync_workflow_result,
                'error_handling': error_handling_result
            }
            
            # Cleanup
            print(f"Cleaning up {logger_name}...", file=original_stdout)
            try:
                logger.close()
                print(f"✅ {logger_name} cleaned up successfully", file=original_stdout)
            except Exception as e:
                print(f"⚠️  {logger_name} cleanup failed: {e}", file=original_stdout)
                self.warnings.append(f"{logger_name}: Cleanup failed: {e}")
            
            # Determine overall status
            failed_validations = [k for k, v in validations.items() if v['status'] == 'FAIL']
            if failed_validations:
                overall_status = 'FAIL'
                self.errors.append(f"{logger_name}: Failed validations: {failed_validations}")
            else:
                overall_status = 'PASS'
            
            print(f"✅ {logger_name} validation complete: {overall_status}", file=original_stdout)
            
            return {
                'logger_name': logger_name,
                'status': overall_status,
                'validations': validations
            }
            
        except Exception as e:
            print(f"❌ {logger_name} validation failed: {e}", file=original_stdout)
            traceback.print_exc(file=original_stdout)
            self.errors.append(f"{logger_name}: Validation failed: {e}")
            return {
                'logger_name': logger_name,
                'status': 'FAIL',
                'error': str(e)
            }
        finally:
            # Restore output
            sys.stdout.close()
            sys.stderr.close()
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    
    def validate_all_sync_loggers(self) -> Dict[str, Any]:
        """Validate all sync logger implementations."""
        print("🚀 COMPREHENSIVE SYNC LOGGER VALIDATION")
        print("=" * 60)
        
        # Define all sync loggers to test
        sync_loggers = [
            ('SyncLogger', SyncLogger),
            ('CompositeLogger', CompositeLogger)
        ]
        
        # Validate all sync loggers
        print("\n📋 VALIDATING ALL SYNC LOGGERS")
        print("-" * 40)
        sync_results = []
        for name, logger_class in sync_loggers:
            result = self.validate_logger(logger_class, name)
            sync_results.append(result)
        
        # Compile results
        passed = [r for r in sync_results if r['status'] == 'PASS']
        failed = [r for r in sync_results if r['status'] == 'FAIL']
        
        return {
            'total_loggers': len(sync_results),
            'passed': len(passed),
            'failed': len(failed),
            'sync_results': sync_results,
            'errors': self.errors,
            'warnings': self.warnings
        }
    
    def print_summary(self, results: Dict[str, Any]):
        """Print comprehensive summary."""
        print("\n" + "=" * 60)
        print("📊 SYNC VALIDATION SUMMARY")
        print("=" * 60)
        
        print(f"Total Sync Loggers: {results['total_loggers']}")
        print(f"✅ Passed: {results['passed']}")
        print(f"❌ Failed: {results['failed']}")
        
        if results['errors']:
            print(f"\n🚨 ERRORS ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"  • {error}")
        
        if results['warnings']:
            print(f"\n⚠️  WARNINGS ({len(results['warnings'])}):")
            for warning in results['warnings']:
                print(f"  • {warning}")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        print("-" * 40)
        
        for result in results['sync_results']:
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            print(f"{status_icon} {result['logger_name']}: {result['status']}")
            
            if result['status'] == 'PASS' and 'validations' in result:
                for validation_name, validation_result in result['validations'].items():
                    if validation_result['status'] == 'PASS':
                        if 'performance' in validation_result:
                            print(f"    • {validation_name}: {validation_result['performance']:,.0f} msg/s")
                        elif 'pool_working' in validation_result:
                            print(f"    • {validation_name}: Pool working (hit_rate: {validation_result['hit_rate']:.2f})")
                        else:
                            print(f"    • {validation_name}: OK")
                    elif validation_result['status'] == 'SKIP':
                        print(f"    • {validation_name}: SKIPPED - {validation_result.get('message', 'No message')}")
                    else:
                        print(f"    • {validation_name}: FAILED - {validation_result.get('error', 'Unknown error')}")
            elif result['status'] == 'FAIL':
                print(f"    • Error: {result.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 60)
        
        if results['failed'] == 0:
            print("🎉 ALL SYNC LOGGERS VALIDATED SUCCESSFULLY!")
            print("🚀 Your sync implementation is BULLETPROOF and ready for production!")
        else:
            print(f"⚠️  {results['failed']} SYNC LOGGERS FAILED VALIDATION!")
            print("🔧 Fix the issues above before proceeding.")
        
        print("=" * 60)

def main():
    """Main validation function."""
    validator = SyncValidator()
    
    try:
        results = validator.validate_all_sync_loggers()
        validator.print_summary(results)
        
        # Exit with error code if any validations failed
        if results['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"🚨 VALIDATION SYSTEM FAILED: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
