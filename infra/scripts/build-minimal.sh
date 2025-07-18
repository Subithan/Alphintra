#!/bin/bash

# Minimal Build Script - Optimized for Speed and Performance
# Builds only essential services with parallel operations and caching

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REGISTRY_HOST="localhost:5001"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Services to build (service:type:dockerfile)
SERVICES=(
    "auth-service:python:Dockerfile.distroless"
    "gateway:java:Dockerfile.distroless"
    "trading-api:python:Dockerfile.optimized"
    "graphql-gateway:python:Dockerfile.optimized"
    "strategy-engine:python:Dockerfile.optimized"
)

# Function to build a single service
build_service() {
    local service_config=$1
    local service=$(echo "$service_config" | cut -d: -f1)
    local type=$(echo "$service_config" | cut -d: -f2)
    local dockerfile=$(echo "$service_config" | cut -d: -f3)
    
    local service_dir="$PROJECT_ROOT/src/backend/$service"
    local image_name="$REGISTRY_HOST/$service"
    
    log_info "Building $service ($type service)..."
    
    if [ ! -d "$service_dir" ]; then
        log_error "Service directory not found: $service_dir"
        return 1
    fi
    
    if [ ! -f "$service_dir/$dockerfile" ]; then
        log_error "Dockerfile not found: $service_dir/$dockerfile"
        return 1
    fi
    
    cd "$service_dir"
    
    # Build with BuildKit for better caching and parallel builds
    local tag="${image_name}:$(echo "$dockerfile" | cut -d. -f2)"
    
    log_info "Building image: $tag"
    
    # Use BuildKit with cache mounting for faster builds
    DOCKER_BUILDKIT=1 docker build \
        --file "$dockerfile" \
        --tag "$tag" \
        --tag "${image_name}:latest" \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        . || {
        log_error "Failed to build $service"
        return 1
    }
    
    # Push to local registry
    docker push "$tag" || {
        log_error "Failed to push $service"
        return 1
    }
    
    docker push "${image_name}:latest" || {
        log_warning "Failed to push latest tag for $service"
    }
    
    log_success "Successfully built and pushed $service"
    
    # Display image size
    local size=$(docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep "$tag" | awk '{print $2}')
    log_info "$service image size: $size"
}

# Function to build services in parallel
build_services_parallel() {
    local pids=()
    local failed_services=()
    
    log_info "Starting parallel build for all services..."
    
    for service_config in "${SERVICES[@]}"; do
        local service=$(echo "$service_config" | cut -d: -f1)
        (
            build_service "$service_config" || {
                echo "$service" > "/tmp/build_failed_$service"
                exit 1
            }
        ) &
        pids+=($!)
    done
    
    # Wait for all builds to complete
    local failed=0
    for pid in "${pids[@]}"; do
        if ! wait "$pid"; then
            failed=1
        fi
    done
    
    # Check for failed services
    for service_config in "${SERVICES[@]}"; do
        local service=$(echo "$service_config" | cut -d: -f1)
        if [ -f "/tmp/build_failed_$service" ]; then
            failed_services+=("$service")
            rm -f "/tmp/build_failed_$service"
        fi
    done
    
    if [ $failed -eq 1 ]; then
        log_error "Build failed for services: ${failed_services[*]}"
        return 1
    fi
    
    log_success "All services built successfully"
}

# Function to check and optimize Docker daemon
optimize_docker() {
    log_info "Optimizing Docker for build performance..."
    
    # Check if BuildKit is enabled
    if [ "${DOCKER_BUILDKIT:-0}" != "1" ]; then
        export DOCKER_BUILDKIT=1
        log_info "Enabled Docker BuildKit for faster builds"
    fi
    
    # Prune build cache to free up space (keep recent layers)
    docker builder prune --filter until=24h -f > /dev/null 2>&1 || true
    
    log_success "Docker optimization complete"
}

# Function to display build summary
display_summary() {
    log_info "Build Summary:"
    echo
    echo "Built images:"
    for service_config in "${SERVICES[@]}"; do
        local service=$(echo "$service_config" | cut -d: -f1)
        local dockerfile=$(echo "$service_config" | cut -d: -f3)
        local tag="${REGISTRY_HOST}/$service:$(echo "$dockerfile" | cut -d. -f2)"
        
        if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "$tag"; then
            local size=$(docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep "$tag" | awk '{print $2}')
            echo "  ✅ $service: $tag ($size)"
        else
            echo "  ❌ $service: Build failed"
        fi
    done
    echo
    
    # Display total size
    local total_size=$(docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep "$REGISTRY_HOST" | awk 'BEGIN{total=0} {gsub(/MB|GB/, "", $2); if($2 ~ /GB/) total+=$2*1024; else total+=$2} END{printf "%.1fMB", total}')
    log_info "Total image size: $total_size"
    echo
    
    log_info "Registry contents:"
    curl -s http://$REGISTRY_HOST/v2/_catalog | python3 -m json.tool 2>/dev/null || echo "Registry not accessible"
}

# Main function
main() {
    log_info "Starting minimal build process for Alphintra platform..."
    
    # Check prerequisites
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check if local registry is running
    if ! curl -s http://$REGISTRY_HOST/v2/ > /dev/null; then
        log_error "Local registry at $REGISTRY_HOST is not accessible"
        log_info "Please start the K3D cluster with registry first"
        exit 1
    fi
    
    # Optimize Docker settings
    optimize_docker
    
    # Build all services in parallel
    build_services_parallel
    
    # Display summary
    display_summary
    
    log_success "Minimal build completed successfully!"
    log_info "Images are ready for deployment"
    log_info "Next step: Run './infra/scripts/k8s/deploy-minimal.sh' to deploy"
}

# Execute main function
main "$@"