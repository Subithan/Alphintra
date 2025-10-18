# Observability Stack

## Components

- **Prometheus Operator** collects Istio, application, and Kubernetes metrics.
- **Grafana** renders curated dashboards, including the gateway overview (`grafana-dashboard-gateway`).
- **Alertmanager** dispatches SLO/SLA alerts (configure channels via Terraform or manual `Secret`).

## Installation

1. Install kube-prometheus-stack (Helm example):

   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
     --namespace observability --create-namespace \
     --set grafana.adminPassword=changeme \
     --set prometheus.prometheusSpec.scrapeInterval=30s
   ```

2. Apply Alphintra resources:

   ```bash
   kubectl apply -k infra/kubernetes/observability/base
   ```

   This registers ServiceMonitors for the auth and gateway services and provisions a starter Grafana dashboard.

3. Expose Grafana:

   ```bash
   kubectl port-forward svc/monitoring-grafana -n observability 3000:80
   ```

## Dashboards & Alerts

- Import the `gateway-overview` dashboard (auto-loaded via ConfigMap) to track request rate and p95 latency.
- Recommended alert rules:
  - `GatewayLatencyHigh` when p95 latency > 750ms for 5 minutes.
  - `AuthErrorRateHigh` when HTTP 5xx from auth-service exceeds 2% for 10 minutes.
  - Add SLO burn-rate alerts using multi-window multi-burn configuration.
- Define SLOs in Grafana (Availability, Latency) and back them with Alertmanager routes to on-call rotations.

## Tracing

Enable Istio tracing by setting:

```yaml
meshConfig:
  defaultConfig:
    tracing:
      sampling: 1.0
      zipkin:
        address: otel-collector.observability:9411
```

Pair this with an OpenTelemetry collector deployment forwarding to Cloud Trace or Jaeger.

## Logging

All services emit JSON logs (via Logstash encoder). Configure Google Cloud Logging sinks or Elastic ingestion pipelines to parse the `service` field consistently.

## Maintenance

- Check Prometheus health: `kubectl port-forward svc/monitoring-kube-prometheus-stack-prometheus -n observability 9090`.
- Validate ServiceMonitor discovery: `kubectl get servicemonitors -n observability`.
- Review Grafana dashboards quarterly; keep JSON in VCS.
