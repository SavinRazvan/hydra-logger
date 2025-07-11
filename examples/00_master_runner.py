#!/usr/bin/env python3
"""
Hydra-Logger Examples Master Runner

This script lists and can run all examples in the hierarchical structure.
Each example demonstrates different features of Hydra-Logger.

Features:
- Example discovery and validation
- Progress tracking with detailed reporting
- Error categorization and reporting
- Performance benchmarking
- Professional output formatting
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ExampleResult:
    """Result of running an example."""
    category: str
    filename: str
    success: bool
    duration: float
    error_message: Optional[str] = None
    output: Optional[str] = None
    exit_code: Optional[int] = None

# Example structure with descriptions
EXAMPLES = {
    "01_basics": {
        "01_basic_usage.py": "Zero-configuration, minimal usage of HydraLogger",
        "02_layered_usage.py": "Layered logging with configuration dictionary",
        "03_multiple_destinations.py": "Logging to multiple destinations with different formats"
    },
    "02_async": {
        "01_async_basic.py": "Minimal usage of AsyncHydraLogger",
        "02_async_colored_console.py": "Async logging with colored console output",
        "03_async_file_output.py": "Async logging to files with optimized performance",
        "04_async_structured_logging.py": "Structured logging with JSON, XML, and correlation IDs",
        "05_async_convenience_methods.py": "Convenience methods for HTTP requests, user actions, and errors",
        "06_async_performance_features.py": "Performance optimizations with object pooling and high throughput",
        "07_async_reliability_features.py": "Reliability features including flush, shutdown, and error handling",
        "08_async_comprehensive_example.py": "Comprehensive example demonstrating all async features together"
    },
    "03_format": {
        "01_format_customization.py": "Complete format customization demonstration",
        "02_environment_variables.py": "Format customization using environment variables"
    },
    "04_color": {
        "01_colored_console.py": "Colored console output with format customization",
        "02_color_mode_control.py": "Color mode control for different destinations"
    },
    "05_security": {
        "01_security_features.py": "PII detection, data sanitization, and security features"
    },
    "06_plugins": {
        "01_plugin_basic.py": "Plugin system with custom analytics plugin"
    },
    "07_performance": {
        "01_performance_monitoring.py": "Performance monitoring and metrics collection"
    },
    "08_magic_configs": {
        "01_basic_magic_configs.py": "Custom Magic Config System for sync and async loggers"
    },
    "09_error_handling": {
        "01_comprehensive_error_handling.py": "Comprehensive error handling system with tracking, context managers, and statistics"
    }
}

class ExampleRunner:
    """Professional example runner with comprehensive features."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.results: List[ExampleResult] = []
        self.start_time = time.time()
        self.total_examples = 0
        self.completed_examples = 0
        
    def discover_examples(self) -> Dict[str, Dict[str, str]]:
        """Discover all available examples with validation."""
        discovered = {}
        
        for category, examples in EXAMPLES.items():
            category_path = self.base_dir / category
            if not category_path.exists():
                print(f"Category directory not found: {category}")
                continue
                
            discovered[category] = {}
            for filename, description in examples.items():
                filepath = category_path / filename
                if filepath.exists():
                    discovered[category][filename] = description
                else:
                    print(f"Example file not found: {filepath}")
        
        return discovered
    
    def validate_examples(self, examples: Dict[str, Dict[str, str]]) -> Tuple[int, int]:
        """Validate all examples and return counts."""
        total = 0
        valid = 0
        
        for category, category_examples in examples.items():
            for filename in category_examples.keys():
                total += 1
                filepath = self.base_dir / category / filename
                if filepath.exists():
                    valid += 1
                else:
                    print(f"Missing: {category}/{filename}")
        
        return total, valid
    
    def run_example(self, category: str, filename: str, timeout: float = 30.0) -> ExampleResult:
        """Run a single example with comprehensive error handling."""
        filepath = self.base_dir / category / filename
        start_time = time.time()
        
        try:
            # Run the example with timeout
            result = subprocess.run(
                [sys.executable, str(filepath)],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                return ExampleResult(
                    category=category,
                    filename=filename,
                    success=True,
                    duration=duration,
                    output=result.stdout,
                    exit_code=result.returncode
                )
            else:
                return ExampleResult(
                    category=category,
                    filename=filename,
                    success=False,
                    duration=duration,
                    error_message=result.stderr,
                    output=result.stdout,
                    exit_code=result.returncode
                )
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return ExampleResult(
                category=category,
                filename=filename,
                success=False,
                duration=duration,
                error_message=f"Timeout after {timeout}s"
            )
        except Exception as e:
            duration = time.time() - start_time
            return ExampleResult(
                category=category,
                filename=filename,
                success=False,
                duration=duration,
                error_message=str(e)
            )
    
    def run_all_examples(self, timeout: float = 30.0) -> List[ExampleResult]:
        """Run all examples with progress tracking."""
        examples = self.discover_examples()
        total, valid = self.validate_examples(examples)
        
        print(f"Running {valid}/{total} valid examples")
        print("=" * 60)
        
        self.total_examples = valid
        self.completed_examples = 0
        
        for category, category_examples in examples.items():
            print(f"\nCategory: {category}")
            print("-" * 40)
            
            for filename in category_examples.keys():
                print(f"  Running: {filename}...", end=" ", flush=True)
                
                result = self.run_example(category, filename, timeout)
                self.results.append(result)
                self.completed_examples += 1
                
                if result.success:
                    print(f"✅ ({result.duration:.2f}s)")
                else:
                    print(f"❌ ({result.duration:.2f}s)")
                    if result.error_message:
                        print(f"     Error: {result.error_message[:100]}...")
        
        return self.results
    
    def generate_report(self) -> Dict[str, any]:
        """Generate comprehensive report."""
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        
        total_duration = sum(r.duration for r in self.results)
        avg_duration = total_duration / len(self.results) if self.results else 0
        
        # Categorize errors
        error_categories = {}
        for result in failed:
            error_type = "Unknown"
            if result.error_message:
                if "Timeout" in result.error_message:
                    error_type = "Timeout"
                elif "ImportError" in result.error_message:
                    error_type = "Import Error"
                elif "ModuleNotFoundError" in result.error_message:
                    error_type = "Module Not Found"
                elif "SyntaxError" in result.error_message:
                    error_type = "Syntax Error"
                else:
                    error_type = "Runtime Error"
            
            error_categories[error_type] = error_categories.get(error_type, 0) + 1
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_examples": len(self.results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": (len(successful) / len(self.results)) * 100 if self.results else 0,
            "total_duration": total_duration,
            "avg_duration": avg_duration,
            "error_categories": error_categories,
            "results": [
                {
                    "category": r.category,
                    "filename": r.filename,
                    "success": r.success,
                    "duration": r.duration,
                    "error_message": r.error_message
                }
                for r in self.results
            ]
        }
    
    def print_summary(self):
        """Print professional summary report."""
        report = self.generate_report()
        
        print("\n" + "=" * 60)
        print("📊 SUMMARY REPORT")
        print("=" * 60)
        
        print(f"📈 Success Rate: {report['success_rate']:.1f}%")
        print(f"✅ Successful: {report['successful']}/{report['total_examples']}")
        print(f"❌ Failed: {report['failed']}/{report['total_examples']}")
        print(f"⏱️  Total Duration: {report['total_duration']:.2f}s")
        print(f"📊 Average Duration: {report['avg_duration']:.2f}s")
        
        if report['error_categories']:
            print(f"\n🔍 Error Breakdown:")
            for error_type, count in report['error_categories'].items():
                print(f"   {error_type}: {count}")
        
        if report['failed'] > 0:
            print(f"\n❌ Failed Examples:")
            for result in self.results:
                if not result.success:
                    print(f"   {result.category}/{result.filename}")
                    if result.error_message:
                        print(f"      Error: {result.error_message[:100]}...")
        
        if report['successful'] == report['total_examples']:
            print(f"\n🎉 All examples completed successfully!")
        else:
            print(f"\n⚠️  {report['failed']} examples failed. Check the output above.")
    
    def save_report(self, filename: str = "example_run_report.json"):
        """Save detailed report to JSON file."""
        report = self.generate_report()
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Detailed report saved to: {filename}")
        except Exception as e:
            print(f"\n⚠️  Failed to save report: {e}")

def list_examples():
    """List all available examples with validation."""
    print("🚀 Hydra-Logger Examples")
    print("=" * 50)
    print()
    
    base_dir = Path(__file__).parent
    runner = ExampleRunner(base_dir)
    examples = runner.discover_examples()
    total, valid = runner.validate_examples(examples)
    
    for category, category_examples in examples.items():
        print(f"📁 {category}/")
        for filename, description in category_examples.items():
            filepath = base_dir / category / filename
            if filepath.exists():
                print(f"   ✅ {filename}")
                print(f"      {description}")
            else:
                print(f"   ❌ {filename} (not found)")
        print()
    
    print(f"📊 Summary: {valid}/{total} examples available")

def run_example(category: str, filename: str):
    """Run a specific example with professional output."""
    base_dir = Path(__file__).parent
    filepath = base_dir / category / filename
    
    if not filepath.exists():
        print(f"❌ Example not found: {filepath}")
        return False
    
    print(f"🚀 Running: {filepath}")
    print("=" * 50)
    
    runner = ExampleRunner(base_dir)
    result = runner.run_example(category, filename)
    
    if result.success:
        print(f"\n✅ Example completed successfully: {filepath}")
        print(f"⏱️  Duration: {result.duration:.2f}s")
        return True
    else:
        print(f"\n❌ Example failed: {filepath}")
        print(f"⏱️  Duration: {result.duration:.2f}s")
        if result.error_message:
            print(f"🔍 Error: {result.error_message}")
        return False

def run_all_examples():
    """Run all available examples with professional reporting."""
    print("🚀 Running All Hydra-Logger Examples")
    print("=" * 50)
    print()
    
    base_dir = Path(__file__).parent
    runner = ExampleRunner(base_dir)
    
    # Run all examples
    results = runner.run_all_examples()
    
    # Print summary
    runner.print_summary()
    
    # Save detailed report
    runner.save_report()
    
    return results

def main():
    """Main function with enhanced argument handling."""
    if len(sys.argv) == 1:
        # No arguments - show help
        print("Hydra-Logger Examples Runner")
        print("=" * 30)
        print()
        print("Usage:")
        print("  python 00_master_runner.py list                    # List all examples")
        print("  python 00_master_runner.py run-all                 # Run all examples")
        print("  python 00_master_runner.py run <category> <file>   # Run specific example")
        print("  python 00_master_runner.py validate                # Validate all examples")
        print()
        print("Examples:")
        print("  python 00_master_runner.py run 01_basics 01_basic_usage.py")
        print("  python 00_master_runner.py run 02_async 01_async_basic.py")
        print()
        list_examples()
        
    elif sys.argv[1] == "list":
        list_examples()
        
    elif sys.argv[1] == "run-all":
        run_all_examples()
        
    elif sys.argv[1] == "run" and len(sys.argv) == 4:
        category = sys.argv[2]
        filename = sys.argv[3]
        run_example(category, filename)
        
    elif sys.argv[1] == "validate":
        base_dir = Path(__file__).parent
        runner = ExampleRunner(base_dir)
        examples = runner.discover_examples()
        total, valid = runner.validate_examples(examples)
        print(f"Validation Results: {valid}/{total} examples are valid")
        
    else:
        print("❌ Invalid arguments. Use 'list', 'run-all', 'run <category> <file>', or 'validate'")

if __name__ == "__main__":
    main() 