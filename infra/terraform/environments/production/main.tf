terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }

  backend "gcs" {
    bucket = "alphintra-terraform-state-prod"
    prefix = "environments/production"
  }
}

# Configure providers
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

data "google_client_config" "default" {}

provider "kubernetes" {
  host                   = "https://${module.gke.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(module.gke.ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = "https://${module.gke.endpoint}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(module.gke.ca_certificate)
  }
}

# Local values
locals {
  environment = "production"
  project_id  = var.project_id
  region      = var.region
  zone        = var.zone

  # Network configuration
  network_name    = "alphintra-prod-network"
  subnet_name     = "alphintra-prod-subnet"
  pods_range_name = "alphintra-prod-pods"
  svc_range_name  = "alphintra-prod-services"

  # Database configuration
  database_name    = "alphintra-prod-db"
  database_user    = "alphintra"
  database_version = "POSTGRES_15"

  # GKE configuration
  cluster_name       = "alphintra-prod"
  kubernetes_version = "1.28"
  node_pools = {
    general = {
      name           = "general-pool"
      machine_type   = "n2-standard-4"
      min_count      = 3
      max_count      = 20
      disk_size_gb   = 100
      disk_type      = "pd-ssd"
      preemptible    = false
      node_locations = ["us-central1-a", "us-central1-b", "us-central1-c"]
    }
    trading = {
      name           = "trading-pool"
      machine_type   = "n2-highmem-4"
      min_count      = 2
      max_count      = 15
      disk_size_gb   = 200
      disk_type      = "pd-ssd"
      preemptible    = false
      node_locations = ["us-central1-a", "us-central1-b"]
      node_taints = [
        {
          key    = "workload-type"
          value  = "trading"
          effect = "NO_SCHEDULE"
        }
      ]
      labels = {
        workload-type = "trading"
      }
    }
    analytics = {
      name           = "analytics-pool"
      machine_type   = "n2-highcpu-8"
      min_count      = 1
      max_count      = 10
      disk_size_gb   = 100
      disk_type      = "pd-standard"
      preemptible    = true
      node_locations = ["us-central1-a"]
      node_taints = [
        {
          key    = "workload-type"
          value  = "analytics"
          effect = "NO_SCHEDULE"
        }
      ]
      labels = {
        workload-type = "analytics"
      }
    }
  }

  # Common labels
  common_labels = {
    environment = local.environment
    project     = "alphintra"
    managed-by  = "terraform"
    team        = "platform"
  }
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "compute.googleapis.com",
    "container.googleapis.com",
    "cloudsql.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "servicenetworking.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "secretmanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudtrace.googleapis.com",
    "cloudprofiler.googleapis.com",
    "artifactregistry.googleapis.com",
    "pubsub.googleapis.com",
    "storage.googleapis.com",
    "bigquery.googleapis.com",
    "dataflow.googleapis.com",
    "cloudbuild.googleapis.com",
    "binaryauthorization.googleapis.com",
    "containeranalysis.googleapis.com",
    "securitycenter.googleapis.com"
  ])

  project = local.project_id
  service = each.key

  disable_on_destroy = false
}

# VPC Network
module "vpc" {
  source = "../../modules/vpc"

  project_id   = local.project_id
  network_name = local.network_name
  region       = local.region

  subnets = [
    {
      subnet_name           = local.subnet_name
      subnet_ip             = "10.0.0.0/16"
      subnet_region         = local.region
      subnet_private_access = true
      subnet_flow_logs      = true
      description           = "Main subnet for Alphintra production environment"
    }
  ]

  secondary_ranges = {
    (local.subnet_name) = [
      {
        range_name    = local.pods_range_name
        ip_cidr_range = "10.1.0.0/16"
      },
      {
        range_name    = local.svc_range_name
        ip_cidr_range = "10.2.0.0/16"
      }
    ]
  }

  firewall_rules = [
    {
      name      = "allow-internal"
      direction = "INGRESS"
      allow = [
        {
          protocol = "icmp"
        },
        {
          protocol = "tcp"
          ports    = ["0-65535"]
        },
        {
          protocol = "udp"
          ports    = ["0-65535"]
        }
      ]
      ranges = ["10.0.0.0/8"]
    },
    {
      name      = "allow-ssh"
      direction = "INGRESS"
      allow = [
        {
          protocol = "tcp"
          ports    = ["22"]
        }
      ]
      ranges      = ["35.235.240.0/20"] # IAP range
      target_tags = ["ssh-allowed"]
    },
    {
      name      = "allow-https-lb"
      direction = "INGRESS"
      allow = [
        {
          protocol = "tcp"
          ports    = ["443", "80"]
        }
      ]
      ranges      = ["130.211.0.0/22", "35.191.0.0/16"]
      target_tags = ["https-server"]
    }
  ]

  depends_on = [google_project_service.required_apis]
}

# GKE Cluster
module "gke" {
  source = "../../modules/gke"

  project_id         = local.project_id
  name               = local.cluster_name
  region             = local.region
  zones              = ["us-central1-a", "us-central1-b", "us-central1-c"]
  network            = module.vpc.network_name
  subnetwork         = module.vpc.subnets_names[0]
  ip_range_pods      = local.pods_range_name
  ip_range_services  = local.svc_range_name
  kubernetes_version = local.kubernetes_version

  # Security and compliance
  enable_private_nodes        = true
  enable_private_endpoint     = false
  master_ipv4_cidr_block      = "172.16.0.0/28"
  enable_network_policy       = true
  enable_pod_security_policy  = true
  enable_binary_authorization = true

  # Monitoring and logging
  logging_service    = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"

  # Workload Identity
  identity_namespace = "${local.project_id}.svc.id.goog"

  # Master authorized networks
  master_authorized_networks = [
    {
      cidr_block   = "10.0.0.0/8"
      display_name = "Internal"
    },
    {
      cidr_block   = "0.0.0.0/0" # Restrict this in production
      display_name = "All"
    }
  ]

  # Node pools
  node_pools = [
    for pool_name, pool_config in local.node_pools : {
      name            = pool_config.name
      machine_type    = pool_config.machine_type
      min_count       = pool_config.min_count
      max_count       = pool_config.max_count
      local_ssd_count = 0
      disk_size_gb    = pool_config.disk_size_gb
      disk_type       = pool_config.disk_type
      image_type      = "COS_CONTAINERD"
      auto_repair     = true
      auto_upgrade    = true
      preemptible     = pool_config.preemptible
      node_locations  = pool_config.node_locations

      node_metadata = "GKE_METADATA"

      labels = merge(
        local.common_labels,
        lookup(pool_config, "labels", {})
      )

      taints = lookup(pool_config, "node_taints", [])
    }
  ]

  node_pools_oauth_scopes = {
    all = [
      "https://www.googleapis.com/auth/cloud-platform",
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring"
    ]
  }

  node_pools_tags = {
    all = ["gke-node", "alphintra-${local.environment}"]
  }

  depends_on = [module.vpc]
}

# Cloud SQL instance
module "cloudsql" {
  source = "../../modules/cloudsql"

  project_id       = local.project_id
  name             = local.database_name
  database_version = local.database_version
  region           = local.region
  zone             = local.zone

  # High availability configuration
  availability_type = "REGIONAL"

  # Network configuration
  private_network    = module.vpc.network_self_link
  allocated_ip_range = google_compute_global_address.private_ip_address.name

  # Instance configuration
  tier                  = "db-custom-4-16384" # 4 vCPU, 16GB RAM
  disk_size             = 500
  disk_type             = "PD_SSD"
  disk_autoresize       = true
  disk_autoresize_limit = 1000

  # Backup configuration
  backup_enabled            = true
  backup_start_time         = "02:00"
  backup_location           = local.region
  point_in_time_recovery    = true
  transaction_log_retention = 7

  # Maintenance configuration
  maintenance_window_day  = 7 # Sunday
  maintenance_window_hour = 3

  # Security configuration
  require_ssl         = true
  deletion_protection = true
  authorized_networks = []

  # Database and user configuration
  additional_databases = [
    {
      name      = "alphintra_prod"
      charset   = "UTF8"
      collation = "en_US.UTF8"
    },
    {
      name      = "timescaledb"
      charset   = "UTF8"
      collation = "en_US.UTF8"
    }
  ]

  additional_users = [
    {
      name     = local.database_user
      password = var.database_password
      host     = ""
    },
    {
      name     = "readonly"
      password = var.readonly_database_password
      host     = ""
    }
  ]

  # Database flags for performance
  database_flags = [
    {
      name  = "shared_preload_libraries"
      value = "timescaledb"
    },
    {
      name  = "max_connections"
      value = "200"
    },
    {
      name  = "shared_buffers"
      value = "4096MB"
    },
    {
      name  = "effective_cache_size"
      value = "12GB"
    },
    {
      name  = "work_mem"
      value = "8MB"
    },
    {
      name  = "maintenance_work_mem"
      value = "1GB"
    },
    {
      name  = "checkpoint_completion_target"
      value = "0.9"
    },
    {
      name  = "wal_buffers"
      value = "64MB"
    },
    {
      name  = "default_statistics_target"
      value = "100"
    },
    {
      name  = "random_page_cost"
      value = "1.1"
    }
  ]

  depends_on = [module.vpc]
}

# Private IP address for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  project       = local.project_id
  name          = "private-ip-address"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = module.vpc.network_id
}

# Private VPC connection
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = module.vpc.network_id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]

  depends_on = [google_project_service.required_apis]
}

# Redis instance for caching
module "redis" {
  source = "../../modules/redis"

  project_id     = local.project_id
  name           = "alphintra-cache-prod"
  region         = local.region
  memory_size_gb = 16
  tier           = "STANDARD_HA"
  redis_version  = "REDIS_7_0"

  # Network configuration
  authorized_network = module.vpc.network_id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  # Redis configuration
  auth_enabled            = true
  transit_encryption_mode = "SERVER_AUTH"

  # Backup configuration
  persistence_config = {
    persistence_mode        = "RDB"
    rdb_snapshot_period     = "TWENTY_FOUR_HOURS"
    rdb_snapshot_start_time = "02:00"
  }

  # Maintenance configuration
  maintenance_policy = {
    weekly_maintenance_window = {
      day = "SUNDAY"
      start_time = {
        hours   = 3
        minutes = 0
      }
    }
  }

  depends_on = [module.vpc]
}

# Artifact Registry for container images
module "artifact_registry" {
  source = "../../modules/artifact-registry"

  project_id    = local.project_id
  repository_id = "alphintra-prod"
  location      = local.region
  format        = "DOCKER"
  description   = "Alphintra production container registry"

  # IAM configuration
  members = [
    "serviceAccount:${google_service_account.gke_service_account.email}",
    "serviceAccount:${google_service_account.cloudbuild_service_account.email}"
  ]

  depends_on = [google_project_service.required_apis]
}

# Service accounts
resource "google_service_account" "gke_service_account" {
  project      = local.project_id
  account_id   = "gke-service-account"
  display_name = "GKE Service Account"
  description  = "Service account for GKE cluster nodes"
}

resource "google_service_account" "cloudbuild_service_account" {
  project      = local.project_id
  account_id   = "cloudbuild-service-account"
  display_name = "Cloud Build Service Account"
  description  = "Service account for Cloud Build pipelines"
}

resource "google_service_account" "workload_identity_service_account" {
  project      = local.project_id
  account_id   = "workload-identity-sa"
  display_name = "Workload Identity Service Account"
  description  = "Service account for Kubernetes workload identity"
}

# IAM bindings for service accounts
resource "google_project_iam_member" "gke_service_account_bindings" {
  for_each = toset([
    "roles/container.nodeServiceAccount",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/logging.logWriter"
  ])

  project = local.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.gke_service_account.email}"
}

# Cloud Monitoring and Logging
module "monitoring" {
  source = "../../modules/monitoring"

  project_id  = local.project_id
  environment = local.environment

  # Notification channels
  notification_channels = {
    email = {
      type         = "email"
      display_name = "Alphintra Production Alerts"
      labels = {
        email_address = var.alert_email
      }
    }
    slack = {
      type         = "slack"
      display_name = "Alphintra Slack Alerts"
      labels = {
        channel_name = "#alphintra-alerts"
        url          = var.slack_webhook_url
      }
    }
  }

  # Alert policies
  alert_policies = {
    high_cpu = {
      display_name = "High CPU Usage"
      conditions = [
        {
          display_name = "CPU usage above 80%"
          condition_threshold = {
            filter          = "resource.type=\"gke_container\""
            comparison      = "COMPARISON_GREATER_THAN"
            threshold_value = 0.8
            duration        = "300s"
          }
        }
      ]
    }

    high_memory = {
      display_name = "High Memory Usage"
      conditions = [
        {
          display_name = "Memory usage above 85%"
          condition_threshold = {
            filter          = "resource.type=\"gke_container\""
            comparison      = "COMPARISON_GREATER_THAN"
            threshold_value = 0.85
            duration        = "300s"
          }
        }
      ]
    }

    api_latency = {
      display_name = "High API Latency"
      conditions = [
        {
          display_name = "API latency above 100ms"
          condition_threshold = {
            filter          = "resource.type=\"gke_container\" AND metric.type=\"custom.googleapis.com/api_latency\""
            comparison      = "COMPARISON_GREATER_THAN"
            threshold_value = 0.1
            duration        = "60s"
          }
        }
      ]
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Security configuration
module "security" {
  source = "../../modules/security"

  project_id  = local.project_id
  environment = local.environment

  # Binary Authorization policy
  binary_authorization_policy = {
    default_admission_rule = {
      evaluation_mode  = "REQUIRE_ATTESTATION"
      enforcement_mode = "ENFORCED_BLOCK_AND_AUDIT_LOG"
      require_attestations_by = [
        "projects/${local.project_id}/attestors/prod-attestor"
      ]
    }
  }

  # Secret Manager secrets
  secrets = {
    database_password = {
      secret_id = "database-password"
      data      = var.database_password
    }
    api_keys = {
      secret_id = "api-keys"
      data      = jsonencode(var.api_keys)
    }
    tls_certificate = {
      secret_id = "tls-certificate"
      data      = var.tls_certificate
    }
    tls_private_key = {
      secret_id = "tls-private-key"
      data      = var.tls_private_key
    }
  }

  depends_on = [google_project_service.required_apis]
}

# Cloud Storage buckets for artifacts and backups
resource "google_storage_bucket" "artifacts" {
  name          = "${local.project_id}-artifacts-${local.environment}"
  location      = local.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  encryption {
    default_kms_key_name = google_kms_crypto_key.storage_key.id
  }
}

resource "google_storage_bucket" "backups" {
  name          = "${local.project_id}-backups-${local.environment}"
  location      = local.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
  }

  encryption {
    default_kms_key_name = google_kms_crypto_key.storage_key.id
  }
}

# KMS key ring and keys for encryption
resource "google_kms_key_ring" "alphintra_keyring" {
  name     = "alphintra-${local.environment}"
  location = local.region
}

resource "google_kms_crypto_key" "storage_key" {
  name     = "storage-key"
  key_ring = google_kms_key_ring.alphintra_keyring.id

  version_template {
    algorithm = "GOOGLE_SYMMETRIC_ENCRYPTION"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_kms_crypto_key" "database_key" {
  name     = "database-key"
  key_ring = google_kms_key_ring.alphintra_keyring.id

  version_template {
    algorithm = "GOOGLE_SYMMETRIC_ENCRYPTION"
  }

  lifecycle {
    prevent_destroy = true
  }
}