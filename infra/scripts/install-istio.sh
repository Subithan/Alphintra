#!/bin/bash

# Enhanced Istio installation for Alphintra Trading Platform
# This script installs and configures Istio service mesh with observability

set -e

ISTIO_VERSION="1.20.1"
ISTIO_DIR="istio-${ISTIO_VERSION}"

echo "🕸️  Installing Istio Service Mesh..."

# Check if istioctl is available
if ! command -v istioctl &> /dev/null; then
    echo "📥 Downloading Istio ${ISTIO_VERSION}..."
    
    # Download Istio
    curl -L https://istio.io/downloadIstio | ISTIO_VERSION=${ISTIO_VERSION} sh -
    
    # Add istioctl to PATH for this session
    export PATH="$PWD/${ISTIO_DIR}/bin:$PATH"
    
    echo "✅ Istio downloaded and istioctl added to PATH"
else
    echo "✅ istioctl already available"
fi

# Install Istio with demo profile (includes observability tools)
echo "🚀 Installing Istio with demo profile..."
istioctl install --set values.defaultRevision=default \
  --set values.pilot.env.EXTERNAL_ISTIOD=false \
  --set values.gateways.istio-ingressgateway.type=LoadBalancer \
  --set values.gateways.istio-ingressgateway.ports[0].port=80 \
  --set values.gateways.istio-ingressgateway.ports[0].targetPort=8080 \
  --set values.gateways.istio-ingressgateway.ports[0].name=http2 \
  --set values.gateways.istio-ingressgateway.ports[1].port=443 \
  --set values.gateways.istio-ingressgateway.ports[1].targetPort=8443 \
  --set values.gateways.istio-ingressgateway.ports[1].name=https \
  -y

# Wait for Istio components to be ready
echo "⏳ Waiting for Istio components to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/istiod -n istio-system
kubectl wait --for=condition=available --timeout=300s deployment/istio-ingressgateway -n istio-system

# Install Istio observability addons
echo "📊 Installing Istio observability addons..."

# Apply Prometheus addon
echo "  - Installing Prometheus..."
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/prometheus.yaml

# Apply Grafana addon
echo "  - Installing Grafana..."
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/grafana.yaml

# Apply Jaeger addon
echo "  - Installing Jaeger..."
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/jaeger.yaml

# Apply Kiali addon
echo "  - Installing Kiali..."
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/kiali.yaml

# Wait for addons to be ready
echo "⏳ Waiting for observability addons to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n istio-system || echo "⚠️  Prometheus deployment timeout (may still be starting)"
kubectl wait --for=condition=available --timeout=300s deployment/grafana -n istio-system || echo "⚠️  Grafana deployment timeout (may still be starting)"
kubectl wait --for=condition=available --timeout=300s deployment/jaeger -n istio-system || echo "⚠️  Jaeger deployment timeout (may still be starting)"
kubectl wait --for=condition=available --timeout=300s deployment/kiali -n istio-system || echo "⚠️  Kiali deployment timeout (may still be starting)"

# Create Istio Gateway for the application
echo "🚪 Creating Istio Gateway..."
cat <<EOF | kubectl apply -f -
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: alphintra-gateway
  namespace: alphintra-dev
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "*"
  - port:
      number: 443
      name: https
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: alphintra-tls
    hosts:
    - "*"
EOF

# Create VirtualService for routing
echo "🛣️  Creating VirtualService for routing..."
cat <<EOF | kubectl apply -f -
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: alphintra-vs
  namespace: alphintra-dev
spec:
  hosts:
  - "*"
  gateways:
  - alphintra-gateway
  http:
  - match:
    - uri:
        prefix: /api/auth
    route:
    - destination:
        host: auth-service
        port:
          number: 8080
  - match:
    - uri:
        prefix: /api/trading
    route:
    - destination:
        host: trading-api
        port:
          number: 8080
  - match:
    - uri:
        prefix: /api
    route:
    - destination:
        host: gateway
        port:
          number: 8080
  - match:
    - uri:
        prefix: /
    route:
    - destination:
        host: gateway
        port:
          number: 8080
EOF

# Create DestinationRules for traffic policies
echo "📋 Creating DestinationRules..."
cat <<EOF | kubectl apply -f -
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: alphintra-destination-rules
  namespace: alphintra-dev
spec:
  host: "*.alphintra-dev.svc.cluster.local"
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        maxRequestsPerConnection: 10
    outlierDetection:
      consecutiveErrors: 3
      interval: 30s
      baseEjectionTime: 30s
EOF

# Enable automatic sidecar injection for application namespaces
echo "💉 Enabling automatic sidecar injection..."
kubectl label namespace alphintra-dev istio-injection=enabled --overwrite
kubectl label namespace alphintra-ml istio-injection=enabled --overwrite

# Display installation summary
echo "✅ Istio installation complete!"
echo ""
echo "🕸️  Istio Service Mesh Information:"
echo "  Version: ${ISTIO_VERSION}"
echo "  Profile: demo (with observability)"
echo "  Ingress Gateway: LoadBalancer"
echo ""
echo "📊 Observability Tools:"
echo "  - Prometheus: kubectl port-forward -n istio-system svc/prometheus 9090:9090"
echo "  - Grafana: kubectl port-forward -n istio-system svc/grafana 3000:3000"
echo "  - Jaeger: kubectl port-forward -n istio-system svc/jaeger 16686:16686"
echo "  - Kiali: kubectl port-forward -n istio-system svc/kiali 20001:20001"
echo ""
echo "🚪 Gateway Configuration:"
echo "  - Gateway: alphintra-gateway (alphintra-dev namespace)"
echo "  - VirtualService: alphintra-vs (routing configured)"
echo "  - DestinationRule: alphintra-destination-rules (traffic policies)"
echo ""
echo "💉 Sidecar Injection:"
echo "  - alphintra-dev: enabled"
echo "  - alphintra-ml: enabled"
echo ""
echo "🔧 Next steps:"
echo "  1. Deploy applications to namespaces with istio-injection=enabled"
echo "  2. Access observability tools using the port-forward commands above"
echo "  3. Monitor service mesh traffic through Kiali dashboard"