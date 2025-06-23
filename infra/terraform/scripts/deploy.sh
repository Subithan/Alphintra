#!/bin/bash

# Alphintra Production Deployment Script
# This script automates the deployment of the Alphintra trading platform to production

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
TERRAFORM_DIR="${PROJECT_ROOT}/infra/terraform"
KUBERNETES_DIR="${PROJECT_ROOT}/infra/kubernetes"

# Default values
ENVIRONMENT="production"
PROJECT_ID=""
REGION="us-central1"
ZONE="us-central1-a"
DRY_RUN=false
SKIP_PLAN=false
AUTO_APPROVE=false
VERBOSE=false

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

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy Alphintra trading platform to production environment.

OPTIONS:
    -e, --environment ENVIRONMENT    Environment to deploy to (default: production)
    -p, --project-id PROJECT_ID      GCP project ID (required)
    -r, --region REGION              GCP region (default: us-central1)
    -z, --zone ZONE                  GCP zone (default: us-central1-a)
    -d, --dry-run                    Perform a dry run (plan only)
    -s, --skip-plan                  Skip terraform plan phase
    -a, --auto-approve               Auto-approve terraform apply
    -v, --verbose                    Enable verbose output
    -h, --help                       Show this help message

EXAMPLES:
    # Basic deployment
    $0 --project-id alphintra-prod

    # Dry run deployment
    $0 --project-id alphintra-prod --dry-run

    # Auto-approved deployment (CI/CD)
    $0 --project-id alphintra-prod --auto-approve

    # Staging environment deployment
    $0 --environment staging --project-id alphintra-staging

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -p|--project-id)
                PROJECT_ID="$2"
                shift 2
                ;;
            -r|--region)
                REGION="$2"
                shift 2
                ;;
            -z|--zone)
                ZONE="$2"
                shift 2
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -s|--skip-plan)
                SKIP_PLAN=true
                shift
                ;;
            -a|--auto-approve)
                AUTO_APPROVE=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    # Validate required arguments
    if [[ -z "$PROJECT_ID" ]]; then
        log_error "Project ID is required. Use -p or --project-id to specify."
        usage
        exit 1
    fi

    # Validate environment
    if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
        log_error "Invalid environment: $ENVIRONMENT. Must be one of: development, staging, production"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check required tools
    local required_tools=("terraform" "gcloud" "kubectl" "helm" "docker")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is not installed or not in PATH"
            exit 1
        fi
    done

    # Check terraform version
    local terraform_version=$(terraform version -json | jq -r '.terraform_version')
    local required_terraform_version="1.0.0"
    if ! printf '%s\n%s\n' "$required_terraform_version" "$terraform_version" | sort -V | head -n1 | grep -q "^$required_terraform_version$"; then
        log_error "Terraform version $terraform_version is too old. Required: $required_terraform_version or later"
        exit 1
    fi

    # Check Google Cloud SDK authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
        log_error "Not authenticated to Google Cloud. Run 'gcloud auth login' first"
        exit 1
    fi

    # Check project access
    if ! gcloud projects describe "$PROJECT_ID" &> /dev/null; then
        log_error "Cannot access project $PROJECT_ID. Check project ID and permissions"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Setup environment
setup_environment() {
    log_info "Setting up environment..."

    # Set Google Cloud project
    gcloud config set project "$PROJECT_ID"

    # Export environment variables
    export TF_VAR_project_id="$PROJECT_ID"
    export TF_VAR_region="$REGION"
    export TF_VAR_zone="$ZONE"
    export TF_VAR_environment="$ENVIRONMENT"

    # Set Terraform workspace
    cd "${TERRAFORM_DIR}/environments/${ENVIRONMENT}"
    terraform workspace select "$ENVIRONMENT" 2>/dev/null || terraform workspace new "$ENVIRONMENT"

    log_success "Environment setup completed"
}

# Initialize Terraform
init_terraform() {
    log_info "Initializing Terraform..."

    cd "${TERRAFORM_DIR}/environments/${ENVIRONMENT}"

    # Initialize with backend configuration
    terraform init \
        -backend-config="bucket=${PROJECT_ID}-terraform-state" \
        -backend-config="prefix=environments/${ENVIRONMENT}" \
        -upgrade

    log_success "Terraform initialization completed"
}

# Plan Terraform deployment
plan_terraform() {
    if [[ "$SKIP_PLAN" == "true" ]]; then
        log_warning "Skipping Terraform plan phase"
        return 0
    fi

    log_info "Planning Terraform deployment..."

    cd "${TERRAFORM_DIR}/environments/${ENVIRONMENT}"

    # Create plan file
    local plan_file="tfplan-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"
    
    terraform plan \
        -var-file="terraform.tfvars" \
        -out="$plan_file" \
        -detailed-exitcode

    local plan_exit_code=$?

    case $plan_exit_code in
        0)
            log_info "No changes detected in Terraform plan"
            ;;
        1)
            log_error "Terraform plan failed"
            exit 1
            ;;
        2)
            log_info "Changes detected in Terraform plan"
            
            # Show plan summary
            terraform show "$plan_file"
            
            if [[ "$DRY_RUN" == "true" ]]; then
                log_info "Dry run mode - stopping after plan"
                rm -f "$plan_file"
                exit 0
            fi
            
            # Prompt for approval if not auto-approved
            if [[ "$AUTO_APPROVE" != "true" ]]; then
                echo
                read -p "Do you want to apply these changes? (yes/no): " -r
                if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                    log_info "Deployment cancelled by user"
                    rm -f "$plan_file"
                    exit 0
                fi
            fi
            
            # Export plan file for apply phase
            export TERRAFORM_PLAN_FILE="$plan_file"
            ;;
    esac

    log_success "Terraform planning completed"
}

# Apply Terraform deployment
apply_terraform() {
    log_info "Applying Terraform deployment..."

    cd "${TERRAFORM_DIR}/environments/${ENVIRONMENT}"

    local apply_args=()
    
    if [[ -n "${TERRAFORM_PLAN_FILE:-}" ]]; then
        apply_args+=("$TERRAFORM_PLAN_FILE")
    else
        apply_args+=("-var-file=terraform.tfvars")
        if [[ "$AUTO_APPROVE" == "true" ]]; then
            apply_args+=("-auto-approve")
        fi
    fi

    terraform apply "${apply_args[@]}"

    # Clean up plan file
    if [[ -n "${TERRAFORM_PLAN_FILE:-}" ]]; then
        rm -f "$TERRAFORM_PLAN_FILE"
    fi

    log_success "Terraform deployment completed"
}

# Configure kubectl
configure_kubectl() {
    log_info "Configuring kubectl..."

    # Get GKE cluster credentials
    gcloud container clusters get-credentials \
        "alphintra-${ENVIRONMENT}" \
        --region="$REGION" \
        --project="$PROJECT_ID"

    # Verify cluster connection
    kubectl cluster-info

    log_success "kubectl configuration completed"
}

# Deploy Kubernetes applications
deploy_kubernetes() {
    log_info "Deploying Kubernetes applications..."

    cd "${KUBERNETES_DIR}/environments/${ENVIRONMENT}"

    # Apply security policies first
    log_info "Applying security policies..."
    kubectl apply -f "${KUBERNETES_DIR}/security/" --recursive

    # Apply base infrastructure
    log_info "Applying base infrastructure..."
    kubectl apply -k .

    # Wait for rollout to complete
    log_info "Waiting for deployment rollout..."
    kubectl rollout status deployment/auth-service -n "alphintra-${ENVIRONMENT}" --timeout=600s
    kubectl rollout status deployment/trading-api -n "alphintra-${ENVIRONMENT}" --timeout=600s
    kubectl rollout status deployment/strategy-engine -n "alphintra-${ENVIRONMENT}" --timeout=600s
    kubectl rollout status deployment/broker-connector -n "alphintra-${ENVIRONMENT}" --timeout=600s
    kubectl rollout status deployment/broker-simulator -n "alphintra-${ENVIRONMENT}" --timeout=600s

    log_success "Kubernetes deployment completed"
}

# Install ArgoCD
install_argocd() {
    log_info "Installing ArgoCD..."

    # Check if ArgoCD namespace exists
    if ! kubectl get namespace argocd &> /dev/null; then
        kubectl create namespace argocd
    fi

    # Install ArgoCD
    kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

    # Wait for ArgoCD to be ready
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=600s

    # Apply ArgoCD applications
    kubectl apply -f "${KUBERNETES_DIR}/gitops/app-of-apps.yaml"

    log_success "ArgoCD installation completed"
}

# Perform health checks
health_checks() {
    log_info "Performing health checks..."

    local namespace="alphintra-${ENVIRONMENT}"

    # Check pod status
    local pods_ready=$(kubectl get pods -n "$namespace" --field-selector=status.phase=Running --no-headers | wc -l)
    local pods_total=$(kubectl get pods -n "$namespace" --no-headers | wc -l)
    
    log_info "Pods ready: $pods_ready/$pods_total"

    # Check service endpoints
    local services=("auth-service" "trading-api" "strategy-engine" "broker-connector" "broker-simulator")
    
    for service in "${services[@]}"; do
        if kubectl get service "$service" -n "$namespace" &> /dev/null; then
            local endpoint=$(kubectl get service "$service" -n "$namespace" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
            if [[ -n "$endpoint" ]]; then
                log_success "$service endpoint: $endpoint"
            else
                log_warning "$service endpoint not ready yet"
            fi
        else
            log_warning "$service not found"
        fi
    done

    # Check ingress
    if kubectl get ingress -n "$namespace" &> /dev/null; then
        local ingress_ip=$(kubectl get ingress -n "$namespace" -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}')
        if [[ -n "$ingress_ip" ]]; then
            log_success "Ingress IP: $ingress_ip"
        else
            log_warning "Ingress IP not ready yet"
        fi
    fi

    log_success "Health checks completed"
}

# Generate deployment report
generate_report() {
    log_info "Generating deployment report..."

    local report_file="deployment-report-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S).md"
    local namespace="alphintra-${ENVIRONMENT}"

    cat > "$report_file" << EOF
# Alphintra Deployment Report

**Environment:** $ENVIRONMENT  
**Project ID:** $PROJECT_ID  
**Region:** $REGION  
**Date:** $(date)  
**Deployed by:** $(whoami)  

## Infrastructure

### GKE Cluster
\`\`\`
$(kubectl cluster-info)
\`\`\`

### Nodes
\`\`\`
$(kubectl get nodes -o wide)
\`\`\`

## Applications

### Deployments
\`\`\`
$(kubectl get deployments -n "$namespace" -o wide)
\`\`\`

### Services
\`\`\`
$(kubectl get services -n "$namespace" -o wide)
\`\`\`

### Pods
\`\`\`
$(kubectl get pods -n "$namespace" -o wide)
\`\`\`

## Configuration

### ConfigMaps
\`\`\`
$(kubectl get configmaps -n "$namespace")
\`\`\`

### Secrets
\`\`\`
$(kubectl get secrets -n "$namespace")
\`\`\`

## Monitoring

### HPA Status
\`\`\`
$(kubectl get hpa -n "$namespace" -o wide)
\`\`\`

### Resource Usage
\`\`\`
$(kubectl top pods -n "$namespace" --no-headers 2>/dev/null || echo "Metrics server not available")
\`\`\`

## Health Status

### Service Health
EOF

    # Add service health checks to report
    local services=("auth-service" "trading-api" "strategy-engine" "broker-connector" "broker-simulator")
    
    for service in "${services[@]}"; do
        echo "- **$service**: $(kubectl get deployment "$service" -n "$namespace" -o jsonpath='{.status.readyReplicas}/{.status.replicas}' 2>/dev/null || echo "Not found") pods ready" >> "$report_file"
    done

    cat >> "$report_file" << EOF

## Next Steps

1. Monitor application logs for any issues
2. Verify all service endpoints are responding
3. Run integration tests
4. Configure monitoring alerts
5. Update DNS records if needed

---
*Generated by Alphintra deployment script*
EOF

    log_success "Deployment report generated: $report_file"
}

# Cleanup on script exit
cleanup() {
    local exit_code=$?
    
    if [[ $exit_code -ne 0 ]]; then
        log_error "Deployment failed with exit code $exit_code"
    fi
    
    # Clean up temporary files
    rm -f tfplan-* 2>/dev/null || true
    
    exit $exit_code
}

# Main execution function
main() {
    trap cleanup EXIT

    log_info "Starting Alphintra deployment to $ENVIRONMENT environment"
    log_info "Project: $PROJECT_ID, Region: $REGION"

    # Execute deployment steps
    check_prerequisites
    setup_environment
    init_terraform
    plan_terraform
    
    if [[ "$DRY_RUN" != "true" ]]; then
        apply_terraform
        configure_kubectl
        deploy_kubernetes
        install_argocd
        health_checks
        generate_report
        
        log_success "🎉 Deployment completed successfully!"
        log_info "Access your application at the ingress IP address shown above"
        log_info "ArgoCD UI: kubectl port-forward svc/argocd-server -n argocd 8080:443"
        log_info "Grafana: kubectl port-forward svc/grafana -n monitoring 3000:3000"
    else
        log_success "🔍 Dry run completed successfully!"
    fi
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    parse_args "$@"
    main
fi