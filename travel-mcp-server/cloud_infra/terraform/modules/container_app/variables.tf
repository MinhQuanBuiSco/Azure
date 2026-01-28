variable "name" {
  description = "Container App name"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "container_app_environment_id" {
  description = "Container Apps environment ID"
  type        = string
}

variable "revision_mode" {
  description = "Revision mode (Single or Multiple)"
  type        = string
  default     = "Single"
}

variable "container_name" {
  description = "Container name"
  type        = string
}

variable "image" {
  description = "Container image"
  type        = string
}

variable "cpu" {
  description = "CPU cores"
  type        = number
  default     = 0.5
}

variable "memory" {
  description = "Memory (e.g., 1Gi)"
  type        = string
  default     = "1Gi"
}

variable "min_replicas" {
  description = "Minimum replicas"
  type        = number
  default     = 1
}

variable "max_replicas" {
  description = "Maximum replicas"
  type        = number
  default     = 3
}

variable "env_vars" {
  description = "Environment variables"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "secret_env_vars" {
  description = "Secret environment variables"
  type = list(object({
    name        = string
    secret_name = string
  }))
  default = []
}

variable "secrets" {
  description = "Secrets"
  type = list(object({
    name  = string
    value = string
  }))
  default   = []
  sensitive = true
}

variable "ingress_enabled" {
  description = "Enable ingress"
  type        = bool
  default     = true
}

variable "ingress_external" {
  description = "External ingress"
  type        = bool
  default     = true
}

variable "ingress_target_port" {
  description = "Target port"
  type        = number
  default     = 80
}

variable "ingress_transport" {
  description = "Transport protocol"
  type        = string
  default     = "http"
}

variable "registry_server" {
  description = "Container registry server"
  type        = string
  default     = ""
}

variable "registry_username" {
  description = "Container registry username"
  type        = string
  default     = ""
}

variable "registry_password_secret_name" {
  description = "Secret name for registry password"
  type        = string
  default     = "acr-password"
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
