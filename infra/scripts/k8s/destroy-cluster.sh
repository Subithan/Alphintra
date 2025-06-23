#!/bin/bash

# k3d Cluster Destruction Script for Alphintra Trading Platform
# This script safely destroys the k3d cluster and associated resources

set -e

CLUSTER_NAME="alphintra-cluster"
REGISTRY_NAME="alphintra-registry"

echo "🗑️  Destroying Alphintra k3d cluster and resources..."

# Delete the k3d cluster
echo "🏗️  Deleting k3d cluster: $CLUSTER_NAME"
if k3d cluster list | grep -q "$CLUSTER_NAME"; then
    k3d cluster delete $CLUSTER_NAME
    echo "✅ Cluster $CLUSTER_NAME deleted"
else
    echo "⚠️  Cluster $CLUSTER_NAME not found"
fi

# Delete the local registry
echo "📦 Deleting local registry: $REGISTRY_NAME"
if k3d registry list | grep -q "$REGISTRY_NAME"; then
    k3d registry delete $REGISTRY_NAME
    echo "✅ Registry $REGISTRY_NAME deleted"
else
    echo "⚠️  Registry $REGISTRY_NAME not found"
fi

# Clean up any dangling Docker resources
echo "🧹 Cleaning up Docker resources..."
docker system prune -f --volumes || echo "⚠️  Docker cleanup completed with warnings"

# Remove kubectl context
echo "🔧 Cleaning up kubectl context..."
kubectl config delete-context k3d-$CLUSTER_NAME 2>/dev/null || echo "⚠️  kubectl context not found"

echo ""
echo "✅ Cleanup completed successfully!"
echo ""
echo "🔍 Remaining k3d resources:"
echo "Clusters:"
k3d cluster list || echo "  No clusters found"
echo "Registries:"
k3d registry list || echo "  No registries found"
echo ""
echo "💡 To recreate the cluster, run: make k8s-setup"