variable "project_id" {
  description = "Target GCP project id."
  type        = string
}

variable "region" {
  description = "Default region for regional resources."
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Default zone for zonal resources."
  type        = string
  default     = "us-central1-f"
}

variable "network_name" {
  description = "Name of the VPC network."
  type        = string
  default     = "alphintra-staging-vpc"
}

variable "subnets" {
  description = "Subnet configuration for the environment."
  type = list(object({
    name          = string
    region        = string
    ip_cidr_range = string
    secondary_ip_ranges = optional(list(object({
      range_name    = string
      ip_cidr_range = string
    })), [])
  }))
}

variable "artifact_registry_repositories" {
  description = "Artifact Registry repositories to manage."
  type = list(object({
    repository_id = string
    location      = string
    format        = string
    description   = optional(string, "")
    labels        = optional(map(string), {})
    kms_key_name  = optional(string)
  }))
  default = []
}

variable "workload_identity_project" {
  description = "Project hosting the GKE Workload Identity pool (defaults to project_id)."
  type        = string
  default     = null
}

variable "workload_identity_service_accounts" {
  description = "Service accounts that require Workload Identity mappings."
  type = list(object({
    name        = string
    account_id  = string
    display_name = string
    description = optional(string, "")
    roles       = list(string)
    kubernetes_service_accounts = optional(list(object({
      namespace = string
      name      = string
    })), [])
  }))
  default = []
}

variable "cloudsql_instance_name" {
  description = "Existing Cloud SQL instance to host the auth database."
  type        = string
  default     = "alphintra-db-instance"
}

variable "auth_database_name" {
  description = "Database name for the auth service."
  type        = string
  default     = "alphintra_auth_service"
}

variable "auth_database_user" {
  description = "Database user for the auth service."
  type        = string
  default     = "alphintra"
}

variable "auth_database_password" {
  description = "Password for the auth database user."
  type        = string
  sensitive   = true
}

variable "auth_database_secret_name" {
  description = "Secret Manager secret name storing the auth DB password."
  type        = string
  default     = "auth-service-db-password"
}
