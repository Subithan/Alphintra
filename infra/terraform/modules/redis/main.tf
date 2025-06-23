terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

resource "google_redis_instance" "cache" {
  name           = var.name
  project        = var.project_id
  region         = var.region
  memory_size_gb = var.memory_size_gb
  tier           = var.tier
  redis_version  = var.redis_version

  authorized_network = var.authorized_network
  connect_mode       = var.connect_mode

  auth_enabled            = var.auth_enabled
  transit_encryption_mode = var.transit_encryption_mode

  dynamic "persistence_config" {
    for_each = var.persistence_config != null ? [var.persistence_config] : []
    content {
      persistence_mode        = persistence_config.value.persistence_mode
      rdb_snapshot_period     = persistence_config.value.rdb_snapshot_period
      rdb_snapshot_start_time = persistence_config.value.rdb_snapshot_start_time
    }
  }

  dynamic "maintenance_policy" {
    for_each = var.maintenance_policy != null ? [var.maintenance_policy] : []
    content {
      dynamic "weekly_maintenance_window" {
        for_each = [maintenance_policy.value.weekly_maintenance_window]
        content {
          day = weekly_maintenance_window.value.day
          dynamic "start_time" {
            for_each = [weekly_maintenance_window.value.start_time]
            content {
              hours   = start_time.value.hours
              minutes = start_time.value.minutes
            }
          }
        }
      }
    }
  }

  labels = {
    environment = "production"
    managed-by  = "terraform"
  }
}