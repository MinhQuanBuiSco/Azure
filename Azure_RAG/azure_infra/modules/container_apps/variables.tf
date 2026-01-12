variable "environment_name" {
  description = "Name of the Container Apps Environment"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID"
  type        = string
}

variable "backend_app_name" {
  description = "Name of the backend container app"
  type        = string
}

variable "backend_image" {
  description = "Backend Docker image"
  type        = string
}

variable "backend_cpu" {
  description = "CPU allocation"
  type        = number
  default     = 1.0
}

variable "backend_memory" {
  description = "Memory allocation"
  type        = string
  default     = "2Gi"
}

variable "backend_min_replicas" {
  description = "Minimum replicas"
  type        = number
  default     = 3
}

variable "backend_max_replicas" {
  description = "Maximum replicas"
  type        = number
  default     = 50
}

variable "backend_env_vars" {
  description = "Environment variables"
  type = list(object({
    name  = string
    value = string
  }))
}

variable "backend_secrets" {
  description = "Secrets"
  type = list(object({
    name  = string
    value = string
  }))
  sensitive = true
}

variable "acr_server" {
  description = "ACR login server"
  type        = string
}

variable "acr_username" {
  description = "ACR username"
  type        = string
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
