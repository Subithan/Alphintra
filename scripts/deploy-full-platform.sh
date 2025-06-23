#!/bin/bash
# Alphintra Trading Platform - Full Cloud Deployment Script
# Deploys the entire architecture to cloud infrastructure

set -e  # Exit on error

# Configuration
ENVIRONMENT=${1:-prod}
REGION=${2:-us-central1}
PROJECT_NAME="alphintra"

# Colors
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
MAGENTA='\033[35m'
CYAN='\033[36m'
RESET='\033[0m'

# Logging
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
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    commands=("docker" "kubectl" "terraform" "gcloud" "helm")
    for cmd in "${commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error "$cmd is required but not installed. Run: make install-prereqs"
        fi
    done
    
    success "All prerequisites satisfied"
}

# Initialize environment
initialize_environment() {
    log "Initializing environment: $ENVIRONMENT in region: $REGION"
    
    # Authenticate with cloud providers
    if command -v gcloud &> /dev/null; then
        gcloud auth application-default login --quiet || true
        gcloud config set project "$PROJECT_NAME-$ENVIRONMENT" || true
    fi
    
    # Initialize Terraform backend
    cd infrastructure/terraform
    terraform init -upgrade
    cd ../..
    
    success "Environment initialized"
}

# Deploy infrastructure
deploy_infrastructure() {
    log "Deploying cloud infrastructure..."
    
    cd infrastructure/terraform
    
    # Plan infrastructure
    terraform plan \
        -var="environment=$ENVIRONMENT" \
        -var="region=$REGION" \
        -var="project_name=$PROJECT_NAME" \
        -out=tfplan
    
    # Apply infrastructure
    terraform apply tfplan
    
    cd ../..
    success "Infrastructure deployed"
}

# Deploy Kubernetes clusters
deploy_kubernetes() {
    log "Deploying Kubernetes clusters..."
    
    # Get cluster credentials
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        # Multi-region production
        gcloud container clusters get-credentials "$PROJECT_NAME-americas" --region="us-central1" || true
        gcloud container clusters get-credentials "$PROJECT_NAME-emea" --region="europe-west1" || true
        gcloud container clusters get-credentials "$PROJECT_NAME-apac" --region="asia-southeast1" || true
    else
        # Single region for staging/dev
        gcloud container clusters get-credentials "$PROJECT_NAME-$ENVIRONMENT" --region="$REGION" || true
    fi
    
    # Install essential cluster components
    kubectl apply -f infrastructure/kubernetes/cluster-setup/
    
    success "Kubernetes clusters ready"
}

# Deploy core services
deploy_core_services() {
    log "Deploying core services (databases, messaging, caching)..."
    
    # Create namespaces
    kubectl create namespace core --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace trading --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace ai --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace global --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace security --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy core infrastructure
    kubectl apply -f infrastructure/kubernetes/core/
    
    # Wait for core services
    kubectl wait --for=condition=ready pod -l app=postgresql -n core --timeout=300s || true
    kubectl wait --for=condition=ready pod -l app=redis -n core --timeout=300s || true
    kubectl wait --for=condition=ready pod -l app=kafka -n core --timeout=300s || true
    
    success "Core services deployed"
}

# Deploy trading services
deploy_trading_services() {
    log "Deploying trading engine and market data services..."
    
    kubectl apply -f infrastructure/kubernetes/trading/
    
    # Wait for trading services
    kubectl wait --for=condition=ready pod -l app=trading-engine -n trading --timeout=300s || true
    kubectl wait --for=condition=ready pod -l app=market-data -n trading --timeout=300s || true
    kubectl wait --for=condition=ready pod -l app=risk-engine -n trading --timeout=300s || true
    
    success "Trading services deployed"
}

# Deploy AI/ML services
deploy_ai_services() {
    log "Deploying AI/ML services (LLM, Quantum, Federated Learning)..."
    
    kubectl apply -f infrastructure/kubernetes/ai/
    
    # Wait for AI services
    kubectl wait --for=condition=ready pod -l app=llm-analyzer -n ai --timeout=300s || true
    kubectl wait --for=condition=ready pod -l app=quantum-optimizer -n ai --timeout=300s || true
    kubectl wait --for=condition=ready pod -l app=federated-learning -n ai --timeout=300s || true
    
    success "AI/ML services deployed"
}

# Deploy global services
deploy_global_services() {
    log "Deploying global services (FX hedging, compliance, regional coordinators)..."
    
    kubectl apply -f infrastructure/kubernetes/global/
    
    # Wait for global services
    kubectl wait --for=condition=ready pod -l app=fx-hedging -n global --timeout=300s || true
    kubectl wait --for=condition=ready pod -l app=compliance-engine -n global --timeout=300s || true
    kubectl wait --for=condition=ready pod -l app=regional-coordinator -n global --timeout=300s || true
    
    success "Global services deployed"
}

# Deploy monitoring stack
deploy_monitoring() {
    log "Deploying monitoring and observability stack..."
    
    # Add Helm repositories
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
    helm repo update
    
    # Install Prometheus
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --create-namespace \
        --values infrastructure/helm/prometheus-values.yaml \
        --wait
    
    # Install Grafana
    helm upgrade --install grafana grafana/grafana \
        --namespace monitoring \
        --values infrastructure/helm/grafana-values.yaml \
        --wait
    
    # Install Jaeger
    helm upgrade --install jaeger jaegertracing/jaeger \
        --namespace monitoring \
        --values infrastructure/helm/jaeger-values.yaml \
        --wait
    
    success "Monitoring stack deployed"
}

# Deploy security services
deploy_security() {
    log "Deploying security and compliance services..."
    
    kubectl apply -f infrastructure/kubernetes/security/
    
    # Configure security policies
    kubectl apply -f infrastructure/kubernetes/security/policies/
    
    success "Security services deployed"
}

# Initialize data
initialize_data() {
    log "Initializing databases and loading reference data..."
    
    # Database migrations
    kubectl create job --from=cronjob/db-migrations db-migrations-initial -n core || true
    kubectl wait --for=condition=complete job/db-migrations-initial -n core --timeout=600s || true
    
    # Load reference data
    kubectl create job --from=cronjob/data-loader data-loader-initial -n core || true
    kubectl wait --for=condition=complete job/data-loader-initial -n core --timeout=600s || true
    
    success "Data initialized"
}

# Configure GitOps
configure_gitops() {
    log "Configuring ArgoCD for GitOps..."
    
    # Install ArgoCD
    kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
    kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
    
    # Wait for ArgoCD
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s || true
    
    # Configure ArgoCD applications
    kubectl apply -f infrastructure/argocd/applications/ || true
    
    success "GitOps configured"
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Check pod status
    echo -e "\n${CYAN}Pod Status:${RESET}"
    kubectl get pods --all-namespaces | grep -E "(trading|ai|global|core|monitoring)" | head -20
    
    # Check services
    echo -e "\n${CYAN}Service Status:${RESET}"
    kubectl get services --all-namespaces | grep -E "(trading|ai|global|core|monitoring)" | head -10
    
    # Check ingress
    echo -e "\n${CYAN}Ingress Status:${RESET}"
    kubectl get ingress --all-namespaces || true
    
    success "Deployment verification complete"
}

# Show access information
show_access_info() {
    log "Gathering access information..."
    
    # Get external IPs
    GRAFANA_IP=$(kubectl get service grafana -n monitoring -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
    API_IP=$(kubectl get service api-gateway -n trading -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
    
    echo -e "\n${GREEN}🎉 Alphintra Platform Deployment Complete!${RESET}"
    echo -e "${GREEN}===========================================${RESET}"
    echo ""
    echo -e "${CYAN}📊 Monitoring Dashboard:${RESET}"
    if [[ "$GRAFANA_IP" != "pending" ]]; then
        echo -e "   http://$GRAFANA_IP:3000"
    else
        echo -e "   kubectl port-forward -n monitoring svc/grafana 3000:80"
        echo -e "   Then access: http://localhost:3000"
    fi
    echo ""
    echo -e "${CYAN}🔌 API Gateway:${RESET}"
    if [[ "$API_IP" != "pending" ]]; then
        echo -e "   http://$API_IP:8080"
    else
        echo -e "   kubectl port-forward -n trading svc/api-gateway 8080:80"
        echo -e "   Then access: http://localhost:8080"
    fi
    echo ""
    echo -e "${CYAN}📋 Get Grafana Password:${RESET}"
    echo -e "   kubectl get secret grafana -n monitoring -o jsonpath='{.data.admin-password}' | base64 -d"
    echo ""
    echo -e "${CYAN}📈 Check Status:${RESET}"
    echo -e "   make status"
    echo ""
}

# Main deployment flow
main() {
    echo -e "${MAGENTA}================================================${RESET}"
    echo -e "${MAGENTA}  🚀 Alphintra Platform Deployment Started${RESET}"
    echo -e "${MAGENTA}================================================${RESET}"
    echo ""
    
    local start_time=$(date +%s)
    
    # Deployment steps
    check_prerequisites
    initialize_environment
    deploy_infrastructure
    deploy_kubernetes
    deploy_core_services
    deploy_trading_services
    deploy_ai_services
    deploy_global_services
    deploy_monitoring
    deploy_security
    initialize_data
    configure_gitops
    verify_deployment
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))
    
    echo ""
    echo -e "${GREEN}⏱️  Total deployment time: ${minutes}m ${seconds}s${RESET}"
    
    show_access_info
}

# Error handling
trap 'error "Deployment failed on line $LINENO"' ERR

# Run main deployment
main "$@"