#!/bin/bash
# Alphintra Trading Platform - Destruction Script
# Safely destroys the entire platform with confirmations

set -e

ENVIRONMENT=${1:-prod}

# Colors
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
CYAN='\033[36m'
RESET='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${RESET}"
}

success() {
    echo -e "${GREEN}✅ $1${RESET}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${RESET}"
}

error() {
    echo -e "${RED}❌ $1${RESET}"
}

main() {
    echo -e "${RED}================================================${RESET}"
    echo -e "${RED}  ⚠️  ALPHINTRA PLATFORM DESTRUCTION${RESET}"
    echo -e "${RED}================================================${RESET}"
    echo ""
    echo -e "${RED}Environment: $ENVIRONMENT${RESET}"
    echo -e "${RED}THIS WILL PERMANENTLY DELETE:${RESET}"
    echo "  🗑️  All cloud infrastructure"
    echo "  🗑️  All databases and data"
    echo "  🗑️  All Kubernetes clusters"
    echo "  🗑️  All monitoring and logs"
    echo "  🗑️  All Docker containers and volumes"
    echo ""
    echo -e "${RED}THIS CANNOT BE UNDONE!${RESET}"
    echo ""
    
    read -p "Type 'DESTROY' to confirm total destruction: " confirmation
    
    if [[ "$confirmation" != "DESTROY" ]]; then
        echo -e "${YELLOW}Operation cancelled${RESET}"
        exit 0
    fi
    
    log "Starting platform destruction..."
    
    # Check for Kubernetes deployment
    if command -v kubectl >/dev/null 2>&1 && kubectl cluster-info >/dev/null 2>&1; then
        log "Destroying Kubernetes resources..."
        
        # Delete all Alphintra resources
        kubectl delete all --all --all-namespaces --timeout=300s || true
        kubectl delete namespaces core trading ai global monitoring security --timeout=300s || true
        kubectl delete pv --all --timeout=300s || true
        kubectl delete pvc --all --all-namespaces --timeout=300s || true
        
        success "Kubernetes resources destroyed"
    fi
    
    # Check for Docker deployment
    if [[ -f "docker-compose.local.yml" ]]; then
        log "Destroying Docker deployment..."
        
        docker-compose -f docker-compose.local.yml down -v --remove-orphans || true
        docker system prune -af || true
        
        success "Docker deployment destroyed"
    fi
    
    # Destroy Terraform infrastructure
    if [[ -d "infrastructure/terraform" ]]; then
        log "Destroying cloud infrastructure..."
        
        cd infrastructure/terraform
        terraform destroy -auto-approve || true
        cd ../..
        
        success "Cloud infrastructure destroyed"
    fi
    
    # Clean up local files
    log "Cleaning up local files..."
    rm -f .env.local
    rm -f docker-compose.local.yml
    rm -rf infrastructure/monitoring/prometheus.yml
    rm -rf infrastructure/database/init/
    
    success "Local files cleaned"
    
    echo ""
    echo -e "${GREEN}🗑️  Platform destruction complete${RESET}"
    echo ""
}

main "$@"