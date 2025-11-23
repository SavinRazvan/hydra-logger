# Hydra-Logger Examples

This directory contains 16 working examples demonstrating all features of the Hydra-Logger library. Each example is fully functional and tested.

## Quick Start

### Run All Examples

The easiest way to test all examples with detailed reporting:

```bash
python3 examples/run_all_examples.py
```

This will:
- Execute all 16 examples
- Verify log file creation
- Report detailed results with timing
- Show  summary statistics

### Run Individual Examples

You can also run any example individually:

```bash
python3 examples/01_format_control.py
python3 examples/02_destination_control.py
python3 examples/12_quick_start_async.py
# ... etc
```

## Example Files and Their Log Outputs

Each example creates log files named after itself in the `logs/examples/` directory:

1. **01_format_control.py** - Format Control
   - Creates: `01_format_control.log`, `01_format_control.jsonl`
   - Demonstrates: Multiple formats (plain-text, json-lines) for different destinations

2. **02_destination_control.py** - Destination Control
   - Creates: `02_destination_control_auth.log`, `02_destination_control_api.jsonl`, `02_destination_control_errors.log`
   - Demonstrates: Multiple layers with different destinations (file-only, console+file)

3. **03_extension_control.py** - Extension Control
   - Creates: `03_extension_control.jsonl`
   - Demonstrates: Enabling/disabling extensions (security, performance)

4. **04_runtime_control.py** - Runtime Control
   - Creates: `04_runtime_control.jsonl`
   - Demonstrates: Creating and managing extensions at runtime

5. **05_custom_configurations.py** - Custom Configurations
   - Creates: `05_custom_configurations_db.log`
   - Demonstrates: Custom logger configurations with specific settings

6. **06_basic_colored_logging.py** - Basic Colored Logging
   - Creates: `06_basic_colored_logging.jsonl`
   - Demonstrates: Color system for console output (all log levels)

7. **07_multi_layer_colored_logging.py** - Multi-Layer Colored Logging
   - Creates: `07_multi_layer_colored_logging.jsonl`
   - Demonstrates: Different colors for different layers (api, database, security)

8. **08_mixed_console_file_output.py** - Mixed Console and File
   - Creates: `08_mixed_console_file_output.log`
   - Demonstrates: Colored console output + plain-text file output

9. **09_all_logger_types_colors.py** - All Logger Types with Colors
   - Creates: `09_all_logger_types_colors.jsonl`
   - Demonstrates: Colors with SyncLogger, AsyncLogger, and CompositeLogger

10. **10_disable_colors.py** - Disable Colors
    - Creates: `10_disable_colors.jsonl`
    - Demonstrates: Plain text output without ANSI color codes

11. **11_quick_start_basic.py** - Quick Start Basic
    - Creates: `11_quick_start_basic.jsonl`
    - Demonstrates: Simple synchronous logging usage

12. **12_quick_start_async.py** - Quick Start Async
    - Creates: `12_quick_start_async.jsonl`
    - Demonstrates: Asynchronous logging with proper cleanup

13. **13_extension_system_example.py** - Extension System
    - Creates: `13_extension_system_example.jsonl`
    - Demonstrates: Data protection extension with redaction patterns

14. **14_class_based_logging.py** - Class-Based Logging
    - Creates: `14_class_based_logging_app.jsonl`, `14_class_based_logging_service.log`, `14_class_based_logging_model.log`
    - Demonstrates: Logging from classes, instance methods, static methods, class methods, properties, and constructors

15. **15_eda_microservices_patterns.py** - EDA & Microservices Patterns
    - Creates: `15_microservice_auto.jsonl`, `15_microservice_shared.jsonl`, `15_microservice_events.jsonl`, `15_eda_service.jsonl`
    - Demonstrates: Event-driven architecture, microservices patterns, shared logger instances, correlation IDs, graceful shutdown

16. **16_multi_layer_web_app.py** - Multi-Layer Web Application
    - Creates: `16_api_requests.jsonl`, `16_database_operations.jsonl`, `16_frontend_events.jsonl`, `16_authentication.jsonl`, `16_middleware.jsonl`
    - Demonstrates: Professional web application logging with multiple layers (API, Database, Frontend, Auth, Middleware), concurrent requests, separate log files per layer

## Log File Naming Convention

All log files follow a consistent naming pattern for easy identification:

- **Single Layer Examples**: `XX_example_name.ext`
  - Example: `01_format_control.log`
  
- **Multi-Layer Examples**: `XX_example_name_layer.ext`
  - Example: `02_destination_control_auth.log`, `14_class_based_logging_service.log`

- **File Extensions**:
  - `.log` - Plain text or JSON format
  - `.jsonl` - JSON Lines format

## Features Demonstrated

### Core Features
- Format control (plain-text, json, json-lines, colored)
- Destination control (console, file, multiple destinations)
- Layer-based logging
- Extension system (security, performance, data protection)
- Function name tracking (automatic detection of file_name, function_name, line_number)

### Logger Types
- SyncLogger - Synchronous logging
- AsyncLogger - Asynchronous logging with queue-based processing
- CompositeLogger - Composite pattern for multiple components

### Output Formats
- Plain text
- JSON
- JSON Lines (JSONL)
- Colored console output
- Mixed formats (different format per destination)

### Features
- Runtime extension management
- Custom configurations
- Class-based logging with proper function tracking
- Multi-layer colored logging
- Async cleanup and resource management
- Event-driven architecture (EDA) patterns
- Microservices logging patterns
- Multi-layer web application logging
- Automatic cleanup with context managers

## Verification

All examples are verified to:
- Execute without errors
- Create expected log files
- Include proper function tracking (file_name, function_name, line_number)
- Display correct log messages with example counters `[XX]`

## Output Locations

All log files are written to: `logs/examples/`

The directory is automatically created if it doesn't exist.

## Notes

- Examples use counter prefixes `[01]`, `[02]`, etc. in log messages for easy identification
- Console output may include colors (if terminal supports ANSI escape codes)
- **Automatic Cleanup**: All examples use context managers (`with` or `async with`) for automatic cleanup
  - Sync examples: `with create_logger(...) as logger:` 
  - Async examples: `async with create_async_logger(...) as logger:`
  - No manual `close()` or `close_async()` needed - context managers handle it automatically
- All examples demonstrate proper function tracking in their log entries (file_name, function_name, line_number)
- Log files are automatically created in the correct format based on configuration
- Format-extension validation ensures `.jsonl` files use `json-lines` format automatically

