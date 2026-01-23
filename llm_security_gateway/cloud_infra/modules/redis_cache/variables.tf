variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "name_suffix" {
  description = "Suffix for resource names"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "sku_name" {
  description = "Redis SKU name"
  type        = string
  default     = "Basic"
}

variable "family" {
  description = "Redis family"
  type        = string
  default     = "C"
}

variable "capacity" {
  description = "Redis capacity"
  type        = number
  default     = 0
}
