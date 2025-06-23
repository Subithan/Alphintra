# Outputs for GKE Module

output "cluster_name" {
  description = "Name of the GKE cluster"
  value       = google_container_cluster.cluster.name
}

output "cluster_id" {
  description = "ID of the GKE cluster"
  value       = google_container_cluster.cluster.id
}

output "cluster_endpoint" {
  description = "Endpoint of the GKE cluster"
  value       = google_container_cluster.cluster.endpoint
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "CA certificate of the GKE cluster"
  value       = google_container_cluster.cluster.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "cluster_location" {
  description = "Location of the GKE cluster"
  value       = google_container_cluster.cluster.location
}

output "cluster_master_version" {
  description = "Master version of the GKE cluster"
  value       = google_container_cluster.cluster.master_version
}

output "cluster_node_version" {
  description = "Node version of the GKE cluster"
  value       = google_container_cluster.cluster.node_version
}

output "cluster_service_account" {
  description = "Service account used by the cluster nodes"
  value       = google_service_account.gke_nodes.email
}

output "workload_identity_service_account" {
  description = "Service account for Workload Identity"
  value       = google_service_account.workload_identity.email
}

output "general_pool_name" {
  description = "Name of the general node pool"
  value       = google_container_node_pool.general_pool.name
}

output "analytics_pool_name" {
  description = "Name of the analytics node pool"
  value       = var.enable_analytics_pool ? google_container_node_pool.analytics_pool[0].name : null
}

output "kubectl_config_command" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.cluster.name} --location ${google_container_cluster.cluster.location} --project ${var.project_id}"
}