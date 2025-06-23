# Alphintra Infrastructure

## 🚀 Overview

This directory contains the complete infrastructure setup for the Alphintra Trading Platform. The infrastructure is designed to simulate Google Cloud Platform (GCP) services locally for development and seamlessly deploy to production on GCP.

## 📁 Directory Structure

```
infra/
├── docker/                     # Docker Compose configurations
│   ├── docker-compose.yml      # Main orchestration file
│   ├── docker-compose.base.yml # Base infrastructure services
│   ├── docker-compose.dev.yml  # Development environment
│   ├── docker-compose.prod.yml # Production environment
│   ├── .env.example            # Environment variables template
│   ├── .env.dev                # Development environment variables
│   └── config/                 # Service configurations
│       ├── redis/              # Redis configuration
│       ├── nginx/              # Nginx proxy configuration
│       ├── kafka/              # Kafka configuration
│       └── vault/              # Vault configuration
├── terraform/                  # Infrastructure as Code (upcoming)
├── kubernetes/                 # Kubernetes manifests (upcoming)
├── scripts/                    # Automation scripts
│   ├── check-prerequisites.sh  # Prerequisites checker
│   ├── setup-monitoring.sh     # Monitoring stack setup
│   └── ...                     # Additional automation scripts
├── docs/                       # Infrastructure documentation
└── Makefile                    # Infrastructure automation
```

## 🛠️ Quick Start

### Prerequisites

1. **System Requirements**:
   - 8GB+ RAM
   - 20GB+ available disk space
   - Docker 20.10+
   - Docker Compose 1.29+

2. **Check Prerequisites**:
   ```bash
   cd infra
   ./scripts/check-prerequisites.sh
   ```

3. **Install Dependencies**:
   ```bash
   make install
   ```

### Development Environment

1. **Setup Development Environment**:
   ```bash
   make setup-dev
   ```

2. **Start Development Environment**:
   ```bash
   make start-dev
   ```

3. **Check Status**:
   ```bash
   make status-dev
   make health-dev
   ```

4. **Access Services**:
   - **API Gateway**: http://localhost:8080
   - **Grafana**: http://localhost:3001 (admin/admin123)
   - **Prometheus**: http://localhost:9090
   - **MLflow**: http://localhost:5000
   - **Jaeger**: http://localhost:16686
   - **Kafka UI**: http://localhost:8084
   - **Redis Commander**: http://localhost:8085
   - **MinIO Console**: http://localhost:9001

### Production Environment

1. **Setup Production Environment**:
   ```bash
   make setup-prod
   ```

2. **Start Production Environment**:
   ```bash
   make start-prod
   ```

## 🏗️ Architecture

### GCP Service Mapping

| GCP Service | Local Equivalent | Purpose |
|-------------|------------------|---------|
| **Cloud SQL** | PostgreSQL + TimescaleDB | Primary database + time-series data |
| **Cloud Memorystore** | Redis Cluster | Caching and session storage |
| **Cloud Pub/Sub** | Kafka + Pub/Sub Emulator | Event streaming and messaging |
| **Vertex AI** | MLflow + Local ML | Model training and serving |
| **Cloud Storage** | MinIO | Object storage for artifacts |
| **GKE** | k3d/minikube | Container orchestration |
| **Cloud Dataflow** | Apache Flink | Stream processing |
| **Cloud Dataproc** | Apache Spark | Batch processing |

### Infrastructure Components

#### Core Services
- **PostgreSQL**: Multi-database setup for service isolation
- **TimescaleDB**: High-performance time-series data storage
- **Redis Cluster**: Master-replica setup for high availability
- **Apache Kafka**: Event streaming with Zookeeper coordination
- **MLflow**: ML lifecycle management with PostgreSQL backend
- **MinIO**: S3-compatible object storage

#### Application Services
- **API Gateway**: Spring Cloud Gateway for routing and authentication
- **Auth Service**: FastAPI authentication and authorization
- **Trading API**: Core trading functionality and portfolio management
- **Strategy Engine**: Trading strategy execution and backtesting
- **Broker Connector**: Exchange integrations (Binance, Coinbase)
- **Broker Simulator**: Mock exchange for testing

#### Monitoring Stack
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Dashboards and visualization
- **Jaeger**: Distributed tracing and performance monitoring
- **AlertManager**: Alert routing and notification

## 🔧 Commands Reference

### Environment Management
```bash
# Setup environments
make setup-dev          # Setup development environment
make setup-staging      # Setup staging environment
make setup-prod         # Setup production environment

# Start/Stop environments
make start-dev          # Start development environment
make stop-dev           # Stop development environment
make restart-dev        # Restart development environment

# Environment status
make status-dev         # Show service status
make health-dev         # Check service health
make logs-dev           # View all logs
make logs-dev SERVICE=trading-api  # View specific service logs
```

### Development Operations
```bash
# Service management
make shell-trading-api  # Open shell in service container
make debug-trading-api  # Debug specific service

# Data operations
make backup-dev         # Backup development data
make restore-dev        # Restore from backup
make migrate-dev        # Run database migrations

# Testing
make test-unit          # Run unit tests
make test-integration   # Run integration tests
make test-e2e           # Run end-to-end tests
```

### Monitoring
```bash
make monitor-dev        # Open monitoring dashboards
make prometheus         # Open Prometheus
make grafana           # Open Grafana
make mlflow            # Open MLflow
```

### Cleanup
```bash
make clean             # Clean Docker resources
make reset-dev         # Reset development environment completely
```

## 📊 Monitoring & Observability

### Metrics Collection
- **Application Metrics**: Order latency, execution rates, portfolio performance
- **System Metrics**: CPU, memory, disk usage, network I/O
- **Business Metrics**: Revenue, active users, trading volume

### Dashboards
- **System Overview**: Infrastructure health and performance
- **Trading Metrics**: Trading performance and analytics
- **Application Performance**: Service-level metrics and traces

### Alerting
- **High Order Latency**: Alert when order execution takes too long
- **Low Trading Volume**: Alert when trading activity drops
- **Service Health**: Alert when services go down
- **Resource Usage**: Alert on high CPU/memory/disk usage

## 🔐 Security

### Development Security
- Environment-specific configurations
- No hardcoded credentials
- Internal Docker networks
- Service-to-service authentication

### Production Security
- JWT token validation
- Role-based access control (RBAC)
- Encrypted data at rest
- Container image scanning
- Network policies
- Audit logging

## 🐛 Troubleshooting

### Common Issues

#### Service Startup Issues
```bash
# Check service status
make status-dev

# View service logs
make logs-dev SERVICE=<service-name>

# Check health endpoints
curl http://localhost:8080/actuator/health
```

#### Database Connection Issues
```bash
# Check database status
make shell-postgres
psql -U alphintra -d alphintra_dev -c "SELECT version();"
```

#### Port Conflicts
```bash
# Check port usage
lsof -i :8080

# Update port mappings in .env files
```

#### Memory Issues
```bash
# Check Docker resource usage
docker stats

# Increase Docker memory limits in Docker Desktop
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
make start-dev

# Connect to debug ports
# Gateway: localhost:5005
# Auth Service: localhost:5001
# Trading API: localhost:5002
```

## 📚 Documentation

### Architecture Documentation
- [Phase 1: Enhanced Local GCP Simulation](docs/infrastructure/Phase1-Enhanced-Local-GCP-Simulation.md)
- [Service Configuration Guide](docs/infrastructure/Service-Configuration.md)
- [Monitoring Setup Guide](docs/infrastructure/Monitoring-Setup.md)

### Development Guides
- [Local Development Workflow](docs/development/Local-Development.md)
- [Testing Guide](docs/development/Testing.md)
- [Debugging Guide](docs/development/Debugging.md)

### Deployment Guides
- [Production Deployment](docs/deployment/Production-Deployment.md)
- [GCP Migration Guide](docs/deployment/GCP-Migration.md)
- [CI/CD Setup](docs/deployment/CICD-Setup.md)

## 🚧 Roadmap

### Phase 1 ✅ (Current)
- ✅ Enhanced Docker Compose setup
- ✅ Multi-environment configurations
- ✅ GCP service simulation
- ✅ Comprehensive monitoring
- ✅ Development automation

### Phase 2 🔄 (Next)
- ⏳ Local Kubernetes cluster setup
- ⏳ Istio service mesh integration
- ⏳ CI/CD pipeline implementation
- ⏳ Advanced stream processing

### Phase 3 📋 (Future)
- 📋 Terraform infrastructure modules
- 📋 GCP production deployment
- 📋 Advanced security features
- 📋 Multi-region setup

## 🤝 Contributing

### Development Workflow
1. Create feature branch from `main`
2. Make changes in the `infra/` directory
3. Test changes with development environment
4. Update documentation as needed
5. Submit pull request

### Testing Infrastructure Changes
```bash
# Test development environment
make setup-dev
make start-dev
make health-dev

# Run infrastructure tests
make test-infrastructure

# Validate configurations
make validate-config
```

### Adding New Services
1. Add service to appropriate Docker Compose file
2. Update environment variables
3. Add monitoring configuration
4. Update documentation
5. Add health checks

## 📞 Support

### Getting Help
- Check troubleshooting section above
- Review documentation in `docs/` directory
- Check existing GitHub issues
- Create new issue with detailed description

### Reporting Issues
When reporting issues, please include:
- Environment details (dev/staging/prod)
- Error messages and logs
- Steps to reproduce
- System information

### Feature Requests
- Describe the use case
- Explain the benefits
- Provide implementation suggestions
- Consider backward compatibility

---

## 🎯 Next Steps

After setting up the infrastructure:

1. **Explore the Platform**:
   ```bash
   make quick-start
   ```

2. **Review Documentation**:
   - Read the [Phase 1 documentation](docs/infrastructure/Phase1-Enhanced-Local-GCP-Simulation.md)
   - Explore service configurations
   - Understand monitoring setup

3. **Customize for Your Needs**:
   - Update environment variables
   - Modify service configurations
   - Add custom dashboards
   - Configure alerting

4. **Prepare for Production**:
   - Review security settings
   - Plan resource requirements
   - Set up external integrations
   - Configure backup strategies

Happy trading! 🚀📈