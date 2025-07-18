#!/bin/bash
# Deployment Validation Script for Secure API Microservices Architecture
# Validates that all components are properly deployed and configured

set -euo pipefail

# Configuration
CLUSTER_NAME="alphintra-cluster"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Validation results tracking
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

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

log_check() {
    echo -e "${PURPLE}[CHECK]${NC} $1"
}

# Validation result functions
check_passed() {
    ((TOTAL_CHECKS++))
    ((PASSED_CHECKS++))
    log_success "✅ $1"
}

check_failed() {
    ((TOTAL_CHECKS++))
    ((FAILED_CHECKS++))
    log_error "❌ $1"
}

check_warning() {
    ((TOTAL_CHECKS++))
    ((WARNING_CHECKS++))
    log_warning "⚠️  $1"
}

# Validate cluster connectivity
validate_cluster() {
    log_info "Validating Cluster Connectivity..."
    
    if kubectl cluster-info >/dev/null 2>&1; then
        check_passed "Kubernetes cluster is accessible"
    else
        check_failed "Cannot connect to Kubernetes cluster"
        return 1
    fi
    
    # Check if it's the correct cluster
    local current_context
    current_context=$(kubectl config current-context)
    if [[ "$current_context" == *"$CLUSTER_NAME"* ]]; then
        check_passed "Connected to correct cluster: $current_context"
    else
        check_warning "Current context '$current_context' doesn't match expected cluster '$CLUSTER_NAME'"
    fi
    
    # Check cluster health
    if kubectl get nodes --no-headers | grep -q "Ready"; then
        check_passed "Cluster nodes are ready"
    else
        check_failed "Cluster nodes are not ready"
    fi
}

# Validate namespaces
validate_namespaces() {
    log_info "Validating Namespaces..."
    
    local required_namespaces=("alphintra" "monitoring")
    
    for namespace in "${required_namespaces[@]}"; do
        if kubectl get namespace "$namespace" >/dev/null 2>&1; then
            check_passed "Namespace '$namespace' exists"
        else
            check_failed "Namespace '$namespace' does not exist"
        fi
    done
    
    # Check Istio injection on alphintra namespace
    if kubectl get namespace alphintra -o jsonpath='{.metadata.labels.istio-injection}' 2>/dev/null | grep -q "enabled"; then
        check_passed "Istio injection enabled on alphintra namespace"
    else
        check_warning "Istio injection not enabled on alphintra namespace"
    fi
}

# Validate core infrastructure
validate_infrastructure() {
    log_info "Validating Core Infrastructure..."
    
    local infrastructure_components=(
        "postgresql-primary:StatefulSet:alphintra"
        "redis-primary:StatefulSet:alphintra"
        "eureka-server:Deployment:alphintra"
        "config-server:Deployment:alphintra"
        "api-gateway:Deployment:alphintra"
    )
    
    for component in "${infrastructure_components[@]}"; do
        IFS=":" read -r name type namespace <<< "$component"
        
        if kubectl get "$type" "$name" -n "$namespace" >/dev/null 2>&1; then
            local ready_replicas
            local desired_replicas
            
            if [[ "$type" == "StatefulSet" ]]; then
                ready_replicas=$(kubectl get "$type" "$name" -n "$namespace" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
                desired_replicas=$(kubectl get "$type" "$name" -n "$namespace" -o jsonpath='{.spec.replicas}')
            else
                ready_replicas=$(kubectl get "$type" "$name" -n "$namespace" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
                desired_replicas=$(kubectl get "$type" "$name" -n "$namespace" -o jsonpath='{.spec.replicas}')
            fi
            
            if [[ "${ready_replicas:-0}" == "${desired_replicas:-1}" ]]; then
                check_passed "$type/$name is ready ($ready_replicas/$desired_replicas)"
            else
                check_failed "$type/$name is not ready ($ready_replicas/$desired_replicas)"
            fi
        else
            check_failed "$type/$name does not exist in namespace $namespace"
        fi
    done
}

# Validate microservices
validate_microservices() {
    log_info "Validating Microservices..."
    
    local microservices=(
        "trading-service"
        "risk-service"
        "user-service"
        "no-code-service"
        "strategy-service"
        "broker-service"
        "notification-service"
        "graphql-gateway"
    )
    
    for service in "${microservices[@]}"; do
        # Check deployment
        if kubectl get deployment "$service" -n alphintra >/dev/null 2>&1; then
            local ready_replicas
            local desired_replicas
            ready_replicas=$(kubectl get deployment "$service" -n alphintra -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
            desired_replicas=$(kubectl get deployment "$service" -n alphintra -o jsonpath='{.spec.replicas}')
            
            if [[ "${ready_replicas:-0}" == "${desired_replicas:-1}" ]]; then
                check_passed "Microservice $service is ready ($ready_replicas/$desired_replicas)"
            else
                check_failed "Microservice $service is not ready ($ready_replicas/$desired_replicas)"
            fi
        else
            check_failed "Microservice deployment $service does not exist"
        fi
        
        # Check service
        if kubectl get service "$service" -n alphintra >/dev/null 2>&1; then
            check_passed "Service $service exists"
        else
            check_failed "Service $service does not exist"
        fi
        
        # Check HPA if exists
        if kubectl get hpa "${service}-hpa" -n alphintra >/dev/null 2>&1; then
            check_passed "HPA for $service is configured"
        else
            check_warning "HPA for $service is not configured"
        fi
    done
}

# Validate monitoring stack
validate_monitoring() {
    log_info "Validating Monitoring Stack..."
    
    local monitoring_components=(
        "prometheus:Deployment:monitoring"
        "grafana:Deployment:monitoring"
        "jaeger:Deployment:monitoring"
        "alertmanager:Deployment:monitoring"
    )
    
    for component in "${monitoring_components[@]}"; do
        IFS=":" read -r name type namespace <<< "$component"
        
        if kubectl get "$type" "$name" -n "$namespace" >/dev/null 2>&1; then
            local ready_replicas
            local desired_replicas
            ready_replicas=$(kubectl get "$type" "$name" -n "$namespace" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
            desired_replicas=$(kubectl get "$type" "$name" -n "$namespace" -o jsonpath='{.spec.replicas}')
            
            if [[ "${ready_replicas:-0}" == "${desired_replicas:-1}" ]]; then
                check_passed "Monitoring component $name is ready ($ready_replicas/$desired_replicas)"
            else
                check_failed "Monitoring component $name is not ready ($ready_replicas/$desired_replicas)"
            fi
        else
            check_failed "Monitoring component $type/$name does not exist"
        fi
    done
    
    # Check monitoring services
    local monitoring_services=("prometheus" "grafana" "jaeger-query" "alertmanager")
    for service in "${monitoring_services[@]}"; do
        if kubectl get service "$service" -n monitoring >/dev/null 2>&1; then
            check_passed "Monitoring service $service exists"
        else
            check_failed "Monitoring service $service does not exist"
        fi
    done
    
    # Check PVCs
    local monitoring_pvcs=("prometheus-pvc" "grafana-pvc")
    for pvc in "${monitoring_pvcs[@]}"; do
        if kubectl get pvc "$pvc" -n monitoring >/dev/null 2>&1; then
            local status
            status=$(kubectl get pvc "$pvc" -n monitoring -o jsonpath='{.status.phase}')
            if [[ "$status" == "Bound" ]]; then
                check_passed "PVC $pvc is bound"
            else
                check_failed "PVC $pvc is not bound (status: $status)"
            fi
        else
            check_failed "PVC $pvc does not exist"
        fi
    done
}

# Validate network policies and security
validate_security() {
    log_info "Validating Security Configuration..."
    
    # Check network policies
    if kubectl get networkpolicies -n alphintra --no-headers | wc -l | grep -q "^[1-9]"; then
        check_passed "Network policies are configured"
    else
        check_warning "No network policies found in alphintra namespace"
    fi
    
    # Check service accounts
    local service_accounts=("default" "prometheus")
    for sa in "${service_accounts[@]}"; do
        if kubectl get serviceaccount "$sa" -n alphintra >/dev/null 2>&1 || kubectl get serviceaccount "$sa" -n monitoring >/dev/null 2>&1; then
            check_passed "Service account $sa exists"
        else
            check_failed "Service account $sa does not exist"
        fi
    done
    
    # Check RBAC
    if kubectl get clusterrole prometheus >/dev/null 2>&1; then
        check_passed "Prometheus ClusterRole exists"
    else
        check_failed "Prometheus ClusterRole does not exist"
    fi
    
    if kubectl get clusterrolebinding prometheus >/dev/null 2>&1; then
        check_passed "Prometheus ClusterRoleBinding exists"
    else
        check_failed "Prometheus ClusterRoleBinding does not exist"
    fi
    
    # Check secrets
    local secrets=("api-gateway-secret")
    for secret in "${secrets[@]}"; do
        if kubectl get secret "$secret" -n alphintra >/dev/null 2>&1; then
            check_passed "Secret $secret exists"
        else
            check_warning "Secret $secret does not exist"
        fi
    done
}

# Validate ingress and load balancing
validate_ingress() {
    log_info "Validating Ingress and Load Balancing..."
    
    # Check API Gateway external service
    if kubectl get service api-gateway-external -n alphintra >/dev/null 2>&1; then
        local service_type
        service_type=$(kubectl get service api-gateway-external -n alphintra -o jsonpath='{.spec.type}')
        if [[ "$service_type" == "NodePort" ]]; then
            local node_port
            node_port=$(kubectl get service api-gateway-external -n alphintra -o jsonpath='{.spec.ports[0].nodePort}')
            check_passed "API Gateway external service is configured (NodePort: $node_port)"
        else
            check_warning "API Gateway external service type is $service_type (expected NodePort)"
        fi
    else
        check_failed "API Gateway external service does not exist"
    fi
    
    # Check ingress controller
    if kubectl get pods -n ingress-nginx --no-headers 2>/dev/null | grep -q "ingress-nginx-controller"; then
        check_passed "NGINX Ingress Controller is deployed"
    else
        check_warning "NGINX Ingress Controller is not deployed"
    fi
    
    # Check ingress resources
    if kubectl get ingress -n alphintra --no-headers | wc -l | grep -q "^[1-9]"; then
        check_passed "Ingress resources are configured"
    else
        check_warning "No ingress resources found"
    fi
}

# Validate persistent volumes
validate_storage() {
    log_info "Validating Storage Configuration..."
    
    # Check PVCs
    local pvcs_info
    pvcs_info=$(kubectl get pvc -A --no-headers 2>/dev/null | wc -l)
    if [[ "$pvcs_info" -gt 0 ]]; then
        check_passed "Persistent Volume Claims are configured ($pvcs_info PVCs found)"
    else
        check_warning "No Persistent Volume Claims found"
    fi
    
    # Check specific PVCs
    local required_pvcs=(
        "prometheus-pvc:monitoring"
        "grafana-pvc:monitoring"
    )
    
    for pvc_info in "${required_pvcs[@]}"; do
        IFS=":" read -r pvc namespace <<< "$pvc_info"
        if kubectl get pvc "$pvc" -n "$namespace" >/dev/null 2>&1; then
            local status
            status=$(kubectl get pvc "$pvc" -n "$namespace" -o jsonpath='{.status.phase}')
            local capacity
            capacity=$(kubectl get pvc "$pvc" -n "$namespace" -o jsonpath='{.status.capacity.storage}')
            check_passed "PVC $pvc is $status with capacity $capacity"
        else
            check_failed "Required PVC $pvc does not exist in namespace $namespace"
        fi
    done
}

# Validate environment variables and configuration
validate_configuration() {
    log_info "Validating Configuration..."
    
    # Check ConfigMaps
    local configmaps=(
        "api-gateway-config:alphintra"
        "prometheus-config:monitoring"
        "grafana-config:monitoring"
        "alertmanager-config:monitoring"
    )
    
    for cm_info in "${configmaps[@]}"; do
        IFS=":" read -r cm namespace <<< "$cm_info"
        if kubectl get configmap "$cm" -n "$namespace" >/dev/null 2>&1; then
            check_passed "ConfigMap $cm exists in namespace $namespace"
        else
            check_warning "ConfigMap $cm does not exist in namespace $namespace"
        fi
    done
    
    # Check environment variables in key deployments
    local key_deployments=("api-gateway" "trading-service" "no-code-service")
    for deployment in "${key_deployments[@]}"; do
        if kubectl get deployment "$deployment" -n alphintra >/dev/null 2>&1; then
            local env_vars
            env_vars=$(kubectl get deployment "$deployment" -n alphintra -o jsonpath='{.spec.template.spec.containers[0].env[*].name}' 2>/dev/null || echo "")
            if [[ -n "$env_vars" ]]; then
                check_passed "Deployment $deployment has environment variables configured"
            else
                check_warning "Deployment $deployment has no environment variables configured"
            fi
        fi
    done
}

# Validate resource limits and requests
validate_resources() {
    log_info "Validating Resource Configuration..."
    
    # Check resource requests and limits
    local deployments
    deployments=$(kubectl get deployments -n alphintra --no-headers | awk '{print $1}')
    
    local deployments_with_resources=0
    local total_deployments=0
    
    for deployment in $deployments; do
        ((total_deployments++))
        local has_requests
        local has_limits
        has_requests=$(kubectl get deployment "$deployment" -n alphintra -o jsonpath='{.spec.template.spec.containers[0].resources.requests}' 2>/dev/null)
        has_limits=$(kubectl get deployment "$deployment" -n alphintra -o jsonpath='{.spec.template.spec.containers[0].resources.limits}' 2>/dev/null)
        
        if [[ -n "$has_requests" && -n "$has_limits" ]]; then
            ((deployments_with_resources++))
            check_passed "Deployment $deployment has resource requests and limits configured"
        else
            check_warning "Deployment $deployment missing resource configuration"
        fi
    done
    
    if [[ $deployments_with_resources -eq $total_deployments ]]; then
        check_passed "All deployments have resource configuration"
    else
        check_warning "$deployments_with_resources/$total_deployments deployments have resource configuration"
    fi
}

# Generate validation report
generate_validation_report() {
    log_info "Generating Validation Report..."
    
    local report_file="$PROJECT_ROOT/validation-report-$(date +%Y%m%d-%H%M%S).txt"
    local success_rate=0
    
    if [[ $TOTAL_CHECKS -gt 0 ]]; then
        success_rate=$(( PASSED_CHECKS * 100 / TOTAL_CHECKS ))
    fi
    
    cat > "$report_file" << EOF
=======================================================
Alphintra Secure API Microservices Validation Report
=======================================================
Date: $(date)
Cluster: $CLUSTER_NAME
Kubernetes Context: $(kubectl config current-context)

VALIDATION SUMMARY:
Total Checks: $TOTAL_CHECKS
Passed: $PASSED_CHECKS
Failed: $FAILED_CHECKS
Warnings: $WARNING_CHECKS
Success Rate: ${success_rate}%

COMPONENT STATUS:
- Cluster Connectivity: $(if kubectl cluster-info >/dev/null 2>&1; then echo "✅ HEALTHY"; else echo "❌ FAILED"; fi)
- Namespaces: $(if kubectl get namespace alphintra monitoring >/dev/null 2>&1; then echo "✅ CONFIGURED"; else echo "❌ MISSING"; fi)
- Core Infrastructure: $(if kubectl get statefulset postgresql-primary redis-primary -n alphintra >/dev/null 2>&1; then echo "✅ DEPLOYED"; else echo "❌ INCOMPLETE"; fi)
- API Gateway: $(if kubectl get deployment api-gateway -n alphintra >/dev/null 2>&1; then echo "✅ DEPLOYED"; else echo "❌ MISSING"; fi)
- Microservices: $(kubectl get deployments -n alphintra --no-headers | wc -l) services deployed
- Monitoring Stack: $(if kubectl get deployment prometheus grafana -n monitoring >/dev/null 2>&1; then echo "✅ DEPLOYED"; else echo "❌ INCOMPLETE"; fi)
- Security: $(if kubectl get networkpolicies -n alphintra >/dev/null 2>&1; then echo "✅ CONFIGURED"; else echo "⚠️  BASIC"; fi)

READINESS STATUS:
$(kubectl get pods -n alphintra --no-headers | awk '{print $1 ": " $3}')

MONITORING SERVICES:
$(kubectl get pods -n monitoring --no-headers | awk '{print $1 ": " $3}')

RESOURCE UTILIZATION:
$(kubectl top nodes 2>/dev/null || echo "Metrics server not available")

RECOMMENDATIONS:
$(if [[ $FAILED_CHECKS -gt 0 ]]; then
    echo "- Address $FAILED_CHECKS failed checks before production deployment"
fi)
$(if [[ $WARNING_CHECKS -gt 0 ]]; then
    echo "- Review $WARNING_CHECKS warnings for optimization opportunities"
fi)
$(if [[ $success_rate -lt 90 ]]; then
    echo "- Success rate below 90% - significant issues detected"
elif [[ $success_rate -lt 95 ]]; then
    echo "- Success rate below 95% - minor issues detected"
else
    echo "- System validation successful - ready for deployment"
fi)

=======================================================
EOF

    log_success "Validation report generated: $report_file"
}

# Main execution
main() {
    log_info "Starting Deployment Validation for Alphintra Secure API Microservices"
    echo "======================================================="
    
    validate_cluster
    validate_namespaces
    validate_infrastructure
    validate_microservices
    validate_monitoring
    validate_security
    validate_ingress
    validate_storage
    validate_configuration
    validate_resources
    
    generate_validation_report
    
    echo "======================================================="
    log_info "Validation Summary:"
    echo "  Total Checks: $TOTAL_CHECKS"
    echo "  Passed: $PASSED_CHECKS"
    echo "  Failed: $FAILED_CHECKS"
    echo "  Warnings: $WARNING_CHECKS"
    
    local success_rate=0
    if [[ $TOTAL_CHECKS -gt 0 ]]; then
        success_rate=$(( PASSED_CHECKS * 100 / TOTAL_CHECKS ))
    fi
    echo "  Success Rate: ${success_rate}%"
    
    if [[ $FAILED_CHECKS -eq 0 ]]; then
        log_success "🎉 Validation completed successfully! System is ready for production."
        return 0
    else
        log_error "💥 Validation failed with $FAILED_CHECKS critical issues. Please address these before proceeding."
        return 1
    fi
}

# Handle script arguments
case "${1:-all}" in
    "cluster")
        validate_cluster
        ;;
    "namespaces")
        validate_namespaces
        ;;
    "infrastructure")
        validate_infrastructure
        ;;
    "microservices")
        validate_microservices
        ;;
    "monitoring")
        validate_monitoring
        ;;
    "security")
        validate_security
        ;;
    "ingress")
        validate_ingress
        ;;
    "storage")
        validate_storage
        ;;
    "configuration")
        validate_configuration
        ;;
    "resources")
        validate_resources
        ;;
    "all"|*)
        main
        ;;
esac