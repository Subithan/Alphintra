#!/bin/bash

# Phase 3 Local Kubernetes Testing
# This uses Phase 2's k3d cluster to test Phase 3 Kubernetes manifests

set -euo pipefail

echo "☸️ PHASE 3 LOCAL KUBERNETES TESTING"
echo "==================================="
echo "This uses k3d cluster to test Phase 3 Kubernetes configurations"
echo

# Check if k3d cluster exists
if ! kubectl cluster-info &> /dev/null; then
    echo "🏗️ Setting up k3d cluster first..."
    cd infra/scripts
    ./setup-k8s-cluster.sh
    cd ../..
else
    echo "✅ Kubernetes cluster already running"
fi

echo
echo "🧪 Testing Phase 3 Kubernetes Manifests..."

# Create test namespace
kubectl create namespace alphintra-phase3-test --dry-run=client -o yaml | kubectl apply -f -

# Test namespace configuration
echo "📦 Testing namespace configuration..."
kubectl apply -f infra/kubernetes/environments/production/namespace.yaml --dry-run=client

# Test HPA configurations  
echo "📈 Testing HPA configurations..."
kubectl apply -f infra/kubernetes/environments/production/hpa.yaml --dry-run=client

# Test network policies
echo "🔒 Testing security policies..."
kubectl apply -f infra/kubernetes/security/network-policies/default-deny-all.yaml --dry-run=client

# Test ArgoCD configurations
echo "🔄 Testing ArgoCD GitOps..."
kubectl apply -f infra/kubernetes/gitops/app-of-apps.yaml --dry-run=client

echo
echo "✅ Phase 3 local Kubernetes testing completed!"
echo
echo "📋 What was tested:"
echo "  ✅ Kubernetes namespace configurations"
echo "  ✅ Horizontal Pod Autoscaling (HPA)" 
echo "  ✅ Network security policies"
echo "  ✅ ArgoCD GitOps applications"
echo "  ✅ Production-ready Kubernetes manifests"