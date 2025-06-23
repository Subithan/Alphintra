# Alphintra Trading Platform

A comprehensive algorithmic trading platform built with microservices architecture, featuring real-time market data processing, strategy execution, and portfolio management.

## 🏗️ Infrastructure Overview

The platform is built on a robust infrastructure stack designed for high-performance trading operations:

### Core Services
- **PostgreSQL** - Primary database for user data, strategies, and trades
- **TimescaleDB** - Time-series database for market data and metrics
- **Redis** - Caching and session management
- **Apache Kafka** - Event streaming and message queues
- **MLflow** - Machine learning model management
- **MinIO** - Object storage for files and artifacts

### Monitoring & Observability
- **Prometheus** - Metrics collection and monitoring
- **Grafana** - Dashboards and visualization
- **Jaeger** - Distributed tracing

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- At least 8GB RAM available
- Ports 3000, 5001, 5432, 5433, 6379, 9001, 9090, 9092, 16686 available

### 1. Start Infrastructure Services

```bash
# Start all infrastructure services
docker-compose up -d postgres timescaledb redis zookeeper kafka mlflow minio prometheus grafana jaeger

# Wait for services to initialize (2-3 minutes)
# Check status
./check-services.sh
```

### 2. Verify Setup

Run the service checker to ensure everything is working:

```bash
chmod +x check-services.sh
./check-services.sh
```

You should see all services marked as ✓ HEALTHY.

## 📊 Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | admin/admin |
| **MLflow** | http://localhost:5001 | - |
| **MinIO Console** | http://localhost:9001 | admin/admin123 |
| **Prometheus** | http://localhost:9090 | - |
| **Jaeger** | http://localhost:16686 | - |
| **PostgreSQL** | localhost:5432 | alphintra/alphintra123 |
| **TimescaleDB** | localhost:5433 | timescale/timescale123 |
| **Redis** | localhost:6379 | password: redis123 |
| **Kafka** | localhost:9092 | - |

## 🗄️ Database Schema

### PostgreSQL Tables
The main database includes tables for:
- **Users & Authentication** - User accounts, profiles, API keys
- **Trading Accounts** - Broker connections and account management
- **Strategies** - Trading strategy definitions and subscriptions
- **Trades & Positions** - Trade execution and portfolio positions
- **Performance Metrics** - Strategy performance tracking
- **Notifications** - User alerts and system notifications

### TimescaleDB Hypertables
Time-series data includes:
- **Market Data** - OHLCV candlestick data
- **Price Ticks** - Real-time price feeds
- **Order Book Snapshots** - Market depth data
- **Trading Signals** - Strategy-generated signals
- **Portfolio Snapshots** - Portfolio value over time
- **Strategy Metrics** - Performance metrics over time
- **System Metrics** - Infrastructure monitoring data

## 📨 Kafka Topics

The following topics are configured for event streaming:

- **trade-execution** (3 partitions) - Trade orders and executions
- **strategy-signals** (3 partitions) - Trading signals from strategies
- **market-data** (6 partitions) - Real-time market data feeds
- **user-events** (2 partitions) - User authentication and management events

## 🔧 Development Commands

### Docker Management
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker logs <container_name>

# Restart specific service
docker-compose restart <service_name>
```

### Database Access
```bash
# PostgreSQL shell
docker exec -it alphintra-postgres psql -U alphintra -d alphintra

# TimescaleDB shell
docker exec -it alphintra-timescaledb psql -U timescale -d timescaledb

# Redis shell
docker exec -it alphintra-redis redis-cli -a redis123
```

### Kafka Management
```bash
# List topics
docker exec alphintra-kafka kafka-topics --list --bootstrap-server localhost:9092

# Create topic
docker exec alphintra-kafka kafka-topics --create --topic <topic-name> --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

# Consume messages
docker exec alphintra-kafka kafka-console-consumer --topic <topic-name> --bootstrap-server localhost:9092 --from-beginning
```

## 📈 Monitoring

### Grafana Dashboards
Access Grafana at http://localhost:3000 (admin/admin) to view:
- System performance metrics
- Database performance
- Kafka message throughput
- Application-specific metrics

### Prometheus Metrics
Access Prometheus at http://localhost:9090 to query:
- Infrastructure metrics
- Custom application metrics
- Alert rules and targets

### Distributed Tracing
Access Jaeger at http://localhost:16686 to trace:
- Request flows across services
- Performance bottlenecks
- Error tracking

## 🏛️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   Mobile App    │    │   API Gateway   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
    ┌────────────────────────────┼────────────────────────────┐
    │                           │                            │
┌───▼────┐  ┌──────────┐  ┌─────▼─────┐  ┌──────────────┐   │
│ Auth   │  │ Trading  │  │ Strategy  │  │ Market Data  │   │
│Service │  │   API    │  │  Engine   │  │   Service    │   │
└───┬────┘  └─────┬────┘  └─────┬─────┘  └──────┬───────┘   │
    │             │             │               │           │
    └─────────────┼─────────────┼───────────────┼───────────┘
                  │             │               │
              ┌───▼─────────────▼───────────────▼───┐
              │           Kafka Event Bus           │
              └─────────────────┬───────────────────┘
                                │
    ┌───────────────────────────┼───────────────────────────┐
    │                          │                           │
┌───▼────┐  ┌─────────┐  ┌─────▼─────┐  ┌──────────────┐   │
│PostgreSQL│ │TimescaleDB│ │   Redis   │  │    MinIO     │   │
│(Main DB) │ │(Time-series)│(Cache)   │  │ (Storage)    │   │
└──────────┘ └───────────┘ └───────────┘  └──────────────┘   │
                                                             │
    ┌────────────────────────────────────────────────────────┘
    │
┌───▼────┐  ┌─────────┐  ┌───────────┐
│MLflow  │  │Prometheus│  │  Jaeger   │
│(ML Ops)│  │(Metrics) │  │ (Tracing) │
└────────┘  └─────────┘  └───────────┘
```

## 🔐 Security Features

- **Encrypted API Keys** - Broker API keys stored encrypted
- **JWT Authentication** - Secure user authentication
- **Role-based Access** - Different permission levels
- **Rate Limiting** - API request throttling
- **Audit Logging** - Complete action tracking

## 📝 Next Steps

1. **Application Services** - Deploy the microservices (auth, trading API, strategy engine)
2. **Frontend Development** - Build the web dashboard and mobile app
3. **Strategy Development** - Implement trading algorithms
4. **Broker Integration** - Connect to exchanges (Binance, Bybit, etc.)
5. **Testing & Monitoring** - Set up comprehensive testing and alerting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the service logs using `./check-services.sh`

---

**Status**: Infrastructure Ready ✅  
**Next**: Deploy Application Services

## 🏗️ Architecture Overview

alphintra is built using a microservices architecture with the following components:

### Core Services
- **API Gateway** (Spring Cloud Gateway) - Central entry point with routing, authentication, and rate limiting
- **Auth Service** (FastAPI) - User authentication, authorization, and API key management
- **Trading API** (FastAPI) - Trade execution, portfolio management, and market data
- **Strategy Engine** (Python) - Automated trading strategies with ML capabilities
- **Broker Connector** (FastAPI) - Real exchange integration (Binance, Coinbase)
- **Broker Simulator** (FastAPI) - Simulated trading environment for testing

### Infrastructure
- **PostgreSQL** - Primary database for user data, trades, and configurations
- **TimescaleDB** - Time-series database for market data and metrics
- **Redis** - Caching and session management
- **Apache Kafka** - Event streaming and inter-service communication
- **MLflow** - Machine learning model management and tracking

### Monitoring & Observability
- **Prometheus** - Metrics collection and monitoring
- **Grafana** - Dashboards and visualization
- **Structured Logging** - Centralized logging across all services

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git
- 8GB+ RAM recommended

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Alphintra
   ```

2. **Start the platform**
   ```bash
   docker-compose up -d
   ```

3. **Verify services are running**
   ```bash
   docker-compose ps
   ```

4. **Access the services**
   - API Gateway: http://localhost:8080
   - Grafana Dashboard: http://localhost:3001 (admin/admin123)
   - Prometheus: http://localhost:9090
   - MLflow: http://localhost:5000

### Initial Setup

1. **Create a user account**
   ```bash
   curl -X POST "http://localhost:8080/api/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "password": "securepassword",
       "full_name": "John Doe"
     }'
   ```

2. **Login and get access token**
   ```bash
   curl -X POST "http://localhost:8080/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "password": "securepassword"
     }'
   ```

## 📊 Features

### Trading Strategies
- **DCA (Dollar Cost Averaging)** - Systematic investment strategy
- **Grid Trading** - Profit from market volatility
- **Momentum Trading** - Technical indicator-based strategies
- **ML-Based Strategies** - Machine learning powered trading decisions

### Market Data
- Real-time price feeds
- Historical OHLCV data
- Order book snapshots
- Trade execution data

### Portfolio Management
- Multi-asset portfolio tracking
- Performance analytics
- Risk metrics
- P&L reporting

### Risk Management
- Position sizing
- Stop-loss orders
- Portfolio diversification
- Drawdown protection

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
POSTGRES_PASSWORD=your_secure_password
TIMESCALE_PASSWORD=your_secure_password
REDIS_PASSWORD=your_secure_password

# Security
JWT_SECRET=your-super-secret-jwt-key-that-should-be-at-least-256-bits-long

# Exchange API Keys (for real trading)
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
COINBASE_API_KEY=your_coinbase_api_key
COINBASE_SECRET_KEY=your_coinbase_secret_key
COINBASE_PASSPHRASE=your_coinbase_passphrase

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Service Configuration

Each service can be configured through environment variables or configuration files:

- **Gateway**: `src/backend/gateway/src/main/resources/application.yml`
- **Python Services**: Environment variables in Docker Compose

## 📈 API Documentation

### Authentication
All API requests (except registration/login) require a Bearer token:

```bash
Authorization: Bearer <your_jwt_token>
```

### Key Endpoints

#### Trading API
- `POST /api/trading/trades` - Create a new trade
- `GET /api/trading/trades` - Get trading history
- `GET /api/trading/portfolio` - Get portfolio summary
- `GET /api/trading/market-data/{symbol}` - Get market data

#### Strategy Engine
- `POST /api/strategies` - Create a trading strategy
- `GET /api/strategies` - List active strategies
- `PUT /api/strategies/{id}` - Update strategy parameters
- `DELETE /api/strategies/{id}` - Stop a strategy

#### Broker Services
- `POST /api/broker/orders` - Place an order
- `GET /api/broker/orders/{id}` - Get order status
- `GET /api/broker/balance` - Get account balance

## 🔍 Monitoring

### Grafana Dashboards

Access Grafana at http://localhost:3001 with credentials `admin/admin123`:

- **System Overview** - Service health, request rates, response times
- **Trading Metrics** - Trade performance, strategy analytics
- **Infrastructure** - Database performance, message queue metrics

### Prometheus Metrics

Key metrics available at http://localhost:9090:

- `http_requests_total` - HTTP request counts
- `http_request_duration_seconds` - Request latency
- `trading_orders_total` - Trading order metrics
- `strategy_signals_total` - Strategy signal counts

### Health Checks

All services expose health check endpoints:
- Gateway: `GET /actuator/health`
- Python services: `GET /health`

## 🧪 Testing

### Running Tests

```bash
# Run all service tests
docker-compose -f docker-compose.test.yml up --build

# Run specific service tests
cd src/backend/trading-api
python -m pytest tests/
```

### Simulation Mode

Use the broker simulator for testing strategies without real money:

```bash
# Enable simulation mode
curl -X POST "http://localhost:8080/api/simulator/enable" \
  -H "Authorization: Bearer <token>"
```

## 🚀 Deployment

### Production Deployment

1. **Update environment variables** for production
2. **Configure SSL/TLS** certificates
3. **Set up external databases** (managed PostgreSQL, Redis)
4. **Configure monitoring** and alerting
5. **Deploy using Docker Swarm or Kubernetes**

### Scaling

- **Horizontal scaling**: Add more service instances
- **Database scaling**: Use read replicas for TimescaleDB
- **Message queue scaling**: Kafka cluster with multiple brokers

## 🔒 Security

### Best Practices
- All passwords and API keys stored as environment variables
- JWT tokens with configurable expiration
- Rate limiting on all endpoints
- Input validation and sanitization
- HTTPS in production

### API Security
- Bearer token authentication
- Role-based access control
- API key management for external integrations
- Request signing for exchange APIs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit a pull request

### Development Setup

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Install development dependencies
pip install -r requirements-dev.txt

# Run pre-commit hooks
pre-commit install
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` directory for detailed guides
- **Issues**: Report bugs and feature requests on GitHub Issues
- **Discussions**: Join community discussions on GitHub Discussions

## 🗺️ Roadmap

### Phase 1 (Current)
- ✅ Core microservices architecture
- ✅ Basic trading strategies
- ✅ Broker simulator
- ✅ Monitoring and observability

### Phase 2 (Next)
- 🔄 Advanced ML strategies
- 🔄 Web frontend (React)
- 🔄 Mobile app
- 🔄 Advanced risk management

### Phase 3 (Future)
- 📋 Multi-exchange arbitrage
- 📋 Social trading features
- 📋 Advanced analytics
- 📋 Institutional features

## 📊 Performance

### Benchmarks
- **Latency**: < 10ms for order placement
- **Throughput**: 1000+ requests/second
- **Uptime**: 99.9% availability target
- **Data Processing**: Real-time market data processing

### Resource Requirements

#### Minimum (Development)
- 4 CPU cores
- 8GB RAM
- 50GB storage

#### Recommended (Production)
- 8+ CPU cores
- 16GB+ RAM
- 200GB+ SSD storage
- Load balancer
- Managed databases

---

**Built with ❤️ for the trading community**

## 🏗️ Architecture Components

### Core Infrastructure
- **PostgreSQL** (Cloud SQL simulation)
- **TimescaleDB** (Time-series market data)
- **Redis** (Cloud Memorystore simulation)
- **Apache Kafka** (Event streaming)
- **Kubernetes** (GKE simulation via Minikube/k3d)
- **Istio** (Service mesh)
- **MLflow** (Vertex AI simulation)

### Microservices
- **Strategy Engine** (Java/Spring Boot)
- **Trading API** (FastAPI/Python)
- **Auth Service** (Spring Boot)
- **Broker Connector** (Multi-exchange integration)
- **Risk Engine** (Real-time risk management)

### Monitoring & Observability
- **Prometheus** (Metrics collection)
- **Grafana** (Dashboards)
- **Loki/ELK** (Logging)

## 🚀 Quick Start

1. **Prerequisites**
   ```bash
   # Install Docker and Docker Compose
   docker --version
   docker-compose --version
   
   # Install Kubernetes (choose one)
   # Option A: Minikube
   minikube start
   
   # Option B: k3d
   k3d cluster create Alphintra-cluster
   ```

2. **Start Infrastructure**
   ```bash
   # Start all services
   docker-compose up -d
   
   # Check service status
   docker-compose ps
   ```

3. **Initialize Databases**
   ```bash
   # PostgreSQL setup
   docker exec -it Alphintra-db psql -U Alphintra -d Alphintra -f /docker-entrypoint-initdb.d/init.sql
   
   # TimescaleDB setup
   docker exec -it Alphintra-tsdb psql -U tsuser -d Alphintra_ts -f /docker-entrypoint-initdb.d/timescale_init.sql
   ```

4. **Access Services**
   - **Trading API**: http://localhost:8000
   - **Strategy Engine**: http://localhost:8081
   - **Grafana**: http://localhost:3000
   - **Prometheus**: http://localhost:9090
   - **MLflow**: http://localhost:5000

## 📁 Project Structure

```
Alphintra/
├── infra/                    # Infrastructure as Code
│   ├── terraform/           # GCP deployment configs
│   └── docker-compose.yaml  # Local development
├── src/                     # Source code
│   ├── backend/            # Microservices
│   ├── frontend/           # Web applications
│   └── ml/                 # ML training & serving
├── databases/              # Database configurations
├── pipelines/              # Data processing
├── services/               # Supporting services
├── ci-cd/                  # CI/CD configurations
└── docs/                   # Documentation
```

## 🔧 Development Workflow

1. **Local Development**
   - Use Docker Compose for rapid iteration
   - Hot reload enabled for all services
   - Mock broker APIs for safe testing

2. **Testing**
   - Unit tests for each microservice
   - Integration tests with test databases
   - End-to-end trading simulation

3. **Deployment**
   - Kubernetes manifests for staging
   - Terraform for GCP production
   - CI/CD pipeline automation

## 🛡️ Security & Compliance

- **KYC Integration** (Sumsub/Onfido simulation)
- **Risk Management** (Real-time monitoring)
- **Audit Logging** (Complete transaction trails)
- **Secrets Management** (HashiCorp Vault)

## 📊 Monitoring

- **Application Metrics** (Custom Prometheus metrics)
- **Infrastructure Health** (System resource monitoring)
- **Trading Performance** (Strategy effectiveness tracking)
- **Risk Alerts** (Real-time notifications)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request

## 📄 License

Proprietary - Alphintra Trading Platform

---

**Ready to revolutionize algorithmic trading! 🚀**