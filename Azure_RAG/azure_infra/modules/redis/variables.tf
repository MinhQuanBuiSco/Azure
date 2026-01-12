variable "name" {
  description = "Name of the Redis cache"
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

variable "sku_name" {
  description = "SKU name (Basic, Standard, Premium)"
  type        = string
  default     = "Standard"
}

variable "capacity" {
  description = "Cache capacity"
  type        = number
  default     = 1
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
