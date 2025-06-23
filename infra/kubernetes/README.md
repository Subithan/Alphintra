# Alphintra Kubernetes Configuration

## Overview
This directory contains Kubernetes manifests, Helm charts, and configuration files for deploying the Alphintra Trading Platform on both local k3d clusters and Google Kubernetes Engine (GKE).

## Directory Structure
```
kubernetes/
├── base/                  # Base Kubernetes manifests
│   ├── namespace.yaml     # Namespaces
│   ├── configmaps/        # ConfigMaps
│   ├── secrets/           # Secret templates
│   └── services/          # Service definitions
├── overlays/              # Kustomize overlays
│   ├── dev/              # Development overrides
│   ├── staging/          # Staging overrides
│   └── prod/             # Production overrides
├── helm-charts/          # Custom Helm charts
│   ├── alphintra-platform/
│   ├── trading-services/
│   └── infrastructure/
├── istio/                # Istio service mesh configuration
│   ├── gateways/         # Istio Gateways
│   ├── virtual-services/ # VirtualServices
│   ├── destination-rules/ # DestinationRules
│   └── policies/         # Security policies
└── local-k3d/           # k3d local cluster setup
    ├── cluster-config.yaml
    ├── setup.sh
    └── istio-setup.sh
```

## Quick Start

### Local Development with k3d
```bash
# Create k3d cluster
cd local-k3d
./setup.sh

# Install Istio
./istio-setup.sh

# Deploy applications
kubectl apply -k ../overlays/dev/
```

### Production Deployment on GKE
```bash
# Connect to GKE cluster
gcloud container clusters get-credentials alphintra-prod-gke --region us-central1

# Deploy with Helm
helm install alphintra ./helm-charts/alphintra-platform/ -f values-prod.yaml
```

## Prerequisites
- kubectl
- k3d (for local development)
- Helm 3
- Istioctl (for service mesh)