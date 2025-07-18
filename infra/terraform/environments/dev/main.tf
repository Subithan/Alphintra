# Development Environment Configuration for Alphintra Trading Platform
# This configuration creates a development environment on GCP

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

# Local values
locals {
  environment = "dev"
  common_labels = {
    environment = local.environment
    project     = "alphintra"
    managed_by  = "terraform"
  }
}

# VPC Network
module "vpc" {
  source = "../../modules/vpc"

  project_id   = var.project_id
  environment  = local.environment
  region       = var.region
  network_name = "${var.project_name}-${local.environment}-vpc"

  # Subnet CIDR blocks
  private_subnet_cidr  = "10.1.0.0/24"
  public_subnet_cidr   = "10.1.1.0/24"
  database_subnet_cidr = "10.1.2.0/24"
  pods_cidr           = "10.2.0.0/16"
  services_cidr       = "10.3.0.0/16"

  # SSH access (restrict in production)
  ssh_source_ranges = var.ssh_source_ranges

  labels = local.common_labels
}

# GKE Cluster
module "gke" {
  source = "../../modules/gke"

  project_id   = var.project_id
  environment  = local.environment
  cluster_name = "${var.project_name}-${local.environment}-gke"
  location     = var.region

  # Network configuration
  network_name = module.vpc.network_name
  subnet_name  = module.vpc.private_subnet_name

  # Cluster configuration
  release_channel                = "STABLE"
  enable_private_endpoint        = false  # Allow external access in dev
  enable_master_global_access    = true
  enable_network_policy          = true
  enable_istio                   = var.enable_istio
  enable_binary_authorization    = false  # Disabled in dev for faster builds

  # Master authorized networks (allow from development IPs)
  master_authorized_networks = var.master_authorized_networks

  # Node pool configuration
  general_pool_min_nodes     = 1
  general_pool_max_nodes     = 5
  general_pool_machine_type  = "e2-standard-2"  # Smaller instances for dev
  general_pool_disk_size_gb  = 50
  general_pool_preemptible   = true  # Use preemptible for cost savings

  # Analytics pool (disabled in dev to save costs)
  enable_analytics_pool = false

  labels = local.common_labels
}

# Cloud SQL Database
module "cloudsql" {
  source = "../../modules/cloudsql"

  project_id    = var.project_id
  environment   = local.environment
  instance_name = "${var.project_name}-${local.environment}-db"
  region        = var.region

  # Database configuration
  database_version  = "POSTGRES_15"
  tier             = "db-custom-1-3840"  # Smaller instance for dev
  availability_type = "ZONAL"  # Single zone for dev
  disk_type        = "PD_SSD"
  disk_size        = 20  # Smaller disk for dev

  # Network configuration
  private_network = module.vpc.network_self_link
  ipv4_enabled    = false  # Private IP only
  require_ssl     = true

  # Backup configuration (minimal for dev)
  point_in_time_recovery_enabled = false
  backup_retained_count         = 3
  transaction_log_retention_days = 3

  # Performance settings (lower for dev)
  max_connections      = "100"
  shared_buffers      = "1GB"
  effective_cache_size = "2GB"
  work_mem            = "2MB"
  maintenance_work_mem = "128MB"

  # Databases and users
  databases = [
    "trading_db",
    "auth_db",
    "strategy_db",
    "risk_db",
    "analytics_db"
  ]

  database_users = [
    "trading_user",
    "auth_user",
    "strategy_user",
    "risk_user",
    "analytics_user",
    "readonly_user"
  ]

  # TimescaleDB for time-series data
  enable_timescaledb = true

  # Security (relaxed for dev)
  deletion_protection                = false
  store_passwords_in_secret_manager = true

  labels = local.common_labels

  depends_on = [module.vpc]
}

# Redis (Cloud Memorystore) - Basic configuration for dev
resource "google_redis_instance" "cache" {
  name           = "${var.project_name}-${local.environment}-redis"
  tier           = "BASIC"  # Basic tier for dev
  memory_size_gb = 1        # Small instance for dev
  region         = var.region

  # Network
  authorized_network = module.vpc.network_id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  # Configuration
  redis_version     = "REDIS_7_0"
  display_name     = "Alphintra Dev Redis"
  redis_configs = {
    maxmemory-policy = "allkeys-lru"
  }

  # Maintenance
  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 3
        minutes = 0
      }
    }
  }

  labels = local.common_labels
}

# Pub/Sub Topic for event streaming
resource "google_pubsub_topic" "market_data" {
  name = "${var.project_name}-${local.environment}-market-data"

  labels = local.common_labels
}

resource "google_pubsub_topic" "trade_events" {
  name = "${var.project_name}-${local.environment}-trade-events"

  labels = local.common_labels
}

resource "google_pubsub_topic" "risk_alerts" {
  name = "${var.project_name}-${local.environment}-risk-alerts"

  labels = local.common_labels
}

# Pub/Sub Subscriptions
resource "google_pubsub_subscription" "market_data_sub" {
  name  = "${var.project_name}-${local.environment}-market-data-sub"
  topic = google_pubsub_topic.market_data.name

  # Message retention
  message_retention_duration = "86400s"  # 24 hours
  retain_acked_messages     = false

  # Acknowledgment deadline
  ack_deadline_seconds = 20

  labels = local.common_labels
}

resource "google_pubsub_subscription" "trade_events_sub" {
  name  = "${var.project_name}-${local.environment}-trade-events-sub"
  topic = google_pubsub_topic.trade_events.name

  message_retention_duration = "86400s"
  retain_acked_messages     = false
  ack_deadline_seconds      = 20

  labels = local.common_labels
}

# Secret Manager for sensitive configuration
resource "google_secret_manager_secret" "api_keys" {
  secret_id = "${var.project_name}-${local.environment}-api-keys"

  replication {
    auto {}
  }

  labels = local.common_labels
}

resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "${var.project_name}-${local.environment}-jwt-secret"

  replication {
    auto {}
  }

  labels = local.common_labels
}

# Generate JWT secret
resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

resource "google_secret_manager_secret_version" "jwt_secret" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = random_password.jwt_secret.result
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "compute.googleapis.com",
    "container.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "pubsub.googleapis.com",
    "secretmanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "servicenetworking.googleapis.com",
    "aiplatform.googleapis.com"
  ])

  service = each.value
  disable_dependent_services = true
}