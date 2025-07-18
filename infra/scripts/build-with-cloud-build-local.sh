#!/bin/bash

# Direct Docker Build Solution (replaces deprecated cloud-build-local)
# Builds optimized distroless images locally without Google Cloud project

set -e

# Configuration
LOCAL_REGISTRY="localhost:5001"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🚀 Building Alphintra with Direct Docker Build..."
echo "   Using Google Distroless images"
echo "   No Google Cloud project required"
echo "   Local registry: $LOCAL_REGISTRY"
echo "   Alternative to deprecated cloud-build-local"
echo ""

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check if Docker is running
if ! docker ps &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if K3D registry is running
if ! docker ps | grep -q "k3d-alphintra-registry"; then
    echo "❌ K3D registry not found. Please run './setup-k8s-cluster.sh' first."
    exit 1
fi

echo "✅ Prerequisites verified"
echo ""

# Direct Docker build approach (no cloud-build-local dependency)
echo "🏗️  Starting direct Docker builds..."
cd "$BASE_DIR"

# Function to build service with error handling
build_service() {
    local service_name="$1"
    local dockerfile="$2"
    local context="$3"
    local image_tag="$4"
    
    echo "🔨 Building $service_name..."
    if docker build -f "$dockerfile" -t "$LOCAL_REGISTRY/alphintra/$service_name:$image_tag" "$context"; then
        echo "✅ $service_name built successfully"
        
        # Push to local registry
        echo "📤 Pushing $service_name to local registry..."
        if docker push "$LOCAL_REGISTRY/alphintra/$service_name:$image_tag"; then
            echo "✅ $service_name pushed successfully"
        else
            echo "❌ Failed to push $service_name"
            return 1
        fi
    else
        echo "❌ Failed to build $service_name"
        return 1
    fi
}

# Build all services with parallel execution
echo "🚀 Building all services in parallel..."
echo "   This will build all services simultaneously using Docker"
echo "   Build time: ~5-10 minutes"
echo ""

# Build Java services (Google Distroless)
(
    build_service "api-gateway" "src/backend/gateway/Dockerfile.distroless" "src/backend/gateway" "distroless"
) &
GATEWAY_PID=$!

(
    build_service "auth-service" "src/backend/auth-service/Dockerfile.distroless" "src/backend/auth-service" "distroless"
) &
AUTH_PID=$!

# Build Python services (Alpine optimized)
(
    build_service "trading-api" "src/backend/trading-api/Dockerfile.optimized" "src/backend/trading-api" "optimized"
) &
TRADING_PID=$!

(
    build_service "graphql-gateway" "src/backend/graphql-gateway/Dockerfile.optimized" "src/backend/graphql-gateway" "optimized"
) &
GRAPHQL_PID=$!

(
    build_service "strategy-engine" "src/backend/strategy-engine/Dockerfile.optimized" "src/backend/strategy-engine" "optimized"
) &
STRATEGY_PID=$!

# Wait for all builds to complete
echo "⏳ Waiting for all builds to complete..."
BUILD_FAILED=false

wait $GATEWAY_PID || BUILD_FAILED=true
wait $AUTH_PID || BUILD_FAILED=true
wait $TRADING_PID || BUILD_FAILED=true
wait $GRAPHQL_PID || BUILD_FAILED=true
wait $STRATEGY_PID || BUILD_FAILED=true

if [ "$BUILD_FAILED" = true ]; then
    echo "❌ One or more builds failed. Please check the output above."
    exit 1
fi

echo "🎉 All builds completed successfully!"

# Verify build results
echo ""
echo "🔍 Verifying build results..."

# Check if images were built
SERVICES=("api-gateway" "auth-service" "trading-api" "graphql-gateway" "strategy-engine")
MISSING_IMAGES=()

for SERVICE in "${SERVICES[@]}"; do
    if [[ "$SERVICE" == "api-gateway" || "$SERVICE" == "auth-service" ]]; then
        TAG="distroless"
    else
        TAG="optimized"
    fi
    
    if ! docker images $LOCAL_REGISTRY/alphintra/$SERVICE:$TAG --format="table {{.Repository}}" | grep -q "$SERVICE"; then
        MISSING_IMAGES+=("$SERVICE")
    fi
done

if [[ ${#MISSING_IMAGES[@]} -gt 0 ]]; then
    echo "❌ Some images failed to build:"
    for SERVICE in "${MISSING_IMAGES[@]}"; do
        echo "  - $SERVICE"
    done
    exit 1
fi

echo "✅ All images built successfully!"
echo ""

# Display final results
echo "📊 Build Results Summary:"
echo "Service                | Image Type         | Size"
echo "----------------------|--------------------|------"

# List all services with their respective tags
SERVICES=(
    "api-gateway:distroless:Google Distroless"
    "auth-service:distroless:Google Distroless"
    "trading-api:optimized:Alpine Python"
    "graphql-gateway:optimized:Alpine Python"
    "strategy-engine:optimized:Alpine Python"
)

for SERVICE_INFO in "${SERVICES[@]}"; do
    IFS=':' read -r SERVICE TAG TYPE <<< "$SERVICE_INFO"
    
    if docker images "$LOCAL_REGISTRY/alphintra/$SERVICE:$TAG" --format "table {{.Size}}" | tail -n 1 &> /dev/null; then
        SIZE=$(docker images "$LOCAL_REGISTRY/alphintra/$SERVICE:$TAG" --format "table {{.Size}}" | tail -n 1)
        printf "%-21s | %-18s | %s\n" "$SERVICE" "$TYPE" "$SIZE"
    else
        printf "%-21s | %-18s | %s\n" "$SERVICE" "$TYPE" "Build failed"
    fi
done

echo ""
echo "🎯 Performance Achievements:"
echo "  ✅ Java services using Google Distroless (~150MB each)"
echo "  ✅ Python services using Alpine (~120MB each)"
echo "  ✅ No Google Cloud project required"
echo "  ✅ Parallel build execution with native Docker"
echo "  ✅ Local registry integration"
echo "  ✅ Replaced deprecated cloud-build-local"
echo ""

echo "🚀 Next Steps:"
echo "1. Deploy to K3D cluster:"
echo "   ./k8s/deploy-with-cloud-build-local.sh"
echo ""
echo "2. Test the deployment:"
echo "   kubectl get pods -n alphintra"
echo "   curl http://localhost:8080/actuator/health"
echo ""
echo "3. Monitor resource usage:"
echo "   kubectl top pods -n alphintra"
echo "   kubectl top nodes"
echo ""

echo "✅ Direct Docker build execution complete!"
echo "   All images available at: $LOCAL_REGISTRY/alphintra/*"
echo "   Ready for K3D deployment!"
echo "   Alternative solution for deprecated cloud-build-local"