# 📚 Hydra-Logger Synchronous Examples

Welcome to the **Hydra-Logger Synchronous Examples**! This directory contains a comprehensive collection of examples demonstrating how to use Hydra-Logger in synchronous Python applications.

## 🎯 Learning Path

The examples are organized in a progressive learning path, from basic concepts to advanced enterprise patterns:

### **🌱 Foundation (01-05)**
- **01_basic_setup** - Get started with basic logging
- **02_console_only** - Console-only logging
- **03_file_only** - File-only logging
- **04_simple_config** - Configuration file examples
- **05_multiple_layers** - Multi-layered logging

### **🔧 Core Features (06-10)**
- **06_rotation** - Log file rotation
- **07_performance_monitoring** - Performance tracking
- **08_error_handling** - Error handling patterns
- **09_custom_formatters** - Custom formatting
- **10_environment_detection** - Environment-based configuration

### **🚀 Real-World Applications (11-15)**
- **11_web_application** - Web application logging
- **12_microservices** - Microservice patterns
- **13_high_concurrency** - High-concurrency scenarios
- **14_backpressure_handling** - Handling backpressure
- **15_structured_logging** - Structured logging formats

### **☁️ Advanced Patterns (16-20)**
- **16_cloud_integration** - Cloud service integration
- **17_database_logging** - Database operation logging
- **18_queue_based** - Queue-based logging
- **19_monitoring_integration** - Monitoring system integration
- **20_enterprise_patterns** - Enterprise-grade patterns

## 📁 Example Structure

Each example follows this structure:
```
examples_sync/
├── 01_basic_setup/
│   ├── README.md          # Example description
│   ├── main.py            # Main example code
│   └── logs/              # Generated logs
│       └── example.log
├── 02_console_only/
│   ├── README.md
│   ├── console_demo.py
│   └── logs/
└── ...
```

## 🚀 Quick Start

### **1. Basic Setup**
```bash
cd examples_sync/01_basic_setup
python main.py
```

### **2. View Generated Logs**
```bash
# Check the logs directory in each example
ls examples_sync/01_basic_setup/logs/
```

### **3. Run All Examples**
```bash
# Run all examples sequentially
for dir in examples_sync/*/; do
    if [ -f "$dir/main.py" ]; then
        echo "Running $(basename "$dir")..."
        cd "$dir" && python main.py && cd ../..
    fi
done
```

## 📊 Log Organization

Each example generates logs in its own `logs/` subdirectory:

```
examples_sync/
├── 01_basic_setup/logs/
│   ├── basic.log
│   └── console.log
├── 11_web_application/logs/
│   ├── app/
│   │   ├── main.log
│   │   └── errors.log
│   ├── api/
│   │   ├── requests.log
│   │   └── responses.log
│   └── database/
│       └── queries.log
└── ...
```

## 🎯 Example Categories

### **Basic Examples (01-05)**
Perfect for beginners learning Hydra-Logger:
- Simple logging setup
- Console and file output
- Configuration management
- Multi-layered logging

### **Feature Examples (06-10)**
Demonstrate core Hydra-Logger features:
- File rotation and management
- Performance monitoring
- Error handling patterns
- Custom formatting
- Environment detection

### **Application Examples (11-15)**
Real-world application scenarios:
- Web application logging
- Microservice patterns
- High-concurrency handling
- Structured logging formats

### **Advanced Examples (16-20)**
Enterprise-grade patterns:
- Cloud service integration
- Database logging
- Queue-based systems
- Monitoring integration
- Enterprise patterns

## 🔧 Running Examples

### **Prerequisites**
```bash
# Install Hydra-Logger
pip install hydra-logger

# Or install in development mode
pip install -e .
```

### **Running Individual Examples**
```bash
# Basic setup
cd examples_sync/01_basic_setup
python main.py

# Web application
cd examples_sync/11_web_application
python main.py

# Enterprise patterns
cd examples_sync/20_enterprise_patterns
python main.py
```

### **Running All Examples**
```bash
# Run all examples
python -m examples_sync.run_all_examples
```

## 📈 Expected Outcomes

After running the examples, you should understand:

1. **Basic Logging** - How to set up simple logging
2. **Configuration** - How to use configuration files
3. **Multi-layered Logging** - How to organize logs by purpose
4. **Performance** - How to monitor logging performance
5. **Error Handling** - How to handle logging errors
6. **Real-world Patterns** - How to use Hydra-Logger in applications
7. **Enterprise Patterns** - How to scale logging for enterprise use

## 🧪 Testing Examples

Each example can be tested independently:

```bash
# Test basic setup
cd examples_sync/01_basic_setup
python -m pytest test_main.py

# Test web application
cd examples_sync/11_web_application
python -m pytest test_web_app.py
```

## 📚 Related Documentation

- **[API Reference](../docs/api.md)** - Complete API documentation
- **[Configuration Guide](../docs/configuration.md)** - Configuration options
- **[Async Examples](../examples_async/)** - Asynchronous logging examples
- **[Migration Guide](../docs/migration.md)** - Migration from other logging systems

## 🤝 Contributing

To add new examples:

1. Create a new numbered directory (e.g., `21_new_feature/`)
2. Add a `README.md` explaining the example
3. Add the main example code
4. Add tests if applicable
5. Update this README with the new example

## 📝 Example Template

Each example should follow this template:

```python
# main.py
from hydra_logger import HydraLogger

def main():
    # Initialize logger
    logger = HydraLogger()
    
    # Demonstrate the feature
    logger.info("EXAMPLE", "This demonstrates the feature")
    
    # Show expected output
    print("Check logs/example.log for output")

if __name__ == "__main__":
    main()
```

```markdown
# README.md
## Feature Name

Brief description of what this example demonstrates.

### Running the Example
```bash
python main.py
```

### Expected Output
Describe what you should see in the logs.

### Key Concepts
- Concept 1
- Concept 2
- Concept 3
```

---

**Happy Logging! 🐉** 