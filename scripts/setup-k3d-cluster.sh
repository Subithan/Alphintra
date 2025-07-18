#!/bin/bash
# scripts/setup-k3d-cluster.sh
# Secure K3D Cluster Setup for Alphintra Financial Platform

set -e

echo "🚀 Setting up K3D cluster for Alphintra Financial Platform..."

# Check if k3d is installed
if ! command -v k3d &> /dev/null; then
    echo "❌ k3d is not installed. Please install k3d first."
    echo "Run: curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Delete existing cluster if it exists
echo "🧹 Cleaning up existing cluster..."
k3d cluster delete alphintra-cluster 2>/dev/null || true

# Create registry directory
mkdir -p /tmp/k3d-registry

echo "🏗️ Creating K3D cluster with optimal settings for financial platform..."

# Create k3d cluster with specific configuration for Alphintra
k3d cluster create alphintra-cluster \
  --api-port 6550 \
  --port "80:80@loadbalancer" \
  --port "443:443@loadbalancer" \
  --port "30001:30001@loadbalancer" \
  --port "30002:30002@loadbalancer" \
  --port "30003:30003@loadbalancer" \
  --agents 3 \
  --servers 1 \
  --k3s-arg "--disable=traefik@server:0" \
  --k3s-arg "--disable=metrics-server@server:0" \
  --volume "/tmp/k3d-registry:/var/lib/rancher/k3s/agent/etc/registries.d" \
  --registry-create k3d-registry.localhost:5000

echo "⏳ Waiting for cluster to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s

echo "📦 Creating namespaces..."
# Create namespaces
kubectl create namespace alphintra
kubectl create namespace alphintra-system
kubectl create namespace monitoring
kubectl create namespace istio-system

# Label namespaces for network policies
kubectl label namespace alphintra name=alphintra
kubectl label namespace alphintra-system name=alphintra-system
kubectl label namespace monitoring name=monitoring

echo "🔐 Setting up security policies..."
# Apply default deny-all network policy
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: alphintra
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
EOF

echo "📊 Installing Traefik as ingress controller..."
# Install Traefik
kubectl apply -f https://raw.githubusercontent.com/traefik/traefik/v2.10/docs/content/reference/dynamic-configuration/kubernetes-crd-definition-v1.yml
kubectl apply -f https://raw.githubusercontent.com/traefik/traefik/v2.10/docs/content/reference/dynamic-configuration/kubernetes-crd-rbac.yml

# Create Traefik deployment
kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: traefik-ingress-controller
  namespace: kube-system
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: traefik
  namespace: kube-system
  labels:
    app: traefik
spec:
  replicas: 1
  selector:
    matchLabels:
      app: traefik
  template:
    metadata:
      labels:
        app: traefik
    spec:
      serviceAccountName: traefik-ingress-controller
      containers:
      - name: traefik
        image: traefik:v2.10
        args:
        - --api.insecure=true
        - --providers.kubernetesingress
        - --providers.kubernetescrd
        - --entrypoints.web.address=:80
        - --entrypoints.websecure.address=:443
        - --certificatesresolvers.letsencrypt.acme.email=admin@alphintra.com
        - --certificatesresolvers.letsencrypt.acme.storage=/data/acme.json
        - --certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web
        ports:
        - name: web
          containerPort: 80
        - name: websecure
          containerPort: 443
        - name: admin
          containerPort: 8080
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: traefik
  namespace: kube-system
spec:
  selector:
    app: traefik
  ports:
  - name: web
    port: 80
    targetPort: 80
  - name: websecure
    port: 443
    targetPort: 443
  - name: admin
    port: 8080
    targetPort: 8080
  type: LoadBalancer
EOF

echo "⏳ Waiting for Traefik to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/traefik -n kube-system

echo "✅ K3D cluster 'alphintra-cluster' created successfully!"
echo "📋 Cluster Information:"
echo "   - API Server: https://localhost:6550"
echo "   - HTTP Ingress: http://localhost:80"
echo "   - HTTPS Ingress: https://localhost:443"
echo "   - Grafana (when deployed): http://localhost:30001"
echo "   - Registry: k3d-registry.localhost:5000"
echo ""
echo "🔧 Next steps:"
echo "   1. Run: kubectl get nodes"
echo "   2. Deploy databases: kubectl apply -f k3d/databases/"
echo "   3. Deploy services: kubectl apply -f k3d/services/"
echo "   4. Check status: kubectl get pods -A"
echo ""
echo "🎯 Ready to deploy Alphintra microservices!"