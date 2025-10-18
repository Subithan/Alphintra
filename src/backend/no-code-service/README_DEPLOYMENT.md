# No-Code Service Deployment Guide

This guide explains how to deploy the Alphintra No-Code Service to Google Cloud Platform using the established cloud build methodology.

## Prerequisites

1. **Google Cloud SDK** installed and authenticated
2. **kubectl** configured with cluster access
3. **gcloud** project set to `alphintra-472817`
4. **Docker** installed (for local testing)

## Architecture Overview

The no-code service is a FastAPI-based Python microservice that:
- Provides visual workflow builder for trading strategies
- Connects to Cloud SQL PostgreSQL database
- Uses Cloud SQL Proxy for secure database connections
- Implements JWT-based authentication with user association
- Supports both REST and GraphQL APIs
- Includes comprehensive caching and performance optimizations

## Deployment Process

### 1. Database Setup

First, create the Cloud SQL database and user:

```bash
# Run the database setup script
./scripts/setup_cloud_sql_database.sh
```

This script will:
- Create Cloud SQL instance if it doesn't exist
- Create database `alphintra_nocode_service`
- Create user `nocode_service_user` with password `alphintra@123`
- Configure necessary permissions
- Generate connection strings

### 2. Create Kubernetes Secrets

Create the required secrets for database connectivity:

```bash
# Create secrets for the service
./scripts/create_secrets.sh
```

If you prefer to create secrets manually:

```bash
# Get connection name from Cloud SQL
CONNECTION_NAME=$(gcloud sql instances describe alphintra-db-instance --format="value(connectionName)")

# Create database URL
DATABASE_URL="postgresql+pg8000://nocode_service_user:alphintra@123@localhost:5432/alphintra_nocode_service?host=/cloudsql/${CONNECTION_NAME}&unix_sock=/cloudsql/${CONNECTION_NAME}/.s.PGSQL.5432"

# Create secret
kubectl create secret generic no-code-service-secrets \
  --namespace=alphintra \
  --from-literal=database-url="$DATABASE_URL" \
  --from-literal=cloud-sql-connection-name="$CONNECTION_NAME"
```

### 3. Deploy the Service

Deploy using Kustomize:

```bash
# Apply the Kubernetes manifests
kubectl apply -k dev
```

### 4. Verify Deployment

Check the deployment status:

```bash
# Check deployment
kubectl get deployment no-code-service -n alphintra

# Check pods
kubectl get pods -l app=no-code-service -n alphintra

# Check service
kubectl get service no-code-service -n alphintra

# View logs
kubectl logs -f deployment/no-code-service -n alphintra
```

### 5. Test the Service

Test the health endpoint:

```bash
# Port forward to test locally
kubectl port-forward -n alphintra service/no-code-service 8006:8006

# Test health endpoint
curl http://localhost:8006/health
```

## Cloud Build CI/CD

The service includes an optimized Cloud Build configuration (`cloudbuild.yaml`) that:

- **Builds in <60 seconds** using high-performance machines
- **Implements caching** for Python dependencies via GCS
- **Runs parallel execution** for faster builds
- **Deploys automatically** to Kubernetes
- **Includes health checks** and verification

### Triggering Builds

Builds are automatically triggered by:
- Commits to the main branch
- Pull requests
- Manual triggers

To manually trigger a build:

```bash
# Using Cloud Build
gcloud builds submit --config=cloudbuild.yaml .

# Or use the GitHub Actions workflow
git push origin main
```

## Configuration

### Environment Variables

Key environment variables (configured via ConfigMap and secrets):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `CLOUD_SQL_CONNECTION_NAME` | Cloud SQL instance connection name | - |
| `REDIS_URL` | Redis connection string | `redis://:alphintra_redis_pass@redis-primary.alphintra.svc.cluster.local:6379/2` |
| `AUTH_SERVICE_URL` | Auth service URL | `http://auth-service.alphintra.svc.cluster.local:8009` |
| `AIML_SERVICE_URL` | AI/ML service URL | `http://ai-ml-strategy-service.alphintra.svc.cluster.local:8002` |
| `DEV_MODE` | Development mode flag | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Resource Limits

The deployment includes configured resource limits:
- **Memory**: 512Mi request, 1Gi limit
- **CPU**: 250m request, 500m limit
- **Replicas**: 2 (with HPA up to 10)

### Health Checks

Comprehensive health check configuration:
- **Liveness Probe**: `/health` every 30s (60s delay)
- **Readiness Probe**: `/health` every 10s (30s delay)
- **Startup Probe**: `/health` every 10s (300s timeout)

## Database Management

### Migrations

The service uses Alembic for database migrations:

```bash
# Enter the running container
kubectl exec -it deployment/no-code-service -n alphintra -- bash

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Show migration history
alembic history
```

### Initialization

The service automatically initializes the database on startup if tables don't exist, using the `init_database.py` script.

## Monitoring and Logging

### Logs

View logs for different components:

```bash
# Application logs
kubectl logs -f deployment/no-code-service -n alphintra

# Cloud SQL proxy logs
kubectl logs -f deployment/no-code-service -c cloud-sql-proxy -n alphintra
```

### Metrics

Prometheus metrics are exposed at `/metrics` endpoint.

### Health Monitoring

The service provides comprehensive health endpoints:
- `/health` - Basic health check
- `/metrics` - Prometheus metrics

## Security

### Authentication

- JWT tokens are forwarded from the service gateway
- Local JWT extraction with auth service fallback
- User association enforced across all data operations

### Database Security

- Cloud SQL Proxy for secure connections
- Dedicated database user with limited permissions
- Connection via private IP

### Container Security

- Non-root user execution (UID: 1001)
- Minimal runtime image
- All capabilities dropped
- Read-only filesystem (except required directories)

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check Cloud SQL proxy logs
   kubectl logs deployment/no-code-service -c cloud-sql-proxy -n alphintra

   # Verify secrets
   kubectl get secret no-code-service-secrets -o yaml -n alphintra
   ```

2. **Pod Crashing**
   ```bash
   # Check pod events
   kubectl describe pod -l app=no-code-service -n alphintra

   # Check logs
   kubectl logs -p deployment/no-code-service -n alphintra
   ```

3. **Build Failures**
   ```bash
   # Check Cloud Build logs
   gcloud builds list --limit=1
   gcloud builds log BUILD_ID
   ```

### Performance Optimization

- **Cache Hit Rate**: Monitor GCS cache utilization
- **Build Time**: Target <60 seconds
- **Memory Usage**: Monitor pod memory consumption
- **Database Connections**: Use connection pooling

## Development

### Local Development

For local development with Cloud SQL:

```bash
# Start Cloud SQL proxy locally
./cloud_sql_proxy -instances=CONNECTION_NAME=tcp:5432

# Set environment variables
export DATABASE_URL="postgresql+pg8000://nocode_service_user:alphintra@123@localhost:5432/alphintra_nocode_service"
export DEV_MODE=true

# Run the service
python main.py
```

### Testing

```bash
# Run tests locally
python -m pytest

# Test database migrations
alembic upgrade head
```

## Support

For deployment issues:
1. Check the troubleshooting section above
2. Review Cloud Build logs
3. Examine Kubernetes events and logs
4. Verify Cloud SQL connectivity
5. Check secrets and configurations

The deployment follows the established patterns from auth-service and service-gateway for consistency and reliability.