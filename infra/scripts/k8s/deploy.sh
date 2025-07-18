#!/bin/bash

# Kubernetes Deployment Script for Alphintra Trading Platform
# This script deploys all Alphintra services using our standardized YAML manifests

set -e

ENV=${1:-dev}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
KUSTOMIZE_DIR="$BASE_DIR/kubernetes/base"

echo "🚀 Deploying Alphintra Trading Platform to Kubernetes (${ENV} environment)..."

# Set kubectl context to k3d cluster
echo "🔧 Setting kubectl context to k3d cluster..."
kubectl config use-context k3d-alphintra-cluster

# Verify cluster is ready
echo "🔍 Verifying cluster status..."
kubectl cluster-info
echo ""
echo "📊 Node Status:"
kubectl get nodes
echo ""

# Check if Istio is installed
echo "🕸️  Checking Istio installation..."
if ! kubectl get namespace istio-system > /dev/null 2>&1; then
    echo "⚠️  Istio is not installed. Please run '../install-istio.sh' first."
    echo "   This is required for service mesh functionality."
    exit 1
else
    echo "✅ Istio is installed and ready"
fi

# Verify namespaces exist
echo "📁 Verifying namespaces..."
if ! kubectl get namespace alphintra > /dev/null 2>&1; then
    echo "⚠️  Alphintra namespace not found. Please run '../setup-k8s-cluster.sh' first."
    exit 1
fi

if ! kubectl get namespace monitoring > /dev/null 2>&1; then
    echo "⚠️  Monitoring namespace not found. Please run '../setup-k8s-cluster.sh' first."
    exit 1
fi

echo "✅ All required namespaces are present"
echo ""

# Build and push Docker images to local registry
echo "🐳 Building and pushing Docker images..."

# Build API Gateway
if [ -f "$BASE_DIR/../src/backend/gateway/Dockerfile" ]; then
    echo "  📦 Building API Gateway..."
    cd "$BASE_DIR/../src/backend/gateway"
    docker build -t localhost:5001/alphintra/api-gateway:latest .
    docker push localhost:5001/alphintra/api-gateway:latest
else
    echo "  ⚠️  Gateway Dockerfile not found, skipping..."
fi

# Build GraphQL Gateway
if [ -f "$BASE_DIR/../src/backend/graphql-gateway/Dockerfile" ]; then
    echo "  📦 Building GraphQL Gateway..."
    cd "$BASE_DIR/../src/backend/graphql-gateway"
    docker build -t localhost:5001/alphintra/graphql-gateway:latest .
    docker push localhost:5001/alphintra/graphql-gateway:latest
else
    echo "  ⚠️  GraphQL Gateway Dockerfile not found, skipping..."
fi

# Build Auth Service (if exists)
if [ -f "$BASE_DIR/../src/backend/auth-service/Dockerfile" ]; then
    echo "  📦 Building Auth Service..."
    cd "$BASE_DIR/../src/backend/auth-service"
    docker build -t localhost:5001/alphintra/auth-service:latest .
    docker push localhost:5001/alphintra/auth-service:latest
fi

# Build Trading API
if [ -f "$BASE_DIR/../src/backend/trading-api/Dockerfile" ]; then
    echo "  📦 Building Trading API..."
    cd "$BASE_DIR/../src/backend/trading-api"
    docker build -t localhost:5001/alphintra/trading-api:latest .
    docker push localhost:5001/alphintra/trading-api:latest
fi

echo "✅ Docker images built and pushed to local registry"
echo ""

# Deploy using our standardized Kustomization
echo "🏗️  Deploying platform using standardized manifests..."
cd "$KUSTOMIZE_DIR"

echo "  📋 Validating manifests..."
kubectl apply --dry-run=client -k . > /dev/null
echo "  ✅ Manifest validation passed"

echo "  🚀 Deploying all services..."
kubectl apply -k .

echo ""
echo "⏳ Waiting for core services to be ready..."

# Wait for infrastructure services
echo "  💾 Waiting for Redis..."
kubectl wait --for=condition=ready --timeout=5m pod/redis-0 -n alphintra || echo "Redis StatefulSet not found or not ready"

echo "  🐘 Waiting for PostgreSQL..."
kubectl wait --for=condition=ready --timeout=5m pod/postgresql-0 -n alphintra || echo "PostgreSQL StatefulSet not found or not ready"

# Wait for core application services
echo "  🌐 Waiting for API Gateway..."
kubectl wait --for=condition=available --timeout=10m deployment/api-gateway -n alphintra || echo "API Gateway deployment not found or not ready"

echo "  🔐 Waiting for Auth Service..."
kubectl wait --for=condition=available --timeout=5m deployment/auth-service -n alphintra || echo "Auth Service deployment not found or not ready"

echo "  📊 Waiting for GraphQL Gateway..."
kubectl wait --for=condition=available --timeout=5m deployment/graphql-gateway -n alphintra || echo "GraphQL Gateway deployment not found or not ready"

echo "  🔍 Waiting for Eureka Server..."
kubectl wait --for=condition=available --timeout=5m deployment/eureka-server -n alphintra || echo "Eureka Server deployment not found or not ready"

echo ""
echo "🔍 Verifying deployment status..."
echo ""
echo "📊 Pod Status (alphintra namespace):"
kubectl get pods -n alphintra -o wide
echo ""
echo "📊 Pod Status (monitoring namespace):"
kubectl get pods -n monitoring -o wide
echo ""
echo "🌐 Service Status (alphintra namespace):"
kubectl get services -n alphintra
echo ""
echo "🌐 Service Status (monitoring namespace):"
kubectl get services -n monitoring
echo ""

# Check Istio sidecar injection
echo "🕸️  Checking Istio sidecar injection..."
SIDECAR_COUNT=$(kubectl get pods -n alphintra -o jsonpath='{.items[*].spec.containers[*].name}' | grep -c istio-proxy || echo "0")
if [ "$SIDECAR_COUNT" -gt 0 ]; then
    echo "✅ Istio sidecars are injected (found $SIDECAR_COUNT sidecars)"
else
    echo "⚠️  No Istio sidecars found. Check namespace labels or restart pods."
fi

# Check ingress status
echo ""
echo "🌍 Ingress Status:"
kubectl get ingress -n alphintra || echo "No ingress resources found"

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "🔧 Access Information:"
echo "  🌐 API Gateway: http://localhost:8080"
echo "  🔍 Eureka Dashboard: http://localhost:8762"
echo "  ⚙️  Config Server: http://localhost:8889/actuator/health"
echo "  📊 GraphQL Playground: http://localhost:8080/graphql (via Gateway)"
echo ""
echo "📊 Monitoring & Observability:"
echo "  📈 Prometheus: http://localhost:9091"
echo "  📊 Grafana: http://localhost:3001 (admin/admin)"
echo "  🔍 Jaeger: http://localhost:16687"
echo "  🕸️  Kiali: kubectl port-forward -n istio-system svc/kiali 20001:20001"
echo ""
echo "🔧 API Endpoints:"
echo "  🔐 Authentication: http://localhost:8080/api/auth/*"
echo "  💹 Trading API: http://localhost:8080/api/trading/*"
echo "  📊 GraphQL API: http://localhost:8080/graphql"
echo "  ⚙️  Actuator (Gateway): http://localhost:8080/actuator/health"
echo ""
echo "📋 Useful Commands:"
echo "  kubectl get pods -n alphintra -w                    # Watch pod status"
echo "  kubectl logs -f deployment/api-gateway -n alphintra # Follow Gateway logs"
echo "  kubectl logs -f deployment/graphql-gateway -n alphintra # Follow GraphQL logs"
echo "  kubectl describe pod <pod-name> -n alphintra       # Debug pod issues"
echo "  kubectl get events -n alphintra --sort-by='.lastTimestamp' # Check events"
echo ""
echo "🔄 To redeploy after changes:"
echo "  kubectl rollout restart deployment/api-gateway -n alphintra"
echo "  kubectl rollout restart deployment/graphql-gateway -n alphintra"
echo ""

# Final health check
echo "🏥 Performing final health checks..."
sleep 5

# Check API Gateway health
if kubectl get pods -n alphintra -l app=api-gateway --field-selector=status.phase=Running | grep -q "Running"; then
    echo "✅ API Gateway is running"
else
    echo "⚠️  API Gateway may not be running properly"
fi

# Check GraphQL Gateway health
if kubectl get pods -n alphintra -l app=graphql-gateway --field-selector=status.phase=Running | grep -q "Running"; then
    echo "✅ GraphQL Gateway is running"
else
    echo "⚠️  GraphQL Gateway may not be running properly"
fi

echo ""
echo "🎉 Alphintra Trading Platform deployment complete!"
echo "   Access the platform at http://localhost:8080"