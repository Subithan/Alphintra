"""
Monitoring and metrics utilities for the inference service.
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass
from threading import Lock

import structlog
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest

logger = structlog.get_logger(__name__)


@dataclass
class ServiceMetrics:
    """Service-level metrics."""
    uptime_start: datetime
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    active_connections: int = 0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0


class PrometheusMetrics:
    """Prometheus metrics collector for the inference service."""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        self._metrics_lock = Lock()
        
        # Service-level metrics
        self.service_uptime = Gauge(
            'inference_service_uptime_seconds',
            'Service uptime in seconds',
            registry=self.registry
        )
        
        self.service_info = Gauge(
            'inference_service_info', 
            'Service information',
            ['version', 'service'],
            registry=self.registry
        )
        
        # HTTP request metrics
        self.http_requests_total = Counter(
            'inference_service_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            'inference_service_http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Strategy execution metrics
        self.strategies_active = Gauge(
            'inference_service_strategies_active',
            'Number of active strategies',
            registry=self.registry
        )
        
        self.strategy_executions_total = Counter(
            'inference_service_strategy_executions_total',
            'Total strategy executions',
            ['strategy_id', 'source', 'status'],
            registry=self.registry
        )
        
        self.strategy_execution_duration = Histogram(
            'inference_service_strategy_execution_duration_seconds',
            'Strategy execution duration',
            ['strategy_id', 'source'],
            registry=self.registry
        )
        
        # Signal generation metrics
        self.signals_generated_total = Counter(
            'inference_service_signals_generated_total',
            'Total signals generated',
            ['strategy_id', 'symbol', 'action'],
            registry=self.registry
        )
        
        self.signals_distributed_total = Counter(
            'inference_service_signals_distributed_total',
            'Total signals distributed',
            ['channel', 'status'],
            registry=self.registry
        )
        
        self.signal_confidence = Histogram(
            'inference_service_signal_confidence',
            'Signal confidence scores',
            ['strategy_id', 'symbol'],
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            registry=self.registry
        )
        
        # Market data metrics
        self.market_data_requests_total = Counter(
            'inference_service_market_data_requests_total',
            'Total market data requests',
            ['provider', 'data_type', 'status'],
            registry=self.registry
        )
        
        self.market_data_latency = Histogram(
            'inference_service_market_data_latency_seconds',
            'Market data request latency',
            ['provider', 'data_type'],
            registry=self.registry
        )
        
        # WebSocket metrics
        self.websocket_connections = Gauge(
            'inference_service_websocket_connections',
            'Active WebSocket connections',
            registry=self.registry
        )
        
        self.websocket_messages_sent_total = Counter(
            'inference_service_websocket_messages_sent_total',
            'Total WebSocket messages sent',
            registry=self.registry
        )
        
        # Error metrics
        self.errors_total = Counter(
            'inference_service_errors_total',
            'Total errors',
            ['component', 'error_type'],
            registry=self.registry
        )
        
        # Resource metrics
        self.memory_usage = Gauge(
            'inference_service_memory_usage_bytes',
            'Memory usage in bytes',
            registry=self.registry
        )
        
        self.cpu_usage = Gauge(
            'inference_service_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        # Database metrics
        self.database_connections = Gauge(
            'inference_service_database_connections',
            'Active database connections',
            ['database'],
            registry=self.registry
        )
        
        self.database_queries_total = Counter(
            'inference_service_database_queries_total',
            'Total database queries',
            ['database', 'operation', 'status'],
            registry=self.registry
        )
        
        self.database_query_duration = Histogram(
            'inference_service_database_query_duration_seconds',
            'Database query duration',
            ['database', 'operation'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_hits_total = Counter(
            'inference_service_cache_hits_total',
            'Total cache hits',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_misses_total = Counter(
            'inference_service_cache_misses_total',
            'Total cache misses',
            ['cache_type'],
            registry=self.registry
        )
        
        # Set initial values
        self.service_info.labels(version='1.0.0', service='inference-service').set(1)
        self._start_time = time.time()
        
    def update_uptime(self):
        """Update service uptime metric."""
        uptime = time.time() - self._start_time
        self.service_uptime.set(uptime)
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        with self._metrics_lock:
            self.http_requests_total.labels(
                method=method, 
                endpoint=endpoint, 
                status=str(status_code)
            ).inc()
            
            self.http_request_duration.labels(
                method=method, 
                endpoint=endpoint
            ).observe(duration)
    
    def update_active_strategies(self, count: int):
        """Update active strategies count."""
        self.strategies_active.set(count)
    
    def record_strategy_execution(self, strategy_id: str, source: str, status: str, duration: float):
        """Record strategy execution metrics."""
        with self._metrics_lock:
            self.strategy_executions_total.labels(
                strategy_id=strategy_id,
                source=source,
                status=status
            ).inc()
            
            if status == 'success':
                self.strategy_execution_duration.labels(
                    strategy_id=strategy_id,
                    source=source
                ).observe(duration)
    
    def record_signal_generated(self, strategy_id: str, symbol: str, action: str, confidence: float):
        """Record signal generation metrics."""
        with self._metrics_lock:
            self.signals_generated_total.labels(
                strategy_id=strategy_id,
                symbol=symbol,
                action=action
            ).inc()
            
            self.signal_confidence.labels(
                strategy_id=strategy_id,
                symbol=symbol
            ).observe(confidence)
    
    def record_signal_distributed(self, channel: str, status: str):
        """Record signal distribution metrics."""
        self.signals_distributed_total.labels(
            channel=channel,
            status=status
        ).inc()
    
    def record_market_data_request(self, provider: str, data_type: str, status: str, latency: float):
        """Record market data request metrics."""
        with self._metrics_lock:
            self.market_data_requests_total.labels(
                provider=provider,
                data_type=data_type,
                status=status
            ).inc()
            
            if status == 'success':
                self.market_data_latency.labels(
                    provider=provider,
                    data_type=data_type
                ).observe(latency)
    
    def update_websocket_connections(self, count: int):
        """Update WebSocket connections count."""
        self.websocket_connections.set(count)
    
    def record_websocket_message_sent(self):
        """Record WebSocket message sent."""
        self.websocket_messages_sent_total.inc()
    
    def record_error(self, component: str, error_type: str):
        """Record error occurrence."""
        self.errors_total.labels(
            component=component,
            error_type=error_type
        ).inc()
    
    def update_resource_usage(self, memory_bytes: float, cpu_percent: float):
        """Update resource usage metrics."""
        self.memory_usage.set(memory_bytes)
        self.cpu_usage.set(cpu_percent)
    
    def update_database_connections(self, database: str, count: int):
        """Update database connections count."""
        self.database_connections.labels(database=database).set(count)
    
    def record_database_query(self, database: str, operation: str, status: str, duration: float):
        """Record database query metrics."""
        with self._metrics_lock:
            self.database_queries_total.labels(
                database=database,
                operation=operation,
                status=status
            ).inc()
            
            if status == 'success':
                self.database_query_duration.labels(
                    database=database,
                    operation=operation
                ).observe(duration)
    
    def record_cache_access(self, cache_type: str, hit: bool):
        """Record cache access (hit or miss)."""
        if hit:
            self.cache_hits_total.labels(cache_type=cache_type).inc()
        else:
            self.cache_misses_total.labels(cache_type=cache_type).inc()
    
    def generate_metrics(self) -> str:
        """Generate Prometheus metrics output."""
        self.update_uptime()
        return generate_latest(self.registry).decode('utf-8')


class PerformanceMonitor:
    """Performance monitoring utility."""
    
    def __init__(self):
        self.metrics = ServiceMetrics(uptime_start=datetime.utcnow())
        self._operation_times: Dict[str, float] = {}
    
    def start_operation(self, operation_id: str) -> None:
        """Start timing an operation."""
        self._operation_times[operation_id] = time.time()
    
    def end_operation(self, operation_id: str) -> Optional[float]:
        """End timing an operation and return duration."""
        start_time = self._operation_times.pop(operation_id, None)
        if start_time:
            return time.time() - start_time
        return None
    
    def get_uptime_seconds(self) -> float:
        """Get service uptime in seconds."""
        return (datetime.utcnow() - self.metrics.uptime_start).total_seconds()
    
    def update_system_metrics(self) -> None:
        """Update system resource metrics."""
        try:
            import psutil
            import os
            
            # Get current process
            process = psutil.Process(os.getpid())
            
            # Memory usage
            memory_info = process.memory_info()
            self.metrics.memory_usage_mb = memory_info.rss / 1024 / 1024
            
            # CPU usage
            self.metrics.cpu_usage_percent = process.cpu_percent()
            
        except ImportError:
            # psutil not available, use basic metrics
            import resource
            
            # Memory usage (rough estimate)
            usage = resource.getrusage(resource.RUSAGE_SELF)
            self.metrics.memory_usage_mb = usage.ru_maxrss / 1024  # On Linux, this is in KB
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        self.update_system_metrics()
        
        return {
            "uptime_seconds": self.get_uptime_seconds(),
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "success_rate": (
                self.metrics.successful_requests / max(self.metrics.total_requests, 1)
            ),
            "active_connections": self.metrics.active_connections,
            "memory_usage_mb": self.metrics.memory_usage_mb,
            "cpu_usage_percent": self.metrics.cpu_usage_percent
        }


# Global instances
prometheus_metrics = PrometheusMetrics()
performance_monitor = PerformanceMonitor()


def setup_prometheus_metrics() -> PrometheusMetrics:
    """Setup and return Prometheus metrics instance."""
    logger.info("Prometheus metrics initialized")
    return prometheus_metrics


def get_performance_monitor() -> PerformanceMonitor:
    """Get the performance monitor instance."""
    return performance_monitor