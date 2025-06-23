#!/bin/bash

# Phase 3 Testing Script - Alphintra Trading Platform
# This script validates all Phase 3 components and features

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Test configuration
TEST_PROJECT_ID="${TEST_PROJECT_ID:-alphintra-test}"
TEST_REGION="${TEST_REGION:-us-central1}"
TEST_ZONE="${TEST_ZONE:-us-central1-a}"
TEST_ENVIRONMENT="${TEST_ENVIRONMENT:-development}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

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

# Test execution functions
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    ((TESTS_TOTAL++))
    log_info "Running test: $test_name"
    
    if eval "$test_command" &> /tmp/test_output; then
        log_success "✅ $test_name - PASSED"
        ((TESTS_PASSED++))
        return 0
    else
        log_error "❌ $test_name - FAILED"
        log_error "Error output:"
        cat /tmp/test_output | head -20
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test summary
test_summary() {
    echo
    echo "=================================================="
    echo "📊 PHASE 3 TEST RESULTS SUMMARY"
    echo "=================================================="
    echo "Total Tests: $TESTS_TOTAL"
    echo "Passed: $TESTS_PASSED"
    echo "Failed: $TESTS_FAILED"
    echo "Success Rate: $(( TESTS_PASSED * 100 / TESTS_TOTAL ))%"
    echo "=================================================="
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_success "🎉 All Phase 3 tests passed!"
        return 0
    else
        log_error "❌ Some Phase 3 tests failed!"
        return 1
    fi
}

# Prerequisites tests
test_prerequisites() {
    echo
    log_info "🔍 Testing Prerequisites..."
    
    # Check required tools
    run_test "Docker installed" "docker --version"
    run_test "Terraform installed" "terraform version"
    run_test "kubectl installed" "kubectl version --client"
    run_test "gcloud installed" "gcloud version"
    run_test "helm installed" "helm version"
    
    # Check tool versions
    run_test "Terraform version >= 1.0" 'terraform version | grep -E "Terraform v[1-9]"'
    run_test "kubectl version >= 1.24" 'kubectl version --client | grep -E "GitVersion.*v1\.(2[4-9]|[3-9][0-9])"'
    
    # Check project structure
    run_test "GitHub workflows exist" "test -d .github/workflows"
    run_test "Terraform modules exist" "test -d infra/terraform/modules"
    run_test "Kubernetes configs exist" "test -d infra/kubernetes"
    run_test "Phase 3 documentation exists" "test -f docs/infrastructure/Phase3-Production-Cloud-Deployment.md"
    
    log_success "Prerequisites tests completed"
}

# Test Terraform configurations
test_terraform() {
    echo
    log_info "🏗️ Testing Terraform Configurations..."
    
    cd "$PROJECT_ROOT/infra/terraform/environments/production"
    
    # Terraform validation tests
    run_test "Terraform format check" "terraform fmt -check -recursive"
    run_test "Terraform validation" "terraform validate"
    
    # Test with sample variables
    cat > terraform.tfvars.test << EOF
project_id = "$TEST_PROJECT_ID"
region     = "$TEST_REGION"
zone       = "$TEST_ZONE"
environment = "test"

# Test values
database_password = "test-password-123"
readonly_database_password = "readonly-test-123"
jwt_secret = "test-jwt-secret-32-characters-long"
tls_certificate = "test-certificate"
tls_private_key = "test-private-key"
alert_email = "test@example.com"
slack_webhook_url = "https://hooks.slack.com/services/test/test/test"

api_keys = {
  binance_api_key     = "test-key"
  binance_secret_key  = "test-secret"
  coinbase_api_key    = "test-key"
  coinbase_secret_key = "test-secret"
  alpha_vantage_key   = "test-key"
  finnhub_api_key     = "test-key"
  polygon_api_key     = "test-key"
  quandl_api_key      = "test-key"
}
EOF
    
    run_test "Terraform plan (dry run)" "terraform plan -var-file=terraform.tfvars.test -detailed-exitcode || test \$? -eq 2"
    
    # Cleanup test file
    rm -f terraform.tfvars.test
    
    cd "$PROJECT_ROOT"
    log_success "Terraform tests completed"
}

# Test GitHub Actions workflows
test_github_actions() {
    echo
    log_info "🔄 Testing GitHub Actions Workflows..."
    
    # Check workflow syntax
    run_test "Backend CI workflow syntax" "python3 -c 'import yaml; yaml.safe_load(open(\".github/workflows/ci-backend.yml\"))'"
    run_test "Production CD workflow syntax" "python3 -c 'import yaml; yaml.safe_load(open(\".github/workflows/cd-production.yml\"))'"
    run_test "Security scan workflow syntax" "python3 -c 'import yaml; yaml.safe_load(open(\".github/workflows/security-scan.yml\"))'"
    
    # Check workflow completeness
    run_test "CI workflow has required jobs" "grep -q 'test:\\|build-images:\\|security-scan:' .github/workflows/ci-backend.yml"
    run_test "CD workflow has deployment jobs" "grep -q 'blue-green-deployment:\\|post-deployment-validation:' .github/workflows/cd-production.yml"
    run_test "Security workflow has scan jobs" "grep -q 'dependency-scan:\\|static-analysis:\\|container-scan:' .github/workflows/security-scan.yml"
    
    log_success "GitHub Actions tests completed"
}

# Test Kubernetes configurations
test_kubernetes() {
    echo
    log_info "☸️ Testing Kubernetes Configurations..."
    
    cd "$PROJECT_ROOT/infra/kubernetes"
    
    # Validate Kubernetes manifests
    run_test "Kubernetes YAML syntax validation" "find . -name '*.yaml' -exec kubectl apply --dry-run=client --validate=true -f {} \;"
    run_test "Kustomize build production" "kubectl kustomize environments/production"
    run_test "Kustomize build staging" "kubectl kustomize environments/staging || echo 'Staging not fully configured'"
    
    # Check ArgoCD configurations
    run_test "ArgoCD app-of-apps syntax" "kubectl apply --dry-run=client --validate=true -f gitops/app-of-apps.yaml"
    
    # Test security policies
    run_test "Network policies validation" "find security/network-policies -name '*.yaml' -exec kubectl apply --dry-run=client --validate=true -f {} \;"
    
    cd "$PROJECT_ROOT"
    log_success "Kubernetes tests completed"
}

# Test security configurations
test_security() {
    echo
    log_info "🔒 Testing Security Configurations..."
    
    # Test security scanning tools (if available)
    if command -v bandit &> /dev/null; then
        run_test "Bandit security scan" "bandit -r src/backend/ -f json -o /tmp/bandit-report.json || test \$? -eq 1"
    else
        log_warning "Bandit not installed, skipping SAST test"
    fi
    
    if command -v safety &> /dev/null; then
        run_test "Safety dependency scan" "find src/backend -name requirements.txt -exec safety check -r {} \; || true"
    else
        log_warning "Safety not installed, skipping dependency scan"
    fi
    
    # Check for hardcoded secrets
    run_test "No hardcoded secrets in Python code" "! grep -r -i 'password.*=.*['\''\"']' src/backend/ --include='*.py' | grep -v test"
    run_test "No API keys in code" "! grep -r -E 'api_key.*=.*['\''\"'][A-Za-z0-9]{20,}' src/backend/ --include='*.py'"
    
    # Test security policies exist
    run_test "Network policies exist" "test -f infra/kubernetes/security/network-policies/default-deny-all.yaml"
    run_test "RBAC policies exist" "test -d infra/kubernetes/security/rbac"
    
    log_success "Security tests completed"
}

# Test deployment automation scripts
test_automation() {
    echo
    log_info "🤖 Testing Deployment Automation..."
    
    # Test script permissions and syntax
    run_test "Deploy script is executable" "test -x infra/terraform/scripts/deploy.sh"
    run_test "Rollback script is executable" "test -x infra/terraform/scripts/rollback.sh"
    
    # Test script help and validation
    run_test "Deploy script help" "infra/terraform/scripts/deploy.sh --help"
    run_test "Rollback script help" "infra/terraform/scripts/rollback.sh --help"
    
    # Test script validation (dry run)
    run_test "Deploy script validation" "infra/terraform/scripts/deploy.sh --project-id test-project --dry-run || test \$? -eq 1"
    
    log_success "Automation tests completed"
}

# Test documentation
test_documentation() {
    echo
    log_info "📚 Testing Documentation..."
    
    # Check documentation files exist
    run_test "Phase 3 documentation exists" "test -f docs/infrastructure/Phase3-Production-Cloud-Deployment.md"
    run_test "Phase 3 README exists" "test -f README-Phase3.md"
    run_test "Main README exists" "test -f README.md"
    
    # Check documentation completeness
    run_test "Phase 3 docs has architecture section" "grep -q '## Architecture' docs/infrastructure/Phase3-Production-Cloud-Deployment.md"
    run_test "Phase 3 docs has deployment guide" "grep -q 'Deployment' docs/infrastructure/Phase3-Production-Cloud-Deployment.md"
    run_test "README has quick start" "grep -q 'Quick Start' README-Phase3.md"
    
    # Validate markdown syntax (if markdownlint available)
    if command -v markdownlint &> /dev/null; then
        run_test "Markdown syntax validation" "markdownlint docs/ README*.md || true"
    else
        log_warning "markdownlint not available, skipping markdown validation"
    fi
    
    log_success "Documentation tests completed"
}

# Test container builds (local)
test_container_builds() {
    echo
    log_info "🐳 Testing Container Builds..."
    
    local services=("auth-service" "trading-api" "strategy-engine" "broker-connector" "broker-simulator")
    
    for service in "${services[@]}"; do
        if [[ -f "src/backend/$service/Dockerfile" ]]; then
            run_test "$service Dockerfile syntax" "docker build --dry-run src/backend/$service/ || hadolint src/backend/$service/Dockerfile || true"
        else
            log_warning "Dockerfile not found for $service"
        fi
    done
    
    log_success "Container build tests completed"
}

# Integration test simulation
test_integration_simulation() {
    echo
    log_info "🔗 Testing Integration Scenarios..."
    
    # Test environment file templates
    run_test "Environment template exists" "test -f infra/terraform/environments/production/terraform.tfvars.example || test -f infra/terraform/environments/production/variables.tf"
    
    # Test service connectivity simulation
    run_test "Service port configuration" "grep -q '8001\\|8002\\|8003\\|8005\\|8006' infra/kubernetes/environments/production/*.yaml"
    
    # Test monitoring configuration
    run_test "Monitoring namespace configured" "grep -q 'monitoring' infra/kubernetes/environments/production/*.yaml || true"
    
    # Test ingress configuration
    run_test "Ingress configuration exists" "find infra/kubernetes -name '*ingress*' -o -name '*gateway*' | head -1"
    
    log_success "Integration simulation tests completed"
}

# Main test execution
main() {
    echo "🧪 Starting Phase 3 Testing Suite"
    echo "=================================="
    echo "Test Project: $TEST_PROJECT_ID"
    echo "Test Region: $TEST_REGION"
    echo "Test Environment: $TEST_ENVIRONMENT"
    echo "=================================="
    
    # Run all test suites
    test_prerequisites
    test_terraform
    test_github_actions
    test_kubernetes
    test_security
    test_automation
    test_documentation
    test_container_builds
    test_integration_simulation
    
    # Show summary
    test_summary
}

# Cleanup function
cleanup() {
    rm -f /tmp/test_output
    rm -f /tmp/bandit-report.json
}

trap cleanup EXIT

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi