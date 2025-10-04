# Alphintra Local GCP Simulation

This document provides comprehensive instructions for setting up and running a complete local simulation of the Alphintra Trading Platform that mimics Google Cloud Platform (GCP) services using local alternatives.

## 🏗️ Architecture Overview

Our local GCP simulation provides a complete development environment that mirrors the production GCP setup:

### GCP Service Mapping

| GCP Service | Local Alternative | Purpose |
|-------------|-------------------|----------|
| Cloud SQL (PostgreSQL) | PostgreSQL Container | User data, configurations |
| Cloud SQL (TimescaleDB) | TimescaleDB Container | Time-series market data |
| Cloud Memorystore (Redis) | Redis Cluster | Caching, session storage |
| Cloud Pub/Sub | Apache Kafka | Event streaming, messaging |
| Google Kubernetes Engine (GKE) | k3d Cluster | Container orchestration |
| Istio Service Mesh | Istio on k3d | Traffic management, security |
| Cloud Storage | MinIO | Object storage for ML models |
| Vertex AI | MLflow + Custom ML Services | ML model management |
| Cloud Monitoring | Prometheus + Grafana | Metrics and monitoring |
| Cloud Trace | Jaeger | Distributed tracing |
| Cloud Logging | ELK Stack (Optional) | Centralized logging |

### Infrastructure Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     Local GCP Simulation                        │
├─────────────────────────────────────────────────────────────────┤
│  Docker Compose (Infrastructure Layer)                         │
│  ├── PostgreSQL (User Data)                                    │
│  ├── TimescaleDB (Time Series Data)                           │
│  ├── Redis Cluster (Caching)                                  │
│  ├── Kafka + Zookeeper (Event Streaming)                     │
│  ├── MLflow (ML Model Registry)                               │
│  ├── MinIO (Object Storage)                                   │
│  ├── Prometheus (Metrics)                                     │
│  ├── Grafana (Dashboards)                                     │
│  └── Jaeger (Tracing)                                         │
├─────────────────────────────────────────────────────────────────┤
│  Kubernetes (Application Layer)                                │
│  ├── k3d Cluster (3 nodes)                                    │
│  ├── Istio Service Mesh                                       │
│  ├── MetalLB (Load Balancer)                                  │
│  ├── Application Services:                                    │
│  │   ├── Gateway Service                                       │
│  │   ├── Auth Service                                          │
│  │   ├── Trading API                                           │
│  │   ├── Strategy Engine                                       │
│  │   └── Broker Simulator                                      │
│  └── Observability Stack                                      │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

Ensure you have the following tools installed:

```bash
# Docker and Docker Compose
docker --version
docker-compose --version

# Kubernetes tools
kubectl version --client
k3d version

# Optional: Istio CLI
istioctl version --remote=false
```

### Installation Links

- **Docker**: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)
- **k3d**: [https://k3d.io/v5.4.6/#installation](https://k3d.io/v5.4.6/#installation)
- **kubectl**: [https://kubernetes.io/docs/tasks/tools/](https://kubernetes.io/docs/tasks/tools/)

### One-Command Setup

```bash
# Navigate to project root
cd /path/to/Alphintra

# Run the comprehensive setup script
./infra/scripts/setup-local-gcp.sh
```

This script will:
1. ✅ Check all prerequisites
2. 📦 Start Docker infrastructure services
3. ☸️ Create and configure k3d cluster
4. 🕸️ Install Istio service mesh
5. 📊 Deploy monitoring stack
6. 🎯 Display access information

## 📋 Manual Setup (Step by Step)

If you prefer to set up components individually:

### Step 1: Infrastructure Services (Docker)

```bash
# Start all infrastructure services
docker-compose up -d

# Check service health
docker-compose ps

# View logs for specific service
docker-compose logs -f postgres
```

### Step 2: Kubernetes Cluster

```bash
# Create k3d cluster with enhanced configuration
./infra/scripts/setup-k8s-cluster.sh

# Verify cluster
kubectl get nodes
kubectl get namespaces
```

### Step 3: Istio Service Mesh

```bash
# Install Istio with observability tools
./infra/scripts/install-istio.sh

# Verify Istio installation
istioctl proxy-status
kubectl get pods -n istio-system
```

### Step 4: Deploy Applications

```bash
# Deploy all application services
kubectl apply -k infra/kubernetes/overlays/dev/

# Check deployment status
kubectl get pods -n alphintra-dev
kubectl get services -n alphintra-dev
```

## 🔗 Service Access

### Infrastructure Services (Docker)

| Service | URL | Credentials |
|---------|-----|-------------|
| PostgreSQL | `localhost:5432` | `alphintra/password123` |
| TimescaleDB | `localhost:5433` | `alphintra/password123` |
| Redis Master | `localhost:6379` | No auth |
| Redis Replica | `localhost:6380` | No auth |
| Kafka | `localhost:9092` | No auth |
| Zookeeper | `localhost:2181` | No auth |
| MLflow | `http://localhost:5000` | No auth |
| MinIO Console | `http://localhost:9001` | `admin/password123` |
| MinIO API | `http://localhost:9000` | `admin/password123` |

### Kubernetes Services (Port Forward Required)

```bash
# Prometheus
kubectl port-forward -n istio-system svc/prometheus 9090:9090
# Access: http://localhost:9090

# Grafana
kubectl port-forward -n istio-system svc/grafana 3000:3000
# Access: http://localhost:3000

# Jaeger
kubectl port-forward -n istio-system svc/jaeger 16686:16686
# Access: http://localhost:16686

# Kiali
kubectl port-forward -n istio-system svc/kiali 20001:20001
# Access: http://localhost:20001

# Application Gateway (through Istio)
kubectl port-forward -n istio-system svc/istio-ingressgateway 8080:80
# Access: http://localhost:8080
```

### Application Services

Once deployed, applications are accessible through the Istio ingress gateway:

- **API Gateway**: `http://localhost:8080/`
- **Auth Service**: `http://localhost:8080/api/auth/`
- **Trading API**: `http://localhost:8080/api/trading/`
- **Health Checks**: `http://localhost:8080/actuator/health`

## 🛠️ Development Workflow

### Building and Deploying Applications

```bash
# Build application images
./scripts/build-images.sh

# Tag for local registry
docker tag alphintra/gateway:latest localhost:5001/alphintra/gateway:dev-latest
docker tag alphintra/auth-service:latest localhost:5001/alphintra/auth-service:dev-latest
# ... repeat for other services

# Push to local registry
docker push localhost:5001/alphintra/gateway:dev-latest
docker push localhost:5001/alphintra/auth-service:dev-latest
# ... repeat for other services

# Deploy to Kubernetes
kubectl apply -k infra/kubernetes/overlays/dev/

# Watch deployment progress
kubectl get pods -n alphintra-dev -w
```

### Updating Configurations

```bash
# Update Kubernetes manifests
kubectl apply -k infra/kubernetes/overlays/dev/

# Restart specific deployment
kubectl rollout restart deployment/gateway -n alphintra-dev

# Update ConfigMaps
kubectl create configmap app-config --from-literal=LOG_LEVEL=INFO -n alphintra-dev --dry-run=client -o yaml | kubectl apply -f -
```

### Monitoring and Debugging

```bash
# View application logs
kubectl logs -f deployment/gateway -n alphintra-dev

# Execute into pod
kubectl exec -it deployment/gateway -n alphintra-dev -- /bin/bash

# Check service mesh status
istioctl proxy-status
istioctl proxy-config cluster gateway-xxx-xxx.alphintra-dev

# View metrics
curl http://localhost:8080/actuator/prometheus

# Check database connections
docker exec -it alphintra_postgres_1 psql -U alphintra -d alphintra_db
```

## 📊 Monitoring and Observability

### Prometheus Metrics

- **URL**: `http://localhost:9090`
- **Key Metrics**:
  - `http_requests_total` - HTTP request counts
  - `http_request_duration_seconds` - Request latency
  - `jvm_memory_used_bytes` - JVM memory usage
  - `kafka_consumer_lag` - Kafka consumer lag

### Grafana Dashboards

- **URL**: `http://localhost:3000`
- **Default Login**: `admin/admin`
- **Pre-configured Dashboards**:
  - Istio Service Mesh
  - Spring Boot Applications
  - Kafka Monitoring
  - Infrastructure Overview

### Jaeger Tracing

- **URL**: `http://localhost:16686`
- **Features**:
  - Distributed request tracing
  - Service dependency mapping
  - Performance analysis
  - Error tracking

### Kiali Service Mesh

- **URL**: `http://localhost:20001`
- **Features**:
  - Service topology visualization
  - Traffic flow analysis
  - Security policy management
  - Configuration validation

## 🔧 Configuration Management

### Environment Variables

Key configuration options for development:

```bash
# Application Configuration
SPRING_PROFILES_ACTIVE=kubernetes,dev
LOGGING_LEVEL_ROOT=DEBUG
MANAGEMENT_TRACING_SAMPLING_PROBABILITY=1.0

# Database Configuration
SPRING_DATASOURCE_URL=jdbc:postgresql://postgres.default.svc.cluster.local:5432/alphintra_db
SPRING_JPA_SHOW_SQL=true

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka.default.svc.cluster.local:9092
KAFKA_AUTO_OFFSET_RESET=earliest

# Redis Configuration
REDIS_HOST=redis-master.default.svc.cluster.local
REDIS_PORT=6379

# ML Configuration
MLFLOW_TRACKING_URI=http://mlflow.default.svc.cluster.local:5000
FEATURE_STORE_URL=http://minio.default.svc.cluster.local:9000
```

### Secrets Management

```bash
# Create secrets
kubectl create secret generic app-secrets \
  --from-literal=jwt-secret=dev-secret \
  --from-literal=db-password=password123 \
  -n alphintra-dev

# Update secrets
kubectl patch secret app-secrets -n alphintra-dev -p '{"data":{"jwt-secret":"bmV3LXNlY3JldA=="}}'
```

## 🧪 Testing

### Health Checks

```bash
# Check all service health
for service in gateway auth-service trading-api strategy-engine broker-simulator; do
  echo "Checking $service..."
  kubectl exec -n alphintra-dev deployment/$service -- curl -s http://localhost:8080/actuator/health | jq '.status'
done
```

### API Testing

```bash
# Test authentication
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}'

# Test trading API
curl -X GET http://localhost:8080/api/trading/positions \
  -H "Authorization: Bearer <token>"
```

### Load Testing

```bash
# Install hey (HTTP load testing tool)
go install github.com/rakyll/hey@latest

# Run load test
hey -n 1000 -c 10 http://localhost:8080/api/trading/health
```

## 🔄 Maintenance

### Cleanup

```bash
# Stop and remove all containers
docker-compose down -v

# Delete k3d cluster
k3d cluster delete alphintra-cluster
k3d registry delete alphintra-registry

# Clean up Docker resources
docker system prune -a
```

### Backup and Restore

```bash
# Backup PostgreSQL
docker exec alphintra_postgres_1 pg_dump -U alphintra alphintra_db > backup.sql

# Restore PostgreSQL
docker exec -i alphintra_postgres_1 psql -U alphintra alphintra_db < backup.sql

# Backup Kubernetes configs
kubectl get all -n alphintra-dev -o yaml > k8s-backup.yaml
```

### Updates

```bash
# Update Docker images
docker-compose pull
docker-compose up -d

# Update Kubernetes manifests
kubectl apply -k infra/kubernetes/overlays/dev/

# Update Istio
istioctl upgrade
```

## 🐛 Troubleshooting

### Common Issues

1. **Services not starting**:
   ```bash
   # Check Docker logs
   docker-compose logs <service-name>
   
   # Check resource usage
   docker stats
   ```

2. **Kubernetes pods failing**:
   ```bash
   # Describe pod for events
   kubectl describe pod <pod-name> -n alphintra-dev
   
   # Check pod logs
   kubectl logs <pod-name> -n alphintra-dev
   ```

3. **Network connectivity issues**:
   ```bash
   # Test DNS resolution
   kubectl exec -it deployment/gateway -n alphintra-dev -- nslookup postgres.default.svc.cluster.local
   
   # Test service connectivity
   kubectl exec -it deployment/gateway -n alphintra-dev -- curl http://auth-service:8080/actuator/health
   ```

4. **Istio issues**:
   ```bash
   # Check Istio proxy status
   istioctl proxy-status
   
   # Analyze configuration
   istioctl analyze -n alphintra-dev
   ```

### Performance Tuning

```bash
# Increase resource limits
kubectl patch deployment gateway -n alphintra-dev -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "gateway",
          "resources": {
            "limits": {"memory": "1Gi", "cpu": "500m"},
            "requests": {"memory": "512Mi", "cpu": "250m"}
          }
        }]
      }
    }
  }
}'

# Scale deployments
kubectl scale deployment gateway --replicas=3 -n alphintra-dev
```

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [k3d Documentation](https://k3d.io/)
- [Istio Documentation](https://istio.io/latest/docs/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)

## 🤝 Contributing

To contribute to the local GCP simulation setup:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly in the local environment
5. Submit a pull request

## 📞 Support

For issues with the local setup:

1. Check the troubleshooting section above
2. Review logs for error messages
3. Create an issue in the repository with:
   - Environment details
   - Error logs
   - Steps to reproduce

---

**Happy Trading! 🚀📈**