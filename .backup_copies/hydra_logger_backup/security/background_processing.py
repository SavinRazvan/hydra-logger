"""
Background Processing for Security Operations in Hydra-Logger

This module provides background thread processing for security operations
to improve performance by moving heavy security processing off the main thread.
It supports multiple operation types, priority queuing, and result caching.

FEATURES:
- Background thread processing for security operations
- Priority-based task queuing
- Result caching and performance optimization
- Multiple security operation types
- Batch processing for efficiency
- Configurable worker threads and queue sizes
- Performance monitoring and statistics

OPERATION TYPES:
- PII_DETECTION: Personal information detection
- DATA_SANITIZATION: Data sanitization processing
- ENCRYPTION: Cryptographic operations
- HASH_VALIDATION: Hash generation and validation
- THREAT_DETECTION: Security threat detection

USAGE:
    from hydra_logger.security.background_processing import (
        BackgroundSecurityProcessor, SecurityOperationType
    )
    
    # Create background processor
    processor = BackgroundSecurityProcessor(
        max_workers=4,
        queue_size=1000,
        batch_size=10
    )
    
    # Submit security task
    task_id = processor.submit_task(
        operation_type=SecurityOperationType.PII_DETECTION,
        data="sensitive data",
        priority=1
    )
    
    # Get processing statistics
    stats = processor.get_stats()
    print(f"Tasks processed: {stats['tasks_processed']}")
    
    # Shutdown processor
    processor.shutdown()
"""

import threading
import queue
import time
import re
from typing import Any, Dict, List, Optional, Callable, Union
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass
from enum import Enum
import logging


class SecurityOperationType(Enum):
    """Types of security operations that can be processed in background."""
    PII_DETECTION = "pii_detection"
    DATA_SANITIZATION = "data_sanitization"
    ENCRYPTION = "encryption"
    HASH_VALIDATION = "hash_validation"
    THREAT_DETECTION = "threat_detection"


@dataclass
class SecurityTask:
    """Represents a security task to be processed in background."""
    task_id: str
    operation_type: SecurityOperationType
    data: Any
    callback: Optional[Callable] = None
    priority: int = 0  # Higher number = higher priority
    created_at: float = 0.0
    timeout: float = 30.0  # Timeout in seconds
    
    def __lt__(self, other):
        """Less than comparison for priority queue."""
        if not isinstance(other, SecurityTask):
            return NotImplemented
        # Higher priority first, then earlier creation time
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.created_at < other.created_at
    
    def __le__(self, other):
        """Less than or equal comparison for priority queue."""
        return self.__lt__(other) or self.__eq__(other)
    
    def __gt__(self, other):
        """Greater than comparison for priority queue."""
        return not self.__le__(other)
    
    def __ge__(self, other):
        """Greater than or equal comparison for priority queue."""
        return not self.__lt__(other)
    
    def __eq__(self, other):
        """Equal comparison for priority queue."""
        if not isinstance(other, SecurityTask):
            return NotImplemented
        return self.task_id == other.task_id


@dataclass
class SecurityResult:
    """Result of a security operation."""
    task_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    processing_time: float = 0.0
    callback: Optional[Callable] = None


class BackgroundSecurityProcessor:
    """
    Background processor for security operations.
    
    Moves heavy security processing to background threads to improve
    main thread performance while maintaining security functionality.
    """
    
    def __init__(self, 
                 max_workers: int = 4,
                 queue_size: int = 1000,
                 batch_size: int = 10,
                 processing_interval: float = 0.01):
        """
        Initialize background security processor.
        
        Args:
            max_workers: Maximum number of background worker threads
            queue_size: Maximum size of the task queue
            batch_size: Number of tasks to process in a single batch
            processing_interval: Interval between batch processing (seconds)
        """
        self.max_workers = max_workers
        self.queue_size = queue_size
        self.batch_size = batch_size
        self.processing_interval = processing_interval
        
        # Task queue with priority support
        self._task_queue = queue.PriorityQueue(maxsize=queue_size)
        self._result_queue = queue.Queue()
        
        # Thread pool for background processing
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._workers = []
        
        # Statistics and monitoring
        self._stats = {
            'tasks_queued': 0,
            'tasks_processed': 0,
            'tasks_failed': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0,
            'queue_size': 0,
            'active_workers': 0,
            'last_reset': time.time()
        }
        
        # Caching for repeated operations
        self._result_cache = {}
        self._cache_max_size = 1000
        self._cache_ttl = 300.0  # 5 minutes
        
        # Compiled patterns cache
        self._compiled_patterns = {}
        
        # Control flags
        self._running = False
        self._shutdown = False
        
        # Start background workers
        self._start_workers()
    
    def _start_workers(self):
        """Start background worker threads."""
        self._running = True
        
        # Start batch processor
        batch_processor = threading.Thread(
            target=self._batch_processor,
            name="SecurityBatchProcessor",
            daemon=True
        )
        batch_processor.start()
        self._workers.append(batch_processor)
        
        # Start result processor
        result_processor = threading.Thread(
            target=self._result_processor,
            name="SecurityResultProcessor",
            daemon=True
        )
        result_processor.start()
        self._workers.append(result_processor)
    
    def _batch_processor(self):
        """Process tasks in batches for efficiency."""
        while not self._shutdown:
            try:
                batch = []
                
                # Collect batch of tasks
                for _ in range(self.batch_size):
                    try:
                        # Get task with timeout (priority, task) tuple
                        priority, task = self._task_queue.get(timeout=self.processing_interval)
                        batch.append(task)
                    except queue.Empty:
                        break
                
                if batch:
                    # Process batch in parallel
                    futures = []
                    for task in batch:
                        future = self._executor.submit(self._process_task, task)
                        futures.append(future)
                    
                    # Wait for batch completion
                    for future in futures:
                        try:
                            result = future.result(timeout=30.0)
                            if hasattr(result, 'task_id'):  # Check if it's a SecurityResult
                                self._result_queue.put(result)
                            else:
                                logging.error(f"Invalid result type: {type(result)}")
                                self._stats['tasks_failed'] += 1
                        except Exception as e:
                            logging.error(f"Error processing security task: {e}")
                            self._stats['tasks_failed'] += 1
                
                # Update statistics
                self._stats['queue_size'] = self._task_queue.qsize()
                self._stats['active_workers'] = len([w for w in self._workers if w.is_alive()])
                
            except Exception as e:
                logging.error(f"Error in batch processor: {e}")
                time.sleep(0.1)
    
    def _result_processor(self):
        """Process completed results and call callbacks."""
        while not self._shutdown:
            try:
                result = self._result_queue.get(timeout=1.0)
                
                # Update statistics
                self._stats['tasks_processed'] += 1
                self._stats['total_processing_time'] += result.processing_time
                self._stats['average_processing_time'] = (
                    self._stats['total_processing_time'] / self._stats['tasks_processed']
                )
                
                # Call callback if provided
                if hasattr(result, 'callback') and result.callback:
                    try:
                        result.callback(result)
                    except Exception as e:
                        logging.error(f"Error in result callback: {e}")
                
                # Cache result if applicable
                self._cache_result(result)
                
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error in result processor: {e}")
    
    def _process_task(self, task: SecurityTask) -> SecurityResult:
        """Process a single security task."""
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(task)
            if cache_key in self._result_cache:
                cached_result = self._result_cache[cache_key]
                if time.time() - cached_result['timestamp'] < self._cache_ttl:
                    return SecurityResult(
                        task_id=task.task_id,
                        success=True,
                        result=cached_result['result'],
                        processing_time=time.time() - start_time
                    )
            
            # Process based on operation type
            if task.operation_type == SecurityOperationType.PII_DETECTION:
                result = self._process_pii_detection(task.data)
            elif task.operation_type == SecurityOperationType.DATA_SANITIZATION:
                result = self._process_data_sanitization(task.data)
            elif task.operation_type == SecurityOperationType.ENCRYPTION:
                result = self._process_encryption(task.data)
            elif task.operation_type == SecurityOperationType.HASH_VALIDATION:
                result = self._process_hash_validation(task.data)
            elif task.operation_type == SecurityOperationType.THREAT_DETECTION:
                result = self._process_threat_detection(task.data)
            else:
                raise ValueError(f"Unknown operation type: {task.operation_type}")
            
            processing_time = time.time() - start_time
            
            return SecurityResult(
                task_id=task.task_id,
                success=True,
                result=result,
                processing_time=processing_time,
                callback=task.callback
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return SecurityResult(
                task_id=task.task_id,
                success=False,
                result=None,
                error=str(e),
                processing_time=processing_time,
                callback=task.callback
            )
    
    def _process_pii_detection(self, data: Any) -> Dict[str, Any]:
        """Process PII detection in background."""
        if isinstance(data, str):
            return self._detect_pii_in_string(data)
        elif isinstance(data, dict):
            return self._detect_pii_in_dict(data)
        elif isinstance(data, list):
            return self._detect_pii_in_list(data)
        else:
            return {'detected': False, 'patterns': [], 'redacted_data': data}
    
    def _detect_pii_in_string(self, text: str) -> Dict[str, Any]:
        """Detect PII in a string."""
        patterns = self._get_compiled_patterns()
        detected_patterns = []
        redacted_text = text
        
        for pattern_name, pattern in patterns.items():
            matches = pattern.findall(text)
            if matches:
                detected_patterns.append({
                    'pattern': pattern_name,
                    'matches': matches,
                    'count': len(matches)
                })
                # Redact the matches
                redacted_text = pattern.sub(f'[REDACTED_{pattern_name.upper()}]', redacted_text)
        
        return {
            'detected': len(detected_patterns) > 0,
            'patterns': detected_patterns,
            'redacted_data': redacted_text,
            'original_length': len(text),
            'redacted_length': len(redacted_text)
        }
    
    def _detect_pii_in_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect PII in a dictionary."""
        result = {'detected': False, 'patterns': [], 'redacted_data': {}}
        
        for key, value in data.items():
            if isinstance(value, str):
                pii_result = self._detect_pii_in_string(value)
                if pii_result['detected']:
                    result['detected'] = True
                    result['patterns'].extend(pii_result['patterns'])
                result['redacted_data'][key] = pii_result['redacted_data']
            else:
                result['redacted_data'][key] = value
        
        return result
    
    def _detect_pii_in_list(self, data: List[Any]) -> Dict[str, Any]:
        """Detect PII in a list."""
        result = {'detected': False, 'patterns': [], 'redacted_data': []}
        
        for item in data:
            if isinstance(item, str):
                pii_result = self._detect_pii_in_string(item)
                if pii_result['detected']:
                    result['detected'] = True
                    result['patterns'].extend(pii_result['patterns'])
                result['redacted_data'].append(pii_result['redacted_data'])
            else:
                result['redacted_data'].append(item)
        
        return result
    
    def _get_compiled_patterns(self) -> Dict[str, re.Pattern]:
        """Get compiled regex patterns for PII detection."""
        if not self._compiled_patterns:
            patterns = {
                'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
                'credit_card': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
                'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
                'api_key': r'\b[A-Za-z0-9]{20,}\b'
            }
            
            self._compiled_patterns = {
                name: re.compile(pattern, re.IGNORECASE)
                for name, pattern in patterns.items()
            }
        
        return self._compiled_patterns
    
    def _process_data_sanitization(self, data: Any) -> Any:
        """Process data sanitization in background."""
        # Placeholder for data sanitization logic
        return data
    
    def _process_encryption(self, data: Any) -> Any:
        """Process encryption in background."""
        if isinstance(data, dict) and 'data' in data and 'key' in data:
            # Crypto operations
            from .crypto import CryptoUtils
            crypto = CryptoUtils(use_background_processing=False)
            return crypto.encrypt_symmetric(data['data'], data['key'])
        else:
            # Simple encryption for other data types
            import hashlib
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            elif isinstance(data, bytes):
                data_bytes = data
            else:
                data_bytes = str(data).encode('utf-8')
            
            # Simple hash-based encryption (for demonstration)
            return hashlib.sha256(data_bytes).hexdigest()
    
    def _process_hash_validation(self, data: Any) -> Any:
        """Process hash validation in background."""
        if isinstance(data, dict) and 'data' in data and 'algorithm' in data:
            # Crypto operations
            from .crypto import CryptoUtils
            crypto = CryptoUtils(use_background_processing=False)
            if 'expected_hash' in data:
                # Hash validation - generate hash and compare
                generated_hash = crypto._hash_data_sync(data['data'], data['algorithm'])
                return {
                    'valid': generated_hash == data['expected_hash'],
                    'generated_hash': generated_hash,
                    'expected_hash': data['expected_hash']
                }
            else:
                # Hash generation
                return crypto._hash_data_sync(data['data'], data['algorithm'])
        else:
            # Simple hashing for other data types
            import hashlib
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            elif isinstance(data, bytes):
                data_bytes = data
            else:
                data_bytes = str(data).encode('utf-8')
            
            return hashlib.sha256(data_bytes).hexdigest()
    
    def _process_threat_detection(self, data: Any) -> Any:
        """Process threat detection in background."""
        # Placeholder for threat detection logic
        return data
    
    def _get_cache_key(self, task: SecurityTask) -> str:
        """Generate cache key for task."""
        import hashlib
        key_data = f"{task.operation_type.value}:{str(task.data)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _cache_result(self, result: SecurityResult):
        """Cache result for future use."""
        if len(self._result_cache) >= self._cache_max_size:
            # Remove oldest entries
            oldest_key = min(self._result_cache.keys(), 
                           key=lambda k: self._result_cache[k]['timestamp'])
            del self._result_cache[oldest_key]
        
        cache_key = f"result_{result.task_id}"
        self._result_cache[cache_key] = {
            'result': result.result,
            'timestamp': time.time()
        }
    
    def submit_task(self, 
                   operation_type: SecurityOperationType,
                   data: Any,
                   callback: Optional[Callable] = None,
                   priority: int = 0,
                   timeout: float = 30.0) -> str:
        """
        Submit a security task for background processing.
        
        Args:
            operation_type: Type of security operation
            data: Data to process
            callback: Optional callback function for result
            priority: Task priority (higher = more important)
            timeout: Task timeout in seconds
            
        Returns:
            Task ID for tracking
        """
        task_id = f"{operation_type.value}_{int(time.time() * 1000)}"
        
        task = SecurityTask(
            task_id=task_id,
            operation_type=operation_type,
            data=data,
            callback=callback,
            priority=priority,
            created_at=time.time(),
            timeout=timeout
        )
        
        try:
            # Add to queue with priority (negative for max-heap behavior)
            self._task_queue.put((-priority, task), timeout=1.0)
            self._stats['tasks_queued'] += 1
            return task_id
        except queue.Full:
            raise RuntimeError("Security task queue is full")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self._stats.copy()
    
    def reset_stats(self):
        """Reset processing statistics."""
        self._stats = {
            'tasks_queued': 0,
            'tasks_processed': 0,
            'tasks_failed': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0,
            'queue_size': 0,
            'active_workers': 0,
            'last_reset': time.time()
        }
    
    def shutdown(self, timeout: float = 30.0):
        """Shutdown the background processor."""
        self._shutdown = True
        
        # Wait for workers to finish
        for worker in self._workers:
            worker.join(timeout=timeout)
        
        # Shutdown executor
        self._executor.shutdown(wait=True)
        
        self._running = False


# Global instance for easy access
_background_processor = None


def get_background_processor() -> BackgroundSecurityProcessor:
    """Get the global background security processor instance."""
    global _background_processor
    if _background_processor is None:
        _background_processor = BackgroundSecurityProcessor()
    return _background_processor


def shutdown_background_processor():
    """Shutdown the global background security processor."""
    global _background_processor
    if _background_processor is not None:
        _background_processor.shutdown()
        _background_processor = None
