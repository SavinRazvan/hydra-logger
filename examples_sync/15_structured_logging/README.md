# 15 - Structured Logging

## 🎯 Overview

This example demonstrates all the different log formats supported by Hydra-Logger:
- **Text Format** - Traditional plain text logging
- **JSON Format** - Structured JSON for log aggregation
- **CSV Format** - Comma-separated values for analytics
- **Syslog Format** - Standard syslog format
- **GELF Format** - Graylog Extended Log Format

## 🚀 Running the Example

```bash
python log_formats_demo.py
```

## 📊 Expected Output

### Text Format
```
2025-01-27 10:30:15 INFO [CONFIG] Configuration loaded (log_formats_demo.py:45)
```

### JSON Format
```json
{"timestamp": "2025-01-27 10:30:15", "level": "INFO", "logger": "CONFIG", "message": "Configuration loaded", "filename": "log_formats_demo.py", "lineno": 45}
```

### CSV Format
```csv
timestamp,level,logger,message,filename,lineno
2025-01-27 10:30:15,INFO,CONFIG,Configuration loaded,log_formats_demo.py,45
```

### Syslog Format
```
<134>2025-01-27T10:30:15.123Z hostname CONFIG: Configuration loaded
```

### GELF Format
```json
{"version": "1.1", "host": "hostname", "short_message": "Configuration loaded", "level": 6, "_logger": "CONFIG"}
```

## 🔑 Key Concepts

- **Format Selection**: Choose the right format for your use case
- **Structured Data**: JSON and CSV formats include structured data
- **Log Aggregation**: JSON and GELF formats work with log aggregation systems
- **Analytics**: CSV format is perfect for data analysis
- **System Integration**: Syslog format integrates with system logging

## 📁 Generated Files

```
logs/
├── text_format.log      # Plain text format
├── json_format.json     # JSON format
├── csv_format.csv       # CSV format
├── syslog_format.log    # Syslog format
└── gelf_format.gelf     # GELF format
```

## 🎨 Code Example

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Text format configuration
text_config = LoggingConfig(
    layers={
        "CONFIG": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/text_format.log",
                    format="text"
                )
            ]
        )
    }
)

# JSON format configuration
json_config = LoggingConfig(
    layers={
        "CONFIG": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/json_format.json",
                    format="json"
                )
            ]
        )
    }
)

# Use different formats
text_logger = HydraLogger(text_config)
json_logger = HydraLogger(json_config)

text_logger.info("CONFIG", "Configuration loaded")
json_logger.info("CONFIG", "Configuration loaded")
```

## 🧪 Testing

```bash
# Run the example
python log_formats_demo.py

# Check different format outputs
cat logs/text_format.log
cat logs/json_format.json
cat logs/csv_format.csv
cat logs/syslog_format.log
cat logs/gelf_format.gelf
```

## 📚 Use Cases

### **Text Format**
- Human-readable logs
- Traditional logging
- Simple debugging

### **JSON Format**
- Log aggregation systems (ELK Stack, Splunk)
- Machine-readable logs
- Structured data analysis

### **CSV Format**
- Data analysis and reporting
- Excel/spreadsheet integration
- Statistical analysis

### **Syslog Format**
- System integration
- Network devices
- Standard logging protocols

### **GELF Format**
- Graylog integration
- Centralized logging
- Network transmission

## 📚 Next Steps

After understanding this example, try:
- **16_cloud_integration** - Cloud service integration
- **17_database_logging** - Database operation logging
- **18_queue_based** - Queue-based logging 