#!/usr/bin/env python3
"""
📊 Data Processor: Real application with file-only logging

This example demonstrates a background data processing application
that uses comprehensive file logging for monitoring and debugging.

Features:
- Background data processing
- Comprehensive file logging
- Performance monitoring
- Error handling with logging
- Structured data logging

Time: 10 minutes
Difficulty: Intermediate
"""

import os
import time
import random
import json
from datetime import datetime
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


class DataProcessor:
    """Background data processing application with comprehensive logging."""
    
    def __init__(self):
        """Initialize the data processor with file-only logging."""
        # Create log directories
        os.makedirs("logs/examples", exist_ok=True)
        
        # Configure comprehensive logging
        self.config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path="logs/examples/data_processor.log",
                            format="text"
                        )
                    ]
                ),
                "PERF": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path="logs/examples/performance.json",
                            format="json"
                        )
                    ]
                ),
                "ERRORS": LogLayer(
                    level="ERROR",
                    destinations=[
                        LogDestination(
                            type="file",
                            path="logs/examples/errors.log",
                            format="text"
                        )
                    ]
                ),
                "DATA": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path="logs/examples/processed_data.csv",
                            format="csv"
                        )
                    ]
                )
            }
        )
        
        self.logger = HydraLogger(self.config)
        self.processed_count = 0
        self.error_count = 0
        
    def start_processing(self):
        """Start the data processing with comprehensive logging."""
        self.logger.info("APP", "Data processor started", 
                        timestamp=datetime.now().isoformat(),
                        version="1.0.0")
        
        print("📊 Data Processor Started")
        print("=" * 40)
        print("Processing data with comprehensive file logging...")
        print("Check logs/examples/ for generated files")
        print()
        
        # Simulate data processing
        for i in range(10):
            try:
                self.process_item(i)
                time.sleep(0.5)  # Simulate processing time
            except Exception as e:
                self.logger.error("ERRORS", "Processing error", 
                                item_id=i, error=str(e))
                self.error_count += 1
        
        self.finish_processing()
    
    def process_item(self, item_id):
        """Process a single data item with detailed logging."""
        start_time = time.time()
        
        # Log processing start
        self.logger.info("APP", "Processing item", 
                        item_id=item_id, 
                        timestamp=datetime.now().isoformat())
        
        # Simulate processing with random success/failure
        if random.random() < 0.1:  # 10% chance of error
            raise Exception(f"Random processing error for item {item_id}")
        
        # Simulate data transformation
        original_data = {"id": item_id, "value": random.randint(1, 100)}
        processed_data = {
            "id": item_id,
            "original_value": original_data["value"],
            "processed_value": original_data["value"] * 2,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
        
        # Log processed data
        self.logger.info("DATA", "Data processed", **processed_data)
        
        # Log performance metrics
        processing_time = time.time() - start_time
        self.logger.info("PERF", "Item processing completed",
                        item_id=item_id,
                        processing_time_ms=round(processing_time * 1000, 2),
                        memory_usage_mb=random.randint(50, 200),
                        cpu_usage_percent=random.randint(10, 30))
        
        self.processed_count += 1
        
        # Log progress
        if self.processed_count % 3 == 0:
            self.logger.info("APP", "Processing progress", 
                           items_processed=self.processed_count,
                           total_items=10,
                           progress_percent=(self.processed_count / 10) * 100)
    
    def finish_processing(self):
        """Finish processing with summary logging."""
        self.logger.info("APP", "Data processing completed",
                        total_processed=self.processed_count,
                        total_errors=self.error_count,
                        success_rate=((self.processed_count - self.error_count) / self.processed_count) * 100,
                        completion_time=datetime.now().isoformat())
        
        print("✅ Processing completed!")
        print(f"📊 Items processed: {self.processed_count}")
        print(f"❌ Errors encountered: {self.error_count}")
        print(f"📈 Success rate: {((self.processed_count - self.error_count) / self.processed_count) * 100:.1f}%")
        print()
        print("📁 Generated log files:")
        print("   📄 logs/examples/data_processor.log - Application logs")
        print("   📊 logs/examples/performance.json - Performance metrics")
        print("   ❌ logs/examples/errors.log - Error logs")
        print("   📋 logs/examples/processed_data.csv - Processed data")
        print()
        print("🔍 Check the log files to see comprehensive logging in action!")


def run_data_processor():
    """Run the data processor example."""
    print("📊 Data Processor Example")
    print("=" * 40)
    print("This example demonstrates file-only logging in a real application.")
    print("The data processor will:")
    print("  ✅ Process 10 data items")
    print("  ✅ Log to multiple file formats")
    print("  ✅ Track performance metrics")
    print("  ✅ Handle errors gracefully")
    print("  ✅ Generate structured data logs")
    print()
    
    processor = DataProcessor()
    processor.start_processing()


if __name__ == "__main__":
    run_data_processor() 