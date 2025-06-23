#!/bin/bash

# Alphintra Infrastructure Prerequisites Checker
# This script checks if all required tools and dependencies are installed

set -euo pipefail

# Color codes
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

# Check if command exists
check_command() {
    local cmd=$1
    local name=${2:-$cmd}
    local install_hint=${3:-""}
    
    if command -v "$cmd" >/dev/null 2>&1; then
        local version
        case $cmd in
            docker)
                version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
                ;;
            docker-compose)
                version=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
                ;;
            kubectl)
                version=$(kubectl version --client --short 2>/dev/null | cut -d' ' -f3 || echo "unknown")
                ;;
            terraform)
                version=$(terraform version | head -n1 | cut -d' ' -f2)
                ;;
            helm)
                version=$(helm version --short --client | cut -d' ' -f2)
                ;;
            jq)
                version=$(jq --version 2>/dev/null | cut -d'-' -f2)
                ;;
            curl)
                version=$(curl --version | head -n1 | cut -d' ' -f2)
                ;;
            git)
                version=$(git --version | cut -d' ' -f3)
                ;;
            *)
                version="installed"
                ;;
        esac
        log_success "$name is installed (version: $version)"
        return 0
    else
        log_error "$name is not installed"
        if [[ -n "$install_hint" ]]; then
            echo "         Install hint: $install_hint"
        fi
        return 1
    fi
}

# Check minimum version
check_version() {
    local current=$1
    local minimum=$2
    local name=$3
    
    if [[ "$(printf '%s\n' "$minimum" "$current" | sort -V | head -n1)" = "$minimum" ]]; then
        log_success "$name version $current meets minimum requirement ($minimum)"
        return 0
    else
        log_error "$name version $current does not meet minimum requirement ($minimum)"
        return 1
    fi
}

# Check Docker and Docker Compose
check_docker() {
    log_info "Checking Docker requirements..."
    
    local docker_ok=true
    local compose_ok=true
    
    if ! check_command "docker" "Docker" "Visit https://docs.docker.com/get-docker/"; then
        docker_ok=false
    fi
    
    if ! check_command "docker-compose" "Docker Compose" "Visit https://docs.docker.com/compose/install/"; then
        compose_ok=false
    fi
    
    if $docker_ok; then
        # Check Docker version
        local docker_version
        docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        check_version "$docker_version" "20.10.0" "Docker"
        
        # Check if Docker daemon is running
        if docker info >/dev/null 2>&1; then
            log_success "Docker daemon is running"
        else
            log_error "Docker daemon is not running"
            echo "         Please start Docker daemon"
            docker_ok=false
        fi
    fi
    
    if $compose_ok; then
        # Check Docker Compose version
        local compose_version
        compose_version=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        check_version "$compose_version" "1.29.0" "Docker Compose"
    fi
    
    return $(($docker_ok && $compose_ok))
}

# Check Kubernetes tools
check_kubernetes() {
    log_info "Checking Kubernetes tools..."
    
    local k8s_ok=true
    
    if ! check_command "kubectl" "kubectl" "Visit https://kubernetes.io/docs/tasks/tools/"; then
        k8s_ok=false
    fi
    
    # Check for local Kubernetes solutions
    local k8s_local_found=false
    if command -v k3d >/dev/null 2>&1; then
        log_success "k3d is available for local Kubernetes"
        k8s_local_found=true
    elif command -v minikube >/dev/null 2>&1; then
        log_success "minikube is available for local Kubernetes"
        k8s_local_found=true
    elif command -v kind >/dev/null 2>&1; then
        log_success "kind is available for local Kubernetes"
        k8s_local_found=true
    else
        log_warning "No local Kubernetes solution found (k3d, minikube, or kind)"
        echo "         Install one of them for local development"
    fi
    
    return $k8s_ok
}

# Check Terraform
check_terraform() {
    log_info "Checking Terraform..."
    
    if check_command "terraform" "Terraform" "Visit https://learn.hashicorp.com/tutorials/terraform/install-cli"; then
        local tf_version
        tf_version=$(terraform version | head -n1 | cut -d' ' -f2 | tr -d 'v')
        check_version "$tf_version" "1.0.0" "Terraform"
        return $?
    fi
    
    return 1
}

# Check development tools
check_dev_tools() {
    log_info "Checking development tools..."
    
    local tools_ok=true
    
    # Essential tools
    if ! check_command "git" "Git" "Visit https://git-scm.com/downloads"; then
        tools_ok=false
    fi
    
    if ! check_command "curl" "curl" "Usually pre-installed on most systems"; then
        tools_ok=false
    fi
    
    if ! check_command "jq" "jq" "Visit https://stedolan.github.io/jq/download/"; then
        tools_ok=false
    fi
    
    # Optional but recommended tools
    check_command "yq" "yq" "Visit https://github.com/mikefarah/yq#install" || log_warning "yq is recommended for YAML processing"
    check_command "helm" "Helm" "Visit https://helm.sh/docs/intro/install/" || log_warning "Helm is recommended for Kubernetes deployments"
    check_command "istioctl" "Istio CLI" "Visit https://istio.io/latest/docs/setup/getting-started/" || log_warning "istioctl is recommended for service mesh"
    
    return $tools_ok
}

# Check system resources
check_resources() {
    log_info "Checking system resources..."
    
    local resources_ok=true
    
    # Check available memory
    if [[ "$OSTYPE" == "darwin"* ]]; then
        local total_mem_gb
        total_mem_gb=$(( $(sysctl hw.memsize | awk '{print $2}') / 1024 / 1024 / 1024 ))
    elif [[ "$OSTYPE" == "linux"* ]]; then
        local total_mem_gb
        total_mem_gb=$(( $(grep MemTotal /proc/meminfo | awk '{print $2}') / 1024 / 1024 ))
    else
        log_warning "Cannot determine memory on this OS"
        total_mem_gb=8  # Assume minimum
    fi
    
    if [[ $total_mem_gb -ge 8 ]]; then
        log_success "System has sufficient memory (${total_mem_gb}GB >= 8GB)"
    else
        log_error "System has insufficient memory (${total_mem_gb}GB < 8GB)"
        resources_ok=false
    fi
    
    # Check available disk space
    local available_gb
    available_gb=$(df -BG . | tail -n1 | awk '{print $4}' | tr -d 'G')
    
    if [[ $available_gb -ge 20 ]]; then
        log_success "System has sufficient disk space (${available_gb}GB >= 20GB)"
    else
        log_error "System has insufficient disk space (${available_gb}GB < 20GB)"
        resources_ok=false
    fi
    
    return $resources_ok
}

# Check network connectivity
check_network() {
    log_info "Checking network connectivity..."
    
    local network_ok=true
    
    # Check internet connectivity
    if curl -s --connect-timeout 5 https://google.com >/dev/null; then
        log_success "Internet connectivity is available"
    else
        log_error "Internet connectivity is not available"
        network_ok=false
    fi
    
    # Check Docker Hub connectivity
    if curl -s --connect-timeout 5 https://hub.docker.com >/dev/null; then
        log_success "Docker Hub is accessible"
    else
        log_warning "Docker Hub is not accessible (may affect image pulls)"
    fi
    
    # Check if ports are available
    local ports=(8080 8001 8002 8003 5432 6379 9092 9090 3001 5000)
    local ports_blocked=()
    
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            ports_blocked+=($port)
        fi
    done
    
    if [[ ${#ports_blocked[@]} -eq 0 ]]; then
        log_success "All required ports are available"
    else
        log_warning "Some ports are already in use: ${ports_blocked[*]}"
        echo "         You may need to stop other services or change port mappings"
    fi
    
    return $network_ok
}

# Main function
main() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║            Alphintra Infrastructure Prerequisites           ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    local all_good=true
    
    # Run all checks
    check_docker || all_good=false
    echo ""
    
    check_kubernetes || all_good=false
    echo ""
    
    check_terraform || all_good=false
    echo ""
    
    check_dev_tools || all_good=false
    echo ""
    
    check_resources || all_good=false
    echo ""
    
    check_network || all_good=false
    echo ""
    
    # Summary
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                            Summary                           ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    
    if $all_good; then
        log_success "All prerequisites are satisfied! 🎉"
        echo ""
        echo "You can now run:"
        echo "  make setup-dev    # Set up development environment"
        echo "  make start-dev    # Start development environment"
        exit 0
    else
        log_error "Some prerequisites are missing or not configured properly"
        echo ""
        echo "Please install the missing components and run this script again."
        echo ""
        echo "Quick install commands:"
        echo "  make install      # Install all dependencies automatically"
        exit 1
    fi
}

# Run main function
main "$@"