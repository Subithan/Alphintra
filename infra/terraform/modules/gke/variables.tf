# Variables for GKE Module

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "cluster_name" {
  description = "Name of the GKE cluster"
  type        = string
}

variable "location" {
  description = "Location for the GKE cluster (region or zone)"
  type        = string
}

variable "network_name" {
  description = "Name of the VPC network"
  type        = string
}

variable "subnet_name" {
  description = "Name of the subnet"
  type        = string
}

# Private cluster configuration
variable "enable_private_endpoint" {
  description = "Enable private endpoint for the cluster"
  type        = bool
  default     = false
}

variable "master_ipv4_cidr_block" {
  description = "CIDR block for the master nodes"
  type        = string
  default     = "172.16.0.0/28"
}

variable "enable_master_global_access" {
  description = "Enable global access to the master endpoint"
  type        = bool
  default     = true
}

variable "master_authorized_networks" {
  description = "List of master authorized networks"
  type = list(object({
    cidr_block   = string
    display_name = string
  }))
  default = null
}

# Cluster configuration
variable "release_channel" {
  description = "Release channel for GKE cluster"
  type        = string
  default     = "STABLE"
  validation {
    condition     = contains(["RAPID", "REGULAR", "STABLE"], var.release_channel)
    error_message = "Release channel must be one of: RAPID, REGULAR, STABLE."
  }
}

variable "enable_network_policy" {
  description = "Enable network policy"
  type        = bool
  default     = true
}

variable "enable_istio" {
  description = "Enable Istio service mesh"
  type        = bool
  default     = true
}

variable "enable_binary_authorization" {
  description = "Enable binary authorization"
  type        = bool
  default     = false
}

variable "maintenance_start_time" {
  description = "Start time for daily maintenance window (HH:MM)"
  type        = string
  default     = "03:00"
}

# General node pool configuration
variable "general_pool_min_nodes" {
  description = "Minimum number of nodes in the general pool"
  type        = number
  default     = 1
}

variable "general_pool_max_nodes" {
  description = "Maximum number of nodes in the general pool"
  type        = number
  default     = 10
}

variable "general_pool_machine_type" {
  description = "Machine type for general pool nodes"
  type        = string
  default     = "e2-standard-4"
}

variable "general_pool_disk_size_gb" {
  description = "Disk size in GB for general pool nodes"
  type        = number
  default     = 100
}

variable "general_pool_disk_type" {
  description = "Disk type for general pool nodes"
  type        = string
  default     = "pd-standard"
}

variable "general_pool_preemptible" {
  description = "Use preemptible instances for general pool"
  type        = bool
  default     = false
}

# Analytics node pool configuration
variable "enable_analytics_pool" {
  description = "Enable analytics node pool for high-memory workloads"
  type        = bool
  default     = true
}

variable "analytics_pool_min_nodes" {
  description = "Minimum number of nodes in the analytics pool"
  type        = number
  default     = 0
}

variable "analytics_pool_max_nodes" {
  description = "Maximum number of nodes in the analytics pool"
  type        = number
  default     = 5
}

variable "analytics_pool_machine_type" {
  description = "Machine type for analytics pool nodes"
  type        = string
  default     = "n2-highmem-4"
}

variable "analytics_pool_disk_size_gb" {
  description = "Disk size in GB for analytics pool nodes"
  type        = number
  default     = 200
}

variable "analytics_pool_disk_type" {
  description = "Disk type for analytics pool nodes"
  type        = string
  default     = "pd-ssd"
}

variable "analytics_pool_preemptible" {
  description = "Use preemptible instances for analytics pool"
  type        = bool
  default     = true
}

# Workload Identity configuration
variable "workload_identity_namespace" {
  description = "Kubernetes namespace for Workload Identity"
  type        = string
  default     = "default"
}

variable "workload_identity_service_account" {
  description = "Kubernetes service account for Workload Identity"
  type        = string
  default     = "default"
}

variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
  default     = {}
}