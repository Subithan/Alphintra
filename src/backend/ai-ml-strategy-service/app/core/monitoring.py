"""
Monitoring and metrics configuration.
"""

from prometheus_client import Counter, Histogram, Gauge, start_http_server
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Define Prometheus metrics
REQUEST_COUNT = Counter(
    'ai_ml_strategy_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'ai_ml_strategy_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'ai_ml_strategy_active_connections',
    'Number of active connections'
)

TRAINING_JOBS_TOTAL = Counter(
    'ai_ml_strategy_training_jobs_total',
    'Total number of training jobs',
    ['status']
)

TRAINING_JOBS_DURATION = Histogram(
    'ai_ml_strategy_training_job_duration_seconds',
    'Training job duration in seconds'
)

BACKTESTS_TOTAL = Counter(
    'ai_ml_strategy_backtests_total',
    'Total number of backtests',
    ['status']
)

BACKTEST_DURATION = Histogram(
    'ai_ml_strategy_backtest_duration_seconds',
    'Backtest duration in seconds'
)

PAPER_TRADES_TOTAL = Counter(
    'ai_ml_strategy_paper_trades_total',
    'Total number of paper trades',
    ['symbol', 'side']
)

ACTIVE_STRATEGIES = Gauge(
    'ai_ml_strategy_active_strategies',
    'Number of active strategies'
)

DATABASE_CONNECTIONS = Gauge(
    'ai_ml_strategy_database_connections',
    'Number of database connections',
    ['pool_name']
)

REDIS_CONNECTIONS = Gauge(
    'ai_ml_strategy_redis_connections',
    'Number of Redis connections'
)

DATASET_UPLOADS_TOTAL = Counter(
    'ai_ml_strategy_dataset_uploads_total',
    'Total number of dataset uploads',
    ['status']
)

DATASET_SIZE_BYTES = Histogram(
    'ai_ml_strategy_dataset_size_bytes',
    'Dataset size in bytes'
)

EXPERIMENT_RUNS_TOTAL = Counter(
    'ai_ml_strategy_experiment_runs_total',
    'Total number of experiment runs',
    ['status']
)

CODE_EXECUTIONS_TOTAL = Counter(
    'ai_ml_strategy_code_executions_total',
    'Total number of code executions',
    ['status']
)

CODE_EXECUTION_DURATION = Histogram(
    'ai_ml_strategy_code_execution_duration_seconds',
    'Code execution duration in seconds'
)


def setup_metrics():
    """
    Setup Prometheus metrics server.
    """
    if settings.ENABLE_METRICS:
        try:
            start_http_server(settings.PROMETHEUS_PORT)
            logger.info(
                "Prometheus metrics server started",
                port=settings.PROMETHEUS_PORT
            )
        except Exception as e:
            logger.error(
                "Failed to start Prometheus metrics server",
                error=str(e),
                port=settings.PROMETHEUS_PORT
            )


def record_request_metrics(method: str, endpoint: str, status_code: int, duration: float):
    """
    Record request metrics.
    """
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)


def record_training_job_metrics(status: str, duration: float = None):
    """
    Record training job metrics.
    """
    TRAINING_JOBS_TOTAL.labels(status=status).inc()
    if duration is not None:
        TRAINING_JOBS_DURATION.observe(duration)


def record_backtest_metrics(status: str, duration: float = None):
    """
    Record backtest metrics.
    """
    BACKTESTS_TOTAL.labels(status=status).inc()
    if duration is not None:
        BACKTEST_DURATION.observe(duration)


def record_paper_trade_metrics(symbol: str, side: str):
    """
    Record paper trade metrics.
    """
    PAPER_TRADES_TOTAL.labels(symbol=symbol, side=side).inc()


def record_dataset_upload_metrics(status: str, size_bytes: int = None):
    """
    Record dataset upload metrics.
    """
    DATASET_UPLOADS_TOTAL.labels(status=status).inc()
    if size_bytes is not None:
        DATASET_SIZE_BYTES.observe(size_bytes)


def record_experiment_metrics(status: str):
    """
    Record experiment metrics.
    """
    EXPERIMENT_RUNS_TOTAL.labels(status=status).inc()


def record_code_execution_metrics(status: str, duration: float = None):
    """
    Record code execution metrics.
    """
    CODE_EXECUTIONS_TOTAL.labels(status=status).inc()
    if duration is not None:
        CODE_EXECUTION_DURATION.observe(duration)


def update_active_strategies_count(count: int):
    """
    Update active strategies gauge.
    """
    ACTIVE_STRATEGIES.set(count)


def update_database_connections_count(pool_name: str, count: int):
    """
    Update database connections gauge.
    """
    DATABASE_CONNECTIONS.labels(pool_name=pool_name).set(count)


def update_redis_connections_count(count: int):
    """
    Update Redis connections gauge.
    """
    REDIS_CONNECTIONS.set(count)