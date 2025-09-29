"""Pytest configuration and fixtures for the AI/ML Strategy Service."""
import os
import pytest
from dotenv import load_dotenv

# Load test environment variables BEFORE importing application modules
# This ensures that the settings object is created with the test environment
load_dotenv('src/backend/ai-ml-strategy-service/.env.test')
os.environ['TESTING'] = 'True'

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.types import CHAR, JSON
import uuid
from app.core.auth import get_current_user_id

# Import app after environment is set
from main import app
from app.core.config import settings
from app.models.base import Base
from app.core.database import get_db

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=False  # Disable SQL logging for tests to reduce noise
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the database URL in settings
settings.DATABASE_URL = SQLALCHEMY_DATABASE_URL

# Add a compilation directive for UUID on SQLite
@compiles(UUID, "sqlite")
def compile_uuid_sqlite(element, compiler, **kw):
    return "CHAR(32)"

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"

# Create test database tables
Base.metadata.create_all(bind=engine)

# Fixture for database session
@pytest.fixture(scope="function")
def db_session():
    """Create a clean database session for each test case."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

# Fixture for FastAPI test client
@pytest.fixture(scope="module")
def client():
    """Create a test client for FastAPI application."""
    # Override get_db dependency
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    def override_get_current_user_id():
        return uuid.uuid4()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    with TestClient(app) as test_client:
        test_client.headers = {
            "Authorization": "Bearer dummy-test-token"
        }
        yield test_client

# Common test data fixtures
@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    return {
        "symbol": "AAPL",
        "timestamp": "2023-01-01T00:00:00",
        "open": 150.0,
        "high": 155.0,
        "low": 149.5,
        "close": 154.0,
        "volume": 1000000
    }

@pytest.fixture
def sample_strategy_config():
    """Sample strategy configuration for testing."""
    return {
        "name": "Moving Average Crossover",
        "description": "Basic moving average crossover strategy",
        "parameters": {
            "short_window": 20,
            "long_window": 50
        },
        "symbols": ["AAPL", "MSFT"],
        "timeframe": "1d"
    }