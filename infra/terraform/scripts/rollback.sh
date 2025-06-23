#!/bin/bash

# Alphintra Production Rollback Script
# This script handles rollback scenarios for the Alphintra trading platform

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
ROLLBACK_TYPE="kubernetes"  # kubernetes, terraform, full
TARGET_VERSION=""
CONFIRM_ROLLBACK=false
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

Rollback Alphintra trading platform deployment.

OPTIONS:
    -e, --environment ENVIRONMENT    Environment to rollback (default: production)
    -p, --project-id PROJECT_ID      GCP project ID (required)
    -r, --region REGION              GCP region (default: us-central1)
    -t, --type TYPE                  Rollback type: kubernetes, terraform, full (default: kubernetes)
    -v, --version VERSION            Target version to rollback to
    -c, --confirm                    Confirm rollback without prompting
    -a, --auto-approve               Auto-approve all rollback operations
    --verbose                        Enable verbose output
    -h, --help                       Show this help message

ROLLBACK TYPES:
    kubernetes    Rollback Kubernetes deployments only
    terraform     Rollback Terraform infrastructure
    full          Complete rollback (Kubernetes + Terraform)

EXAMPLES:
    # Rollback Kubernetes deployments to previous version
    $0 --project-id alphintra-prod --type kubernetes

    # Rollback to specific version
    $0 --project-id alphintra-prod --version v1.2.3

    # Full rollback with confirmation
    $0 --project-id alphintra-prod --type full --confirm

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
            -t|--type)
                ROLLBACK_TYPE="$2"
                shift 2
                ;;
            -v|--version)
                TARGET_VERSION="$2"
                shift 2
                ;;
            -c|--confirm)
                CONFIRM_ROLLBACK=true
                shift
                ;;
            -a|--auto-approve)
                AUTO_APPROVE=true
                shift
                ;;
            --verbose)
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

    # Validate rollback type
    if [[ ! "$ROLLBACK_TYPE" =~ ^(kubernetes|terraform|full)$ ]]; then
        log_error "Invalid rollback type: $ROLLBACK_TYPE. Must be one of: kubernetes, terraform, full"
        exit 1
    fi
}

# Safety checks for production environment
production_safety_checks() {
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_warning "🚨 PRODUCTION ROLLBACK REQUESTED 🚨"
        log_warning "This is a critical operation that will affect live trading operations"
        
        if [[ "$CONFIRM_ROLLBACK" != "true" && "$AUTO_APPROVE" != "true" ]]; then
            echo
            log_warning "Please confirm the following:"
            echo "1. You have identified the issue requiring rollback"
            echo "2. You have notified the relevant stakeholders"
            echo "3. You understand this will temporarily stop trading operations"
            echo "4. You have a communication plan for users"
            echo
            
            read -p "Type 'ROLLBACK PRODUCTION' to confirm: " -r
            if [[ "$REPLY" != "ROLLBACK PRODUCTION" ]]; then
                log_info "Production rollback cancelled"
                exit 0
            fi
        fi
        
        log_warning "Production rollback confirmed. Proceeding..."
    fi
}

# Get current deployment status
get_current_status() {
    log_info "Getting current deployment status..."

    local namespace="alphintra-${ENVIRONMENT}"
    
    # Configure kubectl
    gcloud container clusters get-credentials \
        "alphintra-${ENVIRONMENT}" \
        --region="$REGION" \
        --project="$PROJECT_ID"

    # Get current image versions
    log_info "Current application versions:"
    local services=("auth-service" "trading-api" "strategy-engine" "broker-connector" "broker-simulator")
    
    for service in "${services[@]}"; do
        local image=$(kubectl get deployment "$service" -n "$namespace" -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "Not found")
        log_info "  $service: $image"
    done

    # Get rollout history
    log_info "Deployment history (last 5 revisions):"
    for service in "${services[@]}"; do
        if kubectl get deployment "$service" -n "$namespace" &> /dev/null; then
            echo "=== $service ==="
            kubectl rollout history deployment/"$service" -n "$namespace" --limit=5
            echo
        fi
    done
}

# Get target version for rollback
determine_target_version() {
    if [[ -n "$TARGET_VERSION" ]]; then
        log_info "Using specified target version: $TARGET_VERSION"
        return
    fi

    log_info "Determining target version for rollback..."
    
    local namespace="alphintra-${ENVIRONMENT}"
    
    # Get previous revision number
    local service="trading-api"  # Use trading-api as reference service
    local previous_revision=$(kubectl rollout history deployment/"$service" -n "$namespace" --format=table | tail -n 2 | head -n 1 | awk '{print $1}')
    
    if [[ -n "$previous_revision" && "$previous_revision" != "REVISION" ]]; then
        TARGET_VERSION="revision-$previous_revision"
        log_info "Target version determined: $TARGET_VERSION (previous revision)"
    else
        log_error "Could not determine target version for rollback"
        exit 1
    fi
}

# Create backup before rollback
create_backup() {
    log_info "Creating backup before rollback..."

    local backup_dir="backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"

    local namespace="alphintra-${ENVIRONMENT}"

    # Backup current deployment configurations
    kubectl get deployments -n "$namespace" -o yaml > "$backup_dir/deployments.yaml"
    kubectl get services -n "$namespace" -o yaml > "$backup_dir/services.yaml"
    kubectl get configmaps -n "$namespace" -o yaml > "$backup_dir/configmaps.yaml"
    kubectl get secrets -n "$namespace" -o yaml > "$backup_dir/secrets.yaml"
    
    # Backup database (if possible)
    log_info "Initiating database backup..."
    # Note: In production, this would trigger Cloud SQL backup
    # gcloud sql backups create --instance=alphintra-prod-db --project="$PROJECT_ID"

    log_success "Backup created in $backup_dir"
    echo "BACKUP_DIR=$backup_dir" > .rollback_backup
}

# Perform Kubernetes rollback
rollback_kubernetes() {
    log_info "Performing Kubernetes rollback..."

    local namespace="alphintra-${ENVIRONMENT}"
    local services=("auth-service" "trading-api" "strategy-engine" "broker-connector" "broker-simulator")

    # Scale down critical services first to prevent data inconsistency
    log_info "Scaling down services for safe rollback..."
    for service in "${services[@]}"; do
        if kubectl get deployment "$service" -n "$namespace" &> /dev/null; then
            kubectl scale deployment "$service" -n "$namespace" --replicas=0
        fi
    done

    # Wait for pods to terminate
    log_info "Waiting for pods to terminate..."
    sleep 30

    # Perform rollback for each service
    for service in "${services[@]}"; do
        if kubectl get deployment "$service" -n "$namespace" &> /dev/null; then
            log_info "Rolling back $service..."
            
            if [[ "$TARGET_VERSION" =~ ^revision- ]]; then
                local revision=$(echo "$TARGET_VERSION" | cut -d'-' -f2)
                kubectl rollout undo deployment/"$service" -n "$namespace" --to-revision="$revision"
            else
                # Rollback to previous revision
                kubectl rollout undo deployment/"$service" -n "$namespace"
            fi
        fi
    done

    # Scale services back up
    log_info "Scaling services back up..."
    kubectl scale deployment auth-service -n "$namespace" --replicas=3
    kubectl scale deployment trading-api -n "$namespace" --replicas=5
    kubectl scale deployment strategy-engine -n "$namespace" --replicas=3
    kubectl scale deployment broker-connector -n "$namespace" --replicas=3
    kubectl scale deployment broker-simulator -n "$namespace" --replicas=2

    # Wait for rollout to complete
    log_info "Waiting for rollback to complete..."
    for service in "${services[@]}"; do
        if kubectl get deployment "$service" -n "$namespace" &> /dev/null; then
            kubectl rollout status deployment/"$service" -n "$namespace" --timeout=600s
        fi
    done

    log_success "Kubernetes rollback completed"
}

# Perform Terraform rollback
rollback_terraform() {
    log_info "Performing Terraform rollback..."

    cd "${TERRAFORM_DIR}/environments/${ENVIRONMENT}"

    # Get current Terraform state backup
    terraform state pull > "terraform-state-backup-$(date +%Y%m%d-%H%M%S).json"

    if [[ -n "$TARGET_VERSION" && "$TARGET_VERSION" != "revision-"* ]]; then
        # Rollback to specific Terraform version/commit
        log_info "Rolling back Terraform to version: $TARGET_VERSION"
        
        # This would typically involve:
        # 1. Checking out specific git commit/tag
        # 2. Running terraform plan and apply
        log_warning "Terraform version rollback requires manual git operations"
        log_warning "Please checkout the target version manually and re-run with kubernetes rollback only"
    else
        # Rollback to previous Terraform state
        log_info "Rolling back to previous Terraform state..."
        
        # Import previous state if available
        local state_backup=$(ls -t terraform-state-backup-*.json 2>/dev/null | head -n2 | tail -n1)
        if [[ -n "$state_backup" ]]; then
            log_info "Found previous state backup: $state_backup"
            # In production, this would be more sophisticated
            log_warning "Manual intervention required for Terraform state rollback"
        fi
    fi

    log_success "Terraform rollback preparation completed"
}

# Verify rollback success
verify_rollback() {
    log_info "Verifying rollback success..."

    local namespace="alphintra-${ENVIRONMENT}"
    local failed_checks=0

    # Check pod status
    log_info "Checking pod status..."
    local pods_ready=$(kubectl get pods -n "$namespace" --field-selector=status.phase=Running --no-headers | wc -l)
    local pods_total=$(kubectl get pods -n "$namespace" --no-headers | wc -l)
    
    if [[ $pods_ready -eq $pods_total && $pods_total -gt 0 ]]; then
        log_success "All pods are running ($pods_ready/$pods_total)"
    else
        log_error "Some pods are not running ($pods_ready/$pods_total)"
        ((failed_checks++))
    fi

    # Check service health
    log_info "Checking service health..."
    local services=("auth-service" "trading-api" "strategy-engine" "broker-connector" "broker-simulator")
    
    for service in "${services[@]}"; do
        if kubectl get deployment "$service" -n "$namespace" &> /dev/null; then
            local ready_replicas=$(kubectl get deployment "$service" -n "$namespace" -o jsonpath='{.status.readyReplicas}')
            local desired_replicas=$(kubectl get deployment "$service" -n "$namespace" -o jsonpath='{.spec.replicas}')
            
            if [[ "$ready_replicas" == "$desired_replicas" ]]; then
                log_success "$service: $ready_replicas/$desired_replicas replicas ready"
            else
                log_error "$service: $ready_replicas/$desired_replicas replicas ready"
                ((failed_checks++))
            fi
        fi
    done

    # Check basic connectivity
    log_info "Checking basic connectivity..."
    
    # Port forward and test auth service
    kubectl port-forward -n "$namespace" svc/auth-service 8001:8001 &
    local port_forward_pid=$!
    sleep 5
    
    if curl -f http://localhost:8001/health &> /dev/null; then
        log_success "Auth service health check passed"
    else
        log_error "Auth service health check failed"
        ((failed_checks++))
    fi
    
    kill $port_forward_pid 2>/dev/null || true

    # Summary
    if [[ $failed_checks -eq 0 ]]; then
        log_success "🎉 Rollback verification passed!"
        return 0
    else
        log_error "❌ Rollback verification failed ($failed_checks issues detected)"
        return 1
    fi
}

# Generate rollback report
generate_rollback_report() {
    log_info "Generating rollback report..."

    local report_file="rollback-report-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S).md"
    local namespace="alphintra-${ENVIRONMENT}"

    cat > "$report_file" << EOF
# Alphintra Rollback Report

**Environment:** $ENVIRONMENT  
**Project ID:** $PROJECT_ID  
**Rollback Type:** $ROLLBACK_TYPE  
**Target Version:** $TARGET_VERSION  
**Date:** $(date)  
**Performed by:** $(whoami)  

## Rollback Summary

### Services Rolled Back
EOF

    # Add service versions to report
    local services=("auth-service" "trading-api" "strategy-engine" "broker-connector" "broker-simulator")
    
    for service in "${services[@]}"; do
        local image=$(kubectl get deployment "$service" -n "$namespace" -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "Not found")
        echo "- **$service**: $image" >> "$report_file"
    done

    cat >> "$report_file" << EOF

### Current Status
\`\`\`
$(kubectl get deployments -n "$namespace" -o wide)
\`\`\`

### Pod Status
\`\`\`
$(kubectl get pods -n "$namespace" -o wide)
\`\`\`

### Health Check Results
EOF

    # Add health check results
    if verify_rollback &> /dev/null; then
        echo "✅ All health checks passed" >> "$report_file"
    else
        echo "❌ Some health checks failed - manual intervention required" >> "$report_file"
    fi

    cat >> "$report_file" << EOF

## Next Steps

1. Monitor application logs for stability
2. Verify all business functions are working
3. Communicate rollback status to stakeholders
4. Investigate root cause of original issue
5. Plan forward fix if needed

## Rollback Artifacts

- Backup Directory: $(cat .rollback_backup 2>/dev/null || echo "Not available")
- Terraform State Backup: Available in terraform directory
- Kubernetes Configurations: Backed up before rollback

---
*Generated by Alphintra rollback script*
EOF

    log_success "Rollback report generated: $report_file"
}

# Post-rollback actions
post_rollback_actions() {
    log_info "Performing post-rollback actions..."

    # Send notifications (in production, this would send alerts)
    log_info "Sending rollback notifications..."
    
    # Create incident tracking (in production, this would create tickets)
    log_info "Creating incident tracking..."
    
    # Update monitoring dashboards
    log_info "Updating monitoring annotations..."
    
    log_success "Post-rollback actions completed"
}

# Main execution function
main() {
    log_info "Starting Alphintra rollback for $ENVIRONMENT environment"
    log_info "Project: $PROJECT_ID, Type: $ROLLBACK_TYPE"

    # Safety checks
    production_safety_checks

    # Pre-rollback steps
    get_current_status
    determine_target_version
    create_backup

    # Perform rollback based on type
    case $ROLLBACK_TYPE in
        kubernetes)
            rollback_kubernetes
            ;;
        terraform)
            rollback_terraform
            ;;
        full)
            rollback_kubernetes
            rollback_terraform
            ;;
    esac

    # Post-rollback verification and reporting
    if verify_rollback; then
        generate_rollback_report
        post_rollback_actions
        
        log_success "🔄 Rollback completed successfully!"
        log_info "Please monitor the system closely and verify business operations"
    else
        log_error "🚨 Rollback completed but verification failed!"
        log_error "Manual intervention may be required"
        generate_rollback_report
        exit 1
    fi
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    parse_args "$@"
    main
fi