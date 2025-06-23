variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "environment" {
  description = "The environment name"
  type        = string
}

variable "notification_channels" {
  description = "Map of notification channels to create"
  type = map(object({
    type         = string
    display_name = string
    labels       = map(string)
  }))
  default = {}
}

variable "alert_policies" {
  description = "Map of alert policies to create"
  type = map(object({
    display_name = string
    conditions = list(object({
      display_name = string
      condition_threshold = object({
        filter          = string
        comparison      = string
        threshold_value = number
        duration        = string
      })
    }))
  }))
  default = {}
}