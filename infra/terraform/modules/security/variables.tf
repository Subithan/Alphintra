variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "environment" {
  description = "The environment name"
  type        = string
}

variable "binary_authorization_policy" {
  description = "Binary Authorization policy configuration"
  type = object({
    default_admission_rule = object({
      evaluation_mode           = string
      enforcement_mode          = string
      require_attestations_by   = list(string)
    })
  })
  default = {
    default_admission_rule = {
      evaluation_mode         = "ALWAYS_ALLOW"
      enforcement_mode        = "ENFORCED_BLOCK_AND_AUDIT_LOG"
      require_attestations_by = []
    }
  }
}

variable "secrets" {
  description = "Map of secrets to create in Secret Manager"
  type = map(object({
    secret_id = string
    data      = string
  }))
  default   = {}
  sensitive = true
}