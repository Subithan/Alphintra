output "network_name" {
  description = "Name of the created VPC network."
  value       = google_compute_network.this.name
}

output "subnetwork_names" {
  description = "Names of created subnetworks."
  value       = [for subnet in google_compute_subnetwork.this : subnet.name]
}
