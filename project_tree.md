📦hydra-logger
 ┣ 📂.git
 ┃ ┣ 📂branches
 ┃ ┣ 📂hooks
 ┣ ...
 ┣ 📂.github
 ┃ ┣ 📂ISSUE_TEMPLATE
 ┃ ┃ ┣ 📜bug_report.md
 ┃ ┃ ┗ 📜feature_request.md
 ┃ ┣ 📂workflows
 ┃ ┃ ┗ 📜ci.yml
 ┃ ┗ 📜pull_request_template.md
 ┣ 📂benchmarks
 ┃ ┣ 📂__pycache__
 ┃ ┃ ┗ 📜_plugins.cpython-38.pyc
 ┃ ┣ 📂_logs
 ┃ ┃ ┣ 📜asynccomposite.jsonl
 ┃ ┃ ┣ 📜asynccsv.csv
 ┃ ┃ ┣ 📜binary-compactlogger.bin
 ┃ ┃ ┣ 📜binary-extendedlogger.bin
 ┃ ┃ ┣ 📜hydraasynccompositelogger.jsonl
 ┃ ┃ ┣ 📜hydraasynccsvlogger.csv
 ┃ ┃ ┣ 📜hydrabinarycompactlogger.bin
 ┃ ┃ ┣ 📜hydrabinaryextendedlogger.bin
 ┃ ┃ ┣ 📜hydrabinarylogger.bin
 ┃ ┃ ┣ 📜hydracsvlogger.csv
 ┃ ┃ ┣ 📜hydrajsonlineslogger.jsonl
 ┃ ┃ ┣ 📜hydrajsonlogger.jsonl
 ┃ ┃ ┣ 📜hydrasynccompositelogger.jsonl
 ┃ ┃ ┣ 📜hydrasyncdatabaselogger.jsonl
 ┃ ┃ ┣ 📜json-lineslogger.jsonl
 ┃ ┃ ┣ 📜sync_database.jsonl
 ┃ ┃ ┣ 📜sync_file.jsonl
 ┃ ┃ ┗ 📜synccomposite.jsonl
 ┃ ┣ 📂_results
 ┃ ┃ ┣ 📜asynccomposite_results.json
 ┃ ┃ ┣ ...
 ┃ ┣ 📂utils
 ┃ ┃ ┣ 📂__pycache__
 ┃ ┃ ┃ ┣ 📜__init__.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜constants.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜models.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜performance.cpython-38.pyc
 ┃ ┃ ┃ ┗ 📜validation.cpython-38.pyc
 ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┣ 📜constants.py
 ┃ ┃ ┣ 📜models.py
 ┃ ┃ ┣ 📜performance.py
 ┃ ┃ ┗ 📜validation.py
 ┃ ┣ 📜_plugins.py
 ┃ ┗ 📜benchmark.py
 ┣ 📂docs
 ┃ ┣ 📂api-reference
 ┃ ┣ 📂configuration
 ┃ ┃ ┣ 📜automatic-setup.md
 ┃ ┃ ┗ 📜overview.md
 ┃ ┣ 📂examples
 ┃ ┃ ┣ 📜basic-logging.md
 ┃ ┃ ┣ 📜config-management.md
 ┃ ┃ ┗ 📜multi-layer.md
 ┃ ┣ 📂getting-started
 ┃ ┃ ┗ 📜quick-start.md
 ┃ ┣ 📜COLOR_SYSTEM_DOCUMENTATION.md
 ┃ ┣ 📜OPTIONAL_DEPENDENCIES.md
 ┃ ┣ 📜README.md
 ┃ ┗ 📜TIMESTAMP_FORMATS.md
 ┣ 📂examples
 ┃ ┣ 📜my_config.yaml
 ┃ ┣ 📜simple_usage.py
 ┃ ┗ 📜timestamp_formats.py
 ┣ 📂hydra_logger
 ┃ ┣ 📂__pycache__
 ┃ ┃ ┗ 📜__init__.cpython-38.pyc
 ┃ ┣ 📂config
 ┃ ┃ ┣ 📂__pycache__
 ┃ ┃ ┃ ┣ 📜__init__.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜builder.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜defaults.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜exporters.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜loaders.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜magic_configs.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜models.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜setup.cpython-38.pyc
 ┃ ┃ ┃ ┗ 📜validators.cpython-38.pyc
 ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┣ 📜builder.py
 ┃ ┃ ┣ 📜defaults.py
 ┃ ┃ ┣ 📜exporters.py
 ┃ ┃ ┣ 📜loaders.py
 ┃ ┃ ┣ 📜magic_configs.py
 ┃ ┃ ┣ 📜models.py
 ┃ ┃ ┣ 📜setup.py
 ┃ ┃ ┗ 📜validators.py
 ┃ ┣ 📂core
 ┃ ┃ ┣ 📂__pycache__
 ┃ ┃ ┃ ┣ 📜__init__.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜cache_manager.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜constants.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜exceptions.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜layer_manager.cpython-38.pyc
 ┃ ┃ ┃ ┗ 📜logger_manager.cpython-38.pyc
 ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┣ 📜base.py
 ┃ ┃ ┣ 📜batch_processor.py
 ┃ ┃ ┣ 📜cache_manager.py
 ┃ ┃ ┣ 📜compiled_logging.py
 ┃ ┃ ┣ 📜composition.py
 ┃ ┃ ┣ 📜constants.py
 ┃ ┃ ┣ 📜decorators.py
 ┃ ┃ ┣ 📜exceptions.py
 ┃ ┃ ┣ 📜layer_manager.py
 ┃ ┃ ┣ 📜lifecycle.py
 ┃ ┃ ┣ 📜logger_manager.py
 ┃ ┃ ┣ 📜memory_optimizer.py
 ┃ ┃ ┣ 📜mixins.py
 ┃ ┃ ┣ 📜object_pool.py
 ┃ ┃ ┣ 📜parallel_processor.py
 ┃ ┃ ┣ 📜safeguards.py
 ┃ ┃ ┣ 📜system_optimizer.py
 ┃ ┃ ┣ 📜test_orchestrator.py
 ┃ ┃ ┣ 📜traits.py
 ┃ ┃ ┗ 📜validation.py
 ┃ ┣ 📂factories
 ┃ ┃ ┣ 📂__pycache__
 ┃ ┃ ┃ ┣ 📜__init__.cpython-38.pyc
 ┃ ┃ ┃ ┗ 📜logger_factory.cpython-38.pyc
 ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┗ 📜logger_factory.py
 ┃ ┣ 📂formatters
 ┃ ┃ ┣ 📂__pycache__
 ┃ ┃ ┃ ┣ 📜__init__.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜base.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜binary.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜color.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜json.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜standard_formats.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜structured.cpython-38.pyc
 ┃ ┃ ┃ ┗ 📜text.cpython-38.pyc
 ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┣ 📜base.py
 ┃ ┃ ┣ 📜binary.py
 ┃ ┃ ┣ 📜color.py
 ┃ ┃ ┣ 📜json.py
 ┃ ┃ ┣ 📜standard_formats.py
 ┃ ┃ ┣ 📜structured.py
 ┃ ┃ ┗ 📜text.py
 ┃ ┣ 📂handlers
 ┃ ┃ ┣ 📂__pycache__
 ┃ ┃ ┃ ┣ 📜__init__.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜base.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜cloud.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜composite.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜console.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜database.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜file.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜network.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜null.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜queue.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜rotating.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜stream.cpython-38.pyc
 ┃ ┃ ┃ ┗ 📜system.cpython-38.pyc
 ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┣ 📜base.py
 ┃ ┃ ┣ 📜cloud.py
 ┃ ┃ ┣ 📜composite.py
 ┃ ┃ ┣ 📜console.py
 ┃ ┃ ┣ 📜database.py
 ┃ ┃ ┣ 📜file.py
 ┃ ┃ ┣ 📜manager.py
 ┃ ┃ ┣ 📜network.py
 ┃ ┃ ┣ 📜null.py
 ┃ ┃ ┣ 📜queue.py
 ┃ ┃ ┣ 📜rotating.py
 ┃ ┃ ┣ 📜stream.py
 ┃ ┃ ┗ 📜system.py
 ┃ ┣ 📂interfaces
 ┃ ┃ ┣ 📂__pycache__
 ┃ ┃ ┃ ┣ 📜__init__.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜config.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜formatter.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜handler.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜lifecycle.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜logger.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜monitor.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜plugin.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜registry.cpython-38.pyc
 ┃ ┃ ┃ ┗ 📜security.cpython-38.pyc
 ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┣ 📜config.py
 ┃ ┃ ┣ 📜formatter.py
 ┃ ┃ ┣ 📜handler.py
 ┃ ┃ ┣ 📜lifecycle.py
 ┃ ┃ ┣ 📜logger.py
 ┃ ┃ ┣ 📜monitor.py
 ┃ ┃ ┣ 📜plugin.py
 ┃ ┃ ┣ 📜registry.py
 ┃ ┃ ┗ 📜security.py
 ┃ ┣ 📂loggers
 ┃ ┃ ┣ 📂__pycache__
 ┃ ┃ ┃ ┣ 📜__init__.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜async_logger.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜base.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜composite_logger.cpython-38.pyc
 ┃ ┃ ┃ ┗ 📜sync_logger.cpython-38.pyc
 ┃ ┃ ┣ 📂adapters
 ┃ ┃ ┃ ┗ 📜__init__.py
 ┃ ┃ ┣ 📂engines
 ┃ ┃ ┃ ┣ 📂__pycache__
 ┃ ┃ ┃ ┃ ┣ 📜__init__.cpython-38.pyc
 ┃ ┃ ┃ ┃ ┣ 📜monitoring_engine.cpython-38.pyc
 ┃ ┃ ┃ ┃ ┗ 📜plugin_engine.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┃ ┣ 📜monitoring_engine.py
 ┃ ┃ ┃ ┣ 📜plugin_engine.py
 ┃ ┃ ┃ ┗ 📜security_engine.py
 ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┣ 📜async_logger.py
 ┃ ┃ ┣ 📜base.py
 ┃ ┃ ┣ 📜composite_logger.py
 ┃ ┃ ┗ 📜sync_logger.py
 ┃ ┣ 📂monitoring
 ┃ ┃ ┣ 📂__pycache__
 ┃ ┃ ┃ ┣ 📜__init__.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜adaptive_performance.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜alerts.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜auto_optimization.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜dashboard.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜health.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜memory.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜metrics.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜performance.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜performance_profiles.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜profiling.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜reporting.cpython-38.pyc
 ┃ ┃ ┃ ┗ 📜resource_management.cpython-38.pyc
 ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┣ 📜adaptive_performance.py
 ┃ ┃ ┣ 📜alerts.py
 ┃ ┃ ┣ 📜auto_optimization.py
 ┃ ┃ ┣ 📜dashboard.py
 ┃ ┃ ┣ 📜health.py
 ┃ ┃ ┣ 📜memory.py
 ┃ ┃ ┣ 📜metrics.py
 ┃ ┃ ┣ 📜performance.py
 ┃ ┃ ┣ 📜performance_monitoring.py
 ┃ ┃ ┣ 📜performance_profiles.py
 ┃ ┃ ┣ 📜profiling.py
 ┃ ┃ ┣ 📜reporting.py
 ┃ ┃ ┗ 📜resource_management.py
 ┃ ┣ 📂plugins
 ┃ ┃ ┣ 📂__pycache__
 ┃ ┃ ┃ ┣ 📜__init__.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜analyzer.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜base.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜discovery.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜manager.cpython-38.pyc
 ┃ ┃ ┃ ┗ 📜registry.cpython-38.pyc
 ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┣ 📜analyzer.py
 ┃ ┃ ┣ 📜base.py
 ┃ ┃ ┣ 📜discovery.py
 ┃ ┃ ┣ 📜manager.py
 ┃ ┃ ┗ 📜registry.py
 ┃ ┣ 📂registry
 ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┣ 📜compatibility.py
 ┃ ┃ ┣ 📜component_registry.py
 ┃ ┃ ┣ 📜discovery.py
 ┃ ┃ ┣ 📜formatter_registry.py
 ┃ ┃ ┣ 📜handler_registry.py
 ┃ ┃ ┣ 📜lifecycle.py
 ┃ ┃ ┣ 📜metadata.py
 ┃ ┃ ┣ 📜plugin_registry.py
 ┃ ┃ ┗ 📜versioning.py
 ┃ ┣ 📂security
 ┃ ┃ ┣ 📂__pycache__
 ┃ ┃ ┃ ┣ 📜__init__.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜access_control.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜audit.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜background_processing.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜compliance.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜crypto.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜encryption.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜hasher.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜redaction.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜sanitizer.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜threat_detection.cpython-38.pyc
 ┃ ┃ ┃ ┗ 📜validator.cpython-38.pyc
 ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┣ 📜access_control.py
 ┃ ┃ ┣ 📜audit.py
 ┃ ┃ ┣ 📜background_processing.py
 ┃ ┃ ┣ 📜compliance.py
 ┃ ┃ ┣ 📜crypto.py
 ┃ ┃ ┣ 📜encryption.py
 ┃ ┃ ┣ 📜hasher.py
 ┃ ┃ ┣ 📜performance_levels.py
 ┃ ┃ ┣ 📜redaction.py
 ┃ ┃ ┣ 📜sanitizer.py
 ┃ ┃ ┣ 📜threat_detection.py
 ┃ ┃ ┗ 📜validator.py
 ┃ ┣ 📂types
 ┃ ┃ ┣ 📂__pycache__
 ┃ ┃ ┃ ┣ 📜__init__.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜context.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜enums.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜events.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜formatters.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜handlers.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜levels.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜metadata.cpython-38.pyc
 ┃ ┃ ┃ ┗ 📜records.cpython-38.pyc
 ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┣ 📜context.py
 ┃ ┃ ┣ 📜enums.py
 ┃ ┃ ┣ 📜events.py
 ┃ ┃ ┣ 📜formatters.py
 ┃ ┃ ┣ 📜handlers.py
 ┃ ┃ ┣ 📜levels.py
 ┃ ┃ ┣ 📜metadata.py
 ┃ ┃ ┣ 📜plugins.py
 ┃ ┃ ┗ 📜records.py
 ┃ ┣ 📂utils
 ┃ ┃ ┣ 📂__pycache__
 ┃ ┃ ┃ ┣ 📜__init__.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜async_utils.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜caching.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜compression.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜debugging.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜file.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜helpers.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜network.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜serialization.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜sync_utils.cpython-38.pyc
 ┃ ┃ ┃ ┣ 📜text.cpython-38.pyc
 ┃ ┃ ┃ ┗ 📜time.cpython-38.pyc
 ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┣ 📜async_utils.py
 ┃ ┃ ┣ 📜caching.py
 ┃ ┃ ┣ 📜compression.py
 ┃ ┃ ┣ 📜debugging.py
 ┃ ┃ ┣ 📜file.py
 ┃ ┃ ┣ 📜helpers.py
 ┃ ┃ ┣ 📜network.py
 ┃ ┃ ┣ 📜serialization.py
 ┃ ┃ ┣ 📜sync_utils.py
 ┃ ┃ ┣ 📜text.py
 ┃ ┃ ┗ 📜time.py
 ┃ ┗ 📜__init__.py
 ┣ 📂logs
 ┣ 📂tests
 ┃ ┣ 📂compatibility
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂coverage
 ┃ ┃ ┣ 📜.gitignore
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂docs
 ┃ ┃ ┣ ...
 ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┣ 📜data_fixtures.py
 ┃ ┃ ┣ 📜logger_fixtures.py
 ┃ ┃ ┗ 📜performance_fixtures.py
 ┃ ┣ 📂integration
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂performance
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂regression
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂security
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂stress
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂unit
 ┃ ┃ ┣ 📂config
 ┃ ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┃ ┣ 📜test_loaders.py
 ┃ ┃ ┃ ┗ 📜test_validators.py
 ┃ ┃ ┣ 📂core
 ┃ ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┃ ┣ 📜test_base.py
 ┃ ┃ ┃ ┣ 📜test_lifecycle.py
 ┃ ┃ ┃ ┗ 📜test_validation.py
 ┃ ┃ ┣ 📂factories
 ┃ ┃ ┃ ┗ 📜__init__.py
 ┃ ┃ ┣ 📂formatters
 ┃ ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┃ ┣ 📜test_json.py
 ┃ ┃ ┃ ┗ 📜test_text.py
 ┃ ┃ ┣ 📂handlers
 ┃ ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┃ ┣ 📜test_console.py
 ┃ ┃ ┃ ┣ 📜test_file.py
 ┃ ┃ ┃ ┗ 📜test_rotating.py
 ┃ ┃ ┣ 📂interfaces
 ┃ ┃ ┃ ┗ 📜__init__.py
 ┃ ┃ ┣ 📂loggers
 ┃ ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┃ ┗ 📜test_base.py
 ┃ ┃ ┣ 📂monitoring
 ┃ ┃ ┃ ┗ 📜__init__.py
 ┃ ┃ ┣ 📂plugins
 ┃ ┃ ┃ ┗ 📜__init__.py
 ┃ ┃ ┣ 📂registry
 ┃ ┃ ┃ ┗ 📜__init__.py
 ┃ ┃ ┣ 📂security
 ┃ ┃ ┃ ┗ 📜__init__.py
 ┃ ┃ ┣ 📂types
 ┃ ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┃ ┣ 📜test_context.py
 ┃ ┃ ┃ ┣ 📜test_enums.py
 ┃ ┃ ┃ ┣ 📜test_events.py
 ┃ ┃ ┃ ┣ 📜test_levels.py
 ┃ ┃ ┃ ┗ 📜test_records.py
 ┃ ┃ ┣ 📂utils
 ┃ ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┃ ┗ 📜test_time.py
 ┃ ┃ ┗ 📜__init__.py
 ┃ ┣ 📂utils
 ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┗ 📜helpers.py
 ┃ ┣ 📂validation
 ┃ ┃ ┣ 📜__init__.py
 ┃ ┃ ┣ 📜test_async_validation.py
 ┃ ┃ ┣ 📜test_safeguards.py
 ┃ ┃ ┗ 📜test_sync_validation.py
 ┃ ┣ 📜README.md
 ┃ ┣ 📜TESTS_COV_PLAN.md
 ┃ ┣ 📜__init__.py
 ┃ ┣ 📜conftest.py
 ┃ ┣ 📜pytest.ini
 ┃ ┗ 📜run_hydra_tests.py
 ┣ 📜.gitignore
 ┣ 📜LICENSE
 ┣ 📜check_coverage.py
 ┣ 📜environment.yml
 ┣ 📜requirements-dev.txt
 ┣ 📜requirements.txt
 ┗ 📜setup.py