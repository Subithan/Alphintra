#!/bin/bash
#
# Optimized Wallet Service Build Script for Cloud Build
# This script triggers an optimized build for the wallet service.
# It is designed to be run from within the 'wallet-service' directory.
#
# Usage:
#   ./build.sh                    # Run optimized build
#   ./build.sh --setup-db         # Setup database before building
#   ./build.sh --setup-python-cache # Setup Python cache bucket first
#   ./build.sh --dry-run          # Show build configuration without executing
#   ./build.sh --help             # Show usage information
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="alphintra-472817"
REGION="us-central1"
INSTANCE_NAME="alphintra-db-instance"
DATABASE_NAME="alphintra_wallet_service"
CACHE_BUCKET="${PROJECT_ID}-python-cache"

# Function to print colored output
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to show usage
show_usage() {
    cat << EOF
Optimized Wallet Service Build Script

USAGE:
    ./build.sh [OPTIONS]

OPTIONS:
    --setup-db           Setup Cloud SQL database before building
    --setup-python-cache Setup Python cache bucket before building
    --dry-run            Show build configuration without executing
    --help               Show this help message

EXAMPLES:
    ./build.sh                           # Optimized build with cache
    ./build.sh --setup-db                # Setup database then build
    ./build.sh --setup-python-cache      # Setup cache bucket then build

BUILD TARGETS:
    Optimized:  ~2-3 minutes (60-80% faster than traditional builds)

REQUIREMENTS:
    - gcloud CLI installed and authenticated
    - Cloud Build API enabled
    - Appropriate IAM permissions
    - Database setup (run with --setup-db if needed)

FEATURES:
    - Python dependency caching
    - Parallel test and Docker execution
    - Database auto-initialization
    - Fast Kubernetes deployment
    - Cloud SQL integration

EOF
}

# Function to setup database
setup_database() {
    print_status "Setting up Wallet Service database..."

    if [ ! -f "../../../infra/scripts/setup-wallet-service-db.sh" ]; then
        print_error "Database setup script not found at ../../../infra/scripts/setup-wallet-service-db.sh"
        exit 1
    fi

    bash ../../../infra/scripts/setup-wallet-service-db.sh
    print_success "Database setup completed"
}

# Function to setup Python cache bucket
setup_python_cache() {
    print_status "Setting up Python cache bucket..."

    if [ ! -f "../../../infra/scripts/setup-python-cache.sh" ]; then
        print_error "Python cache setup script not found at ../../../infra/scripts/setup-python-cache.sh"
        exit 1
    fi

    bash ../../../infra/scripts/setup-python-cache.sh
    print_success "Python cache bucket setup completed"
}

# Function to check database status
check_database_status() {
    print_status "Checking Cloud SQL database status..."

    if gcloud sql databases list --instance="$INSTANCE_NAME" --filter="name:$DATABASE_NAME" --format="value(name)" | grep -q "$DATABASE_NAME"; then
        print_success "Database '$DATABASE_NAME' exists and is accessible"
    else
        print_warning "Database '$DATABASE_NAME' not found - run with --setup-db to create it"
    fi
}

# Function to check cache bucket status
check_cache_status() {
    print_status "Checking Python cache bucket status..."

    if gsutil ls -b "gs://$CACHE_BUCKET" &> /dev/null; then
        CACHE_SIZE=$(gsutil du -sh "gs://$CACHE_BUCKET" 2>/dev/null | cut -f1 || echo "0")
        CACHE_OBJECTS=$(gsutil ls "gs://$CACHE_BUCKET" 2>/dev/null | wc -l)
        print_success "Cache bucket accessible: $CACHE_OBJECTS objects, $CACHE_SIZE total"
    else
        print_warning "Cache bucket not found - run with --setup-python-cache to create it"
    fi
}

# Function to run build
run_build() {
    local build_config="cloudbuild-optimized-hybrid.yaml"
    local description="Optimized Wallet Service Build (with Python caching and database integration)"
    
    # Get current git commit SHA (short version)
    local commit_sha=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")

    print_status "Starting $description..."
    print_status "Using build configuration: $build_config"
    print_status "Using commit SHA: $commit_sha"

    # Check if build config exists
    if [ ! -f "$build_config" ]; then
        print_error "Build configuration not found: $build_config"
        exit 1
    fi

    # Show build start time
    local start_time=$(date '+%Y-%m-%d %H:%M:%S')
    print_status "Build started at: $start_time"

    # Trigger the build
    if [ "$DRY_RUN" = "true" ]; then
        print_status "DRY RUN: Would execute: gcloud builds submit --config $build_config --substitutions=_COMMIT_SHA=$commit_sha . --verbosity=info"
        return 0
    fi

    gcloud builds submit --config "$build_config" --substitutions="_COMMIT_SHA=$commit_sha" . --verbosity=info

    # Show build completion time
    local end_time=$(date '+%Y-%m-%d %H:%M:%S')
    print_success "Build completed at: $end_time"
}

# Main script logic
DRY_RUN="false"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --setup-db)
            setup_database
            shift
            ;;
        --setup-python-cache)
            setup_python_cache
            shift
            ;;
        --dry-run)
            DRY_RUN="true"
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate we're in the correct directory
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found. Please run this script from the wallet-service directory."
    exit 1
fi

# Check gcloud authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    print_error "gcloud not authenticated. Please run: gcloud auth login"
    exit 1
fi

# Check current project
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [[ "$CURRENT_PROJECT" != "$PROJECT_ID" ]]; then
    print_status "Switching to project: $PROJECT_ID"
    gcloud config set project "$PROJECT_ID"
fi

# Show build information
echo ""
echo "🚀 Wallet Service Cloud Build Script"
echo "==================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Configuration: cloudbuild-optimized-hybrid.yaml"
echo "Database: $DATABASE_NAME"
echo "Cache Bucket: $CACHE_BUCKET"
echo ""

# Check database and cache status
check_database_status
check_cache_status

# Run the build
run_build

# Show success message
echo ""
print_success "Wallet Service build completed successfully!"
echo ""
echo "📊 Build Performance:"
echo "  - Optimized build: ~2-3 minutes (60-80% faster)"
echo "  - Python dependency caching enabled"
echo "  - Parallel test and Docker execution"
echo "  - Database auto-initialization on first startup"
echo ""
echo "🔍 Monitor your build at:"
echo "  https://console.cloud.google.com/cloud-build/builds"
echo ""
echo "🚀 To check deployment status:"
echo "  kubectl get pods -n alphintra -l app=wallet-service"
echo ""
echo "🔧 To verify service health:"
echo "  kubectl port-forward -n alphintra svc/wallet-service 8011:8011"
echo "  curl http://localhost:8011/health"
echo ""
echo "💡 To verify database initialization:"
echo "  kubectl logs -n alphintra deployment/wallet-service"
echo ""
echo "🔗 Available Endpoints:"
echo "  - Health: http://wallet-service:8011/health"
echo "  - Root: http://wallet-service:8011/"
echo "  - Binance Connect: http://wallet-service:8011/binance/connect"
echo ""
echo "📊 Database Connection Info:"
echo "  Host: $INSTANCE_NAME"
echo "  Database: $DATABASE_NAME"
echo "  User: wallet_service"
echo "  Tables: users, wallet_connections"
echo ""