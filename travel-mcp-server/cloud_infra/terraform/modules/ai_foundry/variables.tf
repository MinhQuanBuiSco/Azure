variable "name" {
  description = "AI Foundry account name"
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

variable "sku_name" {
  description = "SKU name"
  type        = string
  default     = "S0"
}

variable "custom_subdomain_name" {
  description = "Custom subdomain name"
  type        = string
}

variable "model_deployment_name" {
  description = "Model deployment name"
  type        = string
  default     = "gpt-4o-mini"
}

variable "model_name" {
  description = "OpenAI model name"
  type        = string
  default     = "gpt-4o-mini"
}

variable "model_version" {
  description = "Model version"
  type        = string
  default     = "2024-07-18"
}

variable "deployment_sku_name" {
  description = "Deployment SKU name"
  type        = string
  default     = "GlobalStandard"
}

variable "deployment_capacity" {
  description = "Deployment capacity (tokens per minute in thousands)"
  type        = number
  default     = 10
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
