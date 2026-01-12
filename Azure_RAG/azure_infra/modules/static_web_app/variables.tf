variable "name" {
  description = "Name of the static web app"
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

variable "sku_tier" {
  description = "SKU tier (Free or Standard)"
  type        = string
  default     = "Standard"
}

variable "app_settings" {
  description = "App settings"
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
