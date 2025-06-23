# Variables for VPC Module

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "network_name" {
  description = "Name of the VPC network"
  type        = string
}

variable "private_subnet_cidr" {
  description = "CIDR block for private subnet"
  type        = string
  default     = "10.1.0.0/24"
}

variable "public_subnet_cidr" {
  description = "CIDR block for public subnet"
  type        = string
  default     = "10.1.1.0/24"
}

variable "database_subnet_cidr" {
  description = "CIDR block for database subnet"
  type        = string
  default     = "10.1.2.0/24"
}

variable "pods_cidr" {
  description = "CIDR block for GKE pods"
  type        = string
  default     = "10.2.0.0/16"
}

variable "services_cidr" {
  description = "CIDR block for GKE services"
  type        = string
  default     = "10.3.0.0/16"
}

variable "ssh_source_ranges" {
  description = "Source IP ranges allowed for SSH access"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Restrict this in production
}

variable "enable_nat_gateway" {
  description = "Enable NAT gateway for outbound internet access"
  type        = bool
  default     = true
}

variable "enable_flow_logs" {
  description = "Enable VPC flow logs"
  type        = bool
  default     = true
}

variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
  default     = {}
}