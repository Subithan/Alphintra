output "network" {
  description = "Network resource outputs."
  value = {
    name      = module.network.network_name
    subnetworks = module.network.subnetwork_names
  }
}

output "artifact_registry" {
  description = "Managed Artifact Registry repositories."
  value       = module.artifact_registry.repositories
}

output "service_accounts" {
  description = "Service account emails mapped via Workload Identity."
  value       = module.workload_identity.service_accounts
}
