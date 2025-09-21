"""
Configuration settings for the AI/ML Strategy Service.
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    # Application settings
    APP_NAME: str = "AI/ML Strategy Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    PORT: int = Field(default=8002, description="Port to run the service on")
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    
    # Security settings
    SECRET_KEY: str = Field(..., description="Secret key for JWT token generation")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration in days")
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    
    # Database settings
    DATABASE_URL: str = Field(..., description="PostgreSQL database URL")
    TIMESCALE_DATABASE_URL: Optional[str] = Field(default=None, description="TimescaleDB database URL")
    DATABASE_POOL_SIZE: int = Field(default=20, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=30, description="Database max overflow connections")
    
    # Redis settings
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis URL for caching")
    REDIS_POOL_SIZE: int = Field(default=10, description="Redis connection pool size")
    
    # Google Cloud Platform settings
    GCP_PROJECT_ID: str = Field(..., description="Google Cloud Project ID")
    GCP_REGION: str = Field(default="us-central1", description="Google Cloud Region")
    GCS_BUCKET_NAME: str = Field(..., description="Google Cloud Storage bucket for datasets and models")
    VERTEX_AI_LOCATION: str = Field(default="us-central1", description="Vertex AI location")
    
    # MLflow settings
    MLFLOW_TRACKING_URI: str = Field(..., description="MLflow tracking server URI")
    MLFLOW_EXPERIMENT_NAME: str = Field(default="alphintra-strategies", description="MLflow experiment name")
    
    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092", description="Kafka bootstrap servers")
    KAFKA_CONSUMER_GROUP: str = Field(default="ai-ml-strategy-service", description="Kafka consumer group")
    
    # Strategy execution settings
    CODE_EXECUTION_TIMEOUT: int = Field(default=300, description="Code execution timeout in seconds")
    MAX_DATASET_SIZE_MB: int = Field(default=1024, description="Maximum dataset size in MB")
    MAX_TRAINING_TIME_HOURS: int = Field(default=24, description="Maximum training time in hours")
    
    # Backtesting settings
    MAX_BACKTEST_YEARS: int = Field(default=10, description="Maximum backtest period in years")
    DEFAULT_INITIAL_CAPITAL: float = Field(default=100000.0, description="Default initial capital for backtesting")
    DEFAULT_COMMISSION: float = Field(default=0.001, description="Default commission rate")
    DEFAULT_SLIPPAGE: float = Field(default=0.0005, description="Default slippage rate")
    
    # Paper trading settings
    PAPER_TRADING_INITIAL_CAPITAL: float = Field(default=100000.0, description="Initial capital for paper trading")
    PAPER_TRADING_MAX_POSITIONS: int = Field(default=20, description="Maximum positions in paper trading")
    
    # Rate limiting settings
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, description="API rate limit per minute per user")
    RATE_LIMIT_BURST: int = Field(default=200, description="API rate limit burst capacity")
    
    # Monitoring settings
    PROMETHEUS_PORT: int = Field(default=8003, description="Prometheus metrics port")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    ENABLE_METRICS: bool = Field(default=True, description="Enable Prometheus metrics")
    
    # External service URLs
    AUTH_SERVICE_URL: str = Field(default="http://auth-service:8080", description="Authentication service URL")
    TRADING_ENGINE_URL: str = Field(default="http://trading-engine:8080", description="Trading engine service URL")
    MARKET_DATA_SERVICE_URL: str = Field(default="http://market-data-service:8080", description="Market data service URL")
    
    # Model storage settings
    MODEL_STORAGE_BACKEND: str = Field(default="local", description="Model storage backend: s3, gcs, or local")
    MODEL_STORAGE_BUCKET: Optional[str] = Field(default=None, description="Storage bucket name for models")
    LOCAL_MODEL_STORAGE_PATH: str = Field(default="/tmp/models", description="Local path for model storage")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic."""
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings