# AI/ML Strategy Service

The AI/ML Strategy Service is a comprehensive microservice that provides machine learning capabilities, code-based strategy development, model training orchestration, backtesting, and paper trading functionality for the Alphintra algorithmic trading platform.

## Features

### Core Capabilities
- **Code-based Strategy Development**: Web-based IDE with Python SDK
- **Dataset Management**: Platform and custom dataset handling with validation
- **Model Training Orchestration**: Integration with Vertex AI and Kubeflow
- **Backtesting Engine**: Comprehensive historical strategy testing
- **Paper Trading**: Real-time virtual trading simulation
- **Experiment Tracking**: MLflow integration for ML lifecycle management

### Key Components
- **Strategy Development Engine**: Interactive development environment
- **Dataset Management Service**: Data ingestion, validation, and processing
- **Model Training Orchestrator**: Scalable ML training on cloud resources
- **Backtesting Engine**: Advanced testing methodologies (walk-forward, Monte Carlo)
- **Paper Trading Engine**: Realistic live trading simulation
- **Experiment Tracking Service**: Version control for models and experiments

## Architecture

### Technology Stack
- **Framework**: FastAPI with Python 3.11+
- **Database**: PostgreSQL + TimescaleDB for time-series data
- **Caching**: Redis
- **ML Frameworks**: TensorFlow, PyTorch, Scikit-learn
- **Training Platform**: Google Vertex AI
- **Experiment Tracking**: MLflow
- **Message Queue**: Apache Kafka
- **Storage**: Google Cloud Storage
- **Containerization**: Docker + Kubernetes

### Database Models
- **Strategy Models**: Strategy, StrategyTemplate, DebugSession
- **Dataset Models**: Dataset, DatasetPreview, DataPreprocessingJob
- **Training Models**: TrainingJob, ModelArtifact, HyperparameterTrial
- **Backtesting Models**: BacktestJob, BacktestResult, Trade
- **Paper Trading Models**: PaperAccount, Position, PaperTrade
- **Experiment Models**: Experiment, ExperimentRun, ModelRegistry

## Quick Start

### Development Setup

1. **Clone and navigate to the service directory**:
   ```bash
   cd src/backend/ai-ml-strategy-service
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**:
   ```bash
   alembic upgrade head
   ```

6. **Run the service**:
   ```bash
   python main.py
   ```

The service will be available at `http://localhost:8002`

### Docker Development

1. **Build the Docker image**:
   ```bash
   docker build --target development -t ai-ml-strategy-service:dev .
   ```

2. **Run with Docker Compose** (from project root):
   ```bash
   docker-compose up ai-ml-strategy-service
   ```

### Production Deployment

1. **Build production image**:
   ```bash
   docker build --target production -t ai-ml-strategy-service:latest .
   ```

2. **Deploy to Kubernetes**:
   ```bash
   kubectl apply -f k8s/
   ```

## API Documentation

When running in development mode, API documentation is available at:
- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

### Key Endpoints

#### Strategy Development
- `POST /api/strategies/code/create` - Create new strategy
- `PUT /api/strategies/code/{id}` - Update strategy code
- `POST /api/strategies/code/{id}/execute` - Execute strategy
- `POST /api/strategies/code/{id}/debug` - Start debugging session

#### Dataset Management
- `GET /api/datasets` - List datasets
- `POST /api/datasets/upload` - Upload custom dataset
- `POST /api/datasets/{id}/validate` - Validate dataset
- `GET /api/datasets/{id}/preview` - Preview dataset

#### Model Training
- `POST /api/training/jobs` - Create training job
- `GET /api/training/jobs/{id}` - Get training job status
- `POST /api/training/hyperparameter-tune` - Start hyperparameter tuning

> **Note:** Training jobs are dispatched asynchronously to the configured orchestration backend. The service publishes job specifications to Vertex AI (or another compatible orchestrator) and relies on callback URLs or polling to track progress and completion.

#### Backtesting
- `POST /api/backtests` - Create backtest
- `POST /api/backtests/{id}/run` - Execute backtest
- `GET /api/backtests/{id}/results` - Get backtest results

#### Paper Trading
- `POST /api/paper-trading/accounts` - Create paper trading account
- `POST /api/paper-trading/strategies/{id}/deploy` - Deploy strategy
- `GET /api/paper-trading/performance` - Get performance metrics

## Configuration

### Environment Variables

Key configuration options (see `.env.example` for complete list):

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `GCP_PROJECT_ID`: Google Cloud Project ID
- `MLFLOW_TRACKING_URI`: MLflow tracking server URI
- `SECRET_KEY`: JWT signing secret
- `TRAINING_ORCHESTRATOR_URL`: Base URL for the external training orchestration service (e.g., Vertex AI proxy)
- `TRAINING_JOB_QUEUE_TOPIC`: Optional message queue topic for fire-and-forget submissions when no HTTP endpoint is available
- `TRAINING_ORCHESTRATOR_TOKEN`: Optional bearer token used when calling the orchestration service
- `TRAINING_CALLBACK_BASE_URL`: Public URL where the orchestration service can send progress/completion callbacks

### Database Migrations

Use Alembic for database schema management:

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Development

### Code Structure
```
app/
├── api/          # API routes and endpoints
├── core/         # Core configuration and utilities
├── models/       # Database models
├── services/     # Business logic services
└── utils/        # Utility functions

tests/            # Test suite
k8s/             # Kubernetes manifests
alembic/         # Database migrations
```

### Testing

Run the test suite:
```bash
pytest
pytest --cov=app tests/  # With coverage
```

### Code Quality

Format and lint code:
```bash
black app/ tests/
isort app/ tests/
flake8 app/ tests/
mypy app/
```

## Monitoring

### Metrics
Prometheus metrics are available at `http://localhost:8003/metrics`:
- Request rates and latencies
- Training job success/failure rates
- Backtest execution times
- Database connection pool usage

### Logging
Structured JSON logging with configurable levels:
- Application logs in `/app/logs/`
- Request/response logging
- Error tracking and alerting

### Health Checks
- `/health` - Basic health check
- `/ready` - Readiness probe for Kubernetes

## Security

### Authentication
- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- Permission-based endpoint protection

### Data Protection
- Encrypted data at rest and in transit
- Sandboxed code execution environment
- Input validation and sanitization
- Rate limiting and DDoS protection

## Performance

### Optimization Features
- Async/await throughout the application
- Connection pooling for databases
- Redis caching for frequently accessed data
- Horizontal auto-scaling in Kubernetes

### Resource Management
- Configurable resource limits for training jobs
- Memory-efficient data processing
- Streaming for large datasets
- Connection pool monitoring

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure all checks pass before submitting PRs

## License

This service is part of the Alphintra platform and is proprietary software.