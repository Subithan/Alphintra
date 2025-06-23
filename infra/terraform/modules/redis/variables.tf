variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "name" {
  description = "The name of the Redis instance"
  type        = string
}

variable "region" {
  description = "The region for the Redis instance"
  type        = string
}

variable "memory_size_gb" {
  description = "Redis memory size in GB"
  type        = number
}

variable "tier" {
  description = "The service tier of the instance"
  type        = string
  default     = "STANDARD_HA"
}

variable "redis_version" {
  description = "The version of Redis software"
  type        = string
  default     = "REDIS_7_0"
}

variable "authorized_network" {
  description = "The full name of the Google Compute Engine network"
  type        = string
}

variable "connect_mode" {
  description = "The connection mode of the Redis instance"
  type        = string
  default     = "PRIVATE_SERVICE_ACCESS"
}

variable "auth_enabled" {
  description = "Optional. Indicates whether OSS Redis AUTH is enabled"
  type        = bool
  default     = true
}

variable "transit_encryption_mode" {
  description = "The TLS mode of the Redis instance"
  type        = string
  default     = "SERVER_AUTH"
}

variable "persistence_config" {
  description = "Persistence configuration for the Redis instance"
  type = object({
    persistence_mode        = string
    rdb_snapshot_period     = string
    rdb_snapshot_start_time = string
  })
  default = null
}

variable "maintenance_policy" {
  description = "Maintenance policy for the Redis instance"
  type = object({
    weekly_maintenance_window = object({
      day = string
      start_time = object({
        hours   = number
        minutes = number
      })
    })
  })
  default = null
}