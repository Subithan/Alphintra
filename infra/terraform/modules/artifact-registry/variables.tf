variable "project_id" {
  description = "GCP project id."
  type        = string
}

variable "repositories" {
  description = "Artifact Registry repositories to manage."
  type = list(object({
    repository_id = string
    location      = string
    format        = string
    description   = optional(string, "")
    labels        = optional(map(string), {})
    kms_key_name  = optional(string)
  }))
}
