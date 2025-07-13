"""
Professional AsyncTraceManager for distributed tracing support.

This module provides distributed tracing support including:
- Trace ID generation and propagation
- Correlation ID management
- Professional tracing patterns
- Trace context preservation
"""

import asyncio
import time
import uuid
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager


class TraceContext:
    """
    Professional trace context with comprehensive tracing metadata.
    
    Features:
    - Trace ID and correlation ID management
    - Span tracking and timing
    - Metadata storage
    - Professional tracing patterns
    """
    
    def __init__(self, trace_id: Optional[str] = None, 
                 correlation_id: Optional[str] = None,
                 parent_span_id: Optional[str] = None):
        """
        Initialize TraceContext.
        
        Args:
            trace_id: Unique trace identifier
            correlation_id: Correlation identifier
            parent_span_id: Parent span identifier
        """
        self.trace_id = trace_id or self._generate_trace_id()
        self.correlation_id = correlation_id or self._generate_correlation_id()
        self.parent_span_id = parent_span_id
        self.current_span_id = self._generate_span_id()
        self.created_at = time.time()
        self.spans = []
        self.metadata = {}
        self._span_stack = []
    
    def _generate_trace_id(self) -> str:
        """Generate unique trace ID."""
        return f"trace_{uuid.uuid4().hex}"
    
    def _generate_correlation_id(self) -> str:
        """Generate unique correlation ID."""
        return f"corr_{uuid.uuid4().hex[:16]}"
    
    def _generate_span_id(self) -> str:
        """Generate unique span ID."""
        return f"span_{uuid.uuid4().hex[:12]}"
    
    def start_span(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new span.
        
        Args:
            name: Span name
            metadata: Span metadata
            
        Returns:
            str: Span ID
        """
        span_id = self._generate_span_id()
        span = {
            'span_id': span_id,
            'name': name,
            'start_time': time.time(),
            'parent_span_id': self.current_span_id,
            'metadata': metadata or {},
            'status': 'active'
        }
        
        self.spans.append(span)
        self._span_stack.append(self.current_span_id)
        self.current_span_id = span_id
        
        return span_id
    
    def end_span(self, span_id: str, status: str = 'completed', 
                error: Optional[str] = None) -> bool:
        """
        End a span.
        
        Args:
            span_id: Span ID to end
            status: Span status
            error: Error message if any
            
        Returns:
            bool: True if span was found and ended
        """
        for span in self.spans:
            if span['span_id'] == span_id:
                span['end_time'] = time.time()
                span['duration'] = span['end_time'] - span['start_time']
                span['status'] = status
                if error:
                    span['error'] = error
                
                # Restore parent span
                if self._span_stack and span_id == self.current_span_id:
                    self.current_span_id = self._span_stack.pop()
                
                return True
        
        return False
    
    def get_current_span_id(self) -> str:
        """Get current span ID."""
        return self.current_span_id
    
    def get_trace_stats(self) -> Dict[str, Any]:
        """Get comprehensive trace statistics."""
        active_spans = [s for s in self.spans if s.get('status') == 'active']
        completed_spans = [s for s in self.spans if s.get('status') == 'completed']
        error_spans = [s for s in self.spans if s.get('status') == 'error']
        
        return {
            'trace_id': self.trace_id,
            'correlation_id': self.correlation_id,
            'current_span_id': self.current_span_id,
            'total_spans': len(self.spans),
            'active_spans': len(active_spans),
            'completed_spans': len(completed_spans),
            'error_spans': len(error_spans),
            'created_at': self.created_at,
            'age_seconds': time.time() - self.created_at,
            'span_stack_depth': len(self._span_stack)
        }
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add trace metadata."""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get trace metadata."""
        return self.metadata.get(key, default)


class AsyncTraceManager:
    """
    Professional trace manager for distributed tracing.
    
    Features:
    - Trace ID generation and propagation
    - Correlation ID management
    - Professional tracing patterns
    - Trace context preservation
    """
    
    def __init__(self):
        """Initialize AsyncTraceManager."""
        self._current_trace: Optional[TraceContext] = None
        self._trace_history: List[TraceContext] = []
        self._max_history = 50
        self._start_time = time.time()
        self._trace_count = 0
    
    def start_trace(self, trace_id: Optional[str] = None,
                   correlation_id: Optional[str] = None) -> TraceContext:
        """
        Start a new trace.
        
        Args:
            trace_id: Optional trace ID
            correlation_id: Optional correlation ID
            
        Returns:
            TraceContext: New trace context
        """
        trace = TraceContext(trace_id=trace_id, correlation_id=correlation_id)
        self._current_trace = trace
        self._trace_history.append(trace)
        self._trace_count += 1
        
        # Keep history size manageable
        if len(self._trace_history) > self._max_history:
            self._trace_history.pop(0)
        
        return trace
    
    def get_current_trace(self) -> Optional[TraceContext]:
        """Get current trace context."""
        return self._current_trace
    
    def get_trace_id(self) -> Optional[str]:
        """Get current trace ID."""
        if self._current_trace:
            return self._current_trace.trace_id
        return None
    
    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID."""
        if self._current_trace:
            return self._current_trace.correlation_id
        return None
    
    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for current trace."""
        if self._current_trace:
            self._current_trace.correlation_id = correlation_id
    
    def clear_trace(self) -> None:
        """Clear current trace."""
        self._current_trace = None
    
    def start_span(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Start a span in current trace.
        
        Args:
            name: Span name
            metadata: Span metadata
            
        Returns:
            Optional[str]: Span ID if trace exists
        """
        if self._current_trace:
            return self._current_trace.start_span(name, metadata)
        return None
    
    def end_span(self, span_id: str, status: str = 'completed', 
                error: Optional[str] = None) -> bool:
        """
        End a span in current trace.
        
        Args:
            span_id: Span ID to end
            status: Span status
            error: Error message if any
            
        Returns:
            bool: True if span was ended successfully
        """
        if self._current_trace:
            return self._current_trace.end_span(span_id, status, error)
        return False
    
    def get_trace_stats(self) -> Dict[str, Any]:
        """Get comprehensive trace statistics."""
        return {
            'current_trace_id': self.get_trace_id(),
            'current_correlation_id': self.get_correlation_id(),
            'total_traces': self._trace_count,
            'trace_history_size': len(self._trace_history),
            'uptime': time.time() - self._start_time,
            'has_current_trace': self._current_trace is not None
        }
    
    def get_trace_history(self) -> List[TraceContext]:
        """Get trace history."""
        return self._trace_history.copy()
    
    def reset_trace_history(self) -> None:
        """Reset trace history."""
        self._trace_history.clear()
        self._trace_count = 0


# Global trace manager instance
_trace_manager = AsyncTraceManager()


def get_trace_manager() -> AsyncTraceManager:
    """Get global trace manager instance."""
    return _trace_manager


@asynccontextmanager
async def trace_context(trace_id: Optional[str] = None,
                       correlation_id: Optional[str] = None):
    """
    Async context manager for trace management.
    
    Args:
        trace_id: Optional trace ID
        correlation_id: Optional correlation ID
        
    Yields:
        TraceContext: Trace context
    """
    trace = _trace_manager.start_trace(trace_id, correlation_id)
    try:
        yield trace
    finally:
        _trace_manager.clear_trace()


@asynccontextmanager
async def span_context(name: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Async context manager for span management.
    
    Args:
        name: Span name
        metadata: Span metadata
        
    Yields:
        str: Span ID
    """
    span_id = _trace_manager.start_span(name, metadata)
    try:
        yield span_id
    finally:
        _trace_manager.end_span(span_id) 