#!/usr/bin/env python3
"""
13 - Data Processing

This example demonstrates data processing logging with Hydra-Logger.
Shows how to log data processing operations and track data flow.
"""

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
import time
import random
import json

def simulate_data_processing(logger, data_id, data_size, processing_type):
    """Simulate data processing operation."""
    start_time = time.time()
    
    logger.info("DATA", f"Data processing started",
                data_id=data_id,
                data_size=data_size,
                processing_type=processing_type,
                timestamp=start_time)
    
    # Simulate processing steps
    steps = ["validation", "cleaning", "transformation", "enrichment", "output"]
    
    for step in steps:
        step_start = time.time()
        
        # Simulate processing time
        processing_time = random.uniform(0.1, 0.5)
        time.sleep(processing_time)
        
        # Simulate potential errors
        if random.random() < 0.05:  # 5% chance of error
            logger.error("DATA", f"Error in {step} step",
                        data_id=data_id,
                        step=step,
                        error="Data validation failed",
                        processing_type=processing_type)
            return False
        
        logger.debug("DATA", f"{step} step completed",
                    data_id=data_id,
                    step=step,
                    duration=f"{processing_time:.3f}s",
                    processing_type=processing_type)
    
    total_time = time.time() - start_time
    logger.info("DATA", "Data processing completed",
                data_id=data_id,
                processing_type=processing_type,
                total_duration=f"{total_time:.3f}s",
                success=True)
    
    return True

def main():
    """Demonstrate data processing logging."""
    
    print("📊 Data Processing Demo")
    print("=" * 40)
    
    # Create data processing configuration
    config = LoggingConfig(
        layers={
            "DATA": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/data_processing/processing.log",
                        format="json"
                    )
                ]
            ),
            "BATCH": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/data_processing/batch.log",
                        format="text"
                    )
                ]
            ),
            "STREAM": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/data_processing/stream.log",
                        format="json"
                    )
                ]
            ),
            "QUALITY": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/data_processing/quality.csv",
                        format="csv"
                    )
                ]
            ),
            "METRICS": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/data_processing/metrics.json",
                        format="json"
                    )
                ]
            )
        }
    )
    
    # Initialize logger
    logger = HydraLogger(config)
    
    print("\n🔄 Batch Processing")
    print("-" * 20)
    
    # Simulate batch processing
    batch_id = "batch_20250127_001"
    total_records = 1000
    processed_records = 0
    failed_records = 0
    
    logger.info("BATCH", "Batch processing started",
                batch_id=batch_id,
                total_records=total_records,
                start_time=time.time())
    
    for i in range(total_records):
        data_id = f"data_{i:04d}"
        data_size = random.randint(100, 10000)
        
        success = simulate_data_processing(logger, data_id, data_size, "batch")
        
        if success:
            processed_records += 1
        else:
            failed_records += 1
        
        # Log progress every 100 records
        if (i + 1) % 100 == 0:
            progress = ((i + 1) / total_records) * 100
            logger.info("BATCH", "Batch processing progress",
                        batch_id=batch_id,
                        processed=i + 1,
                        total=total_records,
                        progress=f"{progress:.1f}%",
                        success_rate=f"{((processed_records/(i+1))*100):.1f}%")
    
    logger.info("BATCH", "Batch processing completed",
                batch_id=batch_id,
                total_records=total_records,
                processed_records=processed_records,
                failed_records=failed_records,
                success_rate=f"{(processed_records/total_records)*100:.1f}%")
    
    print("\n🌊 Stream Processing")
    print("-" * 20)
    
    # Simulate stream processing
    stream_id = "stream_20250127_001"
    stream_duration = 10  # seconds
    start_time = time.time()
    
    logger.info("STREAM", "Stream processing started",
                stream_id=stream_id,
                start_time=start_time)
    
    record_count = 0
    while time.time() - start_time < stream_duration:
        data_id = f"stream_data_{record_count:04d}"
        data_size = random.randint(50, 500)
        
        # Simulate real-time processing
        processing_time = random.uniform(0.01, 0.1)
        time.sleep(processing_time)
        
        logger.debug("STREAM", "Stream record processed",
                    stream_id=stream_id,
                    data_id=data_id,
                    data_size=data_size,
                    processing_time=f"{processing_time:.3f}s",
                    timestamp=time.time())
        
        record_count += 1
        
        # Log stream metrics every 10 records
        if record_count % 10 == 0:
            elapsed_time = time.time() - start_time
            throughput = record_count / elapsed_time
            logger.info("STREAM", "Stream processing metrics",
                        stream_id=stream_id,
                        records_processed=record_count,
                        elapsed_time=f"{elapsed_time:.1f}s",
                        throughput=f"{throughput:.1f} records/sec")
    
    logger.info("STREAM", "Stream processing completed",
                stream_id=stream_id,
                total_records=record_count,
                duration=f"{stream_duration:.1f}s",
                avg_throughput=f"{record_count/stream_duration:.1f} records/sec")
    
    print("\n🔍 Data Quality Monitoring")
    print("-" * 25)
    
    # Simulate data quality checks
    quality_checks = [
        ("completeness", 95.2),
        ("accuracy", 98.7),
        ("consistency", 92.1),
        ("timeliness", 99.5),
        ("validity", 97.3)
    ]
    
    for check_name, quality_score in quality_checks:
        logger.info("QUALITY", "Data quality check",
                    check_name=check_name,
                    quality_score=f"{quality_score:.1f}%",
                    status="pass" if quality_score >= 95 else "fail",
                    threshold=95.0)
        
        if quality_score < 95:
            logger.warning("QUALITY", "Data quality below threshold",
                          check_name=check_name,
                          quality_score=f"{quality_score:.1f}%",
                          threshold=95.0,
                          action="data_cleaning_required")
    
    print("\n📈 Performance Metrics")
    print("-" * 20)
    
    # Simulate performance metrics
    metrics = {
        "processing_time_avg": 0.25,
        "throughput": 4000,
        "error_rate": 0.5,
        "memory_usage": 512,
        "cpu_usage": 45.2,
        "disk_io": 1024
    }
    
    for metric_name, value in metrics.items():
        logger.info("METRICS", "Performance metric recorded",
                    metric_name=metric_name,
                    value=value,
                    unit="seconds" if "time" in metric_name else "records/sec" if "throughput" in metric_name else "MB" if "memory" in metric_name else "percent" if "usage" in metric_name else "MB/s",
                    timestamp=time.time())
    
    print("\n🔄 Data Transformation")
    print("-" * 20)
    
    # Simulate data transformation
    transformations = [
        ("normalization", "standardize_data"),
        ("aggregation", "sum_by_category"),
        ("filtering", "remove_outliers"),
        ("enrichment", "add_metadata"),
        ("validation", "check_constraints")
    ]
    
    for transform_name, operation in transformations:
        start_time = time.time()
        processing_time = random.uniform(0.1, 0.3)
        time.sleep(processing_time)
        
        logger.info("DATA", "Data transformation completed",
                    transformation=transform_name,
                    operation=operation,
                    duration=f"{processing_time:.3f}s",
                    records_affected=random.randint(100, 1000))
    
    print("\n📊 Data Analytics")
    print("-" * 18)
    
    # Simulate analytics operations
    analytics_operations = [
        ("descriptive_stats", "mean,median,std"),
        ("correlation_analysis", "pearson,spearman"),
        ("trend_analysis", "time_series"),
        ("anomaly_detection", "isolation_forest"),
        ("clustering", "k_means")
    ]
    
    for analysis_name, method in analytics_operations:
        start_time = time.time()
        processing_time = random.uniform(0.5, 2.0)
        time.sleep(processing_time)
        
        logger.info("DATA", "Analytics operation completed",
                    analysis_name=analysis_name,
                    method=method,
                    duration=f"{processing_time:.3f}s",
                    insights_generated=random.randint(5, 20))
    
    print("\n✅ Data processing demo completed!")
    print("📝 Check the logs/data_processing/ directory for processing logs")
    
    # Show processing summary
    print("\n📊 Processing Summary:")
    print("-" * 25)
    print(f"• Batch records: {total_records}")
    print(f"• Stream records: {record_count}")
    print(f"• Quality checks: {len(quality_checks)}")
    print(f"• Transformations: {len(transformations)}")
    print(f"• Analytics operations: {len(analytics_operations)}")
    print(f"• Success rate: {(processed_records/total_records)*100:.1f}%")

if __name__ == "__main__":
    main() 