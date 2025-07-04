# Service Endpoints Reference

## Available Services

| Service | Internal URL | External Port | Health Check | API Docs |
|---------|-------------|---------------|--------------|----------|
| no-code-service | `http://no-code-service.alphintra.svc.cluster.local:8000` | 8080 | `/health` | `/docs` |
| auth-service | `http://auth-service.alphintra.svc.cluster.local:8000` | 8081 | `/health` | `/docs` |
| trading-api | `http://trading-api.alphintra.svc.cluster.local:8000` | 8082 | `/health` | `/docs` |
| strategy-engine | `http://strategy-engine.alphintra.svc.cluster.local:8000` | 8083 | `/health` | `/docs` |
| broker-simulator | `http://broker-simulator.alphintra.svc.cluster.local:8000` | 8084 | `/health` | `/docs` |
| gateway | `http://gateway.alphintra.svc.cluster.local:8080` | 8085 | `/actuator/health` | `/swagger-ui` |

## Port Forwarding Commands

### No-Code Service
```bash
kubectl port-forward svc/no-code-service 8080:8000 -n alphintra
# Access: http://localhost:8080
```

### Auth Service
```bash
kubectl port-forward svc/auth-service 8081:8000 -n alphintra
# Access: http://localhost:8081
```

### Trading API
```bash
kubectl port-forward svc/trading-api 8082:8000 -n alphintra
# Access: http://localhost:8082
```

### Strategy Engine
```bash
kubectl port-forward svc/strategy-engine 8083:8000 -n alphintra
# Access: http://localhost:8083
```

### Broker Simulator
```bash
kubectl port-forward svc/broker-simulator 8084:8000 -n alphintra
# Access: http://localhost:8084
```

### Gateway (Spring Boot)
```bash
kubectl port-forward svc/gateway 8085:8080 -n alphintra
# Access: http://localhost:8085
```

## API Testing Examples

### Health Check All Services
```bash
# No-Code Service
curl http://localhost:8080/health

# Auth Service
curl http://localhost:8081/health

# Trading API
curl http://localhost:8082/health

# Strategy Engine
curl http://localhost:8083/health

# Broker Simulator
curl http://localhost:8084/health

# Gateway
curl http://localhost:8085/actuator/health
```

### Test No-Code Service Endpoints
```bash
# Get workflows
curl http://localhost:8080/api/v1/workflows

# Create workflow
curl -X POST http://localhost:8080/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-workflow",
    "description": "A test trading workflow"
  }'

# Get workflow by ID
curl http://localhost:8080/api/v1/workflows/{workflow_id}

# Execute workflow
curl -X POST http://localhost:8080/api/v1/workflows/{workflow_id}/execute
```

### Test Auth Service Endpoints
```bash
# Register user
curl -X POST http://localhost:8081/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "firstName": "Test",
    "lastName": "User"
  }'

# Login
curl -X POST http://localhost:8081/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

## Service Communication

### Internal Service-to-Service Communication
Services can communicate with each other using Kubernetes DNS:

```python
# Example: No-Code Service calling Auth Service
import requests

# Internal URL (from within cluster)
auth_url = "http://auth-service.alphintra.svc.cluster.local:8000"
response = requests.get(f"{auth_url}/api/v1/users/profile", 
                       headers={"Authorization": f"Bearer {token}"})
```

### Database Connections
```python
# PostgreSQL connection string
DATABASE_URL = "postgresql://alphintra:alphintra@alphintra-postgres.alphintra.svc.cluster.local:5432/alphintra"

# Redis connection string  
REDIS_URL = "redis://alphintra-redis.alphintra.svc.cluster.local:6379/0"
```

## Ingress Routes

### Available Ingress Routes
```yaml
# no-code-service.local
http://no-code-service.local/          # Full service access
http://localhost/no-code/              # Path-based routing

# Add to /etc/hosts:
echo "127.0.0.1 no-code-service.local" >> /etc/hosts
```

## Development Workflow

### 1. Start All Services
```bash
# Start cluster
k3d cluster start alphintra-dev

# Deploy all services
kubectl apply -k infra/kubernetes/overlays/dev/

# Wait for services to be ready
kubectl wait --for=condition=ready pod -l app=no-code-service -n alphintra --timeout=300s
```

### 2. Port Forward for Development
```bash
# Terminal 1: No-Code Service
kubectl port-forward svc/no-code-service 8080:8000 -n alphintra

# Terminal 2: Auth Service  
kubectl port-forward svc/auth-service 8081:8000 -n alphintra

# Terminal 3: Trading API
kubectl port-forward svc/trading-api 8082:8000 -n alphintra
```

### 3. Test End-to-End Flow
```bash
# 1. Register user
curl -X POST http://localhost:8081/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "dev@test.com", "password": "dev123", "firstName": "Dev", "lastName": "User"}'

# 2. Login and get token
TOKEN=$(curl -X POST http://localhost:8081/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "dev@test.com", "password": "dev123"}' | jq -r '.access_token')

# 3. Create workflow
curl -X POST http://localhost:8080/api/v1/workflows \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "my-trading-strategy", "description": "Automated trading workflow"}'

# 4. Execute workflow
curl -X POST http://localhost:8080/api/v1/workflows/1/execute \
  -H "Authorization: Bearer $TOKEN"
```

## Monitoring

### Check Service Health
```bash
# Check all pod status
kubectl get pods -n alphintra

# Check service endpoints
kubectl get endpoints -n alphintra

# Check resource usage
kubectl top pods -n alphintra
```

### View Service Logs
```bash
# Follow logs for all services
kubectl logs -f deployment/no-code-service -n alphintra &
kubectl logs -f deployment/auth-service -n alphintra &
kubectl logs -f deployment/trading-api -n alphintra &
kubectl logs -f deployment/strategy-engine -n alphintra &

# Stop following logs
pkill -f "kubectl logs"
```

## Environment Variables

### No-Code Service
```bash
DATABASE_URL=postgresql://alphintra:alphintra@alphintra-postgres:5432/alphintra
REDIS_URL=redis://alphintra-redis:6379/0
ENVIRONMENT=development
AUTH_SERVICE_URL=http://auth-service:8000
TRADING_API_URL=http://trading-api:8000
```

### Auth Service
```bash
DATABASE_URL=postgresql://alphintra:alphintra@alphintra-postgres:5432/alphintra
JWT_SECRET=your-jwt-secret
JWT_EXPIRATION=86400
REDIS_URL=redis://alphintra-redis:6379/0
```

### Trading API
```bash
DATABASE_URL=postgresql://alphintra:alphintra@alphintra-postgres:5432/alphintra
BROKER_SIMULATOR_URL=http://broker-simulator:8000
REDIS_URL=redis://alphintra-redis:6379/0
RISK_MANAGEMENT_URL=http://risk-management:8000
```