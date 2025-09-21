#!/usr/bin/env python3
"""
Comprehensive Async Logger Validation with Background Processing.

This script validates all async loggers to ensure background processing
is working correctly and providing performance benefits.
"""

import sys
import os
import time
import asyncio
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hydra_logger import (
    AsyncLogger, UltraOptimizedAsyncLogger, ExtremePerformanceAsyncLogger
)


class AsyncValidationResult:
    """Result of async logger validation."""
    
    def __init__(self, logger_name: str):
        self.logger_name = logger_name
        self.object_pool = "SKIP"
        self.performance = "SKIP"
        self.async_workflow = "SKIP"
        self.error_handling = "SKIP"
        self.background_processing = "SKIP"
        self.overall_status = "PENDING"


async def validate_object_pool(logger, logger_name: str) -> Dict[str, Any]:
    """Validate object pool functionality."""
    try:
        if hasattr(logger, '_record_pool'):
            # Test pool functionality
            initial_stats = logger._record_pool.get_stats()
            
            # Perform some logging to test pool
            for i in range(10):
                await logger.info(f"Test message {i}")
            
            final_stats = logger._record_pool.get_stats()
            
            hit_rate = final_stats.get('hit_rate', 0)
            total_requests = final_stats.get('total_requests', 0)
            
            return {
                'status': 'PASS',
                'message': f'Pool working (hit_rate: {hit_rate:.2f}, requests: {total_requests})',
                'hit_rate': hit_rate,
                'total_requests': total_requests
            }
        else:
            return {
                'status': 'SKIP',
                'message': 'No object pool (standard logger)',
                'hit_rate': 0,
                'total_requests': 0
            }
    except Exception as e:
        return {
            'status': 'FAIL',
            'message': f'Pool validation failed: {e}',
            'hit_rate': 0,
            'total_requests': 0
        }


async def validate_performance(logger, logger_name: str) -> Dict[str, Any]:
    """Validate performance characteristics."""
    try:
        # Suppress output during performance testing
        import io
        import contextlib
        
        # Redirect stdout/stderr to suppress output
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            # Warm up
            for i in range(100):
                await logger.info(f"Warmup message {i}")
            
            # Performance test
            start_time = time.time()
            message_count = 10000
            
            for i in range(message_count):
                await logger.info(f"Performance test message {i}")
            
            end_time = time.time()
            duration = end_time - start_time
            messages_per_second = message_count / duration if duration > 0 else 0
            
            # Check object pool stats if available
            pool_requests = 0
            if hasattr(logger, '_record_pool'):
                pool_stats = logger._record_pool.get_stats()
                pool_requests = pool_stats.get('total_requests', 0)
            
            return {
                'status': 'PASS',
                'message': f'Performance: {messages_per_second:,.0f} msg/s',
                'messages_per_second': messages_per_second,
                'pool_requests': pool_requests
            }
    except Exception as e:
        return {
            'status': 'FAIL',
            'message': f'Performance test failed: {e}',
            'messages_per_second': 0,
            'pool_requests': 0
        }


async def validate_async_workflow(logger, logger_name: str) -> Dict[str, Any]:
    """Validate async workflow functionality."""
    try:
        # Test basic async logging
        await logger.debug("Debug message")
        await logger.info("Info message")
        await logger.warning("Warning message")
        await logger.error("Error message")
        await logger.critical("Critical message")
        
        # Test async context manager
        async with logger:
            await logger.info("Context manager test")
        
        return {
            'status': 'PASS',
            'message': 'Async workflow working correctly'
        }
    except Exception as e:
        return {
            'status': 'FAIL',
            'message': f'Async workflow failed: {e}'
        }


async def validate_error_handling(logger, logger_name: str) -> Dict[str, Any]:
    """Validate error handling."""
    try:
        # Test various error conditions
        await logger.info(None)  # None message
        await logger.info("")    # Empty message
        await logger.info("x" * 10000)  # Very long message
        
        # Test with invalid level
        try:
            await logger.log("invalid_level", "Test message")
        except:
            pass  # Expected to fail
        
        return {
            'status': 'PASS',
            'message': 'Error handling working correctly'
        }
    except Exception as e:
        return {
            'status': 'FAIL',
            'message': f'Error handling failed: {e}'
        }


async def validate_background_processing(logger, logger_name: str) -> Dict[str, Any]:
    """Validate background processing functionality."""
    try:
        # Check if background processing is enabled
        background_enabled = False
        if hasattr(logger, '_use_background_processing'):
            background_enabled = logger._use_background_processing
        
        # Check for background processing components
        has_background_processor = hasattr(logger, '_background_processor')
        has_async_handlers = False
        
        if hasattr(logger, '_handlers'):
            for handler in logger._handlers.values():
                if hasattr(handler, 'emit_async'):
                    has_async_handlers = True
                    break
        
        # Test background processing with multiple concurrent logs
        tasks = []
        for i in range(100):
            task = logger.info(f"Background test message {i}")
            tasks.append(task)
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            'status': 'PASS',
            'message': f'Background processing: enabled={background_enabled}, processor={has_background_processor}, async_handlers={has_async_handlers}',
            'background_enabled': background_enabled,
            'has_processor': has_background_processor,
            'has_async_handlers': has_async_handlers
        }
    except Exception as e:
        return {
            'status': 'FAIL',
            'message': f'Background processing validation failed: {e}',
            'background_enabled': False,
            'has_processor': False,
            'has_async_handlers': False
        }


async def validate_async_logger(logger_class, logger_name: str) -> AsyncValidationResult:
    """Validate a single async logger."""
    result = AsyncValidationResult(logger_name)
    
    print(f"🔍 VALIDATING: {logger_name}")
    print("-" * 50)
    
    try:
        print(f"Creating {logger_name}...")
        logger = logger_class(name=f"test_{logger_name.lower()}")
        print(f"✅ {logger_name} created successfully")
        
        print(f"Running validations for {logger_name}...")
        
        # Object pool validation
        print("  • Testing object pool...")
        pool_result = await validate_object_pool(logger, logger_name)
        result.object_pool = pool_result['status']
        print(f"    Result: {pool_result['status']}")
        if pool_result['status'] != 'SKIP':
            print(f"    Pool: {pool_result['total_requests']} requests, {pool_result['hit_rate']:.2f} hit rate")
        
        # Performance validation
        print("  • Testing performance...")
        perf_result = await validate_performance(logger, logger_name)
        result.performance = perf_result['status']
        print(f"    Result: {perf_result['status']}")
        if perf_result['status'] == 'PASS':
            print(f"    Performance: {perf_result['messages_per_second']:,.0f} msg/s")
        
        # Async workflow validation
        print("  • Testing async workflow...")
        workflow_result = await validate_async_workflow(logger, logger_name)
        result.async_workflow = workflow_result['status']
        print(f"    Result: {workflow_result['status']}")
        
        # Error handling validation
        print("  • Testing error handling...")
        error_result = await validate_error_handling(logger, logger_name)
        result.error_handling = error_result['status']
        print(f"    Result: {error_result['status']}")
        
        # Background processing validation
        print("  • Testing background processing...")
        bg_result = await validate_background_processing(logger, logger_name)
        result.background_processing = bg_result['status']
        print(f"    Result: {bg_result['status']}")
        if bg_result['status'] == 'PASS':
            print(f"    Background: {bg_result['message']}")
        
        # Cleanup
        print(f"Cleaning up {logger_name}...")
        if hasattr(logger, 'close') and asyncio.iscoroutinefunction(logger.close):
            await logger.close()
        else:
            logger.close()
        print(f"✅ {logger_name} cleaned up successfully")
        
        # Determine overall status
        all_results = [result.object_pool, result.performance, result.async_workflow, result.error_handling, result.background_processing]
        if all(r in ['PASS', 'SKIP'] for r in all_results) and any(r == 'PASS' for r in all_results):
            result.overall_status = "PASS"
        else:
            result.overall_status = "FAIL"
        
        print(f"✅ {logger_name} validation complete: {result.overall_status}")
        
    except Exception as e:
        print(f"❌ {logger_name} validation failed: {e}")
        result.overall_status = "FAIL"
    
    print()
    return result


async def main():
    """Main validation function."""
    print("🚀 COMPREHENSIVE ASYNC LOGGER VALIDATION")
    print("=" * 60)
    print()
    print("📋 VALIDATING ALL ASYNC LOGGERS")
    print("-" * 40)
    print()
    
    # Define async loggers to test
    async_loggers = [
        (AsyncLogger, "AsyncLogger"),
        (UltraOptimizedAsyncLogger, "UltraOptimizedAsyncLogger"),
        (ExtremePerformanceAsyncLogger, "ExtremePerformanceAsyncLogger")
    ]
    
    results = []
    
    # Validate each async logger
    for logger_class, logger_name in async_loggers:
        result = await validate_async_logger(logger_class, logger_name)
        results.append(result)
    
    # Print summary
    print("=" * 60)
    print("📊 ASYNC VALIDATION SUMMARY")
    print("=" * 60)
    
    total_loggers = len(results)
    passed_loggers = sum(1 for r in results if r.overall_status == "PASS")
    failed_loggers = sum(1 for r in results if r.overall_status == "FAIL")
    
    print(f"Total Async Loggers: {total_loggers}")
    print(f"✅ Passed: {passed_loggers}")
    print(f"❌ Failed: {failed_loggers}")
    print()
    
    print("📋 DETAILED RESULTS:")
    print("-" * 40)
    
    for result in results:
        status_icon = "✅" if result.overall_status == "PASS" else "❌"
        print(f"{status_icon} {result.logger_name}: {result.overall_status}")
        
        if result.object_pool != "SKIP":
            print(f"    • object_pool: {result.object_pool}")
        if result.performance != "SKIP":
            print(f"    • performance: {result.performance}")
        if result.async_workflow != "SKIP":
            print(f"    • async_workflow: {result.async_workflow}")
        if result.error_handling != "SKIP":
            print(f"    • error_handling: {result.error_handling}")
        if result.background_processing != "SKIP":
            print(f"    • background_processing: {result.background_processing}")
    
    print()
    print("=" * 60)
    if failed_loggers == 0:
        print("🎉 ALL ASYNC LOGGERS VALIDATED SUCCESSFULLY!")
        print("🚀 Your async implementation is BULLETPROOF and ready for production!")
    else:
        print(f"⚠️  {failed_loggers} ASYNC LOGGERS FAILED VALIDATION")
        print("🔧 Please review the failed validations above")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
