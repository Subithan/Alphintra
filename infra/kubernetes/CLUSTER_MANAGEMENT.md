# Kubernetes Cluster Management Guide

## Overview
This guide provides comprehensive instructions for managing the Alphintra microservices in your local k3d cluster.

## Table of Contents
- [Cluster Operations](#cluster-operations)
- [Service Management](#service-management)
- [Monitoring & Debugging](#monitoring--debugging)
- [Communication & Testing](#communication--testing)
- [Troubleshooting](#troubleshooting)

---

## Cluster Operations

### Start Cluster
```bash
# Start existing k3d cluster
k3d cluster start alphintra-dev

# Create new cluster (if doesn't exist)
cd infra/kubernetes/local-k3d
./setup.sh
```

### Stop Cluster
```bash
# Stop cluster (preserves data)
k3d cluster stop alphintra-dev

# Delete cluster (removes all data)
k3d cluster delete alphintra-dev
```

### List Clusters
```bash
# List all k3d clusters
k3d cluster list

# Get cluster info
kubectl cluster-info

# Check current context
kubectl config current-context
```

### Check Cluster Status
```bash
# Check cluster nodes
kubectl get nodes

# Check system pods
kubectl get pods -n kube-system

# Check cluster resources
kubectl top nodes
kubectl top pods -A
```

---

## Service Management

### Available Services
- `auth-service` - Authentication service
- `trading-api` - Trading API service
- `strategy-engine` - Strategy execution engine
- `broker-simulator` - Broker simulation service
- `gateway` - API Gateway
- `no-code-service` - No-code workflow service

### Start Services

#### Start Individual Service
```bash
# Deploy specific service
kubectl apply -f infra/kubernetes/base/auth-service-deployment.yaml

# Deploy no-code service (with ingress)
kubectl apply -f infra/kubernetes/overlays/no-code-service-test/deployment.yaml
kubectl apply -f infra/kubernetes/overlays/no-code-service-test/ingress.yaml
```

#### Start All Services
```bash
# Deploy all base services
kubectl apply -k infra/kubernetes/base/

# Deploy dev overlay
kubectl apply -k infra/kubernetes/overlays/dev/
```

#### Import Docker Images
```bash
# Import service images to k3d cluster
k3d image import no-code-service:latest -c alphintra-dev
k3d image import auth-service:latest -c alphintra-dev
k3d image import trading-api:latest -c alphintra-dev
k3d image import strategy-engine:latest -c alphintra-dev
k3d image import gateway:latest -c alphintra-dev
k3d image import broker-simulator:latest -c alphintra-dev
```

### Stop Services

#### Stop Individual Service
```bash
# Scale down to 0 replicas
kubectl scale deployment no-code-service --replicas=0 -n alphintra

# Delete specific deployment
kubectl delete deployment no-code-service -n alphintra

# Delete service and ingress
kubectl delete svc no-code-service -n alphintra
kubectl delete ingress no-code-service-ingress -n alphintra
```

#### Stop All Services
```bash
# Delete all deployments in namespace
kubectl delete deployments --all -n alphintra

# Delete entire namespace (removes everything)
kubectl delete namespace alphintra
```

### List Services

#### List All Resources
```bash
# List all resources in alphintra namespace
kubectl get all -n alphintra

# List specific resource types
kubectl get deployments -n alphintra
kubectl get services -n alphintra
kubectl get pods -n alphintra
kubectl get ingress -n alphintra
```

#### List Specific Service Resources
```bash
# List no-code service resources
kubectl get all -n alphintra -l app=no-code-service

# List auth service resources
kubectl get all -n alphintra -l app=auth-service
```

#### List with Details
```bash
# Wide output with more details
kubectl get pods -n alphintra -o wide

# Get resource YAML
kubectl get deployment no-code-service -n alphintra -o yaml

# Describe resources
kubectl describe pod <pod-name> -n alphintra
kubectl describe svc no-code-service -n alphintra
```

### Check Service Status

#### Pod Status
```bash
# Check pod status
kubectl get pods -n alphintra

# Check specific service pods
kubectl get pods -n alphintra -l app=no-code-service

# Watch pod status changes
kubectl get pods -n alphintra -w
```

#### Service Health
```bash
# Check service endpoints
kubectl get endpoints -n alphintra

# Check ingress status
kubectl get ingress -n alphintra

# Check service details
kubectl describe svc no-code-service -n alphintra
```

#### Resource Usage
```bash
# Check resource usage
kubectl top pods -n alphintra
kubectl top nodes

# Check resource limits/requests
kubectl describe pod <pod-name> -n alphintra | grep -A 5 "Limits\|Requests"
```

---

## Monitoring & Debugging

### View Logs
```bash
# View current logs
kubectl logs deployment/no-code-service -n alphintra

# Follow logs (real-time)
kubectl logs -f deployment/no-code-service -n alphintra

# View logs from previous container restart
kubectl logs deployment/no-code-service -n alphintra --previous

# View logs with timestamps
kubectl logs deployment/no-code-service -n alphintra --timestamps

# View last N lines
kubectl logs deployment/no-code-service -n alphintra --tail=50

# View logs from all containers in pod
kubectl logs pod/<pod-name> -n alphintra --all-containers
```

### Debug Pods
```bash
# Execute commands in pod
kubectl exec -it deployment/no-code-service -n alphintra -- /bin/bash

# Run one-off commands
kubectl exec deployment/no-code-service -n alphintra -- ps aux
kubectl exec deployment/no-code-service -n alphintra -- env

# Copy files to/from pod
kubectl cp <local-file> alphintra/<pod-name>:/tmp/
kubectl cp alphintra/<pod-name>:/tmp/file ./local-file
```

### Check Events
```bash
# View cluster events
kubectl get events -n alphintra --sort-by='.lastTimestamp'

# Watch events in real-time
kubectl get events -n alphintra -w

# Filter events by object
kubectl get events -n alphintra --field-selector involvedObject.name=no-code-service
```

---

## Communication & Testing

### Internal Service Communication
```bash
# Services communicate via DNS names:
# Format: <service-name>.<namespace>.svc.cluster.local:<port>

# Examples:
# http://no-code-service.alphintra.svc.cluster.local:8000
# http://auth-service.alphintra.svc.cluster.local:8000
# http://trading-api.alphintra.svc.cluster.local:8000
```

### External Access

#### Port Forwarding
```bash
# Forward service port to localhost
kubectl port-forward svc/no-code-service 8080:8000 -n alphintra

# Forward pod port directly
kubectl port-forward pod/<pod-name> 8080:8000 -n alphintra

# Access via: http://localhost:8080
```

#### Ingress Access
```bash
# Add to /etc/hosts for local development
echo "127.0.0.1 no-code-service.local" >> /etc/hosts

# Access via: http://no-code-service.local
# Or via path: http://localhost/no-code
```

### Test Service Endpoints

#### Health Checks
```bash
# Port forward and test
kubectl port-forward svc/no-code-service 8080:8000 -n alphintra &
curl http://localhost:8080/health
pkill -f "kubectl port-forward"

# Test via ingress
curl http://no-code-service.local/health
```

#### API Testing
```bash
# Test API documentation
curl http://localhost:8080/docs

# Test OpenAPI spec
curl http://localhost:8080/openapi.json

# Test specific endpoints
curl -X POST http://localhost:8080/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{"name": "test-workflow"}'
```

#### Internal Testing (from another pod)
```bash
# Create a test pod for internal testing
kubectl run test-pod --image=curlimages/curl -n alphintra --rm -it -- sh

# Inside the test pod:
curl http://no-code-service:8000/health
curl http://auth-service:8000/health
curl http://trading-api:8000/health
```

### Load Testing
```bash
# Simple load test with curl
for i in {1..100}; do
  curl -s http://localhost:8080/health > /dev/null &
done
wait

# Monitor during load test
kubectl top pods -n alphintra
kubectl get events -n alphintra -w
```

---

## Troubleshooting

### Common Issues

#### Image Pull Errors
```bash
# Check if image exists locally
docker images | grep no-code-service

# Import image to k3d cluster
k3d image import no-code-service:latest -c alphintra-dev

# Restart deployment
kubectl rollout restart deployment/no-code-service -n alphintra
```

#### Pod Not Starting
```bash
# Check pod events
kubectl describe pod <pod-name> -n alphintra

# Check logs for errors
kubectl logs <pod-name> -n alphintra

# Check resource constraints
kubectl top pods -n alphintra
kubectl describe node
```

#### Service Not Accessible
```bash
# Check service endpoints
kubectl get endpoints no-code-service -n alphintra

# Check if pods are ready
kubectl get pods -n alphintra -l app=no-code-service

# Verify service selector matches pod labels
kubectl get svc no-code-service -n alphintra -o yaml
kubectl get pods -n alphintra -l app=no-code-service --show-labels
```

#### Network Issues
```bash
# Test internal DNS resolution
kubectl exec -it deployment/no-code-service -n alphintra -- nslookup auth-service

# Check network policies
kubectl get networkpolicies -n alphintra

# Test connectivity between services
kubectl exec -it deployment/no-code-service -n alphintra -- wget -qO- http://auth-service:8000/health
```

### Restart Services
```bash
# Restart deployment (rolling restart)
kubectl rollout restart deployment/no-code-service -n alphintra

# Check rollout status
kubectl rollout status deployment/no-code-service -n alphintra

# View rollout history
kubectl rollout history deployment/no-code-service -n alphintra

# Rollback to previous version
kubectl rollout undo deployment/no-code-service -n alphintra
```

### Resource Management
```bash
# Scale service replicas
kubectl scale deployment no-code-service --replicas=3 -n alphintra

# Update resource limits
kubectl patch deployment no-code-service -n alphintra -p '{"spec":{"template":{"spec":{"containers":[{"name":"no-code-service","resources":{"limits":{"memory":"1Gi","cpu":"1000m"}}}]}}}}'

# Check resource usage
kubectl top pods -n alphintra
```

---

## Quick Reference Commands

### Most Used Commands
```bash
# Check all services status
kubectl get all -n alphintra

# View service logs
kubectl logs -f deployment/no-code-service -n alphintra

# Port forward for testing
kubectl port-forward svc/no-code-service 8080:8000 -n alphintra

# Restart service
kubectl rollout restart deployment/no-code-service -n alphintra

# Debug pod
kubectl exec -it deployment/no-code-service -n alphintra -- /bin/bash

# Import docker image
k3d image import <image-name>:latest -c alphintra-dev
```

### Environment Variables
```bash
# Set commonly used namespace
export NAMESPACE=alphintra

# Use shorter commands
alias k='kubectl'
alias kga='kubectl get all -n $NAMESPACE'
alias kgp='kubectl get pods -n $NAMESPACE'
alias kgs='kubectl get svc -n $NAMESPACE'
alias kd='kubectl describe'
```

---

## Security Considerations

### Service-to-Service Authentication
- Services should use proper authentication mechanisms
- Consider implementing mutual TLS for internal communication
- Use Kubernetes service accounts and RBAC

### Network Policies
```bash
# Apply network policies for security
kubectl apply -f infra/kubernetes/security/network-policies/

# Check current network policies
kubectl get networkpolicies -n alphintra
```

### Secrets Management
```bash
# Create secrets for sensitive data
kubectl create secret generic db-credentials \
  --from-literal=username=alphintra \
  --from-literal=password=secure-password \
  -n alphintra

# Use secrets in deployments
kubectl get secrets -n alphintra
```

---

This documentation provides comprehensive guidance for managing your Alphintra microservices in the k3d cluster. Keep this file updated as your infrastructure evolves.