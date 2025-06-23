# Phase 1: Enhanced Local GCP Service Simulation

## Overview

This document outlines the implementation of Phase 1 of the Alphintra Trading Platform infrastructure development. Phase 1 focuses on creating a comprehensive local development environment that accurately simulates Google Cloud Platform (GCP) services.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [GCP Service Mapping](#gcp-service-mapping)
3. [Infrastructure Components](#infrastructure-components)
4. [Environment Management](#environment-management)
5. [Getting Started](#getting-started)
6. [Service Configuration](#service-configuration)
7. [Monitoring & Observability](#monitoring--observability)
8. [Security Considerations](#security-considerations)
9. [Troubleshooting](#troubleshooting)
10. [Next Steps](#next-steps)

## Architecture Overview

The Phase 1 implementation provides a complete local simulation of the GCP-based Alphintra trading platform. The architecture includes:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Local Development Environment                │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Application   │  │  Infrastructure │  │   Monitoring    │  │
│  │    Services     │  │    Services     │  │   & Logging     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │      Data       │  │    Messaging    │  │      ML/AI      │  │
│  │    Storage      │  │   & Streaming   │  │   & Analytics   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features

- **Multi-Environment Support**: Development, staging, and production configurations
- **GCP Service Emulation**: Local equivalents for all major GCP services
- **Container Orchestration**: Docker Compose with health checks and dependencies
- **Service Mesh Ready**: Prepared for Istio integration
- **Comprehensive Monitoring**: Prometheus, Grafana, and Jaeger integration
- **Development Tools**: Hot reloading, debugging, and testing utilities

## GCP Service Mapping

| GCP Service | Local Equivalent | Implementation | Purpose |
|-------------|------------------|----------------|---------|
| **Cloud SQL** | PostgreSQL + TimescaleDB | Docker containers with persistence | Primary database + time-series data |
| **Cloud Memorystore** | Redis Cluster | Master-replica Redis setup | Caching and session storage |
| **Cloud Pub/Sub** | Kafka + Pub/Sub Emulator | Confluent Kafka stack | Event streaming and messaging |
| **Google Kubernetes Engine** | k3d/minikube | Local K8s cluster | Container orchestration |
| **Vertex AI** | MLflow + Local ML | Python ML stack | Model training and serving |
| **Cloud Storage** | MinIO | S3-compatible storage | Object storage for artifacts |
| **Cloud Dataflow** | Apache Flink | Stream processing engine | Real-time data processing |
| **Cloud Dataproc** | Apache Spark | Batch processing engine | Large-scale analytics |
| **Cloud Run** | Docker Compose | Containerized services | Serverless-style deployments |
| **Cloud Build** | Local CI/CD | GitHub Actions simulation | Build and deployment pipelines |

## Infrastructure Components

### Core Infrastructure Services

#### 1. Database Services

**PostgreSQL (Cloud SQL Simulation)**
- **Purpose**: Primary database for user data, trades, configurations
- **Configuration**: Multiple databases for service isolation
- **Features**: Connection pooling, performance tuning, backup support
- **Ports**: 5432
- **Environment Variables**: `POSTGRES_*`

**TimescaleDB (Time-Series Database)**
- **Purpose**: High-performance storage for market data and metrics
- **Configuration**: Optimized for time-series workloads
- **Features**: Compression, continuous aggregates, retention policies
- **Ports**: 5433
- **Environment Variables**: `TIMESCALE_*`

#### 2. Caching & Session Management

**Redis Cluster**
- **Purpose**: Caching, session storage, real-time data
- **Configuration**: Master-replica setup for high availability
- **Features**: Persistence, memory optimization, clustering support
- **Ports**: 6379 (master), 6380 (replica)
- **Environment Variables**: `REDIS_*`

#### 3. Message Streaming

**Apache Kafka**
- **Purpose**: Event streaming, inter-service communication
- **Configuration**: Single-node setup for development, clustered for production
- **Features**: Topic auto-creation, retention policies, monitoring
- **Ports**: 9092, 9094
- **Dependencies**: Zookeeper

**GCP Pub/Sub Emulator**
- **Purpose**: Google Pub/Sub API compatibility
- **Configuration**: Local emulator for development
- **Features**: Topic and subscription management
- **Ports**: 8085

#### 4. ML/AI Infrastructure

**MLflow**
- **Purpose**: Machine learning lifecycle management
- **Configuration**: PostgreSQL backend, artifact storage
- **Features**: Experiment tracking, model registry, model serving
- **Ports**: 5000
- **Dependencies**: PostgreSQL, MinIO

**MinIO**
- **Purpose**: S3-compatible object storage
- **Configuration**: Single-node setup with web console
- **Features**: Bucket management, versioning, lifecycle policies
- **Ports**: 9000 (API), 9001 (Console)

### Application Services

#### 1. API Gateway
- **Technology**: Spring Cloud Gateway
- **Purpose**: Central entry point, routing, authentication
- **Features**: Rate limiting, CORS, circuit breakers
- **Ports**: 8080

#### 2. Auth Service
- **Technology**: FastAPI (Python)
- **Purpose**: Authentication, authorization, user management
- **Features**: JWT tokens, role-based access, OAuth integration
- **Ports**: 8001

#### 3. Trading API
- **Technology**: FastAPI (Python)
- **Purpose**: Core trading functionality, portfolio management
- **Features**: Order management, market data, risk calculations
- **Ports**: 8002

#### 4. Strategy Engine
- **Technology**: Python
- **Purpose**: Trading strategy execution, backtesting
- **Features**: Multiple strategies, ML integration, performance analytics
- **Ports**: 8003

#### 5. Broker Connector
- **Technology**: FastAPI (Python)
- **Purpose**: Exchange integrations (Binance, Coinbase)
- **Features**: Real-time data feeds, order execution, account management
- **Ports**: 8005

#### 6. Broker Simulator
- **Technology**: FastAPI (Python)
- **Purpose**: Mock exchange for testing
- **Features**: Simulated trading, configurable latency, error simulation
- **Ports**: 8006

### Monitoring & Observability

#### 1. Metrics Collection
**Prometheus**
- **Purpose**: Metrics collection and storage
- **Configuration**: Service discovery, alerting rules
- **Features**: Multi-dimensional metrics, PromQL queries
- **Ports**: 9090

#### 2. Visualization
**Grafana**
- **Purpose**: Dashboards and visualization
- **Configuration**: Pre-configured dashboards, data sources
- **Features**: Real-time monitoring, alerting, reporting
- **Ports**: 3001

#### 3. Distributed Tracing
**Jaeger**
- **Purpose**: Distributed tracing and performance monitoring
- **Configuration**: All-in-one deployment
- **Features**: Request tracing, performance analysis, service maps
- **Ports**: 16686 (UI), 14250 (gRPC), 14268 (HTTP)

## Environment Management

### Environment Types

#### Development Environment
- **Purpose**: Local development and testing
- **Configuration**: `docker-compose.dev.yml`
- **Features**: Hot reloading, debug ports, development tools
- **Command**: `make start-dev`

#### Staging Environment
- **Purpose**: Pre-production testing
- **Configuration**: `docker-compose.staging.yml`
- **Features**: Production-like configuration, limited resources
- **Command**: `make start-staging`

#### Production Environment
- **Purpose**: Production deployment simulation
- **Configuration**: `docker-compose.prod.yml`
- **Features**: Resource limits, security hardening, monitoring
- **Command**: `make start-prod`

### Environment Variables

Each environment uses a dedicated `.env` file:

- `.env.dev` - Development settings
- `.env.staging` - Staging settings
- `.env.prod` - Production settings

Key configuration categories:
- Database credentials and connection strings
- Service ports and endpoints
- Security tokens and secrets
- Resource limits and performance tuning
- External service configurations

## Getting Started

### Prerequisites

1. **System Requirements**:
   - 8GB+ RAM
   - 20GB+ available disk space
   - Docker 20.10+
   - Docker Compose 1.29+

2. **Check Prerequisites**:
   ```bash
   cd infra
   make install
   ./scripts/check-prerequisites.sh
   ```

### Quick Start

1. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd Alphintra/infra
   make setup-dev
   ```

2. **Start Development Environment**:
   ```bash
   make start-dev
   ```

3. **Verify Installation**:
   ```bash
   make health-dev
   ```

4. **Access Services**:
   - API Gateway: http://localhost:8080
   - Grafana: http://localhost:3001 (admin/admin123)
   - Prometheus: http://localhost:9090
   - MLflow: http://localhost:5000
   - Jaeger: http://localhost:16686

### Development Workflow

1. **Environment Management**:
   ```bash
   make start-dev      # Start development environment
   make stop-dev       # Stop development environment
   make restart-dev    # Restart development environment
   make status-dev     # Check service status
   make logs-dev       # View all logs
   ```

2. **Service-Specific Operations**:
   ```bash
   make logs-dev SERVICE=trading-api    # View specific service logs
   make shell-trading-api               # Open shell in service
   make debug-trading-api               # Debug service
   ```

3. **Data Operations**:
   ```bash
   make backup-dev     # Backup development data
   make restore-dev    # Restore from backup
   make migrate-dev    # Run database migrations
   ```

## Service Configuration

### Database Configuration

#### PostgreSQL Optimization
```sql
-- Performance tuning for trading workloads
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
```

#### TimescaleDB Setup
```sql
-- Create hypertables for time-series data
CREATE TABLE market_data (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    price DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    exchange TEXT
);

SELECT create_hypertable('market_data', 'time');

-- Add compression
ALTER TABLE market_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol,exchange'
);

-- Add retention policy
SELECT add_retention_policy('market_data', INTERVAL '1 year');
```

### Redis Configuration

#### Performance Optimization
```conf
# Memory management
maxmemory 1gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# Network optimization
tcp-keepalive 60
timeout 300
```

### Kafka Configuration

#### Topic Management
```bash
# Create trading-specific topics
kafka-topics --create --topic trade-execution --partitions 6 --replication-factor 1
kafka-topics --create --topic market-data --partitions 12 --replication-factor 1
kafka-topics --create --topic strategy-signals --partitions 3 --replication-factor 1
kafka-topics --create --topic risk-alerts --partitions 3 --replication-factor 1
```

## Monitoring & Observability

### Prometheus Metrics

#### Application Metrics
- **Trading Metrics**: Order latency, execution rates, portfolio performance
- **System Metrics**: CPU, memory, disk usage, network I/O
- **Business Metrics**: Revenue, active users, trading volume

#### Custom Metrics Examples
```python
from prometheus_client import Counter, Histogram, Gauge

# Trading-specific metrics
trade_counter = Counter('alphintra_trades_total', 'Total trades executed', ['strategy', 'symbol'])
order_latency = Histogram('alphintra_order_latency_seconds', 'Order execution latency')
active_strategies = Gauge('alphintra_active_strategies', 'Number of active strategies')
```

### Grafana Dashboards

#### Pre-configured Dashboards
1. **System Overview**: Infrastructure health and performance
2. **Trading Metrics**: Trading performance and analytics
3. **Application Performance**: Service-level metrics and traces
4. **Business Intelligence**: Revenue and user metrics

#### Dashboard Features
- Real-time data updates
- Alerting and notifications
- Custom time ranges and filters
- Export and sharing capabilities

### Jaeger Tracing

#### Trace Implementation
```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Configure tracing
tracer = trace.get_tracer(__name__)

@app.post("/api/trades")
async def create_trade(trade_data: TradeData):
    with tracer.start_as_current_span("create_trade") as span:
        span.set_attribute("trade.symbol", trade_data.symbol)
        span.set_attribute("trade.amount", trade_data.amount)
        
        # Trade execution logic
        result = await execute_trade(trade_data)
        return result
```

## Security Considerations

### Development Security

#### Secrets Management
- Environment variables for sensitive data
- Separate configurations per environment
- No hardcoded credentials in code

#### Network Security
- Internal Docker networks
- Port exposure only for necessary services
- Service-to-service authentication

#### Data Protection
- Encrypted data at rest (production)
- Secure communication between services
- Regular security updates

### Production Security Enhancements

#### Authentication & Authorization
- JWT token validation
- Role-based access control (RBAC)
- API key management
- OAuth 2.0 integration

#### Infrastructure Security
- Container image scanning
- Network policies
- Secrets encryption
- Audit logging

## Troubleshooting

### Common Issues

#### Service Startup Issues
```bash
# Check service status
make status-dev

# View service logs
make logs-dev SERVICE=<service-name>

# Check health endpoints
curl http://localhost:8080/actuator/health
curl http://localhost:8001/health
```

#### Database Connection Issues
```bash
# Check database status
make shell-postgres
psql -U alphintra -d alphintra_dev -c "SELECT version();"

# Check TimescaleDB
make shell-timescaledb
psql -U timescale -d timescaledb_dev -c "SELECT * FROM timescaledb_information.hypertables;"
```

#### Memory Issues
```bash
# Check Docker resource usage
docker stats

# Increase Docker memory limits
# Update Docker Desktop settings or system limits
```

#### Port Conflicts
```bash
# Check port usage
lsof -i :8080
netstat -tulpn | grep LISTEN

# Update port mappings in environment files
```

### Debug Mode

#### Enable Debug Logging
```bash
# Set debug environment variables
export LOG_LEVEL=DEBUG
export SQL_ECHO=true

# Start with debug configuration
make start-dev
```

#### Remote Debugging
```bash
# Connect to debug ports
# Gateway: localhost:5005
# Auth Service: localhost:5001
# Trading API: localhost:5002
```

## Performance Optimization

### Database Performance

#### PostgreSQL Tuning
```conf
# postgresql.conf optimizations
shared_buffers = 25% of RAM
effective_cache_size = 75% of RAM
work_mem = (RAM * 0.25) / max_connections
maintenance_work_mem = RAM / 16
```

#### TimescaleDB Optimization
```sql
-- Enable compression for older data
SELECT add_compression_policy('market_data', INTERVAL '7 days');

-- Continuous aggregates for analytics
CREATE MATERIALIZED VIEW market_data_1h
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 hour', time) AS bucket,
       symbol,
       avg(price) as avg_price,
       max(price) as high_price,
       min(price) as low_price,
       sum(volume) as total_volume
FROM market_data
GROUP BY bucket, symbol;
```

### Application Performance

#### Redis Optimization
```conf
# Redis performance tuning
tcp-keepalive 60
tcp-backlog 511
timeout 300
databases 16
```

#### Kafka Performance
```conf
# Producer optimization
batch.size=65536
linger.ms=10
compression.type=lz4
acks=1

# Consumer optimization
fetch.min.bytes=1024
fetch.max.wait.ms=500
max.poll.records=1000
```

## Next Steps

### Phase 2 Preparation

1. **Kubernetes Setup**: Prepare for local Kubernetes deployment
2. **Service Mesh**: Istio integration for advanced traffic management
3. **CI/CD Pipeline**: Automated testing and deployment
4. **Advanced Monitoring**: Custom metrics and alerting

### Phase 2 Components

1. **Container Orchestration**: 
   - Local Kubernetes cluster with k3d
   - Helm charts for service deployment
   - Horizontal Pod Autoscaling

2. **Service Mesh**:
   - Istio installation and configuration
   - Traffic management and security policies
   - Service mesh observability

3. **CI/CD Pipeline**:
   - GitHub Actions workflows
   - Automated testing pipeline
   - Cloud Build integration

4. **Advanced Analytics**:
   - Stream processing with Apache Flink
   - Batch processing with Apache Spark
   - Real-time analytics dashboards

### Migration to GCP

1. **Infrastructure as Code**: Terraform modules for GCP resources
2. **Cloud Native Services**: Migration to managed GCP services
3. **Production Deployment**: Blue-green deployment strategies
4. **Monitoring & Alerting**: Production-grade observability

## Conclusion

Phase 1 provides a comprehensive foundation for the Alphintra trading platform development. The local GCP simulation environment enables rapid development and testing while maintaining compatibility with production cloud services.

The infrastructure supports:
- **Scalable Architecture**: Microservices-based design
- **Development Productivity**: Hot reloading and debugging tools
- **Production Readiness**: Performance optimization and monitoring
- **Cloud Migration**: Seamless transition to GCP services

This foundation prepares the platform for Phase 2 enhancements and eventual production deployment on Google Cloud Platform.