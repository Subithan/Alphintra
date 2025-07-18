#!/bin/bash

# Minimal K3D Deployment Script - Optimized for Speed and Performance
# This script deploys only essential services with parallel operations

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
NAMESPACE="alphintra"
REGISTRY_HOST="localhost:5001"
KUSTOMIZATION_FILE="$PROJECT_ROOT/infra/kubernetes/base/kustomization-minimal.yaml"

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

# Error handling
cleanup() {
    if [ $? -ne 0 ]; then
        log_error "Deployment failed. Check the logs above for details."
        log_info "You can check pod status with: kubectl get pods -n $NAMESPACE"
        log_info "View logs with: kubectl logs -n $NAMESPACE -l app=<service-name>"
    fi
}
trap cleanup EXIT

# Function to wait for multiple deployments in parallel
wait_for_deployments_parallel() {
    local deployments=("$@")
    local pids=()
    
    log_info "Waiting for deployments to be ready (parallel)..."
    
    for deployment in "${deployments[@]}"; do
        (
            log_info "Waiting for deployment/$deployment..."
            kubectl wait --for=condition=available --timeout=180s deployment/"$deployment" -n "$NAMESPACE" || {
                log_error "Deployment $deployment failed to become ready"
                exit 1
            }
            log_success "Deployment $deployment is ready"
        ) &
        pids+=($!)
    done
    
    # Wait for all background processes
    local failed=0
    for pid in "${pids[@]}"; do
        if ! wait "$pid"; then
            failed=1
        fi
    done
    
    if [ $failed -eq 1 ]; then
        log_error "One or more deployments failed"
        return 1
    fi
    
    log_success "All deployments are ready"
}

# Function to wait for StatefulSets in parallel
wait_for_statefulsets_parallel() {
    local statefulsets=("$@")
    local pids=()
    
    log_info "Waiting for StatefulSets to be ready (parallel)..."
    
    for statefulset in "${statefulsets[@]}"; do
        (
            log_info "Waiting for StatefulSet/$statefulset..."
            kubectl wait --for=condition=ready --timeout=180s pod -l app="$statefulset" -n "$NAMESPACE" || {
                log_error "StatefulSet $statefulset failed to become ready"
                exit 1
            }
            log_success "StatefulSet $statefulset is ready"
        ) &
        pids+=($!)
    done
    
    # Wait for all background processes
    local failed=0
    for pid in "${pids[@]}"; do
        if ! wait "$pid"; then
            failed=1
        fi
    done
    
    if [ $failed -eq 1 ]; then
        log_error "One or more StatefulSets failed"
        return 1
    fi
    
    log_success "All StatefulSets are ready"
}

# Main deployment function
main() {
    log_info "Starting minimal K3D deployment for Alphintra platform..."
    
    # Check prerequisites
    log_info "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    if ! command -v k3d &> /dev/null; then
        log_error "k3d is not installed"
        exit 1
    fi
    
    # Check if k3d cluster exists and is running
    if ! k3d cluster list | grep -q "alphintra"; then
        log_error "K3d cluster 'alphintra' does not exist. Please create it first with ./infra/scripts/setup-k8s-cluster-minimal.sh"
        exit 1
    fi
    
    # Check if cluster is accessible via kubectl
    if ! kubectl get nodes > /dev/null 2>&1; then
        log_error "K3d cluster 'alphintra' is not accessible. Please check if it's running."
        exit 1
    fi
    
    # Check if registry is accessible
    if ! curl -s http://$REGISTRY_HOST/v2/ > /dev/null; then
        log_warning "Registry at $REGISTRY_HOST is not accessible. Some images might not be available."
    fi
    
    # Ensure namespace exists
    log_info "Ensuring namespace exists..."
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply minimal configuration  
    log_info "Applying minimal Kubernetes configuration..."
    
    # First apply individual resources that don't have dependencies
    local base_dir="$(dirname "$KUSTOMIZATION_FILE")"
    kubectl apply -f "$base_dir/namespace.yaml" -n "$NAMESPACE" || true
    kubectl apply -f "$base_dir/postgresql-statefulset-minimal.yaml" -n "$NAMESPACE"
    kubectl apply -f "$base_dir/redis-statefulset-optimized.yaml" -n "$NAMESPACE"
    kubectl apply -f "$base_dir/monitoring-stack-minimal.yaml" -n "$NAMESPACE"
    
    # Apply application services
    kubectl apply -f "$base_dir/api-gateway.yaml" -n "$NAMESPACE"
    kubectl apply -f "$base_dir/auth-service.yaml" -n "$NAMESPACE"
    kubectl apply -f "$base_dir/trading-api-deployment.yaml" -n "$NAMESPACE"
    kubectl apply -f "$base_dir/graphql-gateway.yaml" -n "$NAMESPACE"
    kubectl apply -f "$base_dir/strategy-engine-deployment.yaml" -n "$NAMESPACE"
    
    # Wait for StatefulSets first (databases)
    log_info "Waiting for database services..."
    wait_for_statefulsets_parallel "postgresql" "redis"
    
    # Wait for application deployments
    log_info "Waiting for application services..."
    wait_for_deployments_parallel "api-gateway" "auth-service" "trading-service" "graphql-gateway" "strategy-engine" "simple-metrics"
    
    # Verify all services are running
    log_info "Verifying service health..."
    kubectl get pods -n "$NAMESPACE" -o wide
    
    # Display access information
    log_success "Deployment completed successfully!"
    echo
    log_info "Access URLs:"
    echo "  • API Gateway: http://localhost:30080"
    echo "  • GraphQL Gateway: http://localhost:30081"
    echo "  • Trading API: http://localhost:30082"
    echo "  • Metrics Dashboard: http://localhost:30090"
    echo
    log_info "Database connections:"
    echo "  • PostgreSQL: localhost:30432 (user: postgres, password: postgres_dev_password)"
    echo "  • Redis: localhost:30679"
    echo
    log_info "Useful commands:"
    echo "  • Check all pods: kubectl get pods -n $NAMESPACE"
    echo "  • View pod logs: kubectl logs -n $NAMESPACE <pod-name>"
    echo "  • Port forward: kubectl port-forward -n $NAMESPACE service/<service-name> <local-port>:<service-port>"
    echo "  • Delete deployment: kubectl delete namespace $NAMESPACE"
}

# Execute main function
main "$@"