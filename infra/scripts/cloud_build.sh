#!/bin/bash

# Cloud Build Script for Alphintra Services
# Usage: ./cloud_build.sh [service-name]
# Services: no-code-service, auth-service, service-gateway, frontend

set -e

# Get the current commit SHA
COMMIT_SHA=$(git rev-parse HEAD)
PROJECT_ID="alphintra-472817"

# Function to display usage
usage() {
    echo "Usage: $0 [service-name]"
    echo "Services:"
    echo "  no-code-service"
    echo "  auth-service"
    echo "  service-gateway"
    echo "  frontend"
    echo ""
    echo "Example: $0 auth-service"
    exit 1
}

# Check if service name is provided
if [ $# -eq 0 ]; then
    usage
fi

SERVICE_NAME=$1

# Function to build and deploy a service
build_service() {
    local service=$1
    local config_path=$2
    
    echo "========================================="
    echo "Building and deploying $service..."
    echo "========================================="
    
    # Execute gcloud builds submit command
    gcloud builds submit \
        --config "$config_path" \
        --substitutions="_COMMIT_SHA=$COMMIT_SHA,_SERVICE_NAME=$service" \
        --project "$PROJECT_ID"
    
    echo "✅ $service deployed successfully!"
}

# Determine the service and its cloudbuild.yaml path
case $SERVICE_NAME in
    "no-code-service")
        build_service "$SERVICE_NAME" "src/backend/no-code-service/cloudbuild.yaml"
        ;;
    "auth-service")
        build_service "$SERVICE_NAME" "src/backend/auth-service/cloudbuild.yaml"
        ;;
    "service-gateway")
        build_service "$SERVICE_NAME" "src/backend/service-gateway/cloudbuild.yaml"
        ;;
    "frontend")
        echo "========================================="
        echo "Building and deploying frontend..."
        echo "========================================="
        
        # Frontend uses _BUILD_TAG instead of _COMMIT_SHA
        gcloud builds submit \
            --config "src/frontend/cloudbuild.yaml" \
            --substitutions="_BUILD_TAG=$COMMIT_SHA" \
            --project "$PROJECT_ID"
        
        echo "✅ Frontend deployed successfully!"
        ;;
    *)
        echo "Error: Unknown service '$SERVICE_NAME'"
        usage
        ;;
esac

echo ""
echo "========================================="
echo "All operations completed successfully!"
echo "========================================="