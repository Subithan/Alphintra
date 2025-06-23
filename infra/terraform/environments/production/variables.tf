variable "project_id" {
  description = "The GCP project ID"
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "Project ID must be a valid GCP project ID format."
  }
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
  validation {
    condition = contains([
      "us-central1", "us-east1", "us-west1", "us-west2",
      "europe-west1", "europe-west2", "asia-east1", "asia-southeast1"
    ], var.region)
    error_message = "Region must be a valid GCP region."
  }
}

variable "zone" {
  description = "The GCP zone for resources"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "The environment name (production, staging, development)"
  type        = string
  default     = "production"
  validation {
    condition     = contains(["production", "staging", "development"], var.environment)
    error_message = "Environment must be one of: production, staging, development."
  }
}

# Database variables
variable "database_password" {
  description = "Password for the main database user"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.database_password) >= 12
    error_message = "Database password must be at least 12 characters long."
  }
}

variable "readonly_database_password" {
  description = "Password for the readonly database user"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.readonly_database_password) >= 12
    error_message = "Readonly database password must be at least 12 characters long."
  }
}

# API and authentication variables
variable "api_keys" {
  description = "Map of API keys for external services"
  type = object({
    binance_api_key     = string
    binance_secret_key  = string
    coinbase_api_key    = string
    coinbase_secret_key = string
    alpha_vantage_key   = string
    finnhub_api_key     = string
    polygon_api_key     = string
    quandl_api_key      = string
  })
  sensitive = true
}

variable "jwt_secret" {
  description = "Secret key for JWT token signing"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.jwt_secret) >= 32
    error_message = "JWT secret must be at least 32 characters long."
  }
}

# TLS certificates
variable "tls_certificate" {
  description = "TLS certificate for HTTPS endpoints"
  type        = string
  sensitive   = true
}

variable "tls_private_key" {
  description = "TLS private key for HTTPS endpoints"
  type        = string
  sensitive   = true
}

# Monitoring and alerting
variable "alert_email" {
  description = "Email address for production alerts"
  type        = string
  validation {
    condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.alert_email))
    error_message = "Alert email must be a valid email address."
  }
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for production alerts"
  type        = string
  sensitive   = true
  validation {
    condition     = can(regex("^https://hooks\\.slack\\.com/services/", var.slack_webhook_url))
    error_message = "Slack webhook URL must be a valid Slack webhook URL."
  }
}

variable "pagerduty_integration_key" {
  description = "PagerDuty integration key for critical alerts"
  type        = string
  sensitive   = true
  default     = ""
}

# Network configuration
variable "authorized_networks" {
  description = "List of authorized networks for GKE master access"
  type = list(object({
    cidr_block   = string
    display_name = string
  }))
  default = [
    {
      cidr_block   = "0.0.0.0/0"
      display_name = "All"
    }
  ]
}

variable "enable_private_nodes" {
  description = "Enable private nodes in GKE cluster"
  type        = bool
  default     = true
}

variable "enable_network_policy" {
  description = "Enable network policy in GKE cluster"
  type        = bool
  default     = true
}

# Security configuration
variable "enable_binary_authorization" {
  description = "Enable Binary Authorization for container images"
  type        = bool
  default     = true
}

variable "enable_pod_security_policy" {
  description = "Enable Pod Security Policy in GKE cluster"
  type        = bool
  default     = true
}

variable "enable_workload_identity" {
  description = "Enable Workload Identity in GKE cluster"
  type        = bool
  default     = true
}

# Backup and disaster recovery
variable "backup_retention_days" {
  description = "Number of days to retain database backups"
  type        = number
  default     = 30
  validation {
    condition     = var.backup_retention_days >= 7 && var.backup_retention_days <= 365
    error_message = "Backup retention days must be between 7 and 365."
  }
}

variable "enable_point_in_time_recovery" {
  description = "Enable point-in-time recovery for Cloud SQL"
  type        = bool
  default     = true
}

# Performance and scaling
variable "node_pool_config" {
  description = "Configuration for GKE node pools"
  type = map(object({
    machine_type   = string
    min_count      = number
    max_count      = number
    disk_size_gb   = number
    disk_type      = string
    preemptible    = bool
    node_locations = list(string)
    labels         = map(string)
    taints = list(object({
      key    = string
      value  = string
      effect = string
    }))
  }))
  default = {
    general = {
      machine_type   = "n2-standard-4"
      min_count      = 3
      max_count      = 20
      disk_size_gb   = 100
      disk_type      = "pd-ssd"
      preemptible    = false
      node_locations = ["us-central1-a", "us-central1-b", "us-central1-c"]
      labels         = {}
      taints         = []
    }
  }
}

variable "database_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-custom-4-16384"
  validation {
    condition     = can(regex("^db-(standard|custom)-", var.database_tier))
    error_message = "Database tier must be a valid Cloud SQL machine type."
  }
}

variable "database_disk_size" {
  description = "Cloud SQL disk size in GB"
  type        = number
  default     = 500
  validation {
    condition     = var.database_disk_size >= 100 && var.database_disk_size <= 30720
    error_message = "Database disk size must be between 100 GB and 30720 GB."
  }
}

variable "redis_memory_size_gb" {
  description = "Redis instance memory size in GB"
  type        = number
  default     = 16
  validation {
    condition     = var.redis_memory_size_gb >= 1 && var.redis_memory_size_gb <= 300
    error_message = "Redis memory size must be between 1 GB and 300 GB."
  }
}

# Cost optimization
variable "enable_preemptible_nodes" {
  description = "Enable preemptible nodes for cost optimization"
  type        = bool
  default     = false
}

variable "enable_cluster_autoscaling" {
  description = "Enable cluster autoscaling"
  type        = bool
  default     = true
}

# Compliance and governance
variable "enable_audit_logs" {
  description = "Enable audit logs for compliance"
  type        = bool
  default     = true
}

variable "enable_data_encryption" {
  description = "Enable data encryption at rest"
  type        = bool
  default     = true
}

variable "compliance_framework" {
  description = "Compliance framework to follow (SOC2, PCI-DSS, GDPR)"
  type        = string
  default     = "SOC2"
  validation {
    condition     = contains(["SOC2", "PCI-DSS", "GDPR", "HIPAA"], var.compliance_framework)
    error_message = "Compliance framework must be one of: SOC2, PCI-DSS, GDPR, HIPAA."
  }
}

# Feature flags
variable "enable_istio" {
  description = "Enable Istio service mesh"
  type        = bool
  default     = true
}

variable "enable_monitoring" {
  description = "Enable comprehensive monitoring stack"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Enable centralized logging"
  type        = bool
  default     = true
}

variable "enable_tracing" {
  description = "Enable distributed tracing"
  type        = bool
  default     = true
}

# Business continuity
variable "multi_region_deployment" {
  description = "Enable multi-region deployment for high availability"
  type        = bool
  default     = false
}

variable "disaster_recovery_region" {
  description = "Region for disaster recovery deployment"
  type        = string
  default     = "us-east1"
}

# Development and testing
variable "enable_development_access" {
  description = "Enable development team access to production resources"
  type        = bool
  default     = false
}

variable "enable_debug_mode" {
  description = "Enable debug mode for troubleshooting"
  type        = bool
  default     = false
}

# Resource limits
variable "resource_quotas" {
  description = "Resource quotas for namespaces"
  type = object({
    cpu_requests     = string
    memory_requests  = string
    cpu_limits       = string
    memory_limits    = string
    storage_requests = string
    pod_count        = number
  })
  default = {
    cpu_requests     = "20"
    memory_requests  = "40Gi"
    cpu_limits       = "40"
    memory_limits    = "80Gi"
    storage_requests = "100Gi"
    pod_count        = 100
  }
}

# External integrations
variable "external_dns_domain" {
  description = "External DNS domain for services"
  type        = string
  default     = "alphintra.com"
}

variable "certificate_manager_email" {
  description = "Email for Let's Encrypt certificate manager"
  type        = string
  default     = ""
}

# Trading-specific configuration
variable "trading_config" {
  description = "Trading-specific configuration"
  type = object({
    max_position_size     = number
    risk_limit_percentage = number
    enable_paper_trading  = bool
    supported_exchanges   = list(string)
    base_currency         = string
  })
  default = {
    max_position_size     = 10000
    risk_limit_percentage = 2.0
    enable_paper_trading  = false
    supported_exchanges   = ["binance", "coinbase", "kraken"]
    base_currency         = "USD"
  }
}

# Machine learning configuration
variable "ml_config" {
  description = "Machine learning configuration"
  type = object({
    enable_gpu_nodes     = bool
    gpu_type             = string
    model_storage_bucket = string
    training_data_bucket = string
  })
  default = {
    enable_gpu_nodes     = false
    gpu_type             = "nvidia-tesla-t4"
    model_storage_bucket = ""
    training_data_bucket = ""
  }
}