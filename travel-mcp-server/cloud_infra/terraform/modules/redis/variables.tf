variable "name" {
  description = "Redis cache name"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "capacity" {
  description = "Redis cache capacity (0-6 for Basic/Standard, 1-4 for Premium)"
  type        = number
  default     = 0
}

variable "family" {
  description = "Redis cache family (C for Basic/Standard, P for Premium)"
  type        = string
  default     = "C"
}

variable "sku_name" {
  description = "Redis cache SKU (Basic, Standard, Premium)"
  type        = string
  default     = "Basic"
}

variable "non_ssl_port_enabled" {
  description = "Enable non-SSL port"
  type        = bool
  default     = false
}

variable "minimum_tls_version" {
  description = "Minimum TLS version"
  type        = string
  default     = "1.2"
}

variable "maxmemory_policy" {
  description = "Max memory eviction policy"
  type        = string
  default     = "allkeys-lru"
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
