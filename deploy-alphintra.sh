#!/bin/bash
# deploy-alphintra.sh
# Alphintra Financial Platform Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CLUSTER_NAME="alphintra-cluster"
REGISTRY_NAME="k3d-registry.localhost"
REGISTRY_PORT="5000"
K3D_DIR="./k3d"
HELM_CHART_DIR="./k3d/helm/alphintra-platform"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for deployment to be ready
wait_for_deployment() {
    local namespace=$1
    local deployment=$2
    local timeout=${3:-300}
    
    print_status "Waiting for deployment $deployment in namespace $namespace to be ready..."
    kubectl wait --for=condition=available --timeout=${timeout}s deployment/$deployment -n $namespace
}

# Function to wait for statefulset to be ready
wait_for_statefulset() {
    local namespace=$1
    local statefulset=$2
    local timeout=${3:-300}
    
    print_status "Waiting for statefulset $statefulset in namespace $namespace to be ready..."
    kubectl wait --for=condition=ready --timeout=${timeout}s pod -l app=$statefulset -n $namespace
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists k3d; then
        print_error "k3d is not installed. Please install k3d first."
        exit 1
    fi
    
    if ! command_exists kubectl; then
        print_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    if ! command_exists helm; then
        print_error "helm is not installed. Please install helm first."
        exit 1
    fi
    
    if ! command_exists docker; then
        print_error "docker is not installed. Please install docker first."
        exit 1
    fi
    
    print_success "All prerequisites are installed."
}

# Setup K3D cluster
setup_cluster() {
    print_status "Setting up K3D cluster..."
    
    # Make setup script executable and run it
    chmod +x ./setup-k3d-cluster.sh
    ./setup-k3d-cluster.sh
    
    print_success "K3D cluster setup completed."
}

# Deploy databases
deploy_databases() {
    print_status "Deploying databases..."
    
    # Deploy PostgreSQL
    print_status "Deploying PostgreSQL..."
    kubectl apply -f $K3D_DIR/databases/postgresql-config.yaml
    kubectl apply -f $K3D_DIR/databases/postgresql-statefulset.yaml
    
    # Deploy Redis
    print_status "Deploying Redis cluster..."
    kubectl apply -f $K3D_DIR/databases/redis-cluster.yaml
    
    # Deploy database connections config
    kubectl apply -f $K3D_DIR/services/database-connections.yaml
    
    # Wait for databases to be ready
    print_status "Waiting for databases to be ready..."
    wait_for_statefulset "alphintra" "postgresql" 600
    wait_for_statefulset "alphintra" "redis" 600
    
    print_success "Databases deployed successfully."
}

# Deploy infrastructure services
deploy_infrastructure() {
    print_status "Deploying infrastructure services..."
    
    # Deploy Eureka Server
    print_status "Deploying Eureka Server..."
    kubectl apply -f $K3D_DIR/services/eureka-server.yaml
    wait_for_deployment "alphintra-system" "eureka-server" 300
    
    # Deploy API Gateway
    print_status "Deploying API Gateway..."
    kubectl apply -f $K3D_DIR/services/api-gateway.yaml
    wait_for_deployment "alphintra" "api-gateway" 300
    
    print_success "Infrastructure services deployed successfully."
}

# Deploy network policies
deploy_security() {
    print_status "Deploying security policies..."
    
    kubectl apply -f $K3D_DIR/security/network-policies.yaml
    
    print_success "Security policies deployed successfully."
}

# Deploy monitoring
deploy_monitoring() {
    print_status "Deploying monitoring stack..."
    
    kubectl apply -f $K3D_DIR/monitoring/prometheus.yaml
    
    # Wait for Prometheus to be ready
    wait_for_deployment "monitoring" "prometheus" 300
    
    print_success "Monitoring stack deployed successfully."
}

# Add Helm repositories
setup_helm_repos() {
    print_status "Setting up Helm repositories..."
    
    helm repo add bitnami https://charts.bitnami.com/bitnami
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo update
    
    print_success "Helm repositories configured."
}

# Deploy using Helm (optional)
deploy_with_helm() {
    if [ "$1" = "--helm" ]; then
        print_status "Deploying with Helm..."
        
        setup_helm_repos
        
        # Install dependencies
        helm dependency update $HELM_CHART_DIR
        
        # Deploy the chart
        helm upgrade --install alphintra-platform $HELM_CHART_DIR \
            --namespace alphintra \
            --create-namespace \
            --wait \
            --timeout 10m
        
        print_success "Helm deployment completed."
        return 0
    fi
    return 1
}

# Verify deployment
verify_deployment() {
    print_status "Verifying deployment..."
    
    # Check cluster info
    echo "\n=== Cluster Information ==="
    kubectl cluster-info
    
    # Check nodes
    echo "\n=== Nodes ==="
    kubectl get nodes
    
    # Check namespaces
    echo "\n=== Namespaces ==="
    kubectl get namespaces
    
    # Check pods in alphintra namespace
    echo "\n=== Alphintra Pods ==="
    kubectl get pods -n alphintra
    
    # Check pods in alphintra-system namespace
    echo "\n=== Alphintra System Pods ==="
    kubectl get pods -n alphintra-system
    
    # Check pods in monitoring namespace
    echo "\n=== Monitoring Pods ==="
    kubectl get pods -n monitoring
    
    # Check services
    echo "\n=== Services ==="
    kubectl get services -A
    
    # Check ingress routes
    echo "\n=== Ingress Routes ==="
    kubectl get ingressroute -A
    
    # Check persistent volumes
    echo "\n=== Persistent Volumes ==="
    kubectl get pv
    
    # Check persistent volume claims
    echo "\n=== Persistent Volume Claims ==="
    kubectl get pvc -A
    
    print_success "Deployment verification completed."
}

# Show access information
show_access_info() {
    print_status "Access Information:"
    
    echo "\n=== Web Interfaces ==="
    echo "API Gateway: http://api.alphintra.local"
    echo "Eureka Server: http://eureka.alphintra.local (admin/admin)"
    echo "Prometheus: http://prometheus.alphintra.local (admin/admin)"
    echo "Grafana: http://grafana.alphintra.local (admin/grafana_admin_password)"
    
    echo "\n=== Database Access ==="
    echo "PostgreSQL: postgresql.alphintra.svc.cluster.local:5432"
    echo "  - Database: alphintra_main"
    echo "  - Username: alphintra_admin"
    echo "  - Password: alphintra_secure_password"
    
    echo "Redis: redis-master.alphintra.svc.cluster.local:6379"
    echo "  - Password: redis_alphintra_password"
    
    echo "\n=== Port Forwarding Commands ==="
    echo "PostgreSQL: kubectl port-forward svc/postgresql 5432:5432 -n alphintra"
    echo "Redis: kubectl port-forward svc/redis-master 6379:6379 -n alphintra"
    echo "API Gateway: kubectl port-forward svc/api-gateway 8080:8080 -n alphintra"
    echo "Eureka: kubectl port-forward svc/eureka-server 8761:8761 -n alphintra-system"
    echo "Prometheus: kubectl port-forward svc/prometheus 9090:9090 -n monitoring"
    
    echo "\n=== Host File Entries ==="
    echo "Add these entries to your /etc/hosts file:"
    echo "127.0.0.1 api.alphintra.local"
    echo "127.0.0.1 eureka.alphintra.local"
    echo "127.0.0.1 prometheus.alphintra.local"
    echo "127.0.0.1 grafana.alphintra.local"
}

# Cleanup function
cleanup() {
    print_warning "Cleaning up Alphintra deployment..."
    
    # Delete the cluster
    k3d cluster delete $CLUSTER_NAME
    
    # Remove registry directory
    rm -rf ./k3d-registry
    
    print_success "Cleanup completed."
}

# Main deployment function
main() {
    echo "=== Alphintra Financial Platform Deployment ==="
    echo "This script will deploy the complete Alphintra platform on K3D."
    echo ""
    
    # Parse command line arguments
    case "$1" in
        "--cleanup")
            cleanup
            exit 0
            ;;
        "--verify")
            verify_deployment
            show_access_info
            exit 0
            ;;
        "--help")
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --helm      Deploy using Helm charts"
            echo "  --cleanup   Remove the entire deployment"
            echo "  --verify    Verify existing deployment"
            echo "  --help      Show this help message"
            echo ""
            exit 0
            ;;
    esac
    
    # Check if we should deploy with Helm
    if deploy_with_helm "$1"; then
        verify_deployment
        show_access_info
        exit 0
    fi
    
    # Standard deployment process
    check_prerequisites
    setup_cluster
    
    # Wait a bit for cluster to stabilize
    sleep 10
    
    deploy_databases
    deploy_infrastructure
    deploy_security
    deploy_monitoring
    
    # Final verification
    verify_deployment
    show_access_info
    
    print_success "Alphintra platform deployment completed successfully!"
    print_status "You can now access the platform using the URLs shown above."
}

# Run main function with all arguments
main "$@"