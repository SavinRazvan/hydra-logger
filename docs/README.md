# Hydra-Logger Documentation

Welcome to the comprehensive documentation for Hydra-Logger, a dynamic, multi-headed logging system for Python applications that supports custom folder paths, multi-layered logging, multiple log formats, and configuration via YAML/TOML files.

## 📚 Documentation Structure

### Core Documentation
- **[API Reference](api.md)** - Complete API documentation with examples
- **[Configuration Guide](configuration.md)** - Detailed configuration options and formats
- **[Examples Guide](examples.md)** - Comprehensive code examples and use cases
- **[Migration Guide](migration.md)** - How to migrate from existing logging systems

### Advanced Topics
- **[Security Guide](security.md)** - Security best practices and considerations
- **[Testing Guide](testing.md)** - How to run tests and generate coverage reports

## 🚀 Quick Start

For a quick introduction to Hydra-Logger, see the [main README](../README.md) in the project root, which includes:
- Installation instructions
- Basic usage examples
- Feature overview
- Quick configuration examples

## 🎯 Key Features

### Multi-Layered Logging
- Route different types of logs to different destinations
- Custom folder paths for each log file
- Multiple destinations per layer (file and console)
- Independent log levels per layer and destination

### Multiple Log Formats
- **Text**: Traditional plain text logging with timestamps
- **JSON**: Structured logging for log aggregation and analysis
- **CSV**: Comma-separated values for analytics and data processing
- **Syslog**: System integration format for enterprise environments
- **GELF**: Graylog Extended Log Format for centralized logging

### Configuration Management
- YAML and TOML configuration file support
- Programmatic configuration with Pydantic models
- Environment variable support
- Default configuration generation

### Enterprise Features
- File rotation with configurable sizes and backup counts
- Thread-safe logging operations
- Graceful error handling and fallbacks
- Backward compatibility with existing logging code

## 📖 API Reference

The complete API reference is available in [api.md](api.md), including:

### Core Classes
- `HydraLogger` - Main logging class
- `LoggingConfig` - Configuration container
- `LogLayer` - Layer configuration
- `LogDestination` - Destination configuration

### Configuration Models
- Pydantic-based validation
- Type-safe configuration
- Automatic validation and error handling

### Backward Compatibility
- `setup_logging()` function
- `migrate_to_hydra()` migration helper
- Standard Python logging integration

## ⚙️ Configuration

Learn about all configuration options in [configuration.md](configuration.md):

### File Formats
- YAML configuration files
- TOML configuration files
- Programmatic configuration
- Environment variables

### Configuration Options
- Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- File rotation settings
- Multiple destinations per layer
- Format specifications per destination
- Custom folder paths

### Examples
- Simple configurations
- Advanced enterprise setups
- Format-specific configurations
- Real-world use cases

## 🧪 Examples

Comprehensive examples and use cases are documented in [examples.md](examples.md):

### Basic Examples
- Simple logging setup
- Multi-layered logging
- Configuration file usage
- Format demonstrations

### Advanced Examples
- Enterprise logging setups
- Microservices logging
- Performance monitoring
- Security logging
- Analytics and reporting

### Real-World Scenarios
- Web application logging
- API service logging
- Database operation logging
- Security event logging
- Performance metrics collection

## 🔄 Migration

If you're migrating from an existing logging system, check [migration.md](migration.md) for guidance:

### Migration Paths
- From standard Python logging
- From other logging libraries
- From custom logging solutions
- From legacy systems

### Migration Strategies
- Gradual migration
- Complete replacement
- Hybrid approaches
- Testing and validation

## 🔒 Security

Security considerations and best practices are documented in [security.md](security.md):

### Security Features
- Secure file permissions
- Log file encryption
- Access control
- Audit logging

### Best Practices
- Log file security
- Sensitive data handling
- Access monitoring
- Compliance considerations

## 🧪 Testing

Learn how to test Hydra-Logger and generate coverage reports in [testing.md](testing.md):

### Testing Framework
- pytest integration
- Coverage reporting
- Unit tests
- Integration tests
- Performance tests

### Test Coverage
- Code coverage metrics
- HTML and XML reports
- Continuous integration
- Quality assurance

## 📦 Installation and Setup

### Requirements
- Python 3.8+
- Pydantic 2.0+
- PyYAML or TOML support
- Optional: python-json-logger, graypy for advanced formats

### Installation Methods
```bash
# PyPI installation
pip install hydra-logger

# Development installation
git clone https://github.com/SavinRazvan/hydra-logger.git
cd hydra-logger
pip install -e .

# With conda
conda env create -f environment.yml
conda activate hydra-logger
```

## 🏗️ Architecture

### Core Components
- **HydraLogger**: Main logging orchestrator
- **Configuration System**: Pydantic-based configuration management
- **Format Handlers**: Multiple log format support
- **File Handlers**: Rotating file handlers with custom paths
- **Console Handlers**: Console output with format support

### Design Principles
- **Modularity**: Each component is independent and replaceable
- **Extensibility**: Easy to add new formats and destinations
- **Type Safety**: Full type hints and Pydantic validation
- **Performance**: Optimized for high-throughput logging
- **Reliability**: Graceful error handling and fallbacks

## 🤝 Contributing

To contribute to the documentation, see [CONTRIBUTING.md](../CONTRIBUTING.md) in the project root.

### Documentation Standards
- Clear and concise writing
- Code examples for all features
- Real-world use cases
- Professional formatting
- Regular updates and maintenance

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

**For the latest updates and community support, visit the [GitHub repository](https://github.com/SavinRazvan/hydra-logger).** 