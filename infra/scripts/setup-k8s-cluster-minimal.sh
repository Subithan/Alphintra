#!/bin/bash

# Minimal k3d cluster setup for Alphintra Trading Platform
# Optimized for local development with minimal resource usage

set -euo pipefail

CLUSTER_NAME="alphintra"
REGISTRY_NAME="alphintra-registry"
REGISTRY_PORT="5001"

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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v k3d &> /dev/null; then
        log_error "k3d is not installed. Please install it first:"
        echo "  curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash"
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install it first"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first"
        exit 1
    fi
    
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker daemon is not running. Please start Docker first"
        exit 1
    fi
    
    log_success "All prerequisites are met"
}

# Cleanup existing cluster and registry
cleanup_existing() {
    log_info "Cleaning up existing cluster and registry..."
    
    if k3d cluster list | grep -q "$CLUSTER_NAME"; then
        log_warning "Cluster $CLUSTER_NAME already exists. Deleting..."
        k3d cluster delete $CLUSTER_NAME
    fi
    
    if k3d registry list | grep -q "$REGISTRY_NAME"; then
        log_warning "Registry $REGISTRY_NAME already exists. Deleting..."
        k3d registry delete $REGISTRY_NAME
    fi
    
    log_success "Cleanup completed"
}

# Create local registry
create_registry() {
    log_info "Creating local container registry..."
    k3d registry create $REGISTRY_NAME --port $REGISTRY_PORT
    
    # Wait for registry to be ready
    for i in {1..30}; do
        if curl -s http://localhost:$REGISTRY_PORT/v2/ > /dev/null; then
            log_success "Registry is ready at localhost:$REGISTRY_PORT"
            return 0
        fi
        sleep 1
    done
    
    log_error "Registry failed to start"
    exit 1
}

# Create minimal k3d cluster
create_cluster() {
    log_info "Creating minimal k3d cluster..."
    
    k3d cluster create $CLUSTER_NAME \
        --agents 1 \
        --servers 1 \
        --registry-use k3d-$REGISTRY_NAME:$REGISTRY_PORT \
        --port "30080:30080@agent:0" \
        --port "30081:30081@agent:0" \
        --port "30082:30082@agent:0" \
        --port "30090:30090@agent:0" \
        --port "30432:30432@agent:0" \
        --port "30679:30679@agent:0" \
        --k3s-arg "--disable=traefik@server:*" \
        --k3s-arg "--disable=metrics-server@server:*" \
        --k3s-arg "--kube-apiserver-arg=feature-gates=RemoveSelfLink=false@server:*" \
        --wait
    
    log_success "Cluster created successfully"
}

# Configure kubectl context
configure_kubectl() {
    log_info "Configuring kubectl context..."
    kubectl config use-context k3d-$CLUSTER_NAME
    
    # Wait for cluster to be ready
    kubectl wait --for=condition=Ready nodes --all --timeout=300s
    
    log_success "kubectl configured and cluster is ready"
}

# Create namespace and secrets
setup_namespace_and_secrets() {
    log_info "Creating namespace and secrets..."
    
    # Create namespace
    kubectl create namespace alphintra --dry-run=client -o yaml | kubectl apply -f -
    
    # Create minimal secrets for development
    kubectl create secret generic alphintra-secrets \
        --namespace=alphintra \
        --from-literal=postgres-password="postgres_dev_password" \
        --from-literal=redis-password="redis_dev_password" \
        --from-literal=jwt-secret="jwt_dev_secret_key" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    log_success "Namespace and secrets created"
}

# Display cluster information
display_info() {
    log_success "Minimal k3d cluster setup completed!"
    echo
    log_info "Cluster Information:"
    echo "  • Cluster Name: $CLUSTER_NAME"
    echo "  • Registry: localhost:$REGISTRY_PORT"
    echo "  • Context: k3d-$CLUSTER_NAME"
    echo "  • Nodes: 1 server + 1 agent (minimal configuration)"
    echo
    log_info "Available Ports (NodePort services):"
    echo "  • API Gateway: http://localhost:30080"
    echo "  • GraphQL Gateway: http://localhost:30081"
    echo "  • Trading API: http://localhost:30082"
    echo "  • Metrics Dashboard: http://localhost:30090"
    echo "  • PostgreSQL: localhost:30432"
    echo "  • Redis: localhost:30679"
    echo
    log_info "Next Steps:"
    echo "  1. Build images: ./infra/scripts/build-minimal.sh"
    echo "  2. Deploy services: ./infra/scripts/k8s/deploy-minimal.sh"
    echo "  3. Check status: kubectl get pods -n alphintra"
    echo
    log_info "Useful Commands:"
    echo "  • List all resources: kubectl get all -n alphintra"
    echo "  • View logs: kubectl logs -f deployment/<service-name> -n alphintra"
    echo "  • Delete cluster: k3d cluster delete $CLUSTER_NAME"
    echo "  • Delete registry: k3d registry delete $REGISTRY_NAME"
    echo
    log_info "Resource Usage (Estimated):"
    echo "  • Memory: ~1GB total (cluster + workloads)"
    echo "  • CPU: ~0.5 cores"
    echo "  • Disk: ~2GB"
}

# Main function
main() {
    log_info "Starting minimal k3d cluster setup for Alphintra platform..."
    
    check_prerequisites
    cleanup_existing
    create_registry
    create_cluster
    configure_kubectl
    setup_namespace_and_secrets
    display_info
    
    log_success "Setup completed successfully!"
}

# Execute main function
main "$@"