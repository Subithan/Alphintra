# Outputs for Development Environment

# VPC outputs
output "vpc_network_name" {
  description = "VPC network name"
  value       = module.vpc.network_name
}

output "vpc_network_id" {
  description = "VPC network ID"
  value       = module.vpc.network_id
}

output "private_subnet_name" {
  description = "Private subnet name"
  value       = module.vpc.private_subnet_name
}

# GKE outputs
output "gke_cluster_name" {
  description = "GKE cluster name"
  value       = module.gke.cluster_name
}

output "gke_cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = module.gke.cluster_endpoint
  sensitive   = true
}

output "gke_cluster_ca_certificate" {
  description = "GKE cluster CA certificate"
  value       = module.gke.cluster_ca_certificate
  sensitive   = true
}

output "kubectl_config_command" {
  description = "Command to configure kubectl"
  value       = module.gke.kubectl_config_command
}

# Database outputs
output "database_instance_name" {
  description = "Cloud SQL instance name"
  value       = module.cloudsql.instance_name
}

output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = module.cloudsql.connection_name
}

output "database_private_ip" {
  description = "Cloud SQL private IP address"
  value       = module.cloudsql.private_ip_address
}

output "database_names" {
  description = "Created database names"
  value       = module.cloudsql.database_names
}

output "database_users" {
  description = "Created database users"
  value       = module.cloudsql.database_users
}

output "cloud_sql_proxy_command" {
  description = "Command to connect via Cloud SQL Proxy"
  value       = module.cloudsql.cloud_sql_proxy_command
}

# Redis outputs
output "redis_instance_id" {
  description = "Redis instance ID"
  value       = google_redis_instance.cache.id
}

output "redis_host" {
  description = "Redis host address"
  value       = google_redis_instance.cache.host
}

output "redis_port" {
  description = "Redis port"
  value       = google_redis_instance.cache.port
}

# Pub/Sub outputs
output "pubsub_topics" {
  description = "Created Pub/Sub topics"
  value = {
    market_data   = google_pubsub_topic.market_data.name
    trade_events  = google_pubsub_topic.trade_events.name
    risk_alerts   = google_pubsub_topic.risk_alerts.name
  }
}

output "pubsub_subscriptions" {
  description = "Created Pub/Sub subscriptions"
  value = {
    market_data_sub  = google_pubsub_subscription.market_data_sub.name
    trade_events_sub = google_pubsub_subscription.trade_events_sub.name
  }
}

# Secret Manager outputs
output "secret_manager_secrets" {
  description = "Secret Manager secret IDs"
  value = {
    api_keys   = google_secret_manager_secret.api_keys.secret_id
    jwt_secret = google_secret_manager_secret.jwt_secret.secret_id
  }
}

# Connection information for applications
output "application_config" {
  description = "Configuration for applications"
  value = {
    database = {
      host     = module.cloudsql.private_ip_address
      port     = 5432
      name     = "trading_db"
      user     = "trading_user"
      ssl_mode = "require"
    }
    redis = {
      host = google_redis_instance.cache.host
      port = google_redis_instance.cache.port
    }
    pubsub = {
      project_id = var.project_id
      topics = {
        market_data  = google_pubsub_topic.market_data.name
        trade_events = google_pubsub_topic.trade_events.name
        risk_alerts  = google_pubsub_topic.risk_alerts.name
      }
    }
    kubernetes = {
      cluster_name = module.gke.cluster_name
      namespace    = "default"
    }
  }
  sensitive = true
}

# Environment summary
output "environment_summary" {
  description = "Summary of the development environment"
  value = {
    environment     = "development"
    project_id      = var.project_id
    region         = var.region
    vpc_network    = module.vpc.network_name
    gke_cluster    = module.gke.cluster_name
    database       = module.cloudsql.instance_name
    redis_instance = google_redis_instance.cache.name
    cost_optimized = var.use_preemptible_nodes
  }
}