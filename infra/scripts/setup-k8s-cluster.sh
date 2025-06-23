#!/bin/bash

# Enhanced k3d cluster setup for Alphintra Trading Platform
# This script creates a comprehensive local Kubernetes environment

set -e

CLUSTER_NAME="alphintra-cluster"
REGISTRY_NAME="alphintra-registry"
REGISTRY_PORT="5002"

echo "🚀 Setting up Alphintra k3d cluster..."

# Check if cluster already exists
if k3d cluster list | grep -q "$CLUSTER_NAME"; then
    echo "⚠️  Cluster $CLUSTER_NAME already exists. Deleting..."
    k3d cluster delete $CLUSTER_NAME
fi

# Check if registry already exists
if k3d registry list | grep -q "$REGISTRY_NAME"; then
    echo "⚠️  Registry $REGISTRY_NAME already exists. Deleting..."
    k3d registry delete $REGISTRY_NAME
fi

# Create local registry for container images
echo "📦 Creating local container registry..."
k3d registry create $REGISTRY_NAME --port $REGISTRY_PORT

# Create k3d cluster with enhanced configuration
echo "🏗️  Creating k3d cluster with enhanced configuration..."
k3d cluster create $CLUSTER_NAME \
  --agents 2 \
  --servers 1 \
  --registry-use k3d-$REGISTRY_NAME:$REGISTRY_PORT \
  --port "8090:80@loadbalancer" \
  --port "8453:443@loadbalancer" \
  --port "9091:9090@loadbalancer" \
  --port "3010:3000@loadbalancer" \
  --port "5010:5000@loadbalancer" \
  --port "16687:16686@loadbalancer" \
  --k3s-arg "--disable=traefik@server:*" \
  --wait

# Set kubectl context
echo "🔧 Setting kubectl context..."
kubectl config use-context k3d-$CLUSTER_NAME

# Create namespaces
echo "📁 Creating namespaces..."
kubectl create namespace alphintra-system --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace alphintra-dev --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace alphintra-monitoring --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace alphintra-ml --dry-run=client -o yaml | kubectl apply -f -

# Label namespaces for Istio injection
echo "🏷️  Labeling namespaces for Istio injection..."
kubectl label namespace alphintra-dev istio-injection=enabled --overwrite
kubectl label namespace alphintra-ml istio-injection=enabled --overwrite

# Skip MetalLB for faster development setup (using k3d built-in servicelb)
echo "🚀 Using k3d built-in LoadBalancer for faster development setup..."
echo "💡 MetalLB can be installed later if needed: kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.13.12/config/manifests/metallb-native.yaml"

# Note: MetalLB IP pool configuration skipped for development
echo "🌐 LoadBalancer services will use k3d's built-in load balancer..."

# Create storage class for persistent volumes
echo "💾 Creating storage class..."
cat <<EOF | kubectl apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: alphintra-storage
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: rancher.io/local-path
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
EOF

# Display cluster information
echo "✅ Cluster setup complete!"
echo ""
echo "📊 Cluster Information:"
echo "  Cluster Name: $CLUSTER_NAME"
echo "  Registry: localhost:$REGISTRY_PORT"
echo "  Kubeconfig Context: k3d-$CLUSTER_NAME"
echo ""
echo "🌐 Exposed Ports:"
echo "  - HTTP: localhost:8080"
echo "  - HTTPS: localhost:8443"
echo "  - Prometheus: localhost:9090"
echo "  - Grafana: localhost:3000"
echo "  - MLflow: localhost:5000"
echo "  - Jaeger: localhost:16686"
echo ""
echo "📁 Namespaces:"
kubectl get namespaces | grep alphintra
echo ""
echo "🔧 Next steps:"
echo "  1. Run './install-istio.sh' to install Istio service mesh"
echo "  2. Deploy applications with 'kubectl apply -k ../kubernetes/overlays/dev/'"
echo "  3. Access services through the configured ports above"