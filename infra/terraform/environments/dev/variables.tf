# Variables for Development Environment

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "project_name" {
  description = "Name of the project (used in resource naming)"
  type        = string
  default     = "alphintra"
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The GCP zone"
  type        = string
  default     = "us-central1-a"
}

# Network configuration
variable "ssh_source_ranges" {
  description = "Source IP ranges allowed for SSH access"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Restrict this for security
}

variable "master_authorized_networks" {
  description = "List of master authorized networks for GKE"
  type = list(object({
    cidr_block   = string
    display_name = string
  }))
  default = [
    {
      cidr_block   = "0.0.0.0/0"
      display_name = "All networks (dev only)"
    }
  ]
}

# Feature flags
variable "enable_istio" {
  description = "Enable Istio service mesh"
  type        = bool
  default     = true
}

variable "enable_monitoring" {
  description = "Enable enhanced monitoring"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Enable enhanced logging"
  type        = bool
  default     = true
}

# Development specific settings
variable "enable_debug_mode" {
  description = "Enable debug mode for development"
  type        = bool
  default     = true
}

variable "auto_scaling_enabled" {
  description = "Enable auto-scaling for development workloads"
  type        = bool
  default     = true
}

# Cost optimization settings
variable "use_preemptible_nodes" {
  description = "Use preemptible nodes to reduce costs"
  type        = bool
  default     = true
}

variable "auto_shutdown_enabled" {
  description = "Enable automatic shutdown of resources during off-hours"
  type        = bool
  default     = false  # Set to true if you want to implement auto-shutdown
}

# Labels
variable "additional_labels" {
  description = "Additional labels to apply to all resources"
  type        = map(string)
  default     = {}
}