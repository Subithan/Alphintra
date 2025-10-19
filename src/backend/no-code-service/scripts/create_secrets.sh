#!/bin/bash

# Create Kubernetes secrets for no-code service deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="alphintra-472817"
INSTANCE_NAME="alphintra-db-instance"
DATABASE_NAME="alphintra_nocode_service"
DB_USER="nocode_service_user"
DB_PASSWORD="alphintra@123"

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  INFO: $1${NC}" >&2
}

log_success() {
    echo -e "${GREEN}✅ SUCCESS: $1${NC}" >&2
}

log_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}" >&2
}

log_error() {
    echo -e "${RED}❌ ERROR: $1${NC}" >&2
}

# Get Cloud SQL connection details
get_cloudsql_connection() {
    log_info "Getting Cloud SQL connection details..."

    CONNECTION_NAME=$(gcloud sql instances describe "$INSTANCE_NAME" \
        --project="$PROJECT_ID" \
        --format="value(connectionName)")

    if [[ -z "$CONNECTION_NAME" ]]; then
        log_error "Could not get Cloud SQL connection name. Make sure instance '$INSTANCE_NAME' exists."
        exit 1
    fi

    log_success "Connection name: $CONNECTION_NAME"
    echo "$CONNECTION_NAME"
}

# Create no-code service secrets
create_nocode_service_secrets() {
    log_info "Creating Kubernetes secrets for no-code service..."

    CONNECTION_NAME=$(get_cloudsql_connection)

    # URL-encode password and use TCP via local proxy
    DB_PASSWORD_ENC=$(python3 - <<'PY'
import urllib.parse, os
print(urllib.parse.quote(os.environ.get('DB_PASSWORD',''), safe=''))
PY
)
    DATABASE_URL="postgresql+pg8000://${DB_USER}:${DB_PASSWORD_ENC}@127.0.0.1:5432/${DATABASE_NAME}"

    # Create the secrets
    kubectl create secret generic no-code-service-secrets \
        --namespace=alphintra \
        --from-literal=database-url="$DATABASE_URL" \
        --from-literal=cloud-sql-connection-name="$CONNECTION_NAME" \
        --dry-run=client -o yaml | kubectl apply -f -

    log_success "Created no-code-service-secrets secret"
}

# Create Cloud SQL service account secret
create_cloudsql_sa_secret() {
    log_info "Creating Cloud SQL service account secret..."

    # This assumes you have a service account JSON file
    # In production, you should use Workload Identity instead
    if [[ -f "service-account.json" ]]; then
        kubectl create secret generic cloudsql-sa-secret \
            --namespace=alphintra \
            --from-file=service-account.json=service-account.json \
            --dry-run=client -o yaml | kubectl apply -f -

        log_success "Created cloudsql-sa-secret secret"
    else
        log_warning "service-account.json file not found. You will need to create the cloudsql-sa-secret manually."
        log_info "Use: kubectl create secret generic cloudsql-sa-secret --from-file=service-account.json=your-sa-file.json -n alphintra"
    fi
}

# Verify secrets
verify_secrets() {
    log_info "Verifying created secrets..."

    if kubectl get secret no-code-service-secrets -n alphintra &> /dev/null; then
        log_success "✅ no-code-service-secrets secret exists"

        # Show secret keys (without values)
        log_info "Secret keys:"
        kubectl get secret no-code-service-secrets -n alphintra -o jsonpath='{.data.keys[*}' | tr ' ' '\n'
    else
        log_error "❌ no-code-service-secrets secret not found"
        return 1
    fi

    if kubectl get secret cloudsql-sa-secret -n alphintra &> /dev/null; then
        log_success "✅ cloudsql-sa-secret secret exists"
    else
        log_warning "⚠️  cloudsql-sa-secret secret not found (optional for Workload Identity)"
    fi
}

# Main function
main() {
    echo "🔐 Creating Kubernetes Secrets for No-Code Service"
    echo "==================================================="
    echo

    # Check kubectl context
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Check your kubectl configuration."
        exit 1
    fi

    # Create secrets
    create_nocode_service_secrets
    echo

    create_cloudsql_sa_secret
    echo

    # Verify secrets
    verify_secrets
    echo

    log_success "Kubernetes secrets creation completed!"
    echo
    echo "Next steps:"
    echo "1. Ensure the Cloud SQL service account has the 'Cloud SQL Client' role"
    echo "2. Deploy the service using: kubectl apply -k dev"
    echo "3. Monitor deployment with: kubectl logs -f deployment/no-code-service -n alphintra"
    echo
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [--verify]"
        echo
        echo "Options:"
        echo "  --verify  Only verify existing secrets"
        echo "  --help    Show this help message"
        exit 0
        ;;
    --verify)
        log_info "Verifying existing secrets..."
        verify_secrets
        exit 0
        ;;
esac

# Run main function
main "$@"
