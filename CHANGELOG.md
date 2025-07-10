# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Modular architecture with clear separation of concerns
- Zero-configuration mode that works out of the box
- Async logging system with data loss protection
- Format customization with environment variable support
- Color mode control for all destinations
- Plugin system with registry and base classes
- Custom Magic Config System with built-in configs
- Comprehensive examples and documentation

### Changed
- Complete refactoring to modular architecture
- Enhanced error handling and validation
- Improved performance with lazy initialization
- Better type hints and documentation

### Fixed
- All linter errors and type issues
- Import circular dependencies
- Format naming confusion (plain vs text)
- Async method signatures and awaitable errors

## [0.4.0] - Unreleased

### Added
- Modular architecture foundation
- Zero-configuration mode
- Async logging system
- Format customization system
- Color mode control
- Plugin system
- Custom Magic Config System
- Comprehensive documentation and examples

### Changed
- Complete refactoring from monolithic to modular design
- Enhanced error handling and validation
- Improved performance with lazy initialization

### Fixed
- All linter errors and type issues
- Import circular dependencies
- Format naming confusion
- Async method signatures

## [0.2.0] - Unreleased

### Added
- Enhanced JSON formatter with proper structured logging fields
- Comprehensive format-specific tests for all supported formats
- Professional documentation updates across all .md files
- Improved test coverage with format validation tests
- Universal application support documentation
- Professional tone improvements throughout documentation
- Enhanced examples for all application types
- Comprehensive troubleshooting guides

### Fixed
- JSON formatter now produces complete structured output with all fields
- Fixed field names in JSON output (`filename`, `lineno` instead of `file`, `line`)
- Updated tests to match actual JSON output structure
- Resolved linter warnings for JSON log files

### Changed
- Updated README.md with comprehensive format documentation
- Enhanced API documentation with detailed format examples
- Improved testing documentation with format-specific test examples
- Updated test count from 145 to 146 tests
- Professional language improvements throughout documentation
- Enhanced universal application support messaging
- Improved configuration examples for different application types

## [0.1.0] - Unreleased

### Added
- Initial release of Hydra-Logger
- Multi-layered logging support with custom folder paths
- Multiple log formats: text, JSON, CSV, syslog, and GELF
- YAML/TOML configuration file support
- Backward compatibility with existing `setup_logging()` code
- Thread-safe logging operations
- Comprehensive error handling and fallback mechanisms
- File rotation with configurable sizes and backup counts
- Standalone package design for reusability across projects

### Features
- **Multi-layered Logging**: Route different types of logs to different destinations
- **Custom Folder Paths**: Specify custom folders for each log file (e.g., `logs/config/`, `logs/security/`)
- **Multiple Destinations**: File and console output per layer with different log levels
- **Multiple Log Formats**: Support for text, structured JSON, CSV, Syslog, and GELF formats
- **Configuration Files**: YAML/TOML configuration support for easy deployment
- **Backward Compatibility**: Works with existing `setup_logging()` code
- **File Rotation**: Configurable file sizes and backup counts
- **Thread-Safe**: Safe for concurrent logging operations
- **Error Handling**: Graceful fallbacks and error recovery

### Technical Details
- **Test Coverage**: 97% with 146 comprehensive tests
- **Python Support**: Python 3.8+
- **Dependencies**: Minimal dependencies with optional format support
- **Documentation**: Comprehensive API reference and examples
- **Examples**: Real-world demos and configuration examples

### Supported Formats
- **Text Format**: Traditional plain text with timestamps and log levels
- **JSON Format**: Structured JSON format for log aggregation and analysis
- **CSV Format**: Comma-separated values for analytics and data processing
- **Syslog Format**: Standard syslog format for system integration
- **GELF Format**: Graylog Extended Log Format for centralized logging

### Configuration Examples
- Basic usage with default configuration
- Advanced multi-layer configurations
- Configuration file examples (YAML/TOML)
- Real-world application examples
- Migration from existing logging systems

### Documentation
- Comprehensive README with quick start guide
- Detailed API reference documentation
- Testing guide with coverage requirements
- Security documentation
- Contributing guidelines

### Examples and Demos
- Basic usage examples
- Log formats demonstration
- Multi-module application demo
- Multi-file workflow demo
- Configuration examples for various scenarios

---

## Version History

### Version 0.4.0 (Current)
- **Release Date**: Unreleased
- **Status**: Stable release
- **Features**: Complete multi-format logging system
- **Coverage**: 97% test coverage
- **Documentation**: Comprehensive and professional

### Future Versions
- **Planned**: Remote logging destinations (syslog server, etc.)
- **Planned**: Log aggregation and analysis tools
- **Planned**: Performance monitoring integration
- **Planned**: Docker and Kubernetes deployment examples
- **Planned**: Web UI for log visualization
- **Planned**: Integration with popular logging frameworks

---

## Migration Guide

### From setup_logging() to HydraLogger

If you're using the original `setup_logging()` function, you can migrate to HydraLogger:

```python
# Old way
from hydra_logger import setup_logging
setup_logging(enable_file_logging=True, console_level=logging.INFO)

# New way
from hydra_logger import HydraLogger
logger = HydraLogger()
logger.info("DEFAULT", "Your message here")

# Or migrate with custom path
from hydra_logger import migrate_to_hydra
logger = migrate_to_hydra(
    enable_file_logging=True,
    console_level=logging.INFO,
    log_file_path="logs/custom/app.log"
)
```

### Format Migration

The JSON format has been enhanced with complete structured fields:

```python
# Old JSON format (if any)
{"message": "Log message"}

# New JSON format
{
    "timestamp": "2024-01-15 14:30:15",
    "level": "INFO", 
    "logger": "LAYER",
    "message": "Log message",
    "filename": "logger.py",
    "lineno": 483
}
```

---

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](DEVELOPMENT.md#contributing) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ by [Savin Ionut Razvan](https://github.com/SavinRazvan) for better logging organization** 