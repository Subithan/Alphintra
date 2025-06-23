# Variables for Cloud SQL Module

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "instance_name" {
  description = "Name of the Cloud SQL instance"
  type        = string
}

variable "database_version" {
  description = "Database version"
  type        = string
  default     = "POSTGRES_15"
}

variable "region" {
  description = "Region for the Cloud SQL instance"
  type        = string
}

variable "tier" {
  description = "Machine type for the Cloud SQL instance"
  type        = string
  default     = "db-custom-2-8192"
}

variable "availability_type" {
  description = "Availability type (ZONAL or REGIONAL)"
  type        = string
  default     = "REGIONAL"
  validation {
    condition     = contains(["ZONAL", "REGIONAL"], var.availability_type)
    error_message = "Availability type must be either ZONAL or REGIONAL."
  }
}

variable "disk_type" {
  description = "Disk type (PD_SSD or PD_HDD)"
  type        = string
  default     = "PD_SSD"
}

variable "disk_size" {
  description = "Disk size in GB"
  type        = number
  default     = 100
}

variable "disk_autoresize" {
  description = "Enable automatic disk size increase"
  type        = bool
  default     = true
}

# Backup configuration
variable "backup_start_time" {
  description = "Start time for automated backups (HH:MM)"
  type        = string
  default     = "03:00"
}

variable "point_in_time_recovery_enabled" {
  description = "Enable point-in-time recovery"
  type        = bool
  default     = true
}

variable "transaction_log_retention_days" {
  description = "Number of days to retain transaction logs"
  type        = number
  default     = 7
}

variable "backup_retained_count" {
  description = "Number of backups to retain"
  type        = number
  default     = 7
}

# Network configuration
variable "ipv4_enabled" {
  description = "Enable IPv4 access"
  type        = bool
  default     = false
}

variable "private_network" {
  description = "VPC network for private IP"
  type        = string
}

variable "require_ssl" {
  description = "Require SSL connections"
  type        = bool
  default     = true
}

variable "authorized_networks" {
  description = "List of authorized networks"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

# Database configuration
variable "databases" {
  description = "List of databases to create"
  type        = list(string)
  default     = ["trading_db", "auth_db", "analytics_db", "risk_db"]
}

variable "database_users" {
  description = "List of database users to create"
  type        = list(string)
  default     = ["trading_user", "auth_user", "analytics_user", "readonly_user"]
}

# Performance tuning
variable "max_connections" {
  description = "Maximum number of connections"
  type        = string
  default     = "200"
}

variable "shared_buffers" {
  description = "Shared buffers setting"
  type        = string
  default     = "2GB"
}

variable "effective_cache_size" {
  description = "Effective cache size"
  type        = string
  default     = "6GB"
}

variable "work_mem" {
  description = "Work memory setting"
  type        = string
  default     = "4MB"
}

variable "maintenance_work_mem" {
  description = "Maintenance work memory"
  type        = string
  default     = "256MB"
}

# Maintenance window
variable "maintenance_window_day" {
  description = "Day of the week for maintenance (1=Monday, 7=Sunday)"
  type        = number
  default     = 7
  validation {
    condition     = var.maintenance_window_day >= 1 && var.maintenance_window_day <= 7
    error_message = "Maintenance window day must be between 1 and 7."
  }
}

variable "maintenance_window_hour" {
  description = "Hour of the day for maintenance (0-23)"
  type        = number
  default     = 3
  validation {
    condition     = var.maintenance_window_hour >= 0 && var.maintenance_window_hour <= 23
    error_message = "Maintenance window hour must be between 0 and 23."
  }
}

variable "maintenance_window_update_track" {
  description = "Update track for maintenance"
  type        = string
  default     = "stable"
  validation {
    condition     = contains(["canary", "stable"], var.maintenance_window_update_track)
    error_message = "Update track must be either canary or stable."
  }
}

# Read replica configuration
variable "create_read_replica" {
  description = "Create a read replica"
  type        = bool
  default     = false
}

variable "replica_region" {
  description = "Region for the read replica (if different from main)"
  type        = string
  default     = null
}

variable "replica_tier" {
  description = "Machine type for the read replica"
  type        = string
  default     = "db-custom-1-4096"
}

# TimescaleDB
variable "enable_timescaledb" {
  description = "Enable TimescaleDB extension setup"
  type        = bool
  default     = true
}

# Security
variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = true
}

variable "store_passwords_in_secret_manager" {
  description = "Store database passwords in Secret Manager"
  type        = bool
  default     = true
}

variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
  default     = {}
}