#!/bin/bash

# Cloud SQL Database Setup Script for No-Code Service
# Creates database and user for the Alphintra No-Code Service

set -e  # Exit on any error

# Configuration
PROJECT_ID="alphintra-472817"
INSTANCE_NAME="alphintra-db-instance"
REGION="us-central1"
DATABASE_NAME="alphintra_nocode_service"
DB_USER="nocode_service_user"
DB_PASSWORD="alphintra@123"  # As specified in requirements

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  INFO: $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ SUCCESS: $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

log_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
}

# Check if gcloud is installed and authenticated
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Please install Google Cloud SDK."
        exit 1
    fi

    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
        log_error "Not authenticated with gcloud. Please run 'gcloud auth login'."
        exit 1
    fi

    # Set the project
    gcloud config set project "$PROJECT_ID"
    log_success "Prerequisites check completed"
}

# Check if Cloud SQL instance exists
check_cloudsql_instance() {
    log_info "Checking Cloud SQL instance existence..."

    if gcloud sql instances describe "$INSTANCE_NAME" --project="$PROJECT_ID" &> /dev/null; then
        log_success "Cloud SQL instance '$INSTANCE_NAME' exists"
        return 0
    else
        log_warning "Cloud SQL instance '$INSTANCE_NAME' does not exist"
        return 1
    fi
}

# Create Cloud SQL instance if it doesn't exist
create_cloudsql_instance() {
    log_info "Creating Cloud SQL instance '$INSTANCE_NAME'..."

    gcloud sql instances create "$INSTANCE_NAME" \
        --project="$PROJECT_ID" \
        --database-version=POSTGRES_14 \
        --region="$REGION" \
        --tier=db-g1-small \
        --storage-size=20GB \
        --storage-type=SSD \
        --backup-start-time=02:00 \
        --retained-backups-count=7 \
        --retained-transaction-log-days=7 \
        --deletion-protection \
        --enable-bin-log \
        --availability-type=ZONAL

    log_success "Cloud SQL instance creation initiated. This may take a few minutes..."

    # Wait for instance to be ready
    log_info "Waiting for instance to become ready..."
    gcloud sql instances wait "$INSTANCE_NAME" --project="$PROJECT_ID" --timeout=600s

    log_success "Cloud SQL instance is ready"
}

# Get instance connection details
get_instance_connection() {
    log_info "Getting instance connection details..."

    # Get connection name
    CONNECTION_NAME=$(gcloud sql instances describe "$INSTANCE_NAME" \
        --project="$PROJECT_ID" \
        --format="value(connectionName)")

    # Get public IP (if exists)
    PUBLIC_IP=$(gcloud sql instances describe "$INSTANCE_NAME" \
        --project="$PROJECT_ID" \
        --format="value(ipAddresses.ipAddress)" \
        --filter="type=PRIMARY" || echo "")

    log_info "Connection name: $CONNECTION_NAME"
    if [[ -n "$PUBLIC_IP" ]]; then
        log_info "Public IP: $PUBLIC_IP"
    fi
}

# Create database
create_database() {
    log_info "Creating database '$DATABASE_NAME'..."

    if gcloud sql databases describe "$DATABASE_NAME" \
        --instance="$INSTANCE_NAME" \
        --project="$PROJECT_ID" &> /dev/null; then
        log_warning "Database '$DATABASE_NAME' already exists"
        return 0
    fi

    gcloud sql databases create "$DATABASE_NAME" \
        --instance="$INSTANCE_NAME" \
        --project="$PROJECT_ID"

    log_success "Database '$DATABASE_NAME' created successfully"
}

# Create database user
create_database_user() {
    log_info "Creating database user '$DB_USER'..."

    if gcloud sql users describe "$DB_USER" \
        --instance="$INSTANCE_NAME" \
        --project="$PROJECT_ID" &> /dev/null; then
        log_warning "User '$DB_USER' already exists. Updating password..."
        gcloud sql users set-password "$DB_USER" \
            --instance="$INSTANCE_NAME" \
            --project="$PROJECT_ID" \
            --password="$DB_PASSWORD"
    else
        gcloud sql users create "$DB_USER" \
            --instance="$INSTANCE_NAME" \
            --project="$PROJECT_ID" \
            --password="$DB_PASSWORD"
    fi

    log_success "Database user '$DB_USER' created/updated successfully"
}

# Grant permissions to user
grant_permissions() {
    log_info "Granting permissions to user '$DB_USER'..."

    # Connect to database and grant permissions
    gcloud sql connect "$INSTANCE_NAME" \
        --project="$PROJECT_ID" \
        --user=postgres \
        --quiet <<EOF
-- Connect to the target database
\c $DATABASE_NAME;

-- Grant all privileges on the database to the user
GRANT ALL PRIVILEGES ON DATABASE $DATABASE_NAME TO $DB_USER;

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO $DB_USER;

-- Grant all privileges on current and future tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;

EOF

    log_success "Permissions granted successfully"
}

# Test database connection
test_connection() {
    log_info "Testing database connection..."

    # Try to connect using the new user
    if gcloud sql connect "$INSTANCE_NAME" \
        --project="$PROJECT_ID" \
        --user="$DB_USER" \
        --database="$DATABASE_NAME" \
        --quiet \
        --command="SELECT current_database(), current_user;" &> /dev/null; then
        log_success "Database connection test passed"
    else
        log_error "Database connection test failed"
        exit 1
    fi
}

# Generate connection string
generate_connection_string() {
    log_info "Generating connection string..."

    CONNECTION_NAME=$(gcloud sql instances describe "$INSTANCE_NAME" \
        --project="$PROJECT_ID" \
        --format="value(connectionName)")

    # Generate Cloud SQL Proxy connection string
    CLOUDSQL_CONN_STR="postgresql+pg8000://${DB_USER}:${DB_PASSWORD}@localhost/${DATABASE_NAME}?unix_sock=/cloudsql/${CONNECTION_NAME}/.s.PGSQL.5432"

    # Generate TCP connection string (if public IP exists)
    if [[ -n "$PUBLIC_IP" ]]; then
        TCP_CONN_STR="postgresql+pg8000://${DB_USER}:${DB_PASSWORD}@${PUBLIC_IP}:5432/${DATABASE_NAME}"
    else
        TCP_CONN_STR="No public IP available"
    fi

    echo
    log_success "Connection Strings:"
    echo "Cloud SQL Proxy: $CLOUDSQL_CONN_STR"
    echo "TCP Connection:   $TCP_CONN_STR"
    echo
}

# Configure firewall rules (if public IP)
configure_firewall() {
    if [[ -n "$PUBLIC_IP" ]]; then
        log_info "Configuring authorized networks for public access..."

        # Add current IP to authorized networks (optional, for development)
        CURRENT_IP=$(curl -s ifconfig.me || echo "0.0.0.0")

        log_warning "Consider adding your current IP ($CURRENT_IP) to authorized networks for development access"
        log_info "To add authorized network, run:"
        echo "gcloud sql instances patch $INSTANCE_NAME --authorized-networks=$CURRENT_IP/32 --project=$PROJECT_ID"
    fi
}

# Main function
main() {
    echo "🚀 Cloud SQL Database Setup for Alphintra No-Code Service"
    echo "========================================================"
    echo

    # Check prerequisites
    check_prerequisites
    echo

    # Check if instance exists, create if needed
    if ! check_cloudsql_instance; then
        create_cloudsql_instance
        echo
    fi

    # Get connection details
    get_instance_connection
    echo

    # Create database
    create_database
    echo

    # Create user
    create_database_user
    echo

    # Grant permissions
    grant_permissions
    echo

    # Test connection
    test_connection
    echo

    # Generate connection string
    generate_connection_string
    echo

    # Configure firewall (if applicable)
    configure_firewall
    echo

    log_success "Cloud SQL database setup completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Update your application configuration with the connection string above"
    echo "2. Set up Cloud SQL Proxy in your Kubernetes deployment"
    echo "3. Deploy your no-code service"
    echo
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [--test]"
        echo
        echo "Options:"
        echo "  --test    Test database connection only"
        echo "  --help    Show this help message"
        exit 0
        ;;
    --test)
        log_info "Testing existing database connection..."
        if check_cloudsql_instance; then
            get_instance_connection
            test_connection
            generate_connection_string
        else
            log_error "Cloud SQL instance not found"
            exit 1
        fi
        exit 0
        ;;
esac

# Run main function
main "$@"