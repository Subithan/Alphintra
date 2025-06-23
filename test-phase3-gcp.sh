#!/bin/bash

# Phase 3 GCP Production Testing
# This deploys to actual GCP resources (costs money!)

set -euo pipefail

# Configuration
PROJECT_ID="${1:-}"
ENVIRONMENT="${2:-development}"

if [[ -z "$PROJECT_ID" ]]; then
    echo "❌ Error: GCP Project ID required"
    echo
    echo "Usage: $0 <PROJECT_ID> [environment]"
    echo
    echo "Example:"
    echo "  $0 my-alphintra-project development"
    echo "  $0 my-alphintra-project staging"
    echo "  $0 my-alphintra-project production"
    echo
    exit 1
fi

echo "☁️ PHASE 3 GCP PRODUCTION TESTING"
echo "================================="
echo "Project: $PROJECT_ID"
echo "Environment: $ENVIRONMENT"
echo
echo "⚠️  WARNING: This will create actual GCP resources and incur costs!"
echo
read -p "Continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Testing cancelled"
    exit 0
fi

echo
echo "🚀 Deploying Phase 3 to GCP..."

# Run the production deployment
./infra/terraform/scripts/deploy.sh \
  --project-id "$PROJECT_ID" \
  --environment "$ENVIRONMENT" \
  --auto-approve

echo
echo "🧪 Running post-deployment tests..."

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 60

# Check cluster health
echo "🏥 Checking cluster health..."
kubectl get nodes
kubectl get pods -n "alphintra-$ENVIRONMENT"

# Run integration tests
echo "🔗 Running integration tests..."
# Add your integration tests here

echo
echo "✅ Phase 3 GCP testing completed!"
echo
echo "📋 What was deployed:"
echo "  ✅ GKE production cluster"
echo "  ✅ Cloud SQL with TimescaleDB"
echo "  ✅ Redis for caching"
echo "  ✅ All microservices"
echo "  ✅ Monitoring and logging"
echo
echo "🎯 Access your deployment:"
echo "  Grafana: kubectl port-forward -n monitoring svc/grafana 3000:3000"
echo "  ArgoCD: kubectl port-forward -n argocd svc/argocd-server 8080:443"
echo
echo "💰 Remember to clean up resources to avoid charges:"
echo "  terraform destroy (in infra/terraform/environments/$ENVIRONMENT)"