# VPC and Networking Module for Alphintra Trading Platform
# This module creates a VPC with subnets, firewall rules, and NAT gateway

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = var.network_name
  auto_create_subnetworks = false
  routing_mode           = "REGIONAL"
  description            = "VPC for ${var.environment} environment"

  depends_on = [
    google_project_service.compute
  ]
}

# Enable required APIs
resource "google_project_service" "compute" {
  service = "compute.googleapis.com"
  disable_dependent_services = true
}

resource "google_project_service" "container" {
  service = "container.googleapis.com"
  disable_dependent_services = true
}

# Private Subnet for GKE Nodes
resource "google_compute_subnetwork" "private_subnet" {
  name          = "${var.network_name}-private-subnet"
  ip_cidr_range = var.private_subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id
  description   = "Private subnet for GKE nodes"

  # Enable private Google access
  private_ip_google_access = true

  # Secondary IP ranges for GKE
  secondary_ip_range {
    range_name    = "gke-pods"
    ip_cidr_range = var.pods_cidr
  }

  secondary_ip_range {
    range_name    = "gke-services"
    ip_cidr_range = var.services_cidr
  }

  # Log configuration
  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling       = 0.5
    metadata           = "INCLUDE_ALL_METADATA"
    metadata_fields    = []
  }
}

# Public Subnet for Load Balancers
resource "google_compute_subnetwork" "public_subnet" {
  name          = "${var.network_name}-public-subnet"
  ip_cidr_range = var.public_subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id
  description   = "Public subnet for load balancers and NAT gateway"
}

# Database Subnet for Cloud SQL
resource "google_compute_subnetwork" "database_subnet" {
  name          = "${var.network_name}-database-subnet"
  ip_cidr_range = var.database_subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id
  description   = "Private subnet for Cloud SQL and databases"

  private_ip_google_access = true
}

# Cloud Router for NAT Gateway
resource "google_compute_router" "router" {
  name    = "${var.network_name}-router"
  region  = var.region
  network = google_compute_network.vpc.id
  
  bgp {
    asn = 64514
  }
}

# NAT Gateway for outbound internet access
resource "google_compute_router_nat" "nat" {
  name                               = "${var.network_name}-nat"
  router                            = google_compute_router.router.name
  region                            = var.region
  nat_ip_allocate_option            = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Firewall Rules

# Allow internal communication
resource "google_compute_firewall" "allow_internal" {
  name    = "${var.network_name}-allow-internal"
  network = google_compute_network.vpc.name

  allow {
    protocol = "icmp"
  }

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  source_ranges = [
    var.private_subnet_cidr,
    var.database_subnet_cidr,
    var.pods_cidr,
    var.services_cidr
  ]

  direction = "INGRESS"
}

# Allow SSH access
resource "google_compute_firewall" "allow_ssh" {
  name    = "${var.network_name}-allow-ssh"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = var.ssh_source_ranges
  target_tags   = ["ssh-access"]
  direction     = "INGRESS"
}

# Allow HTTP/HTTPS for load balancers
resource "google_compute_firewall" "allow_http_https" {
  name    = "${var.network_name}-allow-http-https"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["http-server", "https-server"]
  direction     = "INGRESS"
}

# Allow health checks
resource "google_compute_firewall" "allow_health_checks" {
  name    = "${var.network_name}-allow-health-checks"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["8080", "8443"]
  }

  source_ranges = [
    "35.191.0.0/16",  # Google Load Balancer health check ranges
    "130.211.0.0/22"
  ]

  target_tags = ["gke-node"]
  direction   = "INGRESS"
}

# Allow Istio sidecar communication
resource "google_compute_firewall" "allow_istio" {
  name    = "${var.network_name}-allow-istio"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["15001", "15006", "15090", "15021"]
  }

  source_ranges = [var.private_subnet_cidr]
  target_tags   = ["gke-node"]
  direction     = "INGRESS"
}

# Private Service Access for Cloud SQL
resource "google_compute_global_address" "private_service_access" {
  name          = "${var.network_name}-private-service-access"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_service_access.name]

  depends_on = [
    google_project_service.servicenetworking
  ]
}

resource "google_project_service" "servicenetworking" {
  service = "servicenetworking.googleapis.com"
  disable_dependent_services = true
}