#!/bin/bash
# Alphintra Trading Platform - Status Check Script
# Comprehensive health check for all platform components

set -e

# Configuration
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

check_service() {
    local service=$1
    local namespace=$2
    local port=${3:-8080}
    
    # Check if pods are running
    local pods=$(kubectl get pods -n "$namespace" -l "app=$service" --no-headers 2>/dev/null | wc -l)
    local ready_pods=$(kubectl get pods -n "$namespace" -l "app=$service" --no-headers 2>/dev/null | grep "Running" | wc -l)
    
    if [[ $pods -eq 0 ]]; then
        error "$service: No pods found"
        return 1
    elif [[ $ready_pods -eq $pods ]]; then
        success "$service: $ready_pods/$pods pods running"
        return 0
    else
        warning "$service: $ready_pods/$pods pods running"
        return 1
    fi
}

check_local_service() {
    local service=$1
    local port=$2
    
    if curl -f "http://localhost:$port/health" >/dev/null 2>&1; then
        success "$service: Healthy (port $port)"
        return 0
    else
        error "$service: Unhealthy (port $port)"
        return 1
    fi
}

# Main status check
main() {
    echo -e "${CYAN}================================================${RESET}"
    echo -e "${CYAN}  📊 Alphintra Platform Status Check${RESET}"
    echo -e "${CYAN}================================================${RESET}"
    echo ""
    echo -e "${BLUE}Environment: $ENVIRONMENT${RESET}"
    echo -e "${BLUE}Timestamp: $(date)${RESET}"
    echo ""
    
    # Detect deployment type
    if command -v kubectl >/dev/null 2>&1 && kubectl cluster-info >/dev/null 2>&1; then
        echo -e "${CYAN}🔍 Checking Kubernetes deployment...${RESET}"
        
        # Check namespaces
        echo -e "\n${CYAN}Namespaces:${RESET}"
        kubectl get namespaces | grep -E "(core|trading|ai|global|monitoring|security)" || warning "No Alphintra namespaces found"
        
        # Check core services
        echo -e "\n${CYAN}Core Services:${RESET}"
        check_service "postgresql" "core"
        check_service "redis" "core"
        check_service "kafka" "core"
        
        # Check trading services
        echo -e "\n${CYAN}Trading Services:${RESET}"
        check_service "trading-engine" "trading"
        check_service "market-data-engine" "trading"
        check_service "risk-engine" "trading"
        check_service "portfolio-manager" "trading"
        
        # Check AI services
        echo -e "\n${CYAN}AI/ML Services:${RESET}"
        check_service "llm-analyzer" "ai"
        check_service "quantum-optimizer" "ai"
        check_service "federated-learning" "ai"
        
        # Check global services
        echo -e "\n${CYAN}Global Services:${RESET}"
        check_service "fx-hedging-engine" "global"
        check_service "compliance-engine" "global"
        check_service "regional-coordinator" "global"
        
        # Check monitoring services
        echo -e "\n${CYAN}Monitoring Services:${RESET}"
        check_service "prometheus" "monitoring"
        check_service "grafana" "monitoring"
        check_service "jaeger" "monitoring"
        
        # Check ingress
        echo -e "\n${CYAN}Ingress Controllers:${RESET}"
        kubectl get ingress --all-namespaces 2>/dev/null || warning "No ingress controllers found"
        
        # Check persistent volumes
        echo -e "\n${CYAN}Storage:${RESET}"
        local pv_count=$(kubectl get pv 2>/dev/null | grep -c "Bound" || echo "0")
        if [[ $pv_count -gt 0 ]]; then
            success "Persistent Volumes: $pv_count bound"
        else
            warning "No persistent volumes bound"
        fi
        
    elif command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
        echo -e "${CYAN}🔍 Checking local Docker deployment...${RESET}"
        
        # Check if docker-compose is running
        if [[ -f "docker-compose.local.yml" ]]; then
            echo -e "\n${CYAN}Docker Containers:${RESET}"
            docker-compose -f docker-compose.local.yml ps
            
            echo -e "\n${CYAN}Service Health:${RESET}"
            check_local_service "API Gateway" "8080"
            check_local_service "Trading Dashboard" "3000"
            check_local_service "Monitoring" "3001"
            check_local_service "Documentation" "8000"
            
            echo -e "\n${CYAN}Database Connectivity:${RESET}"
            if docker exec alphintra-postgres pg_isready -U alphintra >/dev/null 2>&1; then
                success "PostgreSQL: Connected"
            else
                error "PostgreSQL: Connection failed"
            fi
            
            if docker exec alphintra-redis redis-cli ping >/dev/null 2>&1; then
                success "Redis: Connected"
            else
                error "Redis: Connection failed"
            fi
        else
            error "Docker Compose configuration not found"
        fi
    else
        error "Neither Kubernetes nor Docker deployment detected"
        echo "Run 'make deploy-all' for cloud deployment or 'make quick-deploy' for local deployment"
        exit 1
    fi
    
    # Check external dependencies (if in cloud)
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        echo -e "\n${CYAN}External Dependencies:${RESET}"
        
        # Check market data feeds
        if curl -f "https://api.polygon.io/v2/aggs/ticker/AAPL/prev" >/dev/null 2>&1; then
            success "Market Data: Polygon.io reachable"
        else
            warning "Market Data: Polygon.io unreachable"
        fi
        
        # Check cloud provider APIs
        if command -v gcloud >/dev/null 2>&1; then
            if gcloud auth list --filter=status:ACTIVE --format="value(account)" >/dev/null 2>&1; then
                success "GCP: Authenticated"
            else
                warning "GCP: Not authenticated"
            fi
        fi
    fi
    
    # Performance metrics
    echo -e "\n${CYAN}Performance Metrics:${RESET}"
    
    if command -v kubectl >/dev/null 2>&1 && kubectl cluster-info >/dev/null 2>&1; then
        # Resource usage
        echo -e "${BLUE}Resource Usage:${RESET}"
        kubectl top nodes 2>/dev/null || warning "Metrics server not available"
        
        # Pod resource usage
        echo -e "\n${BLUE}Top Resource Consuming Pods:${RESET}"
        kubectl top pods --all-namespaces 2>/dev/null | head -10 || warning "Pod metrics not available"
        
    elif [[ -f "docker-compose.local.yml" ]]; then
        echo -e "${BLUE}Container Resource Usage:${RESET}"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || warning "Docker stats not available"
    fi
    
    # Recent events/logs
    echo -e "\n${CYAN}Recent Events:${RESET}"
    
    if command -v kubectl >/dev/null 2>&1; then
        echo -e "${BLUE}Kubernetes Events (last 10):${RESET}"
        kubectl get events --all-namespaces --sort-by='.lastTimestamp' | tail -10 2>/dev/null || warning "Events not available"
    fi
    
    # Summary
    echo -e "\n${CYAN}================================================${RESET}"
    echo -e "${CYAN}  📋 Status Summary${RESET}"
    echo -e "${CYAN}================================================${RESET}"
    
    if command -v kubectl >/dev/null 2>&1 && kubectl cluster-info >/dev/null 2>&1; then
        local total_pods=$(kubectl get pods --all-namespaces --no-headers 2>/dev/null | wc -l)
        local running_pods=$(kubectl get pods --all-namespaces --no-headers 2>/dev/null | grep "Running" | wc -l)
        local failed_pods=$(kubectl get pods --all-namespaces --no-headers 2>/dev/null | grep -E "(Error|CrashLoopBackOff|Failed)" | wc -l)
        
        echo -e "Total Pods: $total_pods"
        echo -e "Running: ${GREEN}$running_pods${RESET}"
        echo -e "Failed: ${RED}$failed_pods${RESET}"
        
        if [[ $failed_pods -eq 0 ]]; then
            success "All services operational"
        else
            error "$failed_pods services have issues"
        fi
        
    elif [[ -f "docker-compose.local.yml" ]]; then
        local total_containers=$(docker-compose -f docker-compose.local.yml ps -q | wc -l)
        local running_containers=$(docker-compose -f docker-compose.local.yml ps | grep "Up" | wc -l)
        
        echo -e "Total Containers: $total_containers"
        echo -e "Running: ${GREEN}$running_containers${RESET}"
        
        if [[ $running_containers -eq $total_containers ]]; then
            success "All services operational"
        else
            warning "Some services may have issues"
        fi
    fi
    
    echo ""
    echo -e "${GREEN}Status check complete!${RESET}"
    echo ""
    
    # Show useful commands
    echo -e "${CYAN}🔧 Useful Commands:${RESET}"
    if command -v kubectl >/dev/null 2>&1; then
        echo -e "  View pods:         ${YELLOW}kubectl get pods --all-namespaces${RESET}"
        echo -e "  View services:     ${YELLOW}kubectl get services --all-namespaces${RESET}"
        echo -e "  View logs:         ${YELLOW}kubectl logs -f deployment/trading-engine -n trading${RESET}"
        echo -e "  Port forward:      ${YELLOW}kubectl port-forward svc/grafana 3000:3000 -n monitoring${RESET}"
    elif [[ -f "docker-compose.local.yml" ]]; then
        echo -e "  View containers:   ${YELLOW}docker-compose -f docker-compose.local.yml ps${RESET}"
        echo -e "  View logs:         ${YELLOW}docker-compose -f docker-compose.local.yml logs -f${RESET}"
        echo -e "  Restart services:  ${YELLOW}docker-compose -f docker-compose.local.yml restart${RESET}"
    fi
}

main "$@"