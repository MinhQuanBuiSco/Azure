variable "name" {
  description = "Name of Application Insights"
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

variable "application_type" {
  description = "Application type (web, other)"
  type        = string
  default     = "web"
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
