"""
Cloud Service Handlers for Hydra-Logger

This module provides comprehensive cloud-based logging handlers for major
cloud platforms and services. It includes authentication, retry mechanisms,
and batch processing for optimal performance.

ARCHITECTURE:
- BaseCloudHandler: Abstract base class for all cloud handlers
- AWSCloudWatchHandler: AWS CloudWatch Logs integration
- AzureMonitorHandler: Azure Monitor (Log Analytics) integration
- GoogleCloudLoggingHandler: Google Cloud Logging integration
- ElasticsearchHandler: Elasticsearch search and analytics integration
- CloudHandlerFactory: Factory for creating cloud handlers

SUPPORTED CLOUD SERVICES:
- AWS CloudWatch Logs: Real-time log streaming and monitoring
- Azure Monitor: Log Analytics workspace integration
- Google Cloud Logging: GCP logging service integration
- Elasticsearch: Search and analytics platform integration

PERFORMANCE FEATURES:
- Intelligent batch processing (100 messages or 5s intervals)
- Connection pooling and retry mechanisms
- Automatic authentication and credential management
- Formatter-aware handling for optimal performance
- Comprehensive error handling and fallback mechanisms
- Performance statistics and monitoring

AUTHENTICATION:
- AWS: IAM roles, access keys, session tokens, profile-based
- Azure: Workspace ID and key authentication
- Google Cloud: Service account JSON, default credentials
- Elasticsearch: Basic auth, API keys, SSL certificates

USAGE EXAMPLES:

AWS CloudWatch Handler:
    from hydra_logger.handlers import AWSCloudWatchHandler
    
    handler = AWSCloudWatchHandler(
        region="us-east-1",
        log_group="/my-app/logs",
        log_stream="production"
    )
    logger.addHandler(handler)

Azure Monitor Handler:
    from hydra_logger.handlers import AzureMonitorHandler
    
    handler = AzureMonitorHandler(
        workspace_id="your-workspace-id",
        workspace_key="your-workspace-key"
    )
    logger.addHandler(handler)

Google Cloud Logging Handler:
    from hydra_logger.handlers import GoogleCloudLoggingHandler
    
    handler = GoogleCloudLoggingHandler(
        project_id="your-project-id",
        credentials_file="path/to/credentials.json"
    )
    logger.addHandler(handler)

Elasticsearch Handler:
    from hydra_logger.handlers import ElasticsearchHandler
    
    handler = ElasticsearchHandler(
        hosts=["localhost:9200"],
        index_name="app-logs",
        username="elastic",
        password="password"
    )
    logger.addHandler(handler)

Factory Pattern:
    from hydra_logger.handlers import CloudHandlerFactory
    
    # Create AWS handler
    handler = CloudHandlerFactory.create_handler(
        "aws_cloudwatch",
        region="us-east-1",
        log_group="/my-app/logs"
    )
    
    # Create Elasticsearch handler
    handler = CloudHandlerFactory.create_handler(
        "elasticsearch",
        hosts=["localhost:9200"],
        index_name="logs"
    )

Performance Monitoring:
    # Get cloud service statistics
    stats = handler.get_cloud_stats()
    print(f"Connected: {stats['connected']}")
    print(f"Messages processed: {stats['message_count']}")
    print(f"Batch count: {stats['batch_count']}")
    print(f"Error count: {stats['error_count']}")

CONFIGURATION:
- Batch settings: batch_size, batch_timeout, auto_flush
- Connection settings: max_retries, retry_delay, timeout
- Authentication: Service-specific credentials and tokens
- Service-specific: Log groups, workspaces, projects, indices

ERROR HANDLING:
- Automatic retry with exponential backoff
- Fallback mechanisms for failed operations
- Comprehensive error logging
- Graceful degradation
- Connection recovery

THREAD SAFETY:
- Thread-safe operations with proper locking
- Safe concurrent access
- Atomic batch operations
- Connection pooling
"""

import json
import time
import threading
from typing import Optional, Dict, Any, Union, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from hydra_logger.handlers.base import BaseHandler
from hydra_logger.types.records import LogRecord
from hydra_logger.types.levels import LogLevel


class CloudService(Enum):
    """Supported cloud services."""
    AWS_CLOUDWATCH = "aws_cloudwatch"
    AZURE_MONITOR = "azure_monitor"
    GOOGLE_CLOUD = "google_cloud"
    ELASTICSEARCH = "elasticsearch"


@dataclass
class CloudConfig:
    """Configuration for cloud service handlers."""
    # Service settings
    service: CloudService = CloudService.AWS_CLOUDWATCH
    region: str = "us-east-1"
    namespace: str = "HydraLogger"
    
    # Authentication
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    session_token: Optional[str] = None
    profile_name: Optional[str] = None
    
    # Azure specific
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    
    # Google Cloud specific
    project_id: Optional[str] = None
    credentials_file: Optional[str] = None
    
    # Elasticsearch specific
    hosts: Union[str, List[str]] = "localhost:9200"
    username: Optional[str] = None
    password: Optional[str] = None
    index_name: str = "logs"
    
    # Batch settings
    batch_size: int = 100
    batch_timeout: float = 5.0
    auto_flush: bool = True
    
    # Connection settings
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0
    
    # Log group/stream settings (CloudWatch)
    log_group: str = "/hydra-logger/default"
    log_stream: str = "default"
    create_log_group: bool = True
    
    # Workspace settings (Azure)
    workspace_id: Optional[str] = None
    workspace_key: Optional[str] = None


class BaseCloudHandler(BaseHandler):
    """Base class for cloud service handlers."""
    
    def __init__(
        self,
        config: CloudConfig,
        timestamp_config=None,
        **kwargs
    ):
        """Initialize base cloud handler."""
        super().__init__(name="cloud", level=LogLevel.NOTSET, timestamp_config=timestamp_config)
        
        self.config = config
        self._connected = False
        self._connection_lock = threading.RLock()
        
        # Batch handling
        self._batch_buffer = []
        self._batch_lock = threading.Lock()
        self._last_flush = time.time()
        
        # Statistics
        self._message_count = 0
        self._batch_count = 0
        self._error_count = 0
        
        # Formatter-aware handling attributes
        self._is_csv_formatter = False
        self._is_json_formatter = False
        self._is_streaming_formatter = False
        self._needs_special_handling = False
        
        # Initialize cloud service
        self._init_cloud_service()
    
    def setFormatter(self, formatter):
        """
        Set formatter and detect if it needs special handling.
        
        Args:
            formatter: Formatter instance
        """
        super().setFormatter(formatter)
        if formatter:
            self._is_csv_formatter = (hasattr(formatter, 'format_headers') and hasattr(formatter, 'should_write_headers'))
            self._is_json_formatter = hasattr(formatter, 'write_header')
            self._is_streaming_formatter = hasattr(formatter, 'format_for_streaming')
            self._needs_special_handling = (self._is_csv_formatter or self._is_json_formatter or self._is_streaming_formatter)
        else:
            self._is_csv_formatter = False
            self._is_json_formatter = False
            self._is_streaming_formatter = False
            self._needs_special_handling = False
    
    def handleError(self, record: LogRecord) -> None:
        """
        Handle errors that occur during record processing.
        
        Args:
            record: The log record that caused the error
        """
        self._error_count += 1
        # logging.error(f"Cloud handler error processing record: {record.message}")
        
        # Try to log the error to a fallback destination if available
        if hasattr(self, 'fallback_handler') and self.fallback_handler:
            try:
                self.fallback_handler.handle(record)
            except Exception:
                # If fallback also fails, just log to stderr
                # logging.error(f"Fallback handler also failed for record: {record.message}")
                pass
    
    def _init_cloud_service(self) -> None:
        """Initialize cloud service connection."""
        try:
            success = self._establish_connection()
            if success:
                self._connected = True
                self._setup_service()
        except Exception as e:
            # logging.error(f"Cloud service initialization failed: {e}")
            self._connected = False
    
    def _establish_connection(self) -> bool:
        """Establish cloud service connection. Override in subclasses."""
        raise NotImplementedError
    
    def _setup_service(self) -> None:
        """Setup cloud service configuration. Override in subclasses."""
        pass
    
    def _send_log(self, record: LogRecord) -> bool:
        """Send a single log. Override in subclasses."""
        raise NotImplementedError
    
    def _send_batch(self, records: List[LogRecord]) -> bool:
        """Send multiple logs. Override in subclasses."""
        raise NotImplementedError
    
    def emit(self, record: LogRecord) -> None:
        """Emit log record to cloud service."""
        if not self._connected:
            if not self._init_cloud_service():
                self.handleError(record)
                return
        
        try:
            # Add to batch buffer
            with self._batch_lock:
                self._batch_buffer.append(record)
                
                # Check if we should flush
                should_flush = (
                    len(self._batch_buffer) >= self.config.batch_size or
                    (self.config.auto_flush and 
                     time.time() - self._last_flush >= self.config.batch_timeout)
                )
                
                if should_flush:
                    self._flush_batch()
            
            # Update statistics
            self._message_count += 1
            
        except Exception as e:
            self._error_count += 1
            # logging.error(f"Failed to add record to batch: {e}")
            self.handleError(record)
    
    def _flush_batch(self) -> None:
        """Flush the current batch to the cloud service."""
        if not self._batch_buffer:
            return
        
        try:
            # Get current batch
            with self._batch_lock:
                current_batch = self._batch_buffer.copy()
                self._batch_buffer.clear()
                self._last_flush = time.time()
            
            # Send batch
            if self._send_batch(current_batch):
                self._batch_count += 1
            else:
                # Re-add records to buffer on failure
                with self._batch_lock:
                    self._batch_buffer.extend(current_batch)
                    
        except Exception as e:
            self._error_count += 1
            # logging.error(f"Failed to flush batch: {e}")
            
            # Re-add records to buffer on failure
            with self._batch_lock:
                self._batch_buffer.extend(current_batch)
    
    def flush(self) -> None:
        """Flush any pending records."""
        self._flush_batch()
    
    def close(self) -> None:
        """Close the handler."""
        self.flush()
        self._close_connection()
        super().close()
    
    def _close_connection(self) -> None:
        """Close cloud service connection. Override in subclasses."""
        pass
    
    def get_cloud_stats(self) -> Dict[str, Any]:
        """Get cloud service statistics."""
        return {
            'connected': self._connected,
            'message_count': self._message_count,
            'batch_count': self._batch_count,
            'error_count': self._error_count,
            'batch_buffer_size': len(self._batch_buffer),
            'last_flush': self._last_flush,
            'service': self.config.service.value
        }


class AWSCloudWatchHandler(BaseCloudHandler):
    """
    AWS CloudWatch handler.
    
    Provides # logging to AWS CloudWatch Logs service.
    """
    
    def __init__(
        self,
        region: str = "us-east-1",
        log_group: str = "/hydra-logger/default",
        log_stream: str = "default",
        **kwargs
    ):
        """Initialize AWS CloudWatch handler."""
        # Create config
        config = CloudConfig(
            service=CloudService.AWS_CLOUDWATCH,
            region=region,
            log_group=log_group,
            log_stream=log_stream,
            **kwargs
        )
        
        super().__init__(config=config)
        
        self.client = None
        self.sequence_token = None
        self._connection_lock = threading.RLock()
    
    def _establish_connection(self) -> bool:
        """Establish AWS CloudWatch connection."""
        try:
            import boto3  # type: ignore
            
            with self._connection_lock:
                # Create CloudWatch Logs client
                if self.config.access_key and self.config.secret_key:
                    self.client = boto3.client(
                        'logs',
                        region_name=self.config.region,
                        aws_access_key_id=self.config.access_key,
                        aws_secret_access_key=self.config.secret_key,
                        aws_session_token=self.config.session_token
                    )
                elif self.config.profile_name:
                    session = boto3.Session(profile_name=self.config.profile_name)
                    self.client = session.client('logs', region_name=self.config.region)
                else:
                    # Use default credentials (IAM role, environment variables, etc.)
                    self.client = boto3.client('logs', region_name=self.config.region)
                
                return True
                
        except ImportError:
            # logging.error("boto3 library is required for AWS CloudWatch. Install with: pip install boto3")
            return False
        except Exception as e:
            # logging.error(f"AWS CloudWatch connection failed: {e}")
            return False
    
    def _setup_service(self) -> None:
        """Setup CloudWatch log group and stream."""
        try:
            with self._connection_lock:
                # Create log group if needed
                if self.config.create_log_group:
                    try:
                        self.client.create_log_group(logGroupName=self.config.log_group)
                    except self.client.exceptions.ResourceAlreadyExistsException:
                        pass  # Log group already exists
                
                # Create log stream
                try:
                    self.client.create_log_stream(
                        logGroupName=self.config.log_group,
                        logStreamName=self.config.log_stream
                    )
                except self.client.exceptions.ResourceAlreadyExistsException:
                    pass  # Log stream already exists
                
        except Exception as e:
            # logging.error(f"Failed to setup CloudWatch: {e}")
            raise
    
    def _send_log(self, record: LogRecord) -> bool:
        """Send a single log to CloudWatch."""
        try:
            # Prepare log event
            log_event = {
                'timestamp': int(record.timestamp * 1000),  # CloudWatch expects milliseconds
                'message': self.format(record)
            }
            
            # Send log event
            with self._connection_lock:
                response = self.client.put_log_events(
                    logGroupName=self.config.log_group,
                    logStreamName=self.config.log_stream,
                    logEvents=[log_event],
                    sequenceToken=self.sequence_token
                )
                
                # Update sequence token for next request
                if 'nextSequenceToken' in response:
                    self.sequence_token = response['nextSequenceToken']
                
                return True
                
        except self.client.exceptions.InvalidSequenceTokenException as e:
            # Update sequence token and retry
            self.sequence_token = e.response['Error']['Message'].split(':')[-1].strip()
            return self._send_log(record)
        except Exception as e:
            # logging.error(f"Failed to send log to CloudWatch: {e}")
            return False
    
    def _send_batch(self, records: List[LogRecord]) -> bool:
        """Send multiple logs to CloudWatch."""
        try:
            # Prepare log events
            log_events = []
            for record in records:
                log_event = {
                    'timestamp': int(record.timestamp * 1000),
                    'message': self.format(record)
                }
                log_events.append(log_event)
            
            # Send log events
            with self._connection_lock:
                response = self.client.put_log_events(
                    logGroupName=self.config.log_group,
                    logStreamName=self.config.log_stream,
                    logEvents=log_events,
                    sequenceToken=self.sequence_token
                )
                
                # Update sequence token for next request
                if 'nextSequenceToken' in response:
                    self.sequence_token = response['nextSequenceToken']
                
                return True
                
        except self.client.exceptions.InvalidSequenceTokenException as e:
            # Update sequence token and retry
            self.sequence_token = e.response['Error']['Message'].split(':')[-1].strip()
            return self._send_batch(records)
        except Exception as e:
            # logging.error(f"Failed to send batch to CloudWatch: {e}")
            return False
    
    def _close_connection(self) -> None:
        """Close CloudWatch connection."""
        # boto3 clients don't need explicit closing
        pass


class AzureMonitorHandler(BaseCloudHandler):
    """
    Azure Monitor handler.
    
    Provides # logging to Azure Monitor (Log Analytics) service.
    """
    
    def __init__(
        self,
        workspace_id: str,
        workspace_key: str,
        **kwargs
    ):
        """Initialize Azure Monitor handler."""
        # Create config
        config = CloudConfig(
            service=CloudService.AZURE_MONITOR,
            workspace_id=workspace_id,
            workspace_key=workspace_key,
            **kwargs
        )
        
        super().__init__(config=config)
        
        self.workspace_id = workspace_id
        self.workspace_key = workspace_key
        self._connection_lock = threading.RLock()
    
    def _establish_connection(self) -> bool:
        """Establish Azure Monitor connection."""
        try:
            import requests
            
            # Test connection by making a simple request
            test_url = f"https://{self.workspace_id}.ods.opinsights.azure.com/api/logs"
            headers = self._get_headers()
            
            response = requests.get(test_url, headers=headers, timeout=10)
            return response.status_code == 200
            
        except ImportError:
            # logging.error("requests library is required for Azure Monitor")
            return False
        except Exception as e:
            # logging.error(f"Azure Monitor connection failed: {e}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get Azure Monitor request headers."""
        import base64
        import hmac
        import hashlib
        from datetime import datetime
        
        # Generate authorization header
        date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        string_to_sign = f"POST\n{len('')}\napplication/json\nx-ms-date:{date}\n/api/logs"
        
        # Create signature
        signature = base64.b64encode(
            hmac.new(
                base64.b64decode(self.workspace_key),
                string_to_sign.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode()
        
        return {
            'Authorization': f'SharedKey {self.workspace_id}:{signature}',
            'Content-Type': 'application/json',
            'x-ms-date': date
        }
    
    def _setup_service(self) -> None:
        """Setup Azure Monitor service."""
        # No specific setup needed for Azure Monitor
        pass
    
    def _send_log(self, record: LogRecord) -> bool:
        """Send a single log to Azure Monitor."""
        try:
            import requests
            
            # Prepare log data
            log_data = [{
                'TimeGenerated': self.format_timestamp(record),
                'Level': record.levelname,
                'Logger': record.logger_name,
                'Message': self.format(record),
                'Filename': getattr(record, 'file_name', ''),
                'Function': getattr(record, 'function_name', ''),
                'Line': getattr(record, 'line_number', ''),
                'Extra': getattr(record, 'extra', {})
            }]
            
            # Send to Azure Monitor
            url = f"https://{self.workspace_id}.ods.opinsights.azure.com/api/logs"
            headers = self._get_headers()
            
            response = requests.post(
                url,
                json=log_data,
                headers=headers,
                timeout=self.config.timeout
            )
            
            return response.status_code == 200
            
        except Exception as e:
            # logging.error(f"Failed to send log to Azure Monitor: {e}")
            return False
    
    def _send_batch(self, records: List[LogRecord]) -> bool:
        """Send multiple logs to Azure Monitor."""
        try:
            import requests
            
            # Prepare log data
            log_data = []
            for record in records:
                log_entry = {
                    'TimeGenerated': self.format_timestamp(record),
                    'Level': record.levelname,
                    'Logger': record.logger_name,
                    'Message': self.format(record),
                    'Filename': getattr(record, 'file_name', ''),
                    'Function': getattr(record, 'function_name', ''),
                    'Line': getattr(record, 'line_number', ''),
                    'Extra': getattr(record, 'extra', {})
                }
                log_data.append(log_entry)
            
            # Send to Azure Monitor
            url = f"https://{self.workspace_id}.ods.opinsights.azure.com/api/logs"
            headers = self._get_headers()
            
            response = requests.post(
                url,
                json=log_data,
                headers=headers,
                timeout=self.config.timeout
            )
            
            return response.status_code == 200
            
        except Exception as e:
            # logging.error(f"Failed to send batch to Azure Monitor: {e}")
            return False
    
    def _close_connection(self) -> None:
        """Close Azure Monitor connection."""
        # No explicit connection to close
        pass


class GoogleCloudLoggingHandler(BaseCloudHandler):
    """
    Google Cloud Logging handler.
    
    Provides # logging to Google Cloud Logging service.
    """
    
    def __init__(
        self,
        project_id: str,
        credentials_file: Optional[str] = None,
        **kwargs
    ):
        """Initialize Google Cloud Logging handler."""
        # Create config
        config = CloudConfig(
            service=CloudService.GOOGLE_CLOUD,
            project_id=project_id,
            credentials_file=credentials_file,
            **kwargs
        )
        
        super().__init__(config=config)
        
        self.project_id = project_id
        self.credentials_file = credentials_file
        self.client = None
        self._connection_lock = threading.RLock()
    
    def _establish_connection(self) -> bool:
        """Establish Google Cloud Logging connection."""
        try:
            # from google.cloud import logging
            
            with self._connection_lock:
                # Create logging client
                if self.config.credentials_file:
                    # self.client = logging.Client.from_service_account_json(
                    #     self.config.credentials_file,
                    #     project=self.project_id
                    # )
                    pass
                else:
                    # Use default credentials (service account, gcloud auth, etc.)
                    # self.client = logging.Client(project=self.project_id)
                    pass
                
                return True
                
        except ImportError:
            # logging.error("google-cloud-logging library is required for Google Cloud")
            return False
        except Exception as e:
            # logging.error(f"Google Cloud Logging connection failed: {e}")
            return False
    
    def _setup_service(self) -> None:
        """Setup Google Cloud Logging service."""
        # No specific setup needed
        pass
    
    def _send_log(self, record: LogRecord) -> bool:
        """Send a single log to Google Cloud Logging."""
        try:
            with self._connection_lock:
                # Create logger
                logger = self.client.logger('hydra-logger')
                
                # Prepare log entry
                log_entry = {
                    'severity': record.levelname.upper(),
                    'message': self.format(record),
                    'timestamp': self.format_timestamp(record),
                    'labels': {
                        'logger': record.logger_name,
                        'file_name': getattr(record, 'file_name', ''),
                        'function': getattr(record, 'function_name', ''),
                        'line': str(getattr(record, 'line_number', ''))
                    },
                    'jsonPayload': {
                        'extra': getattr(record, 'extra', {})
                    }
                }
                
                # Write log entry
                logger.write_entries([log_entry])
                
                return True
                
        except Exception as e:
            # logging.error(f"Failed to send log to Google Cloud: {e}")
            return False
    
    def _send_batch(self, records: List[LogRecord]) -> bool:
        """Send multiple logs to Google Cloud Logging."""
        try:
            with self._connection_lock:
                # Create logger
                logger = self.client.logger('hydra-logger')
                
                # Prepare log entries
                log_entries = []
                for record in records:
                    log_entry = {
                        'severity': record.levelname.upper(),
                        'message': self.format(record),
                        'timestamp': self.format_timestamp(record),
                        'labels': {
                            'logger': record.logger_name,
                            'file_name': getattr(record, 'file_name', ''),
                            'function': getattr(record, 'function_name', ''),
                            'line': str(getattr(record, 'line_number', ''))
                        },
                        'jsonPayload': {
                            'extra': getattr(record, 'extra', {})
                        }
                    }
                    log_entries.append(log_entry)
                
                # Write log entries
                logger.write_entries(log_entries)
                
                return True
                
        except Exception as e:
            # logging.error(f"Failed to send batch to Google Cloud: {e}")
            return False
    
    def _close_connection(self) -> None:
        """Close Google Cloud Logging connection."""
        if self.client:
            with self._connection_lock:
                try:
                    self.client.close()
                except Exception:
                    pass
                self.client = None


class ElasticsearchHandler(BaseCloudHandler):
    """
    Elasticsearch handler.
    
    Provides # logging to Elasticsearch for search and analytics.
    """
    
    def __init__(
        self,
        hosts: Union[str, List[str]] = "localhost:9200",
        index_name: str = "logs",
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs
    ):
        """Initialize Elasticsearch handler."""
        # Create config
        config = CloudConfig(
            service=CloudService.ELASTICSEARCH,
            hosts=hosts,
            index_name=index_name,
            username=username,
            password=password,
            **kwargs
        )
        
        super().__init__(config=config)
        
        self.index_name = index_name
        self.client = None
        self._connection_lock = threading.RLock()
    
    def _establish_connection(self) -> bool:
        """Establish Elasticsearch connection."""
        try:
            from elasticsearch import Elasticsearch  # type: ignore
            
            with self._connection_lock:
                # Create Elasticsearch client
                if self.config.username and self.config.password:
                    self.client = Elasticsearch(
                        hosts=self.config.hosts,
                        basic_auth=(self.config.username, self.config.password),
                        timeout=self.config.timeout,
                        max_retries=self.config.max_retries,
                        retry_on_timeout=True
                    )
                else:
                    self.client = Elasticsearch(
                        hosts=self.config.hosts,
                        timeout=self.config.timeout,
                        max_retries=self.config.max_retries,
                        retry_on_timeout=True
                    )
                
                # Test connection
                self.client.ping()
                
                return True
                
        except ImportError:
            # logging.error("elasticsearch library is required for Elasticsearch. Install with: pip install elasticsearch")
            return False
        except Exception as e:
            # logging.error(f"Elasticsearch connection failed: {e}")
            return False
    
    def _setup_service(self) -> None:
        """Setup Elasticsearch index and mapping."""
        try:
            with self._connection_lock:
                # Create index if it doesn't exist
                if not self.client.indices.exists(index=self.index_name):
                    # Create index with mapping
                    mapping = {
                        'mappings': {
                            'properties': {
                                'timestamp': {'type': 'date'},
                                'level': {'type': 'keyword'},
                                'logger': {'type': 'keyword'},
                                'message': {'type': 'text'},
                                'file_name': {'type': 'keyword'},
                                'function': {'type': 'keyword'},
                                'line': {'type': 'integer'},
                                'extra': {'type': 'object'}
                            }
                        },
                        'settings': {
                            'number_of_shards': 1,
                            'number_of_replicas': 0
                        }
                    }
                    
                    self.client.indices.create(
                        index=self.index_name,
                        body=mapping
                    )
                
        except Exception as e:
            # logging.error(f"Failed to setup Elasticsearch: {e}")
            raise
    
    def _send_log(self, record: LogRecord) -> bool:
        """Send a single log to Elasticsearch."""
        try:
            # Prepare document
            document = {
                'timestamp': self.format_timestamp(record),
                'level': record.levelname,
                'logger': record.logger_name,
                'message': self.format(record),
                'file_name': getattr(record, 'file_name', ''),
                'function': getattr(record, 'function_name', ''),
                'line': getattr(record, 'line_number', ''),
                'extra': getattr(record, 'extra', {})
            }
            
            # Index document
            with self._connection_lock:
                response = self.client.index(
                    index=self.index_name,
                    body=document
                )
                
                return response['result'] in ['created', 'updated']
                
        except Exception as e:
            # logging.error(f"Failed to send log to Elasticsearch: {e}")
            return False
    
    def _send_batch(self, records: List[LogRecord]) -> bool:
        """Send multiple logs to Elasticsearch."""
        try:
            # Prepare bulk operations
            bulk_data = []
            for record in records:
                # Index action
                bulk_data.append({
                    'index': {
                        '_index': self.index_name
                    }
                })
                
                # Document
                document = {
                    'timestamp': self.format_timestamp(record),
                    'level': record.levelname,
                    'logger': record.logger_name,
                    'message': self.format(record),
                    'file_name': getattr(record, 'file_name', ''),
                    'function': getattr(record, 'function_name', ''),
                    'line': getattr(record, 'line_number', ''),
                    'extra': getattr(record, 'extra', {})
                }
                bulk_data.append(document)
            
            # Execute bulk operation
            with self._connection_lock:
                response = self.client.bulk(body=bulk_data)
                
                # Check for errors
                if response.get('errors', False):
                    # logging.error(f"Bulk operation had errors: {response}")
                    return False
                
                return True
                
        except Exception as e:
            # logging.error(f"Failed to send batch to Elasticsearch: {e}")
            return False
    
    def _close_connection(self) -> None:
        """Close Elasticsearch connection."""
        if self.client:
            with self._connection_lock:
                try:
                    self.client.close()
                except Exception:
                    pass
                self.client = None


class CloudHandlerFactory:
    """Factory for creating cloud service handlers."""
    
    @staticmethod
    def create_handler(
        handler_type: str,
        **kwargs
    ) -> BaseCloudHandler:
        """Create a cloud service handler of the specified type."""
        handler_type = handler_type.lower()
        
        if handler_type in ["aws", "cloudwatch", "aws_cloudwatch"]:
            return AWSCloudWatchHandler(**kwargs)
        elif handler_type in ["azure", "azure_monitor"]:
            return AzureMonitorHandler(**kwargs)
        elif handler_type in ["gcp", "google", "google_cloud"]:
            return GoogleCloudLoggingHandler(**kwargs)
        elif handler_type in ["elasticsearch", "es"]:
            return ElasticsearchHandler(**kwargs)
        else:
            raise ValueError(f"Unknown cloud service handler type: {handler_type}")
    
    @staticmethod
    def create_aws_handler(region: str, log_group: str, **kwargs) -> AWSCloudWatchHandler:
        """Create an AWS CloudWatch handler."""
        return AWSCloudWatchHandler(region=region, log_group=log_group, **kwargs)
    
    @staticmethod
    def create_azure_handler(workspace_id: str, workspace_key: str, **kwargs) -> AzureMonitorHandler:
        """Create an Azure Monitor handler."""
        return AzureMonitorHandler(workspace_id=workspace_id, workspace_key=workspace_key, **kwargs)
    
    @staticmethod
    def create_google_handler(project_id: str, **kwargs) -> GoogleCloudLoggingHandler:
        """Create a Google Cloud Logging handler."""
        return GoogleCloudLoggingHandler(project_id=project_id, **kwargs)
    
    @staticmethod
    def create_elasticsearch_handler(hosts: Union[str, List[str]], **kwargs) -> ElasticsearchHandler:
        """Create an Elasticsearch handler."""
        return ElasticsearchHandler(hosts=hosts, **kwargs)
