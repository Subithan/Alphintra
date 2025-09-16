# Strategy Inference Service

The Strategy Inference Service is a core component of the Alphintra trading platform that executes trading strategies in real-time and distributes trading signals across multiple channels.

## 🎯 Overview

This service bridges the gap between strategy development (AI/ML and No-Code services) and live trading by:

- **Loading strategies** from AI/ML and No-Code service databases
- **Executing strategies** against real-time market data
- **Generating trading signals** with confidence scores and risk assessment
- **Distributing signals** via Kafka, WebSocket, and Redis pub/sub
- **Monitoring performance** with comprehensive metrics and health checks

## 🏗️ Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Strategy       │    │  Inference      │    │  Signal         │
│  Loader         │────│  Engine         │────│  Distributor    │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  AI/ML & NoCode │    │  Market Data    │    │  Kafka/WebSocket│
│  Databases      │    │  Client         │    │  Redis          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Services

1. **Strategy Loader**: Retrieves strategies from multiple database sources
2. **Inference Engine**: Executes strategies in isolated sandboxes
3. **Market Data Client**: Fetches real-time data from multiple providers
4. **Signal Distributor**: Broadcasts signals via multiple channels
5. **Monitoring**: Prometheus metrics and health checks

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL databases (AI/ML and No-Code services)
- Redis
- Kafka

### Local Development Setup

1. **Clone and navigate to the service directory**:
   ```bash
   cd src/backend/inference-service
   ```

2. **Copy environment configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start dependencies with Docker Compose**:
   ```bash
   docker-compose up redis kafka zookeeper -d
   ```

4. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the service**:
   ```bash
   python main.py
   ```

### Docker Deployment

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

2. **For development with debug tools**:
   ```bash
   docker-compose --profile debug up --build
   ```

The service will be available at `http://localhost:8002`

## 📡 API Endpoints

### Health and Monitoring

- `GET /` - Service information
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe
- `GET /health/status` - Detailed status
- `GET /health/metrics` - Prometheus metrics

### Strategy Management

- `GET /api/strategies/list` - List available strategies
- `GET /api/strategies/{strategy_id}` - Get strategy details
- `POST /api/strategies/start` - Start strategy execution
- `POST /api/strategies/{strategy_id}/stop` - Stop strategy execution
- `GET /api/strategies/{strategy_id}/status` - Get strategy status
- `GET /api/strategies/active/list` - List active strategies
- `GET /api/strategies/{strategy_id}/metrics` - Get strategy metrics

### Signal Management

- `GET /api/signals/list` - List trading signals with filtering
- `GET /api/signals/{signal_id}` - Get signal details
- `GET /api/signals/latest/{symbol}` - Get latest signals for symbol
- `GET /api/signals/analytics/summary` - Get signal analytics
- `WS /api/signals/stream` - WebSocket signal streaming

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Database connections
AI_ML_DATABASE_URL=postgresql://user:pass@host:port/db
NO_CODE_DATABASE_URL=postgresql://user:pass@host:port/db

# Message queue and caching
REDIS_URL=redis://localhost:6379
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Market data APIs
POLYGON_API_KEY=your_polygon_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# Performance tuning
MAX_CONCURRENT_STRATEGIES=10
STRATEGY_EXECUTION_TIMEOUT=30
SIGNAL_COOLDOWN_SECONDS=60
```

### Strategy Configuration

Strategies can be configured with:

```json
{
  "strategy_id": "uuid",
  "source": "ai_ml",
  "symbols": ["BTCUSDT", "ETHUSDT"],
  "timeframe": "1h",
  "execution_mode": "paper",
  "parameters": {
    "risk_level": 0.05,
    "take_profit": 0.02,
    "stop_loss": 0.01
  },
  "execution_interval": 300
}
```

## 🔐 Security

### Strategy Sandbox

Strategies execute in isolated sandboxes with:

- **Restricted imports**: Only safe libraries allowed
- **Memory limits**: Configurable per-strategy limits  
- **Execution timeouts**: Prevent infinite loops
- **Code validation**: AST-based security checks

### API Security

- Rate limiting on all endpoints
- Input validation and sanitization
- Optional JWT authentication
- CORS configuration for web clients

## 📊 Monitoring

### Prometheus Metrics

Available at `/health/metrics`:

- **Service metrics**: Uptime, requests, errors
- **Strategy metrics**: Active strategies, executions, signals
- **Signal metrics**: Generated, distributed, confidence scores
- **Market data metrics**: Requests, latency by provider
- **Resource metrics**: Memory, CPU, database connections

### Health Checks

- **Liveness**: Basic service health
- **Readiness**: Dependencies status (databases, Redis, Kafka)
- **Detailed status**: Component-level health information

### Logging

Structured logging with configurable levels:

```python
logger.info("Signal generated", 
           signal_id=signal.signal_id,
           symbol=signal.symbol, 
           confidence=signal.confidence)
```

## 🌊 Signal Streaming

### WebSocket Protocol

Connect to `/api/signals/stream` and send:

```json
{
  "type": "subscribe",
  "symbols": ["BTCUSDT", "ETHUSDT"]
}
```

Receive real-time signals:

```json
{
  "type": "signal",
  "data": {
    "signal_id": "sig_20240115_143022_001",
    "symbol": "BTCUSDT",
    "action": "BUY",
    "confidence": 0.85,
    "execution_params": {
      "quantity": 0.1,
      "price_target": 45250.00
    }
  }
}
```

### Kafka Topics

- `trading_signals` - All trading signals
- `trading_signal_updates` - Signal status updates
- `strategy_status` - Strategy execution status

## 🧪 Testing

### Test Endpoints

When `ENABLE_TEST_ENDPOINTS=true`:

- `POST /api/signals/test` - Generate test signal
- Mock market data available for development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

## 🚀 Deployment

### Kubernetes

Deploy using existing Alphintra Kubernetes configurations:

```bash
cd infra/kubernetes
./scripts/k8s/deploy.sh inference-service
```

### Docker

Production deployment:

```bash
docker build -t alphintra/inference-service:latest .
docker run -d --name inference-service \
  --env-file .env \
  -p 8002:8002 \
  alphintra/inference-service:latest
```

### Integration with Alphintra Platform

The service integrates with:

- **Spring Gateway**: API routing and load balancing
- **Prometheus/Grafana**: Monitoring and alerting
- **Kafka**: Event streaming platform
- **AI/ML Service**: Strategy source database
- **No-Code Service**: Visual workflow database

## 🔧 Development

### Project Structure

```
inference-service/
├── app/
│   ├── api/                 # FastAPI endpoints
│   ├── services/           # Core business logic
│   ├── models/             # Data models
│   └── utils/              # Utilities
├── tests/                  # Test suite
├── Dockerfile             # Container definition
├── docker-compose.yml     # Local development
├── requirements.txt       # Python dependencies
└── main.py                # Application entry point
```

### Adding New Features

1. **New Strategy Source**: Extend `StrategyLoader`
2. **New Market Data Provider**: Extend `MarketDataClient`
3. **New Signal Channel**: Extend `SignalDistributor`
4. **New Metrics**: Add to `PrometheusMetrics`

### Code Quality

- **Type hints**: All functions use type annotations
- **Structured logging**: Consistent log format across components
- **Error handling**: Comprehensive exception handling
- **Documentation**: Inline documentation for all classes/methods

## 📝 Contributing

1. Follow existing code patterns and structure
2. Add tests for new functionality
3. Update documentation for API changes
4. Ensure all health checks pass
5. Test with multiple strategy sources

## 🆘 Troubleshooting

### Common Issues

1. **Strategy fails to load**: Check database connectivity and strategy syntax
2. **Signals not distributed**: Verify Kafka/Redis connectivity
3. **Market data errors**: Check API keys and rate limits
4. **High memory usage**: Adjust strategy memory limits

### Debug Tools

- Kafka UI: `http://localhost:8080` (with debug profile)
- Redis Insight: `http://localhost:8001` (with debug profile)  
- Prometheus metrics: `http://localhost:8002/health/metrics`
- Service status: `http://localhost:8002/health/status`

## 📄 License

Part of the Alphintra trading platform. See main repository for license information.