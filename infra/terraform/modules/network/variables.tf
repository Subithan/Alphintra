variable "project_id" {
  description = "GCP project id."
  type        = string
}

variable "network_name" {
  description = "Name of the VPC network to create."
  type        = string
}

variable "routing_mode" {
  description = "Global routing mode for the network."
  type        = string
  default     = "GLOBAL"
}

variable "subnets" {
  description = "Subnetwork definitions."
  type = list(object({
    name          = string
    region        = string
    ip_cidr_range = string
    secondary_ip_ranges = optional(list(object({
      range_name    = string
      ip_cidr_range = string
    })), [])
  }))
  default = []
}
