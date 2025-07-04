# Kubernetes Quick Start Guide

## Prerequisites
- Docker installed and running
- k3d installed (`brew install k3d` or `curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash`)
- kubectl installed (`brew install kubectl`)

## 🚀 Quick Setup (5 minutes)

### 1. Start Cluster
```bash
# Navigate to k3d setup directory
cd infra/kubernetes/local-k3d

# Run the setup script
./setup.sh

# Verify cluster is running
k3d cluster list
kubectl get nodes
```

### 2. Build and Import Service Images
```bash
# Build no-code service (example)
cd src/backend/no-code-service
docker build -t no-code-service:latest .

# Import to k3d cluster
k3d image import no-code-service:latest -c alphintra-dev

# Repeat for other services as needed
```

### 3. Deploy Services
```bash
# Deploy no-code service
kubectl apply -f infra/kubernetes/overlays/no-code-service-test/deployment.yaml
kubectl apply -f infra/kubernetes/overlays/no-code-service-test/ingress.yaml

# Check deployment status
kubectl get pods -n alphintra -w
```

### 4. Access Service
```bash
# Port forward for testing
kubectl port-forward svc/no-code-service 8080:8000 -n alphintra

# Test health endpoint
curl http://localhost:8080/health

# Access API docs
open http://localhost:8080/docs
```

## 📋 Common Operations

### Check Service Status
```bash
kubectl get all -n alphintra
```

### View Logs
```bash
kubectl logs -f deployment/no-code-service -n alphintra
```

### Restart Service
```bash
kubectl rollout restart deployment/no-code-service -n alphintra
```

### Stop Everything
```bash
k3d cluster stop alphintra-dev
```

## 🔧 Troubleshooting

### Service Won't Start
1. Check if image exists: `docker images | grep no-code-service`
2. Import image: `k3d image import no-code-service:latest -c alphintra-dev`
3. Check logs: `kubectl logs deployment/no-code-service -n alphintra`

### Can't Access Service
1. Check pod status: `kubectl get pods -n alphintra`
2. Port forward: `kubectl port-forward svc/no-code-service 8080:8000 -n alphintra`
3. Test: `curl http://localhost:8080/health`

## 📚 Full Documentation
For complete details, see [CLUSTER_MANAGEMENT.md](./CLUSTER_MANAGEMENT.md)