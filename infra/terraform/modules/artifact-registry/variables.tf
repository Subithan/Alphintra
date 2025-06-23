variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "location" {
  description = "The location for the repository"
  type        = string
}

variable "repository_id" {
  description = "The repository ID"
  type        = string
}

variable "description" {
  description = "The repository description"
  type        = string
  default     = ""
}

variable "format" {
  description = "The repository format"
  type        = string
  default     = "DOCKER"
}

variable "members" {
  description = "List of members to grant access to the repository"
  type        = list(string)
  default     = []
}