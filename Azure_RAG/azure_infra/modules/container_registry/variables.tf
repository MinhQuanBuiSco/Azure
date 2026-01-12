variable "name" {
  description = "Name of the container registry"
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

variable "sku" {
  description = "SKU (Basic, Standard, Premium)"
  type        = string
  default     = "Standard"
}

variable "admin_enabled" {
  description = "Enable admin user"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
