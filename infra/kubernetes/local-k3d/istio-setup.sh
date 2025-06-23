#!/bin/bash
# Istio Service Mesh Setup Script for Alphintra Trading Platform
# This script installs and configures Istio on the k3d cluster

set -euo pipefail

# Configuration
ISTIO_VERSION="1.20.1"
CLUSTER_NAME="alphintra-dev"
ISTIO_DIR="$HOME/.istio"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    if ! command -v kubectl >/dev/null 2>&1; then
        missing_tools+=("kubectl")
    fi
    
    if ! command -v curl >/dev/null 2>&1; then
        missing_tools+=("curl")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi
    
    # Check if cluster is running
    if ! kubectl cluster-info >/dev/null 2>&1; then
        log_error "Kubernetes cluster is not accessible. Please run ./setup.sh first."
        exit 1
    fi
    
    log_success "All prerequisites are satisfied"
}

# Download and install Istio
install_istio() {
    log_info "Installing Istio $ISTIO_VERSION..."
    
    # Create istio directory
    mkdir -p "$ISTIO_DIR"
    cd "$ISTIO_DIR"
    
    # Download Istio if not already present
    if [ ! -d "istio-$ISTIO_VERSION" ]; then
        log_info "Downloading Istio $ISTIO_VERSION..."
        curl -L https://istio.io/downloadIstio | ISTIO_VERSION=$ISTIO_VERSION sh -
    else
        log_info "Istio $ISTIO_VERSION already downloaded"
    fi
    
    # Add istioctl to PATH for this session
    export PATH="$ISTIO_DIR/istio-$ISTIO_VERSION/bin:$PATH"
    
    # Verify istioctl is available
    if ! command -v istioctl >/dev/null 2>&1; then
        log_error "istioctl not found. Please add $ISTIO_DIR/istio-$ISTIO_VERSION/bin to your PATH"
        exit 1
    fi
    
    log_success "Istio tools installed"
}

# Pre-check Istio installation
precheck_istio() {
    log_info "Running Istio pre-installation check..."
    
    istioctl x precheck
    
    log_success "Pre-installation check passed"
}

# Install Istio control plane
install_istio_control_plane() {
    log_info "Installing Istio control plane..."
    
    # Install Istio with demo profile (suitable for development)
    istioctl install --set values.defaultRevision=default \
        --set values.pilot.traceSampling=100.0 \
        --set values.global.proxy.resources.requests.cpu=10m \
        --set values.global.proxy.resources.requests.memory=40Mi \
        --set values.pilot.env.EXTERNAL_ISTIOD=false \
        --yes
    
    log_success "Istio control plane installed"
}

# Enable sidecar injection
enable_sidecar_injection() {
    log_info "Enabling automatic sidecar injection for alphintra namespace..."
    
    kubectl label namespace alphintra istio-injection=enabled --overwrite
    kubectl label namespace monitoring istio-injection=enabled --overwrite
    
    log_success "Automatic sidecar injection enabled"
}

# Install Istio addons
install_istio_addons() {
    log_info "Installing Istio addons..."
    
    local addons_dir="$ISTIO_DIR/istio-$ISTIO_VERSION/samples/addons"
    
    # Install Kiali (service mesh visualization)
    log_info "Installing Kiali..."
    kubectl apply -f "$addons_dir/kiali.yaml"
    
    # Install Jaeger (distributed tracing)
    log_info "Installing Jaeger..."
    kubectl apply -f "$addons_dir/jaeger.yaml"
    
    # Install Prometheus (metrics collection) - only if not already installed
    if ! kubectl get svc prometheus -n istio-system >/dev/null 2>&1; then
        log_info "Installing Prometheus..."
        kubectl apply -f "$addons_dir/prometheus.yaml"
    else
        log_info "Prometheus already installed, skipping..."
    fi
    
    # Install Grafana (metrics visualization)
    log_info "Installing Grafana..."
    kubectl apply -f "$addons_dir/grafana.yaml"
    
    log_success "Istio addons installed"
}

# Wait for Istio components to be ready
wait_for_istio() {
    log_info "Waiting for Istio components to be ready..."
    
    # Wait for Istio control plane
    kubectl wait --for=condition=available --timeout=300s deployment/istiod -n istio-system
    
    # Wait for addons
    kubectl wait --for=condition=available --timeout=300s deployment/kiali -n istio-system
    kubectl wait --for=condition=available --timeout=300s deployment/jaeger -n istio-system
    kubectl wait --for=condition=available --timeout=300s deployment/grafana -n istio-system
    
    log_success "All Istio components are ready"
}

# Create Istio Gateway for the trading platform
create_istio_gateway() {
    log_info "Creating Istio Gateway for Alphintra..."
    
    kubectl apply -f - <<EOF
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: alphintra-gateway
  namespace: alphintra
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "localhost"
    - "alphintra.local"
    - "api.alphintra.local"
    - "monitoring.alphintra.local"
  - port:
      number: 443
      name: https
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: alphintra-tls
    hosts:
    - "localhost"
    - "alphintra.local"
    - "api.alphintra.local"
    - "monitoring.alphintra.local"
---
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: monitoring-gateway
  namespace: monitoring
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "prometheus.alphintra.local"
    - "grafana.alphintra.local"
    - "kiali.alphintra.local"
    - "jaeger.alphintra.local"
EOF
    
    log_success "Istio Gateways created"
}

# Create destination rules for traffic policies
create_destination_rules() {
    log_info "Creating destination rules..."
    
    kubectl apply -f - <<EOF
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: alphintra-services
  namespace: alphintra
spec:
  host: "*.alphintra.svc.cluster.local"
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        maxRequestsPerConnection: 10
    circuitBreaker:
      consecutiveGatewayErrors: 5
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
EOF
    
    log_success "Destination rules created"
}

# Create peer authentication for mTLS
create_peer_authentication() {
    log_info "Creating peer authentication policies..."
    
    kubectl apply -f - <<EOF
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: alphintra
spec:
  mtls:
    mode: STRICT
---
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: monitoring-default
  namespace: monitoring
spec:
  mtls:
    mode: PERMISSIVE
EOF
    
    log_success "Peer authentication policies created"
}

# Create port forwarding for Istio addons
setup_port_forwarding() {
    log_info "Setting up port forwarding for Istio addons..."
    
    # Create a script for easy access to Istio addons
    cat > "$SCRIPT_DIR/access-istio-addons.sh" <<EOF
#!/bin/bash
# Port forwarding script for Istio addons

echo "Starting port forwarding for Istio addons..."
echo "Access the following services:"
echo "  Kiali: http://localhost:20001"
echo "  Jaeger: http://localhost:16686"
echo "  Grafana: http://localhost:3001"
echo "  Prometheus: http://localhost:9091"
echo ""
echo "Press Ctrl+C to stop all port forwarding"

# Function to cleanup background processes
cleanup() {
    echo "Stopping port forwarding..."
    kill \$(jobs -p) 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start port forwarding in background
kubectl port-forward svc/kiali 20001:20001 -n istio-system &
kubectl port-forward svc/jaeger-query 16686:16686 -n istio-system &
kubectl port-forward svc/grafana 3001:3000 -n istio-system &
kubectl port-forward svc/prometheus 9091:9090 -n istio-system &

# Wait for all background processes
wait
EOF
    
    chmod +x "$SCRIPT_DIR/access-istio-addons.sh"
    
    log_success "Port forwarding script created: $SCRIPT_DIR/access-istio-addons.sh"
}

# Display installation summary
display_summary() {
    log_success "Istio service mesh setup completed successfully!"
    echo ""
    log_info "Istio Components Installed:"
    echo "  ✓ Istio Control Plane (istiod)"
    echo "  ✓ Istio Ingress Gateway"
    echo "  ✓ Kiali (Service Mesh Dashboard)"
    echo "  ✓ Jaeger (Distributed Tracing)"
    echo "  ✓ Prometheus (Metrics Collection)"
    echo "  ✓ Grafana (Metrics Visualization)"
    echo ""
    log_info "Security Policies:"
    echo "  ✓ Automatic sidecar injection enabled"
    echo "  ✓ mTLS enabled for alphintra namespace"
    echo "  ✓ Circuit breaker and outlier detection configured"
    echo ""
    log_info "Access Istio Services:"
    echo "  Run: ./access-istio-addons.sh"
    echo "  Or use individual port forwarding:"
    echo "    kubectl port-forward svc/kiali 20001:20001 -n istio-system"
    echo "    kubectl port-forward svc/jaeger-query 16686:16686 -n istio-system"
    echo ""
    log_info "Useful Commands:"
    echo "  istioctl proxy-status"
    echo "  istioctl proxy-config cluster <pod-name> -n alphintra"
    echo "  kubectl get pods -n istio-system"
    echo ""
    log_info "Next Steps:"
    echo "  1. Deploy applications with Istio sidecar injection"
    echo "  2. Configure VirtualServices for traffic routing"
    echo "  3. Set up authorization policies for security"
}

# Main execution
main() {
    log_info "Starting Istio service mesh setup for Alphintra Trading Platform"
    
    check_prerequisites
    install_istio
    precheck_istio
    install_istio_control_plane
    enable_sidecar_injection
    install_istio_addons
    wait_for_istio
    create_istio_gateway
    create_destination_rules
    create_peer_authentication
    setup_port_forwarding
    display_summary
}

# Execute main function
main "$@"