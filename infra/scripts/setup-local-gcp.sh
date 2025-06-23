#!/bin/bash

# Comprehensive Local GCP Simulation Setup for Alphintra Trading Platform
# This script sets up the complete local development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPTS_DIR="${PROJECT_ROOT}/infra/scripts"
DOCKER_DIR="${PROJECT_ROOT}/infra/docker"
KUBERNETES_DIR="${PROJECT_ROOT}/infra/kubernetes"

echo -e "${BLUE}🚀 Alphintra Local GCP Simulation Setup${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo "This script will set up a complete local development environment that simulates GCP services:"
echo "  📦 Docker Compose (Infrastructure services)"
echo "  ☸️  Kubernetes with k3d (Application platform)"
echo "  🕸️  Istio Service Mesh (Traffic management & observability)"
echo "  📊 Monitoring Stack (Prometheus, Grafana, Jaeger)"
echo "  🤖 ML Platform (MLflow, MinIO)"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
    
    local missing_tools=()
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        missing_tools+=("docker-compose")
    fi
    
    # Check k3d
    if ! command -v k3d &> /dev/null; then
        missing_tools+=("k3d")
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        echo ""
        echo "Please install the missing tools:"
        echo "  - Docker: https://docs.docker.com/get-docker/"
        echo "  - k3d: https://k3d.io/v5.4.6/#installation"
        echo "  - kubectl: https://kubernetes.io/docs/tasks/tools/"
        exit 1
    fi
    
    print_status "All prerequisites are installed"
}

# Function to setup Docker infrastructure
setup_docker_infrastructure() {
    echo -e "${BLUE}📦 Setting up Docker infrastructure...${NC}"
    
    cd "${PROJECT_ROOT}"
    
    # Stop any existing containers
    print_info "Stopping existing containers..."
    docker-compose down --remove-orphans || true
    
    # Pull latest images
    print_info "Pulling Docker images..."
    docker-compose pull
    
    # Start infrastructure services
    print_info "Starting infrastructure services..."
    docker-compose up -d
    
    # Wait for services to be healthy
    print_info "Waiting for services to be healthy..."
    sleep 30
    
    # Check service health
    local unhealthy_services=()
    for service in postgres timescaledb redis-master kafka; do
        if ! docker-compose ps | grep "$service" | grep -q "healthy\|Up"; then
            unhealthy_services+=("$service")
        fi
    done
    
    if [ ${#unhealthy_services[@]} -ne 0 ]; then
        print_warning "Some services may not be fully ready: ${unhealthy_services[*]}"
        print_info "You can check service logs with: docker-compose logs <service-name>"
    else
        print_status "All infrastructure services are running"
    fi
}

# Function to setup Kubernetes cluster
setup_kubernetes_cluster() {
    echo -e "${BLUE}☸️  Setting up Kubernetes cluster...${NC}"
    
    cd "${SCRIPTS_DIR}"
    
    # Make scripts executable
    chmod +x setup-k8s-cluster.sh
    chmod +x install-istio.sh
    
    # Setup k3d cluster
    print_info "Creating k3d cluster..."
    ./setup-k8s-cluster.sh
    
    print_status "Kubernetes cluster is ready"
}

# Function to install Istio
install_istio_mesh() {
    echo -e "${BLUE}🕸️  Installing Istio service mesh...${NC}"
    
    cd "${SCRIPTS_DIR}"
    
    # Install Istio
    print_info "Installing Istio and observability tools..."
    ./install-istio.sh
    
    print_status "Istio service mesh is ready"
}

# Function to deploy monitoring stack
deploy_monitoring() {
    echo -e "${BLUE}📊 Deploying monitoring stack...${NC}"
    
    # Create monitoring namespace if it doesn't exist
    kubectl create namespace alphintra-monitoring --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy Prometheus configuration
    if [ -f "${PROJECT_ROOT}/monitoring/prometheus/prometheus.yml" ]; then
        kubectl create configmap prometheus-config \
            --from-file="${PROJECT_ROOT}/monitoring/prometheus/prometheus.yml" \
            -n alphintra-monitoring \
            --dry-run=client -o yaml | kubectl apply -f -
        print_status "Prometheus configuration deployed"
    fi
    
    print_status "Monitoring stack is ready"
}

# Function to display access information
display_access_info() {
    echo ""
    echo -e "${GREEN}🎉 Local GCP Simulation Setup Complete!${NC}"
    echo -e "${GREEN}=======================================${NC}"
    echo ""
    echo -e "${BLUE}📦 Infrastructure Services (Docker):${NC}"
    echo "  🐘 PostgreSQL: localhost:5432 (user: alphintra, db: alphintra_db)"
    echo "  📊 TimescaleDB: localhost:5433 (user: alphintra, db: timeseries_db)"
    echo "  🔴 Redis: localhost:6379 (master), localhost:6380 (replica)"
    echo "  📨 Kafka: localhost:9092 (broker), localhost:2181 (zookeeper)"
    echo "  🤖 MLflow: http://localhost:5000"
    echo "  🪣 MinIO: http://localhost:9001 (admin/password123)"
    echo ""
    echo -e "${BLUE}☸️  Kubernetes Services:${NC}"
    echo "  📊 Prometheus: kubectl port-forward -n istio-system svc/prometheus 9090:9090"
    echo "  📈 Grafana: kubectl port-forward -n istio-system svc/grafana 3000:3000"
    echo "  🔍 Jaeger: kubectl port-forward -n istio-system svc/jaeger 16686:16686"
    echo "  🕸️  Kiali: kubectl port-forward -n istio-system svc/kiali 20001:20001"
    echo ""
    echo -e "${BLUE}🔧 Management Commands:${NC}"
    echo "  📦 Docker services: docker-compose ps"
    echo "  ☸️  Kubernetes pods: kubectl get pods -A"
    echo "  🕸️  Istio status: istioctl proxy-status"
    echo "  📊 Service mesh: kubectl get vs,gw,dr -n alphintra-dev"
    echo ""
    echo -e "${BLUE}🚀 Next Steps:${NC}"
    echo "  1. Deploy applications: kubectl apply -k infra/kubernetes/overlays/dev/"
    echo "  2. Access services through the exposed ports above"
    echo "  3. Monitor applications through Grafana and Kiali dashboards"
    echo "  4. View distributed traces in Jaeger"
    echo ""
    echo -e "${YELLOW}💡 Useful Commands:${NC}"
    echo "  🔄 Restart Docker: docker-compose restart"
    echo "  🗑️  Clean up k3d: k3d cluster delete alphintra-cluster"
    echo "  📋 View logs: docker-compose logs -f <service> or kubectl logs -f <pod>"
}

# Main execution
main() {
    # Check if user wants to proceed
    read -p "Do you want to proceed with the setup? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    # Run setup steps
    check_prerequisites
    setup_docker_infrastructure
    setup_kubernetes_cluster
    install_istio_mesh
    deploy_monitoring
    display_access_info
    
    print_status "Setup completed successfully!"
}

# Run main function
main "$@"