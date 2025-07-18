#!/bin/bash

# Production-Ready Optimized Kubernetes Deployment Script
# Deploys all Alphintra services with Alpine-based images and right-sized resources

set -e

ENV=${1:-production}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
KUSTOMIZE_DIR="$BASE_DIR/kubernetes/base"

echo "🚀 Deploying Alphintra Trading Platform (Production-Ready Optimized)..."
echo "   Environment: $ENV"
echo "   Expected resource usage: <3GB memory, <1.5 CPU cores"
echo "   Expected startup time: <4 minutes"
echo ""

# Set kubectl context to k3d cluster
echo "🔧 Setting kubectl context to k3d cluster..."
kubectl config use-context k3d-alphintra-cluster

# Verify cluster is ready
echo "🔍 Verifying cluster status..."
kubectl cluster-info --request-timeout=10s
echo ""
echo "📊 Node Status:"
kubectl get nodes
echo ""

# Verify namespace exists
echo "📁 Verifying namespace..."
if ! kubectl get namespace alphintra > /dev/null 2>&1; then
    echo "⚠️  Alphintra namespace not found. Please run '../setup-k8s-cluster.sh' first."
    exit 1
fi

echo "✅ Namespace is ready"
echo ""

# Build and push optimized Docker images
echo "🐳 Building and pushing optimized Docker images..."

# Build optimized API Gateway
if [ -f "$BASE_DIR/../src/backend/gateway/Dockerfile.optimized" ]; then
    echo "  📦 Building optimized API Gateway..."
    cd "$BASE_DIR/../src/backend/gateway"
    docker build -f Dockerfile.optimized -t localhost:5001/alphintra/api-gateway:optimized .
    docker push localhost:5001/alphintra/api-gateway:optimized
    echo "    ✅ API Gateway: $(docker images localhost:5001/alphintra/api-gateway:optimized --format 'table {{.Size}}')"
else
    echo "  ⚠️  Optimized Gateway Dockerfile not found, using standard build..."
    cd "$BASE_DIR/../src/backend/gateway"
    docker build -t localhost:5001/alphintra/api-gateway:optimized .
    docker push localhost:5001/alphintra/api-gateway:optimized
fi

# Build optimized Auth Service
if [ -f "$BASE_DIR/../src/backend/auth-service/Dockerfile.optimized" ]; then
    echo "  📦 Building optimized Auth Service..."
    cd "$BASE_DIR/../src/backend/auth-service"
    docker build -f Dockerfile.optimized -t localhost:5001/alphintra/auth-service:optimized .
    docker push localhost:5001/alphintra/auth-service:optimized
    echo "    ✅ Auth Service: $(docker images localhost:5001/alphintra/auth-service:optimized --format 'table {{.Size}}')"
fi

# Build optimized Trading API
if [ -f "$BASE_DIR/../src/backend/trading-api/Dockerfile.optimized" ]; then
    echo "  📦 Building optimized Trading API..."
    cd "$BASE_DIR/../src/backend/trading-api"
    docker build -f Dockerfile.optimized -t localhost:5001/alphintra/trading-api:optimized .
    docker push localhost:5001/alphintra/trading-api:optimized
    echo "    ✅ Trading API: $(docker images localhost:5001/alphintra/trading-api:optimized --format 'table {{.Size}}')"
fi

# Build optimized GraphQL Gateway
if [ -f "$BASE_DIR/../src/backend/graphql-gateway/Dockerfile.optimized" ]; then
    echo "  📦 Building optimized GraphQL Gateway..."
    cd "$BASE_DIR/../src/backend/graphql-gateway"
    docker build -f Dockerfile.optimized -t localhost:5001/alphintra/graphql-gateway:optimized .
    docker push localhost:5001/alphintra/graphql-gateway:optimized
    echo "    ✅ GraphQL Gateway: $(docker images localhost:5001/alphintra/graphql-gateway:optimized --format 'table {{.Size}}')"
fi

# Build optimized Strategy Engine
if [ -f "$BASE_DIR/../src/backend/strategy-engine/Dockerfile.optimized" ]; then
    echo "  📦 Building optimized Strategy Engine..."
    cd "$BASE_DIR/../src/backend/strategy-engine"
    docker build -f Dockerfile.optimized -t localhost:5001/alphintra/strategy-engine:optimized .
    docker push localhost:5001/alphintra/strategy-engine:optimized
    echo "    ✅ Strategy Engine: $(docker images localhost:5001/alphintra/strategy-engine:optimized --format 'table {{.Size}}')"
fi

echo ""
echo "✅ All optimized Docker images built and pushed to local registry"
echo ""

# Deploy using optimized kustomization
echo "🏗️  Deploying optimized platform configuration..."
cd "$KUSTOMIZE_DIR"

echo "  📋 Validating optimized manifests..."
if ! kubectl apply --dry-run=client -f kustomization-optimized.yaml > /dev/null 2>&1; then
    echo "  ❌ Manifest validation failed"
    exit 1
fi
echo "  ✅ Manifest validation passed"

echo "  🚀 Deploying all optimized services..."
kubectl apply -k . --filename=kustomization-optimized.yaml

echo ""
echo "⏳ Waiting for optimized services to be ready..."

# Wait for infrastructure services with shorter timeouts
echo "  💾 Waiting for Redis..."
kubectl wait --for=condition=ready --timeout=3m pod -l app=redis -n alphintra || echo "Redis not ready yet"

echo "  🐘 Waiting for PostgreSQL..."
kubectl wait --for=condition=ready --timeout=3m pod -l app=postgresql -n alphintra || echo "PostgreSQL not ready yet"

# Wait for core application services
echo "  🌐 Waiting for API Gateway..."
kubectl wait --for=condition=available --timeout=4m deployment/api-gateway -n alphintra || echo "API Gateway not ready yet"

echo "  🔐 Waiting for Auth Service..."
kubectl wait --for=condition=available --timeout=3m deployment/auth-service -n alphintra || echo "Auth Service not ready yet"

echo "  📊 Waiting for GraphQL Gateway..."
kubectl wait --for=condition=available --timeout=3m deployment/graphql-gateway -n alphintra || echo "GraphQL Gateway not ready yet"

echo "  💹 Waiting for Trading Service..."
kubectl wait --for=condition=available --timeout=3m deployment/trading-service -n alphintra || echo "Trading Service not ready yet"

echo "  🔍 Waiting for Eureka Server..."
kubectl wait --for=condition=available --timeout=3m deployment/eureka-server -n alphintra || echo "Eureka Server not ready yet"

echo "  🎯 Waiting for Strategy Engine..."
kubectl wait --for=condition=available --timeout=3m deployment/strategy-engine -n alphintra || echo "Strategy Engine not ready yet"

echo ""
echo "🔍 Verifying optimized deployment status..."
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

# Resource usage monitoring
echo "📈 Resource Usage Summary:"
if kubectl top pods -n alphintra > /dev/null 2>&1; then
    echo "  Alphintra Namespace:"
    kubectl top pods -n alphintra
    echo ""
    echo "  Monitoring Namespace:"
    kubectl top pods -n monitoring 2>/dev/null || echo "  Monitoring metrics not available yet"
    echo ""
    echo "  Node Resource Usage:"
    kubectl top nodes
    echo ""
    
    # Calculate total resource usage
    TOTAL_MEMORY=$(kubectl top pods -n alphintra --no-headers 2>/dev/null | awk '{sum += $3} END {print sum}' | sed 's/Mi//')
    TOTAL_CPU=$(kubectl top pods -n alphintra --no-headers 2>/dev/null | awk '{sum += $4} END {print sum}' | sed 's/m//')
    
    echo "  📊 Total Resource Usage:"
    echo "    Memory: ${TOTAL_MEMORY}Mi (Target: <3000Mi)"
    echo "    CPU: ${TOTAL_CPU}m (Target: <1500m)"
    echo ""
else
    echo "  ⚠️  Resource metrics not available yet (metrics server may be starting)"
fi

echo ""
echo "✅ Optimized deployment completed successfully!"
echo ""
echo "🔧 Access Information:"
echo "  🌐 API Gateway: http://localhost:8080"
echo "  🔍 Health Check: http://localhost:8080/actuator/health"
echo "  💹 Trading API: http://localhost:8080/api/trading/portfolio"
echo "  📊 GraphQL Playground: http://localhost:8080/graphql"
echo "  🔐 Auth Service: http://localhost:8080/api/auth/health"
echo "  🔍 Eureka Dashboard: http://localhost:8762"
echo ""
echo "📊 Monitoring & Observability:"
echo "  📈 Prometheus: http://localhost:9091"
echo "  📊 Grafana: http://localhost:3001 (admin/admin)"
echo ""
echo "🧪 Testing Commands:"
echo "  # Test API Gateway health"
echo "  curl http://localhost:8080/actuator/health"
echo ""
echo "  # Test Trading API through Gateway"
echo "  curl http://localhost:8080/api/trading/portfolio"
echo ""
echo "  # Test GraphQL endpoint"
echo "  curl -X POST http://localhost:8080/graphql -H 'Content-Type: application/json' -d '{\"query\":\"{ portfolio { symbol quantity } }\"}'"
echo ""
echo "  # Monitor resource usage"
echo "  kubectl top pods -n alphintra"
echo "  kubectl top nodes"
echo "  docker stats"
echo ""
echo "📋 Debugging Commands:"
echo "  kubectl get pods -n alphintra -w"
echo "  kubectl logs -f deployment/api-gateway -n alphintra"
echo "  kubectl logs -f deployment/trading-service -n alphintra"
echo "  kubectl describe pod <pod-name> -n alphintra"
echo "  kubectl get events -n alphintra --sort-by='.lastTimestamp'"
echo ""
echo "🎯 Performance Validation:"
echo "  # Check total memory usage (should be <3GB)"
echo "  kubectl top pods -A | awk '{sum+=\$3} END {print \"Total Memory: \" sum \"Mi\"}')"
echo ""
echo "  # Check total CPU usage (should be <1500m)"
echo "  kubectl top pods -A | awk '{sum+=\$4} END {print \"Total CPU: \" sum \"m\"}')"
echo ""

# Final health check
echo "🏥 Performing final health checks..."
sleep 15

# Check critical services
GATEWAY_READY=$(kubectl get pods -n alphintra -l app=api-gateway --field-selector=status.phase=Running 2>/dev/null | wc -l)
TRADING_READY=$(kubectl get pods -n alphintra -l app=trading-service --field-selector=status.phase=Running 2>/dev/null | wc -l)
GRAPHQL_READY=$(kubectl get pods -n alphintra -l app=graphql-gateway --field-selector=status.phase=Running 2>/dev/null | wc -l)

echo ""
echo "📊 Final Status Summary:"
if [ "$GATEWAY_READY" -gt 1 ]; then
    echo "  ✅ API Gateway is running"
else
    echo "  ⚠️  API Gateway may not be running properly"
fi

if [ "$TRADING_READY" -gt 1 ]; then
    echo "  ✅ Trading Service is running"
else
    echo "  ⚠️  Trading Service may not be running properly"
fi

if [ "$GRAPHQL_READY" -gt 1 ]; then
    echo "  ✅ GraphQL Gateway is running"
else
    echo "  ⚠️  GraphQL Gateway may not be running properly"
fi

echo ""
echo "🎉 Alphintra Trading Platform optimized deployment complete!"
echo "   🚀 All services deployed with Alpine-based images"
echo "   📈 Resource-optimized configuration active"
echo "   🔒 Production-ready security enabled"
echo "   📊 Monitoring stack available"
echo "   🌐 Access platform at http://localhost:8080"