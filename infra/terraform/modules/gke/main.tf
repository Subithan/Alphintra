# GKE Cluster Module for Alphintra Trading Platform
# This module creates a GKE cluster with node pools optimized for trading workloads

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Enable required APIs
resource "google_project_service" "container" {
  service = "container.googleapis.com"
  disable_dependent_services = true
}

# GKE Cluster
resource "google_container_cluster" "cluster" {
  name     = var.cluster_name
  location = var.location
  project  = var.project_id

  # Network configuration
  network    = var.network_name
  subnetwork = var.subnet_name

  # IP allocation policy for secondary ranges
  ip_allocation_policy {
    cluster_secondary_range_name  = "gke-pods"
    services_secondary_range_name = "gke-services"
  }

  # Private cluster configuration
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = var.enable_private_endpoint
    master_ipv4_cidr_block  = var.master_ipv4_cidr_block

    master_global_access_config {
      enabled = var.enable_master_global_access
    }
  }

  # Master authorized networks
  dynamic "master_authorized_networks_config" {
    for_each = var.master_authorized_networks != null ? [1] : []
    content {
      dynamic "cidr_blocks" {
        for_each = var.master_authorized_networks
        content {
          cidr_block   = cidr_blocks.value.cidr_block
          display_name = cidr_blocks.value.display_name
        }
      }
    }
  }

  # Remove default node pool
  remove_default_node_pool = true
  initial_node_count       = 1

  # Network policy
  network_policy {
    enabled  = var.enable_network_policy
    provider = var.enable_network_policy ? "CALICO" : null
  }

  # Add-on configuration
  addons_config {
    http_load_balancing {
      disabled = false
    }

    horizontal_pod_autoscaling {
      disabled = false
    }

    network_policy_config {
      disabled = !var.enable_network_policy
    }

    # Istio configuration moved to separate addon management
    # Use Istio operator or helm charts for Istio installation

    dns_cache_config {
      enabled = true
    }

    gce_persistent_disk_csi_driver_config {
      enabled = true
    }
  }

  # Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Resource labels
  resource_labels = merge(var.labels, {
    environment = var.environment
    component   = "gke-cluster"
  })

  # Maintenance policy
  maintenance_policy {
    daily_maintenance_window {
      start_time = var.maintenance_start_time
    }
  }

  # Logging and monitoring
  logging_service    = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"

  # Binary Authorization
  dynamic "binary_authorization" {
    for_each = var.enable_binary_authorization ? [1] : []
    content {
      evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
    }
  }

  # Shielded nodes
  enable_shielded_nodes = true

  # Release channel
  release_channel {
    channel = var.release_channel
  }

  depends_on = [
    google_project_service.container
  ]
}

# General Purpose Node Pool
resource "google_container_node_pool" "general_pool" {
  name       = "${var.cluster_name}-general-pool"
  location   = var.location
  cluster    = google_container_cluster.cluster.name
  project    = var.project_id

  # Autoscaling
  autoscaling {
    min_node_count = var.general_pool_min_nodes
    max_node_count = var.general_pool_max_nodes
  }

  # Node configuration
  node_config {
    preemptible  = var.general_pool_preemptible
    machine_type = var.general_pool_machine_type
    disk_size_gb = var.general_pool_disk_size_gb
    disk_type    = var.general_pool_disk_type

    # Service account
    service_account = google_service_account.gke_nodes.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    # Workload Identity
    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    # Shielded instance config
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    # Labels and taints
    labels = merge(var.labels, {
      environment = var.environment
      node-pool   = "general"
    })

    tags = ["gke-node", "${var.cluster_name}-node"]
  }

  # Node management
  management {
    auto_repair  = true
    auto_upgrade = true
  }

  # Upgrade settings
  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }
}

# High Memory Node Pool for Trading Analytics
resource "google_container_node_pool" "analytics_pool" {
  count = var.enable_analytics_pool ? 1 : 0

  name       = "${var.cluster_name}-analytics-pool"
  location   = var.location
  cluster    = google_container_cluster.cluster.name
  project    = var.project_id

  # Autoscaling
  autoscaling {
    min_node_count = var.analytics_pool_min_nodes
    max_node_count = var.analytics_pool_max_nodes
  }

  # Node configuration
  node_config {
    preemptible  = var.analytics_pool_preemptible
    machine_type = var.analytics_pool_machine_type
    disk_size_gb = var.analytics_pool_disk_size_gb
    disk_type    = var.analytics_pool_disk_type

    # Service account
    service_account = google_service_account.gke_nodes.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    # Workload Identity
    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    # Shielded instance config
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    # Labels and taints
    labels = merge(var.labels, {
      environment = var.environment
      node-pool   = "analytics"
    })

    tags = ["gke-node", "${var.cluster_name}-node"]

    # Taint for analytics workloads
    taint {
      key    = "workload-type"
      value  = "analytics"
      effect = "NO_SCHEDULE"
    }
  }

  # Node management
  management {
    auto_repair  = true
    auto_upgrade = true
  }

  # Upgrade settings
  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }
}

# Service Account for GKE Nodes
resource "google_service_account" "gke_nodes" {
  account_id   = "${var.cluster_name}-nodes"
  display_name = "GKE Nodes Service Account for ${var.cluster_name}"
  description  = "Service account for GKE nodes in ${var.cluster_name} cluster"
}

# IAM binding for GKE nodes
resource "google_project_iam_member" "gke_nodes_worker" {
  project = var.project_id
  role    = "roles/container.nodeServiceAccount"
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}

resource "google_project_iam_member" "gke_nodes_registry" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}

resource "google_project_iam_member" "gke_nodes_metrics" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}

resource "google_project_iam_member" "gke_nodes_logs" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}

# Service Account for Workload Identity
resource "google_service_account" "workload_identity" {
  account_id   = "${var.cluster_name}-wi"
  display_name = "Workload Identity Service Account for ${var.cluster_name}"
  description  = "Service account for Workload Identity in ${var.cluster_name} cluster"
}

# IAM binding for Workload Identity
resource "google_service_account_iam_member" "workload_identity_binding" {
  service_account_id = google_service_account.workload_identity.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[${var.workload_identity_namespace}/${var.workload_identity_service_account}]"
}