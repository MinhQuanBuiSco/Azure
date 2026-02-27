variable "environment_name" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "backend_app_name" {
  type = string
}

variable "backend_image" {
  type = string
}

variable "backend_cpu" {
  type    = number
  default = 0.25
}

variable "backend_memory" {
  type    = string
  default = "0.5Gi"
}

variable "backend_min_replicas" {
  type    = number
  default = 0
}

variable "backend_max_replicas" {
  type    = number
  default = 1
}

variable "key_vault_url" {
  type = string
}

variable "allowed_origins" {
  type    = string
  default = "http://localhost:3000"
}

variable "acr_server" {
  type = string
}

variable "acr_username" {
  type = string
}

variable "acr_password" {
  type      = string
  sensitive = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
