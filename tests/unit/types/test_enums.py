"""
Tests for hydra_logger.types.enums module.

This module tests all enum utility functions and enum classes.
"""

import pytest
from enum import Enum
from hydra_logger.types.enums import (
    HandlerType, FormatterType, PluginType, LogLayer, SecurityLevel,
    QueuePolicy, ShutdownPhase, RotationStrategy, CompressionType, 
    EncryptionType, NetworkProtocol, DatabaseType, CloudProvider,
    LogFormat, ColorMode, ValidationLevel, MonitoringLevel, ErrorHandling,
    AsyncMode, CacheStrategy, BackupStrategy, HealthCheckType, AlertSeverity,
    MetricType, TimeUnit, SizeUnit,
    get_enum_values, get_enum_names, get_enum_by_value, get_enum_by_name,
    is_valid_enum_value, is_valid_enum_name
)


class TestEnumUtilityFunctions:
    """Test enum utility functions."""
    
    def test_get_enum_values(self):
        """Test get_enum_values function."""
        values = get_enum_values(HandlerType)
        expected_values = ['console', 'file', 'stream', 'rotating', 'network', 'system', 'database', 'queue', 'cloud', 'composite', 'fallback', 'custom']
        assert values == expected_values
        
        values = get_enum_values(LogFormat)
        expected_values = ['plain', 'json', 'json_lines', 'csv', 'xml', 'yaml', 'toml', 'ini']
        assert values == expected_values
    
    def test_get_enum_names(self):
        """Test get_enum_names function."""
        names = get_enum_names(HandlerType)
        expected_names = ['CONSOLE', 'FILE', 'STREAM', 'ROTATING', 'NETWORK', 'SYSTEM', 'DATABASE', 'QUEUE', 'CLOUD', 'COMPOSITE', 'FALLBACK', 'CUSTOM']
        assert names == expected_names
        
        names = get_enum_names(LogFormat)
        expected_names = ['PLAIN', 'JSON', 'JSON_LINES', 'CSV', 'XML', 'YAML', 'TOML', 'INI']
        assert names == expected_names
    
    def test_get_enum_by_value_success(self):
        """Test get_enum_by_value function with valid values."""
        # Test HandlerType
        assert get_enum_by_value(HandlerType, 'console') == HandlerType.CONSOLE
        assert get_enum_by_value(HandlerType, 'file') == HandlerType.FILE
        
        # Test LogFormat
        assert get_enum_by_value(LogFormat, 'json') == LogFormat.JSON
        assert get_enum_by_value(LogFormat, 'plain') == LogFormat.PLAIN
    
    def test_get_enum_by_value_not_found(self):
        """Test get_enum_by_value function with invalid values."""
        assert get_enum_by_value(HandlerType, 'invalid') is None
        assert get_enum_by_value(LogFormat, 'invalid') is None
        assert get_enum_by_value(HandlerType, 123) is None
    
    def test_get_enum_by_name_success(self):
        """Test get_enum_by_name function with valid names."""
        # Test HandlerType
        assert get_enum_by_name(HandlerType, 'CONSOLE') == HandlerType.CONSOLE
        assert get_enum_by_name(HandlerType, 'FILE') == HandlerType.FILE
        
        # Test LogFormat
        assert get_enum_by_name(LogFormat, 'JSON') == LogFormat.JSON
        assert get_enum_by_name(LogFormat, 'PLAIN') == LogFormat.PLAIN
    
    def test_get_enum_by_name_not_found(self):
        """Test get_enum_by_name function with invalid names."""
        assert get_enum_by_name(HandlerType, 'INVALID') is None
        assert get_enum_by_name(LogFormat, 'INVALID') is None
        assert get_enum_by_name(HandlerType, '') is None
    
    def test_is_valid_enum_value_success(self):
        """Test is_valid_enum_value function with valid values."""
        # Test HandlerType
        assert is_valid_enum_value(HandlerType, 'console') is True
        assert is_valid_enum_value(HandlerType, 'file') is True
        
        # Test LogFormat
        assert is_valid_enum_value(LogFormat, 'json') is True
        assert is_valid_enum_value(LogFormat, 'plain') is True
    
    def test_is_valid_enum_value_invalid(self):
        """Test is_valid_enum_value function with invalid values."""
        # Test HandlerType
        assert is_valid_enum_value(HandlerType, 'invalid') is False
        assert is_valid_enum_value(HandlerType, 123) is False
        
        # Test LogFormat
        assert is_valid_enum_value(LogFormat, 'invalid') is False
        assert is_valid_enum_value(LogFormat, 123) is False
    
    def test_is_valid_enum_name_success(self):
        """Test is_valid_enum_name function with valid names."""
        # Test HandlerType
        assert is_valid_enum_name(HandlerType, 'CONSOLE') is True
        assert is_valid_enum_name(HandlerType, 'FILE') is True
        
        # Test LogFormat
        assert is_valid_enum_name(LogFormat, 'JSON') is True
        assert is_valid_enum_name(LogFormat, 'PLAIN') is True
    
    def test_is_valid_enum_name_invalid(self):
        """Test is_valid_enum_name function with invalid names."""
        # Test HandlerType
        assert is_valid_enum_name(HandlerType, 'INVALID') is False
        assert is_valid_enum_name(HandlerType, '') is False
        
        # Test LogFormat
        assert is_valid_enum_name(LogFormat, 'INVALID') is False
        assert is_valid_enum_name(LogFormat, '') is False


class TestHandlerTypeEnum:
    """Test HandlerType enum specifically."""
    
    def test_handler_type_values(self):
        """Test HandlerType enum values."""
        assert HandlerType.CONSOLE.value == 'console'
        assert HandlerType.FILE.value == 'file'
        assert HandlerType.STREAM.value == 'stream'
        assert HandlerType.NETWORK.value == 'network'
        assert HandlerType.DATABASE.value == 'database'
    
    def test_handler_type_names(self):
        """Test HandlerType enum names."""
        assert HandlerType.CONSOLE.name == 'CONSOLE'
        assert HandlerType.FILE.name == 'FILE'
        assert HandlerType.STREAM.name == 'STREAM'
        assert HandlerType.NETWORK.name == 'NETWORK'
        assert HandlerType.DATABASE.name == 'DATABASE'


class TestFormatterTypeEnum:
    """Test FormatterType enum specifically."""
    
    def test_formatter_type_values(self):
        """Test FormatterType enum values."""
        assert FormatterType.PLAIN_TEXT.value == 'plain_text'
        assert FormatterType.JSON.value == 'json'
        assert FormatterType.JSON_LINES.value == 'json_lines'
        assert FormatterType.CSV.value == 'csv'
        assert FormatterType.SYSLOG.value == 'syslog'
    
    def test_formatter_type_names(self):
        """Test FormatterType enum names."""
        assert FormatterType.PLAIN_TEXT.name == 'PLAIN_TEXT'
        assert FormatterType.JSON.name == 'JSON'
        assert FormatterType.JSON_LINES.name == 'JSON_LINES'
        assert FormatterType.CSV.name == 'CSV'
        assert FormatterType.SYSLOG.name == 'SYSLOG'


class TestLogFormatEnum:
    """Test LogFormat enum specifically."""
    
    def test_log_format_values(self):
        """Test LogFormat enum values."""
        assert LogFormat.PLAIN.value == 'plain'
        assert LogFormat.JSON.value == 'json'
        assert LogFormat.JSON_LINES.value == 'json_lines'
        assert LogFormat.CSV.value == 'csv'
        assert LogFormat.XML.value == 'xml'
        assert LogFormat.YAML.value == 'yaml'
    
    def test_log_format_names(self):
        """Test LogFormat enum names."""
        assert LogFormat.PLAIN.name == 'PLAIN'
        assert LogFormat.JSON.name == 'JSON'
        assert LogFormat.JSON_LINES.name == 'JSON_LINES'
        assert LogFormat.CSV.name == 'CSV'
        assert LogFormat.XML.name == 'XML'
        assert LogFormat.YAML.name == 'YAML'


class TestLogLayerEnum:
    """Test LogLayer enum specifically."""
    
    def test_log_layer_values(self):
        """Test LogLayer enum values."""
        assert LogLayer.DEFAULT.value == 'default'
        assert LogLayer.APP.value == 'APP'
        assert LogLayer.SYSTEM.value == 'SYSTEM'
        assert LogLayer.SECURITY.value == 'SECURITY'
        assert LogLayer.PERFORMANCE.value == 'PERFORMANCE'
    
    def test_log_layer_names(self):
        """Test LogLayer enum names."""
        assert LogLayer.DEFAULT.name == 'DEFAULT'
        assert LogLayer.APP.name == 'APP'
        assert LogLayer.SYSTEM.name == 'SYSTEM'
        assert LogLayer.SECURITY.name == 'SECURITY'
        assert LogLayer.PERFORMANCE.name == 'PERFORMANCE'


class TestSecurityLevelEnum:
    """Test SecurityLevel enum specifically."""
    
    def test_security_level_values(self):
        """Test SecurityLevel enum values."""
        assert SecurityLevel.NONE.value == 'none'
        assert SecurityLevel.BASIC.value == 'basic'
        assert SecurityLevel.STANDARD.value == 'standard'
        assert SecurityLevel.HIGH.value == 'high'
        assert SecurityLevel.MAXIMUM.value == 'maximum'
    
    def test_security_level_names(self):
        """Test SecurityLevel enum names."""
        assert SecurityLevel.NONE.name == 'NONE'
        assert SecurityLevel.BASIC.name == 'BASIC'
        assert SecurityLevel.STANDARD.name == 'STANDARD'
        assert SecurityLevel.HIGH.name == 'HIGH'
        assert SecurityLevel.MAXIMUM.name == 'MAXIMUM'


class TestCompressionTypeEnum:
    """Test CompressionType enum specifically."""
    
    def test_compression_type_values(self):
        """Test CompressionType enum values."""
        assert CompressionType.NONE.value == 'none'
        assert CompressionType.GZIP.value == 'gzip'
        assert CompressionType.BZIP2.value == 'bzip2'
        assert CompressionType.LZMA.value == 'lzma'
        assert CompressionType.ZSTD.value == 'zstd'
    
    def test_compression_type_names(self):
        """Test CompressionType enum names."""
        assert CompressionType.NONE.name == 'NONE'
        assert CompressionType.GZIP.name == 'GZIP'
        assert CompressionType.BZIP2.name == 'BZIP2'
        assert CompressionType.LZMA.name == 'LZMA'
        assert CompressionType.ZSTD.name == 'ZSTD'


class TestEncryptionTypeEnum:
    """Test EncryptionType enum specifically."""
    
    def test_encryption_type_values(self):
        """Test EncryptionType enum values."""
        assert EncryptionType.NONE.value == 'none'
        assert EncryptionType.AES.value == 'aes'
        assert EncryptionType.RSA.value == 'rsa'
        assert EncryptionType.CHACHA20.value == 'chacha20'
    
    def test_encryption_type_names(self):
        """Test EncryptionType enum names."""
        assert EncryptionType.NONE.name == 'NONE'
        assert EncryptionType.AES.name == 'AES'
        assert EncryptionType.RSA.name == 'RSA'
        assert EncryptionType.CHACHA20.name == 'CHACHA20'


class TestEnumIntegration:
    """Test enum integration and edge cases."""
    
    def test_enum_iteration(self):
        """Test iterating over enum classes."""
        handler_types = list(HandlerType)
        assert len(handler_types) == 12
        assert HandlerType.CONSOLE in handler_types
        assert HandlerType.FILE in handler_types
        
        log_formats = list(LogFormat)
        assert len(log_formats) == 8
        assert LogFormat.PLAIN in log_formats
        assert LogFormat.JSON_LINES in log_formats
    
    def test_enum_membership(self):
        """Test enum membership testing."""
        assert HandlerType.CONSOLE in HandlerType
        assert LogFormat.JSON in LogFormat
        assert LogLayer.DEFAULT in LogLayer
    
    def test_enum_string_conversion(self):
        """Test enum string conversion."""
        assert str(HandlerType.CONSOLE) == 'HandlerType.CONSOLE'
        assert str(LogFormat.JSON) == 'LogFormat.JSON'
        assert repr(HandlerType.CONSOLE) == "<HandlerType.CONSOLE: 'console'>"
        assert repr(LogFormat.JSON) == "<LogFormat.JSON: 'json'>"
    
    def test_enum_equality(self):
        """Test enum equality."""
        assert HandlerType.CONSOLE == HandlerType.CONSOLE
        assert HandlerType.CONSOLE != HandlerType.FILE
        assert LogFormat.JSON == LogFormat.JSON
        assert LogFormat.JSON != LogFormat.PLAIN
    
    def test_enum_hash(self):
        """Test enum hashing."""
        # Enums should be hashable
        enum_set = {HandlerType.CONSOLE, HandlerType.FILE, HandlerType.STREAM}
        assert len(enum_set) == 3
        assert HandlerType.CONSOLE in enum_set
        
        enum_dict = {HandlerType.CONSOLE: 'console', HandlerType.FILE: 'file'}
        assert enum_dict[HandlerType.CONSOLE] == 'console'


class TestAdditionalEnums:
    """Test additional enum types."""
    
    def test_plugin_type_enum(self):
        """Test PluginType enum."""
        assert PluginType.ANALYTICS.value == 'analytics'
        assert PluginType.SECURITY.value == 'security'
        assert PluginType.PERFORMANCE.value == 'performance'
        assert PluginType.MONITORING.value == 'monitoring'
    
    def test_queue_policy_enum(self):
        """Test QueuePolicy enum."""
        assert QueuePolicy.DROP_OLDEST.value == 'drop_oldest'
        assert QueuePolicy.BLOCK.value == 'block'
        assert QueuePolicy.ERROR.value == 'error'
        assert QueuePolicy.RETRY.value == 'retry'
    
    def test_shutdown_phase_enum(self):
        """Test ShutdownPhase enum."""
        assert ShutdownPhase.RUNNING.value == 'running'
        assert ShutdownPhase.FLUSHING.value == 'flushing'
        assert ShutdownPhase.CLEANING.value == 'cleaning'
        assert ShutdownPhase.DONE.value == 'done'
    
    def test_rotation_strategy_enum(self):
        """Test RotationStrategy enum."""
        assert RotationStrategy.SIZE.value == 'size'
        assert RotationStrategy.TIME.value == 'time'
        assert RotationStrategy.HYBRID.value == 'hybrid'
        assert RotationStrategy.MANUAL.value == 'manual'
    
    def test_network_protocol_enum(self):
        """Test NetworkProtocol enum."""
        assert NetworkProtocol.TCP.value == 'tcp'
        assert NetworkProtocol.UDP.value == 'udp'
        assert NetworkProtocol.HTTP.value == 'http'
        assert NetworkProtocol.HTTPS.value == 'https'
    
    def test_database_type_enum(self):
        """Test DatabaseType enum."""
        assert DatabaseType.SQLITE.value == 'sqlite'
        assert DatabaseType.POSTGRESQL.value == 'postgresql'
        assert DatabaseType.MYSQL.value == 'mysql'
        assert DatabaseType.MONGODB.value == 'mongodb'
    
    def test_cloud_provider_enum(self):
        """Test CloudProvider enum."""
        assert CloudProvider.AWS.value == 'aws'
        assert CloudProvider.GCP.value == 'gcp'
        assert CloudProvider.AZURE.value == 'azure'
        assert CloudProvider.DIGITALOCEAN.value == 'digitalocean'
        assert CloudProvider.HEROKU.value == 'heroku'
    
    def test_color_mode_enum(self):
        """Test ColorMode enum."""
        assert ColorMode.AUTO.value == 'auto'
        assert ColorMode.ALWAYS.value == 'always'
        assert ColorMode.NEVER.value == 'never'
    
    def test_validation_level_enum(self):
        """Test ValidationLevel enum."""
        assert ValidationLevel.NONE.value == 'none'
        assert ValidationLevel.BASIC.value == 'basic'
        assert ValidationLevel.STRICT.value == 'strict'
    
    def test_monitoring_level_enum(self):
        """Test MonitoringLevel enum."""
        assert MonitoringLevel.NONE.value == 'none'
        assert MonitoringLevel.BASIC.value == 'basic'
        assert MonitoringLevel.DETAILED.value == 'detailed'
        assert MonitoringLevel.VERBOSE.value == 'verbose'
    
    def test_error_handling_enum(self):
        """Test ErrorHandling enum."""
        assert ErrorHandling.IGNORE.value == 'ignore'
        assert ErrorHandling.LOG.value == 'log'
        assert ErrorHandling.RAISE.value == 'raise'
    
    def test_async_mode_enum(self):
        """Test AsyncMode enum."""
        assert AsyncMode.SYNC.value == 'sync'
        assert AsyncMode.ASYNC.value == 'async'
        assert AsyncMode.AUTO.value == 'auto'
    
    def test_cache_strategy_enum(self):
        """Test CacheStrategy enum."""
        assert CacheStrategy.NONE.value == 'none'
        assert CacheStrategy.MEMORY.value == 'memory'
        assert CacheStrategy.DISK.value == 'disk'
        assert CacheStrategy.HYBRID.value == 'hybrid'
        assert CacheStrategy.DISTRIBUTED.value == 'distributed'
    
    def test_backup_strategy_enum(self):
        """Test BackupStrategy enum."""
        assert BackupStrategy.NONE.value == 'none'
        assert BackupStrategy.COPY.value == 'copy'
        assert BackupStrategy.MOVE.value == 'move'
        assert BackupStrategy.COMPRESS.value == 'compress'
        assert BackupStrategy.ENCRYPT.value == 'encrypt'
    
    def test_health_check_type_enum(self):
        """Test HealthCheckType enum."""
        assert HealthCheckType.BASIC.value == 'basic'
        assert HealthCheckType.COMPREHENSIVE.value == 'comprehensive'
        assert HealthCheckType.PERFORMANCE.value == 'performance'
        assert HealthCheckType.SECURITY.value == 'security'
        assert HealthCheckType.INTEGRATION.value == 'integration'
    
    def test_alert_severity_enum(self):
        """Test AlertSeverity enum."""
        assert AlertSeverity.INFO.value == 'info'
        assert AlertSeverity.WARNING.value == 'warning'
        assert AlertSeverity.ERROR.value == 'error'
        assert AlertSeverity.CRITICAL.value == 'critical'
    
    def test_metric_type_enum(self):
        """Test MetricType enum."""
        assert MetricType.COUNTER.value == 'counter'
        assert MetricType.GAUGE.value == 'gauge'
        assert MetricType.HISTOGRAM.value == 'histogram'
        assert MetricType.SUMMARY.value == 'summary'
    
    def test_time_unit_enum(self):
        """Test TimeUnit enum."""
        assert TimeUnit.NANOSECONDS.value == 'ns'
        assert TimeUnit.MICROSECONDS.value == 'μs'
        assert TimeUnit.MILLISECONDS.value == 'ms'
        assert TimeUnit.SECONDS.value == 'seconds'
        assert TimeUnit.MINUTES.value == 'minutes'
        assert TimeUnit.HOURS.value == 'hours'
        assert TimeUnit.DAYS.value == 'days'
        assert TimeUnit.WEEKS.value == 'weeks'
        assert TimeUnit.MONTHS.value == 'months'
        assert TimeUnit.YEARS.value == 'years'
    
    def test_size_unit_enum(self):
        """Test SizeUnit enum."""
        assert SizeUnit.BYTES.value == 'B'
        assert SizeUnit.KILOBYTES.value == 'KB'
        assert SizeUnit.MEGABYTES.value == 'MB'
        assert SizeUnit.GIGABYTES.value == 'GB'
        assert SizeUnit.TERABYTES.value == 'TB'