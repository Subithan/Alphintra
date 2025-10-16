# Istio Mesh Rollout Plan

## Overview

This guide covers installation and configuration of Istio for the Alphintra platform. The manifests under `infra/kubernetes/istio` assume a dedicated `istio-system` namespace and strict mTLS between workloads.

## Installation Steps

1. Add the Istio Helm repository and install the operator:

   ```bash
   istioctl operator init
   kubectl create ns istio-system
   istioctl install -y --set profile=default --set values.pilot.resources.requests.cpu=500m
   ```

2. Apply the base manifests:

   ```bash
   kubectl apply -k infra/kubernetes/istio/base
   ```

3. Apply the environment overlay:

   ```bash
   kubectl apply -k infra/kubernetes/istio/overlays/dev    # or staging/prod
   ```

4. Label the workload namespace to enable sidecar injection (the repo's `namespace.yaml` already sets this for dev/staging/prod, but `kubectl` is handy for ad-hoc clusters):

   ```bash
   kubectl label namespace alphintra istio-injection=enabled --overwrite
   ```

## mTLS & JWT

- `peerauthentication-default.yaml` enforces STRICT mTLS across the mesh.
- `requestauthentication-jwt.yaml` validates JWTs for gateway workloads with JWKS discovered from the auth service.
- `authorizationpolicy-gateway.yaml` allows anonymous access only to health checks and public auth endpoints.

Update `jwksUri`, `issuer`, and `audiences` when rotating JWT keys or integrating with external IdPs.

## Traffic Management

- `ingress-gateway.yaml` exposes HTTP(80) and HTTPS(443) entrypoints. Overlays customize hosts and TLS secrets per environment.
- `virtualservice-gateway.yaml` routes all inbound traffic to the Kotlin service gateway (`service-gateway` deployment).
- `destinationrule-*.yaml` enable Istio mutual TLS and connection tuning for service gateway and auth service.
- `serviceentry-managed-services.yaml` keeps Redis Memorystore and Cloud SQL reachable from within the mesh without disabling mTLS.

## Canary & Rollout

Virtual services support weighted routes for canary releases. Example patch:

```yaml
http:
  - route:
      - destination:
          host: service-gateway
          subset: stable
        weight: 80
      - destination:
          host: service-gateway
          subset: canary
        weight: 20
```

Create subsets in the corresponding `DestinationRule` and label deployments (`version: stable/canary`).

## Certificate Management

TLS secrets referenced in overlays (`*-alphintra-gateway-tls`) are expected to be provisioned via Cert-Manager or ACM. Update secret names as required.

## Observability

Sidecars export metrics and traces once Prometheus and Jaeger are deployed (see `docs/observability/README.md`). Enable request classification via Envoy filters if per-route latency dashboards are required.

## Troubleshooting

- Verify sidecar injection: `kubectl get pods -n alphintra -o jsonpath='{.items[*].spec.containers[*].name}' | tr ' ' '\n' | sort -u` should list `istio-proxy`.
- Inspect JWT issues with `kubectl logs -n alphintra deploy/service-gateway -c istio-proxy`.
- For mTLS failures, run `istioctl proxy-status` and `istioctl analyze` to surface config drift.
