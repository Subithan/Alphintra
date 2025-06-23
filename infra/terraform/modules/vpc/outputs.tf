# Outputs for VPC Module

output "network_name" {
  description = "Name of the VPC network"
  value       = google_compute_network.vpc.name
}

output "network_id" {
  description = "ID of the VPC network"
  value       = google_compute_network.vpc.id
}

output "network_self_link" {
  description = "Self link of the VPC network"
  value       = google_compute_network.vpc.self_link
}

output "private_subnet_name" {
  description = "Name of the private subnet"
  value       = google_compute_subnetwork.private_subnet.name
}

output "private_subnet_id" {
  description = "ID of the private subnet"
  value       = google_compute_subnetwork.private_subnet.id
}

output "private_subnet_cidr" {
  description = "CIDR block of the private subnet"
  value       = google_compute_subnetwork.private_subnet.ip_cidr_range
}

output "public_subnet_name" {
  description = "Name of the public subnet"
  value       = google_compute_subnetwork.public_subnet.name
}

output "public_subnet_id" {
  description = "ID of the public subnet"
  value       = google_compute_subnetwork.public_subnet.id
}

output "database_subnet_name" {
  description = "Name of the database subnet"
  value       = google_compute_subnetwork.database_subnet.name
}

output "database_subnet_id" {
  description = "ID of the database subnet"
  value       = google_compute_subnetwork.database_subnet.id
}

output "router_name" {
  description = "Name of the Cloud Router"
  value       = google_compute_router.router.name
}

output "nat_name" {
  description = "Name of the NAT gateway"
  value       = google_compute_router_nat.nat.name
}

output "pods_cidr" {
  description = "CIDR block for GKE pods"
  value       = var.pods_cidr
}

output "services_cidr" {
  description = "CIDR block for GKE services"  
  value       = var.services_cidr
}

output "private_service_access_name" {
  description = "Name of the private service access"
  value       = google_compute_global_address.private_service_access.name
}