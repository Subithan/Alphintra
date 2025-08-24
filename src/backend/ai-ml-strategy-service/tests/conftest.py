"""Pytest configuration and fixtures for the AI/ML Strategy Service."""
import os
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load test environment variables
load_dotenv('.env.test')

# Ensure we're using test database
os.environ['TESTING'] = 'True'

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
    echo=True  # Enable SQL logging for tests
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the database URL in settings
settings.DATABASE_URL = SQLALCHEMY_DATABASE_URL

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

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
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
