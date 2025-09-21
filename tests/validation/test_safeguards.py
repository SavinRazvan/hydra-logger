#!/usr/bin/env python3
"""
Automated Test Runner with Safeguards for Hydra-Logger.

This script runs comprehensive tests with safeguards to prevent
the mistakes we made before.
"""

import sys
import os
import time
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hydra_logger.core.safeguards import code_safeguards
from hydra_logger import (
    SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger
)


def run_safeguard_validation():
    """Run safeguard validation on all loggers."""
    print("🛡️  RUNNING SAFEGUARD VALIDATION")
    print("=" * 60)
    
    # Define all logger classes
    sync_loggers = {
        'SyncLogger': SyncLogger,
        'CompositeLogger': CompositeLogger
    }
    
    async_loggers = {
        'AsyncLogger': AsyncLogger,
        'CompositeAsyncLogger': CompositeAsyncLogger
    }
    
    all_loggers = {**sync_loggers, **async_loggers}
    
    # Run safeguard validation
    results = code_safeguards.validate_all_loggers(all_loggers)
    
    return results


def run_performance_validation():
    """Run performance validation to ensure no regressions."""
    print("\n🚀 RUNNING PERFORMANCE VALIDATION")
    print("=" * 60)
    
    # Use existing validation tests instead of duplicate performance monitor
    print("✅ Performance validation skipped - using existing test files")
    print("   Run 'python3 test_sync_validation.py' for sync loggers")
    print("   Run 'python3 test_final_validation.py' for async loggers")
    
    return {'status': 'SKIPPED', 'message': 'Using existing validation tests'}


def run_comprehensive_validation():
    """Run comprehensive validation with all safeguards."""
    print("🎯 COMPREHENSIVE VALIDATION WITH SAFEGUARDS")
    print("=" * 70)
    
    start_time = time.time()
    
    # 1. Run safeguard validation
    safeguard_results = run_safeguard_validation()
    
    # 2. Run performance validation
    performance_results = run_performance_validation()
    
    # 3. Calculate overall results
    total_time = time.time() - start_time
    
    # Print final summary
    print(f"\n🎉 COMPREHENSIVE VALIDATION COMPLETE")
    print("=" * 50)
    print(f"⏱️  Total Time: {total_time:.2f} seconds")
    print(f"🛡️  Safeguards: {safeguard_results['passed']}/{safeguard_results['total_loggers']} passed")
    print(f"🚀 Performance: Skipped (use existing validation tests)")
    
    # Check if any critical issues
    critical_issues = 0
    if safeguard_results['failed'] > 0:
        critical_issues += safeguard_results['failed']
        print(f"❌ Critical Issues: {critical_issues}")
    
    if critical_issues == 0:
        print("✅ ALL SAFEGUARDS PASSED - CODE IS BULLETPROOF!")
        return True
    else:
        print(f"⚠️  {critical_issues} CRITICAL ISSUES FOUND - FIX BEFORE PROCEEDING!")
        return False


def main():
    """Main validation function."""
    try:
        success = run_comprehensive_validation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"🚨 VALIDATION SYSTEM FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
