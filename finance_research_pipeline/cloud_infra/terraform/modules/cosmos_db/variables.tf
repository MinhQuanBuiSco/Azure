variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "database_name" {
  description = "Cosmos DB database name"
  type        = string
  default     = "finance_research"
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
