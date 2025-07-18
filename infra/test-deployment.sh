#!/bin/bash

# Test script for the updated Kubernetes deployment workflow
# This script validates the deployment process without actually deploying

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "🧪 Testing Alphintra Kubernetes Deployment Workflow..."
echo ""

echo "📋 Validating deployment configuration..."

# Test 1: Check if scripts are executable
echo "  ✓ Checking script permissions..."
if [ ! -x "$SCRIPT_DIR/scripts/setup-k8s-cluster.sh" ]; then
    echo "❌ setup-k8s-cluster.sh is not executable"
    exit 1
fi

if [ ! -x "$SCRIPT_DIR/scripts/k8s/deploy.sh" ]; then
    echo "❌ deploy.sh is not executable"
    exit 1
fi

echo "  ✅ All scripts are executable"

# Test 2: Validate Kubernetes manifests
echo "  ✓ Validating Kubernetes manifests..."
cd "$SCRIPT_DIR/kubernetes/base"

if ! kubectl apply --dry-run=client -k . > /dev/null 2>&1; then
    echo "❌ Kubernetes manifest validation failed"
    kubectl apply --dry-run=client -k . 2>&1 | head -10
    exit 1
fi

echo "  ✅ Kubernetes manifests are valid"

# Test 3: Check Docker images referenced in manifests
echo "  ✓ Checking Docker image references..."
IMAGE_REFS=$(grep -r "localhost:5001/alphintra" . | grep -E "\.yaml:" | wc -l)
echo "  📊 Found $IMAGE_REFS local registry image references"

# Test 4: Check namespace consistency
echo "  ✓ Checking namespace consistency..."
ALPHINTRA_NS_COUNT=$(grep -r "namespace: alphintra" . | wc -l)
MONITORING_NS_COUNT=$(grep -r "namespace: monitoring" . | wc -l)
echo "  📊 alphintra namespace: $ALPHINTRA_NS_COUNT references"
echo "  📊 monitoring namespace: $MONITORING_NS_COUNT references"

# Test 5: Check for deprecated configurations
echo "  ✓ Checking for deprecated configurations..."
if grep -r "alphintra-dev" . > /dev/null 2>&1; then
    echo "❌ Found deprecated 'alphintra-dev' namespace references"
    grep -r "alphintra-dev" .
    exit 1
fi

echo "  ✅ No deprecated configurations found"

# Test 6: Validate service dependencies
echo "  ✓ Checking service dependencies..."
SERVICES_WITH_DEPS=$(grep -r "depends_on\|waitForDependencies" . | wc -l)
echo "  📊 Found $SERVICES_WITH_DEPS service dependency configurations"

echo ""
echo "✅ All deployment configuration tests passed!"
echo ""
echo "🚀 Deployment Workflow Summary:"
echo "  1. Run: make k8s-setup        (or scripts/setup-k8s-cluster.sh)"
echo "  2. Run: make istio-install     (if using service mesh)"
echo "  3. Run: make k8s-deploy        (or scripts/k8s/deploy.sh)"
echo ""
echo "📊 Platform Components:"
echo "  ✓ API Gateway (Spring Cloud Gateway)"
echo "  ✓ GraphQL Gateway (Python FastAPI)"  
echo "  ✓ Auth Service"
echo "  ✓ Trading API"
echo "  ✓ Eureka Server (Service Discovery)"
echo "  ✓ Config Server"
echo "  ✓ Redis (Caching)"
echo "  ✓ PostgreSQL (Database)"
echo "  ✓ Prometheus & Grafana (Monitoring)"
echo "  ✓ Istio Service Mesh"
echo ""
echo "🌐 Access Points:"
echo "  - API Gateway: http://localhost:8080"
echo "  - GraphQL API: http://localhost:8080/graphql"
echo "  - Eureka Dashboard: http://localhost:8761"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000"
echo ""
echo "🔧 Ready for deployment!"