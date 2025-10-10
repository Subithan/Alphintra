variable "project_id" {
  description = "GCP project id."
  type        = string
}

variable "workload_identity_project" {
  description = "Project that hosts the GKE cluster (defaults to project_id)."
  type        = string
  default     = null
}

variable "service_accounts" {
  description = "Service accounts to create and map via Workload Identity."
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
}
