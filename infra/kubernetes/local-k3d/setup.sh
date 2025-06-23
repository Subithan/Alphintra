#!/bin/bash
# k3d Cluster Setup Script for Alphintra Trading Platform
# This script creates a local Kubernetes cluster that simulates GKE

set -euo pipefail

# Configuration
CLUSTER_NAME="alphintra-dev"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K3D_CONFIG="$SCRIPT_DIR/cluster-config.yaml"

# Color codes for output
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
    
    local missing_tools=()
    
    if ! command -v k3d >/dev/null 2>&1; then
        missing_tools+=("k3d")
    fi
    
    if ! command -v kubectl >/dev/null 2>&1; then
        missing_tools+=("kubectl")
    fi
    
    if ! command -v docker >/dev/null 2>&1; then
        missing_tools+=("docker")
    fi
    
    if ! command -v helm >/dev/null 2>&1; then
        missing_tools+=("helm")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install the missing tools:"
        for tool in "${missing_tools[@]}"; do
            case $tool in
                k3d)
                    echo "  brew install k3d"
                    ;;
                kubectl)
                    echo "  brew install kubectl"
                    ;;
                docker)
                    echo "  Install Docker Desktop from https://www.docker.com/products/docker-desktop"
                    ;;
                helm)
                    echo "  brew install helm"
                    ;;
            esac
        done
        exit 1
    fi
    
    log_success "All prerequisites are installed"
}

# Check if Docker is running
check_docker() {
    log_info "Checking Docker daemon..."
    
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running. Please start Docker Desktop."
        exit 1
    fi
    
    log_success "Docker daemon is running"
}

# Create Docker network
create_network() {
    log_info "Creating Docker network..."
    
    if docker network ls | grep -q alphintra-network; then
        log_warning "Network 'alphintra-network' already exists"
    else
        docker network create alphintra-network
        log_success "Created Docker network 'alphintra-network'"
    fi
}

# Delete existing cluster if it exists
cleanup_existing_cluster() {
    if k3d cluster list | grep -q "$CLUSTER_NAME"; then
        log_warning "Cluster '$CLUSTER_NAME' already exists. Deleting it..."
        k3d cluster delete "$CLUSTER_NAME"
        log_success "Deleted existing cluster '$CLUSTER_NAME'"
    fi
}

# Create k3d cluster
create_cluster() {
    log_info "Creating k3d cluster '$CLUSTER_NAME'..."
    
    if [ ! -f "$K3D_CONFIG" ]; then
        log_error "Cluster configuration file not found: $K3D_CONFIG"
        exit 1
    fi
    
    k3d cluster create --config "$K3D_CONFIG"
    log_success "Created k3d cluster '$CLUSTER_NAME'"
}

# Wait for cluster to be ready
wait_for_cluster() {
    log_info "Waiting for cluster to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if kubectl get nodes --no-headers | grep -q Ready; then
            log_success "Cluster is ready"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts: Waiting for nodes to be ready..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Cluster failed to become ready within expected time"
    exit 1
}

# Install metrics server
install_metrics_server() {
    log_info "Installing metrics server..."
    
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    
    # Patch metrics server for k3d
    kubectl patch deployment metrics-server -n kube-system --type='json' \
        -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'
    
    log_success "Metrics server installed"
}

# Create persistent volumes
create_persistent_volumes() {
    log_info "Creating persistent volumes..."
    
    kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolume
metadata:
  name: postgres-pv
spec:
  capacity:
    storage: 10Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-path
  hostPath:
    path: /tmp/k3d-alphintra-postgres
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: redis-pv
spec:
  capacity:
    storage: 5Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-path
  hostPath:
    path: /tmp/k3d-alphintra-redis
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: kafka-pv
spec:
  capacity:
    storage: 10Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-path
  hostPath:
    path: /tmp/k3d-alphintra-kafka
EOF
    
    log_success "Persistent volumes created"
}

# Install ingress controller
install_ingress_controller() {
    log_info "Installing NGINX Ingress Controller..."
    
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
    
    # Wait for ingress controller to be ready
    kubectl wait --namespace ingress-nginx \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/component=controller \
        --timeout=300s
    
    log_success "NGINX Ingress Controller installed"
}

# Create namespaces
create_namespaces() {
    log_info "Creating namespaces..."
    
    kubectl apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: alphintra
  labels:
    name: alphintra
    istio-injection: enabled
---
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
  labels:
    name: monitoring
---
apiVersion: v1
kind: Namespace
metadata:
  name: infrastructure
  labels:
    name: infrastructure
EOF
    
    log_success "Namespaces created"
}

# Display cluster information
display_cluster_info() {
    log_success "k3d cluster setup completed successfully!"
    echo ""
    log_info "Cluster Information:"
    echo "  Cluster Name: $CLUSTER_NAME"
    echo "  Kubernetes Version: $(kubectl version --short | grep Server | cut -d' ' -f3)"
    echo "  Nodes: $(kubectl get nodes --no-headers | wc -l)"
    echo ""
    log_info "Available Ports:"
    echo "  HTTP: http://localhost:8080"
    echo "  HTTPS: https://localhost:8443"
    echo "  Prometheus: http://localhost:9090"
    echo "  Custom App: http://localhost:3000"
    echo "  MLflow: http://localhost:5000"
    echo ""
    log_info "Registry:"
    echo "  Local Registry: localhost:5555"
    echo ""
    log_info "Useful Commands:"
    echo "  kubectl get nodes"
    echo "  kubectl get pods -A"
    echo "  k3d cluster list"
    echo "  k3d cluster delete $CLUSTER_NAME"
    echo ""
    log_info "Next Steps:"
    echo "  1. Install Istio: ./istio-setup.sh"
    echo "  2. Deploy applications: kubectl apply -k ../overlays/dev/"
}

# Main execution
main() {
    log_info "Starting k3d cluster setup for Alphintra Trading Platform"
    
    check_prerequisites
    check_docker
    create_network
    cleanup_existing_cluster
    create_cluster
    wait_for_cluster
    install_metrics_server
    create_persistent_volumes
    install_ingress_controller
    create_namespaces
    display_cluster_info
}

# Execute main function
main "$@"