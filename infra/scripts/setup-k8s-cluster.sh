#!/bin/bash

# Enhanced k3d cluster setup for Alphintra Trading Platform
# This script creates a comprehensive local Kubernetes environment

set -e

CLUSTER_NAME="alphintra-cluster"
REGISTRY_NAME="alphintra-registry"
REGISTRY_PORT="5001"

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
  --agents 3 \
  --servers 1 \
  --registry-use k3d-$REGISTRY_NAME:$REGISTRY_PORT \
  --port "8080:80@loadbalancer" \
  --port "8443:443@loadbalancer" \
  --port "9091:9090@loadbalancer" \
  --port "3001:3000@loadbalancer" \
  --port "5010:5000@loadbalancer" \
  --port "16687:16686@loadbalancer" \
  --port "8762:8761@loadbalancer" \
  --port "8889:8888@loadbalancer" \
  --k3s-arg "--disable=traefik@server:*" \
  --wait

# Set kubectl context
echo "🔧 Setting kubectl context..."
kubectl config use-context k3d-$CLUSTER_NAME

# Apply namespace configuration from our standardized YAML
echo "📁 Creating standardized namespaces..."
kubectl apply -f /Users/usubithan/Documents/Alphintra/infra/kubernetes/base/namespace.yaml

# Label namespaces for Istio injection (already configured in namespace.yaml)
echo "🏷️  Namespaces are pre-configured with Istio injection labels..."

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

# Setup secrets interactively
echo "🔐 Setting up platform secrets..."
echo ""
echo "You can either:"
echo "  1. Set up secrets interactively (recommended)"
echo "  2. Use default secrets (for quick testing only)"
echo ""
read -p "Do you want to set up secrets interactively? (Y/n): " setup_secrets

if [[ "$setup_secrets" =~ ^[Nn]$ ]]; then
    echo "📝 Using default secrets for quick testing..."
    # Create default secrets for testing
    kubectl create secret generic alphintra-secrets \
      --namespace=alphintra \
      --from-literal=jwt-secret="alphintra_jwt_super_secret_key_for_financial_platform" \
      --from-literal=redis-password="alphintra_redis_pass" \
      --from-literal=postgres-password="alphintra_postgres_pass" \
      --from-literal=internal-service-token="alphintra-internal-token-2024" \
      --from-literal=encryption-key="alphintra_encryption_key_2024" \
      --from-literal=minio-access-key="alphintra-admin" \
      --from-literal=minio-secret-key="alphintra-secret-2024" \
      --dry-run=client -o yaml | kubectl apply -f -

    kubectl create secret generic monitoring-secrets \
      --namespace=monitoring \
      --from-literal=grafana-admin-password="admin" \
      --dry-run=client -o yaml | kubectl apply -f -
    
    echo "⚠️  WARNING: Using default secrets for testing only!"
    echo "   For production, run: ./scripts/setup-secrets.sh"
else
    echo "🚀 Starting interactive secrets setup..."
    ./scripts/setup-secrets.sh
fi

# Display cluster information
echo "✅ Cluster setup complete!"
echo ""
echo "📊 Cluster Information:"
echo "  Cluster Name: $CLUSTER_NAME"
echo "  Registry: localhost:$REGISTRY_PORT"
echo "  Kubeconfig Context: k3d-$CLUSTER_NAME"
echo ""
echo "🌐 Exposed Ports:"
echo "  - API Gateway: localhost:8080"
echo "  - HTTPS: localhost:8443"
echo "  - Prometheus: localhost:9091"
echo "  - Grafana: localhost:3001"
echo "  - MLflow: localhost:5010"
echo "  - Jaeger: localhost:16687"
echo "  - Eureka Server: localhost:8762"
echo "  - Config Server: localhost:8889"
echo ""
echo "📁 Namespaces Created:"
kubectl get namespaces | grep -E "(alphintra|monitoring|infrastructure|stream-processing)"
echo ""
echo "🔐 Secrets Created:"
kubectl get secrets -n alphintra | grep alphintra-secrets
kubectl get secrets -n monitoring | grep monitoring-secrets
echo ""
echo "🔧 Next steps:"
echo "  1. Install Istio: './install-istio.sh'"
echo "  2. Deploy platform: './k8s/deploy.sh'"
echo "  3. Access services through configured ports above"
echo ""
echo "📋 Useful Commands:"
echo "  kubectl get pods -A"
echo "  kubectl get services -A"
echo "  kubectl logs -f deployment/api-gateway -n alphintra"