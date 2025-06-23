# Cloud SQL Module for Alphintra Trading Platform
# This module creates PostgreSQL instances with high availability and performance

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
resource "google_project_service" "sqladmin" {
  service = "sqladmin.googleapis.com"
  disable_dependent_services = true
}

# Random password for database users
resource "random_password" "db_password" {
  for_each = toset(var.database_users)
  length   = 16
  special  = true
}

# Main PostgreSQL instance
resource "google_sql_database_instance" "main" {
  name             = var.instance_name
  database_version = var.database_version
  region           = var.region
  project          = var.project_id

  settings {
    tier              = var.tier
    availability_type = var.availability_type
    disk_type         = var.disk_type
    disk_size         = var.disk_size
    disk_autoresize   = var.disk_autoresize

    # Backup configuration
    backup_configuration {
      enabled                        = true
      start_time                     = var.backup_start_time
      point_in_time_recovery_enabled = var.point_in_time_recovery_enabled
      transaction_log_retention_days = var.transaction_log_retention_days
      
      backup_retention_settings {
        retained_backups = var.backup_retained_count
        retention_unit   = "COUNT"
      }
    }

    # Database flags for performance optimization
    database_flags {
      name  = "shared_preload_libraries"
      value = "pg_stat_statements,pg_hint_plan"
    }

    database_flags {
      name  = "max_connections"
      value = var.max_connections
    }

    database_flags {
      name  = "shared_buffers"
      value = var.shared_buffers
    }

    database_flags {
      name  = "effective_cache_size"
      value = var.effective_cache_size
    }

    database_flags {
      name  = "work_mem"
      value = var.work_mem
    }

    database_flags {
      name  = "maintenance_work_mem"
      value = var.maintenance_work_mem
    }

    database_flags {
      name  = "checkpoint_completion_target"
      value = "0.9"
    }

    database_flags {
      name  = "wal_buffers"
      value = "16MB"
    }

    database_flags {
      name  = "random_page_cost"
      value = "1.1"
    }

    # IP configuration
    ip_configuration {
      ipv4_enabled                                  = var.ipv4_enabled
      private_network                               = var.private_network
      enable_private_path_for_google_cloud_services = true
      require_ssl                                   = var.require_ssl

      dynamic "authorized_networks" {
        for_each = var.authorized_networks
        content {
          name  = authorized_networks.value.name
          value = authorized_networks.value.value
        }
      }
    }

    # Maintenance window
    maintenance_window {
      day          = var.maintenance_window_day
      hour         = var.maintenance_window_hour
      update_track = var.maintenance_window_update_track
    }

    # Insights configuration
    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }

    # User labels
    user_labels = merge(var.labels, {
      environment = var.environment
      component   = "database"
    })
  }

  # Deletion protection
  deletion_protection = var.deletion_protection

  depends_on = [
    google_project_service.sqladmin
  ]
}

# Create databases
resource "google_sql_database" "databases" {
  for_each = toset(var.databases)
  
  name     = each.value
  instance = google_sql_database_instance.main.name
  project  = var.project_id
}

# Create database users
resource "google_sql_user" "users" {
  for_each = toset(var.database_users)
  
  name     = each.value
  instance = google_sql_database_instance.main.name
  password = random_password.db_password[each.value].result
  project  = var.project_id
  type     = "BUILT_IN"
}

# Read replica (optional)
resource "google_sql_database_instance" "read_replica" {
  count = var.create_read_replica ? 1 : 0
  
  name                 = "${var.instance_name}-read-replica"
  database_version     = var.database_version
  region               = var.replica_region != null ? var.replica_region : var.region
  project              = var.project_id
  master_instance_name = google_sql_database_instance.main.name

  replica_configuration {
    failover_target = false
  }

  settings {
    tier              = var.replica_tier
    availability_type = "ZONAL"
    disk_type         = var.disk_type
    disk_size         = var.disk_size
    disk_autoresize   = var.disk_autoresize

    # IP configuration
    ip_configuration {
      ipv4_enabled                                  = var.ipv4_enabled
      private_network                               = var.private_network
      enable_private_path_for_google_cloud_services = true
      require_ssl                                   = var.require_ssl
    }

    # User labels
    user_labels = merge(var.labels, {
      environment = var.environment
      component   = "database-replica"
    })
  }

  deletion_protection = var.deletion_protection
}

# TimescaleDB extension (requires custom setup)
resource "null_resource" "timescaledb_setup" {
  count = var.enable_timescaledb ? 1 : 0

  triggers = {
    instance_id = google_sql_database_instance.main.id
  }

  provisioner "local-exec" {
    command = <<-EOT
      # Install TimescaleDB extension
      echo "Creating TimescaleDB extension requires manual setup or Cloud SQL Proxy connection"
      echo "Connect to the database and run: CREATE EXTENSION IF NOT EXISTS timescaledb;"
      echo "Instance connection name: ${google_sql_database_instance.main.connection_name}"
    EOT
  }

  depends_on = [
    google_sql_database_instance.main,
    google_sql_database.databases
  ]
}

# Store database passwords in Secret Manager (optional)
resource "google_secret_manager_secret" "db_passwords" {
  for_each = var.store_passwords_in_secret_manager ? toset(var.database_users) : toset([])
  
  secret_id = "${var.instance_name}-${each.value}-password"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = merge(var.labels, {
    environment = var.environment
    component   = "database-secret"
  })
}

resource "google_secret_manager_secret_version" "db_passwords" {
  for_each = var.store_passwords_in_secret_manager ? toset(var.database_users) : toset([])
  
  secret      = google_secret_manager_secret.db_passwords[each.value].id
  secret_data = random_password.db_password[each.value].result
}