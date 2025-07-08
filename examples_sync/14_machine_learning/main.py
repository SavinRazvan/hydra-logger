#!/usr/bin/env python3
"""
14 - Machine Learning

This example demonstrates machine learning logging with Hydra-Logger.
Shows how to log ML training, evaluation, and inference operations.
"""

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
import time
import random
import math

def simulate_ml_training(logger, model_name, dataset_size, epochs):
    """Simulate ML model training."""
    logger.info("TRAINING", "Training started",
                model_name=model_name,
                dataset_size=dataset_size,
                epochs=epochs,
                start_time=time.time())
    
    # Simulate training epochs
    for epoch in range(epochs):
        epoch_start = time.time()
        
        # Simulate training metrics
        loss = 1.0 * math.exp(-epoch * 0.3) + random.uniform(0, 0.1)
        accuracy = 0.5 + 0.4 * (1 - math.exp(-epoch * 0.3)) + random.uniform(-0.05, 0.05)
        accuracy = min(0.95, max(0.5, accuracy))  # Clamp between 0.5 and 0.95
        
        epoch_time = time.time() - epoch_start
        
        logger.info("TRAINING", "Epoch completed",
                    model_name=model_name,
                    epoch=epoch + 1,
                    total_epochs=epochs,
                    loss=f"{loss:.4f}",
                    accuracy=f"{accuracy:.4f}",
                    duration=f"{epoch_time:.2f}s")
        
        # Log detailed metrics every 5 epochs
        if (epoch + 1) % 5 == 0:
            logger.info("METRICS", "Training metrics snapshot",
                        model_name=model_name,
                        epoch=epoch + 1,
                        loss=f"{loss:.4f}",
                        accuracy=f"{accuracy:.4f}",
                        learning_rate=0.001,
                        batch_size=32)
    
    logger.info("TRAINING", "Training completed",
                model_name=model_name,
                total_epochs=epochs,
                final_loss=f"{loss:.4f}",
                final_accuracy=f"{accuracy:.4f}")

def simulate_model_evaluation(logger, model_name, test_size):
    """Simulate model evaluation."""
    logger.info("EVALUATION", "Model evaluation started",
                model_name=model_name,
                test_size=test_size)
    
    # Simulate evaluation metrics
    metrics = {
        "accuracy": random.uniform(0.85, 0.95),
        "precision": random.uniform(0.80, 0.90),
        "recall": random.uniform(0.80, 0.90),
        "f1_score": random.uniform(0.80, 0.90),
        "auc": random.uniform(0.85, 0.95)
    }
    
    for metric_name, value in metrics.items():
        logger.info("EVALUATION", f"{metric_name} calculated",
                    model_name=model_name,
                    metric=metric_name,
                    value=f"{value:.4f}")
    
    logger.info("EVALUATION", "Model evaluation completed",
                model_name=model_name,
                overall_score=f"{metrics['accuracy']:.4f}")

def simulate_inference(logger, model_name, batch_size):
    """Simulate model inference."""
    logger.info("INFERENCE", "Inference started",
                model_name=model_name,
                batch_size=batch_size)
    
    # Simulate inference on multiple batches
    total_predictions = 0
    total_time = 0
    
    for batch in range(5):
        batch_start = time.time()
        
        # Simulate inference time
        inference_time = random.uniform(0.1, 0.5)
        time.sleep(inference_time)
        
        predictions = batch_size
        total_predictions += predictions
        total_time += inference_time
        
        logger.debug("INFERENCE", "Batch inference completed",
                    model_name=model_name,
                    batch=batch + 1,
                    predictions=predictions,
                    duration=f"{inference_time:.3f}s")
    
    avg_time = total_time / total_predictions
    logger.info("INFERENCE", "Inference completed",
                model_name=model_name,
                total_predictions=total_predictions,
                total_time=f"{total_time:.3f}s",
                avg_time_per_prediction=f"{avg_time:.3f}s")

def main():
    """Demonstrate machine learning logging."""
    
    print("🤖 Machine Learning Demo")
    print("=" * 40)
    
    # Create ML configuration
    config = LoggingConfig(
        layers={
            "TRAINING": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/ml/training.log",
                        format="json"
                    )
                ]
            ),
            "EVALUATION": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/ml/evaluation.log",
                        format="json"
                    )
                ]
            ),
            "INFERENCE": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/ml/inference.log",
                        format="text"
                    )
                ]
            ),
            "METRICS": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/ml/metrics.csv",
                        format="csv"
                    )
                ]
            ),
            "EXPERIMENT": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/ml/experiments.log",
                        format="json"
                    )
                ]
            )
        }
    )
    
    # Initialize logger
    logger = HydraLogger(config)
    
    print("\n🧪 ML Experiment Tracking")
    print("-" * 25)
    
    # Simulate ML experiments
    experiments = [
        {
            "name": "resnet50_classification",
            "type": "image_classification",
            "dataset": "ImageNet",
            "dataset_size": 1000000,
            "epochs": 50
        },
        {
            "name": "bert_sentiment",
            "type": "text_classification",
            "dataset": "SST-2",
            "dataset_size": 70000,
            "epochs": 10
        },
        {
            "name": "transformer_translation",
            "type": "sequence_to_sequence",
            "dataset": "WMT14",
            "dataset_size": 4500000,
            "epochs": 30
        }
    ]
    
    for exp in experiments:
        logger.info("EXPERIMENT", "Experiment started",
                    experiment_name=exp["name"],
                    model_type=exp["type"],
                    dataset=exp["dataset"],
                    dataset_size=exp["dataset_size"],
                    hyperparameters={
                        "learning_rate": 0.001,
                        "batch_size": 32,
                        "optimizer": "Adam",
                        "loss_function": "CrossEntropyLoss"
                    })
        
        # Simulate training
        simulate_ml_training(logger, exp["name"], exp["dataset_size"], exp["epochs"])
        
        # Simulate evaluation
        test_size = exp["dataset_size"] // 10
        simulate_model_evaluation(logger, exp["name"], test_size)
        
        # Simulate inference
        simulate_inference(logger, exp["name"], 64)
        
        logger.info("EXPERIMENT", "Experiment completed",
                    experiment_name=exp["name"],
                    status="success")
    
    print("\n📊 Model Performance Comparison")
    print("-" * 30)
    
    # Simulate model comparison
    models = ["resnet50", "bert", "transformer"]
    comparison_metrics = ["accuracy", "inference_time", "model_size"]
    
    for model in models:
        for metric in comparison_metrics:
            if metric == "accuracy":
                value = random.uniform(0.85, 0.95)
            elif metric == "inference_time":
                value = random.uniform(10, 100)
            else:  # model_size
                value = random.uniform(100, 1000)
            
            logger.info("METRICS", "Model comparison metric",
                        model_name=model,
                        metric=metric,
                        value=f"{value:.2f}",
                        unit="%" if metric == "accuracy" else "ms" if metric == "inference_time" else "MB")
    
    print("\n🔍 Hyperparameter Tuning")
    print("-" * 25)
    
    # Simulate hyperparameter tuning
    hyperparameters = [
        {"learning_rate": 0.001, "batch_size": 32},
        {"learning_rate": 0.01, "batch_size": 32},
        {"learning_rate": 0.001, "batch_size": 64},
        {"learning_rate": 0.01, "batch_size": 64}
    ]
    
    for i, hp in enumerate(hyperparameters):
        logger.info("EXPERIMENT", "Hyperparameter trial started",
                    trial_id=f"trial_{i+1}",
                    hyperparameters=hp)
        
        # Simulate training with these hyperparameters
        final_accuracy = random.uniform(0.80, 0.95)
        
        logger.info("EXPERIMENT", "Hyperparameter trial completed",
                    trial_id=f"trial_{i+1}",
                    final_accuracy=f"{final_accuracy:.4f}",
                    hyperparameters=hp)
    
    print("\n📈 Model Monitoring")
    print("-" * 20)
    
    # Simulate model monitoring
    monitoring_metrics = [
        ("prediction_accuracy", 0.92),
        ("inference_latency", 45.2),
        ("model_drift", 0.05),
        ("data_quality", 0.98),
        ("system_resources", 0.75)
    ]
    
    for metric_name, value in monitoring_metrics:
        logger.info("METRICS", "Model monitoring metric",
                    metric_name=metric_name,
                    value=f"{value:.3f}",
                    timestamp=time.time(),
                    alert_threshold=0.8 if metric_name != "model_drift" else 0.1)
        
        # Check for alerts
        if metric_name == "model_drift" and value > 0.1:
            logger.warning("METRICS", "Model drift detected",
                          metric_name=metric_name,
                          value=f"{value:.3f}",
                          threshold=0.1,
                          action="retrain_model")
    
    print("\n🔄 Model Deployment")
    print("-" * 20)
    
    # Simulate model deployment
    deployment_stages = [
        ("validation", "Model validation passed"),
        ("testing", "Integration tests passed"),
        ("staging", "Staging deployment successful"),
        ("production", "Production deployment completed")
    ]
    
    for stage, message in deployment_stages:
        logger.info("DEPLOYMENT", f"Deployment stage: {stage}",
                    stage=stage,
                    model_name="production_model",
                    status="success",
                    timestamp=time.time())
    
    print("\n✅ Machine learning demo completed!")
    print("📝 Check the logs/ml/ directory for ML logs")
    
    # Show ML summary
    print("\n📊 ML Summary:")
    print("-" * 15)
    print(f"• Experiments: {len(experiments)}")
    print(f"• Models trained: {len(experiments)}")
    print(f"• Hyperparameter trials: {len(hyperparameters)}")
    print(f"• Monitoring metrics: {len(monitoring_metrics)}")
    print(f"• Deployment stages: {len(deployment_stages)}")

if __name__ == "__main__":
    main() 