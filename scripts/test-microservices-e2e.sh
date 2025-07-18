#!/bin/bash
# End-to-End Testing Script for Alphintra Secure Microservices Architecture
# Validates complete system functionality across all services

set -e

# Configuration
CLUSTER_NAME="alphintra-cluster"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
API_GATEWAY_URL="http://localhost:8080"
GRAPHQL_URL="$API_GATEWAY_URL/graphql"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

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

log_test() {
    echo -e "${PURPLE}[TEST]${NC} $1"
}

# Test result functions
test_passed() {
    ((TOTAL_TESTS++))
    ((PASSED_TESTS++))
    log_success "✅ $1"
}

test_failed() {
    ((TOTAL_TESTS++))
    ((FAILED_TESTS++))
    log_error "❌ $1"
}

# HTTP test helper
http_test() {
    local name="$1"
    local method="$2"
    local url="$3"
    local expected_status="$4"
    local data="${5:-}"
    
    log_test "Testing: $name"
    
    local curl_cmd="curl -s -o /tmp/test_response -w '%{http_code}' -X $method"
    if [[ -n "$data" ]]; then
        curl_cmd="$curl_cmd -H 'Content-Type: application/json' -d '$data'"
    fi
    curl_cmd="$curl_cmd '$url'"
    
    local status_code
    if status_code=$(eval "$curl_cmd" 2>/dev/null); then
        if [[ "$status_code" == "$expected_status" ]]; then
            test_passed "$name - Status: $status_code"
            return 0
        else
            test_failed "$name - Expected: $expected_status, Got: $status_code"
            log_error "Response: $(cat /tmp/test_response 2>/dev/null || echo 'No response')"
            return 1
        fi
    else
        test_failed "$name - Connection failed"
        return 1
    fi
}

# GraphQL test helper
graphql_test() {
    local name="$1"
    local query="$2"
    local expected_fields="$3"
    
    log_test "Testing GraphQL: $name"
    
    local payload="{\"query\": \"$query\"}"
    local response
    
    if response=$(curl -s -X POST -H "Content-Type: application/json" -d "$payload" "$GRAPHQL_URL" 2>/dev/null); then
        if echo "$response" | jq -e ".data" >/dev/null 2>&1; then
            if [[ -n "$expected_fields" ]]; then
                if echo "$response" | jq -e "$expected_fields" >/dev/null 2>&1; then
                    test_passed "GraphQL $name - Query executed successfully"
                    return 0
                else
                    test_failed "GraphQL $name - Expected fields not found: $expected_fields"
                    log_error "Response: $response"
                    return 1
                fi
            else
                test_passed "GraphQL $name - Query executed successfully"
                return 0
            fi
        else
            test_failed "GraphQL $name - No data in response"
            log_error "Response: $response"
            return 1
        fi
    else
        test_failed "GraphQL $name - Connection failed"
        return 1
    fi
}

# Wait for services to be ready
wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    local services=(
        "api-gateway:alphintra:8080"
        "trading-service:alphintra:8080"
        "risk-service:alphintra:8080"
        "user-service:alphintra:8080"
        "no-code-service:alphintra:8080"
        "strategy-service:alphintra:8080"
        "broker-service:alphintra:8080"
        "notification-service:alphintra:8080"
        "graphql-gateway:alphintra:8080"
        "prometheus:monitoring:9090"
        "grafana:monitoring:3000"
    )
    
    for service_info in "${services[@]}"; do
        IFS=":" read -r service namespace port <<< "$service_info"
        log_info "Waiting for $service in namespace $namespace..."
        if kubectl wait --for=condition=Ready pod -l app="$service" -n "$namespace" --timeout=300s >/dev/null 2>&1; then
            log_success "$service is ready"
        else
            log_warning "$service is not ready within timeout"
        fi
    done
}

# Test infrastructure health
test_infrastructure() {
    log_info "Testing Infrastructure Health..."
    
    # Test cluster connectivity
    if kubectl cluster-info >/dev/null 2>&1; then
        test_passed "Kubernetes cluster connectivity"
    else
        test_failed "Kubernetes cluster connectivity"
    fi
    
    # Test namespace existence
    if kubectl get namespace alphintra >/dev/null 2>&1; then
        test_passed "Alphintra namespace exists"
    else
        test_failed "Alphintra namespace exists"
    fi
    
    # Test monitoring namespace
    if kubectl get namespace monitoring >/dev/null 2>&1; then
        test_passed "Monitoring namespace exists"
    else
        test_failed "Monitoring namespace exists"
    fi
    
    # Test core services
    local core_services=("postgresql-primary" "redis-primary" "eureka-server" "api-gateway")
    for service in "${core_services[@]}"; do
        if kubectl get service "$service" -n alphintra >/dev/null 2>&1; then
            test_passed "Core service $service exists"
        else
            test_failed "Core service $service exists"
        fi
    done
}

# Test API Gateway routing
test_api_gateway() {
    log_info "Testing API Gateway Routing..."
    
    # Setup port forwarding for API Gateway
    kubectl port-forward -n alphintra svc/api-gateway 8080:8080 >/dev/null 2>&1 &
    local pf_pid=$!
    sleep 5
    
    # Test health endpoint
    http_test "API Gateway Health" "GET" "$API_GATEWAY_URL/health" "200"
    
    # Test actuator endpoints
    http_test "API Gateway Actuator Health" "GET" "$API_GATEWAY_URL/actuator/health" "200"
    http_test "API Gateway Metrics" "GET" "$API_GATEWAY_URL/actuator/metrics" "200"
    http_test "API Gateway Gateway Routes" "GET" "$API_GATEWAY_URL/actuator/gateway/routes" "200"
    
    # Clean up port forwarding
    kill $pf_pid 2>/dev/null || true
    sleep 2
}

# Test microservices health
test_microservices_health() {
    log_info "Testing Microservices Health..."
    
    local services=("trading-service" "risk-service" "user-service" "no-code-service" "strategy-service" "broker-service" "notification-service" "graphql-gateway")
    
    for service in "${services[@]}"; do
        # Port forward to service
        kubectl port-forward -n alphintra svc/"$service" 8080:8080 >/dev/null 2>&1 &
        local pf_pid=$!
        sleep 3
        
        # Test health endpoint
        http_test "$service Health" "GET" "http://localhost:8080/health" "200"
        
        # Clean up
        kill $pf_pid 2>/dev/null || true
        sleep 1
    done
}

# Test GraphQL API
test_graphql_api() {
    log_info "Testing GraphQL API..."
    
    # Setup port forwarding for GraphQL Gateway
    kubectl port-forward -n alphintra svc/graphql-gateway 8080:8080 >/dev/null 2>&1 &
    local pf_pid=$!
    sleep 5
    
    # Test introspection query
    graphql_test "Introspection" "query { __schema { types { name } } }" ".data.__schema.types"
    
    # Test users query
    graphql_test "Users Query" "query { users(limit: 5) { id username email } }" ".data.users"
    
    # Test strategies query
    graphql_test "Strategies Query" "query { strategies(isActive: true) { id name description } }" ".data.strategies"
    
    # Test workflows query
    graphql_test "Workflows Query" "query { workflows { id name description isActive } }" ".data.workflows"
    
    # Test market data query
    graphql_test "Market Data Query" "query { marketData(symbols: [\"AAPL\", \"GOOGL\"]) { symbol price change } }" ".data.marketData"
    
    # Clean up port forwarding
    kill $pf_pid 2>/dev/null || true
    sleep 2
}

# Test service discovery
test_service_discovery() {
    log_info "Testing Service Discovery..."
    
    # Port forward to Eureka server
    kubectl port-forward -n alphintra svc/eureka-server 8761:8761 >/dev/null 2>&1 &
    local pf_pid=$!
    sleep 5
    
    # Test Eureka dashboard
    http_test "Eureka Server Dashboard" "GET" "http://localhost:8761" "200"
    
    # Test Eureka apps endpoint
    http_test "Eureka Apps Endpoint" "GET" "http://localhost:8761/eureka/apps" "200"
    
    # Clean up
    kill $pf_pid 2>/dev/null || true
    sleep 2
}

# Test monitoring stack
test_monitoring() {
    log_info "Testing Monitoring Stack..."
    
    # Test Prometheus
    kubectl port-forward -n monitoring svc/prometheus 9090:9090 >/dev/null 2>&1 &
    local prometheus_pid=$!
    sleep 5
    
    http_test "Prometheus Targets" "GET" "http://localhost:9090/api/v1/targets" "200"
    http_test "Prometheus Metrics" "GET" "http://localhost:9090/api/v1/label/__name__/values" "200"
    
    kill $prometheus_pid 2>/dev/null || true
    sleep 2
    
    # Test Grafana
    kubectl port-forward -n monitoring svc/grafana 3000:3000 >/dev/null 2>&1 &
    local grafana_pid=$!
    sleep 5
    
    http_test "Grafana Health" "GET" "http://localhost:3000/api/health" "200"
    
    kill $grafana_pid 2>/dev/null || true
    sleep 2
    
    # Test Jaeger
    kubectl port-forward -n monitoring svc/jaeger-query 16686:16686 >/dev/null 2>&1 &
    local jaeger_pid=$!
    sleep 5
    
    http_test "Jaeger API" "GET" "http://localhost:16686/api/services" "200"
    
    kill $jaeger_pid 2>/dev/null || true
    sleep 2
}

# Test database connectivity
test_database_connectivity() {
    log_info "Testing Database Connectivity..."
    
    # Test PostgreSQL connectivity from within cluster
    if kubectl exec -n alphintra statefulset/postgresql -- psql -U postgres -c "SELECT version();" >/dev/null 2>&1; then
        test_passed "PostgreSQL connectivity"
    else
        test_failed "PostgreSQL connectivity"
    fi
    
    # Test Redis connectivity (if Redis is deployed)
    if kubectl get statefulset redis -n alphintra >/dev/null 2>&1; then
        if kubectl exec -n alphintra statefulset/redis -- redis-cli ping >/dev/null 2>&1; then
            test_passed "Redis connectivity"
        else
            test_failed "Redis connectivity"
        fi
    else
        log_warning "Redis not deployed, skipping Redis connectivity test"
    fi
}

# Test security features
test_security() {
    log_info "Testing Security Features..."
    
    # Test network policies exist
    if kubectl get networkpolicies -n alphintra >/dev/null 2>&1; then
        test_passed "Network policies configured"
    else
        test_failed "Network policies configured"
    fi
    
    # Test service accounts
    local service_accounts=("default" "prometheus")
    for sa in "${service_accounts[@]}"; do
        if kubectl get serviceaccount "$sa" -n alphintra >/dev/null 2>&1 || kubectl get serviceaccount "$sa" -n monitoring >/dev/null 2>&1; then
            test_passed "Service account $sa exists"
        else
            test_failed "Service account $sa exists"
        fi
    done
}

# Performance testing
test_performance() {
    log_info "Testing Performance..."
    
    # Setup port forwarding for load testing
    kubectl port-forward -n alphintra svc/api-gateway 8080:8080 >/dev/null 2>&1 &
    local pf_pid=$!
    sleep 5
    
    # Simple load test using curl
    log_test "Running basic load test..."
    local success_count=0
    local total_requests=50
    
    for i in $(seq 1 $total_requests); do
        if curl -s -o /dev/null -w "%{http_code}" "$API_GATEWAY_URL/health" | grep -q "200"; then
            ((success_count++))
        fi
    done
    
    local success_rate=$((success_count * 100 / total_requests))
    if [[ $success_rate -ge 95 ]]; then
        test_passed "Load test - Success rate: ${success_rate}% (${success_count}/${total_requests})"
    else
        test_failed "Load test - Success rate: ${success_rate}% (${success_count}/${total_requests}) - Below 95% threshold"
    fi
    
    # Clean up
    kill $pf_pid 2>/dev/null || true
    sleep 2
}

# Resource utilization check
test_resource_utilization() {
    log_info "Testing Resource Utilization..."
    
    # Check pod resource usage
    if kubectl top pods -n alphintra >/dev/null 2>&1; then
        test_passed "Pod metrics available"
        
        # Check for pods using excessive resources
        local high_cpu_pods
        high_cpu_pods=$(kubectl top pods -n alphintra --no-headers | awk '$2 > 500 {print $1}' | wc -l)
        
        if [[ $high_cpu_pods -eq 0 ]]; then
            test_passed "No pods with excessive CPU usage (>500m)"
        else
            test_warning "Found $high_cpu_pods pods with high CPU usage"
        fi
        
        local high_memory_pods
        high_memory_pods=$(kubectl top pods -n alphintra --no-headers | awk '$3 ~ /[0-9]+Gi/ && $3 > 1 {print $1}' | wc -l)
        
        if [[ $high_memory_pods -eq 0 ]]; then
            test_passed "No pods with excessive memory usage (>1Gi)"
        else
            test_warning "Found $high_memory_pods pods with high memory usage"
        fi
    else
        test_failed "Pod metrics not available - metrics server may not be running"
    fi
}

# Generate test report
generate_test_report() {
    log_info "Generating Test Report..."
    
    local report_file="$PROJECT_ROOT/test-results-$(date +%Y%m%d-%H%M%S).txt"
    
    cat > "$report_file" << EOF
=================================================
Alphintra Secure API Microservices Test Report
=================================================
Date: $(date)
Cluster: $CLUSTER_NAME
Total Tests: $TOTAL_TESTS
Passed: $PASSED_TESTS
Failed: $FAILED_TESTS
Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%

Test Results Summary:
- Infrastructure Health: $(if [[ $FAILED_TESTS -eq 0 ]]; then echo "PASS"; else echo "REVIEW NEEDED"; fi)
- API Gateway: $(if [[ $FAILED_TESTS -eq 0 ]]; then echo "PASS"; else echo "REVIEW NEEDED"; fi)
- Microservices: $(if [[ $FAILED_TESTS -eq 0 ]]; then echo "PASS"; else echo "REVIEW NEEDED"; fi)
- GraphQL API: $(if [[ $FAILED_TESTS -eq 0 ]]; then echo "PASS"; else echo "REVIEW NEEDED"; fi)
- Service Discovery: $(if [[ $FAILED_TESTS -eq 0 ]]; then echo "PASS"; else echo "REVIEW NEEDED"; fi)
- Monitoring: $(if [[ $FAILED_TESTS -eq 0 ]]; then echo "PASS"; else echo "REVIEW NEEDED"; fi)
- Database Connectivity: $(if [[ $FAILED_TESTS -eq 0 ]]; then echo "PASS"; else echo "REVIEW NEEDED"; fi)
- Security: $(if [[ $FAILED_TESTS -eq 0 ]]; then echo "PASS"; else echo "REVIEW NEEDED"; fi)
- Performance: $(if [[ $FAILED_TESTS -eq 0 ]]; then echo "PASS"; else echo "REVIEW NEEDED"; fi)

Services Tested:
$(kubectl get pods -n alphintra --no-headers | awk '{print "- " $1 ": " $3}')

Monitoring Services:
$(kubectl get pods -n monitoring --no-headers | awk '{print "- " $1 ": " $3}')

=================================================
EOF

    log_success "Test report generated: $report_file"
}

# Main execution
main() {
    log_info "Starting End-to-End Testing for Alphintra Secure API Microservices"
    echo "=================================================="
    
    # Verify cluster is accessible
    if ! kubectl cluster-info >/dev/null 2>&1; then
        log_error "Cannot connect to Kubernetes cluster. Please ensure cluster is running and kubectl is configured."
        exit 1
    fi
    
    # Wait for services to be ready
    wait_for_services
    
    # Run all test suites
    test_infrastructure
    test_api_gateway
    test_microservices_health
    test_graphql_api
    test_service_discovery
    test_monitoring
    test_database_connectivity
    test_security
    test_performance
    test_resource_utilization
    
    # Generate final report
    generate_test_report
    
    echo "=================================================="
    log_info "Testing Summary:"
    echo "  Total Tests: $TOTAL_TESTS"
    echo "  Passed: $PASSED_TESTS"
    echo "  Failed: $FAILED_TESTS"
    echo "  Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
    
    if [[ $FAILED_TESTS -eq 0 ]]; then
        log_success "🎉 All tests passed! The Alphintra Secure API Microservices Architecture is ready for production."
        exit 0
    else
        log_warning "⚠️  Some tests failed. Please review the issues before proceeding to production."
        exit 1
    fi
}

# Handle script arguments
case "${1:-all}" in
    "infrastructure")
        test_infrastructure
        ;;
    "gateway")
        test_api_gateway
        ;;
    "microservices")
        test_microservices_health
        ;;
    "graphql")
        test_graphql_api
        ;;
    "discovery")
        test_service_discovery
        ;;
    "monitoring")
        test_monitoring
        ;;
    "database")
        test_database_connectivity
        ;;
    "security")
        test_security
        ;;
    "performance")
        test_performance
        ;;
    "resources")
        test_resource_utilization
        ;;
    "all"|*)
        main
        ;;
esac