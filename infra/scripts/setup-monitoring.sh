#!/bin/bash

# Alphintra Monitoring Stack Setup
# This script sets up Prometheus, Grafana, and Jaeger for the specified environment

set -euo pipefail

# Get environment parameter
ENVIRONMENT=${1:-dev}

# Color codes
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

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MONITORING_DIR="$PROJECT_ROOT/monitoring"

log_info "Setting up monitoring stack for environment: $ENVIRONMENT"

# Create monitoring directories
create_monitoring_directories() {
    log_info "Creating monitoring directories..."
    
    mkdir -p "$MONITORING_DIR/prometheus/rules"
    mkdir -p "$MONITORING_DIR/grafana/dashboards"
    mkdir -p "$MONITORING_DIR/grafana/provisioning/dashboards"
    mkdir -p "$MONITORING_DIR/grafana/provisioning/datasources"
    mkdir -p "$MONITORING_DIR/alertmanager"
    mkdir -p "$MONITORING_DIR/jaeger"
    mkdir -p "$MONITORING_DIR/loki"
    
    log_success "Monitoring directories created"
}

# Setup Prometheus configuration
setup_prometheus() {
    log_info "Setting up Prometheus configuration..."
    
    # Update Prometheus configuration based on environment
    local prometheus_config="$MONITORING_DIR/prometheus/prometheus.yml"
    
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        # Production Prometheus configuration
        cat > "$prometheus_config" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'alphintra-prod'
    replica: 'prometheus-1'
    environment: 'production'

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 15s

  # Application services
  - job_name: 'gateway'
    static_configs:
      - targets: ['gateway:8080']
    metrics_path: /actuator/prometheus
    scrape_interval: 15s

  - job_name: 'auth-service'
    static_configs:
      - targets: ['auth-service:8001']
    metrics_path: /metrics
    scrape_interval: 15s

  - job_name: 'trading-api'
    static_configs:
      - targets: ['trading-api:8002']
    metrics_path: /metrics
    scrape_interval: 15s

  - job_name: 'strategy-engine'
    static_configs:
      - targets: ['strategy-engine:8003']
    metrics_path: /metrics
    scrape_interval: 15s

  - job_name: 'broker-connector'
    static_configs:
      - targets: ['broker-connector:8005']
    metrics_path: /metrics
    scrape_interval: 15s

  # Infrastructure services
  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 15s

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 15s

  - job_name: 'kafka-exporter'
    static_configs:
      - targets: ['kafka-exporter:9308']
    scrape_interval: 15s

# Remote write for long-term storage (production)
remote_write:
  - url: "https://prometheus.googleapis.com/v1/projects/alphintra-trading-platform/location/global/clusters/alphintra-prod/prometheus/api/v1/write"
    queue_config:
      max_samples_per_send: 1000
      max_shards: 200
      capacity: 2500
EOF
    else
        # Development/Staging Prometheus configuration (already exists)
        log_info "Using existing Prometheus configuration for $ENVIRONMENT"
    fi
    
    # Create alerting rules
    cat > "$MONITORING_DIR/prometheus/rules/alphintra.yml" << 'EOF'
groups:
  - name: alphintra.trading
    rules:
      - alert: HighOrderLatency
        expr: histogram_quantile(0.95, rate(alphintra_order_latency_seconds_bucket[5m])) > 0.1
        for: 2m
        labels:
          severity: warning
          service: trading
        annotations:
          summary: "High order execution latency"
          description: "95th percentile order latency is {{ $value }}s"

      - alert: LowTradingVolume
        expr: rate(alphintra_trades_total[5m]) < 0.1
        for: 5m
        labels:
          severity: warning
          service: trading
        annotations:
          summary: "Low trading volume"
          description: "Trading volume is below normal levels"

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} down"
          description: "{{ $labels.job }} service has been down for more than 1 minute"

      - alert: HighErrorRate
        expr: rate(alphintra_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate"
          description: "Error rate is {{ $value }} errors/second"

  - name: alphintra.infrastructure
    rules:
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 90%"

      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is above 80%"

      - alert: DiskSpaceLow
        expr: node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space"
          description: "Disk space is below 10%"

      - alert: DatabaseConnectionFailure
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failure"
          description: "Cannot connect to PostgreSQL database"
EOF
    
    log_success "Prometheus configuration updated"
}

# Setup Grafana datasources
setup_grafana_datasources() {
    log_info "Setting up Grafana datasources..."
    
    cat > "$MONITORING_DIR/grafana/provisioning/datasources/prometheus.yml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
    jsonData:
      timeInterval: "15s"
      queryTimeout: "60s"
      httpMethod: POST

  - name: Jaeger
    type: jaeger
    access: proxy
    url: http://jaeger:16686
    editable: true
    jsonData:
      tracesToLogs:
        datasourceUid: loki
        tags: ['job', 'instance', 'pod', 'namespace']
        mappedTags: [{ key: 'service.name', value: 'service' }]
        mapTagNamesEnabled: true
        spanStartTimeShift: '1h'
        spanEndTimeShift: '1h'

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: true
    jsonData:
      derivedFields:
        - datasourceUid: jaeger
          matcherRegex: "(?:trace_id|traceID)=(\\w+)"
          name: TraceID
          url: "$${__value.raw}"
EOF
    
    log_success "Grafana datasources configured"
}

# Setup Grafana dashboards
setup_grafana_dashboards() {
    log_info "Setting up Grafana dashboards..."
    
    # Dashboard provisioning configuration
    cat > "$MONITORING_DIR/grafana/provisioning/dashboards/dashboards.yml" << 'EOF'
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF
    
    # System overview dashboard
    cat > "$MONITORING_DIR/grafana/dashboards/system-overview.json" << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Alphintra System Overview",
    "tags": ["alphintra", "system"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Service Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up",
            "legendFormat": "{{job}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "green", "value": 1}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{job}} - {{method}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ],
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "5s"
  }
}
EOF
    
    log_success "Grafana dashboards configured"
}

# Setup AlertManager
setup_alertmanager() {
    log_info "Setting up AlertManager..."
    
    local alertmanager_config="$MONITORING_DIR/alertmanager/alertmanager.yml"
    
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        cat > "$alertmanager_config" << 'EOF'
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@alphintra.com'
  smtp_auth_username: 'alerts@alphintra.com'
  smtp_auth_password: 'your-app-password'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
    - match:
        severity: warning
      receiver: 'warning-alerts'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://localhost:5001/alerts'

  - name: 'critical-alerts'
    email_configs:
      - to: 'ops@alphintra.com'
        subject: '[CRITICAL] Alphintra Alert: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Labels: {{ range .Labels.SortedPairs }}
            {{ .Name }}: {{ .Value }}
          {{ end }}
          {{ end }}
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts-critical'
        title: '[CRITICAL] {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'warning-alerts'
    email_configs:
      - to: 'dev@alphintra.com'
        subject: '[WARNING] Alphintra Alert: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          {{ end }}

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
EOF
    else
        cat > "$alertmanager_config" << 'EOF'
global:
  smtp_smarthost: 'mailhog:1025'
  smtp_from: 'alerts@alphintra.local'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://localhost:5001/alerts'
    email_configs:
      - to: 'dev@alphintra.local'
        subject: '[{{ .Status | toUpper }}] {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Labels: {{ range .Labels.SortedPairs }}
            {{ .Name }}: {{ .Value }}
          {{ end }}
          {{ end }}
EOF
    fi
    
    log_success "AlertManager configured"
}

# Create monitoring validation script
create_validation_script() {
    log_info "Creating monitoring validation script..."
    
    cat > "$SCRIPT_DIR/validate-monitoring.sh" << 'EOF'
#!/bin/bash

# Validate monitoring stack
set -euo pipefail

ENVIRONMENT=${1:-dev}

echo "Validating monitoring stack for environment: $ENVIRONMENT"

# Check Prometheus
echo "Checking Prometheus..."
if curl -s http://localhost:9090/-/healthy >/dev/null; then
    echo "✓ Prometheus is healthy"
else
    echo "✗ Prometheus is not responding"
fi

# Check Grafana
echo "Checking Grafana..."
if curl -s http://localhost:3001/api/health >/dev/null; then
    echo "✓ Grafana is healthy"
else
    echo "✗ Grafana is not responding"
fi

# Check Jaeger
echo "Checking Jaeger..."
if curl -s http://localhost:16686/ >/dev/null; then
    echo "✓ Jaeger is healthy"
else
    echo "✗ Jaeger is not responding"
fi

# Validate Prometheus targets
echo "Validating Prometheus targets..."
targets=$(curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[].health' | sort | uniq -c)
echo "Target health status:"
echo "$targets"

echo "Monitoring validation completed!"
EOF
    
    chmod +x "$SCRIPT_DIR/validate-monitoring.sh"
    
    log_success "Monitoring validation script created"
}

# Main execution
main() {
    log_info "Starting monitoring setup for environment: $ENVIRONMENT"
    
    create_monitoring_directories
    setup_prometheus
    setup_grafana_datasources
    setup_grafana_dashboards
    setup_alertmanager
    create_validation_script
    
    log_success "Monitoring stack setup completed for environment: $ENVIRONMENT"
    log_info "You can validate the setup by running: ./scripts/validate-monitoring.sh $ENVIRONMENT"
}

# Execute main function
main "$@"