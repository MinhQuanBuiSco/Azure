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

variable "log_analytics_workspace_id" {
  description = "Log Analytics Workspace ID"
  type        = string
}

variable "backend_image" {
  description = "Backend container image"
  type        = string
}

variable "frontend_image" {
  description = "Frontend container image"
  type        = string
}

variable "azure_ai_endpoint" {
  description = "Azure AI Foundry endpoint"
  type        = string
}

variable "azure_ai_api_key" {
  description = "Azure AI API key"
  type        = string
  sensitive   = true
}

variable "azure_ai_deployment_name" {
  description = "Azure AI deployment name"
  type        = string
}

variable "azure_content_safety_endpoint" {
  description = "Azure Content Safety endpoint"
  type        = string
}

variable "azure_content_safety_key" {
  description = "Azure Content Safety key"
  type        = string
  sensitive   = true
}

variable "redis_connection_string" {
  description = "Redis connection string"
  type        = string
  sensitive   = true
}

variable "cosmos_connection_string" {
  description = "Cosmos DB connection string"
  type        = string
  sensitive   = true
}

variable "application_insights_connection_string" {
  description = "Application Insights connection string"
  type        = string
  sensitive   = true
}

variable "key_vault_id" {
  description = "Key Vault ID for secrets"
  type        = string
}

variable "registry_server" {
  description = "Container registry server URL"
  type        = string
  default     = ""
}

variable "registry_username" {
  description = "Container registry username"
  type        = string
  default     = ""
}

variable "registry_password" {
  description = "Container registry password"
  type        = string
  sensitive   = true
  default     = ""
}
